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
| `requires_live_market_data` | Nécessite des observations live autorisées et fraîches. |
| `requires_historical_calibration` | Nécessite un historique réel, licencié et point-in-time. |
| `requires_paper_trading` | Nécessite une campagne paper définie et archivée. |
| `blocked_for_execution` | La capacité d’ordre est absente par politique et par code. |

## Inventaire actuel

| Capacité | Statut maximal | Limite déterminante |
| --- | --- | --- |
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
| Port IBKR/OPRA read-only | `adapter_ready_not_connected` | Contrat logiciel prêt ; session, entitlement et quotes combo absents. |
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
