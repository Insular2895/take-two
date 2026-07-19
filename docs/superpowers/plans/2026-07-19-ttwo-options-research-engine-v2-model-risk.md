# TTWO Options Research Engine V2: model-risk implementation plan

Status: implementation authorized; research outputs remain `screen_grade` until source-backed TTWO calibration and out-of-sample evidence exist.

## Objective

Replace the V1 European/GBM approximations with an auditable research stack that can:

- price American equity options with a recognized numerical engine;
- represent discrete dividends and flag early exercise, assignment, and pin exposure;
- interpolate an explicit volatility surface;
- compare GBM, Merton jump diffusion, and Heston-style stochastic-volatility paths;
- attribute scenario P&L through exact sequential repricing plus a visible residual;
- calibrate only the parameters supported by supplied history;
- run train/test backtests with executable bid/ask costs and look-ahead controls.

## Guardrails

- No order API, order payload, sizing recommendation, or live-execution status.
- Synthetic fixtures prove mechanics only and never count as empirical validation.
- Heston calibration is reported as insufficient when variance/surface history is absent.
- Assignment and pin outputs are risk levels and reasons, not invented probabilities.
- A report cannot become decision-ready merely because a model executes successfully.

## Implementation

1. Extend canonical Pydantic contracts with pricing, dividend, volatility-surface, model-readiness, calibration, exercise-risk, and backtest types.
2. Use QuantLib finite differences for American exercise and a matched European benchmark; compute stable finite-difference Greeks from the selected pricing engine.
3. Add surface interpolation and coverage diagnostics, then route option repricing through the selected surface/model.
4. Add seeded GBM, Merton, and full-truncation Heston simulations with explicit parameter provenance and calibration status.
5. Replace Greek-only attribution with a sequential repricing waterfall and retain approximation fields for transparency.
6. Add realized-volatility/jump heuristic calibration and reject unsupported Heston calibration.
7. Add deterministic train/test backtesting with no-look-ahead validation and executable entry/exit pricing.
8. Integrate V2 diagnostics into validation, scoring, report rendering, and CLI commands.
9. Add focused unit/property/integration tests and regenerate JSON/Markdown artifacts.
10. Update project documentation and the vault strategy note without changing its `draft_to_validate` decision status.

## Acceptance criteria

- American put value is not below its European benchmark within numerical tolerance.
- A non-dividend American call converges near its European value.
- Dividend/low-extrinsic short calls and near-strike expiry positions receive explainable human-review gates.
- Jump and Heston simulations are seeded, finite, and expose model assumptions.
- Attribution components reconcile exactly to reported P&L through a visible residual.
- Backtests reject look-ahead data and report train/test metrics separately.
- Synthetic outputs are labeled `illustrative`, `screen_grade`, and non-authorizing.
- Existing V1 tests remain green alongside the V2 suite; Ruff, mypy, and package checks pass.

## Primary references

- Cox, Ross, and Rubinstein (1979), *Option Pricing: A Simplified Approach*.
- Merton (1976), *Option Pricing When Underlying Stock Returns Are Discontinuous*.
- Heston (1993), *A Closed-Form Solution for Options with Stochastic Volatility*.
- OCC, *Characteristics and Risks of Standardized Options* and short-call risk material.
- QuantLib project documentation and Python distribution metadata.
