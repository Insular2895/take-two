# Phase M-CF0.2 — Cloud Research Workbench

Date: 2026-08-25
Base commit audited: `3942b2e31bad33dd32ed19aa514ae51acbe7cc24`
Implementation commit: not created or pushed by this task.

## Result

The private Cloudflare application now includes a Research workspace that can create an immutable
budget request, dispatch the fixed Python job through GitHub Actions, receive signed candidate
batches, persist the complete candidate universe in D1, and create an immutable `PLANNED` dossier
from a paper-eligible selection. The existing Position workspace remains present.

No live provider, OPRA entitlement, broker credentials, IBKR connection, opening-order API, paper
execution, holdout, or order transmission was enabled.

## Initial audit and architecture

CF0/CF0.1 previously began only after a local Python dossier export. The missing pre-trade path is
now:

```text
Access + CSRF + action password
→ exact AnalysisBudgetRequest in D1
→ fixed GitHub workflow dispatch (analysis ID only)
→ canonical Python catalog/request/BudgetPolicyV2/PhaseMDecisionContext
→ signed batches of 20 summaries + details
→ D1 completeness check
→ full browser explorer
→ immutable selection + PLANNED dossier
```

D1 is the application truth; GitHub is replaceable compute. After deployment and secret setup, the
Mac and VS Code are not needed to launch `SYNTHETIC_DEMO` or a configured governed-snapshot job.

## UI

- top navigation: `RESEARCH` / `POSITION`;
- preferred/target/maximum budget, SOFT/HARD minimum, and approved data-mode selector;
- durable history and truthful named progress steps, with no fake percentage;
- six views: best overall, best by architecture, top 100, all, paper eligible, research only;
- responsive cards, details drawer, up-to-four comparison, pagination, search, active filter chips,
  and reset;
- 36 user-sort metrics with explicit semantic direction and independent ascending/descending order;
- engine rank and current user rank shown separately;
- six deterministic post-filter heatmap bands from strong green to red; N/A neutral;
- conceptual `EXÉCUTER` control reports `IBKR EXECUTION NOT CONFIGURED`.

Unavailable model outputs remain null/N/A with reasons. The browser never reprices options and
does not synthesize theta paths, probability, CVaR, scenario matrices, or five scores.

## Budget semantics

The default €800 / €1,000 / €1,500 UI maps exactly to V2:

- `target_budget=1000`;
- `under_target_tolerance=200`;
- `max_overspend=500`;
- preferred lower bound €800;
- hard authorized ceiling €1,500;
- `minimum_spend_policy=SOFT` or `HARD` unchanged.

Unknown fields, NaN/infinity, non-positive money, non-EUR currency, and invalid ordering fail
closed. Exact-ceiling and one-cent-over regressions pass.

## Synthetic candidate universe

One deterministic actual run produced:

| Metric | Count |
|---|---:|
| generated and persisted/browsable | 600 |
| hard-vetoed but retained with reasons | 570 |
| research-visible | 600 |
| paper eligible | 8 |
| detail payloads | 600 |
| best-overall projection | 25 |

Architecture counts: long call 36, long put 36, bull call spread 42, bear put spread 42, call
butterfly 12, put butterfly 12, call broken-wing butterfly 12, put broken-wing butterfly 12, call
calendar 36, put calendar 36, call diagonal 84, put diagonal 84, long straddle 18, long strangle 42,
and iron condor 96.

The engine rank uses hard vetoes, paper eligibility, canonical Pareto rank, budget distance,
maximum loss, and candidate ID. It does not add a composite/sixth score. A separate regression
forces an impossible €1 hard ceiling and confirms terminal `NO_TRADE` while retaining the generated
universe.

## Filters, sorting, heatmap, comparison

Filter catalogue: multi-architecture, budget status, capital range, target distance, debit/credit,
expected PnL/return, maximum profit, probability loss/profit, maximum loss, VaR/CVaR, DTE,
theta, four flat-spot horizons, IV, spread, open interest, five score minima, freshness, common/mixed
expiry, and literal search. Activating a numeric filter excludes N/A instead of treating it as zero.

Sort catalogue has 36 raw metrics across engine, return, probability, capital, risk, time, market,
Greeks, and the five independent score dimensions. Filtering precedes sorting and heatmap percentile
calculation; pagination follows all three. Comparison shows raw fields only and never creates a
score or changes rank.

## D1 and security

Additive migrations `0005` and `0006` add analysis requests/runs, complete compact summaries,
details, selections, planned dossiers, callback nonces, filter metrics, indexes, append-only
triggers, and immutable-input triggers. One partial unique index admits a single active analysis.

The Worker fixes repository `Insular2895/take-two`, workflow
`phase-m-research-analysis.yml`, and governed ref `main`; the browser sends no such values. GitHub
receives only `analysis_request_id`. The callback combines a Cloudflare Access service token with
HMAC-SHA256 over timestamp, nonce, analysis ID, method, path, and body hash. The Worker enforces a
five-minute window, unique persisted nonce, 512 KiB body cap, 20-candidate batch cap, strict IDs,
Git provenance, retry idempotency, and final persisted-count equality.

## Actual validation

- Python: `372 passed`, one third-party deprecation warning;
- Ruff: pass;
- strict mypy: pass, 195 source files (local Python 3.14 environment override; project CI remains
  configured for Python 3.11);
- schemas: 34 generated and checked;
- offline artifacts, research registry, Phase 10 release review, Phase 11 gate: pass;
- security gate: pass, 173 Python files scanned, zero forbidden order imports, zero
  `transmit=true` literals;
- Cloudflare: TypeScript, safety scan, and `51` Vitest tests pass;
- D1 local migrations `0005` and `0006`: pass;
- Wrangler deploy dry-run: pass, 184.45 KiB upload / 44.45 KiB gzip;
- workflow YAML/permissions/input/signature-contract tests: pass;
- local Worker HTTP: dashboard, application module, research-state module, styles, and Research API
  returned 200; JavaScript syntax checks pass;
- automated visual browser check: not run because `agent-browser` is absent from this environment.

## Historical freeze

The recorded hashes for M0, M0.1, M0.2, M0.2.1, and the golden trade-economics ticket exactly
match CF0.1. No five-score formula, historical result, ranking, model tuning, OOS artifact, or
holdout input changed. `HOLDOUT=UNOPENED`.

## Free-tier implications and remaining dependencies

One synthetic run writes about 1,200 candidate rows before indexes, plus lifecycle/audit rows.
Cloudflare currently provides finite daily Free allowances and a 500 MB per-D1 database limit;
repeated large snapshots must be measured. GitHub Actions is free for public repositories, while
private repositories consume plan-specific included minutes and can incur charges. Zero cost is
therefore conditional, not guaranteed.

Remaining operational work: merge/push workflow to the default branch, set Worker and GitHub
secrets, add the Access Service Auth policy, apply remote D1 migrations, deploy, and perform the
real authenticated end-to-end GitHub callback run. Live OPRA/provider rights, shadow validation,
IBKR execution review, paper execution, prospective validation, and holdout remain future phases.

## Files changed

- GitHub runner: `.github/workflows/phase-m-research-analysis.yml`.
- Python engine/contracts/callback: `src/take_two_options/cloud/research_*.py` and
  `scripts/run_cloud_research_analysis.py`.
- D1/Worker: `cloudflare/migrations/0005_phase_m_research_workbench.sql`,
  `cloudflare/migrations/0006_research_candidate_filter_metrics.sql`,
  `cloudflare/src/research-*.ts`, `cloudflare/src/future-broker-types.ts`, and integration/config
  updates.
- Browser workbench: `cloudflare/public/dashboard.txt`, `app.txt`, `styles.txt`, and
  `research-state.{js,txt}`.
- Schemas/tests: four `schemas/*research*.schema.json` or budget/result schemas, Python/Worker/UI
  tests, and offline-schema registry updates.
- Specifications/audit: `docs/specs/CF0_*.md`, `docs/specs/FUTURE_BROKER_EXECUTION_PROVIDER.md`,
  and `docs/audits/PHASE_M_CF0_2_RESEARCH_WORKBENCH_AUDIT.md`.
- Reports: this Markdown report and `reports/PHASE_M_CF0_2_RESEARCH_WORKBENCH.json`.

## Final status

```text
CF0_RESEARCH_WORKBENCH = READY_LOCALLY
CF0_BUDGET_CONFIGURATOR = READY
CF0_ANALYSIS_LAUNCHER = READY_PENDING_REMOTE_CONFIGURATION
CF0_CANDIDATE_EXPLORER = READY
CF0_ALL_ADMISSIBLE_COMBINATIONS_VIEW = READY
CF0_FILTER_ENGINE = READY
CF0_SORT_ENGINE = READY
CF0_DYNAMIC_HEATMAP = READY
CF0_CANDIDATE_DETAIL = READY
CF0_CANDIDATE_COMPARISON = READY
CF0_NO_TRADE_UI = READY
CF0_CANDIDATE_SELECTION = READY
CF0_PLANNED_POSITION_FLOW = READY
PHASE_M_CONTEXT_PROPAGATION = COMPLETE
LIVE_MARKET_DATA = NOT_CONFIGURED
IBKR_EXECUTION = NOT_CONFIGURED
ORDER_TRANSMISSION = FORBIDDEN
HOLDOUT = UNOPENED
```
