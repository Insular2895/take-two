# Market-data adapter

CF0 deliberately does not choose or invent a provider. Without both `MARKET_DATA_BASE_URL` and
`MARKET_DATA_API_KEY`, provider status is `NOT_CONFIGURED`; the dashboard can display a clearly
labelled synthetic fixture or last imported canonical snapshot.

`MarketDataProvider` is HTTPS-only and exposes:

- `getUnderlyingQuote()`;
- `getOptionQuotes()`;
- `getFxQuote()`;
- `getProviderStatus()`;
- optional `getComboQuote()`.

The generic adapter expects bearer-authenticated JSON endpoints at `/status`, `/underlying/:ticker`,
`/options?identities=...`, `/fx/:native/:policy`, and optional `/combo/:positionId`. This is an
interface contract, not a claim that any real vendor implements it unchanged. Add a named adapter
and provider-contract tests only after provider selection, entitlements, costs, timestamps, quote
semantics, and usage rights are validated.

Optional per-option `iv` and `greeks` must use decimal IV and per-share Greek conventions; CF0
aggregates exact signed contracts and multiplier. If those semantics are not proven, omit the fields
and the UI displays `N/A`. Exit commission, slippage, and FX execution estimates stay sourced from
the last canonical imported snapshot; live quote data never silently invents them.

Each quote must preserve timestamp, provider, source, and quality. A quote older than 120 seconds is
`DATA_STALE`; the monitor keeps the last PnL but does not evaluate economic exit rules on it. A
provider exception produces `DATA_PROVIDER_ERROR` and never writes zero or fake quotes.

MTM uses leg midpoints and exact signed ratios. Conservative liquidation uses bid for a long leg's
sell-to-close and ask for a short leg's buy-to-close. A real combo bid changes the explicit mode to
`COMBO_QUOTE`; otherwise the mode is `LEGWISE_CONSERVATIVE_ESTIMATE`. Unknown commission, slippage,
or required FX execution cost makes net liquidation and liquidation PnL unavailable rather than
assuming zero.

Provider IV/Greeks are displayed only when supplied. Expected remaining PnL, probability metrics,
CVaR, and five scores are never recomputed in the Worker; they retain the canonical model timestamp
and become visibly stale.
