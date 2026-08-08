"""Permutation placebo diagnostics on signal/return alignment."""

from __future__ import annotations

import random
from statistics import fmean


def placebo_diagnostics(
    strategy_returns: list[float],
    *,
    seed: int,
    signals: list[float] | None = None,
    permutations: int = 999,
    significance: float = 0.05,
) -> tuple[dict[str, float], bool | None]:
    if len(strategy_returns) < 8:
        return {"available_observations": float(len(strategy_returns))}, None
    if signals is None:
        return {"available_observations": float(len(strategy_returns))}, None
    if len(signals) != len(strategy_returns):
        raise ValueError("placebo signals and returns must have identical lengths")
    if permutations < 99:
        raise ValueError("placebo requires at least 99 permutations")
    if not 0 < significance < 1:
        raise ValueError("placebo significance must lie strictly between zero and one")

    def aligned_mean(selected_signals: list[float], returns: list[float]) -> float:
        return fmean(
            signal * realized_return
            for signal, realized_return in zip(selected_signals, returns, strict=True)
        )

    rng = random.Random(seed)
    observed = aligned_mean(signals, strategy_returns)
    null_statistics: list[float] = []
    for _ in range(permutations):
        randomized_signals = list(signals)
        rng.shuffle(randomized_signals)
        null_statistics.append(aligned_mean(randomized_signals, strategy_returns))
    p_value = (1 + sum(value >= observed for value in null_statistics)) / (permutations + 1)
    delayed_one = aligned_mean(signals[:-1], strategy_returns[1:])
    delayed_two = aligned_mean(signals[:-2], strategy_returns[2:])
    results = {
        "available_observations": float(len(strategy_returns)),
        "observed_signal_return_mean": observed,
        "permutation_null_mean": fmean(null_statistics),
        "permutation_p_value": p_value,
        "delay_1_signal_return_mean": delayed_one,
        "delay_2_signal_return_mean": delayed_two,
        "permutations": float(permutations),
    }
    return results, p_value <= significance and observed > max(
        delayed_one,
        delayed_two,
    )
