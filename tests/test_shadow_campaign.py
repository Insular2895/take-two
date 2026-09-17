from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from take_two_options.cli import app
from take_two_options.opra.paper_decisions import (
    PaperDecisionDraft,
    PaperPrediction,
    PaperRealizationDraft,
    build_paper_decision_record,
    build_paper_realization_record,
)
from take_two_options.opra.shadow_campaign import (
    ShadowCampaignManifest,
    ShadowCampaignThresholds,
    evaluate_shadow_campaign,
)

CONFIG_HASH = "a" * 64
IBKR_REPORT_HASH = "b" * 64
HOLDOUT_HASH = "c" * 64
COMMIT = "abcdef1234567"


def _manifest(**updates: object) -> ShadowCampaignManifest:
    payload: dict[str, object] = {
        "campaign_id": "ttwo-shadow-2026-08",
        "planned_start_at": datetime(2026, 8, 8, tzinfo=UTC),
        "planned_end_at": datetime(2026, 8, 31, tzinfo=UTC),
        "approval_status": "approved",
        "thresholds": ShadowCampaignThresholds(
            minimum_decisions=1,
            minimum_realizations=1,
        ),
        "code_commit": COMMIT,
        "strategy_config_hash": CONFIG_HASH,
        "ibkr_validation_report_hash": IBKR_REPORT_HASH,
        "holdout_ledger_hash": HOLDOUT_HASH,
        "data_rights_approval_reference": "owner-review-1",
        "risk_owner_approval_reference": "risk-review-1",
        "example_only": False,
    }
    payload.update(updates)
    return ShadowCampaignManifest.model_validate(payload)


def _decision(*, config_hash: str = CONFIG_HASH):
    return build_paper_decision_record(
        [],
        PaperDecisionDraft(
            decision_id="d1",
            decided_at=datetime(2026, 8, 10, tzinfo=UTC),
            snapshot_id="snapshot-d1",
            snapshot_hash="d" * 64,
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
            config_hash=config_hash,
            code_commit=COMMIT,
        ),
    )


def _realization(decision):
    return build_paper_realization_record(
        PaperRealizationDraft(
            realization_id="r1",
            decision_id=decision.decision_id,
            decision_record_hash=decision.record_hash,
            observed_at=datetime(2026, 8, 13, tzinfo=UTC),
            realized_path_hash="e" * 64,
            paper_entry_timestamp=datetime(2026, 8, 10, tzinfo=UTC),
            paper_exit_timestamp=datetime(2026, 8, 12, tzinfo=UTC),
            paper_entry_price=0,
            paper_exit_price=0,
            slippage_eur=0,
            fees_eur=0,
            pnl_eur=0,
            postmortem="NO_POSITION remained the prudent paper decision.",
        ),
        decisions=[decision],
    )


def test_draft_manifest_is_blocked_without_starting_any_campaign() -> None:
    manifest = ShadowCampaignManifest(
        campaign_id="draft",
        planned_start_at=datetime(2026, 8, 8, tzinfo=UTC),
        planned_end_at=datetime(2026, 8, 31, tzinfo=UTC),
    )
    report = evaluate_shadow_campaign(
        manifest,
        [],
        [],
        now=lambda: datetime(2026, 8, 7, tzinfo=UTC),
    )
    assert report.status == "BLOCKED_DRAFT"
    assert report.maximum_claim == "software_only"
    assert report.paper_validation_passed is False
    assert report.promotion_eligible is False


def test_approved_manifest_requires_human_thresholds_and_lineage() -> None:
    with pytest.raises(ValidationError, match="approved shadow campaign requires"):
        ShadowCampaignManifest(
            campaign_id="unsafe",
            planned_start_at=datetime(2026, 8, 8, tzinfo=UTC),
            planned_end_at=datetime(2026, 8, 31, tzinfo=UTC),
            approval_status="approved",
            example_only=False,
        )


def test_approved_campaign_is_ready_before_its_window() -> None:
    report = evaluate_shadow_campaign(
        _manifest(),
        [],
        [],
        now=lambda: datetime(2026, 8, 7, tzinfo=UTC),
    )
    assert report.status == "READY_TO_START"
    assert report.maximum_claim == "campaign_control_ready"
    assert report.order_capability == "forbidden"


def test_reaching_observation_targets_still_requires_human_review() -> None:
    decision = _decision()
    realization = _realization(decision)
    report = evaluate_shadow_campaign(
        _manifest(),
        [decision],
        [realization],
        now=lambda: datetime(2026, 8, 14, tzinfo=UTC),
    )
    assert report.status == "OBSERVATION_TARGET_REACHED_PENDING_HUMAN_REVIEW"
    assert report.maximum_claim == "prospective_observations_recorded"
    assert report.no_position_count == 1
    assert report.missing_realization_count == 0
    assert report.paper_validation_passed is False
    assert report.promotion_eligible is False


def test_configuration_drift_fails_safe() -> None:
    report = evaluate_shadow_campaign(
        _manifest(),
        [_decision(config_hash="f" * 64)],
        [],
        now=lambda: datetime(2026, 8, 14, tzinfo=UTC),
    )
    assert report.status == "FAILED_SAFE"
    assert any(
        item.detail_code == "SHADOW_CONFIG_HASH_DRIFT" and item.status == "FAIL"
        for item in report.checks
    )


def test_incomplete_campaign_window_never_claims_validation() -> None:
    report = evaluate_shadow_campaign(
        _manifest(),
        [],
        [],
        now=lambda: datetime(2026, 9, 1, tzinfo=UTC),
    )
    assert report.status == "WINDOW_ENDED_INCOMPLETE"
    assert report.paper_validation_passed is False


def test_shadow_status_cli_keeps_the_example_blocked_and_offline(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "status.json"
    result = CliRunner().invoke(
        app,
        [
            "paper",
            "shadow-status",
            "--manifest",
            str(root / "configs/paper/shadow_campaign.example.json"),
            "--decision-ledger",
            str(tmp_path / "missing-decisions.jsonl"),
            "--realization-ledger",
            str(tmp_path / "missing-realizations.jsonl"),
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 1
    assert "BLOCKED_DRAFT" in result.output
    assert "connection_attempted=false" in result.output
    assert '"paper_validation_passed": false' in output.read_text(encoding="utf-8")
