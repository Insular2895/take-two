# 2026 validity audit

Date: 2026-08-08  
Scope: V10 quantitative validation phases 1–9  
Maximum claim: `numerically_validated_research_only`

This audit grades evidence, not attractiveness of a TTWO position. The overall decision chain is
capped by its weakest required component. A strong pricing identity cannot compensate for missing
real option history, event calibration, an unopened holdout or a paper campaign.

| Component | Current grade | Evidence | Missing prerequisite / blocker |
| --- | --- | --- | --- |
| P/Q, units and numerical contracts | `tested` | strict contracts and property/golden tests | independent methodology review |
| European pricing control | `numerically_validated` | analytic/QuantLib parity and finite differences | market calibration is separate |
| American finite-difference pricing | `tested` | QuantLib plus grid refinement | broader contract/dividend benchmark set |
| Diagnosed IV | `numerically_validated` | synthetic recovery and fail-closed brackets | real TTWO point-in-time quote validation |
| SVI finite-grid surface | `tested` | synthetic fit and butterfly/calendar diagnostics | real surface, continuous/global arbitrage evidence |
| EWMA/GARCH calibration harness | `tested` | synthetic recovery and chronological forecasts | real TTWO OOS baseline superiority |
| Experiment/holdout protocol | `tested` | manifests, purge/embargo, sealed ledger mechanics | authorized dataset and unopened holdout |
| Exit Monte Carlo and uncertainty | `tested` | state-machine, convergence, Wilson/ESS, variance reduction | intraday crossings and real calibration |
| Model uncertainty/calibration scoring | `tested` | typed ensemble and Brier/log/ECE harness | real aligned forecasts/outcomes |
| Integer allocation/Pareto | `tested` | exhaustive oracle and exact dominance | validated objectives and risk limits |
| Event scenarios/sequential rules | `tested` | point-in-time graph, origins, sensitivity, advisory rules | real TTWO probabilities/dependencies/shocks |
| Final evidence report/dashboard | `tested` | mandatory sections, monotone grade, static HTML | human/product/regulatory review |
| Real empirical validation | `proposed` | protocol only | authorized point-in-time dataset |
| Fresh final holdout | `proposed` | one-time ledger only | unopened dataset hash and execution |
| Paper validation | `proposed` | plan only | minimum-duration paper campaign |

Decision-chain result: `software_tested_only`. Some isolated mathematical components reach
`numerically_validated`, but the user-facing strategy selection remains capped by uncalibrated
event/model inputs and absent real OOS evidence. `production_ready` is not used.

Open methodological contradictions and corrections are tracked in
[`errata_registry.yaml`](errata_registry.yaml). Formula lineage is checked in
[`formula_lineage_matrix.md`](formula_lineage_matrix.md).
