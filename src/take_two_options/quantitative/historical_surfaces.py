"""Point-in-time historical volatility-surface validation."""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from statistics import fmean
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.historical_data.market_context import MarketContextDataset
from take_two_options.historical_data.option_observations import HistoricalOptionObservation
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


class SurfaceConstructionAudit(StrictModel):
    input_observations: int = Field(ge=0)
    calls_considered: int = Field(ge=0)
    usable_quotes_before_iv: int = Field(ge=0)
    iv_inversions_succeeded: int = Field(ge=0)
    iv_inversions_failed: int = Field(ge=0)
    quotes_used_in_fitted_slices: int = Field(ge=0)
    eligible_slices: int = Field(ge=0)
    eligible_snapshots: int = Field(ge=0)
    heston_shape_eligible_snapshots: int = Field(ge=0)
    exclusion_counts: dict[str, int]
    option_style: Literal["american_call_equal_to_european_under_verified_zero_dividend"]
    forward_convention: str
    rate_convention: str
    quote_weighting: str


class HistoricalSurfaceReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    dataset_hash: str | None = Field(default=None, min_length=64, max_length=64)
    status: Literal[
        "VALIDATED_DEVELOPMENT_ONLY",
        "DEVELOPMENT_DIAGNOSTIC_LIMITED",
        "FIXTURE_ONLY_NOT_VALIDATED",
        "BLOCKED_MISSING_GOVERNED_INPUTS",
    ]
    snapshots: list[SurfaceSnapshotDiagnostic]
    stability: SurfaceStability
    construction: SurfaceConstructionAudit | None = None
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
        else "DEVELOPMENT_DIAGNOSTIC_LIMITED"
        if snapshots
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
        construction=None,
        heston_gate=heston_gate,
        interpolation_policy="flag every interpolated quote; never conceal it as observed",
        extrapolation_policy="diagnostic only; never decision-eligible",
        missing_inputs=[],
        blockers=blockers,
        holdout_used=False,
    )


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _bsm_call(spot: float, strike: float, maturity: float, rate: float, sigma: float) -> float:
    root_time = math.sqrt(maturity)
    d1 = (
        math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * maturity
    ) / (sigma * root_time)
    d2 = d1 - sigma * root_time
    return spot * _normal_cdf(d1) - strike * math.exp(-rate * maturity) * _normal_cdf(d2)


def _call_implied_volatility(
    *, spot: float, strike: float, maturity: float, rate: float, price: float
) -> float | None:
    lower_bound = max(0.0, spot - strike * math.exp(-rate * maturity))
    if maturity <= 0 or price <= lower_bound + 1e-8 or price >= spot:
        return None
    low, high = 0.005, 5.0
    if _bsm_call(spot, strike, maturity, rate, high) < price:
        return None
    for _ in range(80):
        midpoint = (low + high) / 2.0
        if _bsm_call(spot, strike, maturity, rate, midpoint) < price:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def _point_in_time_rate(
    context: MarketContextDataset, *, cutoff: datetime, maturity_days: int
) -> float | None:
    eligible = [curve for curve in context.risk_free_curves if curve.available_at <= cutoff]
    if not eligible:
        return None
    rates = eligible[-1].rates_by_maturity_days
    tenors = sorted(rates)
    if maturity_days <= tenors[0]:
        return rates[tenors[0]]
    if maturity_days >= tenors[-1]:
        return rates[tenors[-1]]
    upper_index = next(index for index, tenor in enumerate(tenors) if tenor >= maturity_days)
    lower_tenor, upper_tenor = tenors[upper_index - 1], tenors[upper_index]
    weight = (maturity_days - lower_tenor) / (upper_tenor - lower_tenor)
    return rates[lower_tenor] * (1.0 - weight) + rates[upper_tenor] * weight


def build_historical_surface_report(
    observations: list[HistoricalOptionObservation],
    context: MarketContextDataset,
    *,
    option_dataset_hash: str,
    context_dataset_hash: str,
    license_authorized: bool,
    minimum_open_interest: float = 20.0,
    maximum_relative_spread: float = 0.30,
    minimum_maturity_days: int = 7,
    maximum_maturity_days: int = 365,
    minimum_moneyness: float = 0.50,
    maximum_moneyness: float = 1.50,
) -> HistoricalSurfaceReport:
    """Invert zero-dividend TTWO calls and fit point-in-time raw-SVI slices."""

    exclusions: Counter[str] = Counter()
    candidates: list[HistoricalSurfaceQuote] = []
    calls_considered = 0
    usable_before_iv = 0
    iv_succeeded = 0
    iv_failed = 0
    for observation in observations:
        if observation.option_type.value != "call":
            exclusions["american_put_excluded"] += 1
            continue
        calls_considered += 1
        if observation.bid is None or observation.ask is None or observation.mid is None:
            exclusions["incomplete_bid_ask"] += 1
            continue
        if observation.mid <= 0:
            exclusions["non_positive_mid"] += 1
            continue
        relative_spread = (observation.ask - observation.bid) / observation.mid
        if relative_spread > maximum_relative_spread:
            exclusions["relative_spread_above_limit"] += 1
            continue
        if (observation.open_interest or 0.0) < minimum_open_interest:
            exclusions["open_interest_below_limit"] += 1
            continue
        if observation.underlying_price is None:
            exclusions["missing_underlying_price"] += 1
            continue
        maturity_days = (observation.expiration - observation.quote_time.date()).days
        if not minimum_maturity_days <= maturity_days <= maximum_maturity_days:
            exclusions["maturity_outside_range"] += 1
            continue
        strike_moneyness = observation.strike / observation.underlying_price
        if not minimum_moneyness <= strike_moneyness <= maximum_moneyness:
            exclusions["strike_moneyness_outside_range"] += 1
            continue
        rate = _point_in_time_rate(
            context, cutoff=observation.available_at, maturity_days=maturity_days
        )
        if rate is None:
            exclusions["point_in_time_rate_unavailable"] += 1
            continue
        usable_before_iv += 1
        maturity_years = maturity_days / 365.0
        implied_volatility = _call_implied_volatility(
            spot=observation.underlying_price,
            strike=observation.strike,
            maturity=maturity_years,
            rate=rate,
            price=observation.mid,
        )
        if implied_volatility is None or not 0.03 <= implied_volatility <= 3.0:
            iv_failed += 1
            exclusions["iv_inversion_or_range_failure"] += 1
            continue
        iv_succeeded += 1
        forward = observation.underlying_price * math.exp(rate * maturity_years)
        candidates.append(
            HistoricalSurfaceQuote(
                snapshot_id=observation.quote_time.date().isoformat(),
                expiration_id=observation.expiration.isoformat(),
                maturity_years=maturity_years,
                log_forward_moneyness=math.log(observation.strike / forward),
                implied_volatility=implied_volatility,
                weight=min(2500.0, 1.0 / max(relative_spread, 0.02) ** 2),
                available_at=observation.available_at,
                decision_cutoff=observation.available_at,
                source_id="marketdata-private-eod-bid-ask-midpoint",
            )
        )

    grouped: dict[tuple[str, str], list[HistoricalSurfaceQuote]] = {}
    for quote in candidates:
        grouped.setdefault((quote.snapshot_id, quote.expiration_id), []).append(quote)
    eligible_keys = {
        key
        for key, values in grouped.items()
        if len({round(value.log_forward_moneyness, 12) for value in values}) >= 5
    }
    exclusions["quotes_in_slices_below_five_distinct_strikes"] += sum(
        len(values) for key, values in grouped.items() if key not in eligible_keys
    )
    surface_quotes = [
        quote
        for key, values in grouped.items()
        if key in eligible_keys
        for quote in values
    ]
    combined_hash = sha256(
        f"{option_dataset_hash}:{context_dataset_hash}:surface-v2".encode()
    ).hexdigest()
    report = validate_surface_history(
        surface_quotes,
        ticker="TTWO",
        dataset_hash=combined_hash,
        synthetic=False,
        license_authorized=license_authorized,
    )
    expiration_counts = [len(snapshot.slices) for snapshot in report.snapshots]
    heston_shape_dates = sum(count >= 4 for count in expiration_counts)
    heston_gate = evaluate_heston_calibration_gate(
        surface_dates=heston_shape_dates,
        expirations_per_date=4 if heston_shape_dates else 0,
        strikes_per_expiration=5 if heston_shape_dates else 0,
        point_in_time_quotes=True,
        constrained_multistart_available=False,
    )
    missing_inputs = ["constrained multi-start Heston implementation and stability diagnostics"]
    if not license_authorized:
        missing_inputs.append("human confirmation of historical option-data research rights")
    return report.model_copy(
        update={
            "report_id": "ttwo-historical-surfaces-v2",
            "construction": SurfaceConstructionAudit(
                input_observations=len(observations),
                calls_considered=calls_considered,
                usable_quotes_before_iv=usable_before_iv,
                iv_inversions_succeeded=iv_succeeded,
                iv_inversions_failed=iv_failed,
                quotes_used_in_fitted_slices=len(surface_quotes),
                eligible_slices=len(eligible_keys),
                eligible_snapshots=len({key[0] for key in eligible_keys}),
                heston_shape_eligible_snapshots=heston_shape_dates,
                exclusion_counts=dict(sorted(exclusions.items())),
                option_style="american_call_equal_to_european_under_verified_zero_dividend",
                forward_convention="F=S*exp(rT), continuous zero dividend yield",
                rate_convention=(
                    "latest conservatively lagged Treasury par-yield curve, "
                    "linear tenor interpolation"
                ),
                quote_weighting=(
                    "inverse squared relative bid/ask spread, floor 2%, capped at 2500"
                ),
            ),
            "heston_gate": heston_gate,
            "missing_inputs": missing_inputs,
            "blockers": list(report.blockers)
            + ["Heston remains blocked until constrained multi-start calibration is implemented."],
        }
    )
