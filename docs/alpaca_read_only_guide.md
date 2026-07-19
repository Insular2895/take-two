# Alpaca read-only market-data guide

Status: `implemented_credentials_required`

## Security boundary

The integration imports only Alpaca stock and option historical-data clients. It does not import
or instantiate `TradingClient`, order requests, position mutations, exercise, or do-not-exercise
endpoints. Credentials are read from the process environment and are redacted from object reprs.

```bash
cp .env.example .env
# Fill the two APCA variables locally, then load them into the current shell.
set -a
source .env
set +a

.venv/bin/ttwo-options alpaca-check --ticker TTWO --stock-feed iex
```

Never pass secrets as CLI arguments or commit `.env`.

## Current option chain

The chain command exports current quote, trade, IV, and Greeks. The free `indicative` feed is a
derived feed; `opra` requires the corresponding subscription.

```bash
.venv/bin/ttwo-options alpaca-chain \
  --ticker TTWO \
  --feed indicative \
  --expiration-from 2026-09-01 \
  --expiration-to 2027-06-30 \
  --strike-min 180 \
  --strike-max 360 \
  --json-out data/alpaca/ttwo_option_chain.json
```

Use this export to verify that every contract symbol in a backtest specification exists.

## Source-backed calibration

The calibration command requests split/dividend-adjusted daily equity bars. Each daily close is
treated as available one calendar day after its Alpaca timestamp, which is conservative for the
look-ahead gate.

```bash
.venv/bin/ttwo-options alpaca-calibrate \
  --ticker TTWO \
  --stock-feed iex \
  --start 2024-02-01T00:00:00Z \
  --end 2026-06-30T23:59:59Z \
  --training-cutoff 2026-07-02T00:00:00Z \
  --dataset-out data/alpaca/ttwo_calibration_dataset.json \
  --json-out reports/alpaca_tt_calibration_report.json \
  --markdown-out reports/alpaca_tt_calibration_report.md
```

`iex` covers IEX activity; `sip` requires the appropriate entitlement and is preferable for broad
US equity coverage. Source-backed calibration moves to `validation_pending`, not research-grade.
Heston remains `insufficient_data` because close history alone cannot identify it robustly.

## Historical option backtest

Alpaca documents historical option data only from February 2024. Its historical API exposes bars
and trades, but not historical option quote/NBBO requests. The adapter therefore maps each selected
bar close to `option_bar_close_proxy`, requires non-zero slippage, and keeps the report
`screen_grade`.

Start from [the example specification](../fixtures/alpaca_tt_options_backtest_spec.example.json),
replace symbols/dates after checking the chain, then run:

```bash
.venv/bin/ttwo-options alpaca-backtest \
  --spec fixtures/alpaca_tt_options_backtest_spec.example.json \
  --dataset-out data/alpaca/ttwo_option_backtest_dataset.json \
  --json-out reports/alpaca_tt_option_backtest_report.json \
  --markdown-out reports/alpaca_tt_option_backtest_report.md
```

For each decision timestamp the adapter selects the latest completed bar whose conservative
availability timestamp is not later than the decision. Missing or non-trading contracts fail the
run instead of being filled with invented prices.

## Data-quality ladder

1. Current OPRA quote/chain: useful for current model inputs, subject to subscription and timing.
2. Historical option bar/trade: real transaction aggregate, usable as a screen-grade proxy.
3. Historical NBBO from another authorized provider: required for execution-grade spread/cost
   testing.

No level authorizes an order in this repository.
