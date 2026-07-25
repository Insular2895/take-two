"""Simple volatility-regime classification using information available at the run date."""

from __future__ import annotations

import math
from statistics import median


def log_returns(closes: list[float]) -> list[float]:
    return [
        math.log(current / previous)
        for previous, current in zip(closes, closes[1:], strict=False)
    ]


def realized_volatility(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance * 252)


def classify_regime(returns: list[float], window: int = 20) -> str:
    if len(returns) < window * 3:
        return "insufficient_data"
    windows = [
        realized_volatility(returns[index - window : index])
        for index in range(window, len(returns) + 1)
    ]
    valid = [value for value in windows if value is not None]
    current = valid[-1]
    center = median(valid)
    if current > center * 1.25:
        return "high_volatility"
    if current < center * 0.75:
        return "low_volatility"
    return "normal_volatility"


def conditional_returns(returns: list[float], regime: str, window: int = 20) -> list[float]:
    if regime == "insufficient_data" or len(returns) < window * 3:
        return returns
    rolling = [
        realized_volatility(returns[index - window : index])
        for index in range(window, len(returns) + 1)
    ]
    valid = [value for value in rolling if value is not None]
    center = median(valid)
    selected: list[float] = []
    for offset, volatility in enumerate(rolling, start=window - 1):
        assert volatility is not None
        matches = (
            regime == "high_volatility"
            and volatility > center * 1.25
            or regime == "low_volatility"
            and volatility < center * 0.75
            or regime == "normal_volatility"
            and center * 0.75 <= volatility <= center * 1.25
        )
        if matches:
            selected.append(returns[offset])
    return selected if len(selected) >= 20 else returns
