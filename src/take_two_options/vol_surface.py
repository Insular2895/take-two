"""Volatility-surface interpolation with explicit fallback diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from take_two_options.domain import (
    MarketDataBundle,
    OptionQuote,
    OptionType,
    SurfaceDiagnostics,
    VolatilitySurface,
    VolatilitySurfaceNode,
)


@dataclass(frozen=True)
class SurfaceLookup:
    volatility: float
    source: str
    extrapolated: bool


def _strike_interpolation(nodes: list[VolatilitySurfaceNode], strike: float) -> tuple[float, bool]:
    ordered = sorted(nodes, key=lambda node: node.strike)
    if strike <= ordered[0].strike:
        return ordered[0].implied_volatility, strike < ordered[0].strike
    if strike >= ordered[-1].strike:
        return ordered[-1].implied_volatility, strike > ordered[-1].strike
    for left, right in zip(ordered, ordered[1:], strict=False):
        if left.strike <= strike <= right.strike:
            weight = (strike - left.strike) / (right.strike - left.strike)
            value = left.implied_volatility + weight * (
                right.implied_volatility - left.implied_volatility
            )
            return value, False
    raise RuntimeError("surface strike interpolation failed")


def interpolate_surface(
    surface: VolatilitySurface,
    *,
    expiration: datetime,
    strike: float,
    option_type: OptionType,
) -> SurfaceLookup:
    typed_nodes = [node for node in surface.nodes if node.option_type is option_type]
    if not typed_nodes:
        raise ValueError(f"surface has no {option_type.value} nodes")

    by_expiry: dict[datetime, list[VolatilitySurfaceNode]] = {}
    for node in typed_nodes:
        by_expiry.setdefault(node.expiration, []).append(node)
    expiries = sorted(by_expiry)
    if expiration <= expiries[0]:
        value, strike_extrapolated = _strike_interpolation(by_expiry[expiries[0]], strike)
        return SurfaceLookup(value, "surface", expiration < expiries[0] or strike_extrapolated)
    if expiration >= expiries[-1]:
        value, strike_extrapolated = _strike_interpolation(by_expiry[expiries[-1]], strike)
        return SurfaceLookup(value, "surface", expiration > expiries[-1] or strike_extrapolated)

    for earlier, later in zip(expiries, expiries[1:], strict=False):
        if earlier <= expiration <= later:
            earlier_vol, earlier_extra = _strike_interpolation(by_expiry[earlier], strike)
            later_vol, later_extra = _strike_interpolation(by_expiry[later], strike)
            total = (later - earlier).total_seconds()
            weight = (expiration - earlier).total_seconds() / total
            value = earlier_vol + weight * (later_vol - earlier_vol)
            return SurfaceLookup(value, "surface", earlier_extra or later_extra)
    raise RuntimeError("surface expiry interpolation failed")


def effective_volatility(bundle: MarketDataBundle, quote: OptionQuote) -> SurfaceLookup:
    if bundle.volatility_surface is not None:
        try:
            return interpolate_surface(
                bundle.volatility_surface,
                expiration=quote.contract.expiration,
                strike=quote.contract.strike,
                option_type=quote.contract.option_type,
            )
        except ValueError:
            pass
    if quote.implied_volatility is not None:
        return SurfaceLookup(quote.implied_volatility, "quote", False)
    return SurfaceLookup(bundle.annualized_volatility, "realized_volatility_fallback", True)


def surface_diagnostics(bundle: MarketDataBundle) -> SurfaceDiagnostics:
    surface = bundle.volatility_surface
    if surface is None:
        return SurfaceDiagnostics(
            available=False,
            expiry_count=0,
            strike_count=0,
            interpolated_contracts=0,
            extrapolated_contracts=len(bundle.option_quotes),
            warnings=["No explicit volatility surface; quote IV/RV fallbacks are in use"],
        )

    extrapolated = 0
    interpolated = 0
    warnings: list[str] = []
    for quote in bundle.option_quotes:
        lookup = effective_volatility(bundle, quote)
        if lookup.source != "surface" or lookup.extrapolated:
            extrapolated += 1
        else:
            interpolated += 1
    if extrapolated:
        warnings.append(f"{extrapolated} contract(s) require surface extrapolation or fallback")
    return SurfaceDiagnostics(
        available=True,
        expiry_count=len({node.expiration for node in surface.nodes}),
        strike_count=len({node.strike for node in surface.nodes}),
        interpolated_contracts=interpolated,
        extrapolated_contracts=extrapolated,
        warnings=warnings,
    )
