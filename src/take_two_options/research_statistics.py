"""Deterministic descriptive statistics for bounded options research panels."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import exp, isfinite, sqrt
from random import Random
from statistics import NormalDist, fmean, stdev


def sample_volatility(values: Sequence[float]) -> float:
    return stdev(values) if len(values) >= 2 else 0.0


def downside_deviation(values: Sequence[float], target: float = 0.0) -> float:
    shortfalls = [min(value - target, 0.0) for value in values]
    if not shortfalls:
        return 0.0
    return sqrt(sum(value * value for value in shortfalls) / len(shortfalls))


def empirical_quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between zero and one")
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def value_at_risk(values: Sequence[float], confidence: float = 0.95) -> float:
    return max(0.0, -empirical_quantile(values, 1 - confidence))


def conditional_value_at_risk(values: Sequence[float], confidence: float = 0.95) -> float:
    cutoff = empirical_quantile(values, 1 - confidence)
    tail = [value for value in values if value <= cutoff]
    return max(0.0, -fmean(tail or [cutoff]))


def profit_factor(values: Sequence[float]) -> float | None:
    gains = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses == 0:
        return None if gains == 0 else float("inf")
    return gains / losses


def payoff_ratio(values: Sequence[float]) -> float | None:
    wins = [value for value in values if value > 0]
    losses = [-value for value in values if value < 0]
    if not wins or not losses:
        return None
    return fmean(wins) / fmean(losses)


def wilson_interval(
    successes: int, observations: int, confidence: float = 0.95
) -> tuple[float, float]:
    if observations <= 0:
        raise ValueError("Wilson interval requires observations")
    if not 0 <= successes <= observations:
        raise ValueError("successes must be within observations")
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    proportion = successes / observations
    denominator = 1 + z * z / observations
    center = (proportion + z * z / (2 * observations)) / denominator
    margin = (
        z
        * sqrt(
            proportion * (1 - proportion) / observations
            + z * z / (4 * observations * observations)
        )
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def bootstrap_interval(
    values: Sequence[float],
    statistic: Callable[[Sequence[float]], float],
    *,
    confidence: float = 0.95,
    samples: int = 2_000,
    seed: int = 17,
) -> tuple[float, float]:
    if not values:
        raise ValueError("bootstrap requires at least one value")
    if samples < 100:
        raise ValueError("bootstrap requires at least 100 samples")
    rng = Random(seed)
    count = len(values)
    estimates = sorted(
        statistic([values[rng.randrange(count)] for _ in range(count)])
        for _ in range(samples)
    )
    alpha = (1 - confidence) / 2
    return (
        empirical_quantile(estimates, alpha),
        empirical_quantile(estimates, 1 - alpha),
    )


def skewness(values: Sequence[float]) -> float:
    if len(values) < 3:
        return 0.0
    mean = fmean(values)
    scale = sample_volatility(values)
    if scale == 0:
        return 0.0
    n = len(values)
    return n / ((n - 1) * (n - 2)) * sum(((value - mean) / scale) ** 3 for value in values)


def kurtosis(values: Sequence[float]) -> float:
    if len(values) < 4:
        return 3.0
    mean = fmean(values)
    scale = sample_volatility(values)
    if scale == 0:
        return 3.0
    n = len(values)
    fourth = sum(((value - mean) / scale) ** 4 for value in values)
    correction = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * fourth
    excess_adjustment = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return correction - excess_adjustment + 3


def deflated_sharpe_probability(values: Sequence[float], trials: int) -> float | None:
    """Approximate DSR probability using the Bailey/Lopez de Prado benchmark Sharpe.

    Returns are kept at their observed holding-period scale. This is a multiple-testing
    diagnostic, not an annualized performance claim.
    """

    if len(values) < 3 or trials < 1:
        return None
    volatility = sample_volatility(values)
    if volatility == 0:
        return 0.5 if fmean(values) == 0 else float(fmean(values) > 0)
    sharpe = fmean(values) / volatility
    variance = (1 - skewness(values) * sharpe + ((kurtosis(values) - 1) / 4) * sharpe**2) / (
        len(values) - 1
    )
    if variance <= 0 or not isfinite(variance):
        return None
    if trials == 1:
        benchmark = 0.0
    else:
        euler_gamma = 0.5772156649015329
        normal = NormalDist()
        expected_max = (
            (1 - euler_gamma) * normal.inv_cdf(1 - 1 / trials)
            + euler_gamma * normal.inv_cdf(1 - 1 / (trials * exp(1)))
        )
        benchmark = sqrt(variance) * expected_max
    z_score = (sharpe - benchmark) / sqrt(variance)
    return NormalDist().cdf(z_score)
