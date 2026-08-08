from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.decision.quality_scores import (
    FiveScoreReport,
    RawScoreMetric,
    ScoreComponent,
    ScoreFormula,
    ScoreKind,
    calculate_quality_score,
    classify_candidate,
)

ROOT = Path(__file__).resolve().parents[1]


def _formula() -> ScoreFormula:
    return ScoreFormula(
        kind=ScoreKind.OPPORTUNITY,
        version="test-v1",
        components=[
            ScoreComponent(
                metric_name="expected_return",
                lower_bound=-0.5,
                upper_bound=1.0,
                direction="increasing",
                weight=0.6,
                weight_status="draft_to_validate",
                rationale="synthetic test",
            ),
            ScoreComponent(
                metric_name="probability_profit",
                lower_bound=0,
                upper_bound=1,
                direction="increasing",
                weight=0.4,
                weight_status="draft_to_validate",
                rationale="synthetic test",
            ),
        ],
    )


def _metrics(expected_return: float) -> list[RawScoreMetric]:
    return [
        RawScoreMetric(
            name="expected_return",
            value=expected_return,
            unit="ratio",
            source_id="fixture",
            available=True,
        ),
        RawScoreMetric(
            name="probability_profit",
            value=0.6,
            unit="probability",
            source_id="fixture",
            available=True,
        ),
    ]


def test_score_is_monotone_and_exposes_raw_metrics_and_sensitivity() -> None:
    low = calculate_quality_score(_formula(), _metrics(0.0))
    high = calculate_quality_score(_formula(), _metrics(0.5))
    assert high.score is not None and low.score is not None and high.score > low.score
    assert high.sensitivity_interval is not None
    assert high.sensitivity_interval[0] <= high.score <= high.sensitivity_interval[1]
    assert high.raw_metrics[0].value == 0.5


def test_missing_metric_produces_no_score() -> None:
    result = calculate_quality_score(_formula(), _metrics(0.2)[:1])
    assert result.score is None
    assert result.contributions == []
    assert "probability_profit" in result.unavailable_reasons[0]


def test_weights_must_be_explicit_and_sum_to_one() -> None:
    payload = _formula().model_dump()
    payload["components"][0]["weight"] = 0.5
    with pytest.raises(ValidationError, match="sum to one"):
        ScoreFormula.model_validate(payload)


def test_classification_keeps_high_risk_and_execution_blocks_visible() -> None:
    assert (
        classify_candidate(
            opportunity=90, risk=85, evidence=90, model_agreement=90, execution_quality=90
        )
        == "HIGH_RISK"
    )
    assert (
        classify_candidate(
            opportunity=90, risk=20, evidence=90, model_agreement=90, execution_quality=20
        )
        == "BLOCKED_EXECUTION"
    )


def test_committed_tt_report_has_five_unavailable_scores_and_no_composite() -> None:
    report = FiveScoreReport.model_validate_json(
        (ROOT / "reports/pre_opra/five_scores_2026-08-08.json").read_text()
    )
    assert report.composite_score is None
    assert report.classification == "BLOCKED_VALIDATION"
    assert all(
        score.score is None
        for score in (
            report.opportunity,
            report.risk,
            report.evidence,
            report.model_agreement,
            report.execution_quality,
        )
    )
