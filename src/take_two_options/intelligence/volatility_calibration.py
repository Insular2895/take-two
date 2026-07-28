"""Point-in-time Dupire local-volatility extraction from the V10 option chain."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from typing import Literal

from take_two_options.domain import OptionType
from take_two_options.intelligence._numpy import np
from take_two_options.intelligence.schemas import (
    LocalVolatilityCalibrationReport,
    LocalVolatilityNode,
)
from take_two_options.thesis_scanner.schemas import ThesisChain, ThesisQuote


def _iv_by_moneyness(
    quotes: list[ThesisQuote],
    *,
    spot: float,
    moneyness_grid: list[float],
) -> list[float]:
    ordered = sorted(
        (
            quote.strike / spot,
            quote.implied_volatility,
        )
        for quote in quotes
        if quote.implied_volatility is not None
    )
    x = np.asarray([item[0] for item in ordered], dtype=float)
    y = np.asarray([item[1] for item in ordered], dtype=float)
    interpolated = np.interp(
        np.asarray(moneyness_grid, dtype=float),
        x,
        y,
        left=y[0],
        right=y[-1],
    )
    return [float(value) for value in interpolated]


def calibrate_local_volatility(
    chain: ThesisChain,
    *,
    rate: float,
    dividend_yield: float,
) -> tuple[list[LocalVolatilityNode], LocalVolatilityCalibrationReport]:
    """Finite-difference Dupire total variance with explicit fallbacks."""
    by_expiration: dict[date, list[ThesisQuote]] = defaultdict(list)
    for quote in chain.quotes:
        if quote.option_type is OptionType.CALL and quote.implied_volatility is not None:
            by_expiration[quote.expiration].append(quote)
    valid_expirations = sorted(
        expiration
        for expiration, quotes in by_expiration.items()
        if len(quotes) >= 3 and expiration > chain.as_of.date()
    )
    moneyness_grid = sorted(
        {
            round(quote.strike / chain.spot, 8)
            for expiration in valid_expirations
            for quote in by_expiration[expiration]
            if 0.5 <= quote.strike / chain.spot <= 2.0
        }
    )
    warnings: list[str] = []
    if len(valid_expirations) < 2 or len(moneyness_grid) < 3:
        return [], LocalVolatilityCalibrationReport(
            status="insufficient_data",
            method="dupire_total_variance_finite_difference",
            expirations=len(valid_expirations),
            moneyness_nodes=len(moneyness_grid),
            output_nodes=0,
            fallback_nodes=0,
            source_ids=sorted({quote.source_id for quote in chain.quotes}),
            warnings=[
                "Dupire extraction needs at least two expirations and three strikes."
            ],
        )
    times = np.asarray(
        [
            (expiration - chain.as_of.date()).days / 365.0
            for expiration in valid_expirations
        ],
        dtype=float,
    )
    implied_volatility = np.asarray(
        [
            _iv_by_moneyness(
                by_expiration[expiration],
                spot=chain.spot,
                moneyness_grid=moneyness_grid,
            )
            for expiration in valid_expirations
        ],
        dtype=float,
    )
    total_variance = implied_volatility**2 * times[:, None]
    time_derivative = np.gradient(total_variance, times, axis=0, edge_order=1)
    log_moneyness = np.log(np.asarray(moneyness_grid, dtype=float))
    strike_derivative = np.asarray(
        [
            np.gradient(row, log_moneyness, edge_order=1)
            for row in total_variance
        ]
    )
    strike_second_derivative = np.asarray(
        [
            np.gradient(row, log_moneyness, edge_order=1)
            for row in strike_derivative
        ]
    )
    output: list[LocalVolatilityNode] = []
    fallback_nodes = 0
    for time_index, time_years in enumerate(times):
        forward_log_shift = (rate - dividend_yield) * float(time_years)
        for strike_index, moneyness in enumerate(moneyness_grid):
            total = float(total_variance[time_index, strike_index])
            first = float(strike_derivative[time_index, strike_index])
            second = float(strike_second_derivative[time_index, strike_index])
            log_forward_moneyness = math.log(moneyness) - forward_log_shift
            denominator = (
                (1.0 - log_forward_moneyness * first / max(total, 1e-12)) ** 2
                - 0.25
                * (0.25 + 1.0 / max(total, 1e-12))
                * first**2
                + 0.5 * second
            )
            numerator = float(time_derivative[time_index, strike_index])
            local_variance = numerator / denominator if denominator > 1e-10 else -1.0
            if not math.isfinite(local_variance) or local_variance <= 1e-8:
                fallback_nodes += 1
                local_volatility = float(
                    implied_volatility[time_index, strike_index]
                )
            else:
                local_volatility = math.sqrt(local_variance)
            output.append(
                LocalVolatilityNode(
                    time_years=float(time_years),
                    moneyness=moneyness,
                    volatility=min(max(local_volatility, 0.01), 3.0),
                )
            )
    status: Literal["calibrated", "partial", "insufficient_data"] = "calibrated"
    if fallback_nodes:
        status = "partial"
        warnings.append(
            f"{fallback_nodes} Dupire nodes were unstable and fell back to implied volatility."
        )
    if chain.price_quality != "opra":
        status = "partial"
        warnings.append(
            f"Surface quality is {chain.price_quality}; live OPRA calibration is required."
        )
    warnings.append(
        "Finite differences do not enforce calendar/butterfly arbitrage globally; "
        "the extracted surface remains a research input."
    )
    return output, LocalVolatilityCalibrationReport(
        status=status,
        method="dupire_total_variance_finite_difference",
        expirations=len(valid_expirations),
        moneyness_nodes=len(moneyness_grid),
        output_nodes=len(output),
        fallback_nodes=fallback_nodes,
        source_ids=sorted({quote.source_id for quote in chain.quotes}),
        warnings=warnings,
    )
