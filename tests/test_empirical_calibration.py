from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

from take_two_options.empirical_calibration import (
    EmpiricalCalibrationReport,
    PriceObservation,
    calibrate_empirical_returns,
)

ROOT = Path(__file__).resolve().parents[1]


def _prices(count: int = 180) -> list[PriceObservation]:
    start = datetime(2024, 1, 2, 21, tzinfo=UTC)
    price = 100.0
    output: list[PriceObservation] = []
    for index in range(count):
        timestamp = start + timedelta(days=index)
        shock = 0.002 * math.sin(index / 4) + (0.035 if index % 47 == 0 else 0.0)
        price *= math.exp(0.0003 + shock)
        output.append(
            PriceObservation(
                timestamp=timestamp,
                available_at=timestamp + timedelta(days=1),
                close=price,
            )
        )
    return output


def test_empirical_calibration_is_deterministic_and_never_claims_holdout() -> None:
    observations = _prices()
    cutoff = observations[-1].available_at
    first = calibrate_empirical_returns(
        observations,
        ticker="XYZ",
        decision_cutoff=cutoff,
        source_ids=["synthetic-test"],
        license_status="authorized_internal",
        bootstrap_draws=50,
        seed=7,
    )
    second = calibrate_empirical_returns(
        observations,
        ticker="XYZ",
        decision_cutoff=cutoff,
        source_ids=["synthetic-test"],
        license_status="authorized_internal",
        bootstrap_draws=50,
        seed=7,
    )
    assert first == second
    assert first.dataset_role == "development_diagnostic"
    assert first.status == "FIT_PENDING_WALK_FORWARD"
    assert len(first.volatility_models) == 4
    assert all(model.one_step_variance_forecast > 0 for model in first.volatility_models)
    assert all(model.standard_error_status == "not_calculable" for model in first.volatility_models)
    assert first.heston_status == "BLOCKED_INSUFFICIENT_CALIBRATION_DATA"


def test_post_cutoff_price_is_excluded_from_dataset_hash_and_counts() -> None:
    observations = _prices(40)
    cutoff = observations[-2].available_at
    report = calibrate_empirical_returns(
        observations,
        ticker="XYZ",
        decision_cutoff=cutoff,
        source_ids=["synthetic-test"],
        license_status="to_review",
        bootstrap_draws=20,
    )
    assert report.empirical is not None
    assert report.empirical.price_observations == 39
    assert report.status == "DIAGNOSTIC_ONLY_LICENSE_REVIEW"


def test_committed_empirical_report_matches_contract_and_exposes_limits() -> None:
    report = EmpiricalCalibrationReport.model_validate_json(
        (ROOT / "reports/pre_opra/empirical_calibration_2026-08-08.json").read_text(
            encoding="utf-8"
        )
    )
    assert report.empirical is not None
    assert report.empirical.return_observations == 615
    assert report.empirical.bootstrap_annualized_log_mean.lower < 0
    assert report.status == "DIAGNOSTIC_ONLY_LICENSE_REVIEW"
    assert all(
        model.status == "diagnostic_fit_license_blocked"
        for model in report.volatility_models
    )
