"""Deterministic raw-SVI slice fitting with explicit static-arbitrage diagnostics."""

from __future__ import annotations

import math
from enum import StrEnum
from statistics import fmean, median

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.intelligence._numpy import np


class SVIFitStatus(StrEnum):
    FITTED = "fitted"
    INSUFFICIENT_DATA = "insufficient_data"
    ARBITRAGE_VIOLATION = "arbitrage_violation"
    FAILED = "failed"


class SVIParameters(StrictModel):
    a: float
    b: float = Field(gt=0)
    rho: float = Field(gt=-1, lt=1)
    m: float
    sigma: float = Field(gt=0)

    @model_validator(mode="after")
    def require_non_negative_minimum(self) -> SVIParameters:
        minimum = self.a + self.b * self.sigma * math.sqrt(1.0 - self.rho**2)
        if minimum < -1e-12:
            raise ValueError("raw SVI minimum total variance cannot be negative")
        return self


class SVIObservation(StrictModel):
    log_forward_moneyness: float
    total_variance: float = Field(gt=0)
    weight: float = Field(default=1.0, gt=0)


class SVIArbitrageReport(StrictModel):
    minimum_total_variance: float
    minimum_density_condition: float
    butterfly_violations: int = Field(ge=0)
    grid_points: int = Field(gt=0)
    butterfly_arbitrage_free: bool


class SVIFitReport(StrictModel):
    status: SVIFitStatus
    parameters: SVIParameters | None = None
    observations: int = Field(ge=0)
    starts_evaluated: int = Field(ge=0)
    weighted_rmse: float | None = Field(default=None, ge=0)
    maximum_absolute_error: float | None = Field(default=None, ge=0)
    arbitrage: SVIArbitrageReport | None = None
    warnings: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ("FORM-SVI-RAW-001", "FORM-SVI-ARBITRAGE-001")


class CalendarArbitrageReport(StrictModel):
    maturities: int = Field(ge=0)
    grid_points: int = Field(gt=0)
    violations: int = Field(ge=0)
    minimum_forward_variance_increment: float | None = None
    calendar_arbitrage_free: bool


class ESSVIGateReport(StrictModel):
    eligible: bool
    expiration_count: int = Field(ge=0)
    minimum_quotes_per_expiration: int = Field(ge=0)
    required_expirations: int = Field(default=4, gt=0)
    required_quotes_per_expiration: int = Field(default=5, gt=0)
    reasons: tuple[str, ...] = ()


def raw_svi_total_variance(log_forward_moneyness: float, parameters: SVIParameters) -> float:
    centered = log_forward_moneyness - parameters.m
    return parameters.a + parameters.b * (
        parameters.rho * centered + math.sqrt(centered * centered + parameters.sigma**2)
    )


def _raw_svi_derivatives(k: float, parameters: SVIParameters) -> tuple[float, float]:
    centered = k - parameters.m
    root = math.sqrt(centered * centered + parameters.sigma**2)
    first = parameters.b * (parameters.rho + centered / root)
    second = parameters.b * parameters.sigma**2 / root**3
    return first, second


def svi_arbitrage_report(
    parameters: SVIParameters, *, k_min: float = -3.0, k_max: float = 3.0, points: int = 601
) -> SVIArbitrageReport:
    """Evaluate the Gatheral-Jacquier density condition on a declared finite grid."""
    if not k_min < k_max or points < 3:
        raise ValueError("arbitrage grid requires k_min < k_max and at least three points")
    variances: list[float] = []
    density_conditions: list[float] = []
    for k_value in np.linspace(k_min, k_max, points):
        k = float(k_value)
        variance = raw_svi_total_variance(k, parameters)
        first, second = _raw_svi_derivatives(k, parameters)
        variances.append(variance)
        if variance <= 0:
            density_conditions.append(float("-inf"))
            continue
        density_conditions.append(
            (1.0 - k * first / (2.0 * variance)) ** 2
            - first**2 / 4.0 * (1.0 / variance + 0.25)
            + second / 2.0
        )
    violations = sum(value < -1e-10 for value in density_conditions)
    return SVIArbitrageReport(
        minimum_total_variance=min(variances),
        minimum_density_condition=min(density_conditions),
        butterfly_violations=violations,
        grid_points=points,
        butterfly_arbitrage_free=min(variances) >= -1e-12 and violations == 0,
    )


def _linear_candidate(
    observations: list[SVIObservation], *, m: float, sigma: float
) -> SVIParameters | None:
    design = []
    targets = []
    for point in observations:
        centered = point.log_forward_moneyness - m
        scale = math.sqrt(point.weight)
        design.append([scale, scale * math.sqrt(centered**2 + sigma**2), scale * centered])
        targets.append(scale * point.total_variance)
    coefficients, *_ = np.linalg.lstsq(
        np.asarray(design, dtype=float), np.asarray(targets, dtype=float), rcond=None
    )
    a, b, c = (float(value) for value in coefficients)
    if b <= 1e-10:
        return None
    rho = max(min(c / b, 0.999), -0.999)
    minimum = a + b * sigma * math.sqrt(1.0 - rho**2)
    if minimum < 0:
        a -= minimum
    return SVIParameters(a=a, b=b, rho=rho, m=m, sigma=sigma)


def fit_svi_slice(observations: list[SVIObservation]) -> SVIFitReport:
    """Fit one raw-SVI total-variance slice with deterministic multi-start linear profiles."""
    unique_k = {point.log_forward_moneyness for point in observations}
    if len(observations) < 5 or len(unique_k) < 5:
        return SVIFitReport(
            status=SVIFitStatus.INSUFFICIENT_DATA,
            observations=len(observations),
            starts_evaluated=0,
            warnings=("SVI requires at least five distinct moneyness observations",),
        )
    k_values = sorted(unique_k)
    span = max(k_values[-1] - k_values[0], 0.1)
    m_candidates = sorted(
        {
            0.0,
            median(k_values),
            fmean(k_values),
            k_values[0] / 2.0,
            k_values[-1] / 2.0,
        }
    )
    sigma_candidates = sorted({0.02, 0.05, 0.10, 0.20, 0.40, max(0.05, span / 2.0), max(0.1, span)})
    best: tuple[float, float, SVIParameters, SVIArbitrageReport] | None = None
    evaluated = 0
    for m in m_candidates:
        for sigma in sigma_candidates:
            parameters = _linear_candidate(observations, m=m, sigma=sigma)
            if parameters is None:
                continue
            evaluated += 1
            errors = [
                raw_svi_total_variance(point.log_forward_moneyness, parameters)
                - point.total_variance
                for point in observations
            ]
            weighted_mse = sum(
                point.weight * error**2 for point, error in zip(observations, errors, strict=True)
            ) / sum(point.weight for point in observations)
            rmse = math.sqrt(weighted_mse)
            maximum_error = max(abs(error) for error in errors)
            arbitrage = svi_arbitrage_report(
                parameters,
                k_min=min(k_values[0] - 1.0, -3.0),
                k_max=max(k_values[-1] + 1.0, 3.0),
            )
            score = rmse + (0.0 if arbitrage.butterfly_arbitrage_free else 1_000.0)
            if best is None or score < best[0]:
                best = (score, maximum_error, parameters, arbitrage)
    if best is None:
        return SVIFitReport(
            status=SVIFitStatus.FAILED,
            observations=len(observations),
            starts_evaluated=evaluated,
            warnings=("No admissible raw-SVI parameter candidate was found",),
        )
    score, maximum_error, parameters, arbitrage = best
    rmse = score if arbitrage.butterfly_arbitrage_free else score - 1_000.0
    status = (
        SVIFitStatus.FITTED
        if arbitrage.butterfly_arbitrage_free
        else SVIFitStatus.ARBITRAGE_VIOLATION
    )
    warnings = (
        ()
        if status is SVIFitStatus.FITTED
        else ("Best raw-SVI fit violates the finite-grid butterfly condition",)
    )
    return SVIFitReport(
        status=status,
        parameters=parameters,
        observations=len(observations),
        starts_evaluated=evaluated,
        weighted_rmse=rmse,
        maximum_absolute_error=maximum_error,
        arbitrage=arbitrage,
        warnings=warnings,
    )


def calendar_arbitrage_report(
    slices: list[tuple[float, SVIParameters]],
    *,
    k_min: float = -2.0,
    k_max: float = 2.0,
    points: int = 401,
) -> CalendarArbitrageReport:
    """Check that total variance does not decrease between ordered maturities."""
    ordered = sorted(slices, key=lambda item: item[0])
    if len({maturity for maturity, _ in ordered}) != len(ordered):
        raise ValueError("SVI slice maturities must be unique")
    if any(maturity <= 0 for maturity, _ in ordered):
        raise ValueError("SVI slice maturities must be positive")
    increments: list[float] = []
    for k_value in np.linspace(k_min, k_max, points):
        variances = [
            raw_svi_total_variance(float(k_value), parameters) for _, parameters in ordered
        ]
        increments.extend(
            current - previous
            for previous, current in zip(variances[:-1], variances[1:], strict=True)
        )
    violations = sum(increment < -1e-10 for increment in increments)
    return CalendarArbitrageReport(
        maturities=len(ordered),
        grid_points=points,
        violations=violations,
        minimum_forward_variance_increment=min(increments) if increments else None,
        calendar_arbitrage_free=violations == 0,
    )


def evaluate_essvi_gate(
    *,
    expiration_count: int,
    minimum_quotes_per_expiration: int,
    point_in_time_quotes: bool,
    svi_slices_arbitrage_checked: bool,
) -> ESSVIGateReport:
    reasons: list[str] = []
    if expiration_count < 4:
        reasons.append("at least four expirations are required")
    if minimum_quotes_per_expiration < 5:
        reasons.append("at least five usable quotes per expiration are required")
    if not point_in_time_quotes:
        reasons.append("point-in-time quote provenance is required")
    if not svi_slices_arbitrage_checked:
        reasons.append("SVI slice arbitrage diagnostics must pass first")
    return ESSVIGateReport(
        eligible=not reasons,
        expiration_count=expiration_count,
        minimum_quotes_per_expiration=minimum_quotes_per_expiration,
        reasons=tuple(reasons),
    )
