"""Secondary explanatory ranking applied only after vetoes and Pareto."""

from __future__ import annotations

import math

from take_two_options.knowledge.schemas import CompiledStrategyCandidate
from take_two_options.quantitative.contracts import Measure, ModelEligibility


def _normalize(values: list[float], value: float, *, higher_is_better: bool) -> float:
    low, high = min(values), max(values)
    if high == low:
        return 0.5
    normalized = (value - low) / (high - low)
    return normalized if higher_is_better else 1 - normalized


def _required(value: float | None, reason: str) -> float:
    if value is None:
        raise ValueError(reason)
    return value


def _has_decision_metrics(candidate: CompiledStrategyCandidate) -> bool:
    return any(
        metric.eligibility is ModelEligibility.DECISION_ELIGIBLE
        and metric.measure is Measure.REAL_WORLD
        for metric in candidate.evaluation.model_metrics
    )


def apply_explanatory_scores(
    candidates: list[CompiledStrategyCandidate],
    weights: dict[str, float],
) -> list[CompiledStrategyCandidate]:
    if not candidates:
        return []
    scorable = [
        candidate
        for candidate in candidates
        if candidate.evaluation.decision_status is ModelEligibility.DECISION_ELIGIBLE
        and candidate.evaluation.conservative_expected_pnl is not None
        and candidate.risk.maximum_loss is not None
        and candidate.evaluation.local_stability is not None
        and _has_decision_metrics(candidate)
    ]
    unscorable = [candidate for candidate in candidates if candidate not in scorable]
    if not scorable:
        return sorted(unscorable, key=lambda candidate: candidate.candidate_id)
    expectations = [
        _required(
            candidate.evaluation.conservative_expected_pnl,
            "missing conservative expectation after eligibility filtering",
        )
        for candidate in scorable
    ]
    probabilities = [
        min(
            metric.probability_profit
            for metric in candidate.evaluation.model_metrics
            if metric.eligibility is ModelEligibility.DECISION_ELIGIBLE
            and metric.measure is Measure.REAL_WORLD
        )
        for candidate in scorable
    ]
    cvars = [
        max(
            metric.cvar_95
            for metric in candidate.evaluation.model_metrics
            if metric.eligibility is ModelEligibility.DECISION_ELIGIBLE
            and metric.measure is Measure.REAL_WORLD
        )
        for candidate in scorable
    ]
    losses = [
        _required(candidate.risk.maximum_loss, "missing maximum loss after filtering")
        for candidate in scorable
    ]
    liquidities = [
        min(
            (
                (leg.quote.open_interest or 0)
                / max((leg.quote.open_interest or 0) + 100, 1)
                for leg in candidate.legs
            ),
            default=0,
        )
        for candidate in scorable
    ]
    stabilities = [
        _required(
            candidate.evaluation.local_stability,
            "missing local stability after filtering",
        )
        for candidate in scorable
    ]
    complexities = [candidate.evaluation.complexity_penalty for candidate in scorable]
    all_values = [
        *expectations,
        *probabilities,
        *cvars,
        *losses,
        *liquidities,
        *stabilities,
        *complexities,
    ]
    if not all(math.isfinite(value) for value in all_values):
        for candidate in scorable:
            candidate.evaluation.decision_status = ModelEligibility.BLOCKED
            candidate.evaluation.numerical_failures.append("NUMERICAL_FAILURE_RANKING")
        return sorted(candidates, key=lambda candidate: candidate.candidate_id)
    for index, candidate in enumerate(scorable):
        components = {
            "conservative_expected_pnl": _normalize(
                expectations, expectations[index], higher_is_better=True
            ),
            "probability_profit": _normalize(
                probabilities, probabilities[index], higher_is_better=True
            ),
            "cvar": _normalize(cvars, cvars[index], higher_is_better=False),
            "maximum_loss": _normalize(losses, losses[index], higher_is_better=False),
            "liquidity": _normalize(
                liquidities, liquidities[index], higher_is_better=True
            ),
            "local_stability": _normalize(
                stabilities, stabilities[index], higher_is_better=True
            ),
            "complexity": _normalize(
                complexities, complexities[index], higher_is_better=False
            ),
        }
        denominator = sum(weights.get(name, 0.0) for name in components)
        candidate.explanatory_score = (
            100
            * sum(weights.get(name, 0.0) * value for name, value in components.items())
            / denominator
            if denominator
            else 0.0
        )
    ranked = sorted(
        scorable,
        key=lambda candidate: (
            candidate.pareto_rank or 10_000,
            -_required(candidate.explanatory_score, "explanatory score was not assigned"),
            candidate.candidate_id,
        ),
    )
    return [*ranked, *sorted(unscorable, key=lambda candidate: candidate.candidate_id)]
