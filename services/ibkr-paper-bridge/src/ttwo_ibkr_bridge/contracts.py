"""Strict wire contracts for the paper bridge."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


class ContractError(ValueError):
    """Raised before any broker-side action when a command is unsafe or malformed."""


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be non-empty text")
    return value.strip()


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractError(f"{field} must be a positive integer")
    return value


def _non_negative_decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ContractError(f"{field} must be numeric") from error
    if not result.is_finite() or result < 0:
        raise ContractError(f"{field} must be finite and non-negative")
    return result


@dataclass(frozen=True)
class ComboLeg:
    con_id: int
    ratio: int
    action: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ComboLeg:
        action = _text(value.get("action"), "leg.action")
        if action not in {"SELL_TO_CLOSE", "BUY_TO_CLOSE"}:
            raise ContractError("leg.action must close, never open, a position")
        return cls(
            con_id=_positive_int(value.get("con_id"), "leg.con_id"),
            ratio=_positive_int(value.get("ratio"), "leg.ratio"),
            action=action,
        )


@dataclass(frozen=True)
class PaperCommand:
    intent_id: str
    intent_type: str
    position_id: str
    preview_id: str | None
    order_ref: str
    ticker: str
    native_currency: str
    requested_quantity: int
    legs: tuple[ComboLeg, ...]
    maximum_exit_slippage_policy: Decimal
    pricing_policy: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PaperCommand:
        if value.get("mode") != "PAPER":
            raise ContractError("only PAPER mode exists")
        account_guard = value.get("account_guard")
        if not isinstance(account_guard, Mapping):
            raise ContractError("account_guard is required")
        if (
            account_guard.get("required_prefix") != "DU"
            or account_guard.get("live_accounts_forbidden") is not True
        ):
            raise ContractError("paper account guard is missing")
        raw_legs = value.get("legs")
        if not isinstance(raw_legs, list) or not raw_legs:
            raise ContractError("at least one combo leg is required")
        if any(not isinstance(item, Mapping) for item in raw_legs):
            raise ContractError("every combo leg must be an object")
        intent_type = _text(value.get("intent_type"), "intent_type")
        if intent_type not in {"MANUAL_CLOSE", "AUTOMATIC_FLOOR_EXIT", "NATIVE_PROTECTIVE_EXIT"}:
            raise ContractError("unsupported paper intent type")
        pricing_policy = _text(value.get("pricing_policy"), "pricing_policy")
        if pricing_policy != "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT":
            raise ContractError("a refreshed bounded limit is mandatory")
        preview = value.get("preview_id")
        if preview is not None and not isinstance(preview, str):
            raise ContractError("preview_id must be text or null")
        return cls(
            intent_id=_text(value.get("intent_id"), "intent_id"),
            intent_type=intent_type,
            position_id=_text(value.get("position_id"), "position_id"),
            preview_id=preview,
            order_ref=_text(value.get("order_ref"), "order_ref"),
            ticker=_text(value.get("ticker"), "ticker").upper(),
            native_currency=_text(value.get("native_currency"), "native_currency").upper(),
            requested_quantity=_positive_int(value.get("requested_quantity"), "requested_quantity"),
            legs=tuple(ComboLeg.from_mapping(item) for item in raw_legs),
            maximum_exit_slippage_policy=_non_negative_decimal(
                value.get("maximum_exit_slippage_policy"),
                "maximum_exit_slippage_policy",
            ),
            pricing_policy=pricing_policy,
        )


@dataclass(frozen=True)
class ClaimedIntent:
    command: PaperCommand
    claim_expires_at: datetime

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ClaimedIntent:
        command = value.get("command")
        if not isinstance(command, Mapping):
            raise ContractError("claim.command is required")
        expires_text = _text(value.get("claim_expires_at"), "claim_expires_at")
        try:
            expires = datetime.fromisoformat(expires_text.replace("Z", "+00:00"))
        except ValueError as error:
            raise ContractError("claim_expires_at is invalid") from error
        if expires.tzinfo is None:
            raise ContractError("claim_expires_at must include a timezone")
        return cls(
            command=PaperCommand.from_mapping(command),
            claim_expires_at=expires.astimezone(UTC),
        )


@dataclass(frozen=True)
class GatewayHealth:
    gateway_connected: bool
    paper_account_verified: bool
    open_intent_count: int
    detail: Mapping[str, Any]


@dataclass(frozen=True)
class GatewayEvent:
    broker_event_key: str
    event_type: str
    occurred_at: datetime
    broker_order_id: int | None = None
    broker_perm_id: int | None = None
    broker_exec_id: str | None = None
    detail: Mapping[str, Any] | None = None

    def as_payload(self) -> dict[str, Any]:
        allowed = {
            "BROKER_ACKNOWLEDGED",
            "PARTIAL_FILL",
            "FILLED",
            "COMMISSION_REPORT",
            "REJECTED",
            "CANCELLED",
            "EXPIRED",
            "AMBIGUOUS",
            "RECOVERY_OBSERVATION",
        }
        if self.event_type not in allowed:
            raise ContractError("unsupported gateway event")
        return {
            "broker_event_key": self.broker_event_key,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "broker_order_id": self.broker_order_id,
            "broker_perm_id": self.broker_perm_id,
            "broker_exec_id": self.broker_exec_id,
            "detail": dict(self.detail or {}),
        }
