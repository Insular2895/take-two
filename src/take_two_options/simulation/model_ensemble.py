"""Conservative cross-model summaries without fitted or arbitrary weights."""

from __future__ import annotations

from statistics import fmean

from take_two_options.knowledge.schemas import CandidateEvaluation, ModelMetrics


def summarize_models(metrics: list[ModelMetrics]) -> CandidateEvaluation:
    expectations = [item.expected_pnl for item in metrics]
    return CandidateEvaluation(
        model_metrics=metrics,
        conservative_expected_pnl=min(expectations) if expectations else None,
        model_dispersion=(
            max(expectations) - min(expectations) if len(expectations) > 1 else 0.0
        ),
        stress_results={
            "unweighted_descriptive_mean_expected_pnl": fmean(expectations)
            if expectations
            else 0.0
        },
    )
