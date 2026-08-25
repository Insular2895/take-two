# Phase 2 documentary research — diagnosed IV and SVI surface

Date: 2026-08-08
Status: `sourced_and_implemented_no_empirical_promotion`

## Conclusions

- Implied volatility remains a root of `model_price(volatility) - target_price`. Bisection is
  retained as the robust baseline because a valid bracket gives deterministic convergence;
  the result must expose bracket prices, iterations, residual, tolerances, and failure status.
- Raw SVI parameterizes total implied variance, not implied volatility. Gatheral–Jacquier
  equation (3.1), printed p. 5, defines the five-parameter slice and its non-negative-minimum
  constraint.
- A raw-SVI fit is not automatically arbitrage-free. Gatheral–Jacquier equation (2.1) and
  Lemma 2.2, printed p. 4, connect non-negative risk-neutral density to `g(k) >= 0`, with an
  asymptotic boundary condition. Calendar-spread freedom requires total variance to be
  non-decreasing in maturity (Lemma 2.1, printed p. 3).
- eSSVI is useful only after enough point-in-time expirations and quote density exist. The
  current synthetic TTWO chain cannot measure its incremental value, so the code implements a
  gate, not an eSSVI calibration.

## Sources inspected

- Endre Süli and David Mayers, *An Introduction to Numerical Analysis*, section 1.6,
  printed pp. 28–29: bisection robustness and bracket contraction.
- Jim Gatheral and Antoine Jacquier, “Arbitrage-free SVI volatility surfaces,”
  arXiv:1204.0646v4, sections 2.1, 2.2 and 3.1, printed pp. 3–5. The PDF and formulas were
  inspected directly; the arXiv record reports submission in 2012 and revision in 2013.
- Pierre Cohort, Jacopo Corbetta, Claude Martini and Ismail Laachir, “Robust calibration and
  arbitrage-free interpolation of SSVI slices,” arXiv:1804.04924v2: the abstract explicitly
  requires butterfly/calendar consistency across slices.
- Arianna Mingone, “No arbitrage global parametrization for the eSSVI volatility surface,”
  arXiv:2204.00312: global eSSVI is a separate calibration problem, not an automatic extension
  of a sparse raw-SVI fit.

## Implementation and alternatives

- `solve_implied_volatility` returns structured failure rather than a misleading scalar.
- `historical_option_analytics` consumes the diagnosed solver while preserving its historical
  output schema.
- `fit_svi_slice` uses deterministic multi-start profiles: for each `(m, sigma)` candidate,
  the remaining raw-SVI coefficients are fitted by weighted least squares. This avoids adding
  SciPy and provides a reproducible baseline; it is not claimed to be a globally optimal
  production calibration.
- Butterfly and calendar tests are finite-grid diagnostics. Their grid and violation counts
  are retained in reports.
- The silent `0.45` path-repricing fallback was removed. Missing IV now fails closed; an
  upstream explicit imputation must carry provenance and lower the eventual decision grade.

## Limits

- The SVI fitter is validated on synthetic known parameters, not a real TTWO point-in-time
  chain.
- Finite-grid `g(k)` checks do not prove the continuous-domain asymptotic condition.
- American-option IV is model-dependent and can be weakly identified at very low vega.
- eSSVI is not implemented. Its gate does not imply it should be implemented later.
