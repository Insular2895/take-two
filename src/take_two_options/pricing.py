"""Deterministic pricing, payoff, cost, and aggregate Greek calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from take_two_options.american import analyze_candidate_option_models
from take_two_options.domain import (
    ExecutionEstimate,
    MarketDataBundle,
    OptionQuote,
    OptionType,
    PayoffPoint,
    PositionSide,
    RiskMetrics,
    StrategyCandidate,
    StrategyKind,
)
from take_two_options.quantitative.contracts import (
    DEFAULT_QUANT_CONVENTIONS,
    Measure,
    require_measure,
)


@dataclass(frozen=True)
class Greeks:
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    measure: Measure = Measure.RISK_NEUTRAL


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def years_to_expiration(expiration: datetime, as_of: datetime) -> float:
    return max(DEFAULT_QUANT_CONVENTIONS.calendar_year_fraction(as_of, expiration), 1e-9)


def black_scholes_price_greeks(
    *,
    spot: float,
    strike: float,
    time_years: float,
    rate: float,
    volatility: float,
    option_type: OptionType,
    dividend_yield: float = 0.0,
    measure: Measure = Measure.RISK_NEUTRAL,
) -> Greeks:
    """Return European indicative Greeks per underlying share.

    Vega and rho are per one percentage-point move. Theta is per calendar day.
    """
    if spot <= 0 or strike <= 0 or volatility <= 0 or time_years <= 0:
        raise ValueError("positive spot, strike, volatility, and time are required")
    require_measure(measure, Measure.RISK_NEUTRAL, context="Black-Scholes pricing")

    sqrt_t = math.sqrt(time_years)
    d1 = (
        math.log(spot / strike)
        + (rate - dividend_yield + 0.5 * volatility * volatility) * time_years
    ) / (volatility * sqrt_t)
    d2 = d1 - volatility * sqrt_t
    discount_r = math.exp(-rate * time_years)
    discount_q = math.exp(-dividend_yield * time_years)
    pdf_d1 = _normal_pdf(d1)

    gamma = discount_q * pdf_d1 / (spot * volatility * sqrt_t)
    vega = spot * discount_q * pdf_d1 * sqrt_t * 0.01
    if option_type is OptionType.CALL:
        price = spot * discount_q * _normal_cdf(d1) - strike * discount_r * _normal_cdf(d2)
        delta = discount_q * _normal_cdf(d1)
        theta_annual = (
            -(spot * discount_q * pdf_d1 * volatility) / (2 * sqrt_t)
            - rate * strike * discount_r * _normal_cdf(d2)
            + dividend_yield * spot * discount_q * _normal_cdf(d1)
        )
        rho = strike * time_years * discount_r * _normal_cdf(d2) * 0.01
    else:
        price = strike * discount_r * _normal_cdf(-d2) - spot * discount_q * _normal_cdf(-d1)
        delta = discount_q * (_normal_cdf(d1) - 1)
        theta_annual = (
            -(spot * discount_q * pdf_d1 * volatility) / (2 * sqrt_t)
            + rate * strike * discount_r * _normal_cdf(-d2)
            - dividend_yield * spot * discount_q * _normal_cdf(-d1)
        )
        rho = -strike * time_years * discount_r * _normal_cdf(-d2) * 0.01

    return Greeks(
        price=price,
        delta=delta,
        gamma=gamma,
        theta=theta_annual / DEFAULT_QUANT_CONVENTIONS.calendar_day_basis,
        vega=vega,
        rho=rho,
    )


def _quote_liquidity(quote: OptionQuote) -> float:
    mid = quote.mid
    if quote.bid is None or quote.ask is None or quote.ask < quote.bid or mid in {None, 0}:
        return 0.0
    assert mid is not None
    spread_ratio = (quote.ask - quote.bid) / mid
    spread_component = max(0.0, 1.0 - min(spread_ratio / 0.25, 1.0))
    open_interest_component = min((quote.open_interest or 0) / 500.0, 1.0)
    volume_component = min((quote.volume or 0) / 100.0, 1.0)
    size_component = min(min(quote.bid_size or 0, quote.ask_size or 0) / 20.0, 1.0)
    return round(
        0.55 * spread_component
        + 0.20 * open_interest_component
        + 0.15 * volume_component
        + 0.10 * size_component,
        6,
    )


def estimate_execution(candidate: StrategyCandidate, bundle: MarketDataBundle) -> ExecutionEstimate:
    theoretical_mid = 0.0
    market_cost = 0.0
    fees = 0.0
    slippage = 0.0
    liquidity_scores: list[float] = []
    has_short_option = False
    notes: list[str] = []

    for leg in candidate.legs:
        side = leg.side.sign
        if leg.instrument_type == "stock":
            assert leg.stock_price is not None
            theoretical_mid += side * leg.quantity * leg.stock_price
            market_cost += side * leg.quantity * leg.stock_price
            if bundle.portfolio.stock_commission is not None:
                fees += bundle.portfolio.stock_commission
            if bundle.portfolio.stock_slippage_bps is not None:
                slippage += (
                    leg.quantity * leg.stock_price * bundle.portfolio.stock_slippage_bps / 10_000
                )
            continue

        assert leg.option_quote is not None
        quote = leg.option_quote
        multiplier = quote.contract.multiplier
        mid = quote.mid or 0.0
        executable_price = quote.ask if leg.side is PositionSide.LONG else quote.bid
        executable_price = executable_price or 0.0
        theoretical_mid += side * leg.quantity * multiplier * mid
        market_cost += side * leg.quantity * multiplier * executable_price
        if bundle.portfolio.commission_per_option_contract is not None:
            fees += leg.quantity * bundle.portfolio.commission_per_option_contract
        if bundle.portfolio.slippage_per_option_contract is not None:
            slippage += leg.quantity * bundle.portfolio.slippage_per_option_contract
        liquidity_scores.append(_quote_liquidity(quote))
        has_short_option = has_short_option or leg.side is PositionSide.SHORT

    total_entry_cost = market_cost + fees + slippage
    margin_requirement: float | None = 0.0
    if has_short_option and not bundle.portfolio.margin_known:
        margin_requirement = None
        notes.append("Broker margin is unknown for a structure containing a short option leg")
    elif has_short_option:
        notes.append("Margin is fixture-provided and must be refreshed at the broker before use")

    return ExecutionEstimate(
        theoretical_mid=round(theoretical_mid, 6),
        executable_debit=round(max(total_entry_cost, 0.0), 6),
        executable_credit=round(max(-total_entry_cost, 0.0), 6),
        fees=round(fees, 6),
        slippage=round(slippage, 6),
        total_entry_cost=round(total_entry_cost, 6),
        margin_requirement=margin_requirement,
        liquidity_score=min(liquidity_scores, default=1.0),
        notes=notes,
    )


def payoff_pnl_at_expiration(
    candidate: StrategyCandidate, spot: float, execution: ExecutionEstimate | None = None
) -> float:
    if spot < 0:
        raise ValueError("spot cannot be negative")
    execution = execution or candidate.execution_estimate
    if execution is None:
        raise ValueError("execution estimate is required")

    terminal_value = 0.0
    for leg in candidate.legs:
        if leg.instrument_type == "stock":
            terminal_value += leg.side.sign * leg.quantity * spot
            continue
        assert leg.option_quote is not None
        contract = leg.option_quote.contract
        intrinsic = (
            max(spot - contract.strike, 0.0)
            if contract.option_type is OptionType.CALL
            else max(contract.strike - spot, 0.0)
        )
        terminal_value += leg.side.sign * leg.quantity * contract.multiplier * intrinsic
    return terminal_value - execution.total_entry_cost


def _aggregate_greeks(candidate: StrategyCandidate, bundle: MarketDataBundle) -> tuple[float, ...]:
    delta = gamma = theta = vega = rho = 0.0
    pricing_by_symbol = {item.contract_symbol: item for item in candidate.pricing_results}
    for leg in candidate.legs:
        side_quantity = leg.side.sign * leg.quantity
        if leg.instrument_type == "stock":
            delta += side_quantity
            continue
        assert leg.option_quote is not None
        quote = leg.option_quote
        contract = quote.contract
        greeks = pricing_by_symbol[contract.local_symbol]
        scale = side_quantity * contract.multiplier
        delta += greeks.delta * scale
        gamma += greeks.gamma * scale
        theta += greeks.theta * scale
        vega += greeks.vega * scale
        rho += greeks.rho * scale
    return tuple(round(value, 6) for value in (delta, gamma, theta, vega, rho))


def _unit_scale(candidate: StrategyCandidate) -> float:
    option_legs = [leg for leg in candidate.legs if leg.instrument_type == "option"]
    if not option_legs:
        return 1.0
    leg = option_legs[0]
    assert leg.option_quote is not None
    return leg.quantity * leg.option_quote.contract.multiplier


def analyze_risk(candidate: StrategyCandidate, bundle: MarketDataBundle) -> RiskMetrics:
    analyze_candidate_option_models(candidate, bundle)
    execution = estimate_execution(candidate, bundle)
    candidate.execution_estimate = execution
    entry_cost = execution.total_entry_cost
    max_gain: float | None
    max_loss: float | None
    break_even: list[float]
    unbounded = False
    unit_scale = _unit_scale(candidate)

    if candidate.kind is StrategyKind.NO_TRADE:
        max_gain, max_loss, break_even = 0.0, 0.0, []
    elif candidate.kind is StrategyKind.STOCK:
        max_gain, max_loss = None, max(entry_cost, 0.0)
        break_even = [entry_cost / candidate.legs[0].quantity]
    elif candidate.kind is StrategyKind.LONG_CALL:
        strike = candidate.legs[0].option_quote.contract.strike  # type: ignore[union-attr]
        max_gain, max_loss = None, max(entry_cost, 0.0)
        break_even = [strike + entry_cost / unit_scale]
    elif candidate.kind is StrategyKind.LONG_PUT:
        strike = candidate.legs[0].option_quote.contract.strike  # type: ignore[union-attr]
        max_gain = max(strike * unit_scale - entry_cost, 0.0)
        max_loss = max(entry_cost, 0.0)
        break_even = [max(strike - entry_cost / unit_scale, 0.0)]
    elif candidate.kind is StrategyKind.BULL_CALL_SPREAD:
        long_strike = candidate.legs[0].option_quote.contract.strike  # type: ignore[union-attr]
        short_strike = candidate.legs[1].option_quote.contract.strike  # type: ignore[union-attr]
        width_value = (short_strike - long_strike) * unit_scale
        max_gain = max(width_value - entry_cost, 0.0)
        max_loss = max(entry_cost, 0.0)
        break_even = [long_strike + entry_cost / unit_scale]
    elif candidate.kind is StrategyKind.BEAR_PUT_SPREAD:
        long_strike = candidate.legs[0].option_quote.contract.strike  # type: ignore[union-attr]
        short_strike = candidate.legs[1].option_quote.contract.strike  # type: ignore[union-attr]
        width_value = (long_strike - short_strike) * unit_scale
        max_gain = max(width_value - entry_cost, 0.0)
        max_loss = max(entry_cost, 0.0)
        break_even = [max(long_strike - entry_cost / unit_scale, 0.0)]
    else:  # pragma: no cover - defensive for future enum additions
        max_gain, max_loss, break_even, unbounded = None, None, [], True

    for leg in candidate.legs:
        if leg.instrument_type == "stock" and leg.side is PositionSide.SHORT:
            unbounded = True
        if leg.instrument_type == "option" and leg.side is PositionSide.SHORT:
            assert leg.option_quote is not None
            is_naked_call = (
                leg.option_quote.contract.option_type is OptionType.CALL
                and len(candidate.legs) == 1
            )
            if is_naked_call:
                unbounded = True

    strikes = [
        leg.option_quote.contract.strike
        for leg in candidate.legs
        if leg.instrument_type == "option" and leg.option_quote is not None
    ]
    spot = bundle.underlying.price
    grid = sorted({0.0, spot * 0.5, spot, spot * 1.5, spot * 2.0, *strikes, *break_even})
    payoff_points = [
        PayoffPoint(spot=point, pnl=round(payoff_pnl_at_expiration(candidate, point), 6))
        for point in grid
    ]
    delta, gamma, theta, vega, rho = _aggregate_greeks(candidate, bundle)
    executable_signed = execution.executable_debit - execution.executable_credit
    metrics = RiskMetrics(
        max_gain=None if max_gain is None else round(max_gain, 6),
        max_loss=None if max_loss is None else round(max_loss, 6),
        break_even_points=[round(point, 6) for point in break_even],
        net_delta=delta,
        net_gamma=gamma,
        net_theta=theta,
        net_vega=vega,
        net_rho=rho,
        debit_credit_mid=execution.theoretical_mid,
        debit_credit_executable=round(executable_signed, 6),
        unbounded_risk=unbounded,
        payoff_points=payoff_points,
    )
    candidate.risk_metrics = metrics
    return metrics
