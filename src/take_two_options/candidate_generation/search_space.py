"""Translate recipes and one trade request into an auditable search space."""

from __future__ import annotations

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.knowledge.schemas import (
    Architecture,
    MarketSnapshot,
    StrategyRecipe,
    TradeRequest,
)


class StrategySearchSpace(StrictModel):
    recipe_id: str
    architecture: Architecture
    minimum_dte: int = Field(gt=0)
    maximum_dte: int = Field(gt=0)
    front_minimum_dte: int | None = Field(default=None, gt=0)
    front_maximum_dte: int | None = Field(default=None, gt=0)
    minimum_moneyness: float = Field(gt=0)
    maximum_moneyness: float = Field(gt=0)
    spread_widths: list[float] = Field(default_factory=list)
    profit_targets: list[float] = Field(min_length=1)
    stops: list[float] = Field(min_length=1)
    holding_days: list[int] = Field(min_length=1)
    rolling_rules: list[str] = Field(min_length=1)
    capital_recovery_rules: list[str] = Field(min_length=1)
    admissible_expirations: list[str] = Field(default_factory=list)
    diagnostic_expirations: list[str] = Field(default_factory=list)
    horizon_gap: bool = False


def _range_values(
    minimum: float | int | None,
    maximum: float | int | None,
    values: list[float],
    *,
    integer: bool = False,
) -> list[float] | list[int]:
    if values:
        return [int(value) for value in values] if integer else values
    assert minimum is not None and maximum is not None
    if minimum == maximum:
        return [int(minimum)] if integer else [float(minimum)]
    midpoint = (float(minimum) + float(maximum)) / 2
    selected = [float(minimum), midpoint, float(maximum)]
    return [int(round(value)) for value in selected] if integer else selected


def build_search_space(
    recipe: StrategyRecipe,
    request: TradeRequest,
    snapshot: MarketSnapshot,
) -> StrategySearchSpace:
    recipe_minimum = int(recipe.dte.minimum or 1)
    recipe_maximum = int(recipe.dte.maximum or request.horizon_max_days)
    minimum_dte = max(recipe_minimum, request.horizon_min_days)
    maximum_dte = min(recipe_maximum, request.horizon_max_days)
    if minimum_dte > maximum_dte:
        minimum_dte, maximum_dte = request.horizon_min_days, request.horizon_max_days
    expirations = []
    for expiration in snapshot.available_expirations:
        dte = (expiration - request.as_of).days
        if minimum_dte <= dte <= maximum_dte:
            expirations.append(expiration.isoformat())
    diagnostic: list[str] = []
    if not expirations and snapshot.available_expirations:
        nearest = min(
            snapshot.available_expirations,
            key=lambda expiration: min(
                abs((expiration - request.as_of).days - minimum_dte),
                abs((expiration - request.as_of).days - maximum_dte),
            ),
        )
        diagnostic = [nearest.isoformat()]

    moneyness_minimum = float(recipe.moneyness.minimum or 0.01)
    moneyness_maximum = float(recipe.moneyness.maximum or 10)
    widths = [float(value) for value in recipe.spread_width.values] if recipe.spread_width else []
    return StrategySearchSpace(
        recipe_id=recipe.recipe_id,
        architecture=recipe.architecture,
        minimum_dte=minimum_dte,
        maximum_dte=maximum_dte,
        front_minimum_dte=(
            int(recipe.front_dte.minimum) if recipe.front_dte and recipe.front_dte.minimum else None
        ),
        front_maximum_dte=(
            int(recipe.front_dte.maximum) if recipe.front_dte and recipe.front_dte.maximum else None
        ),
        minimum_moneyness=moneyness_minimum,
        maximum_moneyness=moneyness_maximum,
        spread_widths=widths,
        profit_targets=[
            float(value)
            for value in _range_values(
                recipe.profit_targets.minimum,
                recipe.profit_targets.maximum,
                recipe.profit_targets.values,
            )
        ],
        stops=[
            float(value)
            for value in _range_values(
                recipe.stops.minimum,
                recipe.stops.maximum,
                recipe.stops.values,
            )
        ],
        holding_days=[
            int(value)
            for value in _range_values(
                recipe.holding_days.minimum,
                recipe.holding_days.maximum,
                recipe.holding_days.values,
                integer=True,
            )
        ],
        rolling_rules=recipe.rolling_rules,
        capital_recovery_rules=recipe.capital_recovery_rules,
        admissible_expirations=expirations,
        diagnostic_expirations=diagnostic,
        horizon_gap=not bool(expirations),
    )
