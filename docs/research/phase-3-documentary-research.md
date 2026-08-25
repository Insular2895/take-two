# Phase 3 documentary research — robust calibration and time series

Date: 2026-08-08
Status: `sourced_and_implemented_no_empirical_promotion`

## Conclusions

- Volatility is latent and conditional; realized returns and option-implied volatility are not
  interchangeable. Tsay chapter 3 distinguishes observed-return volatility models from implied
  volatility and lays out the sequence: mean equation, ARCH-effects check, volatility model,
  then residual diagnostics (printed pp. 110–114).
- GARCH(1,1) uses `h_t = omega + alpha * residual_(t-1)^2 + beta * h_(t-1)` with positive
  coefficients and stationary persistence below one (Tsay equation 3.16, printed p. 132).
  Standardized residuals and their squares must be checked after fitting (printed pp. 119–120,
  134–139); likelihood alone is insufficient.
- Forecast comparisons must be chronological. Historical rolling variance, EWMA and GARCH now
  produce one-step predictions before observing the next squared return and are compared with
  variance MSE and QLIKE.
- Bergomi chapter 6 shows that native Heston is a one-factor instantaneous-variance model and
  cannot accommodate a general variance term structure (printed pp. 201–205). A close-only or
  one-surface calibration therefore remains blocked.

## Sources inspected

- Ruey S. Tsay, *Analysis of Financial Time Series*, Third Edition, Wiley, 2010, chapter 3,
  especially sections 3.1–3.5, printed pp. 110–139.
- Lorenzo Bergomi, *Stochastic Volatility Modeling*, local chapter 6 fragment, “An example of
  one-factor dynamics: the Heston model,” printed pp. 201–205.
- Phase 2 primary SVI sources remain relevant to the required point-in-time surface quality.

The PDF sources were read-only and extracted with Ghostscript `txtwrite`; no source was
modified.

## Implementation and alternatives

- `fit_ewma` profiles a small declared decay grid and returns likelihood plus standardized
  residual diagnostics.
- `fit_garch_11` uses a deterministic constrained grid over `(alpha, beta)`, derives `omega`
  from unconditional variance, rejects persistence at or above 0.995, and records every start.
- This grid search is a transparent reproducible baseline, not a replacement for a bounded
  optimizer with Hessian/profile-likelihood uncertainty.
- `compare_volatility_forecasts` compares rolling historical variance, EWMA and GARCH on an
  untouched chronological suffix. Synthetic runs stay labeled synthetic.
- `evaluate_heston_calibration_gate` requires multiple surface dates, expirations, strikes,
  point-in-time provenance, and constrained multi-start diagnostics before eligibility.

## Limits

- Gaussian GARCH does not model heavy tails or leverage; warnings flag persistence and remaining
  squared-residual dependence.
- Lag-1 diagnostics are screens, not full Ljung–Box tests with calibrated p-values.
- No real TTWO OOS panel is present, so no model is promoted as predictively superior.
- Heston is not fitted; eligibility only means the minimum evidence contract is satisfied.
