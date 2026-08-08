# Phase 10 documentary research — integral validation and claim audit

Date: 2026-08-08  
Status: `tested_research_release_only`

## Questions studied

- Does every software, numerical and financial claim remain below its actual evidence?
- Can every active experiment manifest be replayed without opening a final holdout?
- Did phases 1–9 materially regress the offline suite's runtime or safety boundary?
- Which missing data and technical debt block empirical, holdout and paper promotion?

## Sources and artifacts inspected

- Phase-0 baseline at Git commit `f2f945e` and the current Phase-9 head `3b5a0c2` plus the pending
  Phase-10 audit diff.
- All 25 canonical formula records, 30 documentary source records before the Phase-10 internal
  evidence entry, and the six-entry errata registry.
- The contaminated V7/V8/V9 manifest, `HOLDOUT_LEDGER_STATUS.md`, experiment directories, all
  committed fixtures/reports, schema exports and security scans.
- Existing book passages and primary/official sources already registered by phases 1–9. No new
  quantitative formula or external method was needed in this phase; no long PDF was reprocessed.

## Concepts and formulas retained

- Validation is a ladder: passing mechanics do not establish predictive accuracy.
- Reproducibility requires an active manifest binding code, config, dataset, split, trials and seed.
- Absence of a real manifest is a blocker, not permission to fabricate or replay a fixture as data.
- The release decision uses the weakest required evidence component and keeps execution forbidden.
- Formula IDs concerned: all 25 entries in `formula_registry.yaml`; no new formula.
- Measures: mixed `P/Q` by component; the audit never transforms or aggregates measures.

## Assumptions, alternatives, contradictions and limitations

Assumptions:

- the Git objects at `f2f945e` and current head are immutable comparison points;
- test elapsed times from one local run are descriptive only;
- authoritative claims are the structured registries, evidence sidecar and release review;
- no final holdout is opened during audit.

Alternatives rejected:

- fabricate an active experiment manifest from fixtures: would falsely imply a real dataset;
- promote legacy V7–V9 because they reproduce: their outcomes were already inspected;
- treat more tests as higher predictive accuracy: coverage and market validity are different;
- use a performance ratio from one timing run as a benchmark: too noisy and machine-specific.

Contradictions found:

- the requested “replay every experiment manifest” cannot run because there is no active manifest;
  the only legacy runs are explicitly contaminated. The audit records zero replayed manifests.
- isolated pricing/IV components can be numerically validated while the decision chain is only
  software-tested due to uncalibrated event/model inputs.
- the suite added 51 tests and the one-run pytest timing rose by 0.58 seconds (7.0%); this noisy
  smoke delta says nothing about end-to-end model scalability or predictive accuracy.

Limitations:

- no licensed real point-in-time option dataset;
- no clean final holdout ledger entry;
- no paper run, live combo fill/slippage sample or external methodology review;
- timing comparison has one run per revision and is not statistically benchmarked;
- the permanent `websockets.legacy` deprecation warning remains third-party debt.

## Choice, impact and validation

The final status is `READY_RESEARCH_ONLY`. Financial promotion is
`BLOCKED_MISSING_REAL_EVIDENCE`; the maximum decision claim is `software_tested_only`.

The deterministic release-audit module verifies registry promotion caps, active manifests,
contaminated holdouts, final-holdout status, the synthetic `NO_TRADE` example, missing data,
technical debt and the permanent order prohibition. Its committed JSON is checked byte-for-byte.

Expected impact: a future real-data campaign starts from explicit blockers and cannot silently
reuse contaminated evidence. Validation uses the full unit/property/integration/offline/security
gate plus `scripts/validate_research_registry.py` and `scripts/phase10_release_audit.py --check`.

Implementation: `src/take_two_options/validation/release_audit.py` and
`scripts/phase10_release_audit.py`. Test: `tests/test_phase10_release_audit.py`. Synthetic example:
`validation/phase10_release_review.json` (it deliberately selects the Phase-9 `NO_TRADE` report).
