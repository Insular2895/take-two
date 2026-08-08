# Validation quantitative finale pré-OPRA — TTWO

**Statut : `BLOCKED_BY_DATA` — `NO_POSITION_RECOMMENDED`.**

Le logiciel est testé, mais la preuve financière reste insuffisante. Ce rapport
est un outil de recherche, pas un conseil en investissement, et ne peut créer
aucun ordre.

## Résultat par phase

| Phase | Statut | Livrable |
|---|---|---|
| A — audit des gaps | `READY_RESEARCH_ONLY` | [../../docs/audits/PRE_OPRA_GAP_ANALYSIS.md](../../docs/audits/PRE_OPRA_GAP_ANALYSIS.md) |
| B — configuration | `CONFIG_READY` | [../../docs/config/PRE_OPRA_CONFIG.md](../../docs/config/PRE_OPRA_CONFIG.md) |
| C — données PIT | `BLOCKED` | [data_inventory_2026-08-08.json](data_inventory_2026-08-08.json) |
| D — calibration | `DIAGNOSTIC_ONLY_LICENSE_REVIEW` | [empirical_calibration_2026-08-08.json](empirical_calibration_2026-08-08.json) |
| E — walk-forward | `DIAGNOSTIC_ONLY_LICENSE_REVIEW` | [walk_forward_protocol_2026-08-08.json](walk_forward_protocol_2026-08-08.json) |
| F — holdout final | `UNOPENED` | [../../validation/final_holdout_ledger.jsonl](../../validation/final_holdout_ledger.jsonl) |
| G — baselines | `BLOCKED_INCOMPARABLE_DATA` | [baseline_comparison_2026-08-08.json](baseline_comparison_2026-08-08.json) |
| H — surfaces | `BLOCKED_MISSING_GOVERNED_INPUTS` | [historical_surfaces_2026-08-08.json](historical_surfaces_2026-08-08.json) |
| I — événements/régimes | `BLOCKED_MISSING_GOVERNED_EVENTS` | [event_regime_dataset_2026-08-08.json](event_regime_dataset_2026-08-08.json) |
| J — cinq scores | `BLOCKED_VALIDATION` | [five_scores_2026-08-08.json](five_scores_2026-08-08.json) |
| K — sévérité/gates | `BLOCKED_NO_CANDIDATE_DISTRIBUTION` | [severity_and_gate_sensitivity_2026-08-08.json](severity_and_gate_sensitivity_2026-08-08.json) |
| L — rapport final | `BLOCKED_BY_DATA` | [final_pre_opra_report_2026-08-08.html](final_pre_opra_report_2026-08-08.html) |

## Métriques réellement calculées

- `private_option_envelopes` : 1998
- `private_option_rows` : 46413
- `option_dates` : 250
- `price_observations` : 616
- `return_observations` : 615
- `annualized_realized_volatility` : 0.2965765
- `excess_kurtosis` : 6.96457
- `maximum_drawdown` : 0.27664
- `walk_forward_windows` : 7
- `comparable_strategy_panels` : 0
- `validated_surface_dates` : 0
- `governed_events` : 0

## Cinq scores indépendants

- `opportunity` : **unavailable**
- `risk` : **unavailable**
- `evidence` : **unavailable**
- `model_agreement` : **unavailable**
- `execution_quality` : **unavailable**

Meilleur candidat bloqué : `UNAVAILABLE`.

## Bloqueurs

- Historical option-data licensing remains to_review.
- No aligned comparable panel exists for all nine mandatory strategies.
- Historical IV/delta, governed rates and dividends are incomplete.
- No governed point-in-time event history exists.
- The five score formulas and thresholds remain draft_to_validate.
- The final holdout is unprovisioned and intentionally UNOPENED.

## Préparation OPRA future (phase M non démarrée)

- Obtain authorized OPRA access and document storage/redistribution rights.
- Ingest append-only raw snapshots with checksums and point-in-time timestamps.
- Run shadow/paper validation; do not add order capability.
- Keep Phase M separate and require explicit user validation before starting it.

## Reproductibilité

- Commit : `44ad47cb42e1ee6f1854e22b8678786cfe54dca6`
- Configuration : `629e654b6192f84d681f9e974c6b55934e873bd6df1c7d34554c4983775d6a49`
- Dataset : `0b09a9a9b1de6a9132e2f0eaf1a9cc15152d2fce59e40baefd21812c9886f556`
- Seed : `20260808`
- Commande : `.venv/bin/python scripts/build_pre_opra_final_report.py --generated-at 2026-08-08T20:30:00+02:00`
- Holdout : `UNOPENED`, jamais utilisé
- Capacité d'ordre : `forbidden`
