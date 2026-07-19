import math

from take_two_options.domain import MarketDataBundle, SimulationModel
from take_two_options.simulation import simulate_terminal_spots


def test_jump_and_heston_paths_are_seeded_and_finite(v2_bundle: MarketDataBundle) -> None:
    for model in (
        SimulationModel.MERTON_JUMP_DIFFUSION,
        SimulationModel.HESTON_FULL_TRUNCATION,
    ):
        first = simulate_terminal_spots(v2_bundle, model)
        second = simulate_terminal_spots(v2_bundle.model_copy(deep=True), model)

        assert first == second
        assert all(math.isfinite(spot) and spot > 0 for spot in first.terminal_spots)
        assert all(variance >= 0 for variance in first.terminal_variances)


def test_jump_configuration_can_generate_fatter_left_tail(
    v2_bundle: MarketDataBundle,
) -> None:
    v2_bundle.monte_carlo_paths = 4_000
    v2_bundle.simulation.jump.jump_intensity = 3.0
    v2_bundle.simulation.jump.jump_mean = -0.12
    v2_bundle.simulation.jump.jump_volatility = 0.25
    v2_bundle.simulation.jump.diffusion_volatility = v2_bundle.annualized_volatility
    gbm = sorted(simulate_terminal_spots(v2_bundle, SimulationModel.GBM).terminal_spots)
    jump = sorted(
        simulate_terminal_spots(v2_bundle, SimulationModel.MERTON_JUMP_DIFFUSION).terminal_spots
    )
    index = int(len(gbm) * 0.01)

    assert jump[index] < gbm[index]
