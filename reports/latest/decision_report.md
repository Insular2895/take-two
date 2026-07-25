# ANALYSE

- Ticker: `TTWO`
- Budget: `1000.00 EUR`
- Thèse: Upside thesis around the officially announced Grand Theft Auto VI release, without assuming that the catalyst guarantees a positive stock or option return.
- Horizon: `365–548 jours`
- Date des données: `2026-07-23 20:00:00+00:00`
- Qualité des données: `eod_bid_ask`
- Statut du holdout: `NOT_REACHED_AFTER_HARD_VETOES`
- Nombre total d’essais: `4210`

# VERDICT

`NO_TRADE`

Raisons:

- no candidate survived structural pruning
- BUDGET_EXCEEDED: 1952 of 2105 generated candidates
- COMBO_SPREAD_FAILED: 1401 of 2105 generated candidates
- LIQUIDITY_FAILED: 1565 of 2105 generated candidates
- MAXIMUM_LOSS_EXCEEDED: 1912 of 2105 generated candidates
- THESIS_INCOMPATIBLE: 1326 of 2105 generated candidates

## Candidats constructibles ou finalistes bloqués

Aucun candidat constructible n’est disponible.

## Diagnostics des structures les plus proches

- `cand-bb8f287cd3b2ea82` · `bull_call_spread` · perte max `651.4` · veto `['COMBO_SPREAD_FAILED', 'LIQUIDITY_FAILED']`
- `cand-856f0dadd5d1abb5` · `call_butterfly` · perte max `732.8` · veto `['COMBO_SPREAD_FAILED', 'LIQUIDITY_FAILED']`
- `cand-399166d09dd52093` · `call_broken_wing_butterfly` · perte max `1072.8` · veto `['COMBO_SPREAD_FAILED', 'LIQUIDITY_FAILED']`
- `cand-68acde9e02a5c17c` · `call_diagonal` · perte max `2591.4` · veto `['BUDGET_EXCEEDED', 'MAXIMUM_LOSS_EXCEEDED']`
- `cand-dca82847e69fa5fe` · `call_calendar` · perte max `2711.4` · veto `['BUDGET_EXCEEDED', 'MAXIMUM_LOSS_EXCEEDED']`

## Limites

- End-of-day bid/ask does not prove an intraday or simultaneous combo fill
- Contract multiplier is normalized to 100 and must be rechecked with the broker
- A live timestamped broker combo quote could differ from synthetic leg markets
- Statistical validation was not reached because all structures failed earlier gates

## Provenance

- `natenberg-options-volatility-2015` — Option Volatility and Pricing (source locale)
- `take-two-q2-fy2026` — Fiscal second quarter 2026 results and GTA VI release timing (https://www.take2games.com/ir/news/take-two-interactive-software-inc-reports-results-fiscal-3)
- `ecb-eurusd-2026-07-17` — Dated EUR/USD reference rate used for budget normalization (https://data.ecb.europa.eu/currency-converter)
- `MARKETDATA-EOD-CHAIN-TTWO-20260723-20260725T093424Z` — Timestamped historical option-chain response (https://www.marketdata.app/docs/api/options/chain/)

## Audit

- `reports/latest/trial_registry.jsonl`
- `reports/latest/data_snapshot_manifest.json`
- `reports/latest/audit_log.json`
- `reports/latest/ibkr_ticket_status.json`

- Order capability: `forbidden`
