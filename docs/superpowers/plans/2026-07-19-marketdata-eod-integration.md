# MarketData.app EOD read-only integration plan

Status: implementation authorized by the user on 2026-07-19.

## Objective

Complement Alpaca with historical end-of-day option-chain snapshots containing bid/ask and
liquidity fields. Build look-ahead-controlled TTWO backtest datasets without adding any trading,
order, exercise, portfolio mutation, or broker capability.

## Facts and boundaries

- MarketData.app Free Forever provides one year of historical data and 100 daily API credits.
- Historical option-chain requests are billed per 1,000 returned option symbols.
- The free plan is delayed and licensed for personal, non-commercial use.
- Historical responses tested on 2026-07-19 contained bid/ask, sizes, volume, open interest,
  underlying price, and timestamps. Historical IV and Greeks were null in the tested responses.
- End-of-day bid/ask is better execution evidence than a transaction-bar close, but it is not an
  intraday quote path and must not be labeled as intraday NBBO.

## Architecture

1. `marketdata_data.py` owns credentials, HTTPS transport, cache, response normalization, OCC
   parsing, historical-chain exports, and conversion to the existing backtest contract.
2. `american.py` exposes a narrow QuantLib finite-difference solver for historical implied
   volatility and Greeks from a midpoint price.
3. `backtesting.py` adds an explicit `eod_bid_ask` price basis and preserves its lower readiness
   than historical intraday NBBO.
4. `cli.py` adds read-only chain and backtest commands. Tokens are never accepted as CLI flags.
5. Raw licensed responses remain under ignored `data/marketdata/`; derived user-selected reports
   remain under ignored `reports/marketdata_*` paths.

## Data contracts

- Every snapshot records requested date, actual quote timestamp, retrieval time, provider fields,
  rate-limit headers, cache status, and evidence provenance.
- Historical records must match the requested New York trading date. Silent fallback to a stale
  prior session is rejected.
- Missing or crossed bid/ask blocks conversion to a backtest quote.
- Contract multiplier is supplied explicitly by the backtest specification. It is never inferred
  as 100 from the option symbol.
- Local IV and Greeks record their price input, rate, dividend yield, model, and warnings.
- Cache entries are content-hashed, written atomically, and never contain credentials.

## Commands

- `marketdata-chain`: fetch or reuse one filtered historical EOD chain and optionally compute local
  analytics.
- `marketdata-backtest`: fetch the exact expiration/side/strike groups required by an explicit
  train/test specification, build the dataset, and run the existing backtest.

## Tests

- credentials absent and redacted;
- URL/query construction and token confined to the Authorization header;
- columnar payload validation and requested-date enforcement;
- cache hit, integrity failure, and force refresh;
- OCC parsing and exact-symbol selection;
- local IV/Greek recovery against a QuantLib-generated American option price;
- EOD bid/ask backtest conversion, executable side selection, provenance, and readiness;
- missing/crossed quotes, missing symbols, invalid timelines, and no order capability.

## Acceptance criteria

- Offline unit suite, Ruff, strict mypy, and `pip check` pass.
- No trading SDK or order endpoint is introduced.
- A live TTWO request is attempted only when `MARKETDATA_TOKEN` is present.
- Without credentials, the CLI fails with an actionable message and all offline tests still pass.

## Out of scope

- Intraday historical NBBO, tick replay, queue position, combo quotes, and market impact.
- Commercial redistribution or SaaS licensing.
- Automatic strategy discovery, sizing, paper orders, or live orders.
- Automatic historical Treasury-rate and corporate-action ingestion.
