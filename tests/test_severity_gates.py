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


def test_committed_tt_report_exposes_real_severity_intervals_and_frontier() -> None:
    report = SeverityGateReport.model_validate_json(
        (ROOT / "reports/pre_opra/severity_and_gate_sensitivity_2026-08-08.json").read_text()
    )
    assert report.status == "DEVELOPMENT_ANALYSIS_READY"
    assert report.payoff_severity is not None
    assert report.payoff_severity.observations == 10
    assert report.payoff_severity.severe_loss_ladder[0].probability == pytest.approx(0.5)
    assert all(
        point.wilson_interval_95[0]
        <= point.probability
        <= point.wilson_interval_95[1]
        for point in report.payoff_severity.severe_loss_ladder
    )
    assert report.best_blocked_candidate.selection_status == "identified"
    assert report.best_blocked_candidate.failed_gates[0].name == "opportunity"
    assert report.no_position_frequency == pytest.approx(2 / 3)
    assert report.sensitivity_interpretation == "candidate_pool_evaluated"
    engine = next(
        point
        for point in report.opportunity_risk_frontier
        if point.candidate_id == "engine_candidate"
    )
    assert not engine.pareto_efficient
    assert "buy_and_hold" in engine.dominated_by
    assert report.holdout_used is False
