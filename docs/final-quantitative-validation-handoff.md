# Final handoff — TTWO quantitative validation phases 0–11

Date: 2026-08-08

## 1. Executive summary

The repository is complete as a guarded, read-only quantitative research engine. It is not a
validated trading strategy. The final statuses are:

- research software: `READY_RESEARCH_ONLY`;
- financial promotion: `BLOCKED_MISSING_REAL_EVIDENCE`;
- maximum end-to-end claim: `software_tested_only`;
- execution: `order_capability=forbidden`;
- advanced-model integration: `NO_ADVANCED_MODEL_IMPLEMENTATION`.

The work centralizes units and `P/Q`, validates pricing/IV mechanics, adds SVI and calibration
diagnostics, seals the experiment/holdout protocol, separates simulation/model/belief uncertainty,
computes whole-contract Pareto allocations with cash/`NO_TRADE`, makes event decisions sequential,
and publishes a weakest-link evidence report with complete formula lineage.

## 2. Final architecture

```text
market/evidence inputs (provenance + availability time)
  -> quantitative contracts (units, day count, P/Q)
  -> pricing / IV / SVI / calibration diagnostics
  -> event dependency graph + bounded scenario beliefs
  -> path simulation + chronological exit state + uncertainty
  -> whole-contract feasibility + robust objectives + Pareto frontier
  -> weakest-link evidence grade + static reports
  -> release and advanced-extension gates
  -> advisory output only; cash/NO_TRADE always possible
```

Key packages:

- `quantitative/`: contracts, numerical controls, IV, SVI, calibration and probability/model
  uncertainty;
- `simulation/`: exit state machine, variance reduction and interval diagnostics;
- `optimization/`: versioned objectives and exact finite integer Pareto frontier;
- `intelligence/`: point-in-time event dependencies, scenario sensitivity and integration;
- `validation/`: experiment manifests, holdout governance, release audit and extension gate;
- `reporting/`: complete decision-evidence sidecar and static network-free views;
- `docs/research/`: BOOK inventory, sources, formulas, errata and phase research.

## 3. Install, run and test

Installation:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

Offline synthetic execution:

```bash
.venv/bin/ttwo-options thesis-scan \
  --ticker TTWO \
  --direction bullish \
  --budget-eur 1000 \
  --catalyst-date 2026-11-19 \
  --expiration-buffer-days 45 \
  --target-prices 220,250,280,300,330,360 \
  --max-loss-eur 1000 \
  --top 3 \
  --current-chain fixtures/thesis_scanner/ttwo_synthetic_chain.json \
  --json-out reports/examples/v10_thesis_scan.json \
  --markdown-out reports/examples/v10_thesis_scan.md \
  --html-out reports/examples/v10_thesis_scan.html

.venv/bin/ttwo-options intelligence-run \
  --base-report reports/examples/v10_thesis_scan.json \
  --policy configs/intelligence/v11.yaml \
  --events fixtures/v11/events_empty.json \
  --profile fast_fixture \
  --json-out reports/v11/latest.json \
  --markdown-out reports/v11/latest.md \
  --html-out reports/v11/latest.html
```

Full validation:

```bash
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pip check
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/validate_research_registry.py
.venv/bin/python scripts/phase10_release_audit.py --check
.venv/bin/python scripts/phase11_extension_gate.py --check
.venv/bin/python scripts/security_gate.py
```

Final result: 194 tests passed; Ruff passed; strict mypy passed on 144 source files; dependencies
passed; six schemas passed; offline artifacts passed as fixtures only; 25 Formula IDs and 36
sources passed lineage; both deterministic reviews passed; security scanned 138 Python files with
zero forbidden imports, zero `transmit=True` and every execution path forbidden. The only warning
is the third-party `websockets.legacy` deprecation under Python 3.14.

## 4. Configurations and examples

- Default scanner config: [`configs/thesis_scanner/default.yaml`](../configs/thesis_scanner/default.yaml).
- Intelligence config: [`configs/intelligence/v11.yaml`](../configs/intelligence/v11.yaml).
- Final evidence example: [`reports/examples/phase9_final_evidence.json`](../reports/examples/phase9_final_evidence.json).
- `NO_TRADE` example: report `phase9-synthetic-no-trade`; event probabilities are not empirically
  validated, so cash is preferred.
- Synthetic ranked-strategy examples in `v10_thesis_scan.json`: prudent bull call spread 230/250
  March 2027, balanced long call 280 March 2027 and aggressive long call 300 March 2027. Every one
  remains `watchlist`; these are examples of deterministic ranking, not retained trades.
- Real example: none was added because no authorized aligned dataset/manifest/fresh holdout is
  available. Legacy V7–V9 results remain explicitly contaminated and non-promotional.

## 5. Before/after

The one-run local smoke comparison is descriptive, not a benchmark:

| Metric | Baseline commit `f2f945e` | Phase 10 | Change |
| --- | ---: | ---: | ---: |
| tests | 141 | 192 | +51 (+36.2%) |
| pytest time | 8.23 s | 8.81 s | +0.58 s (+7.0%) |
| wall time | 9.11 s | 9.45 s | +0.34 s (+3.7%) |
| mypy source files | 124 | 142 | +18 |
| security Python files | 121 | 137 | +16 |

Phase 11 ends at 194 tests, 144 typed files and 138 security-scanned files. Predictive accuracy
cannot be compared because there is no active real-data experiment manifest or clean holdout.

## 6. Limits, debt and missing data

Remaining technical debt:

- legacy `Bayesian*` names retained for compatibility;
- daily exit checkpoints can miss intraday crossings;
- full-text PBO conformance remains `to_review`;
- real SVI/Heston calibration and structural-break diagnostics remain unexercised;
- the candidate BOOK alias still awaits user confirmation;
- upstream `websockets.legacy` deprecation warning.

Required data before empirical/holdout/paper promotion:

- licensed point-in-time TTWO chains with bid/ask, OI, volume and timestamps;
- aligned spot, corporate actions, dividends, rates and EUR/USD vintages;
- reviewed event labels with availability timestamps and dependency groups;
- real combo quotes, fills/rejections, commissions, spreads and slippage;
- an untouched final-holdout identity/hash followed by a paper-trading log.

Next useful improvements are therefore a governed real-data campaign, real baseline calibration,
an active manifest, nested chronological OOS comparison, one-time final holdout and paper run—not
another pricing model.

## 7. Sources, contradictions and deliberately absent models

- BOOK inventory: [`research/book_inventory.md`](research/book_inventory.md) and
  [`research/book_inventory.json`](research/book_inventory.json). It correctly groups the eleven
  Bergomi fragments as one incomplete work and the three rate files as partial Volumes I–II.
- Source register: [`research/source_registry.yaml`](research/source_registry.yaml).
- Formula/source/code/test matrix:
  [`research/formula_lineage_matrix.md`](research/formula_lineage_matrix.md).
- Methodological contradictions and corrections:
  [`research/errata_registry.yaml`](research/errata_registry.yaml).
- Per-component evidence levels: [`research/2026_validity_audit.md`](research/2026_validity_audit.md).

Still useful to obtain: the missing Gatheral book, Shreve Volume II, Andersen–Piterbarg Volume III
and accessible PBO full text. Primary papers already substitute for the missing SVI/rough-volatility
claims actually used.

Phase 11 deliberately integrates no model. Bergomi, rough Bergomi, Bayesian filtering, eSSVI,
learned regimes, hierarchical event Bayes, Longstaff–Schwartz and Sobol/QMC are deferred. Advanced
rates/HJM/LMM, higher-order Greeks/AAD and neural surfaces are rejected only for the current scope.
The exact blockers and reversible reconsideration gates are in
[`phase-11-extension-evaluation.md`](phase-11-extension-evaluation.md).

Bergomi could become useful for forward-variance and smile dynamics only after a validated
Heston/SVI baseline and dense multi-date TTWO surfaces show stable incremental OOS pricing or
ranking value. Advanced rates become useful only if stochastic-curve sensitivity materially
changes TTWO option prices/ranks versus the deterministic Treasury curve. Neither condition is
currently demonstrated.

## 8. Exact repository file manifest

Comparison base: `178cfe8d3a3c3c882798775384c96570e04fda2b` (parent of Phase 0). This handoff
adds 69 files and modifies 27, for 96 changed paths including this document.

### Created

- `docs/final-quantitative-validation-handoff.md`
- `docs/math/README.md`
- `docs/phase-10-release-review.md`
- `docs/phase-11-extension-evaluation.md`
- `docs/phase-2-iv-svi-example.md`
- `docs/phase-3-calibration-example.md`
- `docs/phase-4-validation-protocol-example.md`
- `docs/phase-5-simulation-uncertainty-example.md`
- `docs/phase-6-model-uncertainty-example.md`
- `docs/phase-7-allocation-pareto-example.md`
- `docs/phase-8-event-sequential-example.md`
- `docs/phase-9-final-evidence-example.md`
- `docs/research/2026_validity_audit.md`
- `docs/research/book_inventory.json`
- `docs/research/book_inventory.md`
- `docs/research/errata_registry.yaml`
- `docs/research/formula_lineage_matrix.md`
- `docs/research/formula_registry.yaml`
- `docs/research/phase-1-documentary-research.md`
- `docs/research/phase-10-documentary-research.md`
- `docs/research/phase-11-documentary-research.md`
- `docs/research/phase-2-documentary-research.md`
- `docs/research/phase-3-documentary-research.md`
- `docs/research/phase-4-documentary-research.md`
- `docs/research/phase-5-documentary-research.md`
- `docs/research/phase-6-documentary-research.md`
- `docs/research/phase-7-documentary-research.md`
- `docs/research/phase-8-documentary-research.md`
- `docs/research/phase-9-documentary-research.md`
- `docs/research/source_registry.yaml`
- `docs/superpowers/plans/2026-08-08-ttwo-quantitative-validation-v10.md`
- `docs/superpowers/specs/2026-08-08-ttwo-quantitative-validation-v10-design.md`
- `docs/testing_strategy.md`
- `reports/examples/phase9_final_evidence.json`
- `scripts/phase10_release_audit.py`
- `scripts/phase11_extension_gate.py`
- `scripts/validate_research_registry.py`
- `src/take_two_options/intelligence/event_scenarios.py`
- `src/take_two_options/intelligence/sequential_decision.py`
- `src/take_two_options/optimization/allocation_pareto.py`
- `src/take_two_options/quantitative/__init__.py`
- `src/take_two_options/quantitative/calibration.py`
- `src/take_two_options/quantitative/contracts.py`
- `src/take_two_options/quantitative/implied_volatility.py`
- `src/take_two_options/quantitative/model_uncertainty.py`
- `src/take_two_options/quantitative/numerical_validation.py`
- `src/take_two_options/quantitative/probability_calibration.py`
- `src/take_two_options/quantitative/svi.py`
- `src/take_two_options/reporting/evidence_grade.py`
- `src/take_two_options/simulation/exit_state.py`
- `src/take_two_options/simulation/uncertainty.py`
- `src/take_two_options/validation/experiment_protocol.py`
- `src/take_two_options/validation/extension_evaluation.py`
- `src/take_two_options/validation/release_audit.py`
- `tests/test_allocation_pareto.py`
- `tests/test_evidence_grade_reporting.py`
- `tests/test_implied_volatility_svi.py`
- `tests/test_model_uncertainty.py`
- `tests/test_phase10_release_audit.py`
- `tests/test_phase11_extension_evaluation.py`
- `tests/test_quantitative_calibration.py`
- `tests/test_quantitative_foundations.py`
- `tests/test_sequential_event_decision.py`
- `tests/test_simulation_uncertainty.py`
- `tests/test_validation_protocol_v10.py`
- `validation/HOLDOUT_LEDGER_STATUS.md`
- `validation/holdout_protocol_v10.yaml`
- `validation/phase10_release_review.json`
- `validation/phase11_extension_review.json`

### Modified

- `.github/workflows/offline-validation.yml`
- `README.md`
- `docs/LIMITATIONS.md`
- `docs/MODEL_RISK.md`
- `docs/architecture/V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md`
- `docs/known_limits.md`
- `src/take_two_options/accuracy.py`
- `src/take_two_options/american.py`
- `src/take_two_options/calibration.py`
- `src/take_two_options/forecasting/regimes.py`
- `src/take_two_options/intelligence/__init__.py`
- `src/take_two_options/intelligence/bayesian.py`
- `src/take_two_options/intelligence/calibration.py`
- `src/take_two_options/intelligence/optimizer.py`
- `src/take_two_options/intelligence/pipeline.py`
- `src/take_two_options/intelligence/reporting.py`
- `src/take_two_options/intelligence/schemas.py`
- `src/take_two_options/intelligence/stochastic.py`
- `src/take_two_options/intelligence/valuation.py`
- `src/take_two_options/intelligence/volatility_calibration.py`
- `src/take_two_options/pricing.py`
- `src/take_two_options/simulation/conditional_monte_carlo.py`
- `src/take_two_options/simulation/legacy_models.py`
- `src/take_two_options/simulation/path_execution.py`
- `src/take_two_options/validation/pbo.py`
- `src/take_two_options/validation/placebo.py`
- `tests/test_intelligence_v11.py`

The phase-by-phase atomic commits are listed in the implementation plan. No push, merge or remote
branch mutation is part of this handoff.
