# Pre-OPRA blocker closure ledger

This ledger records evidence produced before any OPRA connection. It never authorizes trading,
does not open the final holdout, and keeps licensed observations outside Git.

| Closure | Scope | Status | Evidence | Remaining limitation |
|---|---|---|---|---|
| C1 | Historical option normalization | CLOSED_FOR_LOCAL_RESEARCH | `reports/pre_opra/option_normalization_2026-08-08.json` | EOD quotes; vendor IV/Greeks absent; no simultaneous combo fills |
| C2 | Data rights and governance | PENDING | — | Provider terms and account rights to document |
| C3 | Spot, rates, dividends, FX | PENDING | — | Point-in-time alignment to complete |
| C4 | Governed event history | PENDING | — | Official event set to acquire |
| C5 | Comparable baseline panel | PENDING | — | Real comparable panel absent |
| C6 | Historical volatility surfaces | PENDING | — | Surface diagnostics absent |
| C7 | Empirical/GARCH/Heston models | PENDING | — | Empirical comparison absent |
| C8 | Final development walk-forward | PENDING | — | Final holdout remains unopened |
| C9 | Five quality scores | PENDING | — | Partial-coverage rules absent |
| C10 | Severity, gates and frontier | PENDING | — | Confidence intervals absent |
| C11 | Engine-vs-baseline verdict | PENDING | — | No evidence-backed verdict yet |
| C12 | Final dashboard and report | PENDING | — | Final artifacts not rebuilt |
| C13 | OPRA interface and paper record | PENDING | — | Live OPRA intentionally unavailable |

Invariants: `order_capability=forbidden`; `transmit=false`; `what_if=true`; final holdout
`UNOPENED`; no raw licensed record committed.
