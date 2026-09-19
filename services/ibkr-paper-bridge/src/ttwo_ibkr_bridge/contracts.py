"""Strict wire contracts for the paper bridge."""

from __future__ import annotations

import re
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


def _sha256(value: object, field: str) -> str:
    text = _text(value, field).lower()
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ContractError(f"{field} must be a lowercase sha256")
    return text


def _git_commit(value: object, field: str) -> str:
    text = _text(value, field).lower()
    if not re.fullmatch(r"[a-f0-9]{7,40}", text):
        raise ContractError(f"{field} must be a git commit hash")
    return text


def _utc_datetime(value: object, field: str) -> datetime:
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError(f"{field} is invalid") from error
    if parsed.tzinfo is None:
        raise ContractError(f"{field} must include a timezone")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class ComboLeg:
    con_id: int
    ratio: int
    action: str
    wire_action: str
    local_symbol: str | None = None
    trading_class: str | None = None
    expiration: str | None = None
    strike: Decimal | None = None
    right: str | None = None
    multiplier: int | None = None
    currency: str | None = None
    exchange: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, entry: bool) -> ComboLeg:
        action = _text(value.get("action"), "leg.action")
        allowed = {"BUY_TO_OPEN", "SELL_TO_OPEN"} if entry else {
            "SELL_TO_CLOSE",
            "BUY_TO_CLOSE",
        }
        if action not in allowed:
            expected = "open" if entry else "close"
            raise ContractError(f"leg.action must {expected} the governed position")
        expected_wire_action = "BUY" if action.startswith("BUY_") else "SELL"
        wire_action = str(value.get("wire_action", expected_wire_action)).upper()
        if wire_action != expected_wire_action:
            raise ContractError("application action and IBKR wire action disagree")
        identity_fields = {
            name: value.get(name)
            for name in (
                "local_symbol",
                "trading_class",
                "expiration",
                "strike",
                "right",
                "multiplier",
                "currency",
                "exchange",
            )
        }
        if entry and any(item is None for item in identity_fields.values()):
            raise ContractError("entry legs require the complete qualified contract identity")
        right = (
            None
            if value.get("right") is None
            else _text(value.get("right"), "leg.right").upper()
        )
        if right is not None and right not in {"C", "P"}:
            raise ContractError("leg.right must be C or P")
        expiration = (
            _text(value.get("expiration"), "leg.expiration")
            if value.get("expiration") is not None
            else None
        )
        if expiration is not None and not re.fullmatch(r"\d{8}", expiration):
            raise ContractError("leg.expiration must use YYYYMMDD")
        currency = (
            _text(value.get("currency"), "leg.currency").upper()
            if value.get("currency") is not None
            else None
        )
        if currency is not None and not re.fullmatch(r"[A-Z]{3}", currency):
            raise ContractError("leg.currency must be a three-letter code")
        strike = (
            _non_negative_decimal(value.get("strike"), "leg.strike")
            if value.get("strike") is not None
            else None
        )
        if strike is not None and strike <= 0:
            raise ContractError("leg.strike must be positive")
        return cls(
            con_id=_positive_int(value.get("con_id"), "leg.con_id"),
            ratio=_positive_int(value.get("ratio"), "leg.ratio"),
            action=action,
            wire_action=wire_action,
            local_symbol=(
                _text(value.get("local_symbol"), "leg.local_symbol")
                if value.get("local_symbol") is not None
                else None
            ),
            trading_class=(
                _text(value.get("trading_class"), "leg.trading_class")
                if value.get("trading_class") is not None
                else None
            ),
            expiration=expiration,
            strike=strike,
            right=right,
            multiplier=(
                _positive_int(value.get("multiplier"), "leg.multiplier")
                if value.get("multiplier") is not None
                else None
            ),
            currency=currency,
            exchange=(
                _text(value.get("exchange"), "leg.exchange").upper()
                if value.get("exchange") is not None
                else None
            ),
        )


@dataclass(frozen=True)
class PaperEntryAuthorization:
    original_analysis_id: str
    candidate_id: str
    selection_id: str
    dossier_id: str
    revalidation_ticket_id: str
    revalidation_ticket_hash: str
    ticket_created_at: datetime
    ticket_expires_at: datetime
    confirmation_id: str
    confirmation_hash: str
    structure_type: str
    structure_hash: str
    current_market_snapshot_hash: str
    current_git_commit: str
    current_config_hash: str
    proposed_limit: Decimal
    valid_tick: Decimal
    capital_required_eur: Decimal
    maximum_loss_eur: Decimal
    expected_commissions_eur: Decimal
    cash_flow_type: str
    combo_submission_mode: str
    broker_combo_guarantee_mode: str
    kill_switch_version: str
    what_if_fallback_authorized: bool
    what_if_fallback_policy_version: str | None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PaperEntryAuthorization:
        if value.get("candidate_approved") is not True:
            raise ContractError("entry candidate approval is missing")
        if value.get("dossier_current") is not True:
            raise ContractError("entry dossier is not current")
        if value.get("bag_semantics_verified") is not True:
            raise ContractError("signed BAG semantics are unverified")
        cash_flow_type = _text(value.get("cash_flow_type"), "cash_flow_type").upper()
        if cash_flow_type not in {"DEBIT", "CREDIT"}:
            raise ContractError("cash_flow_type must be DEBIT or CREDIT")
        submission_mode = _text(
            value.get("combo_submission_mode"), "combo_submission_mode"
        ).upper()
        if submission_mode != "WHOLE_BAG":
            raise ContractError("only whole-BAG submission is supported")
        guarantee_mode = _text(
            value.get("broker_combo_guarantee_mode"),
            "broker_combo_guarantee_mode",
        ).upper()
        if guarantee_mode not in {"GUARANTEED", "NON_GUARANTEED", "UNKNOWN"}:
            raise ContractError("invalid broker combo guarantee mode")
        proposed_limit = _non_negative_decimal(value.get("proposed_limit"), "proposed_limit")
        if proposed_limit <= 0:
            raise ContractError("proposed_limit must be positive")
        valid_tick = _non_negative_decimal(value.get("valid_tick"), "valid_tick")
        if valid_tick <= 0:
            raise ContractError("valid_tick must be positive")
        created = _utc_datetime(value.get("ticket_created_at"), "ticket_created_at")
        expires = _utc_datetime(value.get("ticket_expires_at"), "ticket_expires_at")
        if expires <= created:
            raise ContractError("revalidation ticket expiry must follow creation")
        fallback_authorized = value.get("what_if_fallback_authorized") is True
        fallback_policy = value.get("what_if_fallback_policy_version")
        if fallback_authorized:
            fallback_policy = _text(
                fallback_policy,
                "what_if_fallback_policy_version",
            )
        elif fallback_policy is not None:
            raise ContractError("what-if fallback policy requires explicit authorization")
        return cls(
            original_analysis_id=_text(value.get("original_analysis_id"), "original_analysis_id"),
            candidate_id=_text(value.get("candidate_id"), "candidate_id"),
            selection_id=_text(value.get("selection_id"), "selection_id"),
            dossier_id=_text(value.get("dossier_id"), "dossier_id"),
            revalidation_ticket_id=_text(
                value.get("revalidation_ticket_id"), "revalidation_ticket_id"
            ),
            revalidation_ticket_hash=_sha256(
                value.get("revalidation_ticket_hash"), "revalidation_ticket_hash"
            ),
            ticket_created_at=created,
            ticket_expires_at=expires,
            confirmation_id=_text(value.get("confirmation_id"), "confirmation_id"),
            confirmation_hash=_sha256(value.get("confirmation_hash"), "confirmation_hash"),
            structure_type=_text(value.get("structure_type"), "structure_type"),
            structure_hash=_sha256(value.get("structure_hash"), "structure_hash"),
            current_market_snapshot_hash=_sha256(
                value.get("current_market_snapshot_hash"), "current_market_snapshot_hash"
            ),
            current_git_commit=_git_commit(
                value.get("current_git_commit"), "current_git_commit"
            ),
            current_config_hash=_sha256(
                value.get("current_config_hash"), "current_config_hash"
            ),
            proposed_limit=proposed_limit,
            valid_tick=valid_tick,
            capital_required_eur=_non_negative_decimal(
                value.get("capital_required_eur"), "capital_required_eur"
            ),
            maximum_loss_eur=_non_negative_decimal(
                value.get("maximum_loss_eur"), "maximum_loss_eur"
            ),
            expected_commissions_eur=_non_negative_decimal(
                value.get("expected_commissions_eur"), "expected_commissions_eur"
            ),
            cash_flow_type=cash_flow_type,
            combo_submission_mode=submission_mode,
            broker_combo_guarantee_mode=guarantee_mode,
            kill_switch_version=_text(
                value.get("kill_switch_version"), "kill_switch_version"
            ),
            what_if_fallback_authorized=fallback_authorized,
            what_if_fallback_policy_version=fallback_policy,
        )


@dataclass(frozen=True)
class PaperCommand:
    intent_id: str
    intent_type: str
    position_id: str | None
    preview_id: str | None
    order_ref: str
    ticker: str
    native_currency: str
    requested_quantity: int
    legs: tuple[ComboLeg, ...]
    maximum_exit_slippage_policy: Decimal
    pricing_policy: str
    time_in_force: str
    transmit: bool
    entry_authorization: PaperEntryAuthorization | None = None

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
        close_intents = {"MANUAL_CLOSE", "AUTOMATIC_FLOOR_EXIT", "NATIVE_PROTECTIVE_EXIT"}
        if intent_type not in {*close_intents, "PAPER_ENTRY"}:
            raise ContractError("unsupported paper intent type")
        entry = intent_type == "PAPER_ENTRY"
        pricing_policy = _text(value.get("pricing_policy"), "pricing_policy")
        if pricing_policy != "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT":
            raise ContractError("a refreshed bounded limit is mandatory")
        time_in_force = _text(value.get("time_in_force"), "time_in_force").upper()
        if time_in_force not in {"DAY", "GTC", "IOC", "FOK"}:
            raise ContractError("unsupported time_in_force")
        if entry and time_in_force != "DAY":
            raise ContractError("the first governed Paper entry must use DAY")
        transmit = value.get("transmit")
        if entry and transmit is not True:
            raise ContractError("a confirmed Paper entry command must request broker transmission")
        if not entry and transmit is not False:
            raise ContractError("close transmission remains disabled in this release")
        preview = value.get("preview_id")
        if entry:
            preview = _text(preview, "preview_id")
        elif preview is not None and not isinstance(preview, str):
            raise ContractError("preview_id must be text or null")
        raw_authorization = value.get("entry_authorization")
        if entry and not isinstance(raw_authorization, Mapping):
            raise ContractError("PAPER_ENTRY requires a complete entry_authorization")
        entry_authorization = (
            PaperEntryAuthorization.from_mapping(raw_authorization)
            if isinstance(raw_authorization, Mapping)
            else None
        )
        position_value = value.get("position_id")
        if not entry:
            position_value = _text(position_value, "position_id")
        elif position_value is not None:
            raise ContractError("PAPER_ENTRY cannot claim that an unopened position exists")
        maximum_exit_slippage_policy = _non_negative_decimal(
            value.get("maximum_exit_slippage_policy"),
            "maximum_exit_slippage_policy",
        )
        if entry and maximum_exit_slippage_policy != 0:
            raise ContractError("PAPER_ENTRY cannot reuse an exit-slippage allowance")
        return cls(
            intent_id=_text(value.get("intent_id"), "intent_id"),
            intent_type=intent_type,
            position_id=position_value,
            preview_id=preview,
            order_ref=_text(value.get("order_ref"), "order_ref"),
            ticker=_text(value.get("ticker"), "ticker").upper(),
            native_currency=_text(value.get("native_currency"), "native_currency").upper(),
            requested_quantity=_positive_int(value.get("requested_quantity"), "requested_quantity"),
            legs=tuple(ComboLeg.from_mapping(item, entry=entry) for item in raw_legs),
            maximum_exit_slippage_policy=maximum_exit_slippage_policy,
            pricing_policy=pricing_policy,
            time_in_force=time_in_force,
            transmit=bool(transmit),
            entry_authorization=entry_authorization,
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
class RecoveryIdentity:
    intent_id: str
    order_ref: str
    broker_order_id: int | None
    broker_perm_id: int | None
    broker_exec_ids: tuple[str, ...]


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
            "LOCAL_NOT_TRANSMITTED",
            "SUBMISSION_ATTEMPTED",
            "OPEN_ORDER",
            "OPEN_ORDER_END",
            "ORDER_STATUS",
            "ERROR",
            "EXECUTION",
            "EXECUTION_END",
            "BROKER_ACKNOWLEDGED",
            "PARTIAL_FILL",
            "FILLED",
            "COMMISSION_REPORT",
            "COMPLETED_ORDER",
            "COMPLETED_ORDERS_END",
            "REPRICE_PROPOSAL",
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
