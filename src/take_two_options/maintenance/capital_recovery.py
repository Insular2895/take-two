"""Whole-contract capital-recovery feasibility."""

from __future__ import annotations


def recovery_action(
    *,
    long_contracts: int,
    target_contracts_to_sell: int,
) -> str:
    if long_contracts <= 0:
        return "not_applicable"
    if target_contracts_to_sell <= 0:
        return "hold"
    if target_contracts_to_sell >= long_contracts:
        return "close_entire_position"
    if long_contracts == 1:
        return "partial_recovery_impossible"
    return f"sell_{target_contracts_to_sell}_whole_contracts"
