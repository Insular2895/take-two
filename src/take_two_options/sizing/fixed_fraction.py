"""Fixed-fraction sizing without assuming the fraction is universal."""

from __future__ import annotations


def fixed_fraction_amount(*, capital: float, fraction: float, cap: float) -> float:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be within (0, 1]")
    return min(capital * fraction, cap)
