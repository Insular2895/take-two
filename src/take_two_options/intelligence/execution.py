"""Preview-only IBKR artifacts and an explicit forbidden execution boundary."""

from __future__ import annotations

from typing import Any

from take_two_options.data import ReadOnlyBrokerGateway
from take_two_options.intelligence.schemas import ComboQuote, ExecutionPreview
from take_two_options.thesis_scanner.schemas import ThesisCandidate


def build_execution_previews(
    candidates: list[ThesisCandidate],
    *,
    combo_quotes: dict[str, ComboQuote] | None = None,
    what_if_results: dict[str, dict[str, float]] | None = None,
) -> list[ExecutionPreview]:
    """Build non-transmitting tickets; missing broker facts remain blockers."""
    combo_quotes = combo_quotes or {}
    what_if_results = what_if_results or {}
    previews: list[ExecutionPreview] = []
    for candidate in candidates:
        combo = combo_quotes.get(candidate.candidate_id)
        what_if = what_if_results.get(candidate.candidate_id, {})
        blockers: list[str] = []
        if combo is None:
            blockers.append("Live IBKR combo quote is unavailable.")
        elif not combo.executable or combo.ask is None:
            blockers.append("IBKR combo quote is not marked executable.")
        if any(
            metric.price_quality != "opra"
            for metric in candidate.decision_metrics.leg_execution
        ):
            blockers.append("At least one leg is not backed by a live OPRA quote.")
        if not what_if:
            blockers.append(
                "Account-specific commission/margin what-if is unavailable; "
                "some smart combos may not support what-if."
            )
        blockers.append("Contract conIds and deliverables require broker-side resolution.")
        blockers.append("Human confirmation is mandatory; automatic transmission is forbidden.")
        limit = (
            min(candidate.execution.indicative_limit_price_per_share, combo.ask)
            if combo is not None and combo.ask is not None
            else candidate.execution.indicative_limit_price_per_share
        )
        previews.append(
            ExecutionPreview(
                candidate_id=candidate.candidate_id,
                security_type="BAG" if len(candidate.base_candidate.legs) > 1 else "OPT",
                limit_debit_usd=max(limit, 0.0),
                combo_quote=combo,
                estimated_commission_usd=what_if.get("commission_usd"),
                margin_what_if_usd=what_if.get("margin_usd"),
                blockers=blockers,
            )
        )
    return previews


def execution_gateway() -> ReadOnlyBrokerGateway:
    """Return the repository-wide gateway that rejects every order-side mutation."""
    return ReadOnlyBrokerGateway()


def assert_no_order_capability(obj: Any) -> None:
    """Static/runtime defense against accidentally injecting an order-capable adapter."""
    forbidden = (
        "place_order",
        "placeOrder",
        "submit_order",
        "modify_order",
        "cancel_order",
        "cancelOrder",
        "exercise",
        "exerciseOptions",
    )
    exposed = [
        name
        for name in forbidden
        if callable(getattr(obj, name, None))
        and not isinstance(obj, ReadOnlyBrokerGateway)
    ]
    if exposed:
        raise TypeError(f"order-capable object rejected by V11: {', '.join(exposed)}")
