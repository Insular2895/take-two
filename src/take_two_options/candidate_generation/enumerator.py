"""Enumerate every listed combination admitted by each compiled recipe."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from itertools import product

from pydantic import Field

from take_two_options.candidate_generation.factory import build_candidate
from take_two_options.candidate_generation.search_space import (
    StrategySearchSpace,
    build_search_space,
)
from take_two_options.domain import OptionType, PositionSide, StrictModel
from take_two_options.knowledge.schemas import (
    Architecture,
    CompiledStrategyCandidate,
    MarketSnapshot,
    QuoteSnapshot,
    StrategyCatalog,
    StrategyRecipe,
    TradeRequest,
)


class EnumerationResult(StrictModel):
    search_spaces: list[StrategySearchSpace]
    candidates: list[CompiledStrategyCandidate]
    combinations_by_architecture: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


def _width_allowed(width: float, search_space: StrategySearchSpace) -> bool:
    if not search_space.spread_widths:
        return True
    return any(abs(width - allowed) < 1e-8 for allowed in search_space.spread_widths)


def _quotes_for_space(
    snapshot: MarketSnapshot,
    search_space: StrategySearchSpace,
) -> dict[tuple[date, OptionType], list[QuoteSnapshot]]:
    expiration_strings = {
        *search_space.admissible_expirations,
        *search_space.diagnostic_expirations,
    }
    grouped: dict[tuple[date, OptionType], list[QuoteSnapshot]] = defaultdict(list)
    for quote in snapshot.quotes:
        if quote.expiration.isoformat() not in expiration_strings:
            continue
        moneyness = quote.strike / snapshot.spot
        if not search_space.minimum_moneyness <= moneyness <= search_space.maximum_moneyness:
            continue
        grouped[(quote.expiration, quote.option_type)].append(quote)
    for quotes in grouped.values():
        quotes.sort(key=lambda quote: quote.strike)
    return grouped


def _emit(
    target: dict[str, CompiledStrategyCandidate],
    *,
    recipe: StrategyRecipe,
    request: TradeRequest,
    architecture: Architecture,
    leg_specs: list[tuple[PositionSide, int, QuoteSnapshot]],
    horizon_compatible: bool,
) -> None:
    total_ratio = sum(ratio for _, ratio, _ in leg_specs)
    maximum_quantity = max(1, request.maximum_contracts // total_ratio)
    for quantity in range(1, maximum_quantity + 1):
        candidate = build_candidate(
            architecture=architecture,
            recipe=recipe,
            leg_specs=leg_specs,
            quantity=quantity,
            request=request,
            horizon_compatible=horizon_compatible,
        )
        target[candidate.candidate_id] = candidate


def _single_and_verticals(
    target: dict[str, CompiledStrategyCandidate],
    grouped: dict[tuple[date, OptionType], list[QuoteSnapshot]],
    recipe: StrategyRecipe,
    search_space: StrategySearchSpace,
    request: TradeRequest,
) -> None:
    architecture = recipe.architecture
    option_type = (
        OptionType.CALL
        if architecture in {Architecture.LONG_CALL, Architecture.BULL_CALL_SPREAD}
        else OptionType.PUT
    )
    for (expiration, grouped_type), quotes in grouped.items():
        if grouped_type is not option_type:
            continue
        horizon_compatible = expiration.isoformat() in search_space.admissible_expirations
        if architecture in {Architecture.LONG_CALL, Architecture.LONG_PUT}:
            for quote in quotes:
                _emit(
                    target,
                    recipe=recipe,
                    request=request,
                    architecture=architecture,
                    leg_specs=[(PositionSide.LONG, 1, quote)],
                    horizon_compatible=horizon_compatible,
                )
            continue
        for lower_index, lower in enumerate(quotes):
            for upper in quotes[lower_index + 1 :]:
                if not _width_allowed(upper.strike - lower.strike, search_space):
                    continue
                leg_specs = (
                    [
                        (PositionSide.LONG, 1, lower),
                        (PositionSide.SHORT, 1, upper),
                    ]
                    if architecture is Architecture.BULL_CALL_SPREAD
                    else [
                        (PositionSide.SHORT, 1, lower),
                        (PositionSide.LONG, 1, upper),
                    ]
                )
                _emit(
                    target,
                    recipe=recipe,
                    request=request,
                    architecture=architecture,
                    leg_specs=leg_specs,
                    horizon_compatible=horizon_compatible,
                )


def _butterflies(
    target: dict[str, CompiledStrategyCandidate],
    grouped: dict[tuple[date, OptionType], list[QuoteSnapshot]],
    recipe: StrategyRecipe,
    search_space: StrategySearchSpace,
    request: TradeRequest,
) -> None:
    architecture = recipe.architecture
    option_type = (
        OptionType.CALL
        if architecture
        in {Architecture.CALL_BUTTERFLY, Architecture.CALL_BROKEN_WING_BUTTERFLY}
        else OptionType.PUT
    )
    broken = architecture in {
        Architecture.CALL_BROKEN_WING_BUTTERFLY,
        Architecture.PUT_BROKEN_WING_BUTTERFLY,
    }
    for (expiration, grouped_type), quotes in grouped.items():
        if grouped_type is not option_type:
            continue
        horizon_compatible = expiration.isoformat() in search_space.admissible_expirations
        for center_index in range(1, len(quotes) - 1):
            center = quotes[center_index]
            for lower in quotes[:center_index]:
                left_width = center.strike - lower.strike
                if not _width_allowed(left_width, search_space):
                    continue
                for upper in quotes[center_index + 1 :]:
                    right_width = upper.strike - center.strike
                    if not _width_allowed(right_width, search_space):
                        continue
                    symmetric = abs(left_width - right_width) < 1e-8
                    if broken == symmetric:
                        continue
                    _emit(
                        target,
                        recipe=recipe,
                        request=request,
                        architecture=architecture,
                        leg_specs=[
                            (PositionSide.LONG, 1, lower),
                            (PositionSide.SHORT, 2, center),
                            (PositionSide.LONG, 1, upper),
                        ],
                        horizon_compatible=horizon_compatible,
                    )


def _volatility_structures(
    target: dict[str, CompiledStrategyCandidate],
    grouped: dict[tuple[date, OptionType], list[QuoteSnapshot]],
    recipe: StrategyRecipe,
    search_space: StrategySearchSpace,
    request: TradeRequest,
) -> None:
    architecture = recipe.architecture
    expirations = sorted({expiration for expiration, _ in grouped})
    for expiration in expirations:
        calls = grouped.get((expiration, OptionType.CALL), [])
        puts = grouped.get((expiration, OptionType.PUT), [])
        calls_by_strike = {quote.strike: quote for quote in calls}
        puts_by_strike = {quote.strike: quote for quote in puts}
        horizon_compatible = expiration.isoformat() in search_space.admissible_expirations
        if architecture is Architecture.LONG_STRADDLE:
            for strike in sorted(calls_by_strike.keys() & puts_by_strike.keys()):
                _emit(
                    target,
                    recipe=recipe,
                    request=request,
                    architecture=architecture,
                    leg_specs=[
                        (PositionSide.LONG, 1, calls_by_strike[strike]),
                        (PositionSide.LONG, 1, puts_by_strike[strike]),
                    ],
                    horizon_compatible=horizon_compatible,
                )
        elif architecture is Architecture.LONG_STRANGLE:
            for put, call in product(puts, calls):
                if put.strike >= call.strike:
                    continue
                if search_space.spread_widths and not _width_allowed(
                    call.strike - put.strike, search_space
                ):
                    continue
                _emit(
                    target,
                    recipe=recipe,
                    request=request,
                    architecture=architecture,
                    leg_specs=[
                        (PositionSide.LONG, 1, put),
                        (PositionSide.LONG, 1, call),
                    ],
                    horizon_compatible=horizon_compatible,
                )
        else:
            for long_put_index, long_put in enumerate(puts):
                for short_put in puts[long_put_index + 1 :]:
                    put_width = short_put.strike - long_put.strike
                    if not _width_allowed(put_width, search_space):
                        continue
                    for short_call_index, short_call in enumerate(calls):
                        if short_call.strike <= short_put.strike:
                            continue
                        for long_call in calls[short_call_index + 1 :]:
                            call_width = long_call.strike - short_call.strike
                            if not _width_allowed(call_width, search_space):
                                continue
                            _emit(
                                target,
                                recipe=recipe,
                                request=request,
                                architecture=architecture,
                                leg_specs=[
                                    (PositionSide.LONG, 1, long_put),
                                    (PositionSide.SHORT, 1, short_put),
                                    (PositionSide.SHORT, 1, short_call),
                                    (PositionSide.LONG, 1, long_call),
                                ],
                                horizon_compatible=horizon_compatible,
                            )


def _calendars(
    target: dict[str, CompiledStrategyCandidate],
    snapshot: MarketSnapshot,
    grouped_back: dict[tuple[date, OptionType], list[QuoteSnapshot]],
    recipe: StrategyRecipe,
    search_space: StrategySearchSpace,
    request: TradeRequest,
) -> None:
    architecture = recipe.architecture
    option_type = (
        OptionType.CALL
        if architecture in {Architecture.CALL_CALENDAR, Architecture.CALL_DIAGONAL}
        else OptionType.PUT
    )
    is_diagonal = architecture in {Architecture.CALL_DIAGONAL, Architecture.PUT_DIAGONAL}
    all_grouped: dict[tuple[date, OptionType], list[QuoteSnapshot]] = defaultdict(list)
    for quote in snapshot.quotes:
        if quote.option_type is option_type:
            all_grouped[(quote.expiration, quote.option_type)].append(quote)
    for quotes in all_grouped.values():
        quotes.sort(key=lambda quote: quote.strike)
    for (back_expiration, grouped_type), back_quotes in grouped_back.items():
        if grouped_type is not option_type:
            continue
        horizon_compatible = back_expiration.isoformat() in search_space.admissible_expirations
        for (front_expiration, front_type), front_quotes in all_grouped.items():
            if front_type is not option_type or front_expiration >= back_expiration:
                continue
            front_dte = (front_expiration - request.as_of).days
            minimum_front = search_space.front_minimum_dte or min(search_space.holding_days) + 7
            maximum_front = search_space.front_maximum_dte or search_space.maximum_dte
            if not minimum_front <= front_dte <= maximum_front:
                continue
            for back_quote, front_quote in product(back_quotes, front_quotes):
                same_strike = abs(back_quote.strike - front_quote.strike) < 1e-8
                if is_diagonal == same_strike:
                    continue
                if is_diagonal and search_space.spread_widths and not _width_allowed(
                    abs(back_quote.strike - front_quote.strike), search_space
                ):
                    continue
                if architecture is Architecture.CALL_DIAGONAL and (
                    back_quote.strike > front_quote.strike
                ):
                    continue
                if architecture is Architecture.PUT_DIAGONAL and (
                    back_quote.strike < front_quote.strike
                ):
                    continue
                _emit(
                    target,
                    recipe=recipe,
                    request=request,
                    architecture=architecture,
                    leg_specs=[
                        (PositionSide.LONG, 1, back_quote),
                        (PositionSide.SHORT, 1, front_quote),
                    ],
                    horizon_compatible=horizon_compatible,
                )


def enumerate_candidates(
    catalog: StrategyCatalog,
    request: TradeRequest,
    snapshot: MarketSnapshot,
) -> EnumerationResult:
    candidates: dict[str, CompiledStrategyCandidate] = {}
    spaces: list[StrategySearchSpace] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}
    for recipe in catalog.recipes:
        if recipe.architecture not in request.allowed_structures:
            continue
        search_space = build_search_space(recipe, request, snapshot)
        spaces.append(search_space)
        grouped = _quotes_for_space(snapshot, search_space)
        before = len(candidates)
        if recipe.architecture in {
            Architecture.LONG_CALL,
            Architecture.LONG_PUT,
            Architecture.BULL_CALL_SPREAD,
            Architecture.BEAR_PUT_SPREAD,
        }:
            _single_and_verticals(candidates, grouped, recipe, search_space, request)
        elif recipe.architecture in {
            Architecture.CALL_BUTTERFLY,
            Architecture.PUT_BUTTERFLY,
            Architecture.CALL_BROKEN_WING_BUTTERFLY,
            Architecture.PUT_BROKEN_WING_BUTTERFLY,
        }:
            _butterflies(candidates, grouped, recipe, search_space, request)
        elif recipe.architecture in {
            Architecture.LONG_STRADDLE,
            Architecture.LONG_STRANGLE,
            Architecture.IRON_CONDOR,
        }:
            _volatility_structures(candidates, grouped, recipe, search_space, request)
        else:
            _calendars(candidates, snapshot, grouped, recipe, search_space, request)
        counts[recipe.architecture.value] = len(candidates) - before
        if search_space.horizon_gap:
            warnings.append(
                f"{recipe.recipe_id}: no listed expiration satisfies "
                f"{search_space.minimum_dte}-{search_space.maximum_dte} DTE; "
                "nearest maturity is diagnostic only"
            )
    return EnumerationResult(
        search_spaces=spaces,
        candidates=list(candidates.values()),
        combinations_by_architecture=counts,
        warnings=warnings,
    )
