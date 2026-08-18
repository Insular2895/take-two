"""Explainable post-entry monitoring against the preserved decision dossier."""

from __future__ import annotations

from take_two_options.intelligence.exit_rules import evaluate_exit_rules
from take_two_options.intelligence.schemas import (
    MonitorAction,
    PositionDossier,
    PositionMonitorInput,
    PositionMonitorReport,
    PositionTrajectoryFixture,
    PositionTrajectoryReplay,
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
    changes = _probability_changes(
        dossier.initial_scenario_probabilities,
        current.current_scenario_probabilities,
    )
    largest_probability_drop = min(changes.values(), default=0.0)
    prudent_liquidation_pnl = (
        current.prudent_liquidation_value_usd - dossier.actual_cost_usd
        if current.prudent_liquidation_value_usd is not None
        else None
    )
    action, rule_triggers = evaluate_exit_rules(
        dossier,
        current,
        total_pnl_usd=total_pnl,
        prudent_liquidation_pnl_usd=prudent_liquidation_pnl,
    )
    triggers = [trigger.rule_id for trigger in rule_triggers]
    explanation: list[str] = []
    explanation.extend(
        f"{trigger.rule_id}: observed={trigger.observed_value}; "
        f"threshold={trigger.threshold}; suggested={trigger.suggested_action.value}."
        for trigger in rule_triggers
    )
    if action is MonitorAction.HOLD and largest_probability_drop <= -0.20:
        action = MonitorAction.WATCH
        triggers.append("scenario_probability_drop")
        explanation.append("At least one preserved scenario probability fell by 20 points.")
    elif action is MonitorAction.HOLD and current.regime != dossier.initial_regime:
        action = MonitorAction.WATCH
        triggers.append("regime_change")
        explanation.append(
            f"Regime changed from {dossier.initial_regime} to {current.regime}."
        )
    elif action is MonitorAction.HOLD:
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
        prudent_liquidation_pnl_usd=prudent_liquidation_pnl,
        total_pnl_usd=total_pnl,
        expected_remaining_pnl_usd=current.expected_remaining_pnl_usd,
        remaining_cvar_95_usd=current.remaining_cvar_95_usd,
        current_greeks=current.current_greeks,
        liquidity_status=(
            "unknown"
            if current.liquidity_score is None
            else "degraded"
            if current.liquidity_score < 0.5
            else "acceptable"
        ),
        thesis_change=current.thesis_change,
        probability_changes=changes,
        greek_attribution=attribution,
        iv_change=iv_change,
        execution_impact_usd=current.execution_impact_usd,
        regime_change=f"{dossier.initial_regime}->{current.regime}",
        thesis_market_divergence=divergence,
        triggered_rules=triggers,
        rule_triggers=rule_triggers,
        explanation=explanation,
    )


def replay_position_trajectory(
    fixture: PositionTrajectoryFixture,
) -> PositionTrajectoryReplay:
    """Replay an immutable synthetic trajectory through the same advisory monitor."""
    return PositionTrajectoryReplay(
        fixture_id=fixture.fixture_id,
        status="FIXTURE_ONLY_REPLAY",
        reports=[
            monitor_position(fixture.dossier, snapshot)
            for snapshot in fixture.snapshots
        ],
    )
