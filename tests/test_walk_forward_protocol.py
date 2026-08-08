from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from take_two_options.validation.walk_forward_protocol import (
    ChronologicalReturn,
    WalkForwardProtocolConfig,
    WalkForwardProtocolReport,
    run_walk_forward_protocol,
)

ROOT = Path(__file__).resolve().parents[1]


def _observations(count: int = 120) -> list[ChronologicalReturn]:
    start = datetime(2024, 1, 2, 20, tzinfo=UTC)
    return [
        ChronologicalReturn(
            observation_id=f"r-{index:03d}",
            timestamp=start + timedelta(days=index),
            available_at=start + timedelta(days=index + 1),
            log_return=((index % 9) - 4) / 1_000,
        )
        for index in range(count)
    ]


def _config(method: str = "expanding") -> WalkForwardProtocolConfig:
    return WalkForwardProtocolConfig(
        protocol_id="test-v1",
        method=method,
        minimum_train_observations=30,
        rolling_train_observations=30 if method == "rolling" else None,
        validation_observations=10,
        test_observations=10,
        step_observations=10,
        purge_observations=3,
        embargo_observations=2,
        model_id="historical_gaussian_reference",
        probability_floor=0.01,
    )


def _run(
    observations: list[ChronologicalReturn], method: str = "expanding"
) -> WalkForwardProtocolReport:
    return run_walk_forward_protocol(
        observations,
        ticker="XYZ",
        dataset_hash="a" * 64,
        config=_config(method),
        generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        license_status="authorized_internal",
    )


def test_expanding_protocol_freezes_before_validation_and_records_gaps() -> None:
    report = _run(_observations())
    assert report.windows
    for window in report.windows:
        assert window.train_observations >= 30
        assert len(window.purged_observation_ids) == 3
        assert len(window.embargoed_observation_ids) == 2
        assert window.calibrated_through < window.validation_start
        assert window.validation_end < window.test_start
        assert window.recalibrated_after_test is False
    assert report.holdout_touched is False


def test_rolling_protocol_keeps_fixed_training_length() -> None:
    report = _run(_observations(), "rolling")
    assert {window.train_observations for window in report.windows} == {30}


def test_future_mutation_cannot_change_first_frozen_model() -> None:
    observations = _observations()
    original = _run(observations)
    mutated = list(observations)
    mutated[-1] = mutated[-1].model_copy(update={"log_return": 0.9})
    changed = _run(mutated)
    assert original.windows[0].frozen_model_hash == changed.windows[0].frozen_model_hash
    assert original.windows[0].test_summary == changed.windows[0].test_summary


def test_insufficient_history_fails_closed_without_a_fixture_result() -> None:
    report = _run(_observations(20))
    assert report.status == "BLOCKED_INSUFFICIENT_HISTORY"
    assert report.windows == []


def test_committed_walk_forward_manifest_has_seven_untouched_windows() -> None:
    report = WalkForwardProtocolReport.model_validate_json(
        (ROOT / "reports/pre_opra/walk_forward_protocol_2026-08-08.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(report.windows) == 7
    assert report.status == "DIAGNOSTIC_ONLY_LICENSE_REVIEW"
    assert all(window.train_observations >= 252 for window in report.windows)
    assert all(window.recalibrated_after_test is False for window in report.windows)
    assert report.holdout_touched is False
