# TTWO model calibration report

- Evidence class: `illustrative_calibration`
- Training cutoff: `2026-02-20T22:00:00+00:00`
- Model readiness: `screen_grade`
- Order capability: `forbidden`

## Models

- `gbm`: `illustrative`; observations=11; annualized_volatility=0.66058
  - Close-to-close log returns; 252 trading-day annualization
- `merton_jump_diffusion`: `illustrative`; observations=11; jump_intensity=45.8182, jump_mean=0.00529522, jump_volatility=0.130033, diffusion_volatility=0.112274
  - Heuristic jump classification at 1.5 sigma
  - Threshold calibration is screen-grade and sensitive to sample length
- `heston_full_truncation`: `insufficient_data`; observations=11; none
  - Close history alone does not identify a robust Heston parameter set
  - Timestamped option-surface history or another variance proxy is required

## Warnings

- Calibration is not an out-of-sample validation
- Heston parameters were deliberately not inferred from insufficient evidence
- 2 point(s) excluded by timestamp/look-ahead controls
