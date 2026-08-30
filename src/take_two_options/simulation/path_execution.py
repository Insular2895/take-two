"""Reprice whole-contract option legs through canonical economics along paths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from take_two_options.knowledge.schemas import CandidateLeg, CompiledStrategyCandidate
from take_two_options.quantitative.contracts import EvidenceLevel, VolatilityPolicy
from take_two_options.quantitative.costs import (
    EconomicComponent,
    PnLReconciliation,
    reconcile_pnl,
)
from take_two_options.quantitative.pricing import (
    CanonicalMarketState,
    PricingInputError,
    VolatilityState,
    price_option,
    require_contract_economics,
)
from take_two_options.simulation.exit_state import advance_exit_state, initial_exit_state


class PathExecutionError(RuntimeError):
    """A path could not produce decision-grade economic results."""


@dataclass(frozen=True)
class PathExecutionResult:
    pnl: float
    exit_day: int
    exit_reason: str
    maximum_drawdown: float
    return_on_risk: float | None
    reconciliation: PnLReconciliation


@dataclass(frozen=True)
class _PositionExitEconomics:
    theoretical_value: float
    bid_ask_cost: float


def _relative_spread(leg: CandidateLeg) -> float:
    bid = leg.quote.bid
    ask = leg.quote.ask
    if bid is None or ask is None:
        raise PricingInputError(f"BLOCKED_BID_ASK_UNKNOWN:{leg.quote.symbol}")
    mid = (ask + bid) / 2
    if mid <= 0:
        raise PricingInputError(f"BLOCKED_BID_ASK_INVALID:{leg.quote.symbol}")
    return min((ask - bid) / mid, 1.0)


def _position_exit_economics(
    candidate: CompiledStrategyCandidate,
    *,
    spot: float,
    valuation_time: datetime,
    market_state: CanonicalMarketState,
) -> _PositionExitEconomics:
    theoretical_value = 0.0
    bid_ask_cost = 0.0
    for leg in candidate.legs:
        if leg.quote.implied_volatility is None:
            raise PricingInputError(f"BLOCKED_VOLATILITY_UNKNOWN:{leg.quote.symbol}")
        multiplier = require_contract_economics(leg.quote)
        result = price_option(
            leg.quote,
            market_state,
            spot=spot,
            valuation_time=valuation_time,
            volatility_state=VolatilityState(
                annual_volatility=leg.quote.implied_volatility,
                policy=VolatilityPolicy.FROZEN_SURFACE,
                evidence=EvidenceLevel.UNVALIDATED,
                source_id=leg.quote.source_id,
                assumptions=(
                    "Leg IV is frozen along each path; this is not calibrated IV dynamics",
                ),
            ),
        )
        unsigned_value = leg.quantity * multiplier * result.price_per_share
        theoretical_value += leg.side.sign * unsigned_value
        bid_ask_cost += unsigned_value * _relative_spread(leg) / 2
    return _PositionExitEconomics(
        theoretical_value=theoretical_value,
        bid_ask_cost=bid_ask_cost,
    )


def _component(
    value: float | None,
    evidence: EvidenceLevel,
    source: str,
) -> EconomicComponent:
    return EconomicComponent(value=value, evidence=evidence, source=source)


def _path_reconciliation(
    candidate: CompiledStrategyCandidate,
    *,
    theoretical_mid_entry: float,
    entry_bid_ask_cost: float,
    exit_economics: _PositionExitEconomics,
    exit_contract_sides: int,
    commission_per_contract_side: float | None,
    slippage_per_contract_side: float | None,
    expires_on_checkpoint: bool,
    fx_costs: float | None,
) -> PnLReconciliation:
    exit_commission = (
        None
        if commission_per_contract_side is None
        else exit_contract_sides * commission_per_contract_side
    )
    commissions = (
        None if exit_commission is None else candidate.risk.fees + exit_commission
    )
    exit_slippage = (
        None
        if slippage_per_contract_side is None
        else exit_contract_sides * slippage_per_contract_side
    )
    settlement = None if expires_on_checkpoint else 0.0
    return reconcile_pnl(
        gross_pnl=exit_economics.theoretical_value
        - theoretical_mid_entry,
        entry_bid_ask_cost=_component(
            entry_bid_ask_cost,
            EvidenceLevel.KNOWN,
            "executable entry bid/ask",
        ),
        exit_bid_ask_cost=_component(
            exit_economics.bid_ask_cost,
            EvidenceLevel.HEURISTIC,
            "leg-level indicative liquidation spread",
        ),
        entry_slippage=_component(
            candidate.risk.slippage,
            EvidenceLevel.UNVALIDATED,
            "configured entry slippage",
        ),
        exit_slippage=_component(
            exit_slippage,
            (
                EvidenceLevel.UNVALIDATED
                if exit_slippage is not None
                else EvidenceLevel.UNKNOWN
            ),
            "configured exit slippage",
        ),
        commissions=_component(
            commissions,
            EvidenceLevel.ESTIMATED if commissions is not None else EvidenceLevel.UNKNOWN,
            "configured round-trip commissions",
        ),
        exercise_assignment_settlement_costs=_component(
            settlement,
            EvidenceLevel.NOT_APPLICABLE if settlement is not None else EvidenceLevel.UNKNOWN,
            "pre-expiry close policy",
        ),
        fx_costs=_component(
            fx_costs,
            (
                EvidenceLevel.NOT_APPLICABLE
                if fx_costs == 0
                else EvidenceLevel.ESTIMATED
                if fx_costs is not None
                else EvidenceLevel.UNKNOWN
            ),
            "path PnL currency conversion",
        ),
    )


def execute_path(
    candidate: CompiledStrategyCandidate,
    path: list[float],
    *,
    start_date: date,
    market_state: CanonicalMarketState,
    commission_per_contract_side: float | None,
    slippage_per_contract_side: float | None,
    fx_costs: float | None = 0.0,
) -> PathExecutionResult:
    if len(path) < 2:
        raise PathExecutionError("path execution requires at least two checkpoints")
    theoretical_mid_entry = candidate.risk.theoretical_mid_entry
    entry_bid_ask_cost = candidate.risk.entry_bid_ask_cost
    if theoretical_mid_entry is None or entry_bid_ask_cost is None:
        raise PathExecutionError("BLOCKED_ENTRY_ECONOMICS_UNKNOWN")
    maximum_holding = min(candidate.exit_policy.maximum_holding_days, len(path) - 1)
    earliest_expiration = min(leg.quote.expiration for leg in candidate.legs)
    maximum_holding = min(
        maximum_holding,
        max((earliest_expiration - start_date).days, 1),
    )
    exit_contract_sides = sum(leg.quantity for leg in candidate.legs)
    initial_pnl = -(
        entry_bid_ask_cost
        + candidate.risk.fees
        + candidate.risk.slippage
    )
    final_pnl = initial_pnl
    final_return: float | None = None
    final_reconciliation: PnLReconciliation | None = None
    exit_state = initial_exit_state(initial_pnl)
    for day in range(1, maximum_holding + 1):
        valuation_date = start_date + timedelta(days=day)
        valuation_time = datetime.combine(valuation_date, time.min)
        exit_economics = _position_exit_economics(
            candidate,
            spot=path[day],
            valuation_time=valuation_time,
            market_state=market_state,
        )
        reconciliation = _path_reconciliation(
            candidate,
            theoretical_mid_entry=theoretical_mid_entry,
            entry_bid_ask_cost=entry_bid_ask_cost,
            exit_economics=exit_economics,
            exit_contract_sides=exit_contract_sides,
            commission_per_contract_side=commission_per_contract_side,
            slippage_per_contract_side=slippage_per_contract_side,
            expires_on_checkpoint=valuation_date >= earliest_expiration,
            fx_costs=fx_costs,
        )
        if reconciliation.net_pnl is None:
            raise PathExecutionError("BLOCKED_UNKNOWN_TRANSACTION_COST")
        pnl = reconciliation.net_pnl
        capital_at_risk = candidate.risk.maximum_loss
        return_on_risk = (
            pnl / capital_at_risk
            if capital_at_risk is not None and capital_at_risk > 0
            else None
        )
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
        final_return = return_on_risk
        final_reconciliation = reconciliation
        if exit_state.terminal:
            break
    if not exit_state.terminal or final_reconciliation is None:
        raise PathExecutionError("path execution ended without a terminal exit state")
    return PathExecutionResult(
        pnl=round(final_pnl, 6),
        exit_day=exit_state.exit_day or maximum_holding,
        exit_reason=exit_state.state.value,
        maximum_drawdown=round(exit_state.maximum_drawdown, 6),
        return_on_risk=(round(final_return, 8) if final_return is not None else None),
        reconciliation=final_reconciliation,
    )
