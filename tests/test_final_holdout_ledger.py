from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from take_two_options.validation.final_holdout import (
    HoldoutState,
    append_holdout_entry,
    build_holdout_entry,
    load_holdout_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 8, 20, tzinfo=UTC)


def _initialize():
    return build_holdout_entry(
        [],
        occurred_at=NOW,
        event="initialize",
        holdout_id="fresh-v1",
        dataset_hash=None,
        code_commit="abcdef1",
        actor="test",
        purpose="initialize without opening",
    )


def _provision(entries):
    return build_holdout_entry(
        entries,
        occurred_at=NOW + timedelta(minutes=1),
        event="provision",
        holdout_id="fresh-v1",
        dataset_hash="d" * 64,
        code_commit="abcdef1",
        actor="test",
        purpose="seal immutable dataset identity",
    )


def test_unopened_to_opened_once_is_irreversible() -> None:
    initialized = _initialize()
    provisioned = _provision([initialized])
    opened = build_holdout_entry(
        [initialized, provisioned],
        occurred_at=NOW + timedelta(minutes=2),
        event="open_once",
        holdout_id="fresh-v1",
        dataset_hash="d" * 64,
        code_commit="abcdef1",
        actor="test",
        purpose="one final evaluation",
    )
    assert opened.state is HoldoutState.OPENED_ONCE
    with pytest.raises(ValueError, match="allowed only once"):
        build_holdout_entry(
            [initialized, provisioned, opened],
            occurred_at=NOW + timedelta(minutes=3),
            event="open_once",
            holdout_id="fresh-v1",
            dataset_hash="d" * 64,
            code_commit="abcdef1",
            actor="test",
            purpose="forbidden second evaluation",
        )
    with pytest.raises(ValueError, match="only once|cannot reopen"):
        build_holdout_entry(
            [initialized, provisioned, opened],
            occurred_at=NOW + timedelta(minutes=3),
            event="provision",
            holdout_id="fresh-v1",
            dataset_hash="d" * 64,
            code_commit="abcdef1",
            actor="test",
            purpose="forbidden reprovision",
        )


def test_holdout_cannot_open_before_dataset_hash_is_provisioned() -> None:
    initialized = _initialize()
    with pytest.raises(ValueError, match="requires a sealed dataset hash"):
        build_holdout_entry(
            [initialized],
            occurred_at=NOW + timedelta(minutes=1),
            event="open_once",
            holdout_id="fresh-v1",
            dataset_hash=None,
            code_commit="abcdef1",
            actor="test",
            purpose="invalid opening",
        )


def test_terminal_contamination_state_cannot_be_reversed() -> None:
    initialized = _initialize()
    contaminated = build_holdout_entry(
        [initialized],
        occurred_at=NOW + timedelta(minutes=1),
        event="mark_contaminated",
        holdout_id="fresh-v1",
        dataset_hash=None,
        code_commit="abcdef1",
        actor="test",
        purpose="development influence discovered",
    )
    assert contaminated.state is HoldoutState.CONTAMINATED
    with pytest.raises(ValueError, match="terminal"):
        build_holdout_entry(
            [initialized, contaminated],
            occurred_at=NOW + timedelta(minutes=2),
            event="report_unchanged",
            holdout_id="fresh-v1",
            dataset_hash=None,
            code_commit="abcdef1",
            actor="test",
            purpose="terminal means terminal",
        )


def test_persistent_append_checks_expected_head_and_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    initialized = _initialize()
    append_holdout_entry(path, initialized, expected_head_hash=None)
    loaded = load_holdout_ledger(path)
    provisioned = _provision(loaded)
    with pytest.raises(ValueError, match="changed since"):
        append_holdout_entry(path, provisioned, expected_head_hash="f" * 64)
    append_holdout_entry(path, provisioned, expected_head_hash=initialized.entry_hash)
    assert load_holdout_ledger(path)[-1] == provisioned
    path.write_text(path.read_text().replace("fresh-v1", "changed"), encoding="utf-8")
    with pytest.raises(ValueError, match="hash is invalid"):
        load_holdout_ledger(path)


def test_committed_ledger_is_unopened_unprovisioned_and_valid() -> None:
    entries = load_holdout_ledger(ROOT / "validation/final_holdout_ledger.jsonl")
    assert len(entries) == 1
    assert entries[0].state is HoldoutState.UNOPENED
    assert entries[0].dataset_hash is None
    assert entries[0].event == "initialize"
    assert entries[0].tuning_performed is False
