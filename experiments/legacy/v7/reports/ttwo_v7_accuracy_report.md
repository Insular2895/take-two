# TTWO V7 options accuracy report

- Created: `2026-07-19T12:43:10.652632+00:00`
- Panels / variants: `8` / `40`
- Provider requests: `938` (511 cache hits)
- Ranking: `no_trade`
- Order capability: `forbidden`

## Current candidates

- `no_trade`: `no_trade`, accuracy unavailable; baseline retained until an option variant clears every gate
- `primary_h05_dte150__delta45_25:long_call`: `blocked`, accuracy 54.5% [28.0%, 78.7%]; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta45_25:bull_call_spread`: `blocked`, accuracy 9.1% [1.6%, 37.7%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta45_25:long_put`: `blocked`, accuracy 27.3% [9.7%, 56.6%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta45_25:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta55_30:long_call`: `blocked`, accuracy 54.5% [28.0%, 78.7%]; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta55_30:bull_call_spread`: `blocked`, accuracy 9.1% [1.6%, 37.7%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta55_30:long_put`: `blocked`, accuracy 27.3% [9.7%, 56.6%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta55_30:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta65_35:long_call`: `blocked`, accuracy 54.5% [28.0%, 78.7%]; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta65_35:bull_call_spread`: `blocked`, accuracy 9.1% [1.6%, 37.7%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta65_35:long_put`: `blocked`, accuracy 36.4% [15.2%, 64.6%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `primary_h05_dte150__delta65_35:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h10_dte150__delta55_30:long_call`: `blocked`, accuracy 20.0% [3.6%, 62.4%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h10_dte150__delta55_30:bull_call_spread`: `blocked`, accuracy 20.0% [3.6%, 62.4%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h10_dte150__delta55_30:long_put`: `blocked`, accuracy 20.0% [3.6%, 62.4%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h10_dte150__delta55_30:bear_put_spread`: `blocked`, accuracy 20.0% [3.6%, 62.4%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h20_dte150__delta55_30:long_call`: `blocked`, accuracy 0.0% [0.0%, 65.8%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum
- `horizon_h20_dte150__delta55_30:bull_call_spread`: `blocked`, accuracy 0.0% [0.0%, 65.8%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `horizon_h20_dte150__delta55_30:long_put`: `blocked`, accuracy 50.0% [9.5%, 90.5%]; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `horizon_h20_dte150__delta55_30:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 65.8%]; test median return below configured minimum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `horizon_h40_dte150__delta55_30:long_call`: `blocked`, accuracy 0.0% [0.0%, 79.3%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum
- `horizon_h40_dte150__delta55_30:bull_call_spread`: `blocked`, accuracy 0.0% [0.0%, 79.3%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum
- `horizon_h40_dte150__delta55_30:long_put`: `blocked`, accuracy 100.0% [20.7%, 100.0%]; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `horizon_h40_dte150__delta55_30:bear_put_spread`: `blocked`, accuracy 100.0% [20.7%, 100.0%]; deflated Sharpe probability below configured minimum ; train/test stability gap above configured maximum ; holdout validation did not pass
- `expiry_h05_dte090__delta55_30:long_call`: `blocked`, accuracy 54.5% [28.0%, 78.7%]; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte090__delta55_30:bull_call_spread`: `blocked`, accuracy 27.3% [9.7%, 56.6%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte090__delta55_30:long_put`: `blocked`, accuracy 36.4% [15.2%, 64.6%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte090__delta55_30:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte270__delta55_30:long_call`: `blocked`, accuracy 45.5% [21.3%, 72.0%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte270__delta55_30:bull_call_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; test worst loss above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte270__delta55_30:long_put`: `blocked`, accuracy 18.2% [5.1%, 47.7%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass
- `expiry_h05_dte270__delta55_30:bear_put_spread`: `blocked`, accuracy 0.0% [0.0%, 25.9%]; test median return below configured minimum ; test drawdown above configured maximum ; deflated Sharpe probability below configured minimum ; holdout validation did not pass

## Warnings

- Research only; ranking and current candidates cannot authorize an order or size
- Forecast accuracy is observed net win rate with a 95% Wilson interval
- Holdout results do not remove regime, sample-size, or selection uncertainty
- MarketData.app EOD bid/ask is not an intraday NBBO or combo-fill replay
- Deflated Sharpe is a multiple-testing diagnostic at the observed holding-period scale
- No-trade remains the baseline when no option variant clears every gate
