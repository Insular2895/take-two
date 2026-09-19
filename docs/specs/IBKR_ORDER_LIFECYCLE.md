# Cycle de vie des ordres IBKR

Statut logiciel : `ORDER_LIFECYCLE_MODEL = READY_OFFLINE`  
Capacité broker : `PAPER_ADAPTER_CODE = READY_OFFLINE_DISARMED`  
Transmission : `PAPER_ORDER_TRANSMISSION = DISABLED`  
Exécution réelle : `LIVE_EXECUTION = FORBIDDEN`

## Pourquoi ce modèle existe

Un bouton « envoyer » ne prouve pas qu’un ordre a été reçu, accepté ou exécuté. Le contrôle plane
sépare donc trois vérités :

1. **intention locale** : aperçu, confirmation, création et claim de l’intent ;
2. **preuve bridge/TWS** : tentative de soumission et callbacks observés ;
3. **preuve broker** : statut, exécution, commission ou erreur portant les identifiants IBKR.

Une absence de callback n’est pas un rejet. Un ordre sans fill n’est pas un échec. Si la preuve
manque après une coupure, le résultat est `RECONCILIATION_REQUIRED`.

## Deux couches de statut

Le statut brut est conservé dans `raw_broker_status`. Le statut canonique sert à l’interface et aux
contrôles. Le mapping est dans
`services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/order_lifecycle.py`, jamais dans le navigateur.

| Preuve brute IBKR | Statut canonique | Interprétation autorisée |
|---|---|---|
| aucun envoi, `transmit=false` | `LOCAL_NOT_TRANSMITTED` | l’ordre est resté local |
| `PendingSubmit` | `PENDING_SUBMIT` | reçu par la couche API/TWS, acceptation broker non prouvée |
| `PreSubmitted` | `PRE_SUBMITTED` | pré-soumis selon IBKR |
| `Submitted`, 0 fill | `WORKING` | ordre actif, condition `WORKING_NO_FILL_YET` |
| quantité remplie entre 0 et le total | `PARTIALLY_FILLED` | exécution partielle active |
| restant = 0 avec fill positif | `FILLED` | exécution complète |
| `PendingCancel` | `PENDING_CANCEL` | annulation demandée, pas encore finale |
| `Cancelled` | `CANCELLED` | annulation prouvée, cause séparée |
| `ApiCancelled` | `API_CANCELLED` | annulation API brute préservée |
| `Inactive` | `INACTIVE` | état brut inactif ; une erreur séparée précise éventuellement le rejet |
| statut inconnu | `AMBIGUOUS` | aucune conclusion inventée |
| session perdue sur un ordre non résolu | `RECONCILIATION_REQUIRED` | interroger les ordres/exécutions, ne pas renvoyer |

Les quantités ont priorité sur le libellé : `filled > 0` et `remaining > 0` produit toujours
`PARTIALLY_FILLED`; `filled > 0` et `remaining = 0` produit `FILLED`.

## Machine d’état

```text
CREATED → REVALIDATING → PREVIEW_READY → CONFIRMED → READY → CLAIMED
                                                           ├─ LOCAL_NOT_TRANSMITTED
                                                           └─ BROKER_SUBMISSION_ATTEMPTED
                                                              → PENDING_SUBMIT → PRE_SUBMITTED → WORKING
                                                      ├─ PARTIALLY_FILLED → FILLED
                                                      ├─ PENDING_CANCEL → CANCELLED
                                                      ├─ REJECTED / INACTIVE / EXPIRED
                                                      └─ AMBIGUOUS
                                                           └─ RECONCILIATION_REQUIRED
```

Cette vue n’efface pas les transitions brutes. Chaque preuve reste dans le journal append-only.
L’état courant n’est qu’une projection pratique du dernier événement recevable.

## Callbacks préparés

Le normaliseur pur sait produire des événements signés à partir de :

- `openOrder` et `openOrderEnd` ;
- `orderStatus` ;
- `error`, avec code et message nettoyé ;
- `execDetails` et `execDetailsEnd` ;
- `commissionReport` ;
- la borne `completedOrdersEnd` et le type `COMPLETED_ORDER` pour une future adaptation.

IBKR précise qu’un même `orderStatus` peut être dupliqué et que certains changements peuvent ne
pas produire de callback ; `execDetails` doit donc être surveillé en parallèle. Les clés
`broker_event_key`, `permId` et `execId` rendent l’ingestion idempotente. Voir les documentations
officielles [Order submission](https://interactivebrokers.github.io/tws-api/order_submission.html),
[Executions and commissions](https://interactivebrokers.github.io/tws-api/executions_commissions.html)
et [Open orders](https://interactivebrokers.github.io/tws-api/open_orders.html).

## Preuves conservées

Migration additive `0010_order_lifecycle_readiness.sql` :

| Table | Rôle | Mutabilité |
|---|---|---|
| `broker_order_state_latest` | projection canonique courante | mise à jour monotone par date de preuve |
| `broker_order_lifecycle_events` | timeline brute/canonique | append-only |
| `broker_order_errors` | code, message nettoyé, catégorie | append-only |
| `broker_executions` | une ligne par `execId` | append-only |
| `broker_commissions` | commission reliée à l’`execId` | append-only |
| `broker_market_snapshots` | marché figé au moment de soumettre | immuable |
| `broker_reprice_proposals` | proposition de prix consultative | immuable, action automatique interdite |

La timeline stocke le hash SHA-256 de la preuve brute, mais seulement un payload nettoyé. Les
identifiants complets de compte, mots de passe, tokens, secrets et clés API sont retirés avant la
persistance. Le navigateur ne reçoit ni le payload de preuve complet ni l’advanced rejection JSON.

### Qualité d’exécution future

Une exécution est reliée par `intent_id` au snapshot immuable de soumission, qui conserve le
midpoint de décision, la limite soumise et les bid/ask combo observés. Sa ligne `execId` peut en
plus conserver le prix de fill, les bid/ask combo proches du fill, le délai d’exécution, le
slippage contre le midpoint de décision, le slippage contre la quote exécutable et la séquence du
partial fill. La commission reste reliée au même `execId`.

Ces champs sont optionnels tant qu’aucune preuve Paper réelle ne les fournit : une valeur absente
reste `null`. Ils constituent une preuve prospective de qualité d’exécution et ne modifient jamais
les scores historiques figés sans changement de version et validation séparée.

## Temps et ancienneté

Les champs suivants répondent à des questions différentes :

- `intent_created_at` : création locale ;
- `bridge_claimed_at` : prise en charge par le bridge ;
- `broker_submission_attempted_at` : tentative enregistrée ;
- `transmitted_to_broker` : uniquement si une preuve compatible l’établit ;
- `broker_acknowledged_at` : premier statut compatible avec une reconnaissance broker ;
- `submitted_at` et `working_since` : début observé de soumission/travail ;
- `last_status_at` : dernière preuve canonique prise en compte ;
- `last_market_update_at` : dernière cotation utilisée pour diagnostiquer.

`seconds_working` est calculé à l’affichage à partir de `working_since`. Aucun faux timeout n’est
créé. `DAY`, `GTC`, `IOC` et `FOK` sont conservés ; aucun changement automatique de TIF n’existe.

## Annulation et rejet

La cause d’annulation est distincte du statut : `USER_REQUESTED`, `API_REQUESTED`,
`TWS_REQUESTED`, `BROKER_CANCELLED`, `EXCHANGE_CANCELLED`, `TIF_EXPIRED`, `PRECAUTION`,
`INVALID_ORDER`, `PRICE_PROTECTION`, `SESSION_LOST` ou `UNKNOWN`.

Le rejet conserve toujours le code IBKR et une catégorie structurée : pacing/tickers, doublon,
ordre/tick/TIF invalide, échec de soumission/modification, valeur arrêtée, permission de compte,
buying power, droit market data, précaution, contrat/combo/garantie invalide, taille, what-if,
restriction d’exchange, état de compte/session ou rejet inconnu. La catégorie ne remplace jamais
le code brut. La matrice testée couvre 100, 101, 103, 106, 107, 109, 110, 111, 116, 133, 134,
154, 160, 163, 164, 200–203, 312–315, 354, 355, 360, 10002, 10015,
10089–10091, 10186 et 10197. Les codes IBKR officiels sont documentés dans
[TWS API message codes](https://interactivebrokers.github.io/tws-api/message_codes.html).

## Redémarrage et récupération

Le journal SQLite/WAL local mémorise `orderRef`, `orderId`, `permId` et tous les `execId`. Après un
redémarrage :

1. l’outbox non publiée est rejouée de manière idempotente ;
2. les intents non terminaux sont recherchés avec leurs identités broker ;
3. aucun nouvel intent n’est claimé tant qu’un ancien reste non résolu ;
4. si aucun état ne peut être prouvé, le résultat reste `RECONCILIATION_REQUIRED`.

Une reprise ne réutilise donc jamais « absence locale » comme autorisation de soumettre un doublon.

## Frontière actuelle

`main.py` instancie toujours `DisabledGateway()`. Les commandes de fermeture existantes exigent
toujours `transmit=false`; le runtime les classe `LOCAL_NOT_TRANSMITTED`. Le nouveau contrat
`PAPER_ENTRY` peut représenter une demande `transmit=true` uniquement après ticket, preview et
confirmation, mais son intent Cloudflare reste `dispatch_authorized=0` et aucun runtime actif ne
le claim. L’unique primitive de placement est confinée à `paper_gateway.py`; aucune opération
`modifyOrder`, `cancelOrder`, `exerciseOptions` ou capacité Live n’est activée.

Avant un vrai gateway Paper : validation read-only réelle, convention de prix BAG observée,
entitlement OPRA confirmé, cotation combo fraîche, précautions comprises, compte `DU*`, reprise et
callbacks testés, revue sécurité, puis approbation humaine explicite.
