"""Construct precise candidates and calculate executable entry/risk mechanics."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from take_two_options.budget import (
    BrokerCapitalContext,
    BudgetCandidate,
    BudgetStatus,
    CapitalRequirementStatus,
    FlexibleBudgetPolicyV2,
    FXExecutionCost,
    FXRate,
    MixedExpiryLifecycleConfiguration,
    evaluate_budget_policy,
)
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
from take_two_options.quantitative.contracts import EvidenceLevel
from take_two_options.quantitative.pricing import require_contract_economics


def _quote_prices(quote: QuoteSnapshot) -> tuple[float, float]:
    if quote.bid is None or quote.ask is None:
        raise ValueError("BLOCKED_BID_ASK_UNKNOWN")
    return quote.bid, quote.ask


def _entry_price(side: PositionSide, quote: QuoteSnapshot) -> float:
    bid, ask = _quote_prices(quote)
    return ask if side is PositionSide.LONG else bid


def terminal_payoff(legs: Sequence[CandidateLeg], spot: float) -> float:
    payoff = 0.0
    for leg in legs:
        quote = leg.quote
        intrinsic = (
            max(spot - quote.strike, 0.0)
            if quote.option_type.value == "call"
            else max(quote.strike - spot, 0.0)
        )
        multiplier = require_contract_economics(quote)
        payoff += leg.side.sign * leg.quantity * multiplier * intrinsic
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
    if any(leg.quote.bid is None or leg.quote.ask is None for leg in legs):
        raise ValueError("BLOCKED_BID_ASK_UNKNOWN")
    theoretical_mid_entry = 0.0
    for leg in legs:
        bid, ask = _quote_prices(leg.quote)
        theoretical_mid_entry += (
            leg.side.sign
            * leg.quantity
            * require_contract_economics(leg.quote)
            * ((bid + ask) / 2)
        )
    entry_cash = sum(
        leg.side.sign
        * leg.quantity
        * require_contract_economics(leg.quote)
        * leg.entry_price
        for leg in legs
    )
    entry_bid_ask_cost = entry_cash - theoretical_mid_entry
    if entry_bid_ask_cost < -1e-8:
        raise ValueError("executable entry cannot improve on the declared midpoint")
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
        theoretical_mid_entry=round(theoretical_mid_entry, 4),
        entry_bid_ask_cost=round(max(entry_bid_ask_cost, 0.0), 4),
        entry_debit=round(entry_cash, 4),
        fees=round(fees, 4),
        slippage=round(slippage, 4),
        total_cost=round(entry_cash + costs, 4),
        maximum_loss=round(maximum_loss, 4),
        maximum_loss_status=EvidenceLevel.KNOWN,
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
    budget_policy: FlexibleBudgetPolicyV2 | None = None,
    fx: FXRate | None = None,
    fx_cost: FXExecutionCost | None = None,
    broker_context: BrokerCapitalContext | None = None,
    mixed_expiry_lifecycle: MixedExpiryLifecycleConfiguration | None = None,
    phase_m_context_id: str | None = None,
    phase_m_context_hash: str | None = None,
) -> CompiledStrategyCandidate:
    if (phase_m_context_id is None) != (phase_m_context_hash is None):
        raise ValueError("PHASE_M_CONTEXT_PROVENANCE_INCOMPLETE")
    if phase_m_context_id is not None and mixed_expiry_lifecycle is None:
        raise ValueError("PHASE_M_LIFECYCLE_CONTEXT_MISSING")
    if any(quote.bid is None or quote.ask is None for _, _, quote in leg_specs):
        raise ValueError("BLOCKED_BID_ASK_UNKNOWN")
    if any(quote.exercise_style is None for _, _, quote in leg_specs):
        raise ValueError("BLOCKED_EXERCISE_STYLE_UNKNOWN")
    for _, _, quote in leg_specs:
        require_contract_economics(quote)
    legs = [
        CandidateLeg(
            side=side,
            quantity=ratio * quantity,
            quote=quote,
            entry_price=_entry_price(side, quote),
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
    expirations = sorted({leg.quote.expiration for leg in legs})
    mixed_expiry = len(expirations) > 1
    if mixed_expiry:
        common_expiry_proxy = risk.maximum_loss
        risk = CandidateRisk.model_validate(
            {
                **risk.model_dump(),
                "maximum_loss": None,
                "maximum_loss_status": EvidenceLevel.UNKNOWN,
                "diagnostic_common_expiry_maximum_loss": common_expiry_proxy,
                "maximum_gain": None,
                "budget_remaining": None,
            }
        )
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
            and quote.bid is not None
            and quote.ask is not None
            and quote.bid > 0
            and quote.ask > 0
            and (quote.ask - quote.bid) / ((quote.ask + quote.bid) / 2)
            <= liquidity_policy.maximum_relative_spread
        )
        for _, _, quote in leg_specs
    )
    synthetic_combo_exit = 0.0
    for leg in legs:
        bid, ask = _quote_prices(leg.quote)
        exit_price = bid if leg.side is PositionSide.LONG else ask
        synthetic_combo_exit += (
            leg.side.sign
            * leg.quantity
            * require_contract_economics(leg.quote)
            * exit_price
        )
    synthetic_combo_mid = (risk.entry_debit + synthetic_combo_exit) / 2
    synthetic_combo_relative_spread = (
        (risk.entry_debit - synthetic_combo_exit) / abs(synthetic_combo_mid)
        if abs(synthetic_combo_mid) > 1e-9
        else float("inf")
    )
    if len(legs) > 1 and synthetic_combo_relative_spread > liquidity_policy.maximum_relative_spread:
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
    budget_diagnostics = None
    lifecycle_capital_requirement = None
    research_restrictions: list[str] = []
    if budget_policy is None:
        legacy_fx = request.fx_rate_to_usd or (1.0 if request.currency == "USD" else None)
        if legacy_fx is None:
            hard_vetoes.append("FX_RATE_MISSING")
        else:
            if risk.maximum_loss is None:
                hard_vetoes.append("CAPITAL_AT_RISK_UNKNOWN")
                maximum_loss_request_currency = None
            else:
                maximum_loss_request_currency = risk.maximum_loss / legacy_fx
            if (
                maximum_loss_request_currency is not None
                and maximum_loss_request_currency > request.maximum_loss
            ):
                hard_vetoes.append("MAXIMUM_LOSS_EXCEEDED")
            spendable_budget = request.budget * (1 - request.safety_reserve_fraction)
            if (
                maximum_loss_request_currency is not None
                and maximum_loss_request_currency > spendable_budget
            ):
                hard_vetoes.append("BUDGET_EXCEEDED")
    else:
        lifecycle_configuration = (
            mixed_expiry_lifecycle or MixedExpiryLifecycleConfiguration()
        )
        if mixed_expiry:
            identity["mixed_expiry_lifecycle"] = lifecycle_configuration.model_dump(mode="json")
        if (
            phase_m_context_id is None
            and fx is None
            and budget_policy.currency == request.currency
        ):
            if budget_policy.currency == "USD":
                fx = None
            elif request.fx_rate_to_usd is not None and request.fx_rate_as_of is not None:
                fx = FXRate(
                    source_currency="USD",
                    policy_currency=budget_policy.currency,
                    rate_to_policy_currency=1 / request.fx_rate_to_usd,
                    timestamp=datetime.combine(
                        request.fx_rate_as_of,
                        datetime.min.time(),
                        tzinfo=UTC,
                    ),
                    source="TradeRequest.fx_rate_to_usd",
                )
        has_short_leg = any(leg.side is PositionSide.SHORT for leg in legs)
        credit_structure = risk.total_cost <= 0 and has_short_leg
        buying_power_required = credit_structure or mixed_expiry
        budget_candidate = BudgetCandidate(
            candidate_id=f"cand-{stable_hash(identity)[:16]}",
            architecture=architecture.value,
            currency="USD",
            required_entry_cash=risk.total_cost,
            maximum_loss=risk.maximum_loss,
            buying_power_requirement=(
                risk.maximum_loss if credit_structure and not mixed_expiry else None
            ),
            buying_power_required=buying_power_required,
            buying_power_status=(
                CapitalRequirementStatus.ESTIMATED_ANALYTICAL_BOUND
                if credit_structure and not mixed_expiry
                else CapitalRequirementStatus.UNKNOWN
                if buying_power_required
                else CapitalRequirementStatus.NOT_REQUIRED
            ),
            quantity=quantity,
            as_of=max(leg.quote.quote_timestamp for leg in legs),
            mixed_expiry=mixed_expiry,
            first_expiry=(expirations[0] if mixed_expiry else None),
            managed_exit_deadline=(
                lifecycle_configuration.managed_exit_deadline(expirations[0])
                if mixed_expiry
                else None
            ),
            mixed_expiry_lifecycle=(lifecycle_configuration if mixed_expiry else None),
            analytical_loss_bound=None,
            analytical_bound_validated=False,
            legacy_common_expiry_maximum_loss=(
                risk.diagnostic_common_expiry_maximum_loss if mixed_expiry else None
            ),
        )
        budget_evaluation = evaluate_budget_policy(
            budget_candidate,
            budget_policy,
            fx,
            broker_context,
            fx_cost,
        )
        budget_diagnostics = budget_evaluation.diagnostics
        lifecycle_capital_requirement = budget_evaluation.lifecycle_capital_requirement
        hard_budget_statuses = {
            BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING,
            BudgetStatus.MAXIMUM_LOSS_EXCEEDED,
            BudgetStatus.BUYING_POWER_EXCEEDED,
            BudgetStatus.FX_REQUIRED,
        }
        if budget_diagnostics.budget_status in hard_budget_statuses:
            hard_vetoes.append(budget_diagnostics.budget_status.value)
        if "BELOW_HARD_MINIMUM_SPEND" in budget_diagnostics.reason_codes:
            hard_vetoes.append("BELOW_HARD_MINIMUM_SPEND")
        if not budget_diagnostics.paper_eligible:
            research_restrictions.extend(budget_diagnostics.reason_codes)
    if not risk.bounded:
        hard_vetoes.append("UNBOUNDED_RISK")
    if not horizon_compatible:
        hard_vetoes.append("HORIZON_NOT_LISTED")
    if not thesis_compatible:
        hard_vetoes.append("THESIS_INCOMPATIBLE")
    if not liquidity_compatible:
        hard_vetoes.append("LIQUIDITY_FAILED")
    if len(legs) > 1 and synthetic_combo_relative_spread > liquidity_policy.maximum_relative_spread:
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
        research_restrictions=research_restrictions,
        budget_diagnostics=budget_diagnostics,
        lifecycle_capital_requirement=lifecycle_capital_requirement,
        phase_m_context_id=phase_m_context_id,
        phase_m_context_hash=phase_m_context_hash,
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
