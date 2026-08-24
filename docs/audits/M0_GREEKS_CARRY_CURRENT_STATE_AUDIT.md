# M0 Greeks, Carry & Trade Economics — Current-State Audit

Status: `COMPLETED_BEFORE_M0_BUSINESS_CODE`

Audit date: 2026-08-24
Repository: `Insular2895/take-two`
Branch: `codex/v10-quantitative-validation-and-robust-decision-engine`

This audit records the implementation state before M0 changes. It is an engineering
assessment, not a financial-model validation or an authorization to trade. The final holdout was
not opened or inspected.

## Boundaries preserved

- The active repository is read-only research. No submit, modify, cancel, exercise, automatic
  roll, or auto-hedge path is authorized.
- The OPRA provider boundary remains unconnected. No credential or entitlement was requested.
- Historical OOS artifacts and validation thresholds are not modified or retuned by M0.
- `NO_TRADE`, `BLOCKED_INSUFFICIENT_DATA`, and missing-value semantics remain first-class.
- TTWO, GTA VI, strikes, expirations, budgets, targets, horizons, and stresses must remain data or
  configuration inputs rather than new Python constants.

## Scope reviewed

The audit covered the requested paths:

- `src/take_two_options/american.py`
- `src/take_two_options/pricing.py`
- `src/take_two_options/scenarios.py`
- `src/take_two_options/domain.py`
- `src/take_two_options/quantitative/`
- `src/take_two_options/reporting/`
- `src/take_two_options/opra/`
- `src/take_two_options/maintenance/`
- `src/take_two_options/simulation/` and the V11 path engine where probability semantics matter
- `docs/LIMITATIONS.md`
- `docs/READINESS.md`
- `option-research-engine/rules/GREEKS/`
- `option-research-engine/books/` and the relevant book fiches
- relevant pricing, scenario, numerical, simulation, OPRA, reporting, property, and configuration
  tests (excluding the final-holdout content)

## Functional inventory

The status vocabulary is the one required by the M0 specification.

| Capability | Status before M0 | Evidence and precise gap |
|---|---|---|
| Delta | `PARTIAL` | Analytic European and American-FD central differences exist and position aggregation uses side, quantity, and multiplier. Raw/provider convention, units, multi-bump confidence, and per-leg normalized records do not exist. |
| Gamma | `PARTIAL` | Analytic European and American-FD central differences exist and aggregate correctly. Multi-bump/grid confidence and normalized metadata are missing. |
| Theta | `PARTIAL` | Analytic theta is per calendar day and American theta is a one-calendar-day full reprice. The result has no explicit unit object, confidence, intraday status, or economic carry curve. |
| Vega | `PARTIAL` | Values are normalized per one volatility point and aggregate by contract multiplier. Provider convention preservation and convergence diagnostics are missing. |
| Rho | `PARTIAL` | Values are normalized per one percentage point. Pricing uses a flat scalar rate; no curve metadata or rate-shape stresses exist. |
| Theta carry | `MISSING` | No `TimeDecayExposure`, full-repriced 1/7/30/60/90-day carry curve, effective decay rates, or acceleration diagnostics. |
| Intraday time | `PARTIAL` | Exact datetimes are retained in domain objects and the central day-count helper preserves seconds. `option_model_value` converts valuation and expiry to `date`, and one historical result creates a midnight timestamp. No precision status is reported. |
| Vanna | `MISSING` | No same-pricer mixed spot/vol finite difference. |
| Vomma / Volga | `MISSING` | No same-pricer volatility-convexity finite difference. |
| Charm | `MISSING` | No convention record and no one-calendar-day delta drift. |
| Veta | `MISSING` | No one-calendar-day vega drift. |
| Speed | `MISSING` | No spot derivative of recalculated gamma. |
| Color | `MISSING` | No one-calendar-day gamma drift or convention record. |
| Lambda | `MISSING` | No option elasticity or capital-based net/gross delta leverage with denominator guards. |
| Future IV scenarios | `PARTIAL` | Deterministic scenarios apply absolute uniform leg shifts and Heston can provide one terminal volatility override. Scenario types, units, status, provenance, and configurable policy objects are absent. |
| Skew stress | `MISSING` | Current interpolation/SVI diagnostics do not transform skew for a trade scenario. |
| Term-structure stress | `MISSING` | No front/mid/back maturity transformation. |
| Event IV crush | `PARTIAL` | A hardcoded uniform `iv_crush` exists; it is not expiry-aware, configuration-driven, or explicitly labeled `CONFIGURED_STRESS`. |
| Time-dependent breakeven | `MISSING` | Expiration breakevens exist for four simple architectures. There is no horizon/IV clock, generic roots array, or profit-interval solver. |
| Target arrival deadline | `MISSING` | No latest-profitable-arrival solver. |
| P(touch) | `PARTIAL` | V11 retains full real-world paths, while the legacy simulator retains terminals only. No upper/lower barrier metric, first-touch time, confidence interval, or promotion gate exists. |
| P(terminal) | `PARTIAL` | Terminal and path-exit probabilities exist in multiple pipelines with explicit P/Q contracts in newer code. The legacy scenario reporter emits quantiles rather than a governed terminal target probability, and ticket-level availability reasons are absent. |
| Round-trip costs | `MISSING` | Entry BBO, fees, and slippage exist; there is no typed entry/exit decomposition or round-trip total. |
| Exit spread | `MISSING` | A heuristic liquidity penalty exists but is not a symmetric exit-spread estimate. |
| Exit slippage | `MISSING` | Entry slippage exists. Future closing slippage is not modeled or status-labeled. |
| Commissions | `PARTIAL` | Entry commissions are supported. Closing commissions and round-trip reconciliation are missing. |
| FX attribution | `PARTIAL` | EUR/USD conversion exists in scanner/intelligence flows, but no handling-mode contract or constant-entry-FX versus scenario-FX contribution reconciliation exists. |
| Margin | `PARTIAL` | `margin_requirement` is nullable for one unknown path, but `estimate_execution` initializes it to zero and can leave zero when `margin_known=true` without an actual requirement. Buying-power status and provenance are absent. |
| Assignment | `PARTIAL` | Deterministic short-American assignment flags and ex-dividend reasoning exist. There is no separate early-exercise field, adjusted-contract visibility in the ticket, or calibrated probability (correctly not invented). |
| Pin risk | `PARTIAL` | A deterministic threshold-based flag exists. Thresholds are hardcoded and not policy-configured. |
| Numerical Greek confidence | `MISSING` | Generic price/grid comparison helpers exist, plus one American price-grid test. There is no per-Greek multi-bump, alternate-grid, dispersion, benchmark, or confidence object. |
| PnL attribution | `PARTIAL` | Scenario attribution fully reprices a fixed sequence `spot -> time -> IV -> rate`, then labels local delta and the remainder of spot movement as gamma. It is order-dependent, has no Shapley averaging, advanced Taylor terms, FX factor, or explicit full-reprice-versus-approximation residual. |
| Probability outputs | `PARTIAL` | P/Q boundaries, calibration statuses, Wilson intervals, ESS, expected PnL, and loss probabilities exist in newer simulation layers. They are not assembled into the trade-economics ticket, and the legacy Q simulator is not an admissible real-world expected-PnL model. |

## Material correctness findings

### Time and pricing

- `QuantConventionSet.calendar_year_fraction` already preserves exact elapsed seconds for datetime
  inputs.
- The selected QuantLib American engine is date-grid based: `_quantlib_value` accepts `date`, and
  `option_model_value` calls `.date()` on the exact market timestamps. Reporting this result as
  exact intraday American theta would be false precision.
- The cache key contains spot, strike, valuation date, expiry date, scalar rate, volatility,
  option type, dividend inputs, exercise style, and grids. It cannot distinguish intraday points
  on the same date or future curve/dividend-treatment identifiers.

### Dividends

- The pricer currently passes both `continuous_dividend_yield` and discrete dividends into the
  same process without a treatment-mode guard. When both represent the same expected cash flows,
  duplicate economics are possible.
- Flat-spot carry crossing an ex-dividend date is not separated from a spot-adjusted scenario.

### Entry, exit, combo, and margin

- Entry prices use ask for long legs and bid for short legs and include multiplier, commission,
  and slippage.
- Missing midpoint or executable side is currently converted with `or 0.0`. This can turn unknown
  execution data into a false zero instead of a blocker.
- A per-leg quote sum is used as an indicative structure estimate. It is not a broker combo quote
  and must not be described as executable combo evidence.
- No future exit spread is observable pre-OPRA. Any M0 exit estimate must therefore be a
  configurable estimate with `ESTIMATED_CONFIGURED_EXECUTION_MODEL`, not `OBSERVED`.
- `margin_available` is account capacity, not the position's margin requirement. It must not be
  reused as the requirement. Unknown short-structure margin remains null unless an explicit
  bounded-risk estimate or broker value is available.

### Scenarios and attribution

- The existing scenario set contains product-specific and hardcoded labels/moves such as
  `gta_delay`, `+/-12` volatility points, and fixed gap percentages. New M0 economics must use
  generic configuration objects; legacy artifacts remain versioned and are not rewritten.
- Current attribution is internally reconciling but path/order dependent. It is not a
  factor-order-invariant explanation.
- Full repricing already exists and is the correct base to extend. Greeks must remain explanatory
  local approximations.

### Probability and simulation

- `simulation.legacy_models.SimulationPaths` stores only terminal spots and is tagged measure Q;
  it cannot support a pathwise P(touch) claim or real-world expected PnL.
- `ConditionalPathSet` and V11 `StochasticPathSet` retain full paths and are tagged measure P.
  They can support a gated pathwise touch calculation without inventing probabilities.
- A touch metric must remain null when no promoted/calibration-admissible P path set is supplied.

### Reporting and operational boundary

- Existing reports expose costs, basic Greeks, scenario PnL, score components, exercise flags,
  and research blockers in separate formats, but there is no versioned `TradeEconomicsTicket`.
- `LiveOptionQuote` prepares bid/ask, sizes, OI, volume, IV, and first-order provider Greeks, but
  lacks the full contract/deliverable identity and provider convention metadata needed for safe
  future normalization.
- The OPRA protocol exposes health and market-data reads only. Preview artifacts preserve
  `transmit=false`, `what_if=true`, human confirmation, and `order_capability=forbidden`.
- Maintenance helpers are advisory/state-transition functions. M0 must not add auto-hedging,
  automatic rolling, or execution.

## Source state before implementation

### Repository books and rules

- Natenberg and `R-GREEKS-001..004` support aggregation, local sensitivity, gamma/theta economic
  trade-offs, and strict convention normalization.
- Passarelli supports gamma/theta/vega management as conditional diagnostics, not automatic trade
  rules.
- Hull and Glasserman fiches identify the relevant pricing, dividend, rate, path-dependence, and
  numerical-error topics, but their extraction journals are incomplete.
- The Gatheral book and Shreve Volume II are recorded as absent. Existing primary
  Gatheral-Jacquier SVI research and the inspected Björk material can support the currently scoped
  surface and P/Q contracts; absence must remain visible.

### Current official checks performed on 2026-08-24

- QuantLib 1.43 is the current release and the repository pin is current. The official FD engine
  uses `Date` exercise/settlement inputs and supports explicit cash-dividend schedules; this does
  not establish intraday American precision.
- OCC confirms that adjusted equity-option contracts can represent deliverables other than the
  standard 100 shares and that equity options are American-style.
- IBKR documents distinct bid/ask/last/model option-computation streams and the need for both
  option and underlying subscriptions for live Greeks. Provider values therefore require source
  stream and convention preservation.
- IBKR combo contracts require leg `conId` values. A leg sum is not proof of a live combo quote or
  fill.
- IBKR what-if is the future source for expected commission and margin impact; it remains outside
  M0 and must stay `PENDING_BROKER`.
- U.S. Treasury daily CMT observations are par yields with bond-equivalent/semiannual quotation,
  not a published zero curve. Existing interpolation must not be relabeled as zero-rate
  bootstrapping.

## Implementation consequences for M0

1. Preserve current result models through optional, versioned additions.
2. Add typed trade-economics models, one versioned configuration section, and one ticket renderer.
3. Make full repricing the source for carry, scenario matrices, breakevens, deadlines, and factor
   attribution.
4. Calculate advanced Greeks from the same selected pricer with multiple bumps and explicit units.
5. Report exact clock time alongside the QuantLib date-engine limitation and configurable
   near-expiry status.
6. Reject duplicate dividend economics and false execution/margin zeroes.
7. Keep probability values null with machine-readable reasons unless an admissible P distribution
   is supplied.
8. Keep all live quote, combo, margin, slippage, fill, and paper-quality claims pending their
   respective future evidence.

## Pre-M0 readiness conclusion

`M0_INITIAL_STATUS = PARTIAL_FOUNDATION_PRESENT`

The repository has a sound read-only boundary, first-order pricing foundation, explicit P/Q
contracts, path-capable real-world simulators, and useful numerical primitives. It does not yet
make trade carry, advanced sensitivities, exit economics, time-dependent breakevens, pathwise
touch probability, or numerical Greek stability sufficiently explicit for Phase M.
