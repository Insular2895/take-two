# Take Two Options

Read-only, generic, knowledge-driven option research for bounded-risk trade
requests. The active pipeline loads provenance-aware recipes, enumerates listed
strikes and expirations, applies executable bid/ask and whole-contract budget
constraints, runs separate conditional simulations, validates hard gates, then
uses Pareto ranking. `NO_TRADE` and `BLOCKED_INSUFFICIENT_DATA` are first-class
outcomes.

```bash
ttwo-options knowledge validate --knowledge-dir research/knowledge_items
ttwo-options knowledge compile \
  --knowledge-dir research/knowledge_items \
  --catalog-out research/strategy_catalog/catalog.json
ttwo-options data refresh --ticker TTWO
ttwo-options trade analyze \
  --request configs/trades/ttwo_gta6_1000eur.yaml \
  --refresh-data \
  --report-dir reports/latest
ttwo-options trade compare --report reports/latest/decision_report.json
ttwo-options trade ibkr-ticket \
  --report reports/latest/decision_report.json \
  --candidate-id <ID> \
  --mode preview
ttwo-options position monitor \
  --position <POSITION_FILE> \
  --refresh-data \
  --report-dir reports/latest/position
```

The package contains no live-order submission, modification, cancellation, or
exercise capability. An IBKR artifact is preview-only (`transmit=false`,
`what_if=true`) and is created only for a candidate that passes every gate.

V7–V9 are isolated under `experiments/legacy/`; their inspected holdouts are
marked contaminated under `validation/contaminated_holdouts/`.

See [product contract](docs/product/PRODUCT_CONTRACT.md),
[current architecture](docs/architecture/CURRENT_ARCHITECTURE.md),
[migration](docs/MIGRATION.md), and [limitations](docs/LIMITATIONS.md).
