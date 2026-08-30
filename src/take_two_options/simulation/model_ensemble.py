"""Conservative cross-model summaries without fitted or arbitrary weights."""

from __future__ import annotations

import math
from statistics import fmean

from take_two_options.knowledge.schemas import CandidateEvaluation, ModelMetrics
from take_two_options.quantitative.contracts import Measure, ModelEligibility


def summarize_models(metrics: list[ModelMetrics]) -> CandidateEvaluation:
    invalid = [item.model_id for item in metrics if not math.isfinite(item.expected_pnl)]
    if invalid:
        return CandidateEvaluation(
            model_metrics=metrics,
            decision_status=ModelEligibility.BLOCKED,
            decision_reasons=[f"NUMERICAL_FAILURE:{model_id}" for model_id in invalid],
            numerical_failures=invalid,
        )
    eligible = [
        item
        for item in metrics
        if item.eligibility.may_drive_decision and item.measure is Measure.REAL_WORLD
    ]
    expectations = [item.expected_pnl for item in eligible]
    if not expectations:
        return CandidateEvaluation(
            model_metrics=metrics,
            conservative_expected_pnl=None,
            model_dispersion=None,
            decision_status=ModelEligibility.BLOCKED,
            decision_reasons=["NO_DECISION_ELIGIBLE_REAL_WORLD_MODEL"],
        )
    return CandidateEvaluation(
        model_metrics=metrics,
        conservative_expected_pnl=min(expectations),
        model_dispersion=(
            max(expectations) - min(expectations) if len(expectations) > 1 else 0.0
        ),
        decision_status=ModelEligibility.DECISION_ELIGIBLE,
        stress_results={
            "unweighted_decision_eligible_mean_expected_pnl": fmean(expectations)
        },
    )
