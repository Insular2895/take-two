"""Combinatorially symmetric cross-validation estimate of PBO."""

from __future__ import annotations

import itertools
import math
from statistics import fmean


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
        selected = max(range(len(train_means)), key=train_means.__getitem__)
        test_means = [
            fmean(values[index] for index in test_indices)
            for values in performance_by_strategy_and_fold
        ]
        ordered = sorted(test_means)
        rank = ordered.index(test_means[selected]) + 1
        relative_rank = rank / (len(ordered) + 1)
        logits.append(math.log(relative_rank / (1 - relative_rank)))
    return sum(value <= 0 for value in logits) / len(logits)
