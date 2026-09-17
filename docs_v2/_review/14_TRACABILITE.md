# Traçabilité code, tests et documentation

## Matrice principale

| Capacité | Code principal | Tests | Documentation |
|---|---|---|---|
| Contrats chaîne/quote | `opra/contracts.py` | `test_opra_contracts.py`, `test_ibkr_opra_provider.py` | 05, 07 |
| Gates et normalisation | `opra/ibkr_provider.py` | `test_ibkr_opra_provider.py` | 03, 04, 05 |
| Transport officiel | `opra/ibkr_official.py` | scan de frontière + tests fake du provider | 07, 11 |
| Conversion moteur | `live_chain_to_market_snapshot` | test de conversion canonique | 02, 05 |
| BAG/synthétique | contrats + provider + transport | test combo déterministe | 03, 07 |
| What-if offline | `opra/what_if.py`, `BrokerWhatIfEvidence` | `test_ibkr_what_if.py`, preview typée | 07, 11, 12, 17 |
| Diagnostics provider | `IbkrProviderDiagnostics` + rapport | tests retry/cache/validation | 07, 15, 17 |
| Protocole de validation IBKR | `opra/validation.py`, CLI | `test_ibkr_validation.py` | 09, 11, 15 |
| Télémétrie positions | `services/ibkr-paper-bridge` | tests service + Worker | 08 |
| HMAC Python/Worker | fixture canonique partagée | tests bridge + Worker | 08, 09 |
| Journaux shadow immuables | `opra/paper_decisions.py` | `test_paper_decisions.py` | 09, 16 |
| Contrôle campagne shadow | `opra/shadow_campaign.py`, CLI append/status | `test_shadow_campaign.py` | 11, 12, 16 |
| Contrôle Cloudflare | `cloudflare/src` | Vitest Worker | 08, 10 |
| Moteur quantitatif | `decision`, `quantitative`, `simulation`, `validation` | suite Python | 06, 09 |
| Frontière exécution | `data.py`, `intelligence/execution.py`, security gate | tests sécurité | 04 |

## Sources internes prioritaires

- `README.md` ;
- `docs/architecture/CURRENT_ARCHITECTURE.md` ;
- `docs/product/PRODUCT_CONTRACT.md` ;
- `docs/READINESS.md` ;
- `reports/PRE_OPRA_ENGINE_CONSOLIDATION_REPORT.md` ;
- `docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md` ;
- `docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md`.

## Source d’inspiration documentaire

La structure de revue humaine est adaptée du dossier fourni par l’utilisateur :

`https://github.com/Insular2895/hyperliquid-arbitrage-bot/tree/codex-docs/docs_v2/_review`

Les idées reprises sont : point d’entrée, décisions explicites, invariants de sécurité, niveaux de
preuve, éléments humains ouverts et matrice de traçabilité. Le contenu métier de ce dossier reste
spécifique à Take Two et ne reprend pas les décisions du bot Hyperliquid.

## Limite du certificat

Cette matrice prouve où lire et tester une capacité. Elle ne certifie ni la justesse des marchés,
ni la fraîcheur future de la documentation IBKR, ni les droits du compte, ni la rentabilité.
