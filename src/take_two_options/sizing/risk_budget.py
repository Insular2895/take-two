"""Risk-budget sizing."""

from __future__ import annotations


def risk_budget_amount(
    *,
    budget: float,
    maximum_loss: float,
    safety_reserve_fraction: float,
) -> float:
    available = budget * (1 - safety_reserve_fraction)
    return max(0.0, min(available, maximum_loss))
