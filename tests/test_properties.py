from take_two_options.candidates import generate_candidates
from take_two_options.domain import MarketDataBundle
from take_two_options.pricing import analyze_risk, payoff_pnl_at_expiration


def _priced(bundle: MarketDataBundle):  # type: ignore[no-untyped-def]
    candidates = generate_candidates(bundle)
    for candidate in candidates:
        analyze_risk(candidate, bundle)
    return {candidate.id: candidate for candidate in candidates}


def test_long_call_payoff_is_monotone_in_spot(bundle: MarketDataBundle) -> None:
    candidate = _priced(bundle)["ttwo-long-call"]
    pnls = [payoff_pnl_at_expiration(candidate, spot) for spot in range(0, 501, 5)]
    assert all(left <= right for left, right in zip(pnls, pnls[1:], strict=False))


def test_long_put_payoff_is_inverse_monotone_in_spot(bundle: MarketDataBundle) -> None:
    candidate = _priced(bundle)["ttwo-long-put"]
    pnls = [payoff_pnl_at_expiration(candidate, spot) for spot in range(0, 501, 5)]
    assert all(left >= right for left, right in zip(pnls, pnls[1:], strict=False))


def test_vertical_payoffs_remain_inside_exact_bounds(bundle: MarketDataBundle) -> None:
    candidates = _priced(bundle)
    for candidate_id in ("ttwo-bull-call-spread", "ttwo-bear-put-spread"):
        candidate = candidates[candidate_id]
        assert candidate.risk_metrics is not None
        assert candidate.risk_metrics.max_gain is not None
        assert candidate.risk_metrics.max_loss is not None
        for spot in range(0, 601, 3):
            pnl = payoff_pnl_at_expiration(candidate, spot)
            assert -candidate.risk_metrics.max_loss - 1e-8 <= pnl
            assert pnl <= candidate.risk_metrics.max_gain + 1e-8
