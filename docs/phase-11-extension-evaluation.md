# Phase 11 — advanced extension evaluation

Date: 2026-08-08

## Decision

No advanced model is integrated. The deterministic review is committed at
[`validation/phase11_extension_review.json`](../validation/phase11_extension_review.json).

| Current status | Extensions |
| --- | --- |
| `defer` | Bergomi, rough Bergomi, Bayesian filtering, eSSVI, learned regimes, hierarchical event Bayes, Longstaff–Schwartz, Sobol/QMC |
| `reject` for current scope | stochastic rates/HJM/LMM, higher-order Greeks/AAD, neural volatility surface |
| `prototype` | none |
| `candidate_for_implementation` | none |

`reject` is scoped and reversible: it means the extension has no demonstrated decision need in
the current read-only TTWO repository. Every assessment records the data, baseline and measurable
gate that would reopen it.

## Why no implementation follows

The project has no authorized dense TTWO option history, fresh final holdout or paper campaign.
Heston and raw SVI have not yet been validated on real TTWO surfaces. There is therefore no valid
ablation baseline from which Bergomi, rough volatility, filtering or another advanced method can
show incremental out-of-sample value. Documentary sophistication is not material-gain evidence.

The gate requires authorized data, identifiability against a simpler baseline, OOS material gain,
ranking sensitivity, a numerical cost benchmark and independent review before an extension may
become `candidate_for_implementation`. A candidate would still require a separate implementation
decision. `order_capability=forbidden` remains unchanged.

## Full gate

- 194 tests passed (one third-party `websockets.legacy` deprecation warning);
- Ruff and strict mypy passed across 144 typed source files;
- dependency, six-schema, offline-artifact and 36-source lineage checks passed;
- Phase-10 release review and Phase-11 extension review reproduced byte-for-byte;
- security inspected 138 Python files and found every execution path forbidden.
