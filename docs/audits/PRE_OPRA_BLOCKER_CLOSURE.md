# Pre-OPRA blocker closure ledger

This ledger records evidence produced before any OPRA connection. It never authorizes trading,
does not open the final holdout, and keeps licensed observations outside Git.

| Closure | Scope | Status | Evidence | Remaining limitation |
|---|---|---|---|---|
| C1 | Historical option normalization | CLOSED_FOR_LOCAL_RESEARCH | `reports/pre_opra/option_normalization_2026-08-08.json` | EOD quotes; vendor IV/Greeks absent; no simultaneous combo fills |
| C2 | Data rights and governance | CLOSED_WITH_HUMAN_CONFIRMATIONS | `docs/data/DATA_USAGE_RIGHTS.md`; `reports/pre_opra/data_usage_rights_2026-08-08.json` | Account classification and grants remain subscriber confirmations |
| C3 | Spot, rates, dividends, FX | CLOSED_FOR_DEVELOPMENT | `reports/pre_opra/market_context_2026-08-08.json` | IEX rather than SIP; conservative next-day availability lags |
| C4 | Governed event history | CLOSED_FOR_DEVELOPMENT | `reports/pre_opra/event_regime_dataset_2026-08-08.json` | Official subset, not an exhaustive causal event ontology |
| C5 | Comparable baseline panel | CLOSED_DIAGNOSTIC | `reports/pre_opra/baseline_comparison_2026-08-08.json` | Short-DTE development panel; account rights confirmation; not final holdout |
| C6 | Historical volatility surfaces | CLOSED_DIAGNOSTIC | `reports/pre_opra/historical_surfaces_2026-08-08.json` | 50 calendar-arbitrage violations, 21 failed snapshots, rights confirmation; Heston blocked |
| C7 | Empirical/GARCH/Heston models | CLOSED_DIAGNOSTIC | `reports/pre_opra/empirical_calibration_2026-08-08.json` | One development split; Heston blocked; rights confirmation |
| C8 | Final development walk-forward | CLOSED_DIAGNOSTIC | `reports/pre_opra/walk_forward_protocol_2026-08-08.json` | 25 observations vs 41 formal minimum; holdout remains UNOPENED |
| C9 | Five quality scores | CLOSED_DIAGNOSTIC | `reports/pre_opra/five_scores_2026-08-08.json` | Low confidence; holdout/rights/live execution remain missing |
| C10 | Severity, gates and frontier | CLOSED_DIAGNOSTIC | `reports/pre_opra/severity_and_gate_sensitivity_2026-08-08.json` | Wide intervals; thresholds remain draft; OPRA execution pending |
| C11 | Engine-vs-baseline verdict | PENDING | — | No evidence-backed verdict yet |
| C12 | Final dashboard and report | PENDING | — | Final artifacts not rebuilt |
| C13 | OPRA interface and paper record | PENDING | — | Live OPRA intentionally unavailable |

Invariants: `order_capability=forbidden`; `transmit=false`; `what_if=true`; final holdout
`UNOPENED`; no raw licensed record committed.
