"""Read-only maintenance state machine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PositionState(StrEnum):
    PLANNED = "PLANNED"
    ORDER_PREVIEWED = "ORDER_PREVIEWED"
    PAPER_OPEN = "PAPER_OPEN"
    LIVE_ASSISTED_OPEN = "LIVE_ASSISTED_OPEN"
    CAPITAL_RECOVERED = "CAPITAL_RECOVERED"
    TRAILING_ACTIVE = "TRAILING_ACTIVE"
    ROLL_REVIEW = "ROLL_REVIEW"
    EXIT_PENDING = "EXIT_PENDING"
    CLOSED = "CLOSED"
    KILLED = "KILLED"


ALLOWED_TRANSITIONS: dict[PositionState, set[PositionState]] = {
    PositionState.PLANNED: {PositionState.ORDER_PREVIEWED, PositionState.KILLED},
    PositionState.ORDER_PREVIEWED: {PositionState.PAPER_OPEN, PositionState.KILLED},
    PositionState.PAPER_OPEN: {
        PositionState.CAPITAL_RECOVERED,
        PositionState.TRAILING_ACTIVE,
        PositionState.ROLL_REVIEW,
        PositionState.EXIT_PENDING,
        PositionState.KILLED,
    },
    PositionState.LIVE_ASSISTED_OPEN: {
        PositionState.CAPITAL_RECOVERED,
        PositionState.TRAILING_ACTIVE,
        PositionState.ROLL_REVIEW,
        PositionState.EXIT_PENDING,
        PositionState.KILLED,
    },
    PositionState.CAPITAL_RECOVERED: {
        PositionState.TRAILING_ACTIVE,
        PositionState.ROLL_REVIEW,
        PositionState.EXIT_PENDING,
        PositionState.CLOSED,
    },
    PositionState.TRAILING_ACTIVE: {
        PositionState.ROLL_REVIEW,
        PositionState.EXIT_PENDING,
        PositionState.CLOSED,
    },
    PositionState.ROLL_REVIEW: {
        PositionState.PAPER_OPEN,
        PositionState.LIVE_ASSISTED_OPEN,
        PositionState.EXIT_PENDING,
        PositionState.KILLED,
    },
    PositionState.EXIT_PENDING: {PositionState.CLOSED, PositionState.KILLED},
    PositionState.CLOSED: set(),
    PositionState.KILLED: set(),
}


@dataclass(frozen=True)
class TransitionRecord:
    timestamp: datetime
    previous: PositionState
    current: PositionState
    reason: str
    human_actor: str | None


def transition(
    previous: PositionState,
    current: PositionState,
    *,
    reason: str,
    timestamp: datetime,
    human_actor: str | None = None,
) -> TransitionRecord:
    if current not in ALLOWED_TRANSITIONS[previous]:
        raise ValueError(f"transition {previous.value}->{current.value} is not allowed")
    if current is PositionState.LIVE_ASSISTED_OPEN and not human_actor:
        raise ValueError("live-assisted state requires an identified human actor")
    return TransitionRecord(timestamp, previous, current, reason, human_actor)
