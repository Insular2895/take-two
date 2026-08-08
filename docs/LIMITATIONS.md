# Limitations

- Quantitative conventions are now centralized as Actual/365 Fixed for calendar time and 252
  sessions for empirical annualisation. These product conventions are explicit, not universal.
- Active forecast path sets are tagged `P` and pricing path sets are tagged `Q`; historical
  serialized reports were not rewritten, so their documented generation-specific assumptions
  remain authoritative.
- Black–Scholes has an analytic/QuantLib European cross-check and the American finite-difference
  engine has a grid-refinement test. This is numerical evidence, not market calibration evidence.
- The V10 final-holdout protocol is sealed, but no authorized real dataset is provisioned and no
  dataset hash exists. Empirical and holdout promotion remain blocked.
- The diagnosed IV solver and raw-SVI fitter expose failures and synthetic recovery, but no real
  point-in-time TTWO surface has validated fit quality. Butterfly/calendar checks are finite-grid
  diagnostics; eSSVI remains unimplemented behind explicit data and arbitrage gates.
- EWMA and stationary Gaussian GARCH baselines now have likelihood, residual and chronological
  forecast diagnostics. Their committed evidence is synthetic; heavy tails, leverage, structural
  breaks and real TTWO OOS superiority remain unvalidated. Heston calibration remains blocked.
- Experiment manifests, availability-time checks, purge/embargo, order-invariant PBO ties,
  signal-alignment placebo and a one-time hash-chained holdout ledger are implemented. The real
  holdout is absent and unopened; permutation exchangeability and full primary-paper PBO
  conformance remain limitations.
- MarketData.app historical chains are EOD bid/ask, not intraday NBBO or
  simultaneous combo fills.
- Alpaca indicative snapshots do not supply the open-interest/underlying fields
  required by the active liquidity and budget gates.
- V7, V8, and V9 were inspected and are contaminated. The V11.1 split contract
  can lock a fresh holdout, but no authorized historical option dataset has
  populated one yet.
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
- Existing V7–V9 holdouts remain contaminated. V11.1 implements a point-in-time
  walk-forward interface and explicit baselines, but its committed example is
  synthetic and non-validating. Promotion still requires a new real sample,
  untouched holdout, and paper run.
- SEC, FRED, Take-Two RSS, Google Trends alpha, and IBKR/OPRA connectors are
  opt-in read-only ports. The exchange-calendar port is also unconfigured by
  default and therefore reported as a missing required series. The default run
  does not contact external providers. Credentials, fair-access limits, data
  entitlements, terms, and production retry policies remain deployment
  responsibilities.
- A leg-level quote is not an executable combo quote. Some IBKR smart combo
  orders do not support a what-if check, so the absence of a broker what-if
  response must block promotion rather than weaken the gate.
- Position monitoring and multi-date fixture replay emit human-readable advice
  only. They cannot submit, modify, cancel, roll, exercise, or partially close
  a position.

See [V10 known limits](known_limits.md) for scanner-specific details.
