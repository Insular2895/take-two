# Quantitative conventions and formula lineage

This directory is the entry point for mathematical claims used by the engine. A formula is
not accepted because it appears in code or in a summary: it needs a stable formula ID, a
source location, assumptions, units, probability measure, implementation symbol, and test.

## Canonical conventions

- Calendar time and option maturity: Actual/365 Fixed.
- Return and realized-volatility annualisation: 252 trading sessions.
- Rates and dividend yields used by Black–Scholes/QuantLib: continuously compounded annual
  decimals unless a contract explicitly says otherwise.
- Black–Scholes theta: USD per underlying share per calendar day.
- Vega and rho: USD per underlying share for a one-percentage-point change.
- Contract PnL: USD after applying the contract multiplier, quantities, fees, and slippage.
- Forecast distributions: real-world measure `P`.
- Arbitrage-free pricing expectations: risk-neutral measure `Q`.
- A `P`/`Q` crossing is forbidden unless a sourced `MeasureTransition` records the method and
  assumptions.

The executable contract is
`src/take_two_options/quantitative/contracts.py`. The structured lineage is maintained in
`docs/research/formula_registry.yaml`.

Monte Carlo output uncertainty is carried in sidecar reports from
`src/take_two_options/simulation/uncertainty.py`. Unweighted binary path outcomes use Wilson
intervals; weighted paths report ESS but no binomial interval. Antithetic standard errors count
pairs as independent replications, and control-variate reports retain variance before and after
adjustment.

## Evidence levels

`sourced` means the source passage has been inspected. `implemented` means code exists.
`tested` means deterministic/property tests cover the implementation. `numerically_validated`
requires an independent benchmark or convergence evidence. None of these states implies
empirical predictive value, a clean holdout, paper eligibility, or permission to trade.
