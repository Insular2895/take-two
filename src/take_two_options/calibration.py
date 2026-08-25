"""Conservative calibration from timestamped historical closes."""

from __future__ import annotations

import math
from datetime import datetime
from statistics import fmean, stdev
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import (
    CalibrationStatus,
    EvidenceReference,
    ModelReadiness,
    SimulationModel,
    StrictModel,
)
from take_two_options.quantitative.contracts import DEFAULT_QUANT_CONVENTIONS


class HistoricalPricePoint(StrictModel):
    timestamp: datetime
    data_available_at: datetime
    close: float = Field(gt=0)


class CalibrationDataset(StrictModel):
    ticker: str = Field(min_length=1)
    as_of: datetime
    training_cutoff: datetime
    evidence_class: Literal["illustrative_calibration", "source_backed_calibration"]
    source: EvidenceReference
    points: list[HistoricalPricePoint] = Field(min_length=8)
    jump_threshold_sigma: float = Field(default=2.5, gt=1)

    @model_validator(mode="after")
    def validate_history(self) -> CalibrationDataset:
        timestamps = [point.timestamp for point in self.points]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("historical price timestamps must be unique")
        if self.training_cutoff > self.as_of:
            raise ValueError("training cutoff cannot follow dataset as-of")
        if (
            self.evidence_class == "source_backed_calibration"
            and not self.source.status.can_authorize_research
        ):
            raise ValueError("source-backed calibration requires authorizing evidence")
        return self


class ModelCalibrationResult(StrictModel):
    model: SimulationModel
    status: CalibrationStatus
    observations: int = Field(ge=0)
    parameters: dict[str, float] = Field(default_factory=dict)
    diagnostics: list[str] = Field(default_factory=list)


class CalibrationReport(StrictModel):
    ticker: str
    created_at: datetime
    training_cutoff: datetime
    evidence_class: Literal["illustrative_calibration", "source_backed_calibration"]
    model_readiness: ModelReadiness
    results: list[ModelCalibrationResult]
    excluded_points: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


def _annualized_volatility(returns: list[float]) -> float:
    return DEFAULT_QUANT_CONVENTIONS.annualize_volatility(stdev(returns))


def calibrate_dataset(dataset: CalibrationDataset) -> CalibrationReport:
    eligible = sorted(
        (
            point
            for point in dataset.points
            if point.timestamp <= dataset.training_cutoff
            and point.data_available_at <= dataset.training_cutoff
        ),
        key=lambda point: point.timestamp,
    )
    excluded = len(dataset.points) - len(eligible)
    if len(eligible) < 8:
        raise ValueError("at least eight look-ahead-safe training prices are required")
    returns = [
        math.log(current.close / previous.close)
        for previous, current in zip(eligible, eligible[1:], strict=False)
    ]
    if len(returns) < 2 or stdev(returns) == 0:
        raise ValueError("training returns need non-zero dispersion")

    annualized = _annualized_volatility(returns)
    evidence_status = (
        CalibrationStatus.CALIBRATED
        if dataset.evidence_class == "source_backed_calibration"
        else CalibrationStatus.ILLUSTRATIVE
    )
    mean_return = fmean(returns)
    daily_sigma = stdev(returns)
    classified_returns = [
        (
            value,
            abs(value - mean_return) > dataset.jump_threshold_sigma * daily_sigma,
        )
        for value in returns
    ]
    jump_returns = [value for value, is_jump in classified_returns if is_jump]
    diffusion_returns = [value for value, is_jump in classified_returns if not is_jump]

    gbm = ModelCalibrationResult(
        model=SimulationModel.GBM,
        status=evidence_status,
        observations=len(returns),
        parameters={"annualized_volatility": annualized},
        diagnostics=["Close-to-close log returns; 252 trading-day annualization"],
    )
    if len(jump_returns) >= 2 and len(diffusion_returns) >= 2:
        jump = ModelCalibrationResult(
            model=SimulationModel.MERTON_JUMP_DIFFUSION,
            status=evidence_status,
            observations=len(returns),
            parameters={
                "jump_intensity": len(jump_returns)
                / len(returns)
                * DEFAULT_QUANT_CONVENTIONS.trading_session_basis,
                "jump_mean": fmean(jump_returns),
                "jump_volatility": stdev(jump_returns),
                "diffusion_volatility": _annualized_volatility(diffusion_returns),
            },
            diagnostics=[
                f"Heuristic jump classification at {dataset.jump_threshold_sigma:g} sigma",
                "Threshold calibration is screen-grade and sensitive to sample length",
            ],
        )
    else:
        jump = ModelCalibrationResult(
            model=SimulationModel.MERTON_JUMP_DIFFUSION,
            status=CalibrationStatus.INSUFFICIENT_DATA,
            observations=len(returns),
            diagnostics=["At least two jump observations and two diffusion returns are required"],
        )
    heston = ModelCalibrationResult(
        model=SimulationModel.HESTON_FULL_TRUNCATION,
        status=CalibrationStatus.INSUFFICIENT_DATA,
        observations=len(returns),
        diagnostics=[
            "Close history alone does not identify a robust Heston parameter set",
            "Timestamped option-surface history or another variance proxy is required",
        ],
    )
    readiness = (
        ModelReadiness.VALIDATION_PENDING
        if dataset.evidence_class == "source_backed_calibration"
        else ModelReadiness.SCREEN_GRADE
    )
    warnings = [
        "Calibration is not an out-of-sample validation",
        "Heston parameters were deliberately not inferred from insufficient evidence",
    ]
    if excluded:
        warnings.append(f"{excluded} point(s) excluded by timestamp/look-ahead controls")
    return CalibrationReport(
        ticker=dataset.ticker,
        created_at=dataset.as_of,
        training_cutoff=dataset.training_cutoff,
        evidence_class=dataset.evidence_class,
        model_readiness=readiness,
        results=[gbm, jump, heston],
        excluded_points=excluded,
        warnings=warnings,
    )


def render_calibration_markdown(report: CalibrationReport) -> str:
    lines = [
        "# TTWO model calibration report",
        "",
        f"- Evidence class: `{report.evidence_class}`",
        f"- Training cutoff: `{report.training_cutoff.isoformat()}`",
        f"- Model readiness: `{report.model_readiness.value}`",
        "- Order capability: `forbidden`",
        "",
        "## Models",
        "",
    ]
    for result in report.results:
        parameters = (
            ", ".join(f"{name}={value:.6g}" for name, value in result.parameters.items()) or "none"
        )
        lines.append(
            f"- `{result.model.value}`: `{result.status.value}`; "
            f"observations={result.observations}; {parameters}"
        )
        lines.extend(f"  - {diagnostic}" for diagnostic in result.diagnostics)
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    lines.append("")
    return "\n".join(lines)
