"""Diagnosed implied-volatility solving with a robust bisection baseline."""

from __future__ import annotations

import math
from collections.abc import Callable
from enum import StrEnum

from pydantic import Field

from take_two_options.domain import StrictModel


class ImpliedVolStatus(StrEnum):
    CONVERGED = "converged"
    BELOW_BRACKET = "below_bracket"
    ABOVE_BRACKET = "above_bracket"
    NO_BRACKET = "no_bracket"
    MAX_ITERATIONS = "max_iterations"
    NUMERICAL_FAILURE = "numerical_failure"


class ImpliedVolResult(StrictModel):
    status: ImpliedVolStatus
    method: str = "bisection"
    volatility: float | None = Field(default=None, gt=0)
    target_price: float
    model_price: float | None = None
    residual: float | None = None
    iterations: int = Field(ge=0)
    bracket_low: float = Field(gt=0)
    bracket_high: float = Field(gt=0)
    price_at_low: float | None = None
    price_at_high: float | None = None
    price_tolerance: float = Field(gt=0)
    volatility_tolerance: float = Field(gt=0)
    warnings: tuple[str, ...] = ()

    @property
    def converged(self) -> bool:
        return self.status is ImpliedVolStatus.CONVERGED


def solve_implied_volatility(
    price_function: Callable[[float], float],
    *,
    target_price: float,
    bracket: tuple[float, float] = (0.0001, 5.0),
    price_tolerance: float = 1e-6,
    volatility_tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> ImpliedVolResult:
    """Solve a monotone option-price equation and retain bracket/residual diagnostics."""
    low, high = bracket
    if not 0 < low < high:
        raise ValueError("implied-volatility bracket must satisfy 0 < low < high")
    if target_price < 0 or not math.isfinite(target_price):
        raise ValueError("target price must be finite and non-negative")
    if price_tolerance <= 0 or volatility_tolerance <= 0 or max_iterations <= 0:
        raise ValueError("tolerances and max_iterations must be positive")

    try:
        price_low = float(price_function(low))
        price_high = float(price_function(high))
    except (ArithmeticError, ValueError, RuntimeError) as exc:
        return ImpliedVolResult(
            status=ImpliedVolStatus.NUMERICAL_FAILURE,
            target_price=target_price,
            iterations=0,
            bracket_low=low,
            bracket_high=high,
            price_tolerance=price_tolerance,
            volatility_tolerance=volatility_tolerance,
            warnings=(f"bracket evaluation failed: {exc}",),
        )
    if not math.isfinite(price_low) or not math.isfinite(price_high):
        return ImpliedVolResult(
            status=ImpliedVolStatus.NUMERICAL_FAILURE,
            target_price=target_price,
            iterations=0,
            bracket_low=low,
            bracket_high=high,
            price_at_low=price_low,
            price_at_high=price_high,
            price_tolerance=price_tolerance,
            volatility_tolerance=volatility_tolerance,
            warnings=("bracket prices must be finite",),
        )
    if price_high < price_low:
        return ImpliedVolResult(
            status=ImpliedVolStatus.NO_BRACKET,
            target_price=target_price,
            iterations=0,
            bracket_low=low,
            bracket_high=high,
            price_at_low=price_low,
            price_at_high=price_high,
            price_tolerance=price_tolerance,
            volatility_tolerance=volatility_tolerance,
            warnings=("price function is not increasing over the volatility bracket",),
        )
    if target_price < price_low - price_tolerance:
        status = ImpliedVolStatus.BELOW_BRACKET
    elif target_price > price_high + price_tolerance:
        status = ImpliedVolStatus.ABOVE_BRACKET
    else:
        status = None
    if status is not None:
        return ImpliedVolResult(
            status=status,
            target_price=target_price,
            iterations=0,
            bracket_low=low,
            bracket_high=high,
            price_at_low=price_low,
            price_at_high=price_high,
            price_tolerance=price_tolerance,
            volatility_tolerance=volatility_tolerance,
            warnings=("target price lies outside the configured volatility bracket",),
        )
    if price_high - price_low <= price_tolerance:
        return ImpliedVolResult(
            status=ImpliedVolStatus.NO_BRACKET,
            target_price=target_price,
            iterations=0,
            bracket_low=low,
            bracket_high=high,
            price_at_low=price_low,
            price_at_high=price_high,
            price_tolerance=price_tolerance,
            volatility_tolerance=volatility_tolerance,
            warnings=("price is insensitive to volatility over the configured bracket",),
        )

    midpoint = low
    candidate_price = price_low
    for iteration in range(1, max_iterations + 1):
        midpoint = (low + high) / 2.0
        try:
            candidate_price = float(price_function(midpoint))
        except (ArithmeticError, ValueError, RuntimeError) as exc:
            return ImpliedVolResult(
                status=ImpliedVolStatus.NUMERICAL_FAILURE,
                target_price=target_price,
                iterations=iteration,
                bracket_low=low,
                bracket_high=high,
                price_at_low=price_low,
                price_at_high=price_high,
                price_tolerance=price_tolerance,
                volatility_tolerance=volatility_tolerance,
                warnings=(f"iteration evaluation failed: {exc}",),
            )
        residual = candidate_price - target_price
        if abs(residual) <= price_tolerance or high - low <= volatility_tolerance:
            return ImpliedVolResult(
                status=ImpliedVolStatus.CONVERGED,
                volatility=midpoint,
                target_price=target_price,
                model_price=candidate_price,
                residual=residual,
                iterations=iteration,
                bracket_low=low,
                bracket_high=high,
                price_at_low=price_low,
                price_at_high=price_high,
                price_tolerance=price_tolerance,
                volatility_tolerance=volatility_tolerance,
            )
        if candidate_price < target_price:
            low, price_low = midpoint, candidate_price
        else:
            high, price_high = midpoint, candidate_price

    return ImpliedVolResult(
        status=ImpliedVolStatus.MAX_ITERATIONS,
        volatility=midpoint,
        target_price=target_price,
        model_price=candidate_price,
        residual=candidate_price - target_price,
        iterations=max_iterations,
        bracket_low=low,
        bracket_high=high,
        price_at_low=price_low,
        price_at_high=price_high,
        price_tolerance=price_tolerance,
        volatility_tolerance=volatility_tolerance,
        warnings=("configured iteration limit reached",),
    )
