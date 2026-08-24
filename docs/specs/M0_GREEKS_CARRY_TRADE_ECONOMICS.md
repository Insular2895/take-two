# M0 Greeks, Carry & Trade Economics

Version: `1.0`
Status: `COMPLETE_PRE_OPRA` for offline mechanics
Scope: read-only research; no order or position mutation capability

## Purpose

M0 turns a directional option idea into explicit trade economics. The primary financial
calculation is always a full reprice of every leg. Greeks are local diagnostics and the Taylor
attribution is explanatory; neither replaces the full-repriced scenario PnL.

The implementation is generic. Ticker, budget, strikes, expirations, targets, horizons, rate
inputs, IV shocks, numerical bumps and cost assumptions come from market data or the versioned
`trade_economics` configuration.

## Architecture

The M0 contracts live in `trade_economics_models.py`; the calculations live in
`quantitative/trade_economics.py`; the Markdown view lives in
`reporting/trade_economics.py`. `StrategyCandidate.trade_economics` is optional for backward
compatibility. Historical artifacts retain their original schemas.

Two analysis stages prevent advanced finite differences and Shapley repricing from running over
every rejected candidate:

- `screen`: the existing ranking and veto calculations only;
- `deep_analysis`: attach a `TradeEconomicsTicket` to the configured number of top candidates.

The committed pre-OPRA configuration selects `deep_analysis` with a candidate limit. Library
fixtures default to `screen` so legacy pipelines remain fast.

## Economic state and full repricing

For a position with legs `i`, the state value is:

```text
V(S, t, sigma, r) = sum_i side_i * quantity_i * multiplier_i * V_i(S, t, sigma_i, r_i)
```

Stock legs use their underlying-unit quantity. Option legs use the selected European or American
QuantLib finite-difference pricer, the declared dividend mode, the contract multiplier and each
leg's own IV unless a configured transformation changes it.

At and after expiration, an option leg is replaced by intrinsic value. Mixed-expiry carry is
clipped at the earliest expiry; post-expiry settlement cashflows require a separate model and are
not silently invented.

## Time decay and carry

Local theta is the one-calendar-day full-reprice change:

```text
Theta_1d = V(S0, t0 + 1 calendar day, IV0, r0) - V(S0, t0, IV0, r0)
```

Flat-spot carry at horizon `h` is independently repriced:

```text
Carry(h) = V(S0, min(t0 + h, expiry), IV0, r_h) - V(S0, t0, IV0, r0)
```

The engine does not use `theta × days` as the economic forecast. The curve includes `0`, configured
1/7/30/60/90-day points when available, and expiry. Effective decay rates and acceleration are
derived from the full-repriced curve. A horizon that crosses an ex-dividend date is labeled
`CROSSES_DIVIDEND_EVENT`; a simple ex-dividend spot-adjusted value is shown separately and is not
labeled pure theta.

## Advanced Greeks and confidence

Delta, Gamma, Theta, Vega, Rho, Vanna, Vomma, Charm, Veta, optional Speed and optional Color are
computed with the same full pricer as the position. Central finite differences use multiple
configured bump sizes and at least two FD grids. Each result carries:

- raw and normalized values;
- unit, currency, multiplier and position sign;
- model, source, timestamp and calculation method;
- primary bump, alternate bumps, grid levels and estimate dispersion;
- optional European analytic benchmark difference;
- `HIGH`, `MEDIUM`, `LOW` or `UNRELIABLE` confidence.

Confidence measures numerical stability under the configured refinements. It is not statistical
confidence or evidence that the model is calibrated to the market.

## Volatility scenarios

`VolatilityScenario` supports constant leg IV, absolute parallel shifts, relative multipliers,
skew steepening/flattening, short-end crush/expansion, long-end stability, event crush and
spot/vol joint stresses. Units and parameters are explicit. A scenario is labeled one of:

- `CONFIGURED_STRESS`;
- `LEG_LEVEL_STRESS_ONLY` when no surface is present;
- `SURFACE_STRESS_VALID` after the available total-variance checks;
- `SURFACE_STRESS_INVALID` when a transformed surface fails those checks.

No configured stress is described as a calibrated volatility forecast.

Each deep candidate receives a Spot × Time × IV matrix. Every cell exposes full-repriced value,
gross PnL, round-trip cost, net PnL, net return when capital is known, assumptions and scenario
status.

## Breakeven clock and target timing

The generic breakeven solver scans a configured positive-price domain, brackets every sign change,
refines roots by bisection and derives all profitable intervals. It supports monotonic and
non-monotonic payoffs. Roots are arrays; a butterfly can therefore expose two roots and one bounded
profit interval.

For each configured horizon and base/crush/expansion scenario:

```text
NetPnL(S, t) = full_repriced_position_value - total_entry_cash_cost - estimated_exit_cost
```

Target timing evaluates every calendar-day arrival through the earliest expiry and returns
`LATEST_PROFITABLE_ARRIVAL`, `PROFITABLE_THROUGH_EXPIRY`,
`NEVER_BREAKEVEN_AT_THIS_TARGET`, or `NON_MONOTONIC_TIME_RELATION`.

## Costs, capital and margin

Entry economics separate midpoint premium, executable bid/ask cost, slippage, commissions and FX
cost. Missing two-sided or executable quotes are blockers, never zeroes. Per-leg BBO aggregation is
`INDICATIVE`; it is not a live combo quote.

Exit spread, slippage and commission are symmetric, configurable estimates with status
`ESTIMATED_CONFIGURED_EXECUTION_MODEL`. Round-trip costs reconcile exactly to known entry and exit
components. Real exit quality stays `PENDING_OPRA`/`PENDING_PAPER_VALIDATION`.

Margin states are `KNOWN_BROKER`, `ESTIMATED`, `NOT_REQUIRED`, `UNKNOWN` or `BLOCKED`. Unknown and
blocked amounts must be null. A paid-debit defined-risk structure can be `NOT_REQUIRED`; a bounded
credit vertical can carry an analytical estimate; every broker result remains pending an IBKR
what-if preview.

Classic lambda is shown only for a single positive-value option position with a safe denominator.
Multi-leg tickets use net and gross delta-notional leverage relative to known capital at risk.

## Probability and measure boundary

`P(touch)` is pathwise:

```text
P_touch = count(paths crossing the barrier at any checkpoint) / number_of_paths
```

It is distinct from terminal-above/below probability and includes first-touch count, conditional
median first-touch time, Wilson interval and effective sample size. Forecast tickets accept only
measure `P` paths. `Q` pricing paths cannot become real-world probabilities. Without an admissible
promoted model, every probability field is null with a machine-readable reason.

## PnL attribution

Full-repricing attribution uses exact Shapley averaging over spot, time, volatility, rate and FX
state factors, then includes execution costs and an explicit residual. This removes the
factor-order dependence of the legacy sequential attribution. Components reconcile to the primary
full-repriced PnL.

The Taylor sidecar displays Delta, Gamma, Theta, Vega, Vomma, Vanna, Rho, execution costs and the
residual versus full repricing. It is explicitly an approximation.

## Dividends, rates and intraday time

Dividend treatment is one of `NONE`, `CONTINUOUS_YIELD`, `DISCRETE_CASH` or
`HYBRID_EXPLICIT_NON_OVERLAPPING`. Inconsistent inputs fail closed. Hybrid use requires both inputs
and an explanation showing why their economics do not overlap.

An optional risk-free curve preserves source instrument, quote type, compounding, day count,
bootstrap method and interpolation method. A source par yield is not relabeled a zero rate. A
declared zero curve requires an explicit bootstrap method.

The `rate_stresses` configuration must include `BASE_CURVE`, `PARALLEL_UP`, `PARALLEL_DOWN`,
`STEEPENING` and `FLATTENING`. Parallel and short/long-end shifts are expressed in basis points;
each leg receives a maturity-interpolated shift and the position is fully repriced. The resulting
value, gross/net PnL and per-leg shifts are visible in the ticket.

Exact market and expiry datetimes are preserved and exact DTE is reported. The selected QuantLib
FD engine uses `Date`, so American valuations are marked `APPROXIMATED_DATE_ENGINE`; within the
configured near-expiry threshold they become `INSUFFICIENT_NEAR_EXPIRY`. An exact-clock analytic
European benchmark is provided when compatible with the dividend inputs.

## Trade ticket and safety boundary

`TradeEconomicsTicket` version `1.0` contains legs, normalized Greeks, entry/exit/round-trip costs,
margin, payoff bounds, carry, leverage, scenarios, breakeven clock, target timing, attribution,
probability availability, FX, liquidity, exercise risks, intensity, blockers and warnings.

Every ticket enforces:

```text
transmit = false
what_if = true
order_capability = forbidden
```

M0 adds no provider connection, order submission, modification, cancellation, exercise, automatic
roll or automatic hedge path. The golden JSON and Markdown are generated from the same typed
synthetic ticket by `scripts/generate_m0_examples.py`.
