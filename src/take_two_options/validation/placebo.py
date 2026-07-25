"""Placebo diagnostics that refuse to fabricate unavailable signal histories."""

from __future__ import annotations

import random
from statistics import fmean


def placebo_diagnostics(
    strategy_returns: list[float],
    *,
    seed: int,
) -> tuple[dict[str, float], bool | None]:
    if len(strategy_returns) < 8:
        return {"available_observations": float(len(strategy_returns))}, None
    rng = random.Random(seed)
    randomized = list(strategy_returns)
    rng.shuffle(randomized)
    delayed_one = strategy_returns[1:]
    delayed_two = strategy_returns[2:]
    results = {
        "strategy_mean": fmean(strategy_returns),
        "randomized_mean": fmean(randomized),
        "delay_1_mean": fmean(delayed_one),
        "delay_2_mean": fmean(delayed_two),
    }
    return results, results["strategy_mean"] > max(
        results["randomized_mean"],
        results["delay_1_mean"],
        results["delay_2_mean"],
    )
