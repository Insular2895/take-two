from take_two_options.domain import MarketDataBundle, ModelReadiness
from take_two_options.engine import analyze_bundle


def test_v2_report_exposes_model_risk_and_all_simulations(
    v2_bundle: MarketDataBundle,
) -> None:
    report = analyze_bundle(v2_bundle)
    long_call = next(item for item in report.candidates if item.id == "ttwo-long-call")
    scenario_names = {scenario.name for scenario in long_call.scenarios}

    assert report.model_readiness is ModelReadiness.SCREEN_GRADE
    assert report.surface_diagnostics is not None
    assert report.surface_diagnostics.available
    assert long_call.pricing_results
    assert "monte_carlo_gbm_p50" in scenario_names
    assert "monte_carlo_merton_jump_diffusion_p50" in scenario_names
    assert "monte_carlo_heston_full_truncation_p50" in scenario_names
