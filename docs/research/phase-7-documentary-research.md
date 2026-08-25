# Phase 7 documentary research — integer objectives and allocation Pareto frontier

Date: 2026-08-08
Status: `sourced_and_implemented_diagnostic_only`

## Conclusions

- Whole option contracts make the current bounded allocation set discrete and generally
  non-convex. A continuous relaxation can diagnose a smooth surrogate, but it cannot certify an
  executable integer solution. Exhaustive enumeration remains the canonical oracle while the
  configured candidate/contract caps stay small.
- Boyd and Vandenberghe define a Pareto-optimal feasible point as one for which no other feasible
  point is no worse under the ordering and strictly better somewhere (section 4.7.3, printed
  pp. 177–178). The set of such values is the optimal trade-off surface (section 4.7.5, printed
  pp. 181–184).
- Weighted scalarization can reveal Pareto points, but weights encode trade-offs and may miss
  points in non-convex problems. Therefore the engine now computes dominance directly over every
  enumerated feasible allocation; the scalar objective only ranks selections.
- `cash/NO_TRADE` is a feasible all-zero allocation, not an error path. It remains present even
  if a Greek exposure interval would exclude zero for invested portfolios.
- Regime weights derived from the configured scenario updater remain heuristic sensitivity
  weights. An objective contract cannot label them validated OOS without an evidence hash.

## Sources inspected

- Stephen Boyd and Lieven Vandenberghe, *Convex Optimization*, Cambridge University Press,
  2004; local seventh printing with corrections, 2009. Title/copyright pages and section 4.7,
  “Vector optimization,” printed pp. 174–187 inspected.
- Jorge Nocedal and Stephen Wright, *Numerical Optimization*, local PDF, remains secondary. No
  local-gradient method is used to replace the discrete oracle in this phase.

The PDFs remained read-only.

## Implementation and validation

- `OptimizationObjectiveContract` declares ID, version `1.0`, weighted or worst-case expectation,
  all penalty coefficients, regime-weight semantics, whole contracts and mandatory NO_TRADE.
- `optimize_allocations_with_frontier` enumerates the same hard-feasible integer set as the legacy
  optimizer and returns the complete non-dominated frontier plus scalar-ranked selections. The
  old `optimize_allocations` API remains a compatibility wrapper returning only selections.
- Dominance maximizes weighted and worst-case returns while minimizing volatility, adverse CVaR,
  cost, maximum loss, execution risk and model dispersion. No good score may compensate for a
  hard constraint breach.
- Small exhaustive examples verify the exact frontier, cash dominance over a losing allocation,
  whole counts and objective-kind behavior. The V11 integration test verifies a real candidate
  sidecar built from all 16 model/regime valuations.

## Limits

- Pareto membership depends on the declared objectives and the enumerated candidate universe.
- Expected return and CVaR inherit uncalibrated model/regime assumptions.
- O(n²) pairwise dominance is appropriate only for the current bounded feasible set.
- A Pareto point is not a recommendation; it only says no enumerated peer dominates it.
- The continuous gradient/Hessian remains a surrogate diagnostic and does not describe integer,
  CVaR or execution constraints.
