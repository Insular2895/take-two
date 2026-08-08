from __future__ import annotations

from pathlib import Path

import pytest

from take_two_options.decision.severity_gates import (
    CandidateGateInput,
    GateSetting,
    SeverityGateReport,
    evaluate_gate_sensitivity,
    payoff_severity,
)

ROOT = Path(__file__).resolve().parents[1]


def _setting(setting_id: str, opportunity: float, risk: float) -> GateSetting:
    return GateSetting(
        setting_id=setting_id,
        minimum_opportunity=opportunity,
        maximum_risk=risk,
        minimum_evidence=50,
        minimum_execution_quality=50,
        status="draft_to_validate",
    )


def test_severe_loss_ladder_is_complete_and_monotone() -> None:
    severity = payoff_severity([-1.0, -0.8, -0.6, -0.3, -0.15, 0.2, 0.5])
    assert [point.loss_threshold for point in severity.severe_loss_ladder] == [
        0.10,
        0.25,
        0.50,
        0.70,
        0.90,
        0.99,
    ]
    probabilities = [point.probability for point in severity.severe_loss_ladder]
    assert probabilities == sorted(probabilities, reverse=True)
    assert severity.worst_return == -1


def test_gate_sensitivity_exposes_no_position_frequency_and_best_candidate() -> None:
    candidates = [
        CandidateGateInput(
            candidate_id="a",
            opportunity_score=75,
            risk_score=45,
            evidence_score=70,
            execution_quality_score=70,
        ),
        CandidateGateInput(
            candidate_id="b",
            opportunity_score=65,
            risk_score=30,
            evidence_score=70,
            execution_quality_score=70,
        ),
    ]
    rows, frequency = evaluate_gate_sensitivity(
        candidates,
        [_setting("loose", 60, 50), _setting("strict", 80, 30)],
    )
    assert rows[0].best_candidate_id == "a"
    assert rows[1].no_position_recommended
    assert frequency == pytest.approx(0.5)


def test_empty_candidate_pool_is_not_presented_as_financial_gate_sensitivity() -> None:
    rows, frequency = evaluate_gate_sensitivity([], [_setting("base", 50, 70)])
    assert rows[0].no_position_recommended
    assert frequency == 1


def test_committed_tt_report_marks_all_severity_outputs_unavailable() -> None:
    report = SeverityGateReport.model_validate_json(
        (ROOT / "reports/pre_opra/severity_and_gate_sensitivity_2026-08-08.json").read_text()
    )
    assert report.status == "BLOCKED_NO_CANDIDATE_DISTRIBUTION"
    assert report.payoff_severity is None
    assert report.best_blocked_candidate.selection_status == "unavailable"
    assert report.no_position_frequency == 1
    assert report.sensitivity_interpretation == "pipeline_blocked_empty_candidate_pool"
