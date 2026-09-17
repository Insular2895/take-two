from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from take_two_options.cli import app
from take_two_options.opra.what_if import (
    BrokerWhatIfObservation,
    normalize_broker_what_if,
)

NOW = datetime(2026, 9, 17, 18, 0, tzinfo=UTC)


def _observation(**updates: object) -> BrokerWhatIfObservation:
    payload: dict[str, object] = {
        "candidate_id": "candidate-1",
        "observed_at": NOW,
        "source_id": "ibkr-paper-redacted-1",
        "currency": "USD",
        "commission_currency": "USD",
        "commission": "2.45",
        "minimum_commission": "1.00",
        "maximum_commission": "3.00",
        "initial_margin_change": "125.50",
        "maintenance_margin_change": "110.25",
        "example_only": False,
    }
    payload.update(updates)
    return BrokerWhatIfObservation.model_validate(payload)


def test_complete_observation_is_normalized_without_order_capability() -> None:
    report = normalize_broker_what_if(_observation(warning_text="account detail removed"))
    assert report.status == "NORMALIZED_COMPLETE"
    assert report.evidence.complete is True
    assert report.evidence.estimated_commission == pytest.approx(2.45)
    assert report.evidence.initial_margin_change == pytest.approx(125.5)
    assert report.evidence.buying_power_change is None
    assert report.evidence.warnings == [
        "WHAT_IF_INITIAL_MARGIN_BEFORE_MISSING",
        "WHAT_IF_INITIAL_MARGIN_AFTER_MISSING",
        "WHAT_IF_MAINTENANCE_MARGIN_BEFORE_MISSING",
        "WHAT_IF_MAINTENANCE_MARGIN_AFTER_MISSING",
        "WHAT_IF_EQUITY_WITH_LOAN_BEFORE_MISSING",
        "WHAT_IF_EQUITY_WITH_LOAN_CHANGE_MISSING",
        "WHAT_IF_EQUITY_WITH_LOAN_AFTER_MISSING",
        "WHAT_IF_BROKER_WARNING_PRESENT_REDACTED",
    ]
    assert "account detail removed" not in report.model_dump_json()
    assert report.connection_attempted is False
    assert report.strategy_promotion_eligible is False


def test_missing_and_sentinel_values_remain_unknown_and_incomplete() -> None:
    report = normalize_broker_what_if(
        _observation(
            commission="1.7976931348623157e308",
            initial_margin_change="not-a-number",
            commission_currency=None,
        )
    )
    assert report.status == "NORMALIZED_INCOMPLETE"
    assert report.evidence.estimated_commission is None
    assert report.evidence.initial_margin_change is None
    assert "WHAT_IF_COMMISSION_SENTINEL" in report.evidence.warnings
    assert "WHAT_IF_INITIAL_MARGIN_CHANGE_INVALID" in report.evidence.warnings
    assert "WHAT_IF_COMMISSION_CURRENCY_MISSING" in report.evidence.warnings


def test_example_observation_is_rejected() -> None:
    with pytest.raises(ValueError, match="MARKED_EXAMPLE_ONLY"):
        normalize_broker_what_if(_observation(example_only=True))


def test_cli_writes_sanitized_evidence_without_connecting(tmp_path: Path) -> None:
    observation_path = tmp_path / "observation.json"
    evidence_path = tmp_path / "evidence.json"
    report_path = tmp_path / "report.json"
    observation_path.write_text(_observation().model_dump_json(indent=2), encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "paper",
            "what-if-normalize",
            "--observation",
            str(observation_path),
            "--evidence-out",
            str(evidence_path),
            "--report-out",
            str(report_path),
        ],
    )
    assert result.exit_code == 0
    assert "NORMALIZED_COMPLETE" in result.output
    assert "connection_attempted=false" in result.output
    assert json.loads(evidence_path.read_text(encoding="utf-8"))["complete"] is True
    assert json.loads(report_path.read_text(encoding="utf-8"))["transmit"] is False


def test_committed_example_is_blocked_before_writing_evidence(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    evidence_path = tmp_path / "evidence.json"
    report_path = tmp_path / "report.json"
    result = CliRunner().invoke(
        app,
        [
            "paper",
            "what-if-normalize",
            "--observation",
            str(root / "configs/opra/ibkr_what_if_observation.example.json"),
            "--evidence-out",
            str(evidence_path),
            "--report-out",
            str(report_path),
        ],
    )
    assert result.exit_code == 1
    assert "MARKED_EXAMPLE_ONLY" in result.output
    assert not evidence_path.exists()
    assert not report_path.exists()
