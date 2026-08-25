"""Fundamental scenarios remain explicit inputs, never hidden model weights."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FundamentalScenario:
    scenario_id: str
    description: str
    probability: float | None
    source_ids: tuple[str, ...]


def validate_scenarios(scenarios: list[FundamentalScenario]) -> list[str]:
    errors: list[str] = []
    specified = [scenario.probability for scenario in scenarios if scenario.probability is not None]
    if specified and len(specified) != len(scenarios):
        errors.append("scenario probabilities must be all specified or all unknown")
    if specified and abs(sum(specified) - 1.0) > 1e-9:
        errors.append("specified scenario probabilities must sum to one")
    return errors
