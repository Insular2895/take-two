"""Forecasting data contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from take_two_options.domain import StrictModel


class HistoricalReturnSeries(StrictModel):
    ticker: str
    as_of: datetime
    timestamps: list[datetime] = Field(min_length=2)
    closes: list[float] = Field(min_length=2)
    source_id: str


class ForecastModelSummary(StrictModel):
    model_id: str
    calibration_status: str
    observations: int = Field(ge=0)
    annualized_volatility: float | None = Field(default=None, gt=0)
    warnings: list[str] = Field(default_factory=list)


class PriceDistributionForecast(StrictModel):
    ticker: str
    as_of: datetime
    horizon_days: int = Field(gt=0)
    regime: str
    models: list[ForecastModelSummary] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
