"""Build model readiness metadata from pre-cutoff historical closes."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from take_two_options.forecasting.contracts import (
    ForecastModelSummary,
    HistoricalReturnSeries,
    PriceDistributionForecast,
)
from take_two_options.forecasting.regimes import (
    classify_regime,
    log_returns,
    realized_volatility,
)


class ForecastDataError(ValueError):
    """Raised when source-backed historical data is unavailable."""


def load_historical_series(
    path: Path,
    *,
    ticker: str,
    cutoff: datetime,
) -> HistoricalReturnSeries:
    payload = json.loads(path.read_text(encoding="utf-8"))
    points = [
        point
        for point in payload.get("points", [])
        if datetime.fromisoformat(point["timestamp"].replace("Z", "+00:00")) <= cutoff
    ]
    if len(points) < 2:
        raise ForecastDataError("historical series has fewer than two pre-cutoff observations")
    return HistoricalReturnSeries(
        ticker=ticker,
        as_of=cutoff,
        timestamps=[
            datetime.fromisoformat(point["timestamp"].replace("Z", "+00:00"))
            for point in points
        ],
        closes=[float(point["close"]) for point in points],
        source_id=payload["source"]["id"],
    )


def build_price_distribution(
    series: HistoricalReturnSeries,
    *,
    horizon_days: int,
) -> PriceDistributionForecast:
    returns = log_returns(series.closes)
    volatility = realized_volatility(returns)
    regime = classify_regime(returns)
    observations = len(returns)
    status = "calibrated" if observations >= 252 else "insufficient_data"
    warnings = [] if status == "calibrated" else ["fewer than 252 daily returns"]
    return PriceDistributionForecast(
        ticker=series.ticker,
        as_of=series.as_of,
        horizon_days=horizon_days,
        regime=regime,
        models=[
            ForecastModelSummary(
                model_id="gbm_historical",
                calibration_status=status,
                observations=observations,
                annualized_volatility=volatility,
                warnings=warnings,
            ),
            ForecastModelSummary(
                model_id="conditional_historical_bootstrap",
                calibration_status=(
                    "calibrated" if regime != "insufficient_data" else "insufficient_data"
                ),
                observations=observations,
                annualized_volatility=volatility,
                warnings=warnings,
            ),
        ],
        source_ids=[series.source_id],
        assumptions=[
            "Models are evaluated separately; no fixed ensemble weights are imposed",
            "Only observations available by the run cutoff are used",
        ],
        limitations=[
            "Historical returns do not encode a causal GTA VI fundamental forecast",
            "A distribution forecast does not validate an option strategy",
        ],
    )
