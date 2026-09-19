# Readiness V11.1

Ce document est la référence courte pour savoir ce qui est réellement utilisable. Le
JSON, le Markdown et le HTML V11.1 sérialisent le même inventaire. Un statut décrit une
capacité, jamais une promesse de rendement.

## Statuts autorisés

| Statut | Signification |
| --- | --- |
| `production_ready_offline` | Contrat déterministe couvert hors ligne ; pas de conclusion financière live. |
| `experimental_offline` | Implémenté et testable, mais non calibré ou non validé hors échantillon. |
| `fixture_only` | Valide uniquement les mécanismes avec des données synthétiques identifiées. |
| `adapter_ready_not_connected` | Port logiciel présent ; aucune session ni entitlement actif. |
| `configured_not_entitled` | Paramètres non secrets valides ; licence/abonnement non confirmés et aucune connexion tentée. |
| `requires_live_market_data` | Nécessite des observations live autorisées et fraîches. |
| `requires_historical_calibration` | Nécessite un historique réel, licencié et point-in-time. |
| `requires_paper_trading` | Nécessite une campagne paper définie et archivée. |
| `blocked_for_execution` | La capacité d’ordre est absente par politique et par code. |

## Inventaire actuel

| Capacité | Statut maximal | Limite déterminante |
| --- | --- | --- |
| M0 full repricing, Greeks avancés et confiance numérique | `production_ready_offline` | Mécanique testée ; aucune calibration marché ou validation de rendement. |
| M0 flat-spot carry, scénarios et breakeven clock | `production_ready_offline` | IV future configurée, American intraday date-based, cashflows après première échéance exclus. |
| M0 coûts aller-retour et ticket typé | `experimental_offline` | Sortie, slippage et combo sont des estimations avant OPRA/paper. |
| M0 P(touch) pathwise | `experimental_offline` | Calcul disponible sur chemins `P`; aucune probabilité TTWO promue dans le ticket fixture. |
| M0.1 distribution de PnL net | `experimental_offline` | Contrat testé sur chemins économiques synthétiques ; aucun modèle `P` TTWO promu. |
| M0.1 five-score bridge | `production_ready_offline` | Copie déterministe des scores canoniques et de leur scope ; leur calibration financière reste inchangée. |
| M0.1 event-date et mixed-expiry | `production_ready_offline` | Timing et deadline testés ; lifecycle après première échéance volontairement exclu. |
| M0 marge et FX | `experimental_offline` | Architecture explicite ; marge broker et mode FX réel restent à confirmer. |
| M0.2 FlexibleBudgetPolicyV2 et diagnostics | `production_ready_offline` | Contrats/gates testés ; ne valide ni capital broker réel ni décision financière. |
| M0.2 capital mixed-expiry | `experimental_offline` | Fail-closed sans what-if broker ou borne analytique validée ; scenario grids non probants. |
| M0.2.1 sémantique réserve/lifecycle/FX | `production_ready_offline` | Logique déterministe gelée ; contexte compte et coûts broker réels restent Phase M. |
| Moteur contractuel V10.1 et contrôle américain QuantLib | `production_ready_offline` | Dépend encore de la qualité des quotes d’entrée. |
| Provenance et cutoff | `production_ready_offline` | La complétude dépend des connecteurs fournis. |
| Normalisation déterministe des événements | `experimental_offline` | Revue humaine et calibration des règles requises. |
| Bayes auditable | `experimental_offline` | Priors et likelihoods non calibrés historiquement. |
| GBM, local vol, Heston, Heston+jumps | `fixture_only` ou `experimental_offline` | Calibration, convergence et validation hors échantillon manquantes. |
| Import/calibration historique | `experimental_offline` | Dataset privé réel exploité ; droits du compte et surfaces imparfaites restent à confirmer. |
| Walk-forward | `experimental_offline` | 25 observations alignées et 10 OOS, sous le minimum formel de 41. |
| Robustesse, stress et allocation entière | `experimental_offline` | Les entrées probabilistes restent expérimentales. |
| Surveillance par snapshots et replay | `experimental_offline` | Aucune campagne paper/live terminée. |
| Rapports autonomes | `production_ready_offline` | Les résultats héritent du statut de leurs données. |
| Provider IBKR/OPRA read-only | `experimental_offline` | Chaîne, normalisation, BAG et diagnostics de reprise testés avec transport fake ; entitlement/licence et validation live de la nouvelle implémentation absents. |
| What-if broker | `experimental_offline` | Normalisation redacted et consommation typée codées ; requête broker ordre-shaped et valeurs réelles non observées. |
| Contrôle campagne shadow | `experimental_offline` | Manifeste, append prospectif, délais et statut testés ; seuils humains non approuvés et aucune observation prospective collectée. |
| Exécution | `blocked_for_execution` | `transmit=false`, `what_if=true`, confirmation humaine. |

## Gates de promotion

Chaque passage exige un validateur nommé et des preuves archivées. Aucun gate
`automatic_execution` n’existe.

| Gate | Entrée et données | Sortie et métriques minimales | Responsable | Preuves |
| --- | --- | --- | --- | --- |
| `RESEARCH_ONLY` | Fixtures ou données incomplètes | Contrats, provenance, tests et blockers explicites | Mainteneur technique | CI, manifestes, rapports |
| `OFFLINE_VALIDATED` | Suite hors ligne complète | CI verte, schémas stables, reproductibilité et sécurité vertes | Mainteneur technique | Logs CI et hashes |
| `HISTORICALLY_CALIBRATED` | Historique réel autorisé | Qualité acceptée, paramètres identifiables, erreurs documentées | Responsable modèle + data | Dataset hash, licence, rapport |
| `WALK_FORWARD_PASSED` | Calibration gelée et fenêtres point-in-time | Baselines battues selon seuils validés, holdout intact, ECE/Brier/CVaR acceptés | Comité modèle | Plan, résultats, audit anti-look-ahead |
| `PAPER_TRADING` | Gate précédent + flux paper | Durée, échantillon, coûts, rejets et slippage conformes aux seuils approuvés | Risk owner | Journal paper et rapport |
| `LIVE_DATA_READ_ONLY` | Entitlements et licences approuvés | Fraîcheur, reconnexion, complétude et fail-closed testés | Data owner + sécurité | Tests de connecteur et incidents |
| `HUMAN_CONFIRMED_PREVIEW` | Quotes combo et what-if disponibles | Ticket expirant, coûts/marge vérifiés, confirmation explicite, jamais transmis | Opérateur humain | Audit du preview |
| `COMMERCIAL_RESEARCH_PRODUCT` | Juridique, licences, sécurité, support | Checklist commerciale signée, monitoring et reprise testés | Direction + juridique | Dossier de validation |

Les seuils chiffrés de calibration, walk-forward et paper trading restent
`draft_to_validate` dans [VALIDATION_PLAN.md](VALIDATION_PLAN.md). Ils ne doivent pas
être inventés dans le code.

## Readiness M0.1

`M0_1_STATUS = COMPLETE` et `PRE_OPRA_LOGIC_STATUS = COMPLETE` signifient que les sept corrections
de logique financière offline, le schéma ticket 1.1, le renderer, les fixtures et les contrôles
numériques sont présents. Cela ne promeut aucun candidat, score, probabilité ou seuil de risque.
Le holdout reste `UNOPENED` et OPRA reste `NOT_STARTED`. Restent explicitement en attente : NBBO
live, quotes combo, profondeur, fraîcheur live, marge/commissions what-if, fills paper et qualité
d'exécution prospective.

`NEXT_PHASE = M — OPRA READ-ONLY LIVE DATA + SHADOW/PAPER VALIDATION`. Cette phase n'est pas
lancée par M0.

## Readiness M0.2

`M0_2_STATUS = COMPLETE`, `FLEXIBLE_BUDGET_POLICY = READY` et
`PRE_OPRA_LOGIC_STATUS = COMPLETE` signifient que le configurateur V2, les hard gates parallèles,
les quantités entières, le FX point-in-time, le ticket 1.2 et le blocage mixed-expiry non prouvé
sont couverts hors ligne. Les anciens runs restent V1 et leurs hashes ne changent pas. Les cinq
scores ne sont pas retunés.

Le holdout reste `UNOPENED`; OPRA et Phase M restent `NOT_STARTED`. La marge/buying power broker,
les commissions what-if, les quotes combo/NBBO, les fills et la campagne shadow/paper restent des
dépendances externes de promotion.

`NEXT_PHASE = M — OPRA READ-ONLY + SHADOW/PAPER VALIDATION`. M0.2 prépare sa configuration mais
ne lance aucune connexion ni activité paper.

## Readiness M0.2.1

`M0_2_1_STATUS = COMPLETE`, `BUDGET_SEMANTICS = FINALIZED` et
`PRE_OPRA_LOGIC_STATUS = COMPLETE_AND_FROZEN` signifient que la réserve de compte contraint
désormais le plafond effectif, qu'un seul objet lifecycle gouverne toutes les deadlines
mixed-expiry et que les frais de transaction FX sont distincts du taux. Un coût FX requis mais
inconnu reste nul, rend la garantie `UNPROVEN` et bloque le paper.

Cette clôture ne fournit pas les données broker : frais/route FX IBKR, cash USD validé, buying
power, marge combo, commissions et exécution restent à observer en Phase M. Le holdout reste
`UNOPENED`, OPRA `NOT_STARTED` et aucune capacité d'ordre n'existe.

`NEXT_PHASE = M — OPRA READ-ONLY + SHADOW/PAPER VALIDATION`.

## Checkpoint provider IBKR — 16 septembre 2026

Le provider officiel de marché est présent derrière une commande à consentement explicite. Les
contrats, gates, normalisation, cache/retry/pacing, conversion moteur et comparaison BAG sont
`experimental_offline`. Le handshake du 25 août est une preuve séparée et plus étroite ; il ne
promote pas ce provider. `LIVE_DATA_READ_ONLY`, shadow et paper restent non franchis. L'exécution
reste `blocked_for_execution`.

## Checkpoint protocole de validation — 17 septembre 2026

Une commande unique produit maintenant les preuves machine et humaines : santé initiale, seconde
session indépendante, chaîne, identité contrat, complétude, couverture volume/OI/Greeks,
timestamps, type de marché et BAG optionnelle résolue sans `conId` saisi manuellement. Les statuts
séparent échec sûr, chemin observé non promouvable et promotion stricte des seules données. Ce
protocole est `experimental_offline` tant qu'il n'a pas été exécuté contre le provider réel.

La compatibilité HMAC Python/Cloudflare est prouvée par un vecteur partagé. Le trajet
Oracle→Access→Worker→D1→dashboard demeure `requires_live_market_data`/preuve distante requise.

## Checkpoint contrôle shadow — 17 septembre 2026

Le code peut maintenant vérifier un manifeste de campagne, lier un commit, une configuration, une
preuve IBKR, un holdout et deux approbations humaines, puis contrôler deux journaux hash-chaînés
séparant décision et réalisation. Aucun seuil par défaut n'est inventé. Le manifeste d'exemple est
`draft_to_validate` et `example_only=true`, donc bloqué.

Même lorsque les nombres d'observations demandés sont atteints, le rapport conserve
`paper_validation_passed=false`, `promotion_eligible=false` et exige une revue humaine. Cela prépare
la campagne ; cela ne signifie pas qu'elle a commencé ni qu'une stratégie est validée.

## Checkpoint préconnexion offline — 17 septembre 2026

Le normaliseur what-if accepte une transcription redacted déjà obtenue, conserve les inconnues,
rejette les sentinelles et n'alimente la preview que si candidat, devise et complétude concordent.
Il n'appelle aucune primitive broker. Les rapports IBKR intègrent désormais les compteurs de
retry, pacing et cache, avec `stale_fallbacks=0`.

Les commandes shadow savent ajouter décision et réalisation prospectivement. Chaque record porte
campagne et heure d'écriture ; les délais maximums n'ont pas de défaut et doivent être approuvés
par le responsable risque. Les brouillons commités restent bloqués par `example_only=true`.

Ce checkpoint clôt le code sûr réalisable sans branchement. Il ne franchit ni
`LIVE_DATA_READ_ONLY`, ni shadow, ni paper, et n'ajoute aucune capacité d'ordre.
