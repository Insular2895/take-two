# Phase 10 — integral validation and release review

Date: 2026-08-08

## Immediate decision

- Research-only release: `READY_RESEARCH_ONLY`.
- Financial/empirical promotion: `BLOCKED_MISSING_REAL_EVIDENCE`.
- Maximum end-to-end decision claim: `software_tested_only`.
- Execution: `order_capability=forbidden`.

The committed deterministic record is
[`validation/phase10_release_review.json`](../validation/phase10_release_review.json).

## Full gate result

| Check | Result |
| --- | --- |
| Pytest | 192 passed after Phase-10 test, one third-party deprecation warning |
| Ruff | passed |
| mypy strict | passed |
| pip check | no broken requirements |
| schema export | 6 schemas verified |
| offline artifacts | passed; calibration/backtest remain fixture-only |
| documentary lineage | 25/25 Formula IDs complete |
| release audit | deterministic committed review verified |
| security | all execution paths forbidden; no forbidden imports or `transmit=True` |

## Before/after comparison

The same local Python environment and machine ran both detached Phase-0 commit `f2f945e` and the
current tree once. This is a smoke comparison, not a statistically sound performance benchmark.

| Metric | Phase 0 | Phase 10 | Change |
| --- | ---: | ---: | ---: |
| Tests | 141 | 192 | +51 (+36.2%) |
| Pytest-reported time | 8.23 s | 8.81 s | +0.58 s (+7.0%) |
| Wall time (`/usr/bin/time`) | 9.11 s | 9.45 s | +0.34 s (+3.7%) |
| Source files covered by mypy | 124 | 142 after Phase-10 modules | +18 |
| Python files scanned by security | 121 | 137 | +16 |

No before/after predictive accuracy can be computed: there is no authorized aligned TTWO dataset,
active experiment manifest or clean holdout. The measurable improvement is validation coverage,
diagnostics, lineage and fail-closed behavior—not an asserted increase in forecast quality.

## Experiment replay

Active `ExperimentManifest` files found: zero. Replayed: zero. V7, V8 and V9 remain reproducible
only for historical/non-regression purposes and are explicitly contaminated. Creating an active
manifest or ledger entry now would fabricate data access, so the audit stops at the documented
blocker.

## Missing data

- licensed point-in-time TTWO option chains with bid/ask, open interest, volume and timestamps;
- aligned spot, corporate actions, dividends, rates and EUR/USD vintages;
- reviewed event labels with availability timestamps and dependency groups;
- real combo quotes, fills/rejections, commissions, spread and slippage;
- untouched final holdout identity/hash and a later paper-trading log.

## Technical debt

- legacy `Bayesian*` compatibility names;
- daily exit checkpoints that can miss intraday crossings;
- PBO full-text conformance still `to_review`;
- real SVI/Heston calibration and structural-break tests unexercised;
- candidate BOOK alias still awaiting user confirmation;
- third-party `websockets.legacy` deprecation warning.
