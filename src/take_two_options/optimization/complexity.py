"""Transparent complexity penalty; never a substitute for hard gates."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate


def complexity_penalty(candidate: CompiledStrategyCandidate) -> float:
    legs = len(candidate.legs)
    maintenance = sum(
        value != "none"
        for value in (
            candidate.maintenance_policy.rolling_rule,
            candidate.maintenance_policy.capital_recovery_rule,
        )
    )
    triggers = sum(
        value is not None
        for value in (
            candidate.exit_policy.profit_target,
            candidate.exit_policy.stop_loss,
            candidate.exit_policy.trailing_stop,
        )
    )
    return round(max(0.0, (legs - 1) * 0.04 + maintenance * 0.05 + triggers * 0.02), 6)
