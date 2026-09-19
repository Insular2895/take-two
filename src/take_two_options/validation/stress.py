"""Candidate-level cost and model stress tests."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate
from take_two_options.quantitative.pricing import require_contract_economics


def stress_candidate(candidate: CompiledStrategyCandidate) -> dict[str, float]:
    expectation = candidate.evaluation.conservative_expected_pnl
    maximum_loss = candidate.risk.maximum_loss
    if expectation is None or maximum_loss is None:
        return {}
    spread_cost = 0.0
    for leg in candidate.legs:
        if leg.quote.bid is None or leg.quote.ask is None:
            return {}
        spread_cost += (
            (leg.quote.ask - leg.quote.bid)
            * leg.quantity
            * require_contract_economics(leg.quote)
        )
    configured_slippage = candidate.risk.slippage
    return {
        "baseline_expected_pnl": expectation,
        "spread_x1_5_expected_pnl": expectation - 0.5 * spread_cost,
        "slippage_x2_expected_pnl": expectation - configured_slippage,
        "commissions_x2_expected_pnl": expectation - candidate.risk.fees,
        "iv_minus_10pct_proxy": expectation - 0.1 * maximum_loss,
        "iv_plus_10pct_proxy": expectation + 0.1 * maximum_loss,
    }


def stress_passed(results: dict[str, float]) -> bool:
    required = [
        value
        for key, value in results.items()
        if key.endswith("expected_pnl") and key != "baseline_expected_pnl"
    ]
    return bool(required) and min(required) > 0
