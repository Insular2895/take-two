"""IBKR preview artifacts only; no broker client or live-order method exists here."""

from __future__ import annotations

import json
from pathlib import Path

from take_two_options.knowledge.schemas import DecisionReport


class TicketBlockedError(ValueError):
    """Raised when a preview is requested for a non-admissible candidate."""


def build_ibkr_preview(report: DecisionReport, candidate_id: str) -> dict[str, object]:
    candidate = next(
        (item for item in report.candidates if item.candidate_id == candidate_id), None
    )
    if candidate is None:
        raise TicketBlockedError(f"candidate not found: {candidate_id}")
    if candidate.status != "admissible":
        raise TicketBlockedError(
            f"{candidate_id} is {candidate.status}; only admissible candidates get a ticket"
        )
    return {
        "mode": "preview",
        "broker": "IBKR",
        "security_type": "BAG" if len(candidate.legs) > 1 else "OPT",
        "symbol": report.analysis.ticker,
        "currency": "USD",
        "exchange": "SMART",
        "transmit": False,
        "what_if": True,
        "human_confirmation_required": True,
        "order_capability": "forbidden",
        "candidate_id": candidate.candidate_id,
        "legs": [
            {
                "local_symbol": leg.quote.symbol,
                "action": "BUY" if leg.side.value == "long" else "SELL",
                "ratio": leg.quantity,
                "option_type": leg.quote.option_type.value.upper(),
                "strike": leg.quote.strike,
                "expiration": leg.quote.expiration.isoformat(),
                "exchange": "SMART",
                "con_id": None,
                "con_id_status": "resolve_in_tws_before_human_preview",
            }
            for leg in candidate.legs
        ],
    }


def write_ibkr_preview(report: DecisionReport, candidate_id: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(build_ibkr_preview(report, candidate_id), indent=2),
        encoding="utf-8",
    )
    return path


def write_blocked_ticket_status(report: DecisionReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "BLOCKED_NO_ADMISSIBLE_CANDIDATE",
                "verdict": report.verdict.value,
                "ticket_created": False,
                "transmit": False,
                "order_capability": "forbidden",
                "reason": "No candidate passed every hard and statistical gate.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path
