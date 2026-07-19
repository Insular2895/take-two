"""Fundamental thesis helpers kept separate from options mechanics."""

from __future__ import annotations

from take_two_options.domain import FundamentalSnapshot, StrategyCandidate, StrategyKind

_BULLISH = {StrategyKind.STOCK, StrategyKind.LONG_CALL, StrategyKind.BULL_CALL_SPREAD}
_BEARISH = {StrategyKind.LONG_PUT, StrategyKind.BEAR_PUT_SPREAD}


def thesis_fit(candidate: StrategyCandidate, fundamental: FundamentalSnapshot) -> float:
    if candidate.kind is StrategyKind.NO_TRADE:
        return 0.65
    if fundamental.direction == "neutral":
        return 0.5
    if fundamental.direction == "bullish":
        return 1.0 if candidate.kind in _BULLISH else 0.15
    return 1.0 if candidate.kind in _BEARISH else 0.15


def catalyst_coverage(candidate: StrategyCandidate, fundamental: FundamentalSnapshot) -> float:
    option_expirations = [
        leg.option_quote.contract.expiration
        for leg in candidate.legs
        if leg.option_quote is not None
    ]
    if not option_expirations:
        return 1.0
    earliest_expiration = min(option_expirations)
    if earliest_expiration >= fundamental.catalyst_window_end:
        return 1.0
    if earliest_expiration >= fundamental.catalyst_window_start:
        return 0.5
    return 0.0
