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
