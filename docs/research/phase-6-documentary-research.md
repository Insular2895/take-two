# Phase 6 documentary research — belief semantics and model uncertainty

Date: 2026-08-08
Status: `implemented_diagnostic_statistical_bayes_deferred`

## Conclusions

- A posterior distribution is conditional on declared data, likelihood and prior. McElreath
  chapter 2 stresses that this is a model's “small world”; internal coherence does not guarantee
  performance in the real world (printed pp. 19–46).
- Posterior predictive simulation must average outcome simulations over parameter uncertainty.
  Fixing a single parameter estimate makes predictions overconfident (McElreath chapter 3,
  printed pp. 61–68).
- Predictive scoring and out-of-sample comparison answer a predictive question, not whether a
  model is true or causal. Chapter 7 separates regularisation from predictive evaluation and
  cautions against model selection from a score alone (printed pp. 195–239).
- The existing V11 `BayesianScenarioDistribution` uses configured likelihood-like tables,
  subjective event confidence, novelty/freshness multipliers and family caps. Those are useful
  audit controls, but they do not form a fitted likelihood for observed outcomes. Its stable
  serialized name remains for compatibility; its active semantic label is now
  `configured_heuristic_belief` and “confidence” is displayed as evidence sufficiency.
- Model and parameter uncertainty must not be hidden inside Monte Carlo sampling error. The new
  ensemble sidecar separately reports within-member predictive variance, between-member mean
  variance and Monte Carlo error of the weighted mean.

## Sources inspected

- Richard McElreath, *Statistical Rethinking*, Second Edition, 2019 compilation: title page,
  contents, chapters 2–3 and chapter 7 passages on small/large worlds, prior/posterior predictive
  simulation, scoring, overfitting and model comparison.
- Glenn W. Brier, “Verification of Forecasts Expressed in Terms of Probability,” *Monthly
  Weather Review* 78(1), 1950, pp. 1–3. Primary AMS publisher record and DOI inspected.
- Larry Wasserman, *All of Statistics*, remains a secondary general statistical reference.
- Särkkä was not used: no state-space latent-state likelihood has been justified for this phase.

The local McElreath and Wasserman PDFs remained read-only.

## Implementation and validation

- `update_heuristic_scenario_beliefs` is the explicit API. The old
  `update_scenario_distribution` remains a compatibility wrapper and returns byte-equivalent
  Pydantic content for the same inputs.
- Every stochastic path set receives a deterministic SHA-256 parameter-set identity. Duplicate
  model/regime members produced under different policies can therefore remain distinct through
  valuation.
- `summarize_valuation_ensemble` propagates every model/parameter member into a typed report.
  Equal or user-supplied weights remain `diagnostic_only`; `oos_evidence_declared` requires OOS
  weights, a dataset hash and calibrated status for every member, but is not itself a validation
  certificate.
- `evaluate_binary_calibration` emits Brier score, log loss, calibration bins with Wilson bounds,
  ECE, dataset role/hash and a minimum-observation status. Synthetic calibrated and reversed
  forecasts verify directional behavior.
- No new statistical Bayesian model was added. There is no authorized outcome panel and no
  explicit generative likelihood linking GTA VI evidence to scenario outcomes. Adding priors or
  MCMC without those would create false precision.

## Limits

- Equal-weight model mixtures are sensitivity analyses, not Bayesian model averaging.
- Between-model variance depends on the chosen member set; omitted models remain unmeasured.
- Calibration bins and ECE depend on binning, while bin Wilson bounds assume iid outcomes.
- Brier/log scores measure predictive performance, not causal validity or business utility.
- The current event belief update has not been calibrated against repeated independent events;
  its displayed numbers must not be used as empirical frequencies.
- No real TTWO posterior predictive or holdout calibration has been performed.
