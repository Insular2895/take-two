"""Immutable hash-chained paper decisions, with realizations stored separately."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

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


class PaperRealizationRecord(PaperRealizationDraft):
    schema_version: Literal["1.0"] = "1.0"
    realization_hash: str = Field(min_length=64, max_length=64)
    record_kind: Literal["paper_realization"] = "paper_realization"


def build_paper_realization_record(draft: PaperRealizationDraft) -> PaperRealizationRecord:
    provisional = PaperRealizationRecord(**draft.model_dump(), realization_hash="0" * 64)
    payload = provisional.model_dump(mode="json", exclude={"realization_hash"})
    return provisional.model_copy(update={"realization_hash": stable_hash(payload)})
