"""Temporal purging and dynamic embargo for overlapping trades/features."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class LabeledObservation:
    observation_id: str
    feature_start: datetime
    entry: datetime
    exit: datetime


def dynamic_embargo_days(
    observations: list[LabeledObservation],
    *,
    feature_lookback_days: int,
) -> int:
    maximum_holding = max(
        ((observation.exit - observation.entry).days for observation in observations),
        default=0,
    )
    return max(maximum_holding, feature_lookback_days)


def purge_overlaps(
    training: list[LabeledObservation],
    test: list[LabeledObservation],
    *,
    embargo_days: int,
) -> tuple[list[LabeledObservation], list[str]]:
    retained: list[LabeledObservation] = []
    purged: list[str] = []
    embargo = timedelta(days=embargo_days)
    for candidate in training:
        overlaps = any(
            candidate.feature_start <= test_item.exit + embargo
            and candidate.exit >= test_item.feature_start - embargo
            for test_item in test
        )
        if overlaps:
            purged.append(candidate.observation_id)
        else:
            retained.append(candidate)
    return retained, purged
