"""Deterministic Monte Carlo convergence checks."""

from __future__ import annotations

import math
from statistics import fmean, stdev


def expectation_converged(
    values: list[float],
    *,
    relative_tolerance: float = 0.05,
    absolute_tolerance: float = 5.0,
) -> bool:
    if len(values) < 100 or len(values) % 2:
        return False
    half = len(values) // 2
    first = fmean(values[:half])
    full = fmean(values)
    tolerance = max(abs(full) * relative_tolerance, absolute_tolerance)
    standard_error = stdev(values) / math.sqrt(len(values)) if len(values) > 1 else math.inf
    return abs(first - full) <= tolerance and 1.96 * standard_error <= tolerance
