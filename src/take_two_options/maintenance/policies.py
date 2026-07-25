"""Maintenance policy helpers."""

from __future__ import annotations

from take_two_options.knowledge.schemas import MaintenancePolicy


def maintenance_policy(
    *,
    rolling_rule: str,
    recovery_rule: str,
    review_frequency_days: int,
    long_contracts: int,
) -> MaintenancePolicy:
    return MaintenancePolicy(
        rolling_rule=rolling_rule,
        capital_recovery_rule=recovery_rule,
        review_frequency_days=review_frequency_days,
        partial_recovery_feasible=long_contracts > 1,
    )
