from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.reporting.evidence_grade import (
    ComponentEvidenceClaim,
    EstimateWithUncertainty,
    EvidenceGrade,
    FinalDecisionEvidenceReport,
    ProbabilityWithUncertainty,
    calculate_decision_evidence_grade,
    final_decision_html,
    final_decision_markdown,
)

NOW = datetime(2026, 8, 8, 16, tzinfo=UTC)


def _numerical_claim(component_id: str) -> ComponentEvidenceClaim:
    return ComponentEvidenceClaim(
        component_id=component_id,
        implemented=True,
        tests_passed=True,
        source_ids=["book-primary"],
        numerical_validation_passed=True,
    )


def test_decision_grade_is_weakest_required_component_and_monotone() -> None:
    strong = _numerical_claim("pricing").model_copy(
        update={
            "empirical_validation_passed": True,
            "dataset_hash": "a" * 64,
            "out_of_sample_partition": "final_holdout",
            "holdout_validation_passed": True,
            "holdout_ledger_hash": "b" * 64,
            "paper_validation_passed": True,
            "paper_manifest_hash": "c" * 64,
        }
    )
    weak = ComponentEvidenceClaim(
        component_id="event_probabilities",
        implemented=True,
        tests_passed=True,
        empirical_validation_passed=True,
        dataset_hash="d" * 64,
        out_of_sample_partition="validation",
        synthetic_only=True,
    )
    grade = calculate_decision_evidence_grade([strong, weak])
    assert grade.overall_grade is EvidenceGrade.TESTED
    assert "numerical validation" in grade.blockers
    assert grade.decision_claim_cap == "software_tested_only"
    assert grade.order_capability == "forbidden"


def test_optional_component_cannot_raise_or_lower_required_grade() -> None:
    grade = calculate_decision_evidence_grade(
        [
            _numerical_claim("required"),
            ComponentEvidenceClaim(
                component_id="optional",
                required_for_decision=False,
            ),
        ]
    )
    assert grade.overall_grade is EvidenceGrade.NUMERICALLY_VALIDATED


def test_displayed_probability_requires_an_interval() -> None:
    with pytest.raises(ValidationError, match="requires an interval"):
        ProbabilityWithUncertainty(
            probability_id="profit",
            label="Probability of profit",
            central=0.5,
            origin="configured_heuristic",
            uncertainty_diagnostic="Sensitivity only.",
            source_ids=["synthetic-model"],
        )


def _report() -> FinalDecisionEvidenceReport:
    grade = calculate_decision_evidence_grade(
        [_numerical_claim("pricing"), ComponentEvidenceClaim(
            component_id="event_probabilities",
            implemented=True,
            tests_passed=True,
            blockers=["No real TTWO calibration dataset."],
        )]
    )
    return FinalDecisionEvidenceReport(
        report_id="phase9-synthetic-no-trade",
        as_of=NOW,
        decision_status="NO_TRADE",
        selected_candidate_id="NO_TRADE",
        evidence_grade=grade,
        estimates=[
            EstimateWithUncertainty(
                estimate_id="expected-pnl",
                label="Expected PnL",
                central=12,
                interval=(-40, 70),
                unit="USD",
                measure="P",
                uncertainty_diagnostic="Synthetic model range; not an OOS interval.",
                source_ids=["synthetic-scenario-report"],
            )
        ],
        probabilities=[
            ProbabilityWithUncertainty(
                probability_id="target",
                label="Target return probability",
                central=0.3,
                interval=(0.15, 0.48),
                origin="configured_heuristic",
                uncertainty_diagnostic="Belief sensitivity; not confidence coverage.",
                source_ids=["synthetic-scenario-report"],
            )
        ],
        assumptions=["Synthetic scenario weights."],
        favorable_scenarios=["Upside event and stable liquidity."],
        failure_scenarios=["Delay, IV crush or no fill."],
        model_risks=["Model disagreement is not calibrated."],
        data_limits=["No point-in-time TTWO holdout dataset."],
        ranking_reasons=["Cash is preferred because the evidence gate is not met."],
        no_trade_reasons=["Event probabilities have software tests but no empirical validation."],
        source_ids=[
            "book-bjork-arbitrage-theory",
            "official-occ-odd-2024-current-page-2026",
        ],
        synthetic_or_fixture_input=True,
    )


def test_final_report_has_every_required_section_and_static_html() -> None:
    report = _report()
    markdown = final_decision_markdown(report)
    rendered_html = final_decision_html(report)
    for heading in (
        "Estimates and uncertainty",
        "Probabilities and uncertainty",
        "Assumptions",
        "Favorable scenarios",
        "Failure scenarios",
        "Model risks",
        "Data limits",
        "Exact ranking reasons",
        "Exact NO_TRADE reasons",
    ):
        assert heading in markdown
        assert heading in rendered_html
    assert "order_capability=forbidden" in rendered_html
    assert "<script" not in rendered_html
    assert "http://" not in rendered_html
    assert "https://" not in rendered_html


def test_committed_final_evidence_example_matches_typed_contract() -> None:
    path = Path("reports/examples/phase9_final_evidence.json")
    committed = FinalDecisionEvidenceReport.model_validate_json(path.read_text())
    assert committed == _report()
    assert committed.synthetic_or_fixture_input
    assert committed.decision_status == "NO_TRADE"
