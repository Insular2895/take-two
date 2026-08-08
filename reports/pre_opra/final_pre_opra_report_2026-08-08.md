# Validation quantitative finale pré-OPRA — TTWO

**PRE_OPRA_RESEARCH_COMPLETE — NO_POSITION_RECOMMENDED**

Verdict moteur : **`ENGINE_NOT_PROVEN_SUPERIOR`**. Recherche uniquement ; aucune capacité d'ordre.

## A. DATA COVERAGE

Statut : `LOCAL_PRIVATE_DATA_USED`. 20 884 observations options uniques, 631 barres spot, taux, FX et 14 événements.
Preuve : `option_normalization_2026-08-08.json`.

## B. CALIBRATION

Statut : `DEVELOPMENT_CALIBRATED_HESTON_BLOCKED`. Empirique, EWMA, GARCH/GJR et 535 tranches SVI ; Heston reste non identifiable.
Preuve : `empirical_calibration_2026-08-08.json`.

## C. WALK-FORWARD

Statut : `REAL_DEVELOPMENT_OOS_LIMITED`. 10 tests futurs non chevauchants ; DSR 5,7 %, PBO 77,8 %.
Preuve : `walk_forward_protocol_2026-08-08.json`.

## D. HOLDOUT

Statut : `UNOPENED`. Ledger intact ; aucun holdout artificiel n'a été créé ou consulté.
Preuve : `../../validation/final_holdout_ledger.jsonl`.

## E. BASELINES

Statut : `NINE_REAL_ALIGNED_STRATEGIES`. Même capital EUR, mêmes dates, mêmes coûts prudents et même politique FX.
Preuve : `baseline_comparison_2026-08-08.json`.

| Stratégie | Total | E[R] | Médiane | CVaR95 | Max DD | P(profit) | P(cible) | P(perte>50%) | Coûts EUR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cash | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.00 |
| no_position | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.00 |
| underlying | 22.8% | 2.3% | 3.0% | 8.1% | 12.8% | 60.0% | 0.0% | 0.0% | 20.00 |
| buy_and_hold | 25.1% | 2.4% | 3.2% | 7.9% | 12.4% | 60.0% | 0.0% | 0.0% | 1.00 |
| atm_long_call | -65.5% | 10.9% | -1.3% | 64.7% | 92.0% | 50.0% | 10.0% | 30.0% | 1786.77 |
| fixed_delta_long_call | -99.6% | -3.5% | -36.7% | 84.7% | 99.9% | 30.0% | 10.0% | 50.0% | 3474.12 |
| standard_bull_call_spread | -100.0% | -17.5% | -8.2% | 100.0% | 100.0% | 50.0% | 10.0% | 40.0% | 4413.88 |
| random_admissible | -93.7% | -0.3% | -3.3% | 74.6% | 98.4% | 40.0% | 10.0% | 40.0% | 3077.53 |
| engine_candidate | -90.4% | -1.3% | -7.2% | 84.7% | 97.5% | 20.0% | 10.0% | 20.0% | 1682.57 |

## F. TOP CANDIDATES

Statut : `EXPOSED_WITH_NO_POSITION`. Le no-position ne masque ni l'upside mesuré ni le meilleur candidat bloqué.
Preuve : `severity_and_gate_sensitivity_2026-08-08.json`.

- `BEST_RISK_ADJUSTED` : **buy_and_hold** — Meilleur compromis OOS observé : +25,1% composé, CVaR 7,9%.
- `HIGHEST_UPSIDE` : **atm_long_call** — E[R] OOS la plus haute, mais -65,5% composé et CVaR 64,7%.
- `LOWEST_RISK` : **no_position** — Rendement et perte nuls dans le panel ; aucune exposition optionnelle.
- `BEST_BLOCKED_CANDIDATE` : **engine_candidate** — Meilleur candidat moteur visible ; échoue le gate central d'opportunité.
- `BEST_SIMPLE_BASELINE` : **buy_and_hold** — Baseline simple supérieure à V10 sur développement complet et OOS.

## G. FIVE SCORES

Statut : `CALCULATED_PARTIAL_AWARE`. Cinq dimensions calculées sans redistribuer les poids manquants.
Preuve : `five_scores_2026-08-08.json`.

- `opportunity` : **37.1/100**, couverture 100%, confiance `LOW`, manquants aucun
- `risk` : **49.5/100**, couverture 100%, confiance `LOW`, manquants aucun
- `evidence` : **40.3/100**, couverture 80%, confiance `LOW`, manquants holdout_validation, rights_confirmation
- `model_agreement` : **31.5/100**, couverture 50%, confiance `VERY_LOW`, manquants option_expected_return_agreement, candidate_ranking_agreement
- `execution_quality` : **50.5/100**, couverture 75%, confiance `LOW`, manquants live_execution_component

## H. RAW METRICS

Statut : `DISPLAYED`. Rendements, coûts, CVaR, drawdown, DSR, PBO et diagnostics sont conservés.
Preuve : `engine_verdict_2026-08-08.json`.

## I. SEVERE-LOSS LADDER

Statut : `CALCULATED_WITH_INTERVALS`. Six seuils avec intervalles Wilson et bootstrap ; dix observations seulement.
Preuve : `severity_and_gate_sensitivity_2026-08-08.json`.

- P(perte > 10%) = **50%** ; Wilson 95 % [23.7%, 76.3%]
- P(perte > 25%) = **30%** ; Wilson 95 % [10.8%, 60.3%]
- P(perte > 50%) = **20%** ; Wilson 95 % [5.7%, 51.0%]
- P(perte > 70%) = **10%** ; Wilson 95 % [1.8%, 40.4%]
- P(perte > 90%) = **0%** ; Wilson 95 % [0.0%, 27.8%]
- P(perte > 99%) = **0%** ; Wilson 95 % [0.0%, 27.8%]

## J. GATE SENSITIVITY

Statut : `GATE_INSTABILITY`. Le candidat passe le réglage permissif mais échoue central et strict.
Preuve : `severity_and_gate_sensitivity_2026-08-08.json`.

## K. V10 VS BASELINES

Statut : `V10_UNDERPERFORMS`. V10 perd sur le panel complet et OOS ; aucune supériorité ajustée Holm.
Preuve : `engine_verdict_2026-08-08.json`.

## L. ENGINE VERDICT

Statut : `ENGINE_NOT_PROVEN_SUPERIOR`. Verdict mécanique ; aucun retuning après observation du résultat.
Preuve : `engine_verdict_2026-08-08.json`.

## M. REMAINING BLOCKERS

Statut : `THREE_EXTERNAL_OR_FUTURE_DEPENDENCIES`. Droits humains, nouvel échantillon/holdout et OPRA restent irréductibles localement.
Preuve : `../../docs/LIMITATIONS.md`.

- Confirmation humaine du type d'abonnement et des droits de recherche/stockage des fournisseurs historiques.
- Échantillon options formel et holdout réellement futur : 25 observations disponibles contre 41 requises ; il ne peut pas être fabriqué sans fuite.
- Entitlement et identifiants OPRA live requis pour la future Phase M prospective read-only/paper.

## N. OPRA READINESS

Statut : `CONTRACT_DEFINED_NOT_CONNECTED`. Phase M non démarrée ; aucune connexion ou simulation OPRA n'a été effectuée.
Preuve : `../../docs/validation/OPRA_FINAL_VALIDATION_PLAN.md`.

- Contrat de provider live read-only prévu ; aucune méthode d'ordre autorisée.
- Chaînes, bid/ask, timestamps, fraîcheur et spreads devront être journalisés.
- Chaque décision paper sera gelée avant réalisation et reliée par hash.
- La Phase M comparera V10 aux mêmes baselines avec coûts et slippage observés.

Variables attendues : OPRA_PROVIDER, OPRA_API_KEY, OPRA_API_SECRET, OPRA_ACCOUNT_OR_SESSION

Commande : `ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml`

## Reproductibilité

- Commit source : `18bc7bda577e9c4d99518f7e798bde86c353dcce`
- Hash configuration : `98eadf0c3a13322bda6dc630b7fbe0a791ebb5ec2ff99e14004ceecf29265436`
- Hash dataset agrégé : `cd1ad376385bd7a891975637123e97d55c5f08b95fbc4895c7cf2857052514d9`
- Seed : `20260808`
- Holdout : `UNOPENED`
- Invariants : `transmit=false`, `what_if=true`, `order_capability=forbidden`
