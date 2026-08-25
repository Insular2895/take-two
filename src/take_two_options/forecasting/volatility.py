"""Observed IV summaries without an invented surface forecast."""

from __future__ import annotations

from statistics import median

from take_two_options.knowledge.schemas import MarketSnapshot


def observed_iv_summary(snapshot: MarketSnapshot) -> dict[str, float | int | None]:
    values = [
        quote.implied_volatility
        for quote in snapshot.quotes
        if quote.implied_volatility is not None
    ]
    return {
        "observations": len(values),
        "median": median(values) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }
