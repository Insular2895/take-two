"""Locked-holdout and contamination governance."""

from __future__ import annotations

import json
from pathlib import Path


def contaminated_holdout_ids(manifest_path: Path) -> set[str]:
    if not manifest_path.is_file():
        return set()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return set(payload.get("contaminated_holdouts", []))


def holdout_status(
    *,
    requested_holdout_id: str | None,
    contaminated_ids: set[str],
    observations: int,
    configured_minimum: int,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if requested_holdout_id is None:
        return "INSUFFICIENT_DATA", ["no locked final holdout is configured"]
    if requested_holdout_id in contaminated_ids:
        return "CONTAMINATED", [f"{requested_holdout_id} was previously inspected"]
    if observations < configured_minimum:
        reasons.append(
            f"holdout has {observations} observations; configured minimum is "
            f"{configured_minimum}"
        )
        return "INSUFFICIENT_DATA", reasons
    return "PASSED", reasons
