# Limitations

- MarketData.app historical chains are EOD bid/ask, not intraday NBBO or
  simultaneous combo fills.
- Alpaca indicative snapshots do not supply the open-interest/underlying fields
  required by the active liquidity and budget gates.
- V7, V8, and V9 were inspected and are contaminated. No fresh locked
  option-strategy holdout exists yet.
- The accessible option history is too short for robust multi-regime,
  catalyst-specific nested validation.
- Conditional GBM and historical bootstrap are screen-grade distributions, not
  causal GTA VI forecasts.
- Future IV is stressed, but a calibrated detailed IV-surface forecast is P2.
- Rolling is registered but rejected during optimization when future combo
  quotes are unavailable.
- Broker combo margin, live FX, contract IDs, permissions, commissions, and
  fills require a fresh IBKR human preview.
- Structural validity and favorable simulation never substitute for DSR, PBO,
  placebo, external walk-forward, locked holdout, and paper-trading gates.
- V10 thesis mode is a scenario scanner, not a probability model. Expected P&L
  and probability of success are null unless the user supplies a probability
  for every target and the vector sums to one.
- V10 uses a flat configured risk-free rate, continuous dividend yield, and
  per-leg IV stresses. It does not forecast the full future volatility surface.
- A quote with missing open interest, volume, or unconfirmed deliverable can be
  retained only as an explicit watchlist warning; a known threshold breach,
  invalid quote, stale quote, non-standard multiplier, budget breach, or
  unbounded/margin-unknown structure is blocked.
- `LEAPS call` is a maturity label on `long_call`, not a fourth architecture.
  Long calls still have contractually unbounded upside but bounded premium risk.
- V11 is a probabilistic research overlay, not a validated probability engine.
  Its default priors, likelihoods, evidence caps, regime drifts, jump
  parameters, and Heston parameters are explicit experimental assumptions.
- The default V11 run inherits a synthetic V10.1 chain. Its Dupire
  finite-difference surface is therefore `partial`; unstable nodes fall back
  to observed IV and no global static-arbitrage calibration is claimed.
- The V11 path repricer uses conditional Black-Scholes between V10.1 QuantLib
  American control points. Early exercise, discrete dividends, pin risk, and
  assignment still require the V10.1 controls and broker review.
- Without an aligned point-in-time factor file, covariance is limited to the
  available TTWO return series. It cannot infer missing Nasdaq, peer, rate, FX,
  volume, IV, OI, sentiment, news, or catalyst factors.
- Exact integer enumeration solves only the configured finite candidate pool
  and contract cap. Gradient/Hessian diagnostics describe the smooth
  mean-variance surrogate, not CVaR or discrete constraints.
- Existing V7–V9 holdouts remain contaminated. V11 cannot promote a candidate
  without a new nested walk-forward sample, untouched holdout, and paper run.
- SEC, FRED, Take-Two RSS, Google Trends alpha, and IBKR/OPRA connectors are
  opt-in read-only ports. The exchange-calendar port is also unconfigured by
  default and therefore reported as a missing required series. The default run
  does not contact external providers. Credentials, fair-access limits, data
  entitlements, terms, and production retry policies remain deployment
  responsibilities.
- A leg-level quote is not an executable combo quote. Some IBKR smart combo
  orders do not support a what-if check, so the absence of a broker what-if
  response must block promotion rather than weaken the gate.
- Position monitoring emits human-readable advice only. It cannot submit,
  modify, cancel, roll, exercise, or partially close a position.

See [V10 known limits](known_limits.md) for scanner-specific details.
