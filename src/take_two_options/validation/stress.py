"""Candidate-level cost and model stress tests."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate


def stress_candidate(candidate: CompiledStrategyCandidate) -> dict[str, float]:
    expectation = candidate.evaluation.conservative_expected_pnl or 0.0
    spread_cost = sum(
        (leg.quote.ask - leg.quote.bid) * leg.quantity * leg.quote.multiplier
        for leg in candidate.legs
    )
    configured_slippage = candidate.risk.slippage
    return {
        "baseline_expected_pnl": expectation,
        "spread_x1_5_expected_pnl": expectation - 0.5 * spread_cost,
        "slippage_x2_expected_pnl": expectation - configured_slippage,
        "commissions_x2_expected_pnl": expectation - candidate.risk.fees,
        "iv_minus_10pct_proxy": expectation - 0.1 * candidate.risk.maximum_loss,
        "iv_plus_10pct_proxy": expectation + 0.1 * candidate.risk.maximum_loss,
    }


def stress_passed(results: dict[str, float]) -> bool:
    required = [
        value
        for key, value in results.items()
        if key.endswith("expected_pnl") and key != "baseline_expected_pnl"
    ]
    return bool(required) and min(required) > 0
