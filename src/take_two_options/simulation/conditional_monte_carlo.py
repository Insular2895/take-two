"""Conditioned, seeded underlying paths with models kept separate."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import fmean

from take_two_options.forecasting.contracts import HistoricalReturnSeries
from take_two_options.forecasting.regimes import (
    classify_regime,
    conditional_returns,
    log_returns,
    realized_volatility,
)


@dataclass(frozen=True)
class ConditionalPathSet:
    model_id: str
    seed: int
    paths: list[list[float]]
    calibration_observations: int
    assumptions: tuple[str, ...]


def simulate_conditional_paths(
    series: HistoricalReturnSeries,
    *,
    spot: float,
    horizon_days: int,
    paths: int,
    seed: int,
) -> list[ConditionalPathSet]:
    returns = log_returns(series.closes)
    if len(returns) < 20:
        raise ValueError("conditional simulation requires at least 20 returns")
    regime = classify_regime(returns)
    conditioned = conditional_returns(returns, regime)
    volatility = realized_volatility(returns)
    assert volatility is not None
    daily_volatility = volatility / math.sqrt(252)
    daily_mean = fmean(returns)

    gbm_rng = random.Random(seed)
    gbm_paths: list[list[float]] = []
    for _ in range(paths):
        values = [spot]
        for _day in range(horizon_days):
            values.append(
                values[-1]
                * math.exp(
                    daily_mean
                    - 0.5 * daily_volatility * daily_volatility
                    + daily_volatility * gbm_rng.gauss(0.0, 1.0)
                )
            )
        gbm_paths.append(values)

    bootstrap_rng = random.Random(seed + 10_000)
    bootstrap_paths: list[list[float]] = []
    for _ in range(paths):
        values = [spot]
        for _day in range(horizon_days):
            daily_return = conditioned[bootstrap_rng.randrange(len(conditioned))]
            values.append(values[-1] * math.exp(daily_return))
        bootstrap_paths.append(values)
    return [
        ConditionalPathSet(
            model_id="gbm_historical",
            seed=seed,
            paths=gbm_paths,
            calibration_observations=len(returns),
            assumptions=(
                "Historical drift and volatility estimated before the run cutoff",
                "Constant daily volatility within each path",
            ),
        ),
        ConditionalPathSet(
            model_id="conditional_historical_bootstrap",
            seed=seed + 10_000,
            paths=bootstrap_paths,
            calibration_observations=len(conditioned),
            assumptions=(
                f"Returns sampled from the {regime} regime when enough observations exist",
                "Historical daily-return ordering is not preserved",
            ),
        ),
    ]
