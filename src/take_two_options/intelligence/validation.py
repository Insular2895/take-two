"""V11 promotion gates that reuse stress evidence without laundering old holdouts."""

from __future__ import annotations

from take_two_options.intelligence.schemas import CandidateValidationSummary, SimulationRegime
from take_two_options.intelligence.valuation import StrategyPathValuation
from take_two_options.quantitative.pricing import require_contract_economics
from take_two_options.thesis_scanner.schemas import HistoricalEvidence, ThesisCandidate


def validate_candidate(
    candidate: ThesisCandidate,
    valuations: list[StrategyPathValuation],
    *,
    historical_evidence: HistoricalEvidence,
) -> CandidateValidationSummary:
    """Combine new crisis stresses with the preserved contaminated-holdout status."""
    neutral = [
        item.metrics.expected_pnl_usd
        for item in valuations
        if item.metrics.regime is SimulationRegime.NEUTRAL
    ]
    adverse = [
        item.metrics.expected_pnl_usd
        for item in valuations
        if item.metrics.regime is SimulationRegime.ADVERSE
    ]
    rupture = [
        item.metrics.expected_pnl_usd
        for item in valuations
        if item.metrics.regime is SimulationRegime.RUPTURE
    ]
    stress_cvars = [
        item.metrics.cvar_95_usd
        for item in valuations
        if item.metrics.regime in {SimulationRegime.ADVERSE, SimulationRegime.RUPTURE}
    ]
    spread_cost = 0.0
    for leg in candidate.base_candidate.legs:
        if leg.quote.bid is None or leg.quote.ask is None:
            raise ValueError("BLOCKED_BID_ASK_UNKNOWN")
        spread_cost += (
            (leg.quote.ask - leg.quote.bid)
            * leg.quantity
            * require_contract_economics(leg.quote)
        )
    baseline = min(neutral, default=-float("inf"))
    results = {
        "worst_neutral_expected_pnl_usd": baseline,
        "spread_x1_5_expected_pnl_usd": baseline - 0.5 * spread_cost,
        "slippage_x2_expected_pnl_usd": (
            baseline - candidate.base_candidate.risk.slippage
        ),
        "commissions_x2_expected_pnl_usd": (
            baseline - candidate.base_candidate.risk.fees
        ),
        "worst_adverse_expected_pnl_usd": min(adverse, default=-float("inf")),
        "worst_rupture_expected_pnl_usd": min(rupture, default=-float("inf")),
        "worst_stress_cvar_usd": max(stress_cvars, default=float("inf")),
    }
    finite_expectations = [
        results["spread_x1_5_expected_pnl_usd"],
        results["slippage_x2_expected_pnl_usd"],
        results["commissions_x2_expected_pnl_usd"],
        results["worst_adverse_expected_pnl_usd"],
        results["worst_rupture_expected_pnl_usd"],
    ]
    stress_passed = (
        min(finite_expectations) > 0
        and results["worst_stress_cvar_usd"]
        <= candidate.execution.total_cost_usd * 0.80
    )
    contaminated = historical_evidence.status == "weak_contaminated"
    reasons = [
        "V7-V9 holdouts were inspected and cannot be reused for promotion.",
        "No fresh nested walk-forward sample or locked holdout accompanies V11.",
        "Paper monitoring has not been completed.",
    ]
    if not stress_passed:
        reasons.append("At least one cost, adverse, rupture, or CVaR stress gate failed.")
    return CandidateValidationSummary(
        candidate_id=candidate.candidate_id,
        walk_forward_status="contaminated" if contaminated else "insufficient_data",
        holdout_status="contaminated" if contaminated else "insufficient_data",
        stress_status="passed" if stress_passed else "failed",
        stress_results=results,
        paper_status="not_run",
        reasons=reasons,
    )
