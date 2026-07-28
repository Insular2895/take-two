"""Explainable post-entry monitoring against the preserved decision dossier."""

from __future__ import annotations

from take_two_options.intelligence.schemas import (
    MonitorAction,
    PositionDossier,
    PositionMonitorInput,
    PositionMonitorReport,
)


def _probability_changes(
    initial: dict[str, float],
    current: dict[str, float],
) -> dict[str, float]:
    scenarios = set(initial) | set(current)
    return {
        scenario: current.get(scenario, 0.0) - initial.get(scenario, 0.0)
        for scenario in sorted(scenarios)
    }


def monitor_position(
    dossier: PositionDossier,
    current: PositionMonitorInput,
) -> PositionMonitorReport:
    """Map observable rule triggers to one advisory action; never mutate a position."""
    elapsed_days = max((current.as_of - dossier.opened_at).total_seconds() / 86_400, 0.0)
    spot_change = current.current_spot - dossier.initial_spot
    iv_change = current.current_iv - dossier.initial_iv
    rate_change = current.current_rate - dossier.initial_rate
    greek = dossier.initial_greeks
    attribution = {
        "delta": greek.get("delta", 0.0) * spot_change,
        "gamma": 0.5 * greek.get("gamma", 0.0) * spot_change**2,
        "theta": greek.get("theta", 0.0) * elapsed_days,
        "vega": greek.get("vega", 0.0) * iv_change * 100,
        "rho": greek.get("rho", 0.0) * rate_change * 100,
    }
    unrealized = current.market_value_usd - dossier.actual_cost_usd
    total_pnl = unrealized + current.realized_pnl_usd
    return_on_cost = total_pnl / max(dossier.actual_cost_usd, 1e-9)
    changes = _probability_changes(
        dossier.initial_scenario_probabilities,
        current.current_scenario_probabilities,
    )
    largest_probability_drop = min(changes.values(), default=0.0)
    plan = dossier.exit_plan
    triggers: list[str] = []
    explanation: list[str] = []
    action = MonitorAction.KEEP
    if current.thesis_invalidated:
        action = MonitorAction.THESIS_INVALIDATED
        triggers.append("fundamental_invalidation")
        explanation.append("A preserved fundamental invalidation condition is now true.")
    elif return_on_cost <= -plan.operational_stop_loss:
        action = MonitorAction.EXIT
        triggers.append("operational_stop_loss")
        explanation.append(
            f"Total return {return_on_cost:.1%} breached the "
            f"-{plan.operational_stop_loss:.1%} operational stop."
        )
    elif current.days_to_expiration <= plan.exit_days_before_expiration:
        action = MonitorAction.EXIT
        triggers.append("time_exit")
        explanation.append("The pre-expiration time-exit window has been reached.")
    elif return_on_cost >= plan.profit_target:
        action = MonitorAction.EXIT
        triggers.append("profit_target")
        explanation.append("The full profit target has been reached.")
    elif return_on_cost >= plan.partial_profit_target:
        action = MonitorAction.REDUCE
        triggers.append("partial_profit_target")
        explanation.append("The partial-profit threshold calls for a human scale-out review.")
    elif iv_change / dossier.initial_iv <= -plan.iv_crush_threshold:
        action = MonitorAction.REDUCE
        triggers.append("iv_crush")
        explanation.append(
            f"Implied volatility has fallen by at least {plan.iv_crush_threshold:.0%} "
            "from entry."
        )
    elif largest_probability_drop <= -0.20:
        action = MonitorAction.WATCH
        triggers.append("scenario_probability_drop")
        explanation.append("At least one preserved scenario probability fell by 20 points.")
    elif current.regime != dossier.initial_regime:
        action = MonitorAction.WATCH
        triggers.append("regime_change")
        explanation.append(
            f"Regime changed from {dossier.initial_regime} to {current.regime}."
        )
    else:
        explanation.append("No configured profit, loss, time, IV, or thesis trigger fired.")
    divergence = (
        "thesis_weaker_than_market"
        if largest_probability_drop < -0.10 and total_pnl >= 0
        else "market_weaker_than_thesis"
        if largest_probability_drop >= 0 and total_pnl < 0
        else "aligned_or_inconclusive"
    )
    return PositionMonitorReport(
        dossier_id=dossier.dossier_id,
        as_of=current.as_of,
        action=action,
        unrealized_pnl_usd=unrealized,
        total_pnl_usd=total_pnl,
        probability_changes=changes,
        greek_attribution=attribution,
        iv_change=iv_change,
        execution_impact_usd=current.execution_impact_usd,
        regime_change=f"{dossier.initial_regime}->{current.regime}",
        thesis_market_divergence=divergence,
        triggered_rules=triggers,
        explanation=explanation,
    )
