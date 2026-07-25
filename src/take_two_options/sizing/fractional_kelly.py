"""Strongly capped fractional Kelly with explicit eligibility gates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KellyResult:
    status: str
    fraction: float | None
    reasons: tuple[str, ...]


def fractional_kelly(
    *,
    probability_win: float | None,
    payoff_ratio: float | None,
    calibrated: bool,
    sufficient_sample: bool,
    stable: bool,
    maximum_loss_known: bool,
    multiplier: float = 0.25,
    hard_cap: float = 0.05,
) -> KellyResult:
    reasons = []
    if not calibrated:
        reasons.append("probabilities_not_calibrated")
    if not sufficient_sample:
        reasons.append("sample_insufficient")
    if not stable:
        reasons.append("estimates_unstable")
    if not maximum_loss_known:
        reasons.append("maximum_loss_unknown")
    if probability_win is None or payoff_ratio is None or payoff_ratio <= 0:
        reasons.append("payoff_inputs_missing")
    if reasons:
        return KellyResult("KELLY_NOT_ELIGIBLE", None, tuple(reasons))
    assert probability_win is not None and payoff_ratio is not None
    full_kelly = probability_win - (1 - probability_win) / payoff_ratio
    return KellyResult(
        "ELIGIBLE",
        max(0.0, min(full_kelly * multiplier, hard_cap)),
        (),
    )
