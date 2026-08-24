# Phase M governed-context propagation — post-patch audit

Date: 2026-08-24

## Result

`COMPLETE`

The confirmed pre-patch gap is closed without changing quantitative formulas, scores, historical
artifacts, budget semantics, web formulas, or execution capability.

## Gap closure

| Requirement | Result | Evidence |
|---|---|---|
| One canonical typed context | `PASS` | `PhaseMDecisionContext` plus one builder and one loader helper. |
| Config loaded/validated once | `PASS` | Existing `load_prospective_budget_config` is reused; lifecycle is now required. |
| Deterministic hash/provenance | `PASS` | Stable config/context hashes, canonical sources, strict JSON round-trip. |
| Exact pipeline propagation | `PASS` | `analyze_trade` explicitly passes all five context-owned inputs and ID/hash. |
| No Phase M lifecycle default | `PASS` | Context/enumerator/factory fail with `PHASE_M_LIFECYCLE_CONTEXT_MISSING`. |
| No Phase M evidence reconstruction | `PASS` | Legacy request FX, ticket execution FX cost, and ticket margin broker fallbacks are disabled in Phase M mode. |
| Unknown FX cost | `PASS` | Research-visible, guarantee `UNPROVEN`, paper-ineligible, `FX_EXECUTION_COST_UNKNOWN`, null cost. |
| Same-currency FX | `PASS` | No FX object required; cost resolves `NOT_APPLICABLE`. |
| Broker capital | `PASS` | Validated €900 evidence produces `BROKER_BUYING_POWER`; absent evidence remains `UNKNOWN`. |
| Lifecycle consistency | `PASS` | Three-day buffer produces 2027-08-17 from 2027-08-20 across candidate, capital requirement, ticket, scenarios, breakeven, and target arrival. |
| Static config immutability | `PASS` | Pipeline and ticket tests compare pre/post serialized config/bundle. |
| Web compatibility | `PASS` | Optional context ID/hash added to dossier interface; 33 Worker tests and dry-run pass. |
| Legacy compatibility | `PASS` | Full 356-test Python suite passes; historical hash fixtures remain unchanged. |
| Security boundary | `PASS` | Security gate reports zero order imports and zero `transmit=true` literals. |

## Financial acceptance cases

- Converted entry cash €1,497 plus known FX cost €6 yields required cash €1,503 and
  `EXCEEDS_HARD_BUDGET_CEILING` against €1,500.
- Unknown required FX cost remains null and blocks paper eligibility without hiding the candidate
  from research.
- Validated broker buying power €900 is selected as lifecycle capital evidence for a mixed-expiry
  structure; removing it returns the lifecycle to `UNKNOWN`.

## Actual validation results

- `pytest -q`: 356 passed, one third-party deprecation warning.
- `ruff check .`: passed.
- `mypy src scripts`: passed, 191 source files.
- generated schema check: 30 schemas verified.
- offline artifact validation: passed.
- research registry: passed.
- Phase 10 release audit: passed.
- Phase 11 extension gate: passed.
- security gate: passed; 170 Python files scanned, zero forbidden order imports.
- Cloudflare: TypeScript, safety scan, and 33 Vitest tests passed.
- Wrangler production bundle dry-run: passed.

## Historical artifact regression

All six pre-recorded Phase M/M0/five-score SHA-256 values in the pre-patch audit match after the
patch. No historical report or golden ticket was regenerated.

## Remaining dependencies

- live read-only market-data evidence integration;
- real point-in-time FX/FX-cost and broker-capital snapshot acquisition;
- shadow prospective recording;
- paper prospective validation only after its separate authorization;
- final holdout remains unopened.

No remaining dependency is silently represented as complete.
