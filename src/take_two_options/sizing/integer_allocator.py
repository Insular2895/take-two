"""Integer-only allocator for option contracts."""

from __future__ import annotations

import math


def maximum_whole_contracts(
    *,
    per_structure_maximum_loss: float,
    budget: float,
    maximum_contracts: int,
    safety_reserve_fraction: float,
) -> int:
    if per_structure_maximum_loss <= 0:
        return 0
    available = budget * (1 - safety_reserve_fraction)
    return max(0, min(math.floor(available / per_structure_maximum_loss), maximum_contracts))
