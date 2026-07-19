"""Deterministic and seeded scenario analysis for research candidates."""

from __future__ import annotations

from datetime import timedelta

from take_two_options.american import option_model_value
from take_two_options.domain import (
    MarketDataBundle,
    ScenarioAttribution,
    ScenarioResult,
    SimulationModel,
    StrategyCandidate,
)
from take_two_options.simulation import simulate_terminal_spots
from take_two_options.vol_surface import effective_volatility


def _position_value(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    spot: float,
    days_forward: int,
    iv_shift: float,
    rate_shift: float = 0.0,
    volatility_override: float | None = None,
) -> float:
    valuation_time = bundle.analysis_timestamp + timedelta(days=days_forward)
    value = 0.0
    for leg in candidate.legs:
        if leg.instrument_type == "stock":
            value += leg.side.sign * leg.quantity * spot
            continue
        assert leg.option_quote is not None
        quote = leg.option_quote
        contract = quote.contract
        base_volatility = effective_volatility(bundle, quote).volatility
        volatility = max(
            volatility_override if volatility_override is not None else base_volatility + iv_shift,
            0.01,
        )
        option_value = option_model_value(
            quote,
            bundle,
            spot=spot,
            valuation_time=valuation_time,
            volatility=volatility,
            rate=bundle.risk_free_rate + rate_shift,
        )
        value += leg.side.sign * leg.quantity * contract.multiplier * option_value
    return value


def _scenario(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    name: str,
    spot: float,
    days_forward: int,
    iv_shift: float,
    assumptions: list[str],
    liquidity_penalty: bool = False,
    rate_shift: float = 0.0,
) -> ScenarioResult:
    if candidate.execution_estimate is None:
        raise ValueError("candidate must be priced before scenarios are generated")
    value = _position_value(
        candidate,
        bundle,
        spot=spot,
        days_forward=days_forward,
        iv_shift=iv_shift,
        rate_shift=rate_shift,
    )
    pnl = value - candidate.execution_estimate.total_entry_cost
    exit_penalty = 0.0
    if liquidity_penalty:
        exposure = max(abs(candidate.execution_estimate.total_entry_cost), 1.0)
        exit_penalty = exposure * (1.0 - candidate.execution_estimate.liquidity_score) * 0.10
        pnl -= exit_penalty
        assumptions = [*assumptions, "Exit penalty equals 10% of entry exposure times illiquidity"]
    attribution = _attribution(
        candidate,
        bundle,
        spot=spot,
        days_forward=days_forward,
        iv_shift=iv_shift,
        rate_shift=rate_shift,
        pnl=pnl,
        exit_penalty=exit_penalty,
    )
    return ScenarioResult(
        name=name,
        spot=round(spot, 6),
        days_forward=days_forward,
        iv_shift=iv_shift,
        pnl=round(pnl, 6),
        estimated_value=round(value, 6),
        assumptions=assumptions,
        attribution=attribution,
    )


def _attribution(
    candidate: StrategyCandidate,
    bundle: MarketDataBundle,
    *,
    spot: float,
    days_forward: int,
    iv_shift: float,
    rate_shift: float,
    pnl: float,
    exit_penalty: float = 0.0,
    volatility_override: float | None = None,
) -> ScenarioAttribution | None:
    risk = candidate.risk_metrics
    execution = candidate.execution_estimate
    if risk is None or execution is None:
        return None
    initial_value = _position_value(
        candidate,
        bundle,
        spot=bundle.underlying.price,
        days_forward=0,
        iv_shift=0.0,
    )
    spot_value = _position_value(
        candidate,
        bundle,
        spot=spot,
        days_forward=0,
        iv_shift=0.0,
    )
    time_value = _position_value(
        candidate,
        bundle,
        spot=spot,
        days_forward=days_forward,
        iv_shift=0.0,
    )
    volatility_value = _position_value(
        candidate,
        bundle,
        spot=spot,
        days_forward=days_forward,
        iv_shift=iv_shift,
        volatility_override=volatility_override,
    )
    rate_value = _position_value(
        candidate,
        bundle,
        spot=spot,
        days_forward=days_forward,
        iv_shift=iv_shift,
        rate_shift=rate_shift,
        volatility_override=volatility_override,
    )
    spot_change = spot - bundle.underlying.price
    delta = risk.net_delta * spot_change
    gamma = (spot_value - initial_value) - delta
    theta = time_value - spot_value
    vega = volatility_value - time_value
    rho = rate_value - volatility_value
    execution_costs = initial_value - execution.total_entry_cost - exit_penalty
    residual = pnl - delta - gamma - theta - vega - rho - execution_costs
    return ScenarioAttribution(
        delta=round(delta, 6),
        gamma=round(gamma, 6),
        theta=round(theta, 6),
        vega=round(vega, 6),
        rho=round(rho, 6),
        execution_costs=round(execution_costs, 6),
        residual=round(residual, 6),
    )


def deterministic_scenarios(
    candidate: StrategyCandidate, bundle: MarketDataBundle
) -> list[ScenarioResult]:
    spot = bundle.underlying.price
    horizon = bundle.monte_carlo_horizon_days
    scenarios = [
        _scenario(
            candidate,
            bundle,
            name="base_time_passage",
            spot=spot,
            days_forward=horizon,
            iv_shift=0.0,
            assumptions=[
                "Underlying unchanged",
                "Flat risk-free rate",
                "Bundle dividend yield and discrete forecasts are applied",
            ],
        ),
        _scenario(
            candidate,
            bundle,
            name="bullish_gap",
            spot=spot * 1.15,
            days_forward=horizon,
            iv_shift=0.05,
            assumptions=["Illustrative +15% spot gap", "Absolute IV shift +5 points"],
        ),
        _scenario(
            candidate,
            bundle,
            name="bearish_gap",
            spot=spot * 0.85,
            days_forward=horizon,
            iv_shift=0.10,
            assumptions=["Illustrative -15% spot gap", "Absolute IV shift +10 points"],
        ),
        _scenario(
            candidate,
            bundle,
            name="iv_crush",
            spot=spot,
            days_forward=horizon,
            iv_shift=-0.12,
            assumptions=["Absolute IV shift -12 points", "No spot move"],
        ),
        _scenario(
            candidate,
            bundle,
            name="iv_expansion",
            spot=spot,
            days_forward=horizon,
            iv_shift=0.12,
            assumptions=["Absolute IV shift +12 points", "No spot move"],
        ),
        _scenario(
            candidate,
            bundle,
            name="gta_delay",
            spot=spot * 0.90,
            days_forward=horizon,
            iv_shift=0.08,
            assumptions=["Illustrative release-delay shock", "Spot -10%", "IV +8 points"],
        ),
        _scenario(
            candidate,
            bundle,
            name="ex_dividend",
            spot=spot * 0.99,
            days_forward=min(horizon, 30),
            iv_shift=0.0,
            assumptions=["Illustrative 1% ex-dividend spot adjustment", "No dividend forecast"],
        ),
        _scenario(
            candidate,
            bundle,
            name="liquidity_stress",
            spot=spot,
            days_forward=min(horizon, 30),
            iv_shift=0.03,
            assumptions=["Wider exit costs under stressed liquidity"],
            liquidity_penalty=True,
        ),
    ]
    candidate.scenarios = scenarios
    return scenarios


def monte_carlo_scenarios(
    candidate: StrategyCandidate, bundle: MarketDataBundle
) -> list[ScenarioResult]:
    """Return seeded P05/P50/P95 outcomes for every configured simulation model."""
    if candidate.execution_estimate is None:
        raise ValueError("candidate must be priced before Monte Carlo")
    results: list[ScenarioResult] = []
    for model in bundle.simulation.models:
        paths = simulate_terminal_spots(bundle, model)
        outcomes: list[tuple[float, float, float, float, float | None]] = []
        for index, terminal_spot in enumerate(paths.terminal_spots):
            volatility_override = None
            iv_shift = 0.0
            if model is SimulationModel.HESTON_FULL_TRUNCATION:
                volatility_override = max(paths.terminal_variances[index] ** 0.5, 0.01)
                iv_shift = volatility_override - bundle.annualized_volatility
            value = _position_value(
                candidate,
                bundle,
                spot=terminal_spot,
                days_forward=bundle.monte_carlo_horizon_days,
                iv_shift=iv_shift,
                volatility_override=volatility_override,
            )
            outcomes.append(
                (
                    value - candidate.execution_estimate.total_entry_cost,
                    terminal_spot,
                    value,
                    iv_shift,
                    volatility_override,
                )
            )
        outcomes.sort(key=lambda item: (item[0], item[1]))
        for label, quantile in (("p05", 0.05), ("p50", 0.50), ("p95", 0.95)):
            index = min(int((len(outcomes) - 1) * quantile), len(outcomes) - 1)
            pnl, terminal_spot, value, iv_shift, volatility_override = outcomes[index]
            results.append(
                ScenarioResult(
                    name=f"monte_carlo_{model.value}_{label}",
                    spot=round(terminal_spot, 6),
                    days_forward=bundle.monte_carlo_horizon_days,
                    iv_shift=round(iv_shift, 8),
                    pnl=round(pnl, 6),
                    estimated_value=round(value, 6),
                    assumptions=[
                        *paths.assumptions,
                        f"Seed={bundle.monte_carlo_seed}; paths={bundle.monte_carlo_paths}",
                    ],
                    attribution=_attribution(
                        candidate,
                        bundle,
                        spot=terminal_spot,
                        days_forward=bundle.monte_carlo_horizon_days,
                        iv_shift=iv_shift,
                        rate_shift=0.0,
                        pnl=pnl,
                        volatility_override=volatility_override,
                    ),
                )
            )
    candidate.scenarios.extend(results)
    return results
