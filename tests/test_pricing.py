import pytest

from take_two_options.candidates import generate_candidates
from take_two_options.domain import MarketDataBundle, PositionSide
from take_two_options.pricing import (
    analyze_risk,
    estimate_execution,
    payoff_pnl_at_expiration,
)


def _candidates(bundle: MarketDataBundle):  # type: ignore[no-untyped-def]
    candidates = generate_candidates(bundle)
    for candidate in candidates:
        analyze_risk(candidate, bundle)
    return {candidate.id: candidate for candidate in candidates}


def test_long_call_uses_ask_multiplier_fees_and_slippage(bundle: MarketDataBundle) -> None:
    candidate = _candidates(bundle)["ttwo-long-call"]

    assert candidate.execution_estimate is not None
    assert candidate.risk_metrics is not None
    assert candidate.execution_estimate.total_entry_cost == pytest.approx(3002.15)
    assert candidate.risk_metrics.max_loss == pytest.approx(3002.15)
    assert candidate.risk_metrics.break_even_points == pytest.approx([290.0215])
    assert payoff_pnl_at_expiration(candidate, 300.0) == pytest.approx(997.85)


def test_long_put_payoff_and_break_even(bundle: MarketDataBundle) -> None:
    candidate = _candidates(bundle)["ttwo-long-put"]

    assert candidate.risk_metrics is not None
    assert candidate.risk_metrics.max_loss == pytest.approx(2702.15)
    assert candidate.risk_metrics.max_gain == pytest.approx(23297.85)
    assert candidate.risk_metrics.break_even_points == pytest.approx([232.9785])
    assert payoff_pnl_at_expiration(candidate, 0.0) == pytest.approx(23297.85)


def test_bull_call_spread_is_bounded_and_uses_executable_net_debit(
    bundle: MarketDataBundle,
) -> None:
    candidate = _candidates(bundle)["ttwo-bull-call-spread"]

    assert candidate.execution_estimate is not None
    assert candidate.risk_metrics is not None
    assert candidate.execution_estimate.total_entry_cost == pytest.approx(1104.30)
    assert candidate.risk_metrics.max_loss == pytest.approx(1104.30)
    assert candidate.risk_metrics.max_gain == pytest.approx(895.70)
    assert candidate.risk_metrics.break_even_points == pytest.approx([271.043])
    assert payoff_pnl_at_expiration(candidate, 400.0) == pytest.approx(895.70)


def test_bear_put_spread_is_bounded(bundle: MarketDataBundle) -> None:
    candidate = _candidates(bundle)["ttwo-bear-put-spread"]

    assert candidate.risk_metrics is not None
    assert candidate.risk_metrics.max_loss == pytest.approx(704.30)
    assert candidate.risk_metrics.max_gain == pytest.approx(295.70)
    assert candidate.risk_metrics.break_even_points == pytest.approx([252.957])
    assert payoff_pnl_at_expiration(candidate, 0.0) == pytest.approx(295.70)


def test_multi_leg_credit_uses_short_bid_and_long_ask(bundle: MarketDataBundle) -> None:
    candidate = _candidates(bundle)["ttwo-bull-call-spread"].model_copy(deep=True)
    candidate.legs[0].side = PositionSide.SHORT
    candidate.legs[1].side = PositionSide.LONG

    execution = estimate_execution(candidate, bundle)

    assert execution.executable_debit == 0.0
    assert execution.executable_credit == pytest.approx(745.70)
    assert execution.total_entry_cost == pytest.approx(-745.70)


def test_greeks_scale_with_contract_multiplier(bundle: MarketDataBundle) -> None:
    full_candidate = _candidates(bundle)["ttwo-long-call"]
    half_bundle = bundle.model_copy(deep=True)
    for quote in half_bundle.option_quotes:
        quote.contract.multiplier = 50.0
        quote.contract.deliverable = "50 TTWO common shares"
    half_candidate = _candidates(half_bundle)["ttwo-long-call"]

    assert full_candidate.risk_metrics is not None
    assert half_candidate.risk_metrics is not None
    assert half_candidate.risk_metrics.net_delta == pytest.approx(
        full_candidate.risk_metrics.net_delta / 2, rel=1e-5
    )
    assert half_candidate.risk_metrics.net_vega == pytest.approx(
        full_candidate.risk_metrics.net_vega / 2, rel=1e-5
    )
