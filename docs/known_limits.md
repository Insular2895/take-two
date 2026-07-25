# V10 known limits

- `thesis-scan` supports bullish direction only.
- The minimum universe is long call (with a LEAPS maturity label), bull call
  spread, and symmetric call butterfly. It intentionally excludes naked shorts,
  undefined-margin credit combinations, calendars, and diagonals.
- Scenario probabilities are optional and never inferred. Without them, no
  expected P&L or probability of success is displayed.
- The American model uses a flat configured rate/dividend yield and one IV per
  leg stressed by fixed multipliers. It is not a calibrated future IV-surface
  forecast.
- Pre-expiry P&L is a model estimate. Terminal payoff is exact only under the
  stated contract multiplier and deliverable.
- Leg bid/ask cannot prove a simultaneous combo fill. The displayed maximum
  debit must be checked against a live IBKR combo quote.
- Missing OI, volume, or deliverable data lowers a candidate to watchlist;
  known threshold failures are blocked.
- Historical V9 results are weak/contaminated. V10 lowers historical confidence
  but thesis mode remains scenario analysis, not historical validation.
- FX, rate, dividend, commission, slippage, broker permissions, conIds,
  corporate actions, taxes, and account-specific margin require fresh human
  verification.
- The committed full report is deliberately large because it preserves all
  scenario points for auditability.

The general repository limitations remain in [`LIMITATIONS.md`](LIMITATIONS.md).
