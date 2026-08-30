"""Hard-veto filtering followed by a non-compensatory Pareto frontier."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate
from take_two_options.quantitative.contracts import Measure, ModelEligibility


def _objectives(candidate: CompiledStrategyCandidate) -> tuple[float, ...]:
    metrics = [
        item
        for item in candidate.evaluation.model_metrics
        if item.eligibility is ModelEligibility.DECISION_ELIGIBLE
        and item.measure is Measure.REAL_WORLD
    ]
    expectation = candidate.evaluation.conservative_expected_pnl
    maximum_loss = candidate.risk.maximum_loss
    stability = candidate.evaluation.local_stability
    if not metrics or expectation is None or maximum_loss is None or stability is None:
        raise ValueError("blocked candidates cannot enter Pareto objectives")
    probability_profit = min(item.probability_profit for item in metrics)
    cvar = max(item.cvar_95 for item in metrics)
    mean_exit = max(item.mean_exit_days for item in metrics)
    return (
        expectation,
        probability_profit,
        -cvar,
        -maximum_loss,
        -max(candidate.risk.total_cost, 0),
        stability,
        -candidate.evaluation.complexity_penalty,
        -mean_exit,
    )


def dominates(left: CompiledStrategyCandidate, right: CompiledStrategyCandidate) -> bool:
    left_values = _objectives(left)
    right_values = _objectives(right)
    return all(a >= b for a, b in zip(left_values, right_values, strict=True)) and any(
        a > b for a, b in zip(left_values, right_values, strict=True)
    )


def pareto_rank(candidates: list[CompiledStrategyCandidate]) -> list[list[str]]:
    remaining = [
        candidate
        for candidate in candidates
        if candidate.evaluation.decision_status is ModelEligibility.DECISION_ELIGIBLE
        and candidate.evaluation.conservative_expected_pnl is not None
        and candidate.risk.maximum_loss is not None
        and candidate.evaluation.local_stability is not None
    ]
    fronts: list[list[str]] = []
    rank = 1
    while remaining:
        front = [
            candidate
            for candidate in remaining
            if not any(
                dominates(other, candidate)
                for other in remaining
                if other.candidate_id != candidate.candidate_id
            )
        ]
        if not front:
            break
        for candidate in front:
            candidate.pareto_rank = rank
        fronts.append(sorted(candidate.candidate_id for candidate in front))
        ids = {candidate.candidate_id for candidate in front}
        remaining = [candidate for candidate in remaining if candidate.candidate_id not in ids]
        rank += 1
    return fronts
