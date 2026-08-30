# PRE-OPRA Quantitative Engine Consolidation Report

Report date: 2026-08-30

Branch: `codex/m-ibkr-paper-control-readonly`

Scope: offline/read-only quantitative consolidation; no deployment or broker mutation

## 1. Files changed

Core orchestration and public boundary:

- `src/take_two_options/__init__.py`
- `src/take_two_options/decision/pipeline.py`
- `src/take_two_options/legacy_cli.py`
- `src/take_two_options/cloud/research_workbench.py`

Canonical economics, contracts and normalized data:

- `src/take_two_options/quantitative/contracts.py`
- `src/take_two_options/quantitative/pricing.py` (new)
- `src/take_two_options/quantitative/costs.py` (new)
- `src/take_two_options/pricing.py`
- `src/take_two_options/knowledge/schemas.py`
- `src/take_two_options/market_snapshot.py`
- `fixtures/portability/xyz_option_chain.json`

Candidate, simulation, optimization and decision consumers:

- `src/take_two_options/candidate_generation/{enumerator,factory,pruning}.py`
- `src/take_two_options/simulation/{conditional_monte_carlo,evaluation,exit_state,legacy_models,model_ensemble,path_execution}.py`
- `src/take_two_options/optimization/{coarse_search,fine_search,pareto}.py`
- `src/take_two_options/decision/{ranking,verdict}.py`
- `src/take_two_options/validation/stress.py`
- `src/take_two_options/intelligence/{robustness,validation,valuation}.py`
- `src/take_two_options/thesis_scanner/{enumeration,pricing,ranking,reporting,schemas}.py`
- `src/take_two_options/reporting/{decision_report,visualizations}.py`

Tests and repaired historical documentation:

- `tests/test_pre_opra_consolidation.py` (new)
- `tests/test_{budget_policy,engine,engine_v2,knowledge_optimizer,offline_reliability_v11,phase_m_context,portability_xyz,simulation_uncertainty,thesis_scanner,trade_economics}.py`
- `docs/audits/HARDCODED_VALUE_AUDIT.md`
- `docs/audits/V9_REUSE_AUDIT.md`
- `reports/M0_GREEKS_CARRY_HARDENING_REPORT.md`
- `reports/PHASE_M_CONTEXT_PROPAGATION_REPORT.md`
- `reports/PRE_OPRA_ENGINE_CONSOLIDATION_REPORT.md` (new)

## 2. Files deleted

- `src/take_two_options/engine.py`
- `src/take_two_options/scoring.py`

Neither file remains behind as a compatibility wrapper.

## 3. Legacy consumers migrated

- The package export and CLI now import `analyze_trade` directly from
  `take_two_options.decision.pipeline`.
- Engine tests now exercise the canonical pipeline and assert both legacy modules are absent.
- Candidate selection consumers use structural vetoes, explicit eligibility, Pareto rank and the
  secondary explanatory ranking; the legacy score cannot influence a verdict.
- V10/V11 and Phase M report/schema readers accept older artifacts through explicit migrations
  that preserve missingness and label legacy risk evidence `UNVALIDATED` rather than recreating
  formulas.

## 4. Canonical pipeline

`src/take_two_options/decision/pipeline.py` is the sole authoritative orchestration:

```text
normalized snapshot -> candidate generation -> canonical economics -> P simulation
-> risk and eligibility -> hard vetoes -> Pareto -> explanatory ranking
-> validation gates -> verdict/report
```

Candidate-level arithmetic/numerical failures are recorded as `BLOCKED` and do not abort the
remaining batch.

## 5. Canonical pricing path

`quantitative/pricing.py` now owns the minimal provider-independent interface. It requires an
explicit contract, normalized market state, valuation timestamp and volatility state. Rates,
continuous/discrete dividends, exercise style, multiplier, deliverable and adjustment evidence
are validated before whole-contract economics.

Authoritative American and European valuation continues through the existing QuantLib finite-
difference implementation. Path execution no longer contains `_option_value`; it calls the same
canonical interface. The optional batch fast path is restricted to European options without
discrete dividends and non-dividend American calls where European equivalence holds. Unsupported
American/dividend domains fall back to authoritative pricing. Deterministic parity tests use
`abs(error) <= 0.002 + 0.002 * abs(reference)`.

## 6. Exact empirical GBM correction

Historical inputs are log returns. The real-world step is now exactly:

```text
S_next = S_current * exp(mean_log_return + daily_log_return_volatility * Z)
```

The erroneous second `-0.5 * sigma^2` adjustment was removed. The risk-neutral generator remains
unchanged and correctly uses `r - q - 0.5 * sigma^2`.

## 7. Model eligibility rules

- Every simulation/model result carries both `Measure` and `ModelEligibility`.
- Option values and Greeks are Q / `RISK_NEUTRAL`; real-world expected PnL and probabilities must
  be P / `REAL_WORLD`.
- Only P-measure `DECISION_ELIGIBLE` results can enter conservative EV, loss probabilities,
  Pareto, ranking or verdict statistics.
- Q results, legacy Q models, unvalidated bootstrap/Heston/Merton-style stresses and other
  diagnostics remain visible but cannot drive a decision.
- With no eligible P model, the decision statistic is null and status is `BLOCKED`; there is no
  diagnostic fallback.
- Non-finite metrics are rejected at the schema/decision boundary.

## 8. Mixed-expiry corrections

For calendars, diagonals and other mixed-expiry structures, the common-terminal payoff grid is
retained only as an explicitly diagnostic proxy. It no longer masquerades as lifecycle maximum
loss. Unless lifecycle capital is evidenced:

- `maximum_loss = null` with `maximum_loss_status = UNKNOWN`;
- capital-dependent selection is `BLOCKED`;
- `return_on_risk = null`.

Mandatory exit before first expiry remains an operational scenario policy, not proof of broker
margin.

## 9. Cost reconciliation

`quantitative/costs.py` centralizes the exact-once equation:

```text
GrossPnL
- entry bid/ask cost
- exit bid/ask cost
- entry slippage
- exit slippage
- commissions
- exercise/assignment/settlement costs
- FX costs
= NetPnL
```

Each component preserves its evidence level. Any required unknown component keeps net PnL null;
unknown is never converted to zero. Path execution and reporting consume this reconciliation and
do not subtract the same component independently.

## 10. PRE-OPRA data boundary

The provider-independent `MarketSnapshot`/`QuoteSnapshot` boundary now preserves snapshot/source
IDs, exchange/provider/receive timestamps, quote fields, exercise style, multiplier evidence,
deliverable/adjustment evidence, rate/dividend evidence, freshness state, schema version, dataset
ID/hash and deterministic run lineage. Provider payloads remain outside pricing. No arbitrary
freshness TTL was added.

## 11. Tests added or strengthened

Focused regression coverage includes:

- empirical log-return drift and unchanged Q drift;
- explicit and deterministic P/Q paths;
- canonical rate/dividend/American semantics;
- supported fast/reference parity and unsupported-domain fallback;
- explicit multiplier and fail-closed adjusted-contract handling;
- canonical path repricing;
- decision-eligible ensemble filtering and null result without eligible P models;
- mixed-expiry unknown lifecycle risk and null return on risk;
- exact-once and unknown cost reconciliation;
- NaN/Inf rejection and per-candidate numerical isolation;
- blocked validation without real data, unopened holdout and deletion of legacy imports.

## 12. Commands run

```text
.venv/bin/ruff check .
.venv/bin/mypy src scripts
.venv/bin/pytest -q
.venv/bin/python scripts/export_offline_schemas.py --check
.venv/bin/python scripts/validate_offline_artifacts.py
.venv/bin/python scripts/validate_research_registry.py
.venv/bin/python scripts/phase10_release_audit.py --check
.venv/bin/python scripts/phase11_extension_gate.py --check
.venv/bin/python scripts/security_gate.py
.venv/bin/ttwo-options intelligence-run ... --profile fast_fixture ...
.venv/bin/ttwo-options calibration report ...
.venv/bin/ttwo-options position replay ...
.venv/bin/python -m pip check
cd cloudflare && npm ci && npm run check
cd cloudflare && npx wrangler deploy --dry-run --outdir <temporary-directory>
```

## 13. Validation results

| Gate | Result |
| --- | --- |
| Ruff | PASS |
| mypy strict | PASS — 195 source files |
| pytest | PASS — 390 tests; one third-party deprecation warning |
| JSON Schemas | PASS — 34 committed schemas verified |
| Offline fixture/artifact validation | PASS; calibration remains fixture-only and not calibrated |
| Research registry/lineage | PASS |
| Phase 10 deterministic release review | PASS |
| Phase 11 deterministic extension gate | PASS |
| Security boundary | PASS — 173 Python files; zero forbidden order imports, zero `transmit=true` literals |
| Deterministic fixture reports | PASS — intelligence, calibration and position replay |
| Cloudflare control-plane check | PASS — 7 files / 63 tests |
| Cloudflare deployment bundle | PASS — local dry-run only; nothing deployed |
| Dependency consistency | PASS |

## 14. Intentionally unresolved statuses

- `UNVALIDATED`: real-world iid conditioned bootstrap, configured/frozen volatility behavior,
  configured slippage and uncalibrated scenario parameters.
- `DIAGNOSTIC_ONLY`: legacy Q models and uncalibrated advanced model stresses.
- `INSUFFICIENT_DATA`: SVI/eSSVI or calibration paths lacking the required real observations.
- `BLOCKED`: historical calibration, walk-forward promotion, lifecycle capital with missing
  evidence, missing contract economics/costs and any decision with no eligible P model.
- `FINAL_HOLDOUT`: `UNOPENED_UNPROVISIONED`.

## 15. Scope confirmation

- The final holdout was not opened or consumed.
- No OPRA/provider integration was implemented.
- No broker/paper execution, credentials, order placement or account mutation was implemented.
- No new speculative volatility dynamics or global eSSVI calibration was implemented.
- No Heston/Merton or other calibration values were fabricated.
- No training, validation, test or holdout dataset was fabricated.
- No Cloudflare, Oracle or IBKR runtime was changed or restarted during this consolidation.
