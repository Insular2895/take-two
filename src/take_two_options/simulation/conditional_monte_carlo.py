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
from take_two_options.quantitative.contracts import (
    DEFAULT_QUANT_CONVENTIONS,
    Measure,
    ModelEligibility,
)


@dataclass(frozen=True)
class ConditionalPathSet:
    model_id: str
    seed: int
    paths: list[list[float]]
    calibration_observations: int
    assumptions: tuple[str, ...]
    measure: Measure = Measure.REAL_WORLD
    eligibility: ModelEligibility = ModelEligibility.UNVALIDATED


def _next_empirical_gbm_spot(
    current_spot: float,
    *,
    mean_log_return: float,
    daily_log_return_volatility: float,
    gaussian_draw: float,
) -> float:
    """Advance an empirical log-return model without a second variance correction."""

    return current_spot * math.exp(
        mean_log_return + daily_log_return_volatility * gaussian_draw
    )


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
    daily_log_return_volatility = DEFAULT_QUANT_CONVENTIONS.deannualize_volatility(
        volatility
    )
    mean_log_return = fmean(returns)

    gbm_rng = random.Random(seed)
    gbm_paths: list[list[float]] = []
    for _ in range(paths):
        values = [spot]
        for _day in range(horizon_days):
            values.append(
                _next_empirical_gbm_spot(
                    values[-1],
                    mean_log_return=mean_log_return,
                    daily_log_return_volatility=daily_log_return_volatility,
                    gaussian_draw=gbm_rng.gauss(0.0, 1.0),
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
                "Empirical mean log return and volatility estimated before the run cutoff",
                "Constant daily volatility within each path",
                "UNVALIDATED PRE-OPRA forecast model; not decision eligible",
            ),
            eligibility=ModelEligibility.UNVALIDATED,
        ),
        ConditionalPathSet(
            model_id="conditional_historical_bootstrap",
            seed=seed + 10_000,
            paths=bootstrap_paths,
            calibration_observations=len(conditioned),
            assumptions=(
                f"Returns sampled from the {regime} regime when enough observations exist",
                "IID resampling does not preserve historical temporal dependence",
                "DIAGNOSTIC_ONLY until real-data validation exists",
            ),
            eligibility=ModelEligibility.DIAGNOSTIC_ONLY,
        ),
    ]
