"""Diagnosed real-world volatility baselines and calibration gates."""

from __future__ import annotations

import math
from enum import StrEnum
from statistics import fmean, variance
from typing import Literal

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.quantitative.contracts import Measure


class CalibrationFitStatus(StrEnum):
    FITTED = "fitted"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class ResidualDiagnostics(StrictModel):
    mean: float
    variance: float = Field(ge=0)
    lag1_autocorrelation: float
    squared_lag1_autocorrelation: float
    maximum_absolute: float = Field(ge=0)


class CalibrationReport(StrictModel):
    model: str = Field(min_length=1)
    status: CalibrationFitStatus
    measure: Literal[Measure.REAL_WORLD] = Measure.REAL_WORLD
    observations: int = Field(ge=0)
    parameters: dict[str, float] = Field(default_factory=dict)
    gaussian_negative_log_likelihood: float | None = None
    residual_diagnostics: ResidualDiagnostics | None = None
    starts_evaluated: int = Field(ge=0)
    converged: bool
    warnings: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ("FORM-GARCH-001",)


class ForecastMetric(StrictModel):
    model: str
    observations: int = Field(ge=0)
    mean_squared_variance_error: float = Field(ge=0)
    qlike: float


class VolatilityBacktestReport(StrictModel):
    status: str
    train_observations: int = Field(ge=0)
    test_observations: int = Field(ge=0)
    synthetic: bool
    source_id: str = Field(min_length=1)
    metrics: tuple[ForecastMetric, ...] = ()
    warnings: tuple[str, ...] = ()


class HestonCalibrationGate(StrictModel):
    eligible: bool
    surface_dates: int = Field(ge=0)
    expirations_per_date: int = Field(ge=0)
    strikes_per_expiration: int = Field(ge=0)
    reasons: tuple[str, ...] = ()


def _lag1_autocorrelation(values: list[float]) -> float:
    if len(values) < 3:
        return 0.0
    left = values[:-1]
    right = values[1:]
    left_mean = fmean(left)
    right_mean = fmean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / denominator if denominator > 0 else 0.0


def _residual_diagnostics(values: list[float]) -> ResidualDiagnostics:
    return ResidualDiagnostics(
        mean=fmean(values),
        variance=variance(values) if len(values) >= 2 else 0.0,
        lag1_autocorrelation=_lag1_autocorrelation(values),
        squared_lag1_autocorrelation=_lag1_autocorrelation([value**2 for value in values]),
        maximum_absolute=max((abs(value) for value in values), default=0.0),
    )


def ewma_variances(
    returns: list[float], *, decay: float = 0.94, initial_variance: float | None = None
) -> tuple[float, ...]:
    """Return one-step conditional variances using only information available at t-1."""
    if len(returns) < 2:
        raise ValueError("EWMA requires at least two returns")
    if not 0 < decay < 1:
        raise ValueError("EWMA decay must lie strictly between zero and one")
    starting_variance = variance(returns) if initial_variance is None else initial_variance
    if starting_variance <= 0 or not math.isfinite(starting_variance):
        raise ValueError("EWMA initial variance must be finite and positive")
    output = [starting_variance]
    for previous_return in returns[:-1]:
        output.append(decay * output[-1] + (1.0 - decay) * previous_return**2)
    return tuple(output)


def _gaussian_nll(residuals: list[float], variances: tuple[float, ...]) -> float:
    return 0.5 * sum(
        math.log(conditional_variance) + residual**2 / conditional_variance
        for residual, conditional_variance in zip(residuals, variances, strict=True)
    )


def fit_ewma(
    returns: list[float], *, decay_candidates: tuple[float, ...] = (0.85, 0.90, 0.94, 0.97)
) -> CalibrationReport:
    if len(returns) < 30:
        return CalibrationReport(
            model="ewma",
            status=CalibrationFitStatus.INSUFFICIENT_DATA,
            observations=len(returns),
            starts_evaluated=0,
            converged=False,
            warnings=("EWMA calibration requires at least 30 returns",),
        )
    mean = fmean(returns)
    residuals = [value - mean for value in returns]
    best: tuple[float, float, tuple[float, ...]] | None = None
    for decay in decay_candidates:
        conditional_variances = ewma_variances(residuals, decay=decay)
        nll = _gaussian_nll(residuals, conditional_variances)
        if best is None or nll < best[0]:
            best = (nll, decay, conditional_variances)
    assert best is not None
    nll, decay, conditional_variances = best
    standardized = [
        residual / math.sqrt(conditional_variance)
        for residual, conditional_variance in zip(residuals, conditional_variances, strict=True)
    ]
    return CalibrationReport(
        model="ewma",
        status=CalibrationFitStatus.FITTED,
        observations=len(returns),
        parameters={
            "mean": mean,
            "decay": decay,
            "last_variance": conditional_variances[-1],
        },
        gaussian_negative_log_likelihood=nll,
        residual_diagnostics=_residual_diagnostics(standardized),
        starts_evaluated=len(decay_candidates),
        converged=True,
        source_ids=("FORM-EWMA-001", "book-tsay-analysis-financial-time-series"),
    )


def _garch_variances(
    residuals: list[float], *, omega: float, alpha: float, beta: float
) -> tuple[float, ...]:
    current = max(variance(residuals), 1e-12)
    output = [current]
    for previous_residual in residuals[:-1]:
        current = max(omega + alpha * previous_residual**2 + beta * current, 1e-12)
        output.append(current)
    return tuple(output)


def fit_garch_11(
    returns: list[float],
    *,
    alpha_candidates: tuple[float, ...] = (0.03, 0.05, 0.08, 0.12, 0.18),
    beta_candidates: tuple[float, ...] = (0.70, 0.80, 0.85, 0.88, 0.90, 0.94),
) -> CalibrationReport:
    """Fit a stationary Gaussian GARCH(1,1) by deterministic constrained grid search."""
    if len(returns) < 100:
        return CalibrationReport(
            model="garch_11_gaussian",
            status=CalibrationFitStatus.INSUFFICIENT_DATA,
            observations=len(returns),
            starts_evaluated=0,
            converged=False,
            warnings=("GARCH calibration requires at least 100 returns",),
        )
    mean = fmean(returns)
    residuals = [value - mean for value in returns]
    unconditional_variance = variance(residuals)
    if unconditional_variance <= 0:
        return CalibrationReport(
            model="garch_11_gaussian",
            status=CalibrationFitStatus.FAILED,
            observations=len(returns),
            starts_evaluated=0,
            converged=False,
            warnings=("GARCH calibration requires non-zero return variance",),
        )
    best: tuple[float, float, float, float, tuple[float, ...]] | None = None
    evaluated = 0
    for alpha in alpha_candidates:
        for beta in beta_candidates:
            persistence = alpha + beta
            if persistence >= 0.995:
                continue
            omega = unconditional_variance * (1.0 - persistence)
            conditional_variances = _garch_variances(residuals, omega=omega, alpha=alpha, beta=beta)
            nll = _gaussian_nll(residuals, conditional_variances)
            evaluated += 1
            if best is None or nll < best[0]:
                best = (nll, omega, alpha, beta, conditional_variances)
    if best is None:
        return CalibrationReport(
            model="garch_11_gaussian",
            status=CalibrationFitStatus.FAILED,
            observations=len(returns),
            starts_evaluated=evaluated,
            converged=False,
            warnings=("No stationary GARCH candidate was available",),
        )
    nll, omega, alpha, beta, conditional_variances = best
    standardized = [
        residual / math.sqrt(conditional_variance)
        for residual, conditional_variance in zip(residuals, conditional_variances, strict=True)
    ]
    persistence = alpha + beta
    diagnostics = _residual_diagnostics(standardized)
    warnings: list[str] = []
    if persistence >= 0.98:
        warnings.append("Near-unit GARCH persistence makes long-run variance fragile")
    if abs(diagnostics.squared_lag1_autocorrelation) > 0.10:
        warnings.append("Squared standardized residuals retain material lag-1 dependence")
    return CalibrationReport(
        model="garch_11_gaussian",
        status=CalibrationFitStatus.FITTED,
        observations=len(returns),
        parameters={
            "mean": mean,
            "omega": omega,
            "alpha": alpha,
            "beta": beta,
            "persistence": persistence,
            "unconditional_variance": omega / (1.0 - persistence),
            "last_variance": conditional_variances[-1],
        },
        gaussian_negative_log_likelihood=nll,
        residual_diagnostics=diagnostics,
        starts_evaluated=evaluated,
        converged=True,
        warnings=tuple(warnings),
    )


def compare_volatility_forecasts(
    returns: list[float],
    *,
    train_observations: int,
    source_id: str,
    synthetic: bool,
    historical_window: int = 40,
) -> VolatilityBacktestReport:
    """Compare one-step variance forecasts without using future observations."""
    if train_observations < 100 or len(returns) - train_observations < 20:
        return VolatilityBacktestReport(
            status="insufficient_data",
            train_observations=min(train_observations, len(returns)),
            test_observations=max(len(returns) - train_observations, 0),
            synthetic=synthetic,
            source_id=source_id,
            warnings=("Need at least 100 train and 20 test returns",),
        )
    train = returns[:train_observations]
    test = returns[train_observations:]
    ewma = fit_ewma(train)
    garch = fit_garch_11(train)
    if not ewma.converged or not garch.converged:
        return VolatilityBacktestReport(
            status="calibration_failed",
            train_observations=len(train),
            test_observations=len(test),
            synthetic=synthetic,
            source_id=source_id,
            warnings=("EWMA or GARCH training calibration failed",),
        )
    mean = garch.parameters["mean"]
    history = [value - mean for value in train]
    ewma_variance = ewma.parameters["last_variance"]
    garch_variance = garch.parameters["last_variance"]
    forecasts: dict[str, list[float]] = {
        "historical_variance": [],
        "ewma": [],
        "garch_11_gaussian": [],
    }
    realized: list[float] = []
    for value in test:
        forecasts["historical_variance"].append(max(variance(history[-historical_window:]), 1e-12))
        forecasts["ewma"].append(max(ewma_variance, 1e-12))
        forecasts["garch_11_gaussian"].append(max(garch_variance, 1e-12))
        residual = value - mean
        realized.append(residual**2)
        ewma_variance = (
            ewma.parameters["decay"] * ewma_variance
            + (1.0 - ewma.parameters["decay"]) * residual**2
        )
        garch_variance = (
            garch.parameters["omega"]
            + garch.parameters["alpha"] * residual**2
            + garch.parameters["beta"] * garch_variance
        )
        history.append(residual)
    metrics = tuple(
        ForecastMetric(
            model=model,
            observations=len(test),
            mean_squared_variance_error=fmean(
                (forecast - actual) ** 2
                for forecast, actual in zip(predictions, realized, strict=True)
            ),
            qlike=fmean(
                math.log(forecast) + actual / forecast
                for forecast, actual in zip(predictions, realized, strict=True)
            ),
        )
        for model, predictions in forecasts.items()
    )
    warnings = (
        ("Synthetic comparison cannot establish TTWO predictive validity",) if synthetic else ()
    )
    return VolatilityBacktestReport(
        status="completed_synthetic" if synthetic else "completed_pending_validation",
        train_observations=len(train),
        test_observations=len(test),
        synthetic=synthetic,
        source_id=source_id,
        metrics=metrics,
        warnings=warnings,
    )


def evaluate_heston_calibration_gate(
    *,
    surface_dates: int,
    expirations_per_date: int,
    strikes_per_expiration: int,
    point_in_time_quotes: bool,
    constrained_multistart_available: bool,
) -> HestonCalibrationGate:
    reasons: list[str] = []
    if surface_dates < 20:
        reasons.append("at least 20 point-in-time surface dates are required")
    if expirations_per_date < 4:
        reasons.append("at least four expirations per date are required")
    if strikes_per_expiration < 5:
        reasons.append("at least five strikes per expiration are required")
    if not point_in_time_quotes:
        reasons.append("point-in-time bid/ask provenance is required")
    if not constrained_multistart_available:
        reasons.append("constrained multi-start optimization diagnostics are required")
    return HestonCalibrationGate(
        eligible=not reasons,
        surface_dates=surface_dates,
        expirations_per_date=expirations_per_date,
        strikes_per_expiration=strikes_per_expiration,
        reasons=tuple(reasons),
    )
