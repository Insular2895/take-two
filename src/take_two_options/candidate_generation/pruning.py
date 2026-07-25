"""Cheap deterministic pruning before simulation."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate


def prune_candidate(candidate: CompiledStrategyCandidate) -> list[str]:
    reasons = list(candidate.hard_vetoes)
    if not candidate.broker_constructible:
        reasons.append("BROKER_CONTRACT_IDENTITY_MISSING")
    if candidate.risk.maximum_loss <= 0 and candidate.architecture.value != "iron_condor":
        reasons.append("INVALID_MAXIMUM_LOSS")
    if any(leg.quantity != int(leg.quantity) for leg in candidate.legs):
        reasons.append("NON_INTEGER_QUANTITY")
    return sorted(set(reasons))


def structurally_dominated(
    candidate: CompiledStrategyCandidate,
    incumbent: CompiledStrategyCandidate,
) -> bool:
    same_payoff = (
        candidate.architecture == incumbent.architecture
        and [(leg.side, leg.quote.symbol) for leg in candidate.legs]
        == [(leg.side, leg.quote.symbol) for leg in incumbent.legs]
    )
    return (
        same_payoff
        and candidate.risk.maximum_loss >= incumbent.risk.maximum_loss
        and candidate.risk.total_cost >= incumbent.risk.total_cost
        and (
            candidate.risk.maximum_loss > incumbent.risk.maximum_loss
            or candidate.risk.total_cost > incumbent.risk.total_cost
        )
    )
