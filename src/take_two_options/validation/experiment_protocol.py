"""Immutable experiment manifests, point-in-time splits, and holdout access ledger."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash


class ExperimentManifest(StrictModel):
    manifest_id: str = Field(min_length=1)
    manifest_hash: str = Field(min_length=64, max_length=64)
    created_at: datetime
    code_commit: str = Field(min_length=7)
    code_version: str = Field(min_length=1)
    config_hash: str = Field(min_length=64, max_length=64)
    dataset_id: str = Field(min_length=1)
    dataset_hash: str = Field(min_length=64, max_length=64)
    split_policy_hash: str = Field(min_length=64, max_length=64)
    trial_registry_hash: str = Field(min_length=64, max_length=64)
    seed: int
    synthetic: bool
    final_holdout_id: str | None = None
    final_holdout_hash: str | None = Field(default=None, min_length=64, max_length=64)

    @field_validator("created_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("experiment timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def pair_holdout_identity_and_hash(self) -> ExperimentManifest:
        if (self.final_holdout_id is None) != (self.final_holdout_hash is None):
            raise ValueError("holdout ID and hash must both be supplied or both be null")
        return self


def _manifest_payload(manifest: ExperimentManifest) -> dict[str, object]:
    payload = manifest.model_dump(mode="json")
    payload.pop("manifest_hash")
    return payload


def create_experiment_manifest(
    *,
    manifest_id: str,
    created_at: datetime,
    code_commit: str,
    code_version: str,
    config_hash: str,
    dataset_id: str,
    dataset_hash: str,
    split_policy_hash: str,
    trial_registry_hash: str,
    seed: int,
    synthetic: bool,
    final_holdout_id: str | None = None,
    final_holdout_hash: str | None = None,
) -> ExperimentManifest:
    provisional = ExperimentManifest(
        manifest_id=manifest_id,
        manifest_hash="0" * 64,
        created_at=created_at,
        code_commit=code_commit,
        code_version=code_version,
        config_hash=config_hash,
        dataset_id=dataset_id,
        dataset_hash=dataset_hash,
        split_policy_hash=split_policy_hash,
        trial_registry_hash=trial_registry_hash,
        seed=seed,
        synthetic=synthetic,
        final_holdout_id=final_holdout_id,
        final_holdout_hash=final_holdout_hash,
    )
    return provisional.model_copy(
        update={"manifest_hash": stable_hash(_manifest_payload(provisional))}
    )


def verify_experiment_manifest(manifest: ExperimentManifest) -> bool:
    return manifest.manifest_hash == stable_hash(_manifest_payload(manifest))


class PointInTimeObservation(StrictModel):
    observation_id: str = Field(min_length=1)
    feature_start: datetime
    decision_time: datetime
    label_end: datetime
    available_at: datetime

    @field_validator("feature_start", "decision_time", "label_end", "available_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("point-in-time observations require timezone-aware timestamps")
        return value

    @model_validator(mode="after")
    def validate_timeline(self) -> PointInTimeObservation:
        if not self.feature_start <= self.decision_time <= self.label_end:
            raise ValueError("feature_start <= decision_time <= label_end is required")
        if self.available_at > self.decision_time:
            raise ValueError("data available after decision_time would create look-ahead")
        return self


class PointInTimeSplitReport(StrictModel):
    status: Literal["completed", "insufficient_data"]
    train_ids: tuple[str, ...] = ()
    validation_ids: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()
    final_holdout_ids: tuple[str, ...] = ()
    final_holdout_count: int = Field(ge=0)
    final_holdout_opened: bool
    purged_ids: tuple[str, ...] = ()
    embargo_days: int = Field(ge=0)
    warnings: tuple[str, ...] = ()


def _purge_before_boundary(
    observations: list[PointInTimeObservation],
    *,
    next_start: datetime | None,
    embargo_days: int,
) -> tuple[list[PointInTimeObservation], list[str]]:
    if next_start is None:
        return observations, []
    boundary = next_start - timedelta(days=embargo_days)
    retained = [observation for observation in observations if observation.label_end < boundary]
    retained_ids = {observation.observation_id for observation in retained}
    purged = [
        observation.observation_id
        for observation in observations
        if observation.observation_id not in retained_ids
    ]
    return retained, purged


def build_point_in_time_split(
    observations: list[PointInTimeObservation],
    *,
    train_end: datetime,
    validation_end: datetime,
    test_end: datetime,
    final_holdout_end: datetime,
    embargo_days: int,
    open_final_holdout: bool = False,
) -> PointInTimeSplitReport:
    """Build one chronological split and hide final-holdout IDs unless explicitly opened."""
    cutoffs = (train_end, validation_end, test_end, final_holdout_end)
    if any(cutoff.tzinfo is None for cutoff in cutoffs):
        raise ValueError("split cutoffs must be timezone-aware")
    if list(cutoffs) != sorted(cutoffs) or len(set(cutoffs)) != len(cutoffs):
        raise ValueError("split cutoffs must be strictly increasing")
    if embargo_days < 0:
        raise ValueError("embargo cannot be negative")
    ids = [observation.observation_id for observation in observations]
    if len(ids) != len(set(ids)):
        raise ValueError("point-in-time observation IDs must be unique")
    ordered = sorted(observations, key=lambda observation: observation.decision_time)
    train: list[PointInTimeObservation] = []
    validation: list[PointInTimeObservation] = []
    test: list[PointInTimeObservation] = []
    holdout: list[PointInTimeObservation] = []
    for observation in ordered:
        if observation.decision_time <= train_end:
            train.append(observation)
        elif observation.decision_time <= validation_end:
            validation.append(observation)
        elif observation.decision_time <= test_end:
            test.append(observation)
        elif observation.decision_time <= final_holdout_end:
            holdout.append(observation)
    validation_start = validation[0].decision_time if validation else None
    test_start = test[0].decision_time if test else None
    holdout_start = holdout[0].decision_time if holdout else None
    train, train_purged = _purge_before_boundary(
        train, next_start=validation_start, embargo_days=embargo_days
    )
    validation, validation_purged = _purge_before_boundary(
        validation, next_start=test_start, embargo_days=embargo_days
    )
    test, test_purged = _purge_before_boundary(
        test, next_start=holdout_start, embargo_days=embargo_days
    )
    status: Literal["completed", "insufficient_data"] = (
        "completed" if train and validation and test and holdout else "insufficient_data"
    )
    warnings: tuple[str, ...] = ()
    if status == "insufficient_data":
        warnings = ("all four chronological partitions require observations",)
    return PointInTimeSplitReport(
        status=status,
        train_ids=tuple(observation.observation_id for observation in train),
        validation_ids=tuple(observation.observation_id for observation in validation),
        test_ids=tuple(observation.observation_id for observation in test),
        final_holdout_ids=(
            tuple(observation.observation_id for observation in holdout)
            if open_final_holdout
            else ()
        ),
        final_holdout_count=len(holdout),
        final_holdout_opened=open_final_holdout,
        purged_ids=tuple(train_purged + validation_purged + test_purged),
        embargo_days=embargo_days,
        warnings=warnings,
    )


HoldoutAction = Literal["seal", "evaluate", "report", "tune"]


class HoldoutAccessEntry(StrictModel):
    sequence: int = Field(gt=0)
    accessed_at: datetime
    action: HoldoutAction
    holdout_id: str = Field(min_length=1)
    dataset_hash: str = Field(min_length=64, max_length=64)
    code_commit: str = Field(min_length=7)
    purpose: str = Field(min_length=1)
    previous_hash: str | None = Field(default=None, min_length=64, max_length=64)
    entry_hash: str = Field(min_length=64, max_length=64)

    @field_validator("accessed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("holdout ledger timestamps must be timezone-aware")
        return value


def _entry_payload(entry: HoldoutAccessEntry) -> dict[str, object]:
    payload = entry.model_dump(mode="json")
    payload.pop("entry_hash")
    return payload


class HoldoutAccessLedger:
    """Hash-chained ledger that permits one evaluation and forbids later tuning."""

    def __init__(self) -> None:
        self.entries: list[HoldoutAccessEntry] = []

    def register(
        self,
        *,
        accessed_at: datetime,
        action: HoldoutAction,
        holdout_id: str,
        dataset_hash: str,
        code_commit: str,
        purpose: str,
    ) -> HoldoutAccessEntry:
        if not self.entries and action != "seal":
            raise ValueError("the first holdout ledger action must be seal")
        if self.entries:
            first = self.entries[0]
            if holdout_id != first.holdout_id or dataset_hash != first.dataset_hash:
                raise ValueError("holdout identity and dataset hash are immutable")
        evaluated = any(entry.action == "evaluate" for entry in self.entries)
        if action == "evaluate" and evaluated:
            raise ValueError("final holdout evaluation is allowed only once")
        if action == "tune" and evaluated:
            raise ValueError("tuning is forbidden after final holdout evaluation")
        previous_hash = self.entries[-1].entry_hash if self.entries else None
        provisional = HoldoutAccessEntry(
            sequence=len(self.entries) + 1,
            accessed_at=accessed_at,
            action=action,
            holdout_id=holdout_id,
            dataset_hash=dataset_hash,
            code_commit=code_commit,
            purpose=purpose,
            previous_hash=previous_hash,
            entry_hash="0" * 64,
        )
        entry = provisional.model_copy(
            update={"entry_hash": stable_hash(_entry_payload(provisional))}
        )
        self.entries.append(entry)
        return entry

    def verify(self) -> bool:
        previous_hash: str | None = None
        for sequence, entry in enumerate(self.entries, start=1):
            if entry.sequence != sequence or entry.previous_hash != previous_hash:
                return False
            if entry.entry_hash != stable_hash(_entry_payload(entry)):
                return False
            previous_hash = entry.entry_hash
        return True
