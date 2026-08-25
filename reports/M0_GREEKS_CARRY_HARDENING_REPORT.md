# M0 Greeks, Carry & Trade Economics Hardening Report

Report date: 2026-08-24
Repository mode: read-only research
Final holdout dataset: `UNOPENED` and not accessed
OPRA/provider connection: not attempted

## 1. Initial state

The repository already had a QuantLib finite-difference American pricer, analytic European
first-order Greeks, entry-side bid/ask costs, expiration payoffs, deterministic scenarios,
exercise-risk flags and explicit newer P/Q contracts. The pre-code audit found no economic carry
curve, advanced same-pricer Greeks, numerical Greek confidence, future exit/round-trip model,
generic time-dependent breakeven, pathwise ticket-level P(touch), typed FX attribution or unified
trade-economics ticket. Date conversion hid the intraday limitation, dividend inputs could overlap,
and missing execution/margin values could become false zeroes.

Full audit: `docs/audits/M0_GREEKS_CARRY_CURRENT_STATE_AUDIT.md`.

## 2. Files changed

Core implementation:

- `src/take_two_options/models.py`
- `src/take_two_options/trade_economics_models.py`
- `src/take_two_options/quantitative/trade_economics.py`
- `src/take_two_options/american.py`
- `src/take_two_options/pricing.py`
- `src/take_two_options/domain.py`
- `src/take_two_options/engine.py`
- `src/take_two_options/config/contracts.py`
- `src/take_two_options/opra/contracts.py`
- `src/take_two_options/validation/legacy_vetoes.py`
- `src/take_two_options/reporting/trade_economics.py`
- `src/take_two_options/reporting/legacy_reporting.py`
- `src/take_two_options/reporting/__init__.py`

Configuration, schemas and generation:

- `configs/pre_opra/v1/ttwo_research.yaml`
- `scripts/export_offline_schemas.py`
- `scripts/generate_m0_examples.py`
- `schemas/pre_opra_config.schema.json`
- `schemas/live_option_chain_snapshot.schema.json`
- `schemas/trade_economics_ticket.schema.json`

Tests, docs and reports:

- `tests/test_trade_economics.py`
- `tests/test_pre_opra_config.py`
- `tests/test_offline_artifacts_v11.py`
- `docs/specs/M0_GREEKS_CARRY_TRADE_ECONOMICS.md`
- `docs/audits/M0_GREEKS_CARRY_CURRENT_STATE_AUDIT.md`
- `docs/research/M0_GREEK_CONVENTIONS.md`
- `docs/research/M0_2026_VALIDITY_AUDIT.md`
- `docs/LIMITATIONS.md`, `docs/READINESS.md`, `README.md`, `CHANGELOG.md`
- `reports/examples/m0_trade_economics_ticket.json`
- `reports/examples/m0_trade_economics_ticket.md`
- this Markdown report and its JSON companion.

## 3. Features added

- Versioned strict models for every material M0 financial output.
- Screen/deep-analysis split; deep calculations attach only to the configured number of top
  candidates.
- Same-pricer Delta, Gamma, Theta, Vega, Rho, Vanna, Vomma, Charm, Veta, Speed and Color with raw
  versus normalized values, units and confidence diagnostics.
- Full-repriced 0/1/7/30/60/90-day flat-spot carry and expiry point, effective decay rates and
  acceleration status.
- Configurable volatility transformations and Spot × Time × IV matrices.
- Multi-root breakeven clocks, profit intervals and target-arrival deadlines.
- Entry, configured exit and reconciled round-trip costs; null-safe margin/buying power and FX.
- Exact Shapley full-repricing attribution plus explanatory Taylor attribution and residuals.
- Pathwise P(touch), terminal probability, first-touch timing, interval and ESS contract restricted
  to admissible measure-P paths; unavailable probabilities remain null.
- Dividend-mode guards, curve metadata/interpolation, exact DTE and date-engine precision status.
- Full-repriced base, parallel-up/down, steepening and flattening rate-curve stresses with
  maturity-specific leg shifts.
- Human-readable and JSON `TradeEconomicsTicket`, future contract metadata fields and generated
  schemas/golden artifacts.

## 4. Formulas and conventions

Full repricing is primary. Position values sum signed leg prices times quantity and the observed
contract multiplier. Theta, Charm, Veta and Color are forward one-calendar-day value/Greek drifts.
Vega and Vanna are normalized per one volatility point; Vomma per volatility-point squared; Rho per
one percentage-point rate move. Position Greeks are signed, quantity- and multiplier-weighted sums.

Finite differences use configurable alternate spot/IV/rate bumps and FD grids. Numerical
dispersion maps to `HIGH`, `MEDIUM`, `LOW` or `UNRELIABLE`; it is not statistical confidence.
Details and equations are in `docs/research/M0_GREEK_CONVENTIONS.md`.

## 5. Numerical validation

- European QuantLib FD output remains covered against analytic Black–Scholes–Merton values.
- M0 Vanna and Vomma are tested against analytic European benchmarks.
- American prices retain grid-refinement coverage; M0 higher-order estimates are downgraded when
  bump/grid dispersion is high.
- Flat-spot carry is independently repriced and tested not to equal naïve `theta × horizon`.
- Long calls, verticals and a non-monotonic butterfly validate generic breakeven roots/profit
  intervals, including property-based root reconciliation.
- Cost, FX, Shapley and probability decompositions reconcile in tests.
- The committed JSON/Markdown golden outputs are verified as two renderings of the same typed
  synthetic object.

## 6. BOOK sources

Repository source lineage used:

- `B-NATENBERG-1994` and `R-GREEKS-001..004` for local sensitivities, aggregation and convention
  normalization;
- `B-PASSARELLI-2012` for gamma/theta/vega economics net of costs;
- `B-HULL-2021` for pricing/dividend/rate/numerical foundations, with its incomplete extraction
  journal kept visible;
- `B-GLASSERMAN-2003` for pathwise Monte Carlo and numerical-error context.

No BOOK heuristic was promoted into an execution decision or opaque Greek score.

## 7. Official 2026 sources

The audit checked QuantLib 1.43 and official source code/tests, OCC contract specifications and ODD,
IBKR option/combo/margin/what-if documentation, Treasury CMT quotation conventions and OIC advanced
Greek terminology. Links and limitations are recorded in
`docs/research/M0_2026_VALIDITY_AUDIT.md`.

## 8. Remaining limitations

- American FD values remain date-based, not exact intraday.
- Volatility transformations are configured sensitivity stresses, not calibrated forecasts.
- A transformed surface receives only the implemented basic positivity/calendar-total-variance
  diagnostics, not a global arbitrage-free calibration proof.
- Mixed-expiry cashflows after the first expiry are outside the carry model.
- Numerical confidence does not validate market-model accuracy.
- The M0 fixture has no promoted probability model; its probability values are null.
- Treasury par-yield interpolation is not called a zero curve.
- One test warning comes from the third-party `websockets.legacy` deprecation, not M0 code.

## 9. Pending OPRA / broker evidence

Still `PENDING_OPRA` or `PENDING_BROKER`: live NBBO, quote freshness, market depth, complete provider
Greek conventions, contract discovery/adjustments, observed combo quotes, broker what-if margin,
account-specific commissions and current FX handling. The OPRA interface remains read-only and was
not connected.

## 10. Pending paper validation

Still `PENDING_PAPER_VALIDATION`: actual fills, exit spread/slippage, legging risk, prospective
execution quality, target-arrival behavior under live paths, touch-probability calibration and any
strategy-performance claim. No paper phase was started.

## 11. Tests and static validation

- `pytest -q --disable-warnings --maxfail=1`: **276 passed** in 14.55 seconds.
- The final-holdout ledger test read only the governance ledger state and confirmed `UNOPENED`; it
  did not access or mutate any holdout dataset.
- `ruff check .`: **passed**.
- `mypy src`: **passed**, 165 source files.
- `scripts/export_offline_schemas.py --check`: **27 schemas verified**.
- QuantLib runtime version: **1.43**.

## 12. Readiness

All M0 offline acceptance mechanics are implemented and tested: costs, carry, advanced Greeks,
scenario matrices, breakevens, target timing, P(touch) architecture, null-safe unknowns, dividend
guard, confidence, full-repricing attribution, FX, exercise risks, schemas, reporting and safety
boundaries. This status does not validate a strategy, probability, live quote, margin or fill.

M0_STATUS = COMPLETE_PRE_OPRA

NEXT_PHASE = M — OPRA READ-ONLY LIVE DATA + SHADOW/PAPER VALIDATION
