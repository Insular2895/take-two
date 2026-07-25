"""Construct precise candidates and calculate executable entry/risk mechanics."""

from __future__ import annotations

from collections.abc import Sequence

from take_two_options.candidate_generation.registry import ARCHITECTURE_REGISTRY
from take_two_options.domain import PositionSide
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import (
    Architecture,
    CandidateLeg,
    CandidateRisk,
    CompiledStrategyCandidate,
    ExitPolicy,
    MaintenancePolicy,
    ParameterOrigin,
    QuoteSnapshot,
    StrategyRecipe,
    TradeRequest,
)


def terminal_payoff(legs: Sequence[CandidateLeg], spot: float) -> float:
    payoff = 0.0
    for leg in legs:
        quote = leg.quote
        intrinsic = (
            max(spot - quote.strike, 0.0)
            if quote.option_type.value == "call"
            else max(quote.strike - spot, 0.0)
        )
        payoff += leg.side.sign * leg.quantity * quote.multiplier * intrinsic
    return payoff


def _break_evens(legs: Sequence[CandidateLeg], entry_cash: float, costs: float) -> list[float]:
    strikes = sorted({leg.quote.strike for leg in legs})
    high = max(strikes[-1] * 3, strikes[-1] + 500)
    grid = sorted({0.0, *strikes, high})
    points: list[float] = []
    previous_spot = grid[0]
    previous_pnl = terminal_payoff(legs, previous_spot) - entry_cash - costs
    for spot in grid[1:]:
        pnl = terminal_payoff(legs, spot) - entry_cash - costs
        if pnl == 0:
            points.append(spot)
        elif previous_pnl == 0:
            points.append(previous_spot)
        elif previous_pnl * pnl < 0:
            weight = abs(previous_pnl) / (abs(previous_pnl) + abs(pnl))
            points.append(previous_spot + (spot - previous_spot) * weight)
        previous_spot, previous_pnl = spot, pnl
    return sorted({round(point, 4) for point in points})


def _risk(
    architecture: Architecture,
    legs: list[CandidateLeg],
    request: TradeRequest,
) -> CandidateRisk:
    execution = request.execution_policy
    entry_cash = sum(
        leg.side.sign * leg.quantity * leg.quote.multiplier * leg.entry_price for leg in legs
    )
    contract_sides = sum(leg.quantity for leg in legs)
    fees = execution.commission_per_contract_side * contract_sides
    slippage = execution.slippage_per_contract_side * contract_sides
    costs = fees + slippage
    strikes = sorted({leg.quote.strike for leg in legs})
    high = max(strikes[-1] * 4, strikes[-1] + 1_000)
    grid = sorted({0.0, *strikes, high})
    terminal_pnls = [terminal_payoff(legs, spot) - entry_cash - costs for spot in grid]
    maximum_loss = max(0.0, -min(terminal_pnls))
    unbounded_upside = ARCHITECTURE_REGISTRY[architecture].unbounded_upside
    maximum_gain = None if unbounded_upside else max(0.0, max(terminal_pnls))
    fx = request.fx_rate_to_usd or (1.0 if request.currency == "USD" else 0.0)
    budget_usd = request.budget * fx
    return CandidateRisk(
        entry_debit=round(entry_cash, 4),
        fees=round(fees, 4),
        slippage=round(slippage, 4),
        total_cost=round(entry_cash + costs, 4),
        maximum_loss=round(maximum_loss, 4),
        maximum_gain=round(maximum_gain, 4) if maximum_gain is not None else None,
        break_even_points=_break_evens(legs, entry_cash, costs),
        budget_remaining=round((budget_usd - maximum_loss) / fx, 4) if fx else 0.0,
        bounded=ARCHITECTURE_REGISTRY[architecture].bounded_risk,
        executable_sides_used=True,
    )


def build_candidate(
    *,
    architecture: Architecture,
    recipe: StrategyRecipe,
    leg_specs: Sequence[tuple[PositionSide, int, QuoteSnapshot]],
    quantity: int,
    request: TradeRequest,
    horizon_compatible: bool,
) -> CompiledStrategyCandidate:
    legs = [
        CandidateLeg(
            side=side,
            quantity=ratio * quantity,
            quote=quote,
            entry_price=quote.ask if side is PositionSide.LONG else quote.bid,
        )
        for side, ratio, quote in leg_specs
    ]
    policy = ExitPolicy(
        policy_id="coarse",
        profit_target=None,
        stop_loss=None,
        maximum_holding_days=int(recipe.holding_days.maximum or recipe.holding_days.values[-1]),
        origin=recipe.holding_days.origin,
    )
    partial_recovery = sum(leg.quantity for leg in legs if leg.side is PositionSide.LONG) > 1
    maintenance = MaintenancePolicy(
        rolling_rule="none",
        capital_recovery_rule="none",
        review_frequency_days=request.maintenance_preferences.review_frequency_days,
        partial_recovery_feasible=partial_recovery,
    )
    risk = _risk(architecture, legs, request)
    thesis_compatible = request.directional_thesis in recipe.allowed_theses
    liquidity_policy = request.liquidity_policy
    liquidity_compatible = all(
        (
            (quote.open_interest or 0) >= liquidity_policy.minimum_open_interest
            and (
                liquidity_policy.allow_missing_volume
                if quote.volume is None
                else quote.volume >= liquidity_policy.minimum_volume
            )
            and quote.bid > 0
            and quote.ask > 0
            and (quote.ask - quote.bid) / ((quote.ask + quote.bid) / 2)
            <= liquidity_policy.maximum_relative_spread
        )
        for _, _, quote in leg_specs
    )
    synthetic_combo_exit = sum(
        leg.side.sign
        * leg.quantity
        * leg.quote.multiplier
        * (leg.quote.bid if leg.side is PositionSide.LONG else leg.quote.ask)
        for leg in legs
    )
    synthetic_combo_mid = (risk.entry_debit + synthetic_combo_exit) / 2
    synthetic_combo_relative_spread = (
        (risk.entry_debit - synthetic_combo_exit) / abs(synthetic_combo_mid)
        if abs(synthetic_combo_mid) > 1e-9
        else float("inf")
    )
    if (
        len(legs) > 1
        and synthetic_combo_relative_spread
        > liquidity_policy.maximum_relative_spread
    ):
        liquidity_compatible = False
    identity = {
        "architecture": architecture.value,
        "recipe": recipe.recipe_id,
        "quantity": quantity,
        "legs": [
            {"side": side.value, "ratio": ratio, "symbol": quote.symbol}
            for side, ratio, quote in leg_specs
        ],
        "policy": policy.model_dump(mode="json"),
    }
    hard_vetoes: list[str] = []
    fx = request.fx_rate_to_usd or (1.0 if request.currency == "USD" else None)
    if fx is None:
        hard_vetoes.append("FX_RATE_MISSING")
    else:
        maximum_loss_request_currency = risk.maximum_loss / fx
        if maximum_loss_request_currency > request.maximum_loss:
            hard_vetoes.append("MAXIMUM_LOSS_EXCEEDED")
        if maximum_loss_request_currency > request.budget * (1 - request.safety_reserve_fraction):
            hard_vetoes.append("BUDGET_EXCEEDED")
    if not risk.bounded:
        hard_vetoes.append("UNBOUNDED_RISK")
    if not horizon_compatible:
        hard_vetoes.append("HORIZON_NOT_LISTED")
    if not thesis_compatible:
        hard_vetoes.append("THESIS_INCOMPATIBLE")
    if not liquidity_compatible:
        hard_vetoes.append("LIQUIDITY_FAILED")
    if (
        len(legs) > 1
        and synthetic_combo_relative_spread
        > liquidity_policy.maximum_relative_spread
    ):
        hard_vetoes.append("COMBO_SPREAD_FAILED")
    return CompiledStrategyCandidate(
        candidate_id=f"cand-{stable_hash(identity)[:16]}",
        architecture=architecture,
        recipe_id=recipe.recipe_id,
        legs=legs,
        exit_policy=policy,
        maintenance_policy=maintenance,
        risk=risk,
        horizon_compatible=horizon_compatible,
        thesis_compatible=thesis_compatible,
        liquidity_compatible=liquidity_compatible,
        broker_constructible=all(bool(quote.symbol) for _, _, quote in leg_specs),
        source_ids=sorted({quote.source_id for _, _, quote in leg_specs}),
        assumptions=[
            "Entry longs use ask and entry shorts use bid",
            "Terminal payoff uses listed contract multiplier and whole contracts",
            "Leg-by-leg EOD quotes do not prove a simultaneous combo fill",
        ],
        uncertainties=[
            f"synthetic_combo_relative_spread={synthetic_combo_relative_spread:.6f}",
            "A timestamped broker combo quote can supersede the synthetic leg market.",
        ],
        hard_vetoes=hard_vetoes,
    )


def with_exit_policy(
    candidate: CompiledStrategyCandidate,
    *,
    profit_target: float,
    stop_loss: float,
    holding_days: int,
    rolling_rule: str,
    capital_recovery_rule: str,
    origin: ParameterOrigin,
) -> CompiledStrategyCandidate:
    updated = candidate.model_copy(deep=True)
    policy = ExitPolicy(
        policy_id=(
            f"tp{profit_target:g}-sl{stop_loss:g}-h{holding_days}-"
            f"{rolling_rule}-{capital_recovery_rule}"
        ),
        profit_target=profit_target,
        stop_loss=stop_loss,
        maximum_holding_days=holding_days,
        origin=origin,
    )
    updated.exit_policy = policy
    updated.maintenance_policy.rolling_rule = rolling_rule
    updated.maintenance_policy.capital_recovery_rule = capital_recovery_rule
    identity = {
        "base": candidate.candidate_id,
        "exit": policy.model_dump(mode="json"),
        "maintenance": updated.maintenance_policy.model_dump(mode="json"),
    }
    updated.candidate_id = f"cand-{stable_hash(identity)[:16]}"
    return updated
