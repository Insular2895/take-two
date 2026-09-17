"""Immutable hash-chained paper decisions, with realizations stored separately."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash


class ImmutableStrictModel(StrictModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)


class PaperPrediction(ImmutableStrictModel):
    model_id: str
    metric: str
    value: float
    unit: str
    confidence_interval: tuple[float, float] | None = None


class PaperDecisionDraft(ImmutableStrictModel):
    decision_id: str
    decided_at: datetime
    snapshot_id: str
    snapshot_hash: str = Field(min_length=64, max_length=64)
    candidate_set: tuple[str, ...] = Field(min_length=1)
    five_scores: dict[str, float]
    score_coverages: dict[str, float]
    raw_metrics: dict[str, float | int | str | None]
    classification: str
    selected_candidate: str
    best_baseline: str
    no_position_alternative: Literal["no_position"] = "no_position"
    predictions: tuple[PaperPrediction, ...]
    decision_confidence_intervals: dict[str, tuple[float, float]]
    config_hash: str = Field(min_length=64, max_length=64)
    code_commit: str = Field(min_length=7, max_length=40)
    holdout_used: Literal[False] = False
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("decided_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("paper decision timestamp must be timezone-aware")
        return value.astimezone(UTC)


class PaperDecisionRecord(PaperDecisionDraft):
    schema_version: Literal["1.0"] = "1.0"
    sequence: int = Field(gt=0)
    previous_hash: str | None = Field(default=None, min_length=64, max_length=64)
    record_hash: str = Field(min_length=64, max_length=64)
    record_kind: Literal["paper_decision"] = "paper_decision"


def _decision_payload(record: PaperDecisionRecord) -> dict[str, object]:
    payload = record.model_dump(mode="json")
    payload.pop("record_hash")
    return payload


def validate_paper_decision_chain(records: list[PaperDecisionRecord]) -> None:
    previous_hash: str | None = None
    decision_ids: set[str] = set()
    for sequence, record in enumerate(records, start=1):
        if record.sequence != sequence:
            raise ValueError("paper decision sequence is not contiguous")
        if record.previous_hash != previous_hash:
            raise ValueError("paper decision previous_hash chain is broken")
        if record.record_hash != stable_hash(_decision_payload(record)):
            raise ValueError("paper decision record hash is invalid")
        if record.decision_id in decision_ids:
            raise ValueError("paper decision IDs must be unique and immutable")
        decision_ids.add(record.decision_id)
        previous_hash = record.record_hash


def load_paper_decisions(path: Path) -> list[PaperDecisionRecord]:
    if not path.is_file():
        return []
    records = [
        PaperDecisionRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate_paper_decision_chain(records)
    return records


def build_paper_decision_record(
    existing: list[PaperDecisionRecord], draft: PaperDecisionDraft
) -> PaperDecisionRecord:
    validate_paper_decision_chain(existing)
    provisional = PaperDecisionRecord(
        **draft.model_dump(),
        sequence=len(existing) + 1,
        previous_hash=existing[-1].record_hash if existing else None,
        record_hash="0" * 64,
    )
    record = provisional.model_copy(
        update={"record_hash": stable_hash(_decision_payload(provisional))}
    )
    validate_paper_decision_chain([*existing, record])
    return record


def append_paper_decision(
    path: Path, record: PaperDecisionRecord, *, expected_head_hash: str | None
) -> None:
    existing = load_paper_decisions(path)
    actual_head = existing[-1].record_hash if existing else None
    if actual_head != expected_head_hash:
        raise ValueError("paper decision ledger changed since it was read")
    validate_paper_decision_chain([*existing, record])
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, (record.model_dump_json() + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class PaperRealizationDraft(ImmutableStrictModel):
    realization_id: str
    decision_id: str
    decision_record_hash: str = Field(min_length=64, max_length=64)
    observed_at: datetime
    realized_path_hash: str = Field(min_length=64, max_length=64)
    paper_entry_timestamp: datetime
    paper_exit_timestamp: datetime
    paper_entry_price: float = Field(ge=0)
    paper_exit_price: float = Field(ge=0)
    slippage_eur: float = Field(ge=0)
    fees_eur: float = Field(ge=0)
    pnl_eur: float
    postmortem: str
    simulated_only: Literal[True] = True
    transmit: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("observed_at", "paper_entry_timestamp", "paper_exit_timestamp")
    @classmethod
    def require_realization_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("paper realization timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_future_only_chronology(self) -> PaperRealizationDraft:
        if self.paper_exit_timestamp < self.paper_entry_timestamp:
            raise ValueError("paper exit cannot precede paper entry")
        if self.observed_at < self.paper_exit_timestamp:
            raise ValueError("paper realization cannot be recorded before the paper exit")
        return self


class PaperRealizationRecord(PaperRealizationDraft):
    schema_version: Literal["1.1"] = "1.1"
    sequence: int = Field(gt=0)
    previous_hash: str | None = Field(default=None, min_length=64, max_length=64)
    realization_hash: str = Field(min_length=64, max_length=64)
    record_kind: Literal["paper_realization"] = "paper_realization"


def _realization_payload(record: PaperRealizationRecord) -> dict[str, object]:
    payload = record.model_dump(mode="json")
    payload.pop("realization_hash")
    return payload


def validate_paper_realization_chain(
    records: list[PaperRealizationRecord],
    decisions: list[PaperDecisionRecord] | None = None,
) -> None:
    previous_hash: str | None = None
    realization_ids: set[str] = set()
    realized_decision_ids: set[str] = set()
    decisions_by_id = (
        {decision.decision_id: decision for decision in decisions}
        if decisions is not None
        else None
    )
    if decisions is not None:
        validate_paper_decision_chain(decisions)
    for sequence, record in enumerate(records, start=1):
        if record.sequence != sequence:
            raise ValueError("paper realization sequence is not contiguous")
        if record.previous_hash != previous_hash:
            raise ValueError("paper realization previous_hash chain is broken")
        if record.realization_hash != stable_hash(_realization_payload(record)):
            raise ValueError("paper realization record hash is invalid")
        if record.realization_id in realization_ids:
            raise ValueError("paper realization IDs must be unique and immutable")
        if record.decision_id in realized_decision_ids:
            raise ValueError("a paper decision can have only one final realization")
        if decisions_by_id is not None:
            decision = decisions_by_id.get(record.decision_id)
            if decision is None:
                raise ValueError("paper realization references an unknown decision")
            if decision.record_hash != record.decision_record_hash:
                raise ValueError("paper realization decision hash does not match")
            if record.paper_entry_timestamp < decision.decided_at:
                raise ValueError("paper entry cannot precede the frozen decision")
        realization_ids.add(record.realization_id)
        realized_decision_ids.add(record.decision_id)
        previous_hash = record.realization_hash


def load_paper_realizations(
    path: Path,
    decisions: list[PaperDecisionRecord] | None = None,
) -> list[PaperRealizationRecord]:
    if not path.is_file():
        return []
    records = [
        PaperRealizationRecord.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    validate_paper_realization_chain(records, decisions)
    return records


def build_paper_realization_record(
    draft: PaperRealizationDraft,
    existing: list[PaperRealizationRecord] | None = None,
    decisions: list[PaperDecisionRecord] | None = None,
) -> PaperRealizationRecord:
    existing_records = existing or []
    validate_paper_realization_chain(existing_records, decisions)
    provisional = PaperRealizationRecord(
        **draft.model_dump(),
        sequence=len(existing_records) + 1,
        previous_hash=(existing_records[-1].realization_hash if existing_records else None),
        realization_hash="0" * 64,
    )
    record = provisional.model_copy(
        update={"realization_hash": stable_hash(_realization_payload(provisional))}
    )
    validate_paper_realization_chain([*existing_records, record], decisions)
    return record


def append_paper_realization(
    path: Path,
    record: PaperRealizationRecord,
    *,
    expected_head_hash: str | None,
    decisions: list[PaperDecisionRecord] | None = None,
) -> None:
    existing = load_paper_realizations(path, decisions)
    actual_head = existing[-1].realization_hash if existing else None
    if actual_head != expected_head_hash:
        raise ValueError("paper realization ledger changed since it was read")
    validate_paper_realization_chain([*existing, record], decisions)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, (record.model_dump_json() + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
