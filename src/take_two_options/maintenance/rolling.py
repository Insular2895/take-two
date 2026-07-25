"""Rolling requires a fresh chain and remains a review action."""

from __future__ import annotations

from datetime import date


def roll_review_required(*, as_of: date, expiration: date, threshold_days: int) -> bool:
    return (expiration - as_of).days <= threshold_days
