"""M0 full-repricing Greeks, carry, costs, scenarios, and trade tickets."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from itertools import combinations
from statistics import median
from typing import Literal, cast

from take_two_options.american import (
    option_model_value,
    risk_free_rate_for_expiry,
    validate_dividend_treatment,
)
from take_two_options.domain import (
    ExerciseStyle,
    MarketDataBundle,
    OptionQuote,
    OptionType,
    PositionSide,
    StrategyCandidate,
)
from take_two_options.pricing import analyze_risk, black_scholes_price_greeks
from take_two_options.quantitative.contracts import Measure
from take_two_options.research_statistics import wilson_interval
from take_two_options.trade_economics_models import (
    AdvancedGreeks,
    BreakevenClock,
    BreakevenResult,
    BreakevenSolverConfiguration,
    EntryCostBreakdown,
    ExitCostEstimate,
    FullRepricingAttribution,
    FXAttribution,
    FXHandlingMode,
    GreekConfidence,
    GreekConfidenceLevel,
    GreekMeasure,
    GreekTaylorAttribution,
    IntradayPrecisionStatus,
    LegEconomics,
    LeverageDiagnostics,
    LiquidityDiagnostics,
    MarginEstimate,
    MarginStatus,
    PnLAttribution,
    ProbabilityStatus,
    ProfitInterval,
    RateScenario,
    RateScenarioType,
    RateStressResult,
    RoundTripCost,
    ScenarioCell,
    ScenarioMatrix,
    TargetArrivalResult,
    TargetArrivalStatus,
    TimeDecayExposure,
    TimeDecayPoint,
    TouchDirection,
    TouchProbabilityMetrics,
    TradeEconomicsConfiguration,
    TradeEconomicsTicket,
    TradeIntensityCategory,
    TradeIntensityDiagnostics,
    VolatilityScenario,
    VolatilityScenarioStatus,
    VolatilityScenarioType,
)
from take_two_options.vol_surface import effective_volatility

_SECONDS_PER_DAY = 24.0 * 60.0 * 60.0
_GREEK_NAMES = (
    "delta",
    "gamma",
    "theta",
    "vega",
    "rho",
    "vanna",
    "vomma",
    "charm",
    "veta",
    "speed",
    "color",
)
_CONFIDENCE_ORDER = {
    GreekConfidenceLevel.HIGH: 0,
    GreekConfidenceLevel.MEDIUM: 1,
    GreekConfidenceLevel.LOW: 2,
    GreekConfidenceLevel.UNRELIABLE: 3,
}


def _option_legs(candidate: StrategyCandidate) -> list[tuple[int, OptionQuote]]:
    output: list[tuple[int, OptionQuote]] = []
    for index, leg in enumerate(candidate.legs):
        if leg.option_quote is not None:
            output.append((index, leg.option_quote))
    return output


def _effective_expiration(candidate: StrategyCandidate) -> datetime | None:
    expirations = [quote.contract.expiration for _, quote in _option_legs(candidate)]
    return min(expirations) if expirations else None


def _intrinsic(spot: float, quote: OptionQuote) -> float:
    if quote.contract.option_type is OptionType.CALL:
        return max(spot - quote.contract.strike, 0.0)
    return max(quote.contract.strike - spot, 0.0)


def _scenario_volatility(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    scenario: VolatilityScenario,
    *,
    spot: float,
    valuation_time: datetime,
) -> float:
    base = effective_volatility(bundle, quote).volatility
    parameters = scenario.parameters
    scenario_type = scenario.scenario_type
    dte = max(
        (quote.contract.expiration - valuation_time).total_seconds() / _SECONDS_PER_DAY,
        0.0,
    )
    shift_points = 0.0
    if scenario_type is VolatilityScenarioType.PARALLEL_ABSOLUTE_VOL_SHIFT:
        shift_points = parameters.parallel_shift_vol_points or 0.0
    elif scenario_type is VolatilityScenarioType.RELATIVE_VOL_MULTIPLIER:
        return max(base * (parameters.relative_multiplier or 1.0), 0.0001)
    elif scenario_type in {
        VolatilityScenarioType.SKEW_STEEPENING,
        VolatilityScenarioType.SKEW_FLATTENING,
    }:
        slope = parameters.skew_slope_vol_points or 0.0
        if scenario_type is VolatilityScenarioType.SKEW_FLATTENING:
            slope = -slope
        shift_points = slope * math.log(quote.contract.strike / spot)
    elif scenario_type in {
        VolatilityScenarioType.SHORT_END_CRUSH,
        VolatilityScenarioType.SHORT_END_EXPANSION,
    }:
        boundary = parameters.short_end_max_days or 90
        if dte <= boundary:
            shift_points = parameters.front_expiry_shift_vol_points or 0.0
    elif scenario_type is VolatilityScenarioType.LONG_END_STABLE:
        boundary = parameters.long_end_min_days or 365
        if dte < boundary:
            shift_points = parameters.front_expiry_shift_vol_points or 0.0
    elif scenario_type is VolatilityScenarioType.EVENT_IV_CRUSH:
        front = parameters.short_end_max_days or 90
        back = parameters.long_end_min_days or 365
        if dte <= front:
            shift_points = parameters.front_expiry_shift_vol_points or 0.0
        elif dte >= back:
            shift_points = parameters.back_expiry_shift_vol_points or 0.0
        else:
            shift_points = parameters.mid_expiry_shift_vol_points or 0.0
    elif scenario_type in {
        VolatilityScenarioType.SPOT_UP_IV_DOWN,
        VolatilityScenarioType.SPOT_DOWN_IV_UP,
    }:
        shift_points = parameters.parallel_shift_vol_points or 0.0
    return max(base + shift_points * 0.01, 0.0001)


def _scenario_spot(spot: float, scenario: VolatilityScenario) -> float:
    if scenario.scenario_type in {
        VolatilityScenarioType.SPOT_UP_IV_DOWN,
        VolatilityScenarioType.SPOT_DOWN_IV_UP,
    }:
        return spot * (scenario.parameters.spot_multiplier or 1.0)
    return spot


def _rate_shift_for_expiry(
    scenario: RateScenario,
    *,
    valuation_time: datetime,
    expiration: datetime,
) -> float:
    """Return the configured maturity-aware curve shift in basis points."""
    maturity_days = max(
        (expiration - valuation_time).total_seconds() / _SECONDS_PER_DAY,
        0.0,
    )
    if maturity_days <= scenario.short_end_max_days:
        return scenario.short_end_shift_basis_points
    if maturity_days >= scenario.long_end_min_days:
        return scenario.long_end_shift_basis_points
    weight = (maturity_days - scenario.short_end_max_days) / (
        scenario.long_end_min_days - scenario.short_end_max_days
    )
    return scenario.short_end_shift_basis_points + weight * (
        scenario.long_end_shift_basis_points - scenario.short_end_shift_basis_points
    )


def _surface_stress_status(
    bundle: MarketDataBundle,
    scenario: VolatilityScenario,
) -> VolatilityScenarioStatus:
    surface = bundle.volatility_surface
    if surface is None:
        return VolatilityScenarioStatus.LEG_LEVEL_STRESS_ONLY
    transformed: dict[tuple[float, OptionType], list[tuple[float, float]]] = {}
    for node in surface.nodes:
        synthetic = next(
            (
                quote
                for quote in bundle.option_quotes
                if quote.contract.strike == node.strike
                and quote.contract.expiration == node.expiration
                and quote.contract.option_type is node.option_type
            ),
            None,
        )
        if synthetic is None:
            base = node.implied_volatility
            parameters = scenario.parameters
            shift = parameters.parallel_shift_vol_points or 0.0
            if scenario.scenario_type is VolatilityScenarioType.RELATIVE_VOL_MULTIPLIER:
                volatility = base * (parameters.relative_multiplier or 1.0)
            elif scenario.scenario_type is VolatilityScenarioType.CONSTANT_LEG_IV:
                volatility = base
            else:
                volatility = base + shift * 0.01
        else:
            volatility = _scenario_volatility(
                synthetic,
                bundle,
                scenario,
                spot=bundle.underlying.price,
                valuation_time=bundle.analysis_timestamp,
            )
        maturity = max(
            (node.expiration - bundle.analysis_timestamp).total_seconds()
            / (_SECONDS_PER_DAY * 365.0),
            0.0,
        )
        if volatility <= 0 or maturity <= 0:
            return VolatilityScenarioStatus.SURFACE_STRESS_INVALID
        transformed.setdefault((node.strike, node.option_type), []).append(
            (maturity, volatility * volatility * maturity)
        )
    for values in transformed.values():
        ordered = sorted(values)
        if any(
            right[1] + 1e-10 < left[1]
            for left, right in zip(ordered, ordered[1:], strict=False)
        ):
            return VolatilityScenarioStatus.SURFACE_STRESS_INVALID
    return VolatilityScenarioStatus.SURFACE_STRESS_VALID


def reprice_position(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    spot: float,
    valuation_time: datetime,
    volatility_scenario: VolatilityScenario | None = None,
    rate_shift_basis_points: float = 0.0,
    rate_scenario: RateScenario | None = None,
    time_grid: int | None = None,
    price_grid: int | None = None,
) -> float:
    """Fully reprice every live leg under one economic state."""
    validate_dividend_treatment(bundle)
    value = 0.0
    for leg in candidate.legs:
        scale = float(leg.side.sign * leg.quantity)
        if leg.instrument_type == "stock":
            value += scale * spot
            continue
        quote = leg.option_quote
        assert quote is not None
        scale *= quote.contract.multiplier
        if valuation_time >= quote.contract.expiration:
            value += scale * _intrinsic(spot, quote)
            continue
        volatility = (
            _scenario_volatility(
                quote,
                bundle,
                volatility_scenario,
                spot=spot,
                valuation_time=valuation_time,
            )
            if volatility_scenario is not None
            else effective_volatility(bundle, quote).volatility
        )
        scenario_rate_shift = (
            _rate_shift_for_expiry(
                rate_scenario,
                valuation_time=valuation_time,
                expiration=quote.contract.expiration,
            )
            if rate_scenario is not None
            else 0.0
        )
        rate = risk_free_rate_for_expiry(
            bundle,
            valuation_time=valuation_time,
            expiration=quote.contract.expiration,
        ) + (rate_shift_basis_points + scenario_rate_shift) / 10_000.0
        value += scale * option_model_value(
            quote,
            bundle,
            # QuantLib requires a strictly positive quote; 1e-8 is the declared
            # numerical proxy for the economically meaningful S=0 boundary.
            spot=max(spot, 1e-8),
            valuation_time=valuation_time,
            volatility=volatility,
            rate=rate,
            time_grid=time_grid,
            price_grid=price_grid,
        )
    return value


def _single_leg_estimates(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    *,
    spot_relative_bump: float,
    volatility_bump_vol_points: float,
    rate_bump_basis_points: float,
    grid: int,
) -> dict[str, float]:
    spot = bundle.underlying.price
    valuation_time = bundle.analysis_timestamp
    volatility = effective_volatility(bundle, quote).volatility
    rate = risk_free_rate_for_expiry(
        bundle,
        valuation_time=valuation_time,
        expiration=quote.contract.expiration,
    )
    spot_step = max(spot * spot_relative_bump, bundle.trade_economics.greek_bumps.minimum_spot_bump)
    spot_step = min(spot_step, spot * 0.24)
    vol_step = min(volatility_bump_vol_points * 0.01, volatility * 0.49)
    rate_step = rate_bump_basis_points / 10_000.0

    def value(
        selected_spot: float = spot,
        selected_time: datetime = valuation_time,
        selected_volatility: float = volatility,
        selected_rate: float = rate,
    ) -> float:
        if selected_time >= quote.contract.expiration:
            return _intrinsic(selected_spot, quote)
        return option_model_value(
            quote,
            bundle,
            spot=selected_spot,
            valuation_time=selected_time,
            volatility=max(selected_volatility, 0.0001),
            rate=selected_rate,
            time_grid=grid,
            price_grid=grid,
        )

    def delta_gamma(selected_spot: float, selected_time: datetime) -> tuple[float, float]:
        local_step = min(spot_step, selected_spot * 0.24)
        center = value(selected_spot=selected_spot, selected_time=selected_time)
        up = value(selected_spot=selected_spot + local_step, selected_time=selected_time)
        down = value(selected_spot=selected_spot - local_step, selected_time=selected_time)
        delta = (up - down) / (2.0 * local_step)
        gamma = (up - 2.0 * center + down) / (local_step * local_step)
        return delta, gamma

    def vega_at(selected_time: datetime) -> float:
        up = value(selected_time=selected_time, selected_volatility=volatility + vol_step)
        down = value(selected_time=selected_time, selected_volatility=volatility - vol_step)
        return (up - down) * 0.01 / (2.0 * vol_step)

    base = value()
    delta, gamma = delta_gamma(spot, valuation_time)
    next_time = min(
        valuation_time
        + timedelta(days=bundle.trade_economics.greek_bumps.time_bump_calendar_days),
        quote.contract.expiration,
    )
    theta = value(selected_time=next_time) - base
    vega = vega_at(valuation_time)
    rho = (
        value(selected_rate=rate + rate_step) - value(selected_rate=rate - rate_step)
    ) * 0.01 / (2.0 * rate_step)
    vanna_raw = (
        value(selected_spot=spot + spot_step, selected_volatility=volatility + vol_step)
        - value(selected_spot=spot + spot_step, selected_volatility=volatility - vol_step)
        - value(selected_spot=spot - spot_step, selected_volatility=volatility + vol_step)
        + value(selected_spot=spot - spot_step, selected_volatility=volatility - vol_step)
    ) / (4.0 * spot_step * vol_step)
    vomma_raw = (
        value(selected_volatility=volatility + vol_step)
        - 2.0 * base
        + value(selected_volatility=volatility - vol_step)
    ) / (vol_step * vol_step)
    next_delta, next_gamma = delta_gamma(spot, next_time)
    speed = (
        delta_gamma(spot + spot_step, valuation_time)[1]
        - delta_gamma(spot - spot_step, valuation_time)[1]
    ) / (2.0 * spot_step)
    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho,
        "vanna": vanna_raw * 0.01,
        "vomma": vomma_raw * 0.0001,
        "charm": next_delta - delta,
        "veta": vega_at(next_time) - vega,
        "speed": speed,
        "color": next_gamma - gamma,
        "vanna_raw": vanna_raw,
        "vomma_raw": vomma_raw,
    }


def _analytic_advanced_benchmark(
    quote: OptionQuote,
    bundle: MarketDataBundle,
) -> dict[str, float] | None:
    if bundle.dividends:
        return None
    time_years = max(
        (quote.contract.expiration - bundle.analysis_timestamp).total_seconds()
        / (_SECONDS_PER_DAY * 365.0),
        1e-12,
    )
    spot = bundle.underlying.price
    volatility = effective_volatility(bundle, quote).volatility
    rate = risk_free_rate_for_expiry(
        bundle,
        valuation_time=bundle.analysis_timestamp,
        expiration=quote.contract.expiration,
    )
    dividend_yield = (
        bundle.continuous_dividend_yield
        if bundle.dividend_treatment_mode.value
        in {"CONTINUOUS_YIELD", "HYBRID_EXPLICIT_NON_OVERLAPPING"}
        else 0.0
    )
    first = black_scholes_price_greeks(
        spot=spot,
        strike=quote.contract.strike,
        time_years=time_years,
        rate=rate,
        volatility=volatility,
        option_type=quote.contract.option_type,
        dividend_yield=dividend_yield,
    )
    root_time = math.sqrt(time_years)
    d1 = (
        math.log(spot / quote.contract.strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_years
    ) / (volatility * root_time)
    d2 = d1 - volatility * root_time
    density = math.exp(-0.5 * d1 * d1) / math.sqrt(2.0 * math.pi)
    vega_raw = spot * math.exp(-dividend_yield * time_years) * density * root_time
    vanna_raw = -math.exp(-dividend_yield * time_years) * density * d2 / volatility
    vomma_raw = vega_raw * d1 * d2 / volatility
    return {
        "delta": first.delta,
        "gamma": first.gamma,
        "theta": first.theta,
        "vega": first.vega,
        "rho": first.rho,
        "vanna": vanna_raw * 0.01,
        "vomma": vomma_raw * 0.0001,
    }


def _confidence(
    greek: str,
    estimates: list[float],
    *,
    primary_bump: float,
    alternate_bumps: list[float],
    grid_levels: list[int],
    benchmark: float | None,
    config: TradeEconomicsConfiguration,
) -> GreekConfidence:
    primary = estimates[0]
    dispersion = max(estimates) - min(estimates)
    scale = max(abs(primary), config.numerical_tolerances.greek_absolute_scale_floor)
    relative = abs(dispersion) / scale
    thresholds = config.numerical_tolerances
    if relative <= thresholds.greek_high_relative_dispersion:
        level = GreekConfidenceLevel.HIGH
    elif relative <= thresholds.greek_medium_relative_dispersion:
        level = GreekConfidenceLevel.MEDIUM
    elif relative <= thresholds.greek_low_relative_dispersion:
        level = GreekConfidenceLevel.LOW
    else:
        level = GreekConfidenceLevel.UNRELIABLE
    warnings: list[str] = []
    if level in {GreekConfidenceLevel.LOW, GreekConfidenceLevel.UNRELIABLE}:
        warnings.append("Estimate is sensitive to configured bumps or FD grid refinement")
    benchmark_difference = abs(primary - benchmark) if benchmark is not None else None
    return GreekConfidence(
        greek=greek,
        estimate=primary,
        method="same_pricer_central_finite_difference_multi_bump",
        primary_bump=primary_bump,
        alternate_bumps=alternate_bumps,
        grid_levels=grid_levels,
        estimate_dispersion=abs(dispersion),
        relative_dispersion=relative,
        benchmark_difference=benchmark_difference,
        confidence_level=level,
        warnings=warnings,
    )


def calculate_leg_advanced_greeks(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    *,
    side: PositionSide,
) -> AdvancedGreeks:
    """Calculate normalized first/second-order Greeks from the selected full pricer."""
    bumps = bundle.trade_economics.greek_bumps
    primary_index = min(1, len(bumps.spot_relative_bumps) - 1)
    primary_grid = bumps.grid_levels[0]
    estimates_by_run: list[dict[str, float]] = []
    run_bumps: list[tuple[float, float, float, int]] = []
    run_count = max(
        len(bumps.spot_relative_bumps),
        len(bumps.volatility_bumps_vol_points),
        len(bumps.rate_bumps_basis_points),
    )
    for index in range(run_count):
        run_bumps.append(
            (
                bumps.spot_relative_bumps[min(index, len(bumps.spot_relative_bumps) - 1)],
                bumps.volatility_bumps_vol_points[
                    min(index, len(bumps.volatility_bumps_vol_points) - 1)
                ],
                bumps.rate_bumps_basis_points[
                    min(index, len(bumps.rate_bumps_basis_points) - 1)
                ],
                primary_grid,
            )
        )
    primary_tuple = run_bumps[primary_index]
    run_bumps = [primary_tuple, *[item for item in run_bumps if item != primary_tuple]]
    for grid in bumps.grid_levels[1:]:
        run_bumps.append((*primary_tuple[:3], grid))
    for spot_bump, vol_bump, rate_bump, grid in run_bumps:
        estimates_by_run.append(
            _single_leg_estimates(
                quote,
                bundle,
                spot_relative_bump=spot_bump,
                volatility_bump_vol_points=vol_bump,
                rate_bump_basis_points=rate_bump,
                grid=grid,
            )
        )
    analytic = _analytic_advanced_benchmark(quote, bundle) or {}
    confidence: list[GreekConfidence] = []
    for greek in _GREEK_NAMES:
        if greek in {"delta", "gamma", "speed"}:
            primary_bump = primary_tuple[0]
            alternate = bumps.spot_relative_bumps
        elif greek in {"vega", "vanna", "vomma", "veta"}:
            primary_bump = primary_tuple[1]
            alternate = bumps.volatility_bumps_vol_points
        elif greek == "rho":
            primary_bump = primary_tuple[2]
            alternate = bumps.rate_bumps_basis_points
        else:
            primary_bump = float(bumps.time_bump_calendar_days)
            alternate = [float(bumps.time_bump_calendar_days)]
        confidence.append(
            _confidence(
                greek,
                [item[greek] for item in estimates_by_run],
                primary_bump=primary_bump,
                alternate_bumps=list(alternate),
                grid_levels=bumps.grid_levels,
                benchmark=analytic.get(greek),
                config=bundle.trade_economics,
            )
        )
    primary = estimates_by_run[0]
    confidence_by_name = {item.greek: item for item in confidence}
    provider_values = {
        "delta": quote.delta,
        "gamma": quote.gamma,
        "theta": quote.theta,
        "vega": quote.vega,
        "rho": quote.rho,
    }
    units = {
        "delta": "currency_per_1_spot_unit",
        "gamma": "delta_per_1_spot_unit",
        "theta": "currency_per_calendar_day",
        "vega": "currency_per_1_vol_point",
        "rho": "currency_per_1_percentage_point_rate",
        "vanna": "currency_per_spot_unit_per_vol_point",
        "vomma": "currency_per_vol_point_squared",
        "charm": "delta_drift_per_calendar_day",
        "veta": "vega_drift_per_calendar_day",
        "speed": "gamma_per_spot_unit",
        "color": "gamma_drift_per_calendar_day",
    }

    def measure(greek: str, *, raw_key: str | None = None) -> GreekMeasure:
        value = primary[greek]
        raw_value = primary[raw_key] if raw_key else value
        diagnostic = confidence_by_name[greek]
        return GreekMeasure(
            value=value,
            raw_value=raw_value,
            normalized_value=value,
            unit=units[greek],
            currency=quote.contract.currency,
            multiplier=quote.contract.multiplier,
            position_sign=side.sign,
            model=(
                "quantlib_fd_american"
                if quote.contract.exercise_style is ExerciseStyle.AMERICAN
                else "quantlib_fd_european"
            ),
            source="internal_same_full_pricer",
            timestamp=bundle.analysis_timestamp,
            bump_size=diagnostic.primary_bump,
            confidence=diagnostic.confidence_level,
            calculation_method=diagnostic.method,
            provider_raw_value=provider_values.get(greek),
            provider_convention=(
                "provider_convention_not_supplied"
                if provider_values.get(greek) is not None
                else None
            ),
            normalized_internal_value=value,
        )

    return AdvancedGreeks(
        delta=measure("delta"),
        gamma=measure("gamma"),
        theta=measure("theta"),
        vega=measure("vega"),
        rho=measure("rho"),
        vanna=measure("vanna", raw_key="vanna_raw"),
        vomma=measure("vomma", raw_key="vomma_raw"),
        charm_delta_drift_1_calendar_day=measure("charm"),
        veta_vega_drift_1_calendar_day=measure("veta"),
        speed=(
            measure("speed")
            if bundle.trade_economics.advanced_greeks.display_speed
            else None
        ),
        color_gamma_drift_1_calendar_day=(
            measure("color")
            if bundle.trade_economics.advanced_greeks.display_color
            else None
        ),
        confidence=confidence,
        conventions=[
            "Theta is currency per calendar day and is a local one-day reprice.",
            "Vega is currency per +1 volatility point (sigma decimal +0.01).",
            "Rho is currency per +1 percentage-point rate move.",
            "Vanna is d2V/(dS dsigma), normalized per spot unit per vol point.",
            "Vomma is d2V/dsigma2, normalized per vol point squared.",
            "Charm is exposed as Delta(t+1 calendar day)-Delta(t) at flat spot/IV.",
            "Veta is exposed as Vega(t+1 calendar day)-Vega(t) at flat spot/IV.",
            "Color is exposed as Gamma(t+1 calendar day)-Gamma(t) at flat spot/IV.",
        ],
    )


def _worst_confidence(levels: Sequence[GreekConfidenceLevel]) -> GreekConfidenceLevel:
    return max(levels, key=lambda level: _CONFIDENCE_ORDER[level])


def aggregate_advanced_greeks(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    leg_greeks: dict[int, AdvancedGreeks],
) -> AdvancedGreeks | None:
    if not leg_greeks:
        return None
    field_map = {
        "delta": "delta",
        "gamma": "gamma",
        "theta": "theta",
        "vega": "vega",
        "rho": "rho",
        "vanna": "vanna",
        "vomma": "vomma",
        "charm": "charm_delta_drift_1_calendar_day",
        "veta": "veta_vega_drift_1_calendar_day",
        "speed": "speed",
        "color": "color_gamma_drift_1_calendar_day",
    }
    measures: dict[str, GreekMeasure | None] = {}
    diagnostics: list[GreekConfidence] = []
    for greek, field_name in field_map.items():
        total = 0.0
        raw_total = 0.0
        levels: list[GreekConfidenceLevel] = []
        relative_dispersion = 0.0
        for index, leg in enumerate(candidate.legs):
            advanced = leg_greeks.get(index)
            if advanced is None:
                if greek == "delta" and leg.instrument_type == "stock":
                    total += leg.side.sign * leg.quantity
                    raw_total += leg.side.sign * leg.quantity
                continue
            item = getattr(advanced, field_name)
            if item is None:
                continue
            quote = leg.option_quote
            assert quote is not None
            scale = leg.side.sign * leg.quantity * quote.contract.multiplier
            total += item.normalized_internal_value * scale
            raw_total += item.raw_value * scale
            diagnostic = next(value for value in advanced.confidence if value.greek == greek)
            levels.append(diagnostic.confidence_level)
            relative_dispersion = max(relative_dispersion, diagnostic.relative_dispersion)
        if not levels and greek != "delta":
            measures[greek] = None
            continue
        level = _worst_confidence(levels) if levels else GreekConfidenceLevel.HIGH
        source_measure = next(
            (
                getattr(advanced, field_name)
                for advanced in leg_greeks.values()
                if getattr(advanced, field_name) is not None
            ),
            None,
        )
        unit = source_measure.unit if source_measure is not None else "underlying_units"
        measures[greek] = GreekMeasure(
            value=total,
            raw_value=raw_total,
            normalized_value=total,
            unit=unit,
            currency=bundle.underlying.currency,
            multiplier=1.0,
            position_sign=0,
            model="position_aggregate_same_full_pricer",
            source="signed_leg_sum",
            timestamp=bundle.analysis_timestamp,
            bump_size=0.0,
            confidence=level,
            calculation_method="sum(side*quantity*contract_multiplier*normalized_leg_greek)",
            normalized_internal_value=total,
        )
        diagnostics.append(
            GreekConfidence(
                greek=greek,
                estimate=total,
                method="worst_leg_confidence_signed_aggregation",
                primary_bump=0.0,
                alternate_bumps=[],
                grid_levels=bundle.trade_economics.greek_bumps.grid_levels,
                estimate_dispersion=abs(total) * relative_dispersion,
                relative_dispersion=relative_dispersion,
                benchmark_difference=None,
                confidence_level=level,
                warnings=(
                    ["Aggregate confidence is bounded by the least stable component leg"]
                    if level is not GreekConfidenceLevel.HIGH
                    else []
                ),
            )
        )
    required = ("delta", "gamma", "theta", "vega", "rho", "vanna", "vomma", "charm", "veta")
    if any(measures.get(name) is None for name in required):
        return None
    return AdvancedGreeks(
        delta=cast(GreekMeasure, measures["delta"]),
        gamma=cast(GreekMeasure, measures["gamma"]),
        theta=cast(GreekMeasure, measures["theta"]),
        vega=cast(GreekMeasure, measures["vega"]),
        rho=cast(GreekMeasure, measures["rho"]),
        vanna=cast(GreekMeasure, measures["vanna"]),
        vomma=cast(GreekMeasure, measures["vomma"]),
        charm_delta_drift_1_calendar_day=cast(GreekMeasure, measures["charm"]),
        veta_vega_drift_1_calendar_day=cast(GreekMeasure, measures["veta"]),
        speed=measures["speed"],
        color_gamma_drift_1_calendar_day=measures["color"],
        confidence=diagnostics,
        conventions=["Position Greeks are signed sums of normalized leg Greeks."],
    )


def _capital_at_risk(candidate: StrategyCandidate) -> tuple[float | None, str]:
    risk = candidate.risk_metrics
    execution = candidate.execution_estimate
    if (
        risk is not None
        and not risk.unbounded_risk
        and risk.max_loss is not None
        and risk.max_loss > 0
    ):
        return risk.max_loss, "KNOWN_BOUNDED_MAX_LOSS"
    if execution is not None and execution.total_entry_cost > 0:
        return execution.total_entry_cost, "KNOWN_DEBIT_CAPITAL"
    if execution is not None and execution.margin_requirement is not None:
        return execution.margin_requirement, execution.margin_status.value
    return None, "BLOCKED_UNKNOWN_CAPITAL_AT_RISK"


def calculate_leverage(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    aggregate: AdvancedGreeks | None,
    leg_greeks: dict[int, AdvancedGreeks],
) -> LeverageDiagnostics:
    capital, status = _capital_at_risk(candidate)
    warnings: list[str] = []
    if capital is None or capital < bundle.trade_economics.leverage_denominator_floor:
        warnings.append("Leverage is unavailable because capital at risk is unknown or too small")
        return LeverageDiagnostics(
            capital_at_risk=capital,
            capital_status=status,
            warnings=warnings,
        )
    net_delta = aggregate.delta.value if aggregate is not None else 0.0
    gross_delta = 0.0
    for index, leg in enumerate(candidate.legs):
        if leg.instrument_type == "stock":
            gross_delta += abs(leg.quantity * bundle.underlying.price)
            continue
        quote = leg.option_quote
        advanced = leg_greeks.get(index)
        if quote is None or advanced is None:
            continue
        gross_delta += abs(
            advanced.delta.value
            * leg.quantity
            * quote.contract.multiplier
            * bundle.underlying.price
        )
    current_value = reprice_position(
        candidate,
        bundle,
        spot=bundle.underlying.price,
        valuation_time=bundle.analysis_timestamp,
    )
    lambda_value: float | None = None
    if (
        len(candidate.legs) == 1
        and current_value > bundle.trade_economics.leverage_denominator_floor
    ):
        lambda_value = net_delta * bundle.underlying.price / current_value
    elif len(candidate.legs) > 1:
        warnings.append("Classic lambda is suppressed for multi-leg net values")
    else:
        warnings.append("Classic lambda denominator is too small or non-positive")
    return LeverageDiagnostics(
        capital_at_risk=capital,
        capital_status=status,
        lambda_value_elasticity=lambda_value,
        delta_notional_leverage=abs(net_delta * bundle.underlying.price) / capital,
        gross_delta_leverage=gross_delta / capital,
        warnings=warnings,
    )


def build_exit_cost_estimate(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
) -> ExitCostEstimate:
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    policy = bundle.trade_economics.exit_cost_model
    bid_ask = execution.bid_ask_cost * policy.spread_cost_multiplier
    slippage = execution.slippage * policy.slippage_cost_multiplier
    commissions = execution.fees * policy.closing_commission_multiplier
    fx_cost: float | None = None
    warnings = ["Future spread and slippage are configured estimates, not observations"]
    if bundle.trade_economics.fx_mode is FXHandlingMode.CONVERT_AT_ENTRY_AND_EXIT:
        if policy.fx_exit_cost_bps is None:
            warnings.append("FX exit cost is unknown and remains null")
        else:
            fx_cost = (
                abs(execution.theoretical_mid) * policy.fx_exit_cost_bps / 10_000.0
            )
    exercise_cost = policy.assignment_or_exercise_cost
    if any(leg.side is PositionSide.SHORT for leg in candidate.legs) and exercise_cost is None:
        warnings.append("Assignment/exercise cost is unknown; broker validation remains pending")
    total = bid_ask + slippage + commissions + (fx_cost or 0.0) + (exercise_cost or 0.0)
    return ExitCostEstimate(
        estimated_exit_bid_ask_cost=round(bid_ask, 8),
        estimated_exit_slippage=round(slippage, 8),
        closing_commissions=round(commissions, 8),
        fx_exit_cost=None if fx_cost is None else round(fx_cost, 8),
        assignment_or_exercise_cost_if_relevant=exercise_cost,
        total_exit_cost=round(total, 8),
        status=policy.status,
        warnings=warnings,
    )


def build_round_trip_cost(
    candidate: StrategyCandidate,
    exit_cost: ExitCostEstimate,
) -> RoundTripCost:
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    total = (
        execution.bid_ask_cost
        + execution.slippage
        + execution.fees
        + (execution.fx_conversion_cost or 0.0)
        + exit_cost.total_exit_cost
    )
    capital, _ = _capital_at_risk(candidate)
    return RoundTripCost(
        entry_bid_ask_cost=execution.bid_ask_cost,
        entry_slippage=execution.slippage,
        entry_commissions=execution.fees,
        entry_fx_cost=execution.fx_conversion_cost,
        exit=exit_cost,
        total_round_trip_cost=round(total, 8),
        round_trip_cost_as_pct_capital=(total / capital if capital else None),
    )


def _entry_cost(candidate: StrategyCandidate) -> EntryCostBreakdown:
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    return EntryCostBreakdown(
        premium_paid=execution.premium_paid,
        premium_received=execution.premium_received,
        net_premium=execution.net_premium,
        mid_theoretical_value=execution.theoretical_mid,
        bid_ask_cost=execution.bid_ask_cost,
        expected_slippage=execution.slippage,
        commission=execution.fees,
        fx_conversion_cost=execution.fx_conversion_cost,
        total_entry_cost=execution.total_entry_cost,
        total_capital_required=execution.total_capital_required,
        execution_status=execution.execution_status,
        combo_execution_status=execution.combo_execution_status,
        warnings=list(execution.notes),
    )


def _margin(candidate: StrategyCandidate) -> MarginEstimate:
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    source = (
        "broker_preview"
        if execution.margin_status is MarginStatus.KNOWN_BROKER
        else "bounded_strategy_analytical_estimate"
        if execution.margin_status is MarginStatus.ESTIMATED
        else "not_required_for_paid_debit"
        if execution.margin_status is MarginStatus.NOT_REQUIRED
        else "pending_broker_what_if"
    )
    return MarginEstimate(
        margin_requirement=execution.margin_requirement,
        buying_power_usage=execution.margin_requirement,
        status=execution.margin_status,
        source=source,
        warnings=[
            "Real broker margin remains PENDING_BROKER until an IBKR what-if preview is available"
        ],
    )


def calculate_time_decay_exposure(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    aggregate: AdvancedGreeks | None,
) -> TimeDecayExposure | None:
    expiration = _effective_expiration(candidate)
    if expiration is None:
        return None
    analysis_time = bundle.analysis_timestamp
    if expiration <= analysis_time:
        return None
    base_value = reprice_position(
        candidate,
        bundle,
        spot=bundle.underlying.price,
        valuation_time=analysis_time,
    )
    expiry_days = max(math.ceil((expiration - analysis_time).total_seconds() / _SECONDS_PER_DAY), 1)
    requested = [*bundle.trade_economics.time_decay_horizons_days, expiry_days]
    selected_times = sorted(
        {
            analysis_time,
            *(min(analysis_time + timedelta(days=days), expiration) for days in requested),
        }
    )
    capital, capital_status = _capital_at_risk(candidate)
    max_loss = candidate.risk_metrics.max_loss if candidate.risk_metrics else None
    points: list[TimeDecayPoint] = []
    crossed_dividend = False
    for valuation_time in selected_times:
        days = max(
            round((valuation_time - analysis_time).total_seconds() / _SECONDS_PER_DAY),
            0,
        )
        value = reprice_position(
            candidate,
            bundle,
            spot=bundle.underlying.price,
            valuation_time=valuation_time,
        )
        carry_value = value - base_value
        crossed = [
            dividend
            for dividend in bundle.dividends
            if analysis_time.date() < dividend.ex_date <= valuation_time.date()
        ]
        crossed_dividend = crossed_dividend or bool(crossed)
        ex_div_value: float | None = None
        warnings: list[str] = []
        if crossed:
            adjusted_spot = max(
                bundle.underlying.price - sum(dividend.amount for dividend in crossed),
                0.01,
            )
            ex_div_value = reprice_position(
                candidate,
                bundle,
                spot=adjusted_spot,
                valuation_time=valuation_time,
            )
            warnings.append(
                "Flat spot crosses a discrete ex-dividend date; pure carry and the simple "
                "cash-dividend spot adjustment are shown separately"
            )
        points.append(
            TimeDecayPoint(
                horizon_days=days,
                valuation_time=valuation_time,
                estimated_position_value=round(value, 8),
                flat_spot_carry=round(carry_value, 8),
                carry_as_pct_capital=(carry_value / capital if capital else None),
                carry_as_pct_max_loss=(carry_value / max_loss if max_loss else None),
                carry_classification=(
                    "CROSSES_DIVIDEND_EVENT" if crossed else "PURE_FLAT_SPOT_CARRY"
                ),
                ex_div_adjusted_position_value=(
                    round(ex_div_value, 8) if ex_div_value is not None else None
                ),
                warnings=warnings,
            )
        )
    by_days = {point.horizon_days: point for point in points}

    def carry_at(days: int) -> float | None:
        return by_days[days].flat_spot_carry if days in by_days else None

    def rate(start: int, end: int) -> float | None:
        start_value = 0.0 if start == 0 else carry_at(start)
        end_value = carry_at(end)
        if start_value is None or end_value is None:
            return None
        return (end_value - start_value) / (end - start)

    rate_0_7 = rate(0, 7)
    rate_0_30 = rate(0, 30)
    rate_30_60 = rate(30, 60)
    rate_60_90 = rate(60, 90)
    acceleration_30_60 = (
        rate_30_60 - rate_0_30
        if rate_30_60 is not None and rate_0_30 is not None
        else None
    )
    acceleration_60_90 = (
        rate_60_90 - rate_30_60
        if rate_60_90 is not None and rate_30_60 is not None
        else None
    )
    rates = [item for item in (rate_0_30, rate_30_60, rate_60_90) if item is not None]
    if len(rates) >= 2 and any(
        left * right < 0 for left, right in zip(rates, rates[1:], strict=False)
    ):
        acceleration_status = "SIGN_FLIP"
    elif acceleration_30_60 is None and acceleration_60_90 is None:
        acceleration_status = "INSUFFICIENT"
    elif len(rates) >= 2 and abs(rates[-1]) > abs(rates[0]):
        acceleration_status = "ACCELERATING"
    else:
        acceleration_status = "DECELERATING"
    theta = aggregate.theta.value if aggregate is not None else 0.0
    confidence = (
        next(item for item in aggregate.confidence if item.greek == "theta").confidence_level.value
        if aggregate is not None
        else GreekConfidenceLevel.UNRELIABLE.value
    )
    warnings = []
    if len({quote.contract.expiration for _, quote in _option_legs(candidate)}) > 1:
        warnings.append(
            "Carry is clipped at the earliest leg expiry; post-expiry settlement cashflows "
            "for mixed-expiry structures require a separate model"
        )
    if crossed_dividend:
        warnings.append("Dividend/exercise-boundary effects must not be labeled pure theta")
    return TimeDecayExposure(
        current_net_theta=theta,
        theta_per_capital_per_day=(theta / capital if capital else None),
        theta_capital_status=(
            "AVAILABLE" if capital else "BLOCKED_UNKNOWN_CAPITAL_AT_RISK"
        ),
        flat_spot_1d=carry_at(1),
        flat_spot_7d=carry_at(7),
        flat_spot_30d=carry_at(30),
        flat_spot_60d=carry_at(60),
        flat_spot_90d=carry_at(90),
        effective_decay_rate_0_7=rate_0_7,
        effective_decay_rate_0_30=rate_0_30,
        effective_decay_rate_30_60=rate_30_60,
        effective_decay_rate_60_90=rate_60_90,
        decay_acceleration_30_60=acceleration_30_60,
        decay_acceleration_60_90=acceleration_60_90,
        acceleration_status=cast(
            Literal["ACCELERATING", "DECELERATING", "SIGN_FLIP", "INSUFFICIENT"],
            acceleration_status,
        ),
        time_decay_curve=points,
        assumptions=[
            "Full repricing at flat spot with CONSTANT_LEG_IV.",
            "Each leg retains its own current IV; current theta is not multiplied by horizon.",
            f"Capital basis status: {capital_status}.",
        ],
        confidence=confidence,
        warnings=warnings,
    )


def _liquidity_diagnostics(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
) -> list[LiquidityDiagnostics]:
    score = candidate.execution_estimate.liquidity_score if candidate.execution_estimate else 0.0
    output: list[LiquidityDiagnostics] = []
    for _, quote in _option_legs(candidate):
        mid = quote.mid
        spread = quote.ask - quote.bid if quote.ask is not None and quote.bid is not None else None
        age = max((bundle.analysis_timestamp - quote.timestamp).total_seconds(), 0.0)
        output.append(
            LiquidityDiagnostics(
                contract_symbol=quote.contract.local_symbol,
                bid=quote.bid,
                ask=quote.ask,
                mid=mid,
                spread_abs=spread,
                spread_pct_mid=(spread / mid if spread is not None and mid else None),
                bid_size=quote.bid_size,
                ask_size=quote.ask_size,
                volume=quote.volume,
                open_interest=quote.open_interest,
                quote_age_seconds=age,
                source=quote.source.id,
                timestamp=quote.timestamp,
                liquidity_score=score,
                liquidity_model_version="legacy_weighted_heuristic_v1",
                calibration_status="UNCALIBRATED",
            )
        )
    return output


def _scenario_horizons(candidate: StrategyCandidate, bundle: MarketDataBundle) -> list[int]:
    expiration = _effective_expiration(candidate)
    if expiration is None:
        return bundle.trade_economics.scenario_horizons_days
    expiry_days = max(
        math.ceil(
            (expiration - bundle.analysis_timestamp).total_seconds() / _SECONDS_PER_DAY
        ),
        0,
    )
    return sorted(
        {
            min(days, expiry_days)
            for days in [*bundle.trade_economics.scenario_horizons_days, expiry_days]
        }
    )


def _spot_axis(candidate: StrategyCandidate, bundle: MarketDataBundle) -> list[float]:
    spot = bundle.underlying.price
    spot_grid = bundle.trade_economics.spot_grid
    values = (
        [spot * value for value in spot_grid.values]
        if spot_grid.mode == "spot_multipliers"
        else list(spot_grid.values)
    )
    values.extend(quote.contract.strike for _, quote in _option_legs(candidate))
    values.extend(bundle.trade_economics.target_spots)
    values.extend(item.target_price for item in bundle.fundamental.scenarios)
    return sorted({round(value, 8) for value in values if value > 0})


def build_scenario_matrices(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    round_trip: RoundTripCost,
) -> list[ScenarioMatrix]:
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    capital, _ = _capital_at_risk(candidate)
    horizons = _scenario_horizons(candidate, bundle)
    matrices: list[ScenarioMatrix] = []
    for scenario in bundle.trade_economics.volatility_scenarios:
        status = _surface_stress_status(bundle, scenario)
        cells: list[ScenarioCell] = []
        actual_spots = sorted(
            {
                _scenario_spot(value, scenario)
                for value in _spot_axis(candidate, bundle)
            }
        )
        for horizon in horizons:
            valuation_time = bundle.analysis_timestamp + timedelta(days=horizon)
            expiration = _effective_expiration(candidate)
            if expiration is not None:
                valuation_time = min(valuation_time, expiration)
            for spot in actual_spots:
                value = reprice_position(
                    candidate,
                    bundle,
                    spot=spot,
                    valuation_time=valuation_time,
                    volatility_scenario=scenario,
                )
                gross_pnl = value - execution.theoretical_mid
                net_pnl = value - execution.total_entry_cost - round_trip.exit.total_exit_cost
                cells.append(
                    ScenarioCell(
                        spot=round(spot, 8),
                        horizon_days=horizon,
                        valuation_time=valuation_time,
                        volatility_scenario=scenario.name,
                        estimated_position_value=round(value, 8),
                        gross_pnl=round(gross_pnl, 8),
                        round_trip_cost=round_trip.total_round_trip_cost,
                        net_pnl=round(net_pnl, 8),
                        net_return=(net_pnl / capital if capital else None),
                        scenario_status=status.value,
                        assumptions=list(scenario.assumptions),
                    )
                )
        matrices.append(
            ScenarioMatrix(
                scenario_name=scenario.name,
                scenario_type=scenario.scenario_type,
                scenario_status=status,
                spot_axis=actual_spots,
                horizon_days_axis=horizons,
                cells=cells,
                warnings=(
                    ["Surface stress failed available static-arbitrage diagnostics"]
                    if status is VolatilityScenarioStatus.SURFACE_STRESS_INVALID
                    else ["Stress is leg-level only; it is not a calibrated surface forecast"]
                    if status is VolatilityScenarioStatus.LEG_LEVEL_STRESS_ONLY
                    else []
                ),
            )
        )
    return matrices


def build_rate_stress_results(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    round_trip: RoundTripCost,
) -> list[RateStressResult]:
    """Reprice the position under every configured base/shape rate scenario."""
    execution = candidate.execution_estimate
    if execution is None:
        raise ValueError("candidate execution estimate is required")
    output: list[RateStressResult] = []
    for scenario in bundle.trade_economics.rate_stresses:
        value = reprice_position(
            candidate,
            bundle,
            spot=bundle.underlying.price,
            valuation_time=bundle.analysis_timestamp,
            rate_scenario=scenario,
        )
        gross_pnl = value - execution.theoretical_mid
        net_pnl = value - execution.total_entry_cost - round_trip.exit.total_exit_cost
        shifts = {
            quote.contract.local_symbol: _rate_shift_for_expiry(
                scenario,
                valuation_time=bundle.analysis_timestamp,
                expiration=quote.contract.expiration,
            )
            for _, quote in _option_legs(candidate)
        }
        output.append(
            RateStressResult(
                scenario_name=scenario.name,
                scenario_type=scenario.scenario_type,
                status="CONFIGURED_STRESS",
                leg_rate_shifts_basis_points=shifts,
                estimated_position_value=round(value, 8),
                gross_pnl=round(gross_pnl, 8),
                round_trip_cost=round_trip.total_round_trip_cost,
                net_pnl=round(net_pnl, 8),
                assumptions=list(scenario.assumptions),
            )
        )
    return output


def solve_breakeven_regions(
    evaluator: Callable[[float], float],
    *,
    minimum_spot: float,
    maximum_spot: float,
    config: BreakevenSolverConfiguration,
) -> tuple[list[float], list[ProfitInterval]]:
    """Find all sign-changing roots and profitable intervals on a declared domain."""
    if minimum_spot < 0 or maximum_spot <= minimum_spot:
        raise ValueError("invalid breakeven search domain")
    step = (maximum_spot - minimum_spot) / (config.grid_points - 1)
    grid = [minimum_spot + index * step for index in range(config.grid_points)]
    values = [evaluator(spot) for spot in grid]
    roots: list[float] = []

    def add_root(root: float) -> None:
        deduplication_distance = max(config.root_tolerance * 10, step * 0.5)
        if roots and abs(root - roots[-1]) <= deduplication_distance:
            roots[-1] = (roots[-1] + root) / 2.0
        else:
            roots.append(root)

    for index, (left, right) in enumerate(zip(grid, grid[1:], strict=False)):
        left_value = values[index]
        right_value = values[index + 1]
        if abs(left_value) <= config.pnl_tolerance:
            add_root(left)
        elif left_value * right_value < 0:
            low, high = left, right
            low_value = left_value
            for _ in range(config.maximum_iterations):
                midpoint = (low + high) / 2.0
                midpoint_value = evaluator(midpoint)
                if (
                    abs(midpoint_value) <= config.pnl_tolerance
                    or high - low <= config.root_tolerance
                ):
                    low = high = midpoint
                    break
                if low_value * midpoint_value <= 0:
                    high = midpoint
                else:
                    low = midpoint
                    low_value = midpoint_value
            add_root((low + high) / 2.0)
    if abs(values[-1]) <= config.pnl_tolerance:
        add_root(grid[-1])
    boundaries = [minimum_spot, *roots, maximum_spot]
    intervals: list[ProfitInterval] = []
    for index, (left, right) in enumerate(zip(boundaries, boundaries[1:], strict=False)):
        midpoint = (left + right) / 2.0
        if evaluator(midpoint) > config.pnl_tolerance:
            upper: float | None = right
            if index == len(boundaries) - 2 and evaluator(maximum_spot) > 0:
                upper = None
            intervals.append(ProfitInterval(lower=max(left, 0.0), upper=upper))
    return roots, intervals


def build_breakeven_clock(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    exit_cost: ExitCostEstimate,
) -> BreakevenClock | None:
    execution = candidate.execution_estimate
    expiration = _effective_expiration(candidate)
    if execution is None or expiration is None:
        return None
    solver = bundle.trade_economics.breakeven_solver
    targets = [
        bundle.underlying.price * solver.maximum_spot_multiplier,
        *(quote.contract.strike * 1.5 for _, quote in _option_legs(candidate)),
        *(value * 1.5 for value in bundle.trade_economics.target_spots),
    ]
    maximum_spot = max(targets)
    minimum_spot = bundle.underlying.price * solver.minimum_spot_multiplier
    results: list[BreakevenResult] = []
    for scenario in bundle.trade_economics.volatility_scenarios[:3]:
        for horizon in [0, *_scenario_horizons(candidate, bundle)]:
            valuation_time = min(bundle.analysis_timestamp + timedelta(days=horizon), expiration)

            def evaluator(
                spot: float,
                *,
                evaluation_time: datetime = valuation_time,
                volatility_scenario: VolatilityScenario = scenario,
            ) -> float:
                return (
                    reprice_position(
                        candidate,
                        bundle,
                        spot=spot,
                        valuation_time=evaluation_time,
                        volatility_scenario=volatility_scenario,
                    )
                    - execution.total_entry_cost
                    - exit_cost.total_exit_cost
                )

            roots, intervals = solve_breakeven_regions(
                evaluator,
                minimum_spot=minimum_spot,
                maximum_spot=maximum_spot,
                config=solver,
            )
            results.append(
                BreakevenResult(
                    horizon_days=horizon,
                    valuation_time=valuation_time,
                    volatility_scenario=scenario.name,
                    break_even_roots=[round(value, 8) for value in roots],
                    profit_intervals=intervals,
                    status="SOLVED" if roots else "NO_ROOT_IN_DOMAIN",
                    search_domain=(minimum_spot, maximum_spot),
                    warnings=(
                        ["No root was found inside the configured search domain"]
                        if not roots
                        else []
                    ),
                )
            )
    return BreakevenClock(
        results=results,
        assumptions=[
            "Net PnL includes entry cost and the configured estimated exit cost.",
            "Roots and profit intervals are solved from full repricing on a configured domain.",
        ],
    )


def build_target_arrivals(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    exit_cost: ExitCostEstimate,
) -> list[TargetArrivalResult]:
    execution = candidate.execution_estimate
    expiration = _effective_expiration(candidate)
    if execution is None or expiration is None:
        return []
    targets = sorted(
        {
            *bundle.trade_economics.target_spots,
            *(scenario.target_price for scenario in bundle.fundamental.scenarios),
        }
    )
    maximum_days = max(
        math.ceil((expiration - bundle.analysis_timestamp).total_seconds() / _SECONDS_PER_DAY),
        0,
    )
    output: list[TargetArrivalResult] = []
    for scenario in bundle.trade_economics.volatility_scenarios[:3]:
        for target in targets:
            flags: list[bool] = []
            for day in range(maximum_days + 1):
                valuation_time = min(bundle.analysis_timestamp + timedelta(days=day), expiration)
                pnl = (
                    reprice_position(
                        candidate,
                        bundle,
                        spot=target,
                        valuation_time=valuation_time,
                        volatility_scenario=scenario,
                    )
                    - execution.total_entry_cost
                    - exit_cost.total_exit_cost
                )
                flags.append(pnl >= 0)
            profitable = [index for index, value in enumerate(flags) if value]
            segments = sum(
                value and (index == 0 or not flags[index - 1])
                for index, value in enumerate(flags)
            )
            if not profitable:
                status = TargetArrivalStatus.NEVER_BREAKEVEN_AT_THIS_TARGET
                latest = None
            elif segments > 1:
                status = TargetArrivalStatus.NON_MONOTONIC_TIME_RELATION
                latest = bundle.analysis_timestamp + timedelta(days=profitable[-1])
            elif flags[-1]:
                status = TargetArrivalStatus.PROFITABLE_THROUGH_EXPIRY
                latest = expiration
            else:
                status = TargetArrivalStatus.LATEST_PROFITABLE_ARRIVAL
                latest = bundle.analysis_timestamp + timedelta(days=profitable[-1])
            output.append(
                TargetArrivalResult(
                    target_spot=target,
                    volatility_scenario=scenario.name,
                    status=status,
                    latest_profitable_arrival_date=latest,
                    profitable_horizons_days=profitable,
                )
            )
    return output


def calculate_fx_attribution(
    *,
    option_pnl_usd: float,
    mode: FXHandlingMode,
    entry_fx_rate_usd_per_base: float | None,
    scenario_fx_rate_usd_per_base: float | None,
    conversion_fee_bps: float | None = None,
) -> FXAttribution:
    if mode is FXHandlingMode.UNKNOWN:
        return FXAttribution(
            mode=mode,
            option_pnl_usd=option_pnl_usd,
            status="BLOCKED_UNKNOWN_FX_HANDLING",
            warnings=["FX handling is unknown; no conversion fee or contribution is invented"],
        )
    if entry_fx_rate_usd_per_base is None or scenario_fx_rate_usd_per_base is None:
        raise ValueError("known FX handling requires entry and scenario rates")
    scenario = option_pnl_usd / scenario_fx_rate_usd_per_base
    constant = option_pnl_usd / entry_fx_rate_usd_per_base
    fee = (
        abs(scenario) * conversion_fee_bps / 10_000.0
        if conversion_fee_bps is not None
        else None
    )
    return FXAttribution(
        mode=mode,
        option_pnl_usd=option_pnl_usd,
        entry_fx_rate_usd_per_base=entry_fx_rate_usd_per_base,
        scenario_fx_rate_usd_per_base=scenario_fx_rate_usd_per_base,
        pnl_base_at_scenario_fx=scenario,
        pnl_base_at_constant_entry_fx=constant,
        fx_contribution_base=scenario - constant,
        fx_conversion_fees_base=fee,
        status="AVAILABLE",
    )


def calculate_touch_probability(
    paths: Sequence[Sequence[float]] | None,
    *,
    target: float,
    direction: TouchDirection,
    horizon_days: int,
    model: str | None,
    measure: Measure | None,
    calibration_status: ProbabilityStatus,
    minimum_paths: int = 1_000,
) -> TouchProbabilityMetrics:
    unavailable = calibration_status in {
        ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE,
        ProbabilityStatus.PROBABILITY_MODEL_NOT_PROMOTED,
    }
    if paths is None or unavailable:
        status = (
            calibration_status
            if unavailable
            else ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE
        )
        return TouchProbabilityMetrics(
            target=target,
            direction=direction,
            horizon_days=horizon_days,
            model=model,
            calibration_status=status,
            reason=status.value,
        )
    if measure is not Measure.REAL_WORLD:
        raise ValueError("P(touch) for a forecast ticket requires measure P")
    if not paths or any(len(path) < 2 for path in paths):
        raise ValueError("touch probability requires non-empty paths with at least two points")
    touched: list[bool] = []
    terminal_above: list[bool] = []
    first_touch_times: list[float] = []
    for path in paths:
        terminal_above.append(path[-1] >= target)
        indices = [
            index
            for index, value in enumerate(path)
            if (value >= target if direction is TouchDirection.UPPER else value <= target)
        ]
        touched.append(bool(indices))
        if indices:
            first_touch_times.append(indices[0] * horizon_days / (len(path) - 1))
    successes = sum(touched)
    probability_touch = successes / len(paths)
    lower, upper = wilson_interval(successes, len(paths), 0.95)
    reason = None
    if len(paths) < minimum_paths:
        reason = f"ESS_BELOW_CONFIGURED_MINIMUM:{len(paths)}<{minimum_paths}"
    return TouchProbabilityMetrics(
        target=target,
        direction=direction,
        horizon_days=horizon_days,
        probability_touch=probability_touch,
        probability_terminal_above=sum(terminal_above) / len(paths),
        probability_terminal_below=sum(not value for value in terminal_above) / len(paths),
        first_touch_count=successes,
        median_first_touch_time_conditional_on_touch=(
            median(first_touch_times) if first_touch_times else None
        ),
        confidence_interval_touch=(lower, upper),
        effective_sample_size=float(len(paths)),
        model=model,
        calibration_status=calibration_status,
        reason=reason,
    )


def _shapley_attribution(
    factors: tuple[str, ...],
    value: Callable[[frozenset[str]], float],
) -> dict[str, float]:
    count = len(factors)
    factorial = math.factorial
    contributions = {factor: 0.0 for factor in factors}
    for factor in factors:
        others = [item for item in factors if item != factor]
        for size in range(len(others) + 1):
            weight = factorial(size) * factorial(count - size - 1) / factorial(count)
            for subset_items in combinations(others, size):
                subset = frozenset(subset_items)
                contributions[factor] += weight * (
                    value(subset | {factor}) - value(subset)
                )
    return contributions


def build_pnl_attribution(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    aggregate: AdvancedGreeks,
    round_trip: RoundTripCost,
    scenario: VolatilityScenario,
    horizon_days: int,
    rate_scenario: RateScenario | None = None,
) -> PnLAttribution:
    expiration = _effective_expiration(candidate)
    target_time = bundle.analysis_timestamp + timedelta(days=horizon_days)
    if expiration is not None:
        target_time = min(target_time, expiration)
    target_spot = _scenario_spot(bundle.underlying.price, scenario)
    config = bundle.trade_economics
    factors = ("spot", "time", "volatility", "rates", "fx")
    cache: dict[frozenset[str], float] = {}

    def state_value(active: frozenset[str]) -> float:
        if active in cache:
            return cache[active]
        spot = target_spot if "spot" in active else bundle.underlying.price
        valuation_time = target_time if "time" in active else bundle.analysis_timestamp
        selected_scenario = scenario if "volatility" in active else None
        amount = reprice_position(
            candidate,
            bundle,
            spot=spot,
            valuation_time=valuation_time,
            volatility_scenario=selected_scenario,
            rate_scenario=rate_scenario if "rates" in active else None,
        )
        if (
            "fx" in active
            and config.fx_mode is not FXHandlingMode.UNKNOWN
            and config.scenario_fx_rate_usd_per_base is not None
        ):
            amount /= config.scenario_fx_rate_usd_per_base
        elif (
            config.fx_mode is not FXHandlingMode.UNKNOWN
            and config.entry_fx_rate_usd_per_base is not None
        ):
            amount /= config.entry_fx_rate_usd_per_base
        cache[active] = amount
        return amount

    start = state_value(frozenset())
    end = state_value(frozenset(factors))
    contributions = _shapley_attribution(factors, state_value)
    execution_costs = -round_trip.total_round_trip_cost
    full_pnl = end - start + execution_costs
    shapley_sum = sum(contributions.values()) + execution_costs
    full_residual = full_pnl - shapley_sum
    delta_spot = target_spot - bundle.underlying.price
    leg_shifts = []
    for _, quote in _option_legs(candidate):
        base_vol = effective_volatility(bundle, quote).volatility
        target_vol = _scenario_volatility(
            quote,
            bundle,
            scenario,
            spot=target_spot,
            valuation_time=target_time,
        )
        leg_shifts.append((target_vol - base_vol) * 100.0)
    delta_vol_points = sum(leg_shifts) / len(leg_shifts) if leg_shifts else 0.0
    rate_shifts = (
        [
            _rate_shift_for_expiry(
                rate_scenario,
                valuation_time=bundle.analysis_timestamp,
                expiration=quote.contract.expiration,
            )
            for _, quote in _option_legs(candidate)
        ]
        if rate_scenario is not None
        else []
    )
    delta_rate_points = (
        sum(rate_shifts) / len(rate_shifts) / 100.0 if rate_shifts else 0.0
    )
    delta_days = (target_time - bundle.analysis_timestamp).total_seconds() / _SECONDS_PER_DAY
    delta_component = aggregate.delta.value * delta_spot
    gamma_component = 0.5 * aggregate.gamma.value * delta_spot * delta_spot
    theta_component = aggregate.theta.value * delta_days
    vega_component = aggregate.vega.value * delta_vol_points
    vomma_component = 0.5 * aggregate.vomma.value * delta_vol_points * delta_vol_points
    vanna_component = aggregate.vanna.value * delta_spot * delta_vol_points
    rho_component = aggregate.rho.value * delta_rate_points
    approximation = (
        delta_component
        + gamma_component
        + theta_component
        + vega_component
        + vomma_component
        + vanna_component
        + rho_component
        + execution_costs
    )
    return PnLAttribution(
        scenario_name=(
            f"{scenario.name}_{rate_scenario.name}_{horizon_days}d"
            if rate_scenario is not None
            else f"{scenario.name}_{horizon_days}d"
        ),
        taylor=GreekTaylorAttribution(
            delta=delta_component,
            gamma=gamma_component,
            theta=theta_component,
            vega=vega_component,
            vomma=vomma_component,
            vanna=vanna_component,
            rho=rho_component,
            execution_costs=execution_costs,
            greek_approximated_pnl=approximation,
            full_repriced_pnl=full_pnl,
            residual=full_pnl - approximation,
        ),
        full_repricing=FullRepricingAttribution(
            spot=contributions["spot"],
            time=contributions["time"],
            volatility=contributions["volatility"],
            rates=contributions["rates"],
            fx=contributions["fx"],
            execution_costs=execution_costs,
            other=0.0,
            residual=full_residual,
            full_repriced_pnl=full_pnl,
        ),
    )


def _intensity(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    leverage: LeverageDiagnostics,
    time_decay: TimeDecayExposure | None,
    round_trip: RoundTripCost,
    aggregate: AdvancedGreeks | None,
    event_sensitivity: float | None,
) -> TradeIntensityDiagnostics:
    capital, _ = _capital_at_risk(candidate)
    thresholds = bundle.trade_economics.intensity_thresholds
    effective = leverage.delta_notional_leverage
    loss_30 = (
        max(-(time_decay.flat_spot_30d or 0.0) / capital, 0.0)
        if time_decay is not None and capital
        else None
    )
    loss_60 = (
        max(-(time_decay.flat_spot_60d or 0.0) / capital, 0.0)
        if time_decay is not None and capital
        else None
    )
    cost_fraction = round_trip.total_round_trip_cost / capital if capital else None
    triggered: list[str] = []
    category = TradeIntensityCategory.LOW
    if (
        (effective is not None and effective >= thresholds.extreme_effective_leverage)
        or (
            loss_30 is not None
            and loss_30 >= thresholds.extreme_flat_spot_30d_loss_fraction
        )
        or (
            cost_fraction is not None
            and cost_fraction >= thresholds.extreme_round_trip_cost_fraction
        )
    ):
        category = TradeIntensityCategory.EXTREME
        triggered.append("extreme_configured_policy_threshold")
    elif (
        (effective is not None and effective >= thresholds.high_effective_leverage)
        or (
            loss_30 is not None
            and loss_30 >= thresholds.high_flat_spot_30d_loss_fraction
        )
        or (
            cost_fraction is not None
            and cost_fraction >= thresholds.high_round_trip_cost_fraction
        )
    ):
        category = TradeIntensityCategory.HIGH
        triggered.append("high_configured_policy_threshold")
    elif any(value and value > 0 for value in (effective, loss_30, cost_fraction)):
        category = TradeIntensityCategory.MODERATE
    levels = (
        [item.confidence_level for item in aggregate.confidence]
        if aggregate is not None
        else [GreekConfidenceLevel.UNRELIABLE]
    )
    maximum_loss = candidate.risk_metrics.max_loss if candidate.risk_metrics else None
    return TradeIntensityDiagnostics(
        effective_leverage=effective,
        capital_at_risk_pct=(capital / bundle.portfolio.max_loss_budget if capital else None),
        theta_per_capital_per_day=(
            time_decay.theta_per_capital_per_day if time_decay is not None else None
        ),
        flat_spot_30d_loss_pct=loss_30,
        flat_spot_60d_loss_pct=loss_60,
        spread_over_entry_capital_pct=cost_fraction,
        greek_instability=_worst_confidence(levels),
        event_iv_sensitivity=event_sensitivity,
        max_loss_pct=(
            maximum_loss / bundle.portfolio.max_loss_budget
            if maximum_loss is not None
            else None
        ),
        category=category,
        triggered_policies=triggered,
    )


def build_trade_economics_ticket(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    fixture_status: Literal[
        "LIVE_INPUT", "SYNTHETIC_TEST_FIXTURE", "RESEARCH_FIXTURE"
    ] = "RESEARCH_FIXTURE",
    probability_paths: Sequence[Sequence[float]] | None = None,
    probability_measure: Measure | None = None,
    probability_model: str | None = None,
    probability_calibration_status: ProbabilityStatus = (
        ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE
    ),
    probability_horizon_days: int | None = None,
) -> TradeEconomicsTicket:
    """Build one reconciled M0 ticket without creating any execution capability."""
    validate_dividend_treatment(bundle)
    if candidate.risk_metrics is None or candidate.execution_estimate is None:
        analyze_risk(candidate, bundle)
    assert candidate.risk_metrics is not None
    assert candidate.execution_estimate is not None
    leg_greeks: dict[int, AdvancedGreeks] = {}
    legs: list[LegEconomics] = []
    for index, leg in enumerate(candidate.legs):
        if leg.option_quote is None:
            assert leg.stock_price is not None
            premium = leg.quantity * leg.stock_price
            legs.append(
                LegEconomics(
                    side=leg.side.value,
                    quantity=leg.quantity,
                    instrument_type="stock",
                    multiplier=1.0,
                    premium_paid=premium if leg.side is PositionSide.LONG else 0.0,
                    premium_received=premium if leg.side is PositionSide.SHORT else 0.0,
                )
            )
            continue
        quote = leg.option_quote
        advanced = calculate_leg_advanced_greeks(quote, bundle, side=leg.side)
        leg_greeks[index] = advanced
        mid = quote.mid
        if mid is None:
            raise ValueError("BLOCKED_EXECUTION_DATA: two-sided quote required for ticket")
        premium = leg.quantity * quote.contract.multiplier * mid
        legs.append(
            LegEconomics(
                side=leg.side.value,
                quantity=leg.quantity,
                instrument_type="option",
                option_type=quote.contract.option_type.value,
                strike=quote.contract.strike,
                expiration=quote.contract.expiration,
                bid=quote.bid,
                ask=quote.ask,
                mid=mid,
                implied_volatility=effective_volatility(bundle, quote).volatility,
                multiplier=quote.contract.multiplier,
                premium_paid=premium if leg.side is PositionSide.LONG else 0.0,
                premium_received=premium if leg.side is PositionSide.SHORT else 0.0,
                con_id=quote.contract.con_id,
                local_symbol=quote.contract.local_symbol,
                trading_class=quote.contract.trading_class,
                deliverable=quote.contract.deliverable,
                exercise_style=quote.contract.exercise_style.value,
                settlement=quote.contract.settlement_cycle,
                adjusted_contract=quote.contract.adjusted_contract,
                greeks=advanced,
            )
        )
    aggregate = aggregate_advanced_greeks(candidate, bundle, leg_greeks)
    leverage = calculate_leverage(candidate, bundle, aggregate, leg_greeks)
    exit_cost = build_exit_cost_estimate(candidate, bundle)
    round_trip = build_round_trip_cost(candidate, exit_cost)
    time_decay = calculate_time_decay_exposure(candidate, bundle, aggregate=aggregate)
    matrices = build_scenario_matrices(candidate, bundle, round_trip=round_trip)
    rate_stresses = build_rate_stress_results(candidate, bundle, round_trip=round_trip)
    breakeven_clock = build_breakeven_clock(candidate, bundle, exit_cost=exit_cost)
    target_arrivals = build_target_arrivals(candidate, bundle, exit_cost=exit_cost)
    attributions: list[PnLAttribution] = []
    if aggregate is not None:
        horizon = min(30, max(_scenario_horizons(candidate, bundle), default=0))
        attribution_volatility_scenarios = bundle.trade_economics.volatility_scenarios[:3]
        for scenario in attribution_volatility_scenarios:
            attributions.append(
                build_pnl_attribution(
                    candidate,
                    bundle,
                    aggregate=aggregate,
                    round_trip=round_trip,
                    scenario=scenario,
                    horizon_days=horizon,
                )
            )
        base_volatility_scenario = attribution_volatility_scenarios[0]
        for rate_scenario in bundle.trade_economics.rate_stresses:
            if rate_scenario.scenario_type is RateScenarioType.BASE_CURVE:
                continue
            attributions.append(
                build_pnl_attribution(
                    candidate,
                    bundle,
                    aggregate=aggregate,
                    round_trip=round_trip,
                    scenario=base_volatility_scenario,
                    horizon_days=horizon,
                    rate_scenario=rate_scenario,
                )
            )
    targets = sorted(
        {
            *bundle.trade_economics.touch_targets,
            *bundle.trade_economics.target_spots,
        }
    )
    if probability_paths is not None and probability_horizon_days is None:
        raise ValueError("probability paths require their explicit horizon in calendar days")
    if probability_paths is not None and probability_measure is not Measure.REAL_WORLD:
        raise ValueError("ticket probability paths require measure P")
    if probability_paths is not None and probability_calibration_status in {
        ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE,
        ProbabilityStatus.PROBABILITY_MODEL_NOT_PROMOTED,
    }:
        raise ValueError("available paths require an available probability-model status")
    probability_status = probability_calibration_status
    touch = [
        calculate_touch_probability(
            probability_paths,
            target=target,
            direction=(
                TouchDirection.UPPER
                if target >= bundle.underlying.price
                else TouchDirection.LOWER
            ),
            horizon_days=(
                probability_horizon_days
                if probability_horizon_days is not None
                else max(_scenario_horizons(candidate, bundle), default=1)
            ),
            model=probability_model,
            measure=probability_measure,
            calibration_status=probability_status,
        )
        for target in targets
    ]
    base_value = reprice_position(
        candidate,
        bundle,
        spot=bundle.underlying.price,
        valuation_time=bundle.analysis_timestamp,
    )
    option_pnl = base_value - candidate.execution_estimate.total_entry_cost
    fx = calculate_fx_attribution(
        option_pnl_usd=option_pnl,
        mode=bundle.trade_economics.fx_mode,
        entry_fx_rate_usd_per_base=bundle.trade_economics.entry_fx_rate_usd_per_base,
        scenario_fx_rate_usd_per_base=bundle.trade_economics.scenario_fx_rate_usd_per_base,
        conversion_fee_bps=bundle.trade_economics.exit_cost_model.fx_exit_cost_bps,
    )
    event_sensitivity = None
    if aggregate is not None:
        event_scenarios = [
            scenario
            for scenario in bundle.trade_economics.volatility_scenarios
            if scenario.scenario_type is VolatilityScenarioType.EVENT_IV_CRUSH
        ]
        if event_scenarios:
            event_value = reprice_position(
                candidate,
                bundle,
                spot=bundle.underlying.price,
                valuation_time=bundle.analysis_timestamp,
                volatility_scenario=event_scenarios[0],
            )
            event_sensitivity = event_value - base_value
    intensity = _intensity(
        candidate,
        bundle,
        leverage=leverage,
        time_decay=time_decay,
        round_trip=round_trip,
        aggregate=aggregate,
        event_sensitivity=event_sensitivity,
    )
    expirations = sorted({quote.contract.expiration for _, quote in _option_legs(candidate)})
    expiration = min(expirations) if expirations else None
    dte = (
        max((expiration - bundle.analysis_timestamp).total_seconds() / _SECONDS_PER_DAY, 0.0)
        if expiration is not None
        else 0.0
    )
    statuses = [item.intraday_precision_status for item in candidate.pricing_results]
    if IntradayPrecisionStatus.INSUFFICIENT_NEAR_EXPIRY in statuses:
        intraday_status = IntradayPrecisionStatus.INSUFFICIENT_NEAR_EXPIRY
    elif statuses:
        intraday_status = IntradayPrecisionStatus.APPROXIMATED_DATE_ENGINE
    else:
        intraday_status = IntradayPrecisionStatus.NOT_APPLICABLE
    intraday_warning = (
        "American FD engine uses date-level exercise grid; intraday exposure is approximate."
        if intraday_status is not IntradayPrecisionStatus.NOT_APPLICABLE
        else None
    )
    blockers: list[str] = []
    margin = _margin(candidate)
    if margin.status in {MarginStatus.UNKNOWN, MarginStatus.BLOCKED}:
        blockers.append("BLOCKED_UNKNOWN_MARGIN")
    if any(
        leg.option_quote is not None
        and (
            not leg.option_quote.contract.adjustment_understood
            or not leg.option_quote.contract.deliverable
        )
        for leg in candidate.legs
    ):
        blockers.append("BLOCKED_CONTRACT_METADATA")
    assignment = [
        (
            f"{risk.contract_symbol}: assignment={risk.assignment_risk.value}; "
            f"early_exercise={risk.early_exercise_risk.value}; pin={risk.pin_risk.value}; "
            f"adjusted_contract={risk.adjusted_contract}; human_review="
            f"{risk.human_review_required}"
        )
        for risk in candidate.exercise_risks
    ]
    capital, _ = _capital_at_risk(candidate)
    ticket = TradeEconomicsTicket(
        fixture_status=fixture_status,
        candidate_id=candidate.id,
        underlying=bundle.underlying.ticker,
        strategy_name=candidate.name,
        exact_market_timestamp=bundle.analysis_timestamp,
        currency=bundle.underlying.currency,
        data_freshness_status=bundle.underlying.freshness.status.value,
        expirations=expirations,
        dte_exact_days=dte,
        intraday_precision_status=intraday_status,
        intraday_precision_warning=intraday_warning,
        legs=legs,
        entry_cost=_entry_cost(candidate),
        exit_cost_estimate=exit_cost,
        round_trip_cost=round_trip,
        margin=margin,
        maximum_loss=candidate.risk_metrics.max_loss,
        maximum_profit=candidate.risk_metrics.max_gain,
        expiration_breakevens=candidate.risk_metrics.break_even_points,
        capital_at_risk=capital,
        leverage=leverage,
        time_decay=time_decay,
        aggregate_greeks=aggregate,
        breakeven_clock=breakeven_clock,
        target_arrivals=target_arrivals,
        scenario_matrices=matrices,
        rate_stress_results=rate_stresses,
        touch_probabilities=touch,
        pnl_attributions=attributions,
        fx_attribution=fx,
        liquidity=_liquidity_diagnostics(candidate, bundle),
        intensity=intensity,
        assignment_and_exercise_risks=assignment,
        classification=candidate.status.value,
        blockers=blockers,
        warnings=[
            *candidate.assumptions,
            "Full repricing is primary; Greek/Taylor attribution is explanatory only.",
            "All leg-level execution estimates are indicative until combo evidence exists.",
        ],
        data_status="BLOCKED" if blockers else "AVAILABLE_RESEARCH_ONLY",
        probability_status=probability_status,
        transmit=False,
        what_if=True,
        order_capability="forbidden",
    )
    candidate.trade_economics = ticket
    return ticket
