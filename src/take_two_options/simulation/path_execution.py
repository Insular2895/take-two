"""Reprice whole-contract option legs along paths and apply exit policies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

from take_two_options.domain import OptionType, PositionSide
from take_two_options.knowledge.schemas import CandidateLeg, CompiledStrategyCandidate
from take_two_options.quantitative.contracts import DEFAULT_QUANT_CONVENTIONS
from take_two_options.simulation.exit_state import advance_exit_state, initial_exit_state


@dataclass(frozen=True)
class PathExecutionResult:
    pnl: float
    exit_day: int
    exit_reason: str
    maximum_drawdown: float


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _option_value(
    option_type: OptionType,
    *,
    spot: float,
    strike: float,
    time_years: float,
    volatility: float,
    rate: float = 0.0,
) -> float:
    if time_years <= 0:
        return (
            max(spot - strike, 0.0) if option_type is OptionType.CALL else max(strike - spot, 0.0)
        )
    volatility = max(volatility, 0.0001)
    scale = volatility * math.sqrt(time_years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * volatility**2) * time_years) / scale
    d2 = d1 - scale
    discounted_strike = strike * math.exp(-rate * time_years)
    if option_type is OptionType.CALL:
        return spot * _normal_cdf(d1) - discounted_strike * _normal_cdf(d2)
    return discounted_strike * _normal_cdf(-d2) - spot * _normal_cdf(-d1)


def _relative_spread(leg: CandidateLeg) -> float:
    mid = (leg.quote.ask + leg.quote.bid) / 2
    return min((leg.quote.ask - leg.quote.bid) / mid, 1.0) if mid > 0 else 1.0


def _position_exit_value(
    candidate: CompiledStrategyCandidate,
    *,
    spot: float,
    valuation_date: date,
) -> float:
    value = 0.0
    for leg in candidate.legs:
        if leg.quote.implied_volatility is None:
            raise ValueError(
                f"path repricing requires explicit IV for {leg.quote.symbol}; "
                "silent volatility imputation is forbidden"
            )
        days = max((leg.quote.expiration - valuation_date).days, 0)
        theoretical = _option_value(
            leg.quote.option_type,
            spot=spot,
            strike=leg.quote.strike,
            time_years=days / DEFAULT_QUANT_CONVENTIONS.calendar_day_basis,
            volatility=leg.quote.implied_volatility,
        )
        half_spread = _relative_spread(leg) / 2
        executable = (
            theoretical * (1 - half_spread)
            if leg.side is PositionSide.LONG
            else theoretical * (1 + half_spread)
        )
        value += leg.side.sign * leg.quantity * leg.quote.multiplier * max(executable, 0.0)
    return value


def execute_path(
    candidate: CompiledStrategyCandidate,
    path: list[float],
    *,
    start_date: date,
    commission_per_contract_side: float,
    slippage_per_contract_side: float,
) -> PathExecutionResult:
    maximum_holding = min(candidate.exit_policy.maximum_holding_days, len(path) - 1)
    earliest_expiration = min(leg.quote.expiration for leg in candidate.legs)
    maximum_holding = min(maximum_holding, max((earliest_expiration - start_date).days, 1))
    entry_costs = candidate.risk.fees + candidate.risk.slippage
    exit_contract_sides = sum(leg.quantity for leg in candidate.legs)
    exit_costs = exit_contract_sides * (commission_per_contract_side + slippage_per_contract_side)
    denominator = max(candidate.risk.maximum_loss, 0.01)
    final_pnl = -entry_costs
    exit_state = initial_exit_state(final_pnl)
    for day in range(1, maximum_holding + 1):
        value = _position_exit_value(
            candidate,
            spot=path[day],
            valuation_date=start_date + timedelta(days=day),
        )
        pnl = value - candidate.risk.entry_debit - entry_costs - exit_costs
        return_on_risk = pnl / denominator
        exit_state = advance_exit_state(
            exit_state,
            day=day,
            pnl=pnl,
            return_on_risk=return_on_risk,
            is_final_checkpoint=day == maximum_holding,
            profit_target=candidate.exit_policy.profit_target,
            stop_loss=candidate.exit_policy.stop_loss,
        )
        final_pnl = pnl
        if exit_state.terminal:
            break
    if not exit_state.terminal:
        raise RuntimeError("path execution ended without a terminal exit state")
    return PathExecutionResult(
        pnl=round(final_pnl, 6),
        exit_day=exit_state.exit_day or maximum_holding,
        exit_reason=exit_state.state.value,
        maximum_drawdown=round(exit_state.maximum_drawdown, 6),
    )
