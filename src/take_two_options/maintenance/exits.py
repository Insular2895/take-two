"""Exit trigger evaluation."""

from __future__ import annotations


def exit_reason(
    *,
    return_on_risk: float,
    days_held: int,
    profit_target: float | None,
    stop_loss: float | None,
    maximum_holding_days: int,
) -> str | None:
    if profit_target is not None and return_on_risk >= profit_target:
        return "profit_target"
    if stop_loss is not None and return_on_risk <= -stop_loss:
        return "stop_loss"
    if days_held >= maximum_holding_days:
        return "time_exit"
    return None
