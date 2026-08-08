"""Deterministic empirical-return and GARCH-family calibration diagnostics."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime
from statistics import fmean, stdev, variance
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash


class PriceObservation(StrictModel):
    timestamp: datetime
    available_at: datetime
    close: float = Field(gt=0)

    @field_validator("timestamp", "available_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("price timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_availability(self) -> PriceObservation:
        if self.available_at < self.timestamp:
            raise ValueError("price cannot be available before its market timestamp")
        return self


class Interval(StrictModel):
    lower: float
    central: float
    upper: float


class EmpiricalReturnDiagnostics(StrictModel):
    price_observations: int = Field(ge=0)
    return_observations: int = Field(ge=0)
    coverage_start: datetime
    coverage_end: datetime
    arithmetic_mean_daily: float
    log_mean_daily: float
    annualized_log_mean: float
    annualized_realized_volatility: float = Field(ge=0)
    skewness: float
    excess_kurtosis: float
    largest_negative_gap: float
    largest_positive_gap: float
    maximum_drawdown: float = Field(ge=0)
    bootstrap_annualized_log_mean: Interval
    bootstrap_annualized_volatility: Interval
    bootstrap_maximum_drawdown: Interval
    bootstrap_draws: int = Field(gt=0)
    bootstrap_block_size: int = Field(gt=0)
    seed: int


class LjungBoxDiagnostic(StrictModel):
    lags: int = Field(gt=0)
    statistic: float = Field(ge=0)
    p_value: float = Field(ge=0, le=1)
    series: Literal["standardized_residuals", "squared_standardized_residuals"]


class VarCoverageDiagnostic(StrictModel):
    confidence: float = Field(gt=0, lt=1)
    observations: int = Field(gt=0)
    expected_breaches: float = Field(ge=0)
    observed_breaches: int = Field(ge=0)
    observed_rate: float = Field(ge=0, le=1)


class VolatilityModelFit(StrictModel):
    model_id: str
    family: Literal["garch_11", "gjr_garch_11"]
    innovation: Literal["gaussian", "student_t"]
    status: Literal[
        "diagnostic_fit_license_blocked",
        "fit_pending_walk_forward",
        "failed",
    ]
    observations: int = Field(ge=0)
    parameters: dict[str, float]
    standard_errors: dict[str, float]
    standard_error_status: Literal["estimated", "not_calculable"]
    log_likelihood: float | None
    aic: float | None
    bic: float | None
    converged: bool
    starts_evaluated: int = Field(ge=0)
    residual_ljung_box: LjungBoxDiagnostic | None
    squared_residual_ljung_box: LjungBoxDiagnostic | None
    var_coverage_95: VarCoverageDiagnostic | None
    one_step_variance_forecast: float | None = Field(default=None, ge=0)
    diagnostics: list[str]


class EmpiricalCalibrationReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    generated_at: datetime
    decision_cutoff: datetime
    source_ids: list[str] = Field(min_length=1)
    dataset_hash: str = Field(min_length=64, max_length=64)
    dataset_role: Literal["development_diagnostic", "walk_forward", "final_holdout"]
    license_status: Literal["authorized_internal", "to_review"]
    status: Literal[
        "DIAGNOSTIC_ONLY_LICENSE_REVIEW",
        "FIT_PENDING_WALK_FORWARD",
        "BLOCKED_INSUFFICIENT_DATA",
    ]
    empirical: EmpiricalReturnDiagnostics | None
    volatility_models: list[VolatilityModelFit]
    heston_status: Literal["BLOCKED_INSUFFICIENT_CALIBRATION_DATA"]
    blockers: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _interval(values: list[float], central: float) -> Interval:
    return Interval(
        lower=_percentile(values, 0.025),
        central=central,
        upper=_percentile(values, 0.975),
    )


def _maximum_drawdown_from_returns(returns: list[float]) -> float:
    wealth = 1.0
    peak = 1.0
    drawdown = 0.0
    for value in returns:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        drawdown = max(drawdown, 1.0 - wealth / peak)
    return drawdown


def _moments(values: list[float]) -> tuple[float, float]:
    mean = fmean(values)
    centered = [value - mean for value in values]
    second = fmean(value**2 for value in centered)
    if second <= 0:
        return 0.0, 0.0
    skewness = fmean(value**3 for value in centered) / second**1.5
    excess_kurtosis = fmean(value**4 for value in centered) / second**2 - 3.0
    return skewness, excess_kurtosis


def _block_bootstrap(
    log_returns: list[float],
    *,
    draws: int,
    block_size: int,
    seed: int,
) -> tuple[list[float], list[float], list[float]]:
    generator = random.Random(seed)
    annual_means: list[float] = []
    annual_volatilities: list[float] = []
    drawdowns: list[float] = []
    for _ in range(draws):
        sample: list[float] = []
        while len(sample) < len(log_returns):
            start = generator.randrange(0, len(log_returns) - block_size + 1)
            sample.extend(log_returns[start : start + block_size])
        sample = sample[: len(log_returns)]
        annual_means.append(fmean(sample) * 252.0)
        annual_volatilities.append(stdev(sample) * math.sqrt(252.0))
        drawdowns.append(
            _maximum_drawdown_from_returns([math.exp(value) - 1.0 for value in sample])
        )
    return annual_means, annual_volatilities, drawdowns


def empirical_diagnostics(
    observations: list[PriceObservation],
    *,
    bootstrap_draws: int,
    bootstrap_block_size: int,
    seed: int,
) -> tuple[EmpiricalReturnDiagnostics, list[float]]:
    ordered = sorted(observations, key=lambda item: item.timestamp)
    if len(ordered) < 30:
        raise ValueError("empirical diagnostics require at least 30 prices")
    prices = [item.close for item in ordered]
    simple = [
        current / previous - 1.0
        for previous, current in zip(prices[:-1], prices[1:], strict=True)
    ]
    log_returns = [math.log1p(value) for value in simple]
    skewness, excess_kurtosis = _moments(log_returns)
    annual_mean = fmean(log_returns) * 252.0
    annual_volatility = stdev(log_returns) * math.sqrt(252.0)
    bootstrap_mean, bootstrap_volatility, bootstrap_drawdown = _block_bootstrap(
        log_returns,
        draws=bootstrap_draws,
        block_size=bootstrap_block_size,
        seed=seed,
    )
    maximum_drawdown = _maximum_drawdown_from_returns(simple)
    return (
        EmpiricalReturnDiagnostics(
            price_observations=len(prices),
            return_observations=len(log_returns),
            coverage_start=ordered[0].timestamp,
            coverage_end=ordered[-1].timestamp,
            arithmetic_mean_daily=fmean(simple),
            log_mean_daily=fmean(log_returns),
            annualized_log_mean=annual_mean,
            annualized_realized_volatility=annual_volatility,
            skewness=skewness,
            excess_kurtosis=excess_kurtosis,
            largest_negative_gap=min(simple),
            largest_positive_gap=max(simple),
            maximum_drawdown=maximum_drawdown,
            bootstrap_annualized_log_mean=_interval(bootstrap_mean, annual_mean),
            bootstrap_annualized_volatility=_interval(
                bootstrap_volatility, annual_volatility
            ),
            bootstrap_maximum_drawdown=_interval(
                bootstrap_drawdown, maximum_drawdown
            ),
            bootstrap_draws=bootstrap_draws,
            bootstrap_block_size=bootstrap_block_size,
            seed=seed,
        ),
        log_returns,
    )


def _autocorrelation(values: list[float], lag: int) -> float:
    if lag >= len(values):
        return 0.0
    mean = fmean(values)
    denominator = sum((value - mean) ** 2 for value in values)
    if denominator <= 0:
        return 0.0
    return sum(
        (values[index] - mean) * (values[index - lag] - mean)
        for index in range(lag, len(values))
    ) / denominator


def _chi_square_sf_even(statistic: float, degrees: int) -> float:
    """Exact survival function for an even positive number of degrees."""
    if degrees <= 0 or degrees % 2:
        raise ValueError("degrees must be positive and even")
    half = statistic / 2.0
    return min(
        1.0,
        math.exp(-half)
        * sum(half**index / math.factorial(index) for index in range(degrees // 2)),
    )


def _ljung_box(values: list[float], *, lags: int, squared: bool) -> LjungBoxDiagnostic:
    transformed = [value**2 for value in values] if squared else values
    count = len(transformed)
    statistic = count * (count + 2) * sum(
        _autocorrelation(transformed, lag) ** 2 / (count - lag)
        for lag in range(1, lags + 1)
    )
    return LjungBoxDiagnostic(
        lags=lags,
        statistic=statistic,
        p_value=_chi_square_sf_even(statistic, lags),
        series=(
            "squared_standardized_residuals" if squared else "standardized_residuals"
        ),
    )


def _conditional_variances(
    residuals: list[float],
    *,
    omega: float,
    alpha: float,
    beta: float,
    gamma: float,
) -> list[float]:
    current = max(variance(residuals), 1e-12)
    output = [current]
    for residual in residuals[:-1]:
        current = max(
            omega
            + alpha * residual**2
            + gamma * residual**2 * float(residual < 0)
            + beta * current,
            1e-12,
        )
        output.append(current)
    return output


def _log_likelihood(
    residuals: list[float],
    conditional_variances: list[float],
    *,
    innovation: Literal["gaussian", "student_t"],
    degrees_of_freedom: float | None,
) -> float:
    if innovation == "gaussian":
        return sum(
            -0.5 * (math.log(2 * math.pi * value) + residual**2 / value)
            for residual, value in zip(residuals, conditional_variances, strict=True)
        )
    assert degrees_of_freedom is not None
    degrees = degrees_of_freedom
    constant = (
        math.lgamma((degrees + 1) / 2)
        - math.lgamma(degrees / 2)
        - 0.5 * math.log((degrees - 2) * math.pi)
    )
    return sum(
        constant
        - 0.5 * math.log(value)
        - (degrees + 1)
        / 2
        * math.log1p(residual**2 / (value * (degrees - 2)))
        for residual, value in zip(residuals, conditional_variances, strict=True)
    )


def _fit_volatility_model(
    returns: list[float],
    *,
    family: Literal["garch_11", "gjr_garch_11"],
    innovation: Literal["gaussian", "student_t"],
    license_status: Literal["authorized_internal", "to_review"],
) -> VolatilityModelFit:
    if len(returns) < 100:
        return VolatilityModelFit(
            model_id=f"{family}-{innovation}",
            family=family,
            innovation=innovation,
            status="failed",
            observations=len(returns),
            parameters={},
            standard_errors={},
            standard_error_status="not_calculable",
            log_likelihood=None,
            aic=None,
            bic=None,
            converged=False,
            starts_evaluated=0,
            residual_ljung_box=None,
            squared_residual_ljung_box=None,
            var_coverage_95=None,
            diagnostics=["At least 100 returns are required."],
        )
    mean = fmean(returns)
    residuals = [value - mean for value in returns]
    unconditional_variance = variance(residuals)
    gamma_candidates = (0.0,) if family == "garch_11" else (0.02, 0.06, 0.12, 0.20)
    degrees_candidates: tuple[float | None, ...] = (
        (None,) if innovation == "gaussian" else (5.0, 7.0, 10.0, 20.0)
    )
    best: tuple[float, dict[str, float], list[float]] | None = None
    evaluated = 0
    for alpha in (0.03, 0.06, 0.10, 0.15):
        for beta in (0.70, 0.80, 0.88, 0.93):
            for gamma in gamma_candidates:
                persistence = alpha + beta + gamma / 2
                if persistence >= 0.995:
                    continue
                omega = unconditional_variance * (1 - persistence)
                conditional = _conditional_variances(
                    residuals,
                    omega=omega,
                    alpha=alpha,
                    beta=beta,
                    gamma=gamma,
                )
                for degrees in degrees_candidates:
                    likelihood = _log_likelihood(
                        residuals,
                        conditional,
                        innovation=innovation,
                        degrees_of_freedom=degrees,
                    )
                    evaluated += 1
                    parameters = {
                        "mean": mean,
                        "omega": omega,
                        "alpha": alpha,
                        "beta": beta,
                        "persistence": persistence,
                    }
                    if family == "gjr_garch_11":
                        parameters["gamma"] = gamma
                    if degrees is not None:
                        parameters["degrees_of_freedom"] = degrees
                    if best is None or likelihood > best[0]:
                        best = (likelihood, parameters, conditional)
    assert best is not None
    likelihood, parameters, conditional = best
    standardized = [
        residual / math.sqrt(value)
        for residual, value in zip(residuals, conditional, strict=True)
    ]
    parameter_count = len(parameters)
    aic = 2 * parameter_count - 2 * likelihood
    bic = math.log(len(returns)) * parameter_count - 2 * likelihood
    breaches = sum(
        residual < -1.6448536269514722 * math.sqrt(value)
        for residual, value in zip(residuals, conditional, strict=True)
    )
    forecast = (
        parameters["omega"]
        + parameters["alpha"] * residuals[-1] ** 2
        + parameters.get("gamma", 0.0) * residuals[-1] ** 2 * float(residuals[-1] < 0)
        + parameters["beta"] * conditional[-1]
    )
    return VolatilityModelFit(
        model_id=f"{family}-{innovation}",
        family=family,
        innovation=innovation,
        status=(
            "diagnostic_fit_license_blocked"
            if license_status == "to_review"
            else "fit_pending_walk_forward"
        ),
        observations=len(returns),
        parameters=parameters,
        standard_errors={},
        standard_error_status="not_calculable",
        log_likelihood=likelihood,
        aic=aic,
        bic=bic,
        converged=True,
        starts_evaluated=evaluated,
        residual_ljung_box=_ljung_box(standardized, lags=10, squared=False),
        squared_residual_ljung_box=_ljung_box(standardized, lags=10, squared=True),
        var_coverage_95=VarCoverageDiagnostic(
            confidence=0.95,
            observations=len(returns),
            expected_breaches=len(returns) * 0.05,
            observed_breaches=breaches,
            observed_rate=breaches / len(returns),
        ),
        one_step_variance_forecast=forecast,
        diagnostics=[
            "Deterministic constrained grid fit; it is not an optimizer convergence proof.",
            "Parameter standard errors are not calculable from this grid and are not invented.",
            "In-sample AIC/BIC cannot establish predictive superiority.",
        ],
    )


def calibrate_empirical_returns(
    observations: list[PriceObservation],
    *,
    ticker: str,
    decision_cutoff: datetime,
    source_ids: list[str],
    license_status: Literal["authorized_internal", "to_review"],
    bootstrap_draws: int = 1_000,
    bootstrap_block_size: int = 5,
    seed: int = 20_260_808,
) -> EmpiricalCalibrationReport:
    eligible = [item for item in observations if item.available_at <= decision_cutoff]
    dataset_hash = stable_hash([item.model_dump(mode="json") for item in eligible])
    if len(eligible) < 30:
        return EmpiricalCalibrationReport(
            schema_version="1.0",
            report_id=f"{ticker.casefold()}-empirical-calibration-v1",
            ticker=ticker,
            generated_at=decision_cutoff,
            decision_cutoff=decision_cutoff,
            source_ids=source_ids,
            dataset_hash=dataset_hash,
            dataset_role="development_diagnostic",
            license_status=license_status,
            status="BLOCKED_INSUFFICIENT_DATA",
            empirical=None,
            volatility_models=[],
            heston_status="BLOCKED_INSUFFICIENT_CALIBRATION_DATA",
            blockers=["At least 30 point-in-time eligible prices are required."],
        )
    empirical, returns = empirical_diagnostics(
        eligible,
        bootstrap_draws=bootstrap_draws,
        bootstrap_block_size=bootstrap_block_size,
        seed=seed,
    )
    families: tuple[Literal["garch_11", "gjr_garch_11"], ...] = (
        "garch_11",
        "gjr_garch_11",
    )
    innovations: tuple[Literal["gaussian", "student_t"], ...] = (
        "gaussian",
        "student_t",
    )
    models = [
        _fit_volatility_model(
            returns,
            family=family,
            innovation=innovation,
            license_status=license_status,
        )
        for family in families
        for innovation in innovations
    ]
    blockers = [
        "Development sample was already exposed and is not a fresh final holdout.",
        "Volatility fits require chronological walk-forward validation.",
        "Heston is blocked because no eligible IV surface history is available.",
        "Grid-search parameter standard errors are not identifiable.",
    ]
    if license_status == "to_review":
        blockers.insert(0, "Account-specific historical-data rights remain to review.")
    return EmpiricalCalibrationReport(
        schema_version="1.0",
        report_id=f"{ticker.casefold()}-empirical-calibration-v1",
        ticker=ticker,
        generated_at=decision_cutoff,
        decision_cutoff=decision_cutoff,
        source_ids=source_ids,
        dataset_hash=dataset_hash,
        dataset_role="development_diagnostic",
        license_status=license_status,
        status=(
            "DIAGNOSTIC_ONLY_LICENSE_REVIEW"
            if license_status == "to_review"
            else "FIT_PENDING_WALK_FORWARD"
        ),
        empirical=empirical,
        volatility_models=models,
        heston_status="BLOCKED_INSUFFICIENT_CALIBRATION_DATA",
        blockers=blockers,
    )
