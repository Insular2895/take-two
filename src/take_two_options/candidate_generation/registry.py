"""Architecture registry for the active optimizer.

LEAPS is intentionally absent: long-dated options are represented by recipe DTE
constraints on long calls and long puts.
"""

from __future__ import annotations

from dataclasses import dataclass

from take_two_options.knowledge.schemas import Architecture


@dataclass(frozen=True)
class ArchitectureDefinition:
    architecture: Architecture
    legs: int
    bounded_risk: bool
    unbounded_upside: bool
    thesis_families: tuple[str, ...]


ARCHITECTURE_REGISTRY: dict[Architecture, ArchitectureDefinition] = {
    Architecture.LONG_CALL: ArchitectureDefinition(
        Architecture.LONG_CALL, 1, True, True, ("bullish",)
    ),
    Architecture.LONG_PUT: ArchitectureDefinition(
        Architecture.LONG_PUT, 1, True, False, ("bearish",)
    ),
    Architecture.BULL_CALL_SPREAD: ArchitectureDefinition(
        Architecture.BULL_CALL_SPREAD, 2, True, False, ("bullish",)
    ),
    Architecture.BEAR_PUT_SPREAD: ArchitectureDefinition(
        Architecture.BEAR_PUT_SPREAD, 2, True, False, ("bearish",)
    ),
    Architecture.CALL_BUTTERFLY: ArchitectureDefinition(
        Architecture.CALL_BUTTERFLY, 3, True, False, ("neutral", "bullish")
    ),
    Architecture.PUT_BUTTERFLY: ArchitectureDefinition(
        Architecture.PUT_BUTTERFLY, 3, True, False, ("neutral", "bearish")
    ),
    Architecture.CALL_BROKEN_WING_BUTTERFLY: ArchitectureDefinition(
        Architecture.CALL_BROKEN_WING_BUTTERFLY,
        3,
        True,
        False,
        ("neutral", "bullish"),
    ),
    Architecture.PUT_BROKEN_WING_BUTTERFLY: ArchitectureDefinition(
        Architecture.PUT_BROKEN_WING_BUTTERFLY,
        3,
        True,
        False,
        ("neutral", "bearish"),
    ),
    Architecture.CALL_CALENDAR: ArchitectureDefinition(
        Architecture.CALL_CALENDAR, 2, True, True, ("neutral", "bullish")
    ),
    Architecture.PUT_CALENDAR: ArchitectureDefinition(
        Architecture.PUT_CALENDAR, 2, True, False, ("neutral", "bearish")
    ),
    Architecture.CALL_DIAGONAL: ArchitectureDefinition(
        Architecture.CALL_DIAGONAL, 2, True, True, ("bullish",)
    ),
    Architecture.PUT_DIAGONAL: ArchitectureDefinition(
        Architecture.PUT_DIAGONAL, 2, True, False, ("bearish",)
    ),
    Architecture.LONG_STRADDLE: ArchitectureDefinition(
        Architecture.LONG_STRADDLE, 2, True, True, ("volatile",)
    ),
    Architecture.LONG_STRANGLE: ArchitectureDefinition(
        Architecture.LONG_STRANGLE, 2, True, True, ("volatile",)
    ),
    Architecture.IRON_CONDOR: ArchitectureDefinition(
        Architecture.IRON_CONDOR, 4, True, False, ("neutral",)
    ),
}
