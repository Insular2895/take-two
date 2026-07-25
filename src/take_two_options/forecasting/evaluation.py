"""Forecast readiness gates independent from option-candidate performance."""

from __future__ import annotations

from take_two_options.forecasting.contracts import PriceDistributionForecast


def forecast_readiness(forecast: PriceDistributionForecast) -> tuple[bool, list[str]]:
    reasons = [
        f"{model.model_id}: {model.calibration_status}"
        for model in forecast.models
        if model.calibration_status != "calibrated"
    ]
    return not reasons, reasons
