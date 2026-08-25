"""Persistent, hash-chained and irreversible final-holdout state machine."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash


class HoldoutState(StrEnum):
    UNOPENED = "UNOPENED"
    OPENED_ONCE = "OPENED_ONCE"
    CONTAMINATED = "CONTAMINATED"
    INVALID = "INVALID"


HoldoutEvent = Literal[
    "initialize",
    "provision",
    "open_once",
    "report_unchanged",
    "mark_contaminated",
    "invalidate",
]


class HoldoutLedgerEntry(StrictModel):
    schema_version: Literal["1.0"]
    sequence: int = Field(gt=0)
    occurred_at: datetime
    event: HoldoutEvent
    state: HoldoutState
    holdout_id: str = Field(min_length=1)
    dataset_hash: str | None = Field(default=None, min_length=64, max_length=64)
    code_commit: str = Field(min_length=7)
    actor: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    previous_hash: str | None = Field(default=None, min_length=64, max_length=64)
    entry_hash: str = Field(min_length=64, max_length=64)
    tuning_performed: Literal[False]
    order_capability: Literal["forbidden"]

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("holdout ledger timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_dataset_identity(self) -> HoldoutLedgerEntry:
        if self.event == "open_once" and self.dataset_hash is None:
            raise ValueError("opening a holdout requires a sealed dataset hash")
        return self


def _payload(entry: HoldoutLedgerEntry) -> dict[str, object]:
    payload = entry.model_dump(mode="json")
    payload.pop("entry_hash")
    return payload


def _validate_chain(entries: list[HoldoutLedgerEntry]) -> None:
    previous_hash: str | None = None
    previous_state: HoldoutState | None = None
    identity: tuple[str, str | None] | None = None
    opened = False
    for sequence, entry in enumerate(entries, start=1):
        if entry.sequence != sequence:
            raise ValueError("holdout ledger sequence is not contiguous")
        if entry.previous_hash != previous_hash:
            raise ValueError("holdout ledger previous_hash chain is broken")
        if entry.entry_hash != stable_hash(_payload(entry)):
            raise ValueError("holdout ledger entry hash is invalid")
        if sequence == 1:
            if entry.event != "initialize" or entry.state is not HoldoutState.UNOPENED:
                raise ValueError("first holdout event must initialize UNOPENED")
            identity = (entry.holdout_id, entry.dataset_hash)
        else:
            assert previous_state is not None and identity is not None
            previous_id, previous_dataset_hash = identity
            if entry.holdout_id != previous_id:
                raise ValueError("holdout_id is immutable")
            if previous_dataset_hash is not None and entry.dataset_hash != previous_dataset_hash:
                raise ValueError("provisioned dataset_hash is immutable")
            if previous_dataset_hash is None and entry.dataset_hash is not None:
                if entry.event != "provision":
                    raise ValueError("dataset hash can first appear only in a provision event")
                identity = (entry.holdout_id, entry.dataset_hash)
            if previous_state in {HoldoutState.CONTAMINATED, HoldoutState.INVALID}:
                raise ValueError("contaminated and invalid holdout states are terminal")
            if entry.event == "initialize":
                raise ValueError("initialize is allowed only for the first ledger entry")
            if entry.event == "provision" and previous_dataset_hash is not None:
                raise ValueError("a holdout dataset can be provisioned only once")
            if entry.event == "open_once":
                if opened or previous_state is not HoldoutState.UNOPENED:
                    raise ValueError("UNOPENED to OPENED_ONCE is allowed only once")
                if entry.state is not HoldoutState.OPENED_ONCE:
                    raise ValueError("open_once must transition to OPENED_ONCE")
                opened = True
            elif entry.event == "provision":
                if entry.state is not HoldoutState.UNOPENED or opened:
                    raise ValueError("initialization/provisioning cannot reopen a holdout")
            elif entry.event == "report_unchanged":
                if entry.state is not previous_state:
                    raise ValueError("reporting cannot change holdout state")
            elif entry.event == "mark_contaminated":
                if entry.state is not HoldoutState.CONTAMINATED:
                    raise ValueError("mark_contaminated must set CONTAMINATED")
            elif entry.event == "invalidate" and entry.state is not HoldoutState.INVALID:
                raise ValueError("invalidate must set INVALID")
        previous_hash = entry.entry_hash
        previous_state = entry.state


def load_holdout_ledger(path: Path) -> list[HoldoutLedgerEntry]:
    if not path.is_file():
        return []
    entries = [
        HoldoutLedgerEntry.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _validate_chain(entries)
    return entries


def build_holdout_entry(
    entries: list[HoldoutLedgerEntry],
    *,
    occurred_at: datetime,
    event: HoldoutEvent,
    holdout_id: str,
    dataset_hash: str | None,
    code_commit: str,
    actor: str,
    purpose: str,
) -> HoldoutLedgerEntry:
    _validate_chain(entries)
    previous_hash = entries[-1].entry_hash if entries else None
    previous_state = entries[-1].state if entries else None
    state: HoldoutState
    if not entries:
        state = HoldoutState.UNOPENED
    elif event in {"provision", "report_unchanged"}:
        assert previous_state is not None
        state = previous_state
    elif event == "open_once":
        state = HoldoutState.OPENED_ONCE
    elif event == "mark_contaminated":
        state = HoldoutState.CONTAMINATED
    elif event == "invalidate":
        state = HoldoutState.INVALID
    else:
        state = HoldoutState.UNOPENED
    provisional = HoldoutLedgerEntry(
        schema_version="1.0",
        sequence=len(entries) + 1,
        occurred_at=occurred_at,
        event=event,
        state=state,
        holdout_id=holdout_id,
        dataset_hash=dataset_hash,
        code_commit=code_commit,
        actor=actor,
        purpose=purpose,
        previous_hash=previous_hash,
        entry_hash="0" * 64,
        tuning_performed=False,
        order_capability="forbidden",
    )
    entry = provisional.model_copy(update={"entry_hash": stable_hash(_payload(provisional))})
    _validate_chain([*entries, entry])
    return entry


def append_holdout_entry(
    path: Path,
    entry: HoldoutLedgerEntry,
    *,
    expected_head_hash: str | None,
) -> None:
    """Append only when the caller's expected head matches the verified file."""
    entries = load_holdout_ledger(path)
    actual_head = entries[-1].entry_hash if entries else None
    if actual_head != expected_head_hash:
        raise ValueError("holdout ledger changed since it was read")
    _validate_chain([*entries, entry])
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, (entry.model_dump_json() + "\n").encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
