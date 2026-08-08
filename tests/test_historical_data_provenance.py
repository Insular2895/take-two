from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.historical_data.contracts import (
    HistoricalDatasetManifest,
    ObservationState,
    PointInTimeObservation,
    audit_point_in_time,
)
from take_two_options.historical_data.inventory import inventory_marketdata_cache

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = datetime(2026, 1, 2, 20, tzinfo=UTC)


def _observation(
    observation_id: str,
    *,
    state: ObservationState = ObservationState.OBSERVED,
    value: float | None = 100.0,
    available_at: datetime = CUTOFF,
    critical: bool = False,
) -> PointInTimeObservation:
    return PointInTimeObservation(
        observation_id=observation_id,
        dataset_id="pit-test",
        series="XYZ.CLOSE",
        state=state,
        value=value,
        unit="USD_per_share",
        provider="fixture",
        source_id="fixture-source",
        retrieved_at=CUTOFF + timedelta(days=1),
        market_time=CUTOFF - timedelta(hours=1),
        available_at=available_at,
        decision_cutoff=CUTOFF,
        raw_hash="a" * 64,
        critical=critical,
        imputation_notes=("test-only imputation" if state is ObservationState.IMPUTED else None),
    )


def test_anti_lookahead_excludes_information_available_after_decision() -> None:
    past = _observation("past")
    future = _observation("future", available_at=CUTOFF + timedelta(minutes=10))
    audit = audit_point_in_time([past, future])
    assert audit.status == "BLOCKED_LOOKAHEAD"
    assert audit.accepted_ids == ["past"]
    assert audit.excluded_post_cutoff_ids == ["future"]


def test_missing_critical_value_blocks_and_imputation_remains_visible() -> None:
    missing = _observation(
        "missing",
        state=ObservationState.MISSING,
        value=None,
        critical=True,
    )
    imputed = _observation("imputed", state=ObservationState.IMPUTED, value=99.0)
    audit = audit_point_in_time([missing, imputed])
    assert audit.status == "BLOCKED_CRITICAL_MISSING"
    assert audit.critical_missing_ids == ["missing"]
    assert audit.imputed_ids == ["imputed"]


def test_derived_and_imputed_values_require_explicit_lineage() -> None:
    with pytest.raises(ValidationError, match="derived observations require lineage"):
        _observation("derived", state=ObservationState.DERIVED)
    with pytest.raises(ValidationError, match="explicit notes"):
        PointInTimeObservation(
            **{
                **_observation("base").model_dump(),
                "observation_id": "imputed-without-notes",
                "state": "imputed",
                "imputation_notes": None,
            }
        )


def test_source_disagreement_is_retained_as_a_contradiction() -> None:
    left = _observation("left", value=100.0)
    right = _observation("right", value=101.0).model_copy(
        update={"source_id": "other-source"}
    )
    audit = audit_point_in_time([left, right])
    assert audit.status == "PASSED"
    assert len(audit.contradictions) == 1


def test_private_cache_inventory_verifies_payload_hash_without_exposing_rows(
    tmp_path: Path,
) -> None:
    payload = {
        "s": "ok",
        "optionSymbol": ["XYZ261218C00100000"],
        "updated": [1797624000],
        "bid": [7.9],
        "ask": [8.1],
        "openInterest": [200],
        "volume": [50],
        "iv": [None],
        "delta": [None],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    envelope = {
        "fetched_at": "2026-01-03T12:00:00Z",
        "endpoint": "/v1/options/chain/XYZ/",
        "params": {"date": "2026-01-02"},
        "payload": payload,
        "payload_sha256": sha256(canonical.encode()).hexdigest(),
        "usage": {},
    }
    (tmp_path / "cache.json").write_text(json.dumps(envelope), encoding="utf-8")
    component = inventory_marketdata_cache(tmp_path)
    assert component.record_count == 1
    assert component.raw_data_committed is False
    assert set(component.missing_fields) == {"iv", "delta"}


def test_committed_dataset_manifest_is_strict_and_fail_closed() -> None:
    manifest = HistoricalDatasetManifest.model_validate_json(
        (ROOT / "reports/pre_opra/data_inventory_2026-08-08.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest.quality_status.value == "blocked"
    assert manifest.decision_eligible is False
    assert manifest.raw_data_committed is False
    assert sum(component.record_count for component in manifest.components) == 47029
