# Repricing borné — modèle de prévisualisation

Statut logiciel : `REPRICE_PROPOSAL = READY_OFFLINE`  
Modification broker : `DISABLED`  
Chasing automatique : `FORBIDDEN`

## But

Une proposition de repricing répond à une seule question : « si l’opérateur ne changeait que la
limite du BAG, la structure est-elle encore économiquement valide avec le marché actuel ? » Elle
ne modifie rien chez IBKR.

Le calcul borné historique n’est plus une autorisation suffisante. Chaque proposition doit avoir
un `ExecutionRevalidationTicket` complet : marché rafraîchi, moteur économique canonique relancé,
tick actuel, Greeks corrects, dérive matérielle et éventuelle réanalyse. Sans ticket, aucune
proposition n’est exécutable.

## Entrées immuables et variable autorisée

Tout reste identique : ticker, contrat BAG, expirations, strikes, droits call/put, ratios, actions,
quantité, multiplicateur, stratégie, type `LIMIT`, sens débit/crédit et TIF. Le hash de la forme
d’ordre originale doit être identique au hash proposé.

La seule variable autorisée est la **limite combo**. Un hash différent produit
`BLOCKED_ORDER_SHAPE_CHANGED`. Il n’existe aucun fallback jambe par jambe et aucune conversion en
ordre MARKET.

## Conditions préalables

Une prévisualisation utilisable exige simultanément :

- market data `LIVE` ;
- bid et ask combo valides ;
- combo, toutes les jambes et sous-jacent `FRESH` ;
- FX frais si la devise l’exige ;
- convention de prix signé IBKR du BAG vérifiée ;
- headroom de budget dur et de perte maximale connu ;
- borne autorisée de débit maximal ou crédit minimal connue.

Sinon le résultat reste indisponible/bloqué. Une donnée manquante n’est jamais remplacée par zéro.

## Économie débit

Pour un débit, monter la limite accepte de payer davantage :

```text
limite actuelle       5.25
proposition           5.30
quantité                 1
multiplicateur         100
coût incrémental      +5.00
débit maximum autorisé 5.40
```

La proposition est consultable seulement si `5.30 <= 5.40`, si les headrooms couvrent 5 € et si
le hash d’ordre reste identique. Baisser la limite dans ce workflow d’amélioration est bloqué comme
direction incohérente ; l’opérateur peut créer une nouvelle preview si son intention diffère.

## Économie crédit

Pour un crédit, baisser la limite accepte de recevoir moins :

```text
crédit actuel          5.25
proposition            5.20
crédit minimum autorisé 5.10
impact incrémental     5.00
```

La proposition est valide seulement si `5.20 >= 5.10`. Monter le crédit demandé ne correspond pas
à un pas plus agressif et devient `BLOCKED_DIRECTION` dans ce modèle.

## Statuts

| Statut | Sens |
|---|---|
| `READY_FOR_HUMAN_PREVIEW` | calcul cohérent, aucune action automatique |
| `REPRICE_UNAVAILABLE_DATA_STALE` | donnée non live, stale, absente ou incohérente |
| `REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED` | signe BAG non prouvé |
| `BLOCKED_AUTHORIZED_BOUND` | débit max/crédit min dépassé ou absent |
| `BLOCKED_HARD_BUDGET` | headroom de budget insuffisant/inconnu |
| `BLOCKED_MAX_LOSS` | cap de perte dépassé/inconnu |
| `BLOCKED_ORDER_SHAPE_CHANGED` | quantité/jambes/stratégie/type modifiés |
| `BLOCKED_DIRECTION` | le pas n’est pas un repricing agressif autorisé |

Chaque ligne D1 force `automatic_action_allowed = 0` et est immuable. Une politique de dérive non
configurée produit `REQUIRES_POLICY` et `REVIEW_REQUIRED`; aucune constante d’investissement n’est
inventée.

## Nouveau consentement requis

Une proposition qui change matériellement l’autorisation économique doit produire une nouvelle
execution preview et une nouvelle confirmation. Cela inclut notamment une borne de prix plus large,
plus de capital, une perte maximale supérieure, davantage de contrats ou une autre forme d’ordre.

## Ce qui n’existe volontairement pas

- pas de `modifyOrder` dans le runtime activé ;
- pas de boucle de chasing ;
- pas de timer qui avance seul ;
- pas de nombre de pas implicite ;
- pas de passage DAY vers IOC/FOK ;
- pas de contournement des précautions IBKR ;
- pas de soumission Paper ou Live.

Le premier test n’utilisera qu’une proposition fraîche, une revalidation complète et une nouvelle
confirmation humaine. Une ladder automatique reste hors périmètre et interdite.
