"""Local stability around strike/expiration/exit-policy neighbors."""

from __future__ import annotations

from statistics import fmean

from take_two_options.knowledge.schemas import CompiledStrategyCandidate


def local_stability(
    candidate: CompiledStrategyCandidate,
    population: list[CompiledStrategyCandidate],
) -> float | None:
    expectation = candidate.evaluation.conservative_expected_pnl
    if expectation is None:
        return None
    candidate_strikes = sorted(leg.quote.strike for leg in candidate.legs)
    neighbors = [
        other
        for other in population
        if other.candidate_id != candidate.candidate_id
        and other.architecture is candidate.architecture
        and len(other.legs) == len(candidate.legs)
        and abs(
            other.exit_policy.maximum_holding_days
            - candidate.exit_policy.maximum_holding_days
        )
        <= 30
        and max(
            abs(left - right)
            for left, right in zip(
                candidate_strikes,
                sorted(leg.quote.strike for leg in other.legs),
                strict=True,
            )
        )
        <= 10
    ]
    values = [
        other.evaluation.conservative_expected_pnl
        for other in neighbors
        if other.evaluation.conservative_expected_pnl is not None
    ]
    if len(values) < 2:
        return None
    scale = max(abs(expectation), abs(fmean(values)), 1.0)
    dispersion = fmean(abs(value - expectation) for value in values) / scale
    return max(0.0, min(1.0, 1.0 - dispersion))
