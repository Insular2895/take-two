"""Deterministic offline stress suite with explicit proxy and data gaps."""

from __future__ import annotations

from take_two_options.intelligence.schemas import StressTestResult
from take_two_options.intelligence.valuation import StrategyPathValuation
from take_two_options.quantitative.pricing import require_contract_economics
from take_two_options.thesis_scanner.schemas import ThesisCandidate


def run_stress_suite(
    candidate: ThesisCandidate,
    valuations: list[StrategyPathValuation],
) -> list[StressTestResult]:
    """Evaluate reproducible stresses without representing proxies as calibrated forecasts."""
    neutral = [
        item.metrics.expected_pnl_usd
        for item in valuations
        if item.metrics.regime.value == "neutral"
    ]
    baseline = min(neutral, default=None)
    spread_cost = 0.0
    for leg in candidate.base_candidate.legs:
        if leg.quote.bid is None or leg.quote.ask is None:
            raise ValueError("BLOCKED_BID_ASK_UNKNOWN")
        spread_cost += (
            (leg.quote.ask - leg.quote.bid)
            * leg.quantity
            * require_contract_economics(leg.quote)
        )
    fees = candidate.base_candidate.risk.fees
    slippage = candidate.base_candidate.risk.slippage
    stable_points = [
        point.pnl_usd
        for point in candidate.scenario_points
        if point.iv_case.value == "stable"
    ]
    iv_down_points = [
        point.pnl_usd
        for point in candidate.scenario_points
        if point.iv_case.value == "down"
    ]
    nonterminal_points = [
        point.pnl_usd for point in candidate.scenario_points if not point.terminal
    ]

    def result(
        stress_id: str,
        value: float | None,
        *,
        method: str,
        assumptions: list[str],
        insufficient: str | None = None,
    ) -> StressTestResult:
        status = (
            "data_insufficient"
            if insufficient is not None
            else "passed"
            if value is not None and value > 0
            else "failed"
        )
        return StressTestResult(
            candidate_id=candidate.candidate_id,
            stress_id=stress_id,
            status=status,
            stressed_pnl_usd=value,
            method=method,
            assumptions=assumptions,
            blockers=[insufficient] if insufficient is not None else [],
        )

    return [
        result(
            "catalyst_delay",
            min(nonterminal_points) if nonterminal_points else None,
            method="worst_existing_pre_expiry_checkpoint_proxy",
            assumptions=[
                "Uses the worst V10.1 pre-expiry checkpoint; a true shifted catalyst "
                "requires a dated event surface."
            ],
            insufficient=(
                None
                if nonterminal_points
                else "No pre-expiry checkpoint is available."
            ),
        ),
        result(
            "iv_crush",
            min(iv_down_points) if iv_down_points else None,
            method="v10_1_iv_down_scenario",
            assumptions=["Uses Python-computed V10.1 IV-down scenario values."],
            insufficient=None if iv_down_points else "No IV-down scenario is available.",
        ),
        result(
            "market_sell_off",
            min(stable_points) if stable_points else None,
            method="worst_v10_1_stable_iv_spot_scenario",
            assumptions=["Uses the lowest configured spot scenario at stable IV."],
            insufficient=None if stable_points else "No stable-IV spot grid is available.",
        ),
        result(
            "rates_shock",
            None,
            method="not_computed",
            assumptions=[],
            insufficient="No source-backed rate-path surface is available for repricing.",
        ),
        result(
            "eurusd_adverse",
            baseline,
            method="usd_pnl_unchanged_fx_budget_diagnostic",
            assumptions=[
                "USD P&L is shown unchanged; account-specific EUR conversion stress "
                "requires a dated FX path."
            ],
            insufficient="No historical EUR/USD path is connected to this fixture run.",
        ),
        result(
            "bid_ask_x2",
            baseline - spread_cost if baseline is not None else None,
            method="exact_additional_leg_spread_cost",
            assumptions=["Adds one full current leg-level spread to conservative P&L."],
            insufficient=None if baseline is not None else "Neutral model P&L is unavailable.",
        ),
        result(
            "open_interest_volume_degraded",
            None,
            method="liquidity_gate",
            assumptions=[],
            insufficient="Future OI/volume and fill response cannot be inferred offline.",
        ),
        result(
            "negative_gap",
            min(stable_points) if stable_points else None,
            method="worst_configured_terminal_or_checkpoint_spot",
            assumptions=["Diagnostic grid stress; not a calibrated gap distribution."],
            insufficient=None if stable_points else "No spot grid is available.",
        ),
        result(
            "positive_gap",
            max(stable_points) if stable_points else None,
            method="best_configured_terminal_or_checkpoint_spot",
            assumptions=["Diagnostic upside grid; not a calibrated gap distribution."],
            insufficient=None if stable_points else "No spot grid is available.",
        ),
        result(
            "midpoint_unavailable",
            baseline,
            method="already_prudent_ask_bid_entry",
            assumptions=[
                "V10.1 entry already uses ask for buys and bid for sells, not midpoint."
            ],
            insufficient=None if baseline is not None else "Neutral model P&L is unavailable.",
        ),
        result(
            "prudent_bid_ask_exit",
            baseline - spread_cost if baseline is not None else None,
            method="additional_full_spread_liquidation_proxy",
            assumptions=["Simultaneous broker combo liquidation remains unavailable."],
            insufficient=None if baseline is not None else "Neutral model P&L is unavailable.",
        ),
        result(
            "slippage_x2",
            baseline - slippage if baseline is not None else None,
            method="exact_configured_incremental_slippage",
            assumptions=["Doubles configured initial slippage."],
            insufficient=None if baseline is not None else "Neutral model P&L is unavailable.",
        ),
        result(
            "fees_x2",
            baseline - fees if baseline is not None else None,
            method="exact_configured_incremental_fees",
            assumptions=["Doubles configured commissions."],
            insufficient=None if baseline is not None else "Neutral model P&L is unavailable.",
        ),
        result(
            "early_exit",
            min(nonterminal_points) if nonterminal_points else None,
            method="worst_v10_1_pre_expiry_liquidation_proxy",
            assumptions=["Uses existing Python pre-expiry valuations."],
            insufficient=None if nonterminal_points else "No early-exit checkpoint exists.",
        ),
    ]
