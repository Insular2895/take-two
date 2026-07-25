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

See [V10 known limits](known_limits.md) for scanner-specific details.
