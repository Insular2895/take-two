"""Legacy V2 seeded terminal-price models kept for non-regression."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from take_two_options.domain import MarketDataBundle, SimulationModel
from take_two_options.quantitative.contracts import (
    DEFAULT_QUANT_CONVENTIONS,
    Measure,
    ModelEligibility,
)


@dataclass(frozen=True)
class SimulationPaths:
    model: SimulationModel
    terminal_spots: list[float]
    terminal_variances: list[float]
    assumptions: list[str]
    measure: Measure = Measure.RISK_NEUTRAL
    eligibility: ModelEligibility = ModelEligibility.DIAGNOSTIC_ONLY


def _poisson(rng: random.Random, intensity: float) -> int:
    if intensity <= 0:
        return 0
    limit = math.exp(-intensity)
    product = 1.0
    count = 0
    while product > limit:
        count += 1
        product *= rng.random()
    return count - 1


def simulate_terminal_spots(
    bundle: MarketDataBundle,
    model: SimulationModel,
) -> SimulationPaths:
    offsets = {
        SimulationModel.GBM: 0,
        SimulationModel.MERTON_JUMP_DIFFUSION: 10_000,
        SimulationModel.HESTON_FULL_TRUNCATION: 20_000,
    }
    rng = random.Random(bundle.monte_carlo_seed + offsets[model])
    horizon = bundle.monte_carlo_horizon_days / DEFAULT_QUANT_CONVENTIONS.calendar_day_basis
    rate = bundle.risk_free_rate
    dividend_yield = bundle.continuous_dividend_yield
    spot = bundle.underlying.price
    volatility = bundle.annualized_volatility
    terminal_spots: list[float] = []
    terminal_variances: list[float] = []

    if model is SimulationModel.GBM:
        drift = (rate - dividend_yield - 0.5 * volatility * volatility) * horizon
        diffusion = volatility * math.sqrt(horizon)
        for _ in range(bundle.monte_carlo_paths):
            terminal_spots.append(spot * math.exp(drift + diffusion * rng.gauss(0.0, 1.0)))
            terminal_variances.append(volatility * volatility)
        assumptions = [
            "Exact terminal GBM under constant volatility",
            "Risk-neutral drift net of continuous dividend yield",
        ]
    elif model is SimulationModel.MERTON_JUMP_DIFFUSION:
        jump_parameters = bundle.simulation.jump
        diffusion_vol = jump_parameters.diffusion_volatility or volatility
        steps = bundle.simulation.steps
        dt = horizon / steps
        jump_compensator = jump_parameters.jump_intensity * (
            math.exp(
                jump_parameters.jump_mean
                + 0.5 * jump_parameters.jump_volatility * jump_parameters.jump_volatility
            )
            - 1.0
        )
        for _ in range(bundle.monte_carlo_paths):
            log_spot = math.log(spot)
            for _step in range(steps):
                jump_count = _poisson(rng, jump_parameters.jump_intensity * dt)
                jump_sum = sum(
                    rng.gauss(jump_parameters.jump_mean, jump_parameters.jump_volatility)
                    for _jump in range(jump_count)
                )
                log_spot += (
                    (rate - dividend_yield - jump_compensator - 0.5 * diffusion_vol * diffusion_vol)
                    * dt
                    + diffusion_vol * math.sqrt(dt) * rng.gauss(0.0, 1.0)
                    + jump_sum
                )
            terminal_spots.append(math.exp(max(min(log_spot, 50.0), -50.0)))
            terminal_variances.append(diffusion_vol * diffusion_vol)
        assumptions = [
            "Merton compound-Poisson lognormal jumps",
            f"Jump parameters are {jump_parameters.calibration_status.value}",
            "Jump compensator is included in risk-neutral drift",
        ]
    else:
        heston_parameters = bundle.simulation.heston
        steps = bundle.simulation.steps
        dt = horizon / steps
        correlation_scale = math.sqrt(max(1.0 - heston_parameters.correlation**2, 0.0))
        for _ in range(bundle.monte_carlo_paths):
            log_spot = math.log(spot)
            variance = heston_parameters.initial_variance
            for _step in range(steps):
                positive_variance = max(variance, 0.0)
                z_spot = rng.gauss(0.0, 1.0)
                z_independent = rng.gauss(0.0, 1.0)
                z_variance = (
                    heston_parameters.correlation * z_spot + correlation_scale * z_independent
                )
                log_spot += (rate - dividend_yield - 0.5 * positive_variance) * dt + math.sqrt(
                    positive_variance * dt
                ) * z_spot
                variance += (
                    heston_parameters.mean_reversion
                    * (heston_parameters.long_run_variance - positive_variance)
                    * dt
                    + heston_parameters.vol_of_variance
                    * math.sqrt(positive_variance * dt)
                    * z_variance
                )
                variance = max(variance, 0.0)
            terminal_spots.append(math.exp(max(min(log_spot, 50.0), -50.0)))
            terminal_variances.append(variance)
        assumptions = [
            "Heston variance uses full-truncation Euler discretization",
            f"Heston parameters are {heston_parameters.calibration_status.value}",
            "Discretization error remains and is exposed as model risk",
        ]

    return SimulationPaths(
        model=model,
        terminal_spots=terminal_spots,
        terminal_variances=terminal_variances,
        assumptions=assumptions,
    )
