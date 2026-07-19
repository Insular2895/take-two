import pytest

from take_two_options.candidates import generate_candidates
from take_two_options.domain import MarketDataBundle
from take_two_options.pricing import analyze_risk
from take_two_options.scenarios import deterministic_scenarios, monte_carlo_scenarios


def _long_call(bundle: MarketDataBundle):  # type: ignore[no-untyped-def]
    candidate = next(item for item in generate_candidates(bundle) if item.id == "ttwo-long-call")
    analyze_risk(candidate, bundle)
    return candidate


def test_required_deterministic_scenarios_are_present(bundle: MarketDataBundle) -> None:
    scenarios = deterministic_scenarios(_long_call(bundle), bundle)
    names = {scenario.name for scenario in scenarios}

    assert {
        "bullish_gap",
        "bearish_gap",
        "iv_crush",
        "iv_expansion",
        "gta_delay",
        "ex_dividend",
        "liquidity_stress",
    } <= names
    stressed = next(item for item in scenarios if item.name == "gta_delay")
    assert stressed.attribution is not None
    attribution_total = sum(stressed.attribution.model_dump().values())
    assert attribution_total == pytest.approx(stressed.pnl, abs=1e-5)


def test_monte_carlo_is_reproducible_by_seed(bundle: MarketDataBundle) -> None:
    first = _long_call(bundle)
    second = _long_call(bundle.model_copy(deep=True))

    first_results = monte_carlo_scenarios(first, bundle)
    second_results = monte_carlo_scenarios(second, bundle.model_copy(deep=True))

    assert [item.model_dump() for item in first_results] == [
        item.model_dump() for item in second_results
    ]
