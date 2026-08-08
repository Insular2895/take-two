"""Point-in-time event and regime dataset with explicit anti-lookahead controls."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from statistics import fmean
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class EventKind(StrEnum):
    EARNINGS = "earnings"
    PRODUCT_RELEASE = "product_release"
    REGULATORY = "regulatory"
    CORPORATE = "corporate"
    MACRO = "macro"


class PointInTimeEvent(StrictModel):
    event_id: str
    external_id: str
    entity: str
    kind: EventKind
    event_time: datetime
    publication_time: datetime
    available_at: datetime
    decision_cutoff: datetime
    source_id: str
    source_hash: str = Field(min_length=64, max_length=64)
    summary: str

    @model_validator(mode="after")
    def require_temporal_lineage(self) -> PointInTimeEvent:
        timestamps = (
            self.event_time,
            self.publication_time,
            self.available_at,
            self.decision_cutoff,
        )
        if any(value.tzinfo is None for value in timestamps):
            raise ValueError("event timestamps must be timezone-aware")
        if self.available_at < self.publication_time:
            raise ValueError("available_at cannot precede publication_time")
        return self


class EventConflict(StrictModel):
    external_id: str
    event_ids: list[str] = Field(min_length=2)
    reason: str


class RegimeObservation(StrictModel):
    observation_id: str
    available_at: datetime
    decision_cutoff: datetime
    trailing_return: float
    realized_volatility: float = Field(ge=0)
    trend_regime: Literal["bearish", "neutral", "bullish"]
    volatility_regime: Literal["normal", "high"]


class EventStudyRow(StrictModel):
    kind: EventKind
    horizon_sessions: int = Field(gt=0)
    observations: int = Field(gt=0)
    mean_return: float
    probability_positive: float = Field(ge=0, le=1)


class EventOutcome(StrictModel):
    event_id: str
    horizon_sessions: int = Field(gt=0)
    return_value: float


class EventRegimeReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    dataset_hash: str | None = Field(default=None, min_length=64, max_length=64)
    status: Literal[
        "DEVELOPMENT_DATASET_READY",
        "FIXTURE_ONLY_NOT_VALIDATED",
        "BLOCKED_MISSING_GOVERNED_EVENTS",
        "BLOCKED_CONFLICTS",
    ]
    accepted_events: list[PointInTimeEvent]
    excluded_post_cutoff_ids: list[str]
    conflicts: list[EventConflict]
    regimes: list[RegimeObservation]
    event_study: list[EventStudyRow]
    trend_threshold: float = Field(gt=0)
    high_volatility_threshold: float = Field(gt=0)
    threshold_status: Literal["draft_to_validate", "validated"]
    blockers: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def enforce_ready_requirements(self) -> EventRegimeReport:
        if self.status == "DEVELOPMENT_DATASET_READY" and (
            not self.accepted_events or self.conflicts or self.blockers
        ):
            raise ValueError("ready event datasets need events and no conflicts/blockers")
        return self


def classify_regimes(
    rows: list[tuple[str, datetime, datetime, float, float]],
    *,
    trend_threshold: float,
    high_volatility_threshold: float,
) -> list[RegimeObservation]:
    output: list[RegimeObservation] = []
    for observation_id, available_at, cutoff, trailing_return, realized_volatility in rows:
        if available_at > cutoff:
            continue
        trend: Literal["bearish", "neutral", "bullish"] = (
            "bullish"
            if trailing_return >= trend_threshold
            else "bearish"
            if trailing_return <= -trend_threshold
            else "neutral"
        )
        output.append(
            RegimeObservation(
                observation_id=observation_id,
                available_at=available_at,
                decision_cutoff=cutoff,
                trailing_return=trailing_return,
                realized_volatility=realized_volatility,
                trend_regime=trend,
                volatility_regime=(
                    "high" if realized_volatility >= high_volatility_threshold else "normal"
                ),
            )
        )
    return output


def build_event_regime_report(
    events: list[PointInTimeEvent],
    outcomes: list[EventOutcome],
    regime_rows: list[tuple[str, datetime, datetime, float, float]],
    *,
    ticker: str,
    dataset_hash: str,
    trend_threshold: float,
    high_volatility_threshold: float,
    synthetic: bool,
) -> EventRegimeReport:
    excluded = sorted(
        event.event_id for event in events if event.available_at > event.decision_cutoff
    )
    eligible = [event for event in events if event.available_at <= event.decision_cutoff]
    by_external: dict[str, list[PointInTimeEvent]] = {}
    for event in eligible:
        by_external.setdefault(event.external_id, []).append(event)
    conflicts = [
        EventConflict(
            external_id=external_id,
            event_ids=sorted(event.event_id for event in values),
            reason="same external_id has contradictory source hashes or timestamps",
        )
        for external_id, values in sorted(by_external.items())
        if len(values) > 1 and len({(event.source_hash, event.event_time) for event in values}) > 1
    ]
    conflicted = {event_id for conflict in conflicts for event_id in conflict.event_ids}
    accepted = [
        min(values, key=lambda event: (event.available_at, event.event_id))
        for values in by_external.values()
        if not any(event.event_id in conflicted for event in values)
    ]
    accepted_by_id = {event.event_id: event for event in accepted}
    grouped_outcomes: dict[tuple[EventKind, int], list[float]] = {}
    for outcome in outcomes:
        matched_event = accepted_by_id.get(outcome.event_id)
        if matched_event is not None and math.isfinite(outcome.return_value):
            grouped_outcomes.setdefault((matched_event.kind, outcome.horizon_sessions), []).append(
                outcome.return_value
            )
    event_study = [
        EventStudyRow(
            kind=kind,
            horizon_sessions=horizon,
            observations=len(values),
            mean_return=fmean(values),
            probability_positive=sum(value > 0 for value in values) / len(values),
        )
        for (kind, horizon), values in sorted(
            grouped_outcomes.items(), key=lambda item: (item[0][0].value, item[0][1])
        )
    ]
    regimes = classify_regimes(
        regime_rows,
        trend_threshold=trend_threshold,
        high_volatility_threshold=high_volatility_threshold,
    )
    blockers: list[str] = []
    if not accepted:
        blockers.append("No governed point-in-time event history is available.")
    if conflicts:
        blockers.append("Contradictory event records require source review.")
    if synthetic:
        blockers.append("Synthetic events validate mechanics only.")
    status = (
        "FIXTURE_ONLY_NOT_VALIDATED"
        if synthetic
        else "BLOCKED_CONFLICTS"
        if conflicts
        else "DEVELOPMENT_DATASET_READY"
        if accepted
        else "BLOCKED_MISSING_GOVERNED_EVENTS"
    )
    return EventRegimeReport(
        schema_version="1.0",
        report_id=f"{ticker.casefold()}-event-regime-v1",
        ticker=ticker,
        dataset_hash=dataset_hash,
        status=status,
        accepted_events=sorted(accepted, key=lambda event: (event.event_time, event.event_id)),
        excluded_post_cutoff_ids=excluded,
        conflicts=conflicts,
        regimes=regimes,
        event_study=event_study,
        trend_threshold=trend_threshold,
        high_volatility_threshold=high_volatility_threshold,
        threshold_status="draft_to_validate",
        blockers=blockers,
        holdout_used=False,
    )
