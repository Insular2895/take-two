"""Calibration curves and proper scoring diagnostics for binary forecasts."""

from __future__ import annotations

import math
from statistics import fmean
from typing import Literal

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.research_statistics import wilson_interval


class CalibrationBin(StrictModel):
    lower_bound: float = Field(ge=0, le=1)
    upper_bound: float = Field(ge=0, le=1)
    observations: int = Field(gt=0)
    mean_prediction: float = Field(ge=0, le=1)
    observed_frequency: float = Field(ge=0, le=1)
    frequency_interval_low: float = Field(ge=0, le=1)
    frequency_interval_high: float = Field(ge=0, le=1)


class ProbabilityCalibrationReport(StrictModel):
    observations: int = Field(gt=0)
    dataset_role: Literal["development", "validation", "final_holdout"]
    dataset_hash: str | None = None
    status: Literal["insufficient_data", "diagnostic_ready"]
    minimum_observations: int = Field(gt=0)
    brier_score: float = Field(ge=0, le=1)
    log_loss: float = Field(ge=0)
    expected_calibration_error: float = Field(ge=0, le=1)
    bins: tuple[CalibrationBin, ...]
    assumptions: tuple[str, ...]


def evaluate_binary_calibration(
    probabilities: list[float],
    outcomes: list[bool],
    *,
    bins: int = 10,
    minimum_observations: int = 100,
    dataset_role: Literal["development", "validation", "final_holdout"] = "development",
    dataset_hash: str | None = None,
) -> ProbabilityCalibrationReport:
    if not probabilities or len(probabilities) != len(outcomes):
        raise ValueError("calibration requires non-empty aligned predictions and outcomes")
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in probabilities):
        raise ValueError("probabilities must be finite and bounded")
    if bins < 2:
        raise ValueError("calibration requires at least two bins")
    if minimum_observations <= 0:
        raise ValueError("minimum_observations must be positive")
    if dataset_role == "final_holdout" and not dataset_hash:
        raise ValueError("final-holdout calibration requires a dataset hash")

    count = len(probabilities)
    epsilon = 1e-12
    brier = fmean(
        (probability - outcome) ** 2
        for probability, outcome in zip(probabilities, outcomes, strict=True)
    )
    log_loss = -fmean(
        outcome * math.log(max(probability, epsilon))
        + (1 - outcome) * math.log(max(1 - probability, epsilon))
        for probability, outcome in zip(probabilities, outcomes, strict=True)
    )
    calibration_bins: list[CalibrationBin] = []
    ece = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            position
            for position, probability in enumerate(probabilities)
            if lower <= probability < upper or (index == bins - 1 and probability == 1)
        ]
        if not members:
            continue
        successes = sum(outcomes[position] for position in members)
        observed = successes / len(members)
        predicted = fmean(probabilities[position] for position in members)
        interval_low, interval_high = wilson_interval(successes, len(members))
        ece += len(members) / count * abs(predicted - observed)
        calibration_bins.append(
            CalibrationBin(
                lower_bound=lower,
                upper_bound=upper,
                observations=len(members),
                mean_prediction=predicted,
                observed_frequency=observed,
                frequency_interval_low=interval_low,
                frequency_interval_high=interval_high,
            )
        )
    return ProbabilityCalibrationReport(
        observations=count,
        dataset_role=dataset_role,
        dataset_hash=dataset_hash,
        status=("diagnostic_ready" if count >= minimum_observations else "insufficient_data"),
        minimum_observations=minimum_observations,
        brier_score=brier,
        log_loss=log_loss,
        expected_calibration_error=ece,
        bins=tuple(calibration_bins),
        assumptions=(
            "Binary outcomes are aligned point-in-time with their forecasts.",
            "Calibration-bin Wilson intervals assume iid outcomes within each bin.",
            "A diagnostic-ready curve is not itself holdout or production validation.",
        ),
    )
