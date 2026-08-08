"""Combinatorially symmetric cross-validation estimate of PBO."""

from __future__ import annotations

import itertools
import math
from statistics import fmean


def _midrank(value: float, values: list[float]) -> float:
    lower = sum(candidate < value and not math.isclose(candidate, value) for candidate in values)
    equal = sum(math.isclose(candidate, value) for candidate in values)
    return lower + (equal + 1) / 2.0


def probability_of_backtest_overfitting(
    performance_by_strategy_and_fold: list[list[float]],
) -> float | None:
    if len(performance_by_strategy_and_fold) < 2:
        return None
    folds = {len(values) for values in performance_by_strategy_and_fold}
    if len(folds) != 1:
        raise ValueError("all strategies must contain the same number of folds")
    fold_count = folds.pop()
    if fold_count < 4 or fold_count % 2:
        return None
    logits: list[float] = []
    half = fold_count // 2
    all_folds = set(range(fold_count))
    for training_indices_tuple in itertools.combinations(range(fold_count), half):
        training_indices = set(training_indices_tuple)
        test_indices = sorted(all_folds - training_indices)
        train_means = [
            fmean(values[index] for index in training_indices)
            for values in performance_by_strategy_and_fold
        ]
        maximum_train = max(train_means)
        selected = [
            index
            for index, train_mean in enumerate(train_means)
            if math.isclose(train_mean, maximum_train)
        ]
        test_means = [
            fmean(values[index] for index in test_indices)
            for values in performance_by_strategy_and_fold
        ]
        relative_rank = fmean(
            _midrank(test_means[index], test_means) / (len(test_means) + 1) for index in selected
        )
        logits.append(math.log(relative_rank / (1 - relative_rank)))
    return sum(value <= 0 for value in logits) / len(logits)
