"""Mechanical verdict selection; NO_TRADE remains an explicit baseline."""

from __future__ import annotations

from take_two_options.knowledge.schemas import CompiledStrategyCandidate, Verdict
from take_two_options.quantitative.contracts import ModelEligibility


def decide_verdict(
    candidates: list[CompiledStrategyCandidate],
    *,
    data_available: bool,
    horizon_listed: bool,
) -> Verdict:
    if not data_available:
        return Verdict.BLOCKED_INSUFFICIENT_DATA
    if any(
        candidate.status == "admissible"
        and candidate.evaluation.decision_status is ModelEligibility.DECISION_ELIGIBLE
        for candidate in candidates
    ):
        return Verdict.TRADE_ADMISSIBLE
    if any(
        candidate.evaluation.validation is not None
        and candidate.evaluation.validation.status == "INSUFFICIENT_DATA"
        for candidate in candidates
    ):
        return Verdict.BLOCKED_INSUFFICIENT_DATA
    if not horizon_listed:
        return Verdict.WAIT
    if any(candidate.status == "watchlist" for candidate in candidates):
        return Verdict.WATCHLIST
    return Verdict.NO_TRADE
