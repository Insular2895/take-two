"""Strict provenance and point-in-time contracts for historical research data."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel


class ObservationState(StrEnum):
    OBSERVED = "observed"
    DERIVED = "derived"
    IMPUTED = "imputed"
    MISSING = "missing"
    UNAVAILABLE_FROM_SOURCE = "unavailable_from_source"


class LicenseStatus(StrEnum):
    PUBLIC = "public"
    AUTHORIZED_INTERNAL = "authorized_internal"
    REDISTRIBUTION_FORBIDDEN = "redistribution_forbidden"
    TO_REVIEW = "to_review"
    UNKNOWN = "unknown"


class PointInTimeStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    FAILED = "failed"
    TO_REVIEW = "to_review"


class DatasetQualityStatus(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FIXTURE_ONLY = "fixture_only"


class PointInTimeObservation(StrictModel):
    observation_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    series: str = Field(min_length=1)
    state: ObservationState
    value: float | int | str | bool | None
    unit: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    retrieved_at: datetime
    available_at: datetime
    decision_cutoff: datetime
    market_time: datetime | None = None
    event_time: datetime | None = None
    published_at: datetime | None = None
    raw_hash: str | None = Field(default=None, min_length=64, max_length=64)
    derived_from: list[str] = Field(default_factory=list)
    imputation_notes: str | None = None
    critical: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "retrieved_at",
        "available_at",
        "decision_cutoff",
        "market_time",
        "event_time",
        "published_at",
    )
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("point-in-time timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_state_and_timeline(self) -> PointInTimeObservation:
        if self.state in {ObservationState.MISSING, ObservationState.UNAVAILABLE_FROM_SOURCE}:
            if self.value is not None:
                raise ValueError("missing/unavailable observations cannot carry a value")
        elif self.value is None:
            raise ValueError("observed, derived, and imputed observations require a value")
        if self.state is ObservationState.DERIVED and not self.derived_from:
            raise ValueError("derived observations require lineage")
        if self.state is ObservationState.IMPUTED and not self.imputation_notes:
            raise ValueError("imputed observations require explicit notes")
        origin_times = [
            value
            for value in (self.market_time, self.event_time, self.published_at)
            if value is not None
        ]
        if origin_times and self.available_at < max(origin_times):
            raise ValueError("available_at cannot precede the source event/publication/market time")
        return self

    @property
    def point_in_time_eligible(self) -> bool:
        return self.available_at <= self.decision_cutoff


class SourceComponentManifest(StrictModel):
    component_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    data_class: Literal[
        "underlying",
        "options",
        "macro",
        "events",
        "corporate_actions",
        "market_calendar",
    ]
    record_count: int = Field(ge=0)
    coverage_start: datetime | None
    coverage_end: datetime | None
    retrieved_start: datetime | None
    retrieved_end: datetime | None
    content_hash: str = Field(min_length=64, max_length=64)
    observed_fields: list[str] = Field(default_factory=list)
    derived_fields: list[str] = Field(default_factory=list)
    imputed_fields: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    unavailable_fields: list[str] = Field(default_factory=list)
    license_status: LicenseStatus
    license_notes: str = Field(min_length=1)
    terms_uri: str | None = None
    point_in_time_status: PointInTimeStatus
    quality_status: DatasetQualityStatus
    raw_location: Literal["local_private", "public_committable", "not_acquired"]
    raw_data_committed: Literal[False]
    adjustment_policy: str = Field(min_length=1)
    limitations: list[str] = Field(default_factory=list)

    @field_validator(
        "coverage_start",
        "coverage_end",
        "retrieved_start",
        "retrieved_end",
    )
    @classmethod
    def require_component_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("component timestamps must be timezone-aware")
        return value.astimezone(UTC) if value is not None else None


class HistoricalDatasetManifest(StrictModel):
    schema_version: Literal["1.0"]
    dataset_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    created_at: datetime
    decision_cutoff: datetime
    dataset_hash: str = Field(min_length=64, max_length=64)
    components: list[SourceComponentManifest] = Field(min_length=1)
    license_status: LicenseStatus
    point_in_time_status: PointInTimeStatus
    quality_status: DatasetQualityStatus
    decision_eligible: bool
    blockers: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    raw_data_committed: Literal[False]
    order_capability: Literal["forbidden"]

    @field_validator("created_at", "decision_cutoff")
    @classmethod
    def require_manifest_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("manifest timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def enforce_fail_closed_status(self) -> HistoricalDatasetManifest:
        blocked_component = any(
            component.license_status
            in {LicenseStatus.TO_REVIEW, LicenseStatus.UNKNOWN}
            or component.quality_status is DatasetQualityStatus.BLOCKED
            or component.point_in_time_status
            in {PointInTimeStatus.FAILED, PointInTimeStatus.TO_REVIEW}
            for component in self.components
        )
        if self.decision_eligible and (blocked_component or self.blockers):
            raise ValueError("a blocked or unresolved component cannot be decision eligible")
        return self


class PointInTimeAudit(StrictModel):
    status: Literal["PASSED", "BLOCKED_LOOKAHEAD", "BLOCKED_CRITICAL_MISSING"]
    accepted_ids: list[str]
    excluded_post_cutoff_ids: list[str]
    critical_missing_ids: list[str]
    imputed_ids: list[str]
    contradictions: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def audit_point_in_time(observations: list[PointInTimeObservation]) -> PointInTimeAudit:
    accepted: list[str] = []
    excluded: list[str] = []
    critical_missing: list[str] = []
    imputed: list[str] = []
    values_by_key: dict[tuple[str, datetime], set[str]] = {}
    for observation in observations:
        if not observation.point_in_time_eligible:
            excluded.append(observation.observation_id)
            continue
        if observation.critical and observation.state in {
            ObservationState.MISSING,
            ObservationState.UNAVAILABLE_FROM_SOURCE,
        }:
            critical_missing.append(observation.observation_id)
            continue
        if observation.state is ObservationState.IMPUTED:
            imputed.append(observation.observation_id)
        accepted.append(observation.observation_id)
        if observation.value is not None:
            key = (observation.series, observation.available_at)
            values_by_key.setdefault(key, set()).add(repr(observation.value))
    contradictions = [
        f"{series}@{timestamp.isoformat()} has {len(values)} retained values"
        for (series, timestamp), values in sorted(values_by_key.items())
        if len(values) > 1
    ]
    status: Literal["PASSED", "BLOCKED_LOOKAHEAD", "BLOCKED_CRITICAL_MISSING"]
    if critical_missing:
        status = "BLOCKED_CRITICAL_MISSING"
    elif excluded:
        status = "BLOCKED_LOOKAHEAD"
    else:
        status = "PASSED"
    return PointInTimeAudit(
        status=status,
        accepted_ids=accepted,
        excluded_post_cutoff_ids=excluded,
        critical_missing_ids=critical_missing,
        imputed_ids=imputed,
        contradictions=contradictions,
    )
