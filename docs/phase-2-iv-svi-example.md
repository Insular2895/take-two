# Phase 2 example — diagnosed IV and SVI

```python
iv = solve_implied_volatility(price_function, target_price=observed_mid)
if not iv.converged:
    # Keep the quote blocked; do not invent an IV.
    raise ValueError(iv.status.value)

fit = fit_svi_slice(total_variance_observations)
if fit.status != SVIFitStatus.FITTED:
    # Preserve the observed-quote/interpolation baseline and lower the evidence grade.
    raise ValueError(fit.status.value)
```

The result contains the bracket, residual, iterations, weighted RMSE, maximum fit error, and
finite-grid butterfly diagnostic. The eSSVI eligibility report remains false for the current
synthetic two-expiration chain.
