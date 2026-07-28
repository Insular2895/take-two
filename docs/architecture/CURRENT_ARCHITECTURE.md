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
V10.1 report + V11 policy + normalized events + optional factor history
                                |
             provenance-aware data hub and connector status
                                |
      deduplicated/capped Bayesian scenarios -> four regime weights
                                |
  GBM / Dupire local vol / Heston / Heston+jumps path ensembles
                                |
 conditional option repricing + exits + multi-model robustness
                                |
       cost/adverse/rupture/CVaR/holdout/paper promotion gates
                                |
 exact integer allocation under budget/loss/contracts/liquidity
                                |
      cash/no-trade baseline + explainable position monitoring
                                |
 JSON + Markdown + HTML + blocked preview-only IBKR artifacts
```

The V11 package is `intelligence`. Its modules separate schemas, data
connectors, Bayesian updates, covariance, stochastic paths, local-volatility
calibration, valuation, validation, optimization, execution previews,
monitoring, and reporting. See
[`V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md`](V11_PROBABILISTIC_STRATEGY_INTELLIGENCE.md).
