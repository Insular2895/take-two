"""Point-in-time historical volatility-surface validation."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from statistics import fmean
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.quantitative.calibration import (
    HestonCalibrationGate,
    evaluate_heston_calibration_gate,
)
from take_two_options.quantitative.svi import (
    CalendarArbitrageReport,
    SVIFitReport,
    SVIFitStatus,
    SVIObservation,
    calendar_arbitrage_report,
    fit_svi_slice,
)


class QuoteUse(StrEnum):
    OBSERVED = "observed"
    INTERPOLATED = "interpolated"
    EXTRAPOLATED = "extrapolated"


class HistoricalSurfaceQuote(StrictModel):
    snapshot_id: str
    expiration_id: str
    maturity_years: float = Field(gt=0)
    log_forward_moneyness: float
    implied_volatility: float = Field(gt=0, le=5)
    weight: float = Field(default=1, gt=0)
    available_at: datetime
    decision_cutoff: datetime
    use: QuoteUse = QuoteUse.OBSERVED
    source_id: str


class SurfaceSliceDiagnostic(StrictModel):
    snapshot_id: str
    expiration_id: str
    maturity_years: float = Field(gt=0)
    fit: SVIFitReport


class SurfaceSnapshotDiagnostic(StrictModel):
    snapshot_id: str
    slices: list[SurfaceSliceDiagnostic]
    calendar_arbitrage: CalendarArbitrageReport | None
    post_cutoff_quotes_excluded: int = Field(ge=0)
    interpolated_quotes: int = Field(ge=0)
    extrapolated_quotes: int = Field(ge=0)
    status: Literal["FITTED", "BLOCKED_INSUFFICIENT_DATA", "ARBITRAGE_VIOLATION"]


class SurfaceStability(StrictModel):
    fitted_snapshots: int = Field(ge=0)
    parameter_transitions: int = Field(ge=0)
    mean_absolute_parameter_change: float | None = Field(default=None, ge=0)


class HistoricalSurfaceReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    dataset_hash: str | None = Field(default=None, min_length=64, max_length=64)
    status: Literal[
        "VALIDATED_DEVELOPMENT_ONLY",
        "FIXTURE_ONLY_NOT_VALIDATED",
        "BLOCKED_MISSING_GOVERNED_INPUTS",
    ]
    snapshots: list[SurfaceSnapshotDiagnostic]
    stability: SurfaceStability
    heston_gate: HestonCalibrationGate
    interpolation_policy: str
    extrapolation_policy: str
    missing_inputs: list[str]
    blockers: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def prevent_unsubstantiated_validation(self) -> HistoricalSurfaceReport:
        if self.status == "VALIDATED_DEVELOPMENT_ONLY" and (self.blockers or not self.snapshots):
            raise ValueError("validated surface history requires snapshots and no blockers")
        return self


def _snapshot(snapshot_id: str, quotes: list[HistoricalSurfaceQuote]) -> SurfaceSnapshotDiagnostic:
    eligible = [quote for quote in quotes if quote.available_at <= quote.decision_cutoff]
    grouped: dict[str, list[HistoricalSurfaceQuote]] = {}
    for quote in eligible:
        grouped.setdefault(quote.expiration_id, []).append(quote)
    slices: list[SurfaceSliceDiagnostic] = []
    for expiration_id, values in sorted(grouped.items()):
        maturity = values[0].maturity_years
        if any(not math.isclose(value.maturity_years, maturity) for value in values):
            raise ValueError("one expiration cannot have multiple maturities")
        fit = fit_svi_slice(
            [
                SVIObservation(
                    log_forward_moneyness=value.log_forward_moneyness,
                    total_variance=value.implied_volatility**2 * maturity,
                    weight=value.weight,
                )
                for value in values
            ]
        )
        slices.append(
            SurfaceSliceDiagnostic(
                snapshot_id=snapshot_id,
                expiration_id=expiration_id,
                maturity_years=maturity,
                fit=fit,
            )
        )
    fitted = [item for item in slices if item.fit.parameters is not None]
    calendar = (
        calendar_arbitrage_report(
            [(item.maturity_years, item.fit.parameters) for item in fitted if item.fit.parameters]
        )
        if len(fitted) >= 2
        else None
    )
    failed = any(item.fit.status is not SVIFitStatus.FITTED for item in slices)
    violation = calendar is not None and not calendar.calendar_arbitrage_free
    status = (
        "BLOCKED_INSUFFICIENT_DATA"
        if not slices or failed
        else "ARBITRAGE_VIOLATION"
        if violation
        else "FITTED"
    )
    return SurfaceSnapshotDiagnostic(
        snapshot_id=snapshot_id,
        slices=slices,
        calendar_arbitrage=calendar,
        post_cutoff_quotes_excluded=len(quotes) - len(eligible),
        interpolated_quotes=sum(quote.use is QuoteUse.INTERPOLATED for quote in eligible),
        extrapolated_quotes=sum(quote.use is QuoteUse.EXTRAPOLATED for quote in eligible),
        status=status,
    )


def validate_surface_history(
    quotes: list[HistoricalSurfaceQuote],
    *,
    ticker: str,
    dataset_hash: str,
    synthetic: bool,
    license_authorized: bool,
) -> HistoricalSurfaceReport:
    grouped: dict[str, list[HistoricalSurfaceQuote]] = {}
    for quote in quotes:
        grouped.setdefault(quote.snapshot_id, []).append(quote)
    snapshots = [_snapshot(key, values) for key, values in sorted(grouped.items())]
    parameters = [
        item.fit.parameters
        for snapshot in snapshots
        for item in snapshot.slices
        if item.fit.parameters is not None
    ]
    parameter_rows = [[p.a, p.b, p.rho, p.m, p.sigma] for p in parameters]
    changes = [
        fmean(abs(a - b) for a, b in zip(left, right, strict=True))
        for left, right in zip(parameter_rows[:-1], parameter_rows[1:], strict=True)
    ]
    expiration_counts = [len(snapshot.slices) for snapshot in snapshots]
    strike_counts = [item.fit.observations for snapshot in snapshots for item in snapshot.slices]
    all_fitted = bool(snapshots) and all(snapshot.status == "FITTED" for snapshot in snapshots)
    point_in_time = all(snapshot.post_cutoff_quotes_excluded == 0 for snapshot in snapshots)
    heston_gate = evaluate_heston_calibration_gate(
        surface_dates=len(snapshots),
        expirations_per_date=min(expiration_counts, default=0),
        strikes_per_expiration=min(strike_counts, default=0),
        point_in_time_quotes=point_in_time,
        constrained_multistart_available=False,
    )
    blockers: list[str] = []
    if not all_fitted:
        blockers.append("Every development surface must pass SVI and static-arbitrage checks.")
    if not license_authorized:
        blockers.append("Historical option-data licensing remains to_review.")
    status = (
        "FIXTURE_ONLY_NOT_VALIDATED"
        if synthetic
        else "VALIDATED_DEVELOPMENT_ONLY"
        if not blockers
        else "BLOCKED_MISSING_GOVERNED_INPUTS"
    )
    if synthetic:
        blockers.append("Synthetic surfaces validate mechanics only.")
    return HistoricalSurfaceReport(
        schema_version="1.0",
        report_id=f"{ticker.casefold()}-historical-surfaces-v1",
        ticker=ticker,
        dataset_hash=dataset_hash,
        status=status,
        snapshots=snapshots,
        stability=SurfaceStability(
            fitted_snapshots=sum(snapshot.status == "FITTED" for snapshot in snapshots),
            parameter_transitions=len(changes),
            mean_absolute_parameter_change=fmean(changes) if changes else None,
        ),
        heston_gate=heston_gate,
        interpolation_policy="flag every interpolated quote; never conceal it as observed",
        extrapolation_policy="diagnostic only; never decision-eligible",
        missing_inputs=[],
        blockers=blockers,
        holdout_used=False,
    )
