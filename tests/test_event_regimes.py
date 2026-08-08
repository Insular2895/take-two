from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from take_two_options.historical_data.event_regimes import (
    EventKind,
    EventOutcome,
    EventRegimeReport,
    PointInTimeEvent,
    build_event_regime_report,
)

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = datetime(2026, 1, 5, 21, tzinfo=UTC)


def _event(event_id: str, external_id: str, *, future: bool = False) -> PointInTimeEvent:
    publication = CUTOFF - timedelta(hours=2)
    return PointInTimeEvent(
        event_id=event_id,
        external_id=external_id,
        entity="XYZ",
        kind=EventKind.EARNINGS,
        event_time=CUTOFF - timedelta(hours=1),
        publication_time=publication,
        available_at=CUTOFF + timedelta(minutes=1) if future else publication,
        decision_cutoff=CUTOFF,
        source_id="fixture",
        source_hash=("a" if event_id == "e1" else "b") * 64,
        summary="fixture event",
    )


def test_event_dataset_excludes_future_information_and_builds_study() -> None:
    report = build_event_regime_report(
        [_event("e1", "x1"), _event("future", "x2", future=True)],
        [EventOutcome(event_id="e1", horizon_sessions=5, return_value=0.03)],
        [("r1", CUTOFF, CUTOFF, 0.08, 0.35)],
        ticker="XYZ",
        dataset_hash="a" * 64,
        trend_threshold=0.05,
        high_volatility_threshold=0.30,
        synthetic=True,
    )
    assert [event.event_id for event in report.accepted_events] == ["e1"]
    assert report.excluded_post_cutoff_ids == ["future"]
    assert report.event_study[0].mean_return == 0.03
    assert report.regimes[0].trend_regime == "bullish"
    assert report.regimes[0].volatility_regime == "high"


def test_contradictory_duplicate_is_retained_and_not_silently_deduplicated() -> None:
    report = build_event_regime_report(
        [_event("e1", "same"), _event("e2", "same")],
        [],
        [],
        ticker="XYZ",
        dataset_hash="b" * 64,
        trend_threshold=0.05,
        high_volatility_threshold=0.30,
        synthetic=False,
    )
    assert report.status == "BLOCKED_CONFLICTS"
    assert report.accepted_events == []
    assert report.conflicts[0].event_ids == ["e1", "e2"]


def test_committed_tt_report_contains_governed_events_without_licensed_regime_rows() -> None:
    report = EventRegimeReport.model_validate_json(
        (ROOT / "reports/pre_opra/event_regime_dataset_2026-08-08.json").read_text()
    )
    assert report.status == "DEVELOPMENT_DATASET_READY"
    assert report.accepted_events
    assert report.event_study
    assert report.regimes == []
    assert report.threshold_status == "draft_to_validate"
    assert report.holdout_used is False
