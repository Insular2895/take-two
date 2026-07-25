"""Secondary explanatory ranking applied only after vetoes and Pareto."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate


def _normalize(values: list[float], value: float, *, higher_is_better: bool) -> float:
    low, high = min(values), max(values)
    if high == low:
        return 0.5
    normalized = (value - low) / (high - low)
    return normalized if higher_is_better else 1 - normalized


def apply_explanatory_scores(
    candidates: list[CompiledStrategyCandidate],
    weights: dict[str, float],
) -> list[CompiledStrategyCandidate]:
    if not candidates:
        return []
    expectations = [
        candidate.evaluation.conservative_expected_pnl or 0.0
        for candidate in candidates
    ]
    probabilities = [
        min((metric.probability_profit for metric in candidate.evaluation.model_metrics), default=0)
        for candidate in candidates
    ]
    cvars = [
        max((metric.cvar_95 for metric in candidate.evaluation.model_metrics), default=0)
        for candidate in candidates
    ]
    losses = [candidate.risk.maximum_loss for candidate in candidates]
    liquidities = [
        min(
            (
                (leg.quote.open_interest or 0)
                / max((leg.quote.open_interest or 0) + 100, 1)
                for leg in candidate.legs
            ),
            default=0,
        )
        for candidate in candidates
    ]
    stabilities = [candidate.evaluation.local_stability or 0 for candidate in candidates]
    complexities = [candidate.evaluation.complexity_penalty for candidate in candidates]
    for index, candidate in enumerate(candidates):
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
    return sorted(
        candidates,
        key=lambda candidate: (
            candidate.pareto_rank or 10_000,
            -(candidate.explanatory_score or 0),
            candidate.candidate_id,
        ),
    )
