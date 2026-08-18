# Current architecture

```text
TradeRequest + versioned policies
              |
structured knowledge -> validator -> compiler -> StrategyCatalog
              |                             |
read-only chain -> normalized MarketSnapshot -> exhaustive enumerator
                                                   |
                                structural pruning + whole-contract sizing
                                                   |
historical returns -> regime forecast -> separate conditional path models
                                                   |
                          coarse search -> fine exit-policy neighborhood
                                                   |
             nested/purged gates + DSR/PBO/stress/placebo when calculable
                                                   |
                           hard veto -> Pareto -> explanatory score
                                                   |
              DecisionReport + audit + figures + conditional IBKR preview
```

Active packages are `knowledge`, `candidate_generation`, `forecasting`,
`simulation`, `optimization`, `validation`, `sizing`, `maintenance`,
`decision`, and `reporting`.

The former V1–V9 engines remain available only through the hidden `legacy` CLI
and archived experiments. They are not imported by the active decision
pipeline.

V10 adds an independent, read-only thesis path without replacing the active
generic decision pipeline:

```text
ThesisScanRequest + dated policy + chain
                 |
       strict quote/catalyst/FX/liquidity filters
                 |
 long call / LEAPS class + bull call spread + call butterfly
                 |
 conservative debit + bounded risk + EUR budget veto
                 |
 QuantLib American today/30/60/90/catalyst/expiry × spot × IV
                 |
 prudent / balanced / aggressive deterministic rankings
                 |
 JSON + Markdown + standalone dashboard + IBKR preview-only tickets
```

The detailed contract is in
[`V10_BULLISH_THESIS_SCANNER.md`](V10_BULLISH_THESIS_SCANNER.md).

V11 is a modular intelligence overlay. It consumes the immutable V10.1 report
and does not replace structure construction:

```text
V10.1 report + V11.1 policy + observations/events + optional histories
                                |
   provenance/cutoff/freshness -> deterministic event normalization
                                |
 audited Bayes + sensitivity -> four regime weights and confidence
                                |
  GBM / Dupire local vol / Heston / Heston+jumps path ensembles
                                |
 convergence/arbitrage checks + repricing + exits + robustness/stress
                                |
 historical calibration + point-in-time walk-forward (fail-closed)
                                |
 exact integer allocation under budget/loss/concentration/liquidity/Greeks
                                |
 cash/no-trade + advisory snapshots/trajectory replay + readiness inventory
                                |
 JSON + Markdown + network-free HTML + blocked preview-only artifacts
```

The V11 package is `intelligence`. Its modules separate schemas, data
connectors, event normalization, Bayesian updates, historical calibration,
walk-forward backtesting, covariance, stochastic paths, local-volatility
diagnostics, valuation, validation, robustness, optimization, exit rules,
execution previews, monitoring, readiness, and reporting. See
[`V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md`](V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md).
