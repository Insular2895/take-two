from __future__ import annotations

import math
import random

import pytest

from take_two_options.quantitative.calibration import (
    CalibrationFitStatus,
    compare_volatility_forecasts,
    evaluate_heston_calibration_gate,
    ewma_variances,
    fit_ewma,
    fit_garch_11,
)
from take_two_options.quantitative.contracts import Measure


def _garch_returns(
    *, omega: float, alpha: float, beta: float, observations: int, seed: int
) -> list[float]:
    rng = random.Random(seed)
    conditional_variance = omega / (1.0 - alpha - beta)
    values: list[float] = []
    previous = 0.0
    for _ in range(observations):
        conditional_variance = omega + alpha * previous**2 + beta * conditional_variance
        previous = math.sqrt(conditional_variance) * rng.gauss(0.0, 1.0)
        values.append(previous)
    return values


def test_ewma_is_lookahead_safe_deterministic_and_diagnosed() -> None:
    values = [0.01, -0.02, 0.015, -0.005] * 20
    variances = ewma_variances(values, decay=0.94)
    report = fit_ewma(values)

    assert len(variances) == len(values)
    assert all(value > 0 for value in variances)
    assert variances[1] == pytest.approx(0.94 * variances[0] + 0.06 * values[0] ** 2)
    assert report.status is CalibrationFitStatus.FITTED
    assert report.measure is Measure.REAL_WORLD
    assert report.residual_diagnostics is not None


def test_garch_recovers_stationary_synthetic_parameters_with_diagnostics() -> None:
    values = _garch_returns(
        omega=0.000004,
        alpha=0.08,
        beta=0.88,
        observations=1_200,
        seed=41,
    )

    report = fit_garch_11(values)

    assert report.status is CalibrationFitStatus.FITTED
    assert report.parameters["alpha"] == pytest.approx(0.08, abs=0.05)
    assert report.parameters["beta"] == pytest.approx(0.88, abs=0.08)
    assert report.parameters["persistence"] < 0.995
    assert report.residual_diagnostics is not None
    assert math.isfinite(report.gaussian_negative_log_likelihood or float("nan"))


def test_rolling_forecast_comparison_is_reproducible_and_labeled_synthetic() -> None:
    values = _garch_returns(
        omega=0.000004,
        alpha=0.08,
        beta=0.88,
        observations=500,
        seed=7,
    )
    first = compare_volatility_forecasts(
        values,
        train_observations=350,
        source_id="synthetic-garch-test",
        synthetic=True,
    )
    second = compare_volatility_forecasts(
        values,
        train_observations=350,
        source_id="synthetic-garch-test",
        synthetic=True,
    )

    assert first == second
    assert first.status == "completed_synthetic"
    assert {metric.model for metric in first.metrics} == {
        "historical_variance",
        "ewma",
        "garch_11_gaussian",
    }
    assert all(math.isfinite(metric.qlike) for metric in first.metrics)
    assert "predictive validity" in first.warnings[0]


def test_garch_and_heston_fail_closed_when_evidence_is_insufficient() -> None:
    garch = fit_garch_11([0.01, -0.01] * 20)
    blocked = evaluate_heston_calibration_gate(
        surface_dates=1,
        expirations_per_date=2,
        strikes_per_expiration=3,
        point_in_time_quotes=False,
        constrained_multistart_available=False,
    )
    eligible = evaluate_heston_calibration_gate(
        surface_dates=20,
        expirations_per_date=4,
        strikes_per_expiration=5,
        point_in_time_quotes=True,
        constrained_multistart_available=True,
    )

    assert garch.status is CalibrationFitStatus.INSUFFICIENT_DATA
    assert not blocked.eligible and len(blocked.reasons) == 5
    assert eligible.eligible
