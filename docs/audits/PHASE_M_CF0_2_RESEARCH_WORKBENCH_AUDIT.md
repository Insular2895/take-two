# Phase M-CF0.2 Research Workbench audit

Date: 2026-08-25

## Initial audit

The existing CF0/CF0.1 application could import and monitor a canonical position but could not
launch the canonical Python search, persist an analysis lifecycle, expose all generated candidates,
or turn a selected result into a non-active planned dossier. Running research still depended on a
local terminal.

The following boundaries already worked and were retained: Cloudflare Access, CSRF, action password,
D1 and Durable Object position state, Safe Mode, signed position economics, oldest-required-data
freshness, whole-combo close preview, manual close reconciliation, and forbidden order transmission.

## Audit results

| Area | Result | Evidence / limitation |
|---|---|---|
| Candidate exhaustiveness | PASS | All 600 combinations from the deterministic synthetic catalog/request universe are returned and persisted; 570 vetoed rows remain browsable. |
| Budget semantics | PASS | Exact preferred/target/max → V2 tolerance mapping; SOFT/HARD and hard-ceiling regression tests. |
| Ranking immutability | PASS | Python writes `engine_rank`; browser only sorts copies and never writes rank. |
| Sort/filter separation | PASS | Pure browser-state tests cover independent sort, full-set filters, views, and pagination. |
| Heatmap | PASS | Post-filter percentile population, direction inversion, null-neutral behavior, and explicit direction labels. |
| Details | PASS | One detail row and route for every summary; absent modeled metrics remain null/N/A. |
| Comparison | PASS | Client-side maximum four, raw metrics, no composite score. |
| NO_TRADE | PASS | Terminal state, reasons, history, and UI wording are first-class. |
| D1 persistence | PASS | Additive migration, one-active unique index, immutable inputs/runs/selections/plans. |
| Workflow dispatch | PASS | Fixed repo/workflow/ref; only analysis ID input; no browser shell interpolation. Deployment token still required. |
| Callback security | PASS | Access service-token design plus HMAC timestamp, nonce, ID, method, path and body hash; replay/tamper/expiry tests. |
| Selection | PASS | Provenance-bound immutable selection and separate PLANNED dossier; no active position created. |
| Future execution boundary | PASS | Inert type descriptors and status endpoint only; no implementation or opening fallback. |
| Existing CF0 compatibility | PASS | Existing 43 Cloudflare tests remain green within the expanded 51-test suite. |

## Limitations and active dependencies

- `SYNTHETIC_DEMO` is a modeled fixture, not market evidence. Its simplified delta is illustrative;
  theta, expected PnL, probability, CVaR, robustness, and five scores remain N/A.
- `LAST_GOVERNED_SNAPSHOT` requires a committed snapshot path in the runner environment; it fails
  closed when absent.
- GitHub and Cloudflare secrets, an Access Service Auth policy, migration application, deployment,
  and workflow presence on the default branch remain operational setup tasks.
- GitHub-hosted runner cost is plan/repository dependent. “Zero cost” is not a guaranteed property.
- Live data/OPRA, broker credentials, IBKR execution, paper validation, and holdout access remain out
  of scope and unconfigured.

## Historical freeze

No historical OOS artifact, M0/M0.1/M0.2/M0.2.1 logic, five-score formula, historical rank, model
parameter, or holdout input was intentionally modified. Final hash regression and full repository
gates are recorded in the phase report. `HOLDOUT=UNOPENED`.
