# TTWO V8 options opportunity report

- Created: `2026-07-19T15:09:48.887625+00:00`
- Panels / variants: `4` / `17`
- Provider requests: `977` (975 cache hits)
- Ranking: `no_trade`
- Holdout policy: `reused_exploratory`
- Order capability: `forbidden`

## Current candidates

- `no_trade`: `no_trade`, accuracy unavailable; baseline retained until an option variant clears every gate
- `architecture_h05_dte150__delta55_30:long_call`: `blocked`, accuracy 54.5% [28.0%, 78.7%]; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:bull_call_spread`: `blocked`, accuracy 9.1% [1.6%, 37.7%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:long_put`: `blocked`, accuracy 27.3% [9.7%, 56.6%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:long_straddle`: `blocked`, accuracy 9.1% [1.6%, 37.7%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:long_strangle`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:call_butterfly`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:put_butterfly`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `architecture_h05_dte150__delta55_30:iron_condor`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `term_h10_back180_front45__delta55_30:long_call_calendar`: `blocked`, accuracy 0.0% [0.0%, 65.8%]; insufficient test observations ; coverage below configured minimum ; test median return below configured minimum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `term_h10_back180_front45__delta55_30:call_diagonal`: `blocked`, accuracy 0.0% [0.0%, 65.8%]; insufficient train observations ; insufficient test observations ; coverage below configured minimum ; test median return below configured minimum ; deflated Sharpe probability below configured minimum ; no eligible front/back call diagonal
- `leaps_put_h30_dte365_tp80__put_strike_plus10:leaps_put`: `blocked`, accuracy unavailable; insufficient train observations ; insufficient test observations ; coverage below configured minimum ; holdout validation did not pass ; no listed put within 5% of target K+10%
- `leaps_call_h30_dte365_tp80__call_strike_minus10:leaps_call`: `blocked`, accuracy 0.0% [0.0%, 79.3%]; coverage below configured minimum ; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum

## Warnings

- Research only; ranking and current candidates cannot authorize an order or size
- Forecast accuracy is observed net win rate with a 95% Wilson interval
- Holdout results do not remove regime, sample-size, or selection uncertainty
- MarketData.app EOD bid/ask is not an intraday NBBO or combo-fill replay
- Deflated Sharpe is a multiple-testing diagnostic at the observed holding-period scale
- A reused exploratory holdout can populate a watchlist but cannot produce an eligible candidate
- No-trade remains the baseline when no option variant clears every gate
