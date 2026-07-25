"""American-option pricing and explainable exercise-risk assessment."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from functools import lru_cache

import QuantLib as ql  # type: ignore[import-untyped]
from pydantic import Field

from take_two_options.domain import (
    AmericanPricingResult,
    ExerciseRiskAssessment,
    ExerciseStyle,
    MarketDataBundle,
    OptionQuote,
    OptionType,
    PositionSide,
    PricingModel,
    RiskLevel,
    StrategyCandidate,
    StrictModel,
)
from take_two_options.vol_surface import effective_volatility


def _ql_date(value: date) -> ql.Date:
    return ql.Date(value.day, value.month, value.year)


def _intrinsic(spot: float, strike: float, option_type: OptionType) -> float:
    if option_type is OptionType.CALL:
        return max(spot - strike, 0.0)
    return max(strike - spot, 0.0)


@lru_cache(maxsize=16_384)
def _quantlib_value(
    *,
    spot: float,
    strike: float,
    valuation_date: date,
    expiration_date: date,
    rate: float,
    volatility: float,
    option_type: str,
    dividend_yield: float,
    dividends: tuple[tuple[date, float], ...],
    american: bool,
    time_grid: int,
    price_grid: int,
) -> float:
    if valuation_date >= expiration_date:
        return _intrinsic(spot, strike, OptionType(option_type))

    evaluation = _ql_date(valuation_date)
    expiration = _ql_date(expiration_date)
    ql.Settings.instance().evaluationDate = evaluation
    day_count = ql.Actual365Fixed()
    calendar = ql.NullCalendar()
    spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
    dividend_curve = ql.YieldTermStructureHandle(
        ql.FlatForward(evaluation, dividend_yield, day_count)
    )
    risk_free_curve = ql.YieldTermStructureHandle(ql.FlatForward(evaluation, rate, day_count))
    volatility_curve = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(evaluation, calendar, volatility, day_count)
    )
    process = ql.BlackScholesMertonProcess(
        spot_handle,
        dividend_curve,
        risk_free_curve,
        volatility_curve,
    )
    payoff_type = ql.Option.Call if option_type == OptionType.CALL.value else ql.Option.Put
    payoff = ql.PlainVanillaPayoff(payoff_type, strike)
    exercise = (
        ql.AmericanExercise(evaluation, expiration) if american else ql.EuropeanExercise(expiration)
    )
    option = ql.VanillaOption(payoff, exercise)
    active_dividends = [
        (ex_date, amount)
        for ex_date, amount in dividends
        if valuation_date < ex_date <= expiration_date
    ]
    schedule = ql.DividendVector(
        [_ql_date(ex_date) for ex_date, _ in active_dividends],
        [amount for _, amount in active_dividends],
    )
    option.setPricingEngine(
        ql.FdBlackScholesVanillaEngine(
            process,
            schedule,
            time_grid,
            price_grid,
        )
    )
    return max(float(option.NPV()), 0.0)


class HistoricalOptionAnalytics(StrictModel):
    model: str = "quantlib_fd_american"
    price_input: str = "mid"
    target_price: float = Field(gt=0)
    model_price: float = Field(ge=0)
    implied_volatility: float = Field(gt=0, le=5)
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    risk_free_rate: float
    continuous_dividend_yield: float
    dividend_count: int = Field(ge=0)


def american_scenario_value(
    *,
    spot: float,
    strike: float,
    valuation_date: date,
    expiration_date: date,
    option_type: OptionType,
    volatility: float,
    rate: float,
    dividend_yield: float = 0.0,
    dividends: tuple[tuple[date, float], ...] = (),
    time_grid: int = 100,
    price_grid: int = 100,
) -> float:
    """Return an American scenario value from the shared cached QuantLib engine."""
    if spot <= 0 or strike <= 0 or volatility <= 0:
        raise ValueError("spot, strike, and volatility must be positive")
    return _quantlib_value(
        spot=round(spot, 10),
        strike=round(strike, 10),
        valuation_date=valuation_date,
        expiration_date=expiration_date,
        rate=round(rate, 10),
        volatility=round(volatility, 10),
        option_type=option_type.value,
        dividend_yield=round(dividend_yield, 10),
        dividends=dividends,
        american=True,
        time_grid=time_grid,
        price_grid=price_grid,
    )


def american_scenario_analytics(
    *,
    contract_symbol: str,
    spot: float,
    strike: float,
    valuation_date: date,
    expiration_date: date,
    option_type: OptionType,
    volatility: float,
    rate: float,
    dividend_yield: float = 0.0,
    dividends: tuple[tuple[date, float], ...] = (),
    time_grid: int = 100,
    price_grid: int = 100,
) -> AmericanPricingResult:
    """Price one American option scenario with the shared cached QuantLib engine."""
    if spot <= 0 or strike <= 0 or volatility <= 0:
        raise ValueError("spot, strike, and volatility must be positive")
    if valuation_date >= expiration_date:
        raise ValueError("valuation date must precede option expiration")

    def value(
        *,
        selected_spot: float = spot,
        selected_date: date = valuation_date,
        selected_volatility: float = volatility,
        selected_rate: float = rate,
        american: bool = True,
    ) -> float:
        return (
            american_scenario_value(
                spot=selected_spot,
                strike=strike,
                valuation_date=selected_date,
                expiration_date=expiration_date,
                rate=selected_rate,
                volatility=selected_volatility,
                option_type=option_type,
                dividend_yield=dividend_yield,
                dividends=dividends,
                time_grid=time_grid,
                price_grid=price_grid,
            )
            if american
            else _quantlib_value(
                spot=round(selected_spot, 10),
                strike=round(strike, 10),
                valuation_date=selected_date,
                expiration_date=expiration_date,
                rate=round(selected_rate, 10),
                volatility=round(selected_volatility, 10),
                option_type=option_type.value,
                dividend_yield=round(dividend_yield, 10),
                dividends=dividends,
                american=False,
                time_grid=time_grid,
                price_grid=price_grid,
            )
        )

    base = value()
    european = value(american=False)
    spot_step = max(spot * 0.001, 0.01)
    spot_up = value(selected_spot=spot + spot_step)
    spot_down = value(selected_spot=max(spot - spot_step, 0.01))
    delta = (spot_up - spot_down) / (2.0 * spot_step)
    gamma = (spot_up - 2.0 * base + spot_down) / (spot_step * spot_step)

    next_date = min(valuation_date + timedelta(days=1), expiration_date)
    theta = value(selected_date=next_date) - base
    vol_step = min(0.01, volatility * 0.25)
    vega = (
        (
            value(selected_volatility=volatility + vol_step)
            - value(selected_volatility=max(volatility - vol_step, 0.0001))
        )
        * 0.01
        / (2.0 * vol_step)
    )
    rate_step = 0.001
    rho = (
        (value(selected_rate=rate + rate_step) - value(selected_rate=rate - rate_step))
        * 0.01
        / (2.0 * rate_step)
    )
    premium = base - european
    active_dividends = [item for item in dividends if valuation_date < item[0] <= expiration_date]
    warnings = []
    if premium < -0.01:
        warnings.append("American value is below European benchmark beyond numerical tolerance")
    return AmericanPricingResult(
        contract_symbol=contract_symbol,
        valuation_time=datetime.combine(
            valuation_date,
            datetime.min.time(),
        ),
        model=PricingModel.QUANTLIB_FD_AMERICAN,
        price=round(base, 8),
        european_benchmark=round(european, 8),
        early_exercise_premium=round(premium, 8),
        delta=round(delta, 8),
        gamma=round(gamma, 8),
        theta=round(theta, 8),
        vega=round(vega, 8),
        rho=round(rho, 8),
        dividend_count=len(active_dividends),
        warnings=warnings,
    )


def historical_option_analytics(
    *,
    spot: float,
    strike: float,
    valuation_date: date,
    expiration_date: date,
    option_type: OptionType,
    target_price: float,
    rate: float,
    dividend_yield: float = 0.0,
    dividends: tuple[tuple[date, float], ...] = (),
    time_grid: int = 100,
    price_grid: int = 100,
) -> HistoricalOptionAnalytics:
    """Recover American IV from an EOD midpoint and calculate finite-difference Greeks."""
    if spot <= 0 or strike <= 0 or target_price <= 0:
        raise ValueError("spot, strike, and target price must be positive")
    if valuation_date >= expiration_date:
        raise ValueError("valuation date must precede option expiration")
    intrinsic = _intrinsic(spot, strike, option_type)
    if target_price < intrinsic - 0.01:
        raise ValueError("target option price is below intrinsic value")

    def value(
        volatility: float,
        *,
        selected_spot: float = spot,
        selected_date: date = valuation_date,
        selected_rate: float = rate,
    ) -> float:
        return _quantlib_value(
            spot=round(selected_spot, 10),
            strike=round(strike, 10),
            valuation_date=selected_date,
            expiration_date=expiration_date,
            rate=round(selected_rate, 10),
            volatility=round(volatility, 10),
            option_type=option_type.value,
            dividend_yield=round(dividend_yield, 10),
            dividends=dividends,
            american=True,
            time_grid=time_grid,
            price_grid=price_grid,
        )

    lower = 0.0001
    upper = 5.0
    lower_price = value(lower)
    upper_price = value(upper)
    tolerance = 1e-6
    if target_price < lower_price - 0.01 or target_price > upper_price + 0.01:
        raise ValueError("target option price is outside the supported IV range")

    implied_volatility = lower
    for _ in range(100):
        implied_volatility = (lower + upper) / 2.0
        candidate = value(implied_volatility)
        if abs(candidate - target_price) <= tolerance:
            break
        if candidate < target_price:
            lower = implied_volatility
        else:
            upper = implied_volatility

    base = value(implied_volatility)
    spot_step = max(spot * 0.001, 0.01)
    spot_up = value(implied_volatility, selected_spot=spot + spot_step)
    spot_down = value(implied_volatility, selected_spot=max(spot - spot_step, 0.01))
    delta = (spot_up - spot_down) / (2.0 * spot_step)
    gamma = (spot_up - 2.0 * base + spot_down) / (spot_step * spot_step)

    next_date = min(valuation_date + timedelta(days=1), expiration_date)
    theta = value(implied_volatility, selected_date=next_date) - base
    vol_step = min(0.01, implied_volatility * 0.25)
    vega = (
        value(implied_volatility + vol_step)
        - value(max(implied_volatility - vol_step, 0.0001))
    ) * 0.01 / (2.0 * vol_step)
    rate_step = 0.001
    rho = (
        value(implied_volatility, selected_rate=rate + rate_step)
        - value(implied_volatility, selected_rate=rate - rate_step)
    ) * 0.01 / (2.0 * rate_step)
    active_dividends = [
        item for item in dividends if valuation_date < item[0] <= expiration_date
    ]
    return HistoricalOptionAnalytics(
        target_price=round(target_price, 8),
        model_price=round(base, 8),
        implied_volatility=round(implied_volatility, 8),
        delta=round(delta, 8),
        gamma=round(gamma, 8),
        theta=round(theta, 8),
        vega=round(vega, 8),
        rho=round(rho, 8),
        risk_free_rate=rate,
        continuous_dividend_yield=dividend_yield,
        dividend_count=len(active_dividends),
    )


def option_model_value(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    *,
    spot: float | None = None,
    valuation_time: datetime | None = None,
    volatility: float | None = None,
    rate: float | None = None,
    force_european: bool = False,
) -> float:
    contract = quote.contract
    selected_spot = spot if spot is not None else bundle.underlying.price
    selected_time = valuation_time or bundle.analysis_timestamp
    selected_volatility = volatility or effective_volatility(bundle, quote).volatility
    selected_rate = rate if rate is not None else bundle.risk_free_rate
    dividends = tuple((item.ex_date, item.amount) for item in bundle.dividends)
    return _quantlib_value(
        spot=round(selected_spot, 10),
        strike=contract.strike,
        valuation_date=selected_time.date(),
        expiration_date=contract.expiration.date(),
        rate=round(selected_rate, 10),
        volatility=round(selected_volatility, 10),
        option_type=contract.option_type.value,
        dividend_yield=bundle.continuous_dividend_yield,
        dividends=dividends,
        american=(
            contract.exercise_style is ExerciseStyle.AMERICAN
            and bundle.pricing.american_model is PricingModel.QUANTLIB_FD_AMERICAN
            and not force_european
        ),
        time_grid=bundle.pricing.time_grid,
        price_grid=bundle.pricing.price_grid,
    )


def price_option_quote(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    *,
    spot: float | None = None,
    valuation_time: datetime | None = None,
    volatility: float | None = None,
    rate: float | None = None,
) -> AmericanPricingResult:
    selected_spot = spot if spot is not None else bundle.underlying.price
    selected_time = valuation_time or bundle.analysis_timestamp
    selected_volatility = volatility or effective_volatility(bundle, quote).volatility
    selected_rate = rate if rate is not None else bundle.risk_free_rate
    contract = quote.contract
    base = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate,
    )
    european = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate,
        force_european=True,
    )

    spot_step = max(selected_spot * 0.001, 0.01)
    spot_up = option_model_value(
        quote,
        bundle,
        spot=selected_spot + spot_step,
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate,
    )
    spot_down = option_model_value(
        quote,
        bundle,
        spot=max(selected_spot - spot_step, 0.01),
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate,
    )
    delta = (spot_up - spot_down) / (2.0 * spot_step)
    gamma = (spot_up - 2.0 * base + spot_down) / (spot_step * spot_step)

    next_time = min(selected_time + timedelta(days=1), contract.expiration)
    theta = (
        option_model_value(
            quote,
            bundle,
            spot=selected_spot,
            valuation_time=next_time,
            volatility=selected_volatility,
            rate=selected_rate,
        )
        - base
    )
    vol_step = min(0.01, selected_volatility * 0.25)
    vol_up = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=selected_volatility + vol_step,
        rate=selected_rate,
    )
    vol_down = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=max(selected_volatility - vol_step, 0.0001),
        rate=selected_rate,
    )
    vega = (vol_up - vol_down) * 0.01 / (2.0 * vol_step)
    rate_step = 0.001
    rate_up = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate + rate_step,
    )
    rate_down = option_model_value(
        quote,
        bundle,
        spot=selected_spot,
        valuation_time=selected_time,
        volatility=selected_volatility,
        rate=selected_rate - rate_step,
    )
    rho = (rate_up - rate_down) * 0.01 / (2.0 * rate_step)

    warnings: list[str] = []
    premium = base - european
    if premium < -0.01:
        warnings.append("American value is below European benchmark beyond numerical tolerance")
    if effective_volatility(bundle, quote).extrapolated:
        warnings.append("Volatility is extrapolated or uses a fallback")
    active_dividends = [
        item
        for item in bundle.dividends
        if selected_time.date() < item.ex_date <= contract.expiration.date()
    ]
    return AmericanPricingResult(
        contract_symbol=contract.local_symbol,
        valuation_time=selected_time,
        model=(
            bundle.pricing.american_model
            if contract.exercise_style is ExerciseStyle.AMERICAN
            else PricingModel.BLACK_SCHOLES_EUROPEAN
        ),
        price=round(base, 8),
        european_benchmark=round(european, 8),
        early_exercise_premium=round(premium, 8),
        delta=round(delta, 8),
        gamma=round(gamma, 8),
        theta=round(theta, 8),
        vega=round(vega, 8),
        rho=round(rho, 8),
        dividend_count=len(active_dividends),
        warnings=warnings,
    )


def assess_exercise_risk(
    quote: OptionQuote,
    bundle: MarketDataBundle,
    side: PositionSide,
    pricing: AmericanPricingResult,
) -> ExerciseRiskAssessment:
    contract = quote.contract
    spot = bundle.underlying.price
    intrinsic = _intrinsic(spot, contract.strike, contract.option_type)
    extrinsic = max(pricing.price - intrinsic, 0.0)
    days_to_expiry = max((contract.expiration.date() - bundle.analysis_timestamp.date()).days, 0)
    upcoming = sorted(
        (
            dividend
            for dividend in bundle.dividends
            if bundle.analysis_timestamp.date() < dividend.ex_date <= contract.expiration.date()
        ),
        key=lambda dividend: dividend.ex_date,
    )
    next_dividend = upcoming[0] if upcoming else None
    reasons: list[str] = []

    assignment = RiskLevel.LOW
    if side is PositionSide.SHORT and contract.exercise_style is ExerciseStyle.AMERICAN:
        reasons.append("Short American option can be assigned before expiration")
        if intrinsic > 0:
            assignment = RiskLevel.MEDIUM
            reasons.append("Option is in the money")
        low_extrinsic_threshold = max(0.05, spot * 0.0025)
        if intrinsic > 0 and extrinsic <= low_extrinsic_threshold and days_to_expiry <= 30:
            assignment = RiskLevel.HIGH
            reasons.append("Low extrinsic value and <=30 days to expiry increase exercise risk")
        if (
            contract.option_type is OptionType.CALL
            and next_dividend is not None
            and next_dividend.amount > extrinsic
        ):
            assignment = RiskLevel.HIGH
            reasons.append("Forecast dividend exceeds remaining call extrinsic value")

    pin = RiskLevel.LOW
    strike_distance = abs(spot - contract.strike)
    pin_threshold = max(0.50, spot * 0.005)
    if strike_distance <= pin_threshold and days_to_expiry <= 7:
        pin = RiskLevel.HIGH
        reasons.append("Spot is near strike with <=7 days to expiry")
    elif strike_distance <= 2.0 * pin_threshold and days_to_expiry <= 21:
        pin = RiskLevel.MEDIUM
        reasons.append("Spot is near strike with <=21 days to expiry")

    human_review = side is PositionSide.SHORT and contract.exercise_style is ExerciseStyle.AMERICAN
    if not reasons:
        reasons.append("No near-term exercise or pin trigger detected by the heuristic")
    return ExerciseRiskAssessment(
        contract_symbol=contract.local_symbol,
        side=side,
        assignment_risk=assignment,
        pin_risk=pin,
        intrinsic_value=round(intrinsic, 8),
        extrinsic_value=round(extrinsic, 8),
        days_to_expiry=days_to_expiry,
        next_ex_dividend_date=next_dividend.ex_date if next_dividend else None,
        reasons=reasons,
        human_review_required=human_review,
    )


def analyze_candidate_option_models(candidate: StrategyCandidate, bundle: MarketDataBundle) -> None:
    candidate.pricing_results = []
    candidate.exercise_risks = []
    for leg in candidate.legs:
        if leg.option_quote is None:
            continue
        pricing = price_option_quote(leg.option_quote, bundle)
        candidate.pricing_results.append(pricing)
        assessment = assess_exercise_risk(leg.option_quote, bundle, leg.side, pricing)
        candidate.exercise_risks.append(assessment)
        candidate.human_validation_required = (
            candidate.human_validation_required or assessment.human_review_required
        )


def clear_pricing_cache() -> None:
    _quantlib_value.cache_clear()


def american_premium_is_numerically_valid(result: AmericanPricingResult) -> bool:
    return result.early_exercise_premium >= -max(0.01, math.ulp(result.price) * 10)
