from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.intelligence.backtesting import (
    load_walk_forward_dataset,
    run_walk_forward,
)
from take_two_options.intelligence.calibration import validate_historical_dataset
from take_two_options.intelligence.data_hub import UnifiedDataHub
from take_two_options.intelligence.monitoring import replay_position_trajectory
from take_two_options.intelligence.schemas import (
    DataDomain,
    FreshnessStatus,
    PositionTrajectoryFixture,
    SourceProvenance,
    UnifiedObservation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_committed_json_schemas_are_current_and_strict() -> None:
    schema_paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert {path.name for path in schema_paths} == {
        "backtest_report.schema.json",
        "calibration_report.schema.json",
        "event.schema.json",
        "historical_dataset_manifest.schema.json",
        "model_validation.schema.json",
        "observation.schema.json",
        "pre_opra_config.schema.json",
        "readiness.schema.json",
    }
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_calibration_and_walk_forward_examples_cannot_claim_validation() -> None:
    dataset, quality = validate_historical_dataset(
        ROOT / "fixtures/v11/historical_calibration.example.json"
    )
    assert dataset is not None and dataset.synthetic
    assert quality.status == "FIXTURE_ONLY_NOT_CALIBRATED"
    report = run_walk_forward(
        load_walk_forward_dataset(ROOT / "fixtures/v11/walk_forward.example.json")
    )
    assert report.status == "FIXTURE_ONLY_NOT_VALIDATED"
    assert not report.missing_baselines
    assert report.final_holdout_used_for_tuning is False


def test_position_trajectory_replay_is_chronological_and_advisory() -> None:
    fixture = PositionTrajectoryFixture.model_validate_json(
        (ROOT / "fixtures/v11/position_trajectory.example.json").read_text(
            encoding="utf-8"
        )
    )
    report = replay_position_trajectory(fixture)
    assert [item.action.value for item in report.reports] == [
        "HOLD",
        "WATCH",
        "THESIS_INVALIDATED",
    ]
    assert report.order_capability == "forbidden"
    assert report.human_confirmation_required is True


def test_position_trajectory_rejects_out_of_order_snapshots() -> None:
    payload = json.loads(
        (ROOT / "fixtures/v11/position_trajectory.example.json").read_text(
            encoding="utf-8"
        )
    )
    payload["snapshots"] = list(reversed(payload["snapshots"]))
    with pytest.raises(ValidationError, match="unique and chronological"):
        PositionTrajectoryFixture.model_validate(payload)


def test_observation_error_fixture_covers_every_required_failure_mode() -> None:
    payload = json.loads(
        (ROOT / "fixtures/v11/observation_error_cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert {case["case_id"] for case in payload["cases"]} == {
        "future_timestamp",
        "post_cutoff",
        "quote_missing_timestamp",
        "unit_mismatch",
        "duplicate",
        "unknown_source",
        "stale",
    }
    missing_timestamp = next(
        case for case in payload["cases"] if case["case_id"] == "quote_missing_timestamp"
    )
    with pytest.raises(ValidationError):
        UnifiedObservation.model_validate(missing_timestamp["raw_observations"][0])


def test_observation_error_fixture_produces_auditable_data_hub_diagnostics() -> None:
    payload = json.loads(
        (ROOT / "fixtures/v11/observation_error_cases.json").read_text(
            encoding="utf-8"
        )
    )
    cutoff = datetime.fromisoformat(payload["cutoff"].replace("Z", "+00:00"))
    source = SourceProvenance.model_validate(payload["source"])
    cases = {
        case["case_id"]: case
        for case in payload["cases"]
        if "observations" in case
    }
    observations = [
        UnifiedObservation.model_validate(observation)
        for case in cases.values()
        for observation in case["observations"]
    ]
    snapshot = UnifiedDataHub(
        ["TTWO.SPOT"],
        freshness_hours_by_domain={DataDomain.MARKET: 24.0},
    ).collect(
        ticker="TTWO",
        as_of=cutoff,
        connectors=[],
        seed_sources=[source],
        seed_observations=observations,
        checked_at=cutoff,
    )
    warnings = " ".join(snapshot.warnings).lower()
    assert "future/post-cutoff" in warnings
    assert "unit mismatch" in warnings
    assert "duplicate" in warnings
    assert "unknown source" in warnings
    assert any(
        observation.freshness_status is FreshnessStatus.STALE
        for observation in snapshot.observations
    )


def test_readiness_and_commercial_docs_preserve_the_research_boundary() -> None:
    readiness = (ROOT / "docs/READINESS.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs/COMMERCIALIZATION_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    security = (ROOT / "docs/SECURITY.md").read_text(encoding="utf-8")
    assert "COMMERCIAL_RESEARCH_PRODUCT" in readiness
    assert "automatic_execution" in readiness
    assert "- [x]" not in checklist.lower()
    assert "order_capability=forbidden" in security
    assert datetime.now(UTC).tzinfo is not None
