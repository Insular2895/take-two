# Phase 3 example — calibrated volatility baselines

```python
ewma = fit_ewma(train_returns)
garch = fit_garch_11(train_returns)
comparison = compare_volatility_forecasts(
    all_returns,
    train_observations=len(train_returns),
    source_id="point-in-time-series-id",
    synthetic=False,
)
```

The comparison is usable only when both reports converge and standardized-residual warnings are
reviewed. Lower QLIKE on a test suffix is evidence for that suffix, not holdout validation. Heston
remains blocked until its surface-data gate passes.
