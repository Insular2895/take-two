from take_two_options.candidates import generate_candidates
from take_two_options.domain import CandidateStatus, FreshnessStatus, MarketDataBundle, OptionType
from take_two_options.pricing import analyze_risk
from take_two_options.scenarios import deterministic_scenarios
from take_two_options.validation import apply_vetoes
from take_two_options.vol_surface import interpolate_surface, surface_diagnostics


def test_surface_interpolates_across_strike_and_expiry(v2_bundle: MarketDataBundle) -> None:
    assert v2_bundle.volatility_surface is not None
    surface = v2_bundle.volatility_surface
    expiration = (
        surface.nodes[0].expiration
        + (surface.nodes[-1].expiration - surface.nodes[0].expiration) / 2
    )

    result = interpolate_surface(
        surface,
        expiration=expiration,
        strike=245.0,
        option_type=OptionType.CALL,
    )

    assert 0.35 < result.volatility < 0.39
    assert not result.extrapolated
    diagnostics = surface_diagnostics(v2_bundle)
    assert diagnostics.available
    assert diagnostics.expiry_count == 2


def test_stale_explicit_surface_blocks_candidate(v2_bundle: MarketDataBundle) -> None:
    assert v2_bundle.volatility_surface is not None
    v2_bundle.volatility_surface.freshness.status = FreshnessStatus.STALE
    v2_bundle.volatility_surface.freshness.is_stale = True
    candidate = next(item for item in generate_candidates(v2_bundle) if item.id == "ttwo-long-call")
    analyze_risk(candidate, v2_bundle)
    deterministic_scenarios(candidate, v2_bundle)

    assert apply_vetoes(candidate, v2_bundle) is CandidateStatus.BLOCKED
    assert any("VOL-SURFACE" in reason for reason in candidate.veto_reasons)
