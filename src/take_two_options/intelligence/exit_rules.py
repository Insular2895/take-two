"""Configurable advisory exit rules; every trigger still requires a human."""

from __future__ import annotations

from take_two_options.intelligence.schemas import (
    ExitRuleTrigger,
    MonitorAction,
    PositionDossier,
    PositionMonitorInput,
)

_ACTION_PRIORITY = {
    MonitorAction.HOLD: 0,
    MonitorAction.WATCH: 1,
    MonitorAction.REDUCE: 2,
    MonitorAction.EXIT_REVIEW: 3,
    MonitorAction.DATA_STALE: 4,
    MonitorAction.BLOCKED_INSUFFICIENT_DATA: 5,
    MonitorAction.THESIS_INVALIDATED: 6,
}


def evaluate_exit_rules(
    dossier: PositionDossier,
    current: PositionMonitorInput,
    *,
    total_pnl_usd: float,
    prudent_liquidation_pnl_usd: float | None,
) -> tuple[MonitorAction, list[ExitRuleTrigger]]:
    """Evaluate observable thresholds without submitting or scheduling an order."""
    plan = dossier.exit_plan
    return_on_cost = total_pnl_usd / max(dossier.actual_cost_usd, 1e-9)
    prudent_return = (
        prudent_liquidation_pnl_usd / max(dossier.actual_cost_usd, 1e-9)
        if prudent_liquidation_pnl_usd is not None
        else None
    )
    iv_drop = 1.0 - current.current_iv / max(dossier.initial_iv, 1e-9)
    definitions = {rule.rule_id: rule for rule in plan.rules}
    trailing_drawdown = (
        (
            current.peak_prudent_liquidation_value_usd
            - current.prudent_liquidation_value_usd
        )
        / max(dossier.actual_cost_usd, 1e-9)
        if current.peak_prudent_liquidation_value_usd is not None
        and current.prudent_liquidation_value_usd is not None
        else None
    )
    elapsed_days = max((current.as_of - dossier.opened_at).total_seconds() / 86_400, 0)
    days_until_catalyst = (
        (dossier.catalyst_date - current.as_of).total_seconds() / 86_400
        if dossier.catalyst_date is not None
        else None
    )
    theta_loss = max(-current.current_greeks.get("theta", 0.0), 0.0)

    def configured_threshold(rule_id: str, default: float) -> float:
        definition = definitions.get(rule_id)
        if definition is None or isinstance(definition.threshold, (str, bool)):
            return default
        return float(definition.threshold)

    before_catalyst_threshold = configured_threshold("exit_before_catalyst", 0.0)
    after_catalyst_threshold = configured_threshold("exit_after_catalyst", 0.0)
    observed: dict[str, tuple[bool, float | int | str | bool | None, float | int | str | bool]] = {
        "fundamental_invalidation": (
            current.thesis_invalidated,
            current.thesis_invalidated,
            True,
        ),
        "data_insufficient": (
            not current.data_sufficient,
            current.data_sufficient,
            True,
        ),
        "data_stale": (
            not current.data_fresh,
            current.data_fresh,
            False,
        ),
        "operational_stop_loss": (
            (prudent_return if prudent_return is not None else return_on_cost)
            <= -plan.operational_stop_loss,
            prudent_return if prudent_return is not None else return_on_cost,
            -plan.operational_stop_loss,
        ),
        "time_exit": (
            current.days_to_expiration <= plan.exit_days_before_expiration,
            current.days_to_expiration,
            plan.exit_days_before_expiration,
        ),
        "profit_target": (
            (prudent_return if prudent_return is not None else return_on_cost)
            >= plan.profit_target,
            prudent_return if prudent_return is not None else return_on_cost,
            plan.profit_target,
        ),
        "partial_profit_target": (
            (prudent_return if prudent_return is not None else return_on_cost)
            >= plan.partial_profit_target,
            prudent_return if prudent_return is not None else return_on_cost,
            plan.partial_profit_target,
        ),
        "iv_crush": (
            iv_drop >= plan.iv_crush_threshold,
            iv_drop,
            plan.iv_crush_threshold,
        ),
        "theta_limit": (
            "theta_limit" in definitions
            and theta_loss >= configured_threshold("theta_limit", float("inf")),
            theta_loss,
            configured_threshold("theta_limit", float("inf")),
        ),
        "trailing_drawdown": (
            trailing_drawdown is not None
            and trailing_drawdown >= plan.trailing_drawdown,
            trailing_drawdown,
            plan.trailing_drawdown,
        ),
        "temporal_invalidation": (
            dossier.horizon_days is not None and elapsed_days >= dossier.horizon_days,
            elapsed_days,
            dossier.horizon_days or 0,
        ),
        "exit_before_catalyst": (
            days_until_catalyst is not None
            and 0 <= days_until_catalyst <= before_catalyst_threshold,
            days_until_catalyst,
            before_catalyst_threshold,
        ),
        "exit_after_catalyst": (
            days_until_catalyst is not None
            and -days_until_catalyst >= after_catalyst_threshold
            and days_until_catalyst < 0,
            None if days_until_catalyst is None else -days_until_catalyst,
            after_catalyst_threshold,
        ),
        "liquidity_deterioration": (
            current.liquidity_score is not None
            and any(
                rule.rule_id == "liquidity_deterioration"
                and current.liquidity_score < float(rule.threshold)
                for rule in plan.rules
            ),
            current.liquidity_score,
            next(
                (
                    rule.threshold
                    for rule in plan.rules
                    if rule.rule_id == "liquidity_deterioration"
                ),
                0.0,
            ),
        ),
        "expected_value_negative": (
            current.expected_remaining_pnl_usd is not None
            and current.expected_remaining_pnl_usd < 0,
            current.expected_remaining_pnl_usd,
            0.0,
        ),
        "cvar_limit": (
            current.remaining_cvar_95_usd is not None
            and current.remaining_cvar_95_usd
            > dossier.actual_cost_usd
            * float(
                next(
                    (
                        rule.threshold
                        for rule in plan.rules
                        if rule.rule_id == "cvar_limit"
                    ),
                    0.8,
                )
            ),
            current.remaining_cvar_95_usd,
            next(
                (rule.threshold for rule in plan.rules if rule.rule_id == "cvar_limit"),
                0.8,
            ),
        ),
    }
    triggers: list[ExitRuleTrigger] = []
    for rule_id, (triggered, value, threshold) in observed.items():
        if not triggered:
            continue
        definition = definitions.get(rule_id)
        if definition is None:
            continue
        triggers.append(
            ExitRuleTrigger(
                rule_id=rule_id,
                observed_value=value,
                threshold=threshold,
                triggered_at=current.as_of,
                severity=definition.severity,
                suggested_action=definition.suggested_action,
                required_data=definition.required_data,
                confidence=1.0 if current.data_fresh and current.data_sufficient else 0.5,
            )
        )
    action = max(
        (trigger.suggested_action for trigger in triggers),
        key=lambda item: _ACTION_PRIORITY[item],
        default=MonitorAction.HOLD,
    )
    return action, triggers
