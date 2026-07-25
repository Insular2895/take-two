"""Nested chronological windows with purging between parameter search and outer test."""

from __future__ import annotations

from dataclasses import dataclass

from take_two_options.validation.purging import LabeledObservation, purge_overlaps


@dataclass(frozen=True)
class WalkForwardWindow:
    window_id: str
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    purged_ids: tuple[str, ...]


def nested_purged_walk_forward(
    observations: list[LabeledObservation],
    *,
    minimum_train: int,
    minimum_validation: int,
    minimum_test: int,
    embargo_days: int,
) -> list[WalkForwardWindow]:
    ordered = sorted(observations, key=lambda item: item.entry)
    block = minimum_validation + minimum_test
    windows: list[WalkForwardWindow] = []
    outer_start = minimum_train
    index = 1
    while outer_start + block <= len(ordered):
        raw_train = ordered[:outer_start]
        validation = ordered[outer_start : outer_start + minimum_validation]
        test = ordered[
            outer_start + minimum_validation : outer_start + minimum_validation + minimum_test
        ]
        purged_train, purged_ids = purge_overlaps(
            raw_train, [*validation, *test], embargo_days=embargo_days
        )
        if len(purged_train) >= minimum_train:
            windows.append(
                WalkForwardWindow(
                    window_id=f"wf-{index:03d}",
                    train_ids=tuple(item.observation_id for item in purged_train),
                    validation_ids=tuple(item.observation_id for item in validation),
                    test_ids=tuple(item.observation_id for item in test),
                    purged_ids=tuple(purged_ids),
                )
            )
            index += 1
        outer_start += minimum_test
    return windows
