# Phase 6 example — diagnostic model ensemble

```python
report = summarize_valuation_ensemble(
    valuations,
    weight_basis=EnsembleWeightBasis.EQUAL_SENSITIVITY,
)

assert report.claim_status == "diagnostic_only"
assert report.total_predictive_variance == (
    report.within_model_predictive_variance
    + report.between_model_predictive_variance
)
```

More paths can reduce `monte_carlo_standard_error`; they do not remove
`between_model_predictive_variance`. Equal weights are never reinterpreted as posterior model
probabilities.

A binary probability series can be assessed separately:

```python
calibration = evaluate_binary_calibration(
    predictions,
    outcomes,
    dataset_role="validation",
    dataset_hash=validation_hash,
)
```

`diagnostic_ready` means only that the configured minimum sample exists. It does not mean the
model passed an untouched holdout or became production-ready.
