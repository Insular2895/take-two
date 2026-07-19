# Alpaca read-only real-data integration plan

Status: implementation authorized; credentials and live entitlements remain external.

## Objective

Connect the TTWO research engine to Alpaca market data without introducing any order capability.
Produce source-backed calibration datasets from equity bars and source-backed option backtests from
historical option bars, while exposing the absence of historical bid/ask quotes.

## Guardrails

- Environment credentials only; no CLI secret flags, committed keys, or secret logging.
- Import Alpaca market-data clients only. Do not instantiate `TradingClient` or expose order APIs.
- Historical option data before February 2024 is rejected.
- Option bar closes are labeled `bar_close_proxy`, never represented as historical NBBO.
- A proxy-price backtest remains `screen_grade` even when the source bars are real.
- Raw API provenance, retrieval time, symbol, timeframe, and look-ahead-safe availability are kept.

## Implementation

1. Add the official `alpaca-py` SDK and credential/feed configuration.
2. Add a narrow read-only adapter for stock and option historical bars.
3. Convert daily TTWO stock bars into `source_backed_calibration` inputs.
4. Convert explicit option-contract specifications into train/test cases using the latest bar
   available before each decision timestamp.
5. Extend backtest price-quality contracts so NBBO and bar proxies cannot be confused.
6. Add CLI commands, `.env.example`, deterministic fake-client tests, and operator documentation.
7. Attempt a minimal real read only when credentials are present; otherwise report the exact
   credential blocker without weakening tests.

## Primary sources

- Alpaca-py market-data and historical option API documentation.
- Alpaca historical option data availability and feed documentation.
- Alpaca historical option bars endpoint reference.
