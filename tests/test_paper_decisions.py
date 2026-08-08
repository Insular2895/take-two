from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.opra.paper_decisions import (
    PaperDecisionDraft,
    PaperPrediction,
    PaperRealizationDraft,
    append_paper_decision,
    build_paper_decision_record,
    build_paper_realization_record,
    load_paper_decisions,
)


def _draft(decision_id: str, decided_at: datetime) -> PaperDecisionDraft:
    return PaperDecisionDraft(
        decision_id=decision_id,
        decided_at=decided_at,
        snapshot_id=f"snapshot-{decision_id}",
        snapshot_hash="a" * 64,
        candidate_set=("engine_candidate", "no_position"),
        five_scores={"opportunity": 37.1, "risk": 49.5},
        score_coverages={"opportunity": 1.0, "risk": 1.0},
        raw_metrics={"expected_return": -0.01},
        classification="AVOID",
        selected_candidate="no_position",
        best_baseline="buy_and_hold",
        predictions=(
            PaperPrediction(
                model_id="garch",
                metric="probability_profit",
                value=0.2,
                unit="probability",
                confidence_interval=(0.05, 0.51),
            ),
        ),
        decision_confidence_intervals={"expected_return": (-0.2, 0.1)},
        config_hash="b" * 64,
        code_commit="abcdef1234567",
    )


def test_paper_decisions_are_frozen_hash_chained_and_append_only(tmp_path: Path) -> None:
    first = build_paper_decision_record([], _draft("d1", datetime(2026, 8, 8, tzinfo=UTC)))
    with pytest.raises(ValidationError):
        first.classification = "CANDIDATE"
    path = tmp_path / "paper_decisions.jsonl"
    append_paper_decision(path, first, expected_head_hash=None)
    second = build_paper_decision_record(
        [first], _draft("d2", datetime(2026, 8, 9, tzinfo=UTC))
    )
    append_paper_decision(path, second, expected_head_hash=first.record_hash)
    loaded = load_paper_decisions(path)
    assert loaded == [first, second]
    assert second.previous_hash == first.record_hash
    with pytest.raises(ValueError, match="changed since"):
        append_paper_decision(path, second, expected_head_hash=first.record_hash)


def test_realization_is_a_separate_record_linked_to_frozen_decision() -> None:
    decision = build_paper_decision_record(
        [], _draft("d1", datetime(2026, 8, 8, tzinfo=UTC))
    )
    realization = build_paper_realization_record(
        PaperRealizationDraft(
            realization_id="r1",
            decision_id=decision.decision_id,
            decision_record_hash=decision.record_hash,
            observed_at=datetime(2026, 8, 10, tzinfo=UTC),
            realized_path_hash="c" * 64,
            paper_entry_timestamp=datetime(2026, 8, 8, tzinfo=UTC),
            paper_exit_timestamp=datetime(2026, 8, 10, tzinfo=UTC),
            paper_entry_price=10,
            paper_exit_price=8,
            slippage_eur=2,
            fees_eur=1,
            pnl_eur=-203,
            postmortem="future-only fixture",
        )
    )
    assert realization.decision_record_hash == decision.record_hash
    assert realization.record_kind == "paper_realization"
    assert "pnl_eur" not in type(decision).model_fields
    assert realization.paper_exit_timestamp > realization.paper_entry_timestamp
