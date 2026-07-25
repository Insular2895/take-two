"""Plateau diagnostics around a selected parameter point."""

from __future__ import annotations

from statistics import fmean


def stability_score(center: float, neighbors: list[float]) -> float | None:
    if len(neighbors) < 2:
        return None
    scale = max(abs(center), abs(fmean(neighbors)), 1e-9)
    dispersion = fmean(abs(value - center) for value in neighbors) / scale
    return max(0.0, min(1.0, 1.0 - dispersion))
