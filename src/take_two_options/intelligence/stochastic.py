"""Seeded SDE path engines for GBM, local volatility, Heston, and Heston jumps."""

from __future__ import annotations

import math
from dataclasses import dataclass

from take_two_options.intelligence._numpy import NDArray, np
from take_two_options.intelligence.schemas import (
    LocalVolatilityNode,
    SimulationPolicy,
    SimulationRegime,
    SimulationRegimeConfig,
    StochasticModel,
)


@dataclass(frozen=True)
class StochasticPathSet:
    model: StochasticModel
    regime: SimulationRegime
    seed: int
    times_years: NDArray
    spots: NDArray
    variances: NDArray
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]


def _seed(base: int, model: StochasticModel, regime: SimulationRegime) -> int:
    model_offset = {
        StochasticModel.GBM: 0,
        StochasticModel.LOCAL_VOLATILITY: 10_000,
        StochasticModel.HESTON: 20_000,
        StochasticModel.HESTON_JUMP: 30_000,
    }[model]
    regime_offset = {
        SimulationRegime.NEUTRAL: 0,
        SimulationRegime.THESIS: 1_000,
        SimulationRegime.ADVERSE: 2_000,
        SimulationRegime.RUPTURE: 3_000,
    }[regime]
    return base + model_offset + regime_offset


def _volatility_slice(
    nodes: list[LocalVolatilityNode],
    *,
    time_years: float,
    moneyness: NDArray,
) -> NDArray:
    grouped: dict[float, list[LocalVolatilityNode]] = {}
    for node in nodes:
        grouped.setdefault(node.time_years, []).append(node)
    times = sorted(grouped)

    def at_time(selected_time: float) -> NDArray:
        selected = sorted(grouped[selected_time], key=lambda node: node.moneyness)
        x = np.asarray([node.moneyness for node in selected], dtype=float)
        y = np.asarray([node.volatility for node in selected], dtype=float)
        if len(x) == 1:
            return np.full_like(moneyness, y[0])
        return np.interp(moneyness, x, y, left=y[0], right=y[-1])

    if time_years <= times[0]:
        return at_time(times[0])
    if time_years >= times[-1]:
        return at_time(times[-1])
    upper_index = int(np.searchsorted(np.asarray(times), time_years, side="right"))
    lower_time = times[upper_index - 1]
    upper_time = times[upper_index]
    weight = (time_years - lower_time) / (upper_time - lower_time)
    return (1 - weight) * at_time(lower_time) + weight * at_time(upper_time)


def _jump_increment(
    rng: np.random.Generator,
    *,
    paths: int,
    dt: float,
    regime: SimulationRegimeConfig,
) -> NDArray:
    jump = regime.jump
    counts = rng.poisson(jump.intensity_per_year * dt, size=paths)
    standard = rng.standard_normal(paths)
    return counts * jump.log_mean + np.sqrt(counts) * jump.log_volatility * standard


def _jump_compensator(regime: SimulationRegimeConfig) -> float:
    jump = regime.jump
    expected_multiplier_minus_one = math.exp(
        jump.log_mean + 0.5 * jump.log_volatility**2
    ) - 1
    return jump.intensity_per_year * expected_multiplier_minus_one


def simulate_path_set(
    *,
    spot: float,
    policy: SimulationPolicy,
    model: StochasticModel,
    regime: SimulationRegimeConfig,
) -> StochasticPathSet:
    """Simulate a full path matrix; each model remains separately identifiable."""
    if spot <= 0:
        raise ValueError("spot must be positive")
    seed = _seed(policy.seed, model, regime.regime)
    rng = np.random.default_rng(seed)
    horizon_years = policy.horizon_days / 365.0
    dt = horizon_years / policy.steps
    sqrt_dt = math.sqrt(dt)
    times = np.linspace(0.0, horizon_years, policy.steps + 1)
    spots = np.empty((policy.paths, policy.steps + 1), dtype=float)
    variances = np.empty_like(spots)
    spots[:, 0] = spot
    initial_volatility = policy.initial_volatility
    initial_variance = max(initial_volatility**2, 1e-10)
    scenario_volatility = initial_volatility * regime.volatility_multiplier
    scenario_variance = max(scenario_volatility**2, 1e-10)
    variances[:, 0] = initial_variance
    warnings: list[str] = []
    assumptions: tuple[str, ...]

    if model is StochasticModel.GBM:
        transition_steps = max(round(policy.steps * 0.20), 1)
        for step in range(1, policy.steps + 1):
            transition = min(step / transition_steps, 1.0)
            step_variance = (
                (1 - transition) * initial_variance
                + transition * scenario_variance
            )
            step_volatility = math.sqrt(step_variance)
            z = rng.standard_normal(policy.paths)
            spots[:, step] = spots[:, step - 1] * np.exp(
                (regime.annual_drift - 0.5 * step_variance) * dt
                + step_volatility * sqrt_dt * z
            )
            variances[:, step] = step_variance
        assumptions = (
            "Exact lognormal GBM increments with configured real-world drift.",
            "Volatility is constant within each regime.",
        )
    elif model is StochasticModel.LOCAL_VOLATILITY:
        transition_steps = max(round(policy.steps * 0.20), 1)
        for step in range(1, policy.steps + 1):
            previous = spots[:, step - 1]
            base_local_volatility = _volatility_slice(
                policy.local_volatility_nodes,
                time_years=times[step - 1],
                moneyness=previous / spot,
            )
            transition = min(step / transition_steps, 1.0)
            local_volatility = base_local_volatility * (
                1
                + transition * (regime.volatility_multiplier - 1)
            )
            local_variance = np.maximum(local_volatility**2, 1e-10)
            z = rng.standard_normal(policy.paths)
            spots[:, step] = previous * np.exp(
                (regime.annual_drift - 0.5 * local_variance) * dt
                + local_volatility * sqrt_dt * z
            )
            variances[:, step] = local_variance
        assumptions = (
            "Local volatility is interpolated over time and spot moneyness.",
            "Configured nodes require calibration to a point-in-time OPRA IV surface.",
        )
    else:
        heston = policy.heston
        correlation_scale = math.sqrt(max(1.0 - heston.correlation**2, 0.0))
        target_variance_scale = (
            regime.volatility_multiplier**2
            * (1.0 + regime.initial_iv_shift) ** 2
        )
        variances[:, 0] = max(heston.initial_variance, 1e-10)
        compensator = (
            _jump_compensator(regime)
            if model is StochasticModel.HESTON_JUMP
            else 0.0
        )
        for step in range(1, policy.steps + 1):
            previous_variance = np.maximum(variances[:, step - 1], 0.0)
            z_spot = rng.standard_normal(policy.paths)
            z_independent = rng.standard_normal(policy.paths)
            z_variance = heston.correlation * z_spot + correlation_scale * z_independent
            jump_increment = (
                _jump_increment(rng, paths=policy.paths, dt=dt, regime=regime)
                if model is StochasticModel.HESTON_JUMP
                else np.zeros(policy.paths)
            )
            spots[:, step] = spots[:, step - 1] * np.exp(
                (
                    regime.annual_drift
                    - compensator
                    - 0.5 * previous_variance
                )
                * dt
                + np.sqrt(previous_variance) * sqrt_dt * z_spot
                + jump_increment
            )
            next_variance = (
                previous_variance
                + heston.mean_reversion
                * (
                    heston.long_run_variance
                    * target_variance_scale
                    - previous_variance
                )
                * dt
                + heston.vol_of_variance
                * np.sqrt(previous_variance)
                * sqrt_dt
                * z_variance
            )
            variances[:, step] = np.maximum(next_variance, 0.0)
        if heston.calibration_status != "calibrated":
            warnings.append(
                f"Heston parameters are {heston.calibration_status}; outputs are sensitivity tests."
            )
        assumptions = (
            "Heston variance uses full-truncation Euler discretization.",
            "Spot/variance Brownian shocks use the configured correlation.",
            (
                "Compound-Poisson lognormal jumps with drift compensation."
                if model is StochasticModel.HESTON_JUMP
                else "No discrete jumps in this model."
            ),
        )
    spots = np.clip(spots, 1e-8, 1e8)
    variances = np.clip(variances, 0.0, 25.0)
    return StochasticPathSet(
        model=model,
        regime=regime.regime,
        seed=seed,
        times_years=times,
        spots=spots,
        variances=variances,
        assumptions=assumptions,
        warnings=tuple(warnings),
    )


def simulate_all_models(
    *,
    spot: float,
    policy: SimulationPolicy,
) -> list[StochasticPathSet]:
    return [
        simulate_path_set(spot=spot, policy=policy, model=model, regime=regime)
        for regime in policy.regimes
        for model in policy.models
    ]
