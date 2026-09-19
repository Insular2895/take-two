"""Pure IBKR lifecycle normalization and preview-only execution diagnostics.

Nothing in this module can submit, modify, or cancel an order.  It converts future
callback evidence into deterministic, redacted records that the disabled bridge can
persist and test offline.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .contracts import GatewayEvent


class CanonicalExecutionStatus(StrEnum):
    CREATED = "CREATED"
    REVALIDATING = "REVALIDATING"
    EXECUTION_PREVIEW = "EXECUTION_PREVIEW"
    PREVIEW_READY = "PREVIEW_READY"
    CONFIRMED = "CONFIRMED"
    READY = "READY"
    CLAIMED = "CLAIMED"
    BROKER_SUBMISSION_ATTEMPTED = "BROKER_SUBMISSION_ATTEMPTED"
    LOCAL_NOT_TRANSMITTED = "LOCAL_NOT_TRANSMITTED"
    PENDING_SUBMIT = "PENDING_SUBMIT"
    PRE_SUBMITTED = "PRE_SUBMITTED"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELLED = "CANCELLED"
    API_CANCELLED = "API_CANCELLED"
    REJECTED = "REJECTED"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    AMBIGUOUS = "AMBIGUOUS"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class ExecutionCondition(StrEnum):
    NONE = "NONE"
    WORKING_NO_FILL_YET = "WORKING_NO_FILL_YET"
    PARTIAL_FILL_ACTIVE = "PARTIAL_FILL_ACTIVE"
    BROKER_HELD = "BROKER_HELD"
    TIF_CONDITION_NOT_SATISFIED = "TIF_CONDITION_NOT_SATISFIED"
    STATE_UNKNOWN = "STATE_UNKNOWN"


class CancellationCause(StrEnum):
    USER_REQUESTED = "USER_REQUESTED"
    API_REQUESTED = "API_REQUESTED"
    TWS_REQUESTED = "TWS_REQUESTED"
    BROKER_CANCELLED = "BROKER_CANCELLED"
    EXCHANGE_CANCELLED = "EXCHANGE_CANCELLED"
    TIF_EXPIRED = "TIF_EXPIRED"
    PRECAUTION = "PRECAUTION"
    INVALID_ORDER = "INVALID_ORDER"
    PRICE_PROTECTION = "PRICE_PROTECTION"
    SESSION_LOST = "SESSION_LOST"
    UNKNOWN = "UNKNOWN"


class RejectionCategory(StrEnum):
    MESSAGE_RATE = "MESSAGE_RATE"
    TICKER_LIMIT = "TICKER_LIMIT"
    ACCOUNT_PERMISSION = "ACCOUNT_PERMISSION"
    INSUFFICIENT_BUYING_POWER = "INSUFFICIENT_BUYING_POWER"
    MARKET_DATA_PERMISSION = "MARKET_DATA_PERMISSION"
    ORDER_PRECAUTION = "ORDER_PRECAUTION"
    LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE = "LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE"
    INVALID_CONTRACT = "INVALID_CONTRACT"
    INVALID_COMBO = "INVALID_COMBO"
    UNSUPPORTED_ORDER_TYPE = "UNSUPPORTED_ORDER_TYPE"
    EXCHANGE_RESTRICTION = "EXCHANGE_RESTRICTION"
    ACCOUNT_STATE = "ACCOUNT_STATE"
    SESSION_STATE = "SESSION_STATE"
    DUPLICATE_ORDER = "DUPLICATE_ORDER"
    INVALID_ORDER = "INVALID_ORDER"
    INVALID_TICK = "INVALID_TICK"
    INCOMPATIBLE_TIF = "INCOMPATIBLE_TIF"
    SUBMISSION_FAILED = "SUBMISSION_FAILED"
    MODIFICATION_FAILED = "MODIFICATION_FAILED"
    HALTED_SECURITY = "HALTED_SECURITY"
    INVALID_SIZE = "INVALID_SIZE"
    CANCELLATION = "CANCELLATION"
    WHAT_IF_UNSUPPORTED = "WHAT_IF_UNSUPPORTED"
    API_TRADING_NOT_ALLOWED = "API_TRADING_NOT_ALLOWED"
    COMBO_GUARANTEE = "COMBO_GUARANTEE"
    UNKNOWN_BROKER_REJECTION = "UNKNOWN_BROKER_REJECTION"


class CashFlowType(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class MarketabilityDiagnostic(StrEnum):
    WORKING_AT_BID_SIDE = "WORKING_AT_BID_SIDE"
    WORKING_AT_ASK_SIDE = "WORKING_AT_ASK_SIDE"
    WORKING_INSIDE_SPREAD = "WORKING_INSIDE_SPREAD"
    WORKING_NEAR_ASK = "WORKING_NEAR_ASK"
    WORKING_NEAR_BID = "WORKING_NEAR_BID"
    IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE = "IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE"
    MARKETABILITY_UNKNOWN_PRICE_CONVENTION_UNVERIFIED = (
        "MARKETABILITY_UNKNOWN_PRICE_CONVENTION_UNVERIFIED"
    )
    MARKETABILITY_UNKNOWN_DATA_STALE = "MARKETABILITY_UNKNOWN_DATA_STALE"
    MARKETABILITY_UNKNOWN_DATA_NOT_LIVE = "MARKETABILITY_UNKNOWN_DATA_NOT_LIVE"
    MARKETABILITY_UNKNOWN_NO_COMBO_QUOTE = "MARKETABILITY_UNKNOWN_NO_COMBO_QUOTE"
    MARKETABILITY_UNKNOWN_INVALID_QUOTE = "MARKETABILITY_UNKNOWN_INVALID_QUOTE"
    PAPER_SIMULATOR_LIMITATION_POSSIBLE = "PAPER_SIMULATOR_LIMITATION_POSSIBLE"


class RepriceStatus(StrEnum):
    READY_FOR_HUMAN_PREVIEW = "READY_FOR_HUMAN_PREVIEW"
    REPRICE_UNAVAILABLE_DATA_STALE = "REPRICE_UNAVAILABLE_DATA_STALE"
    REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED = (
        "REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED"
    )
    BLOCKED_AUTHORIZED_BOUND = "BLOCKED_AUTHORIZED_BOUND"
    BLOCKED_HARD_BUDGET = "BLOCKED_HARD_BUDGET"
    BLOCKED_MAX_LOSS = "BLOCKED_MAX_LOSS"
    BLOCKED_ORDER_SHAPE_CHANGED = "BLOCKED_ORDER_SHAPE_CHANGED"
    BLOCKED_DIRECTION = "BLOCKED_DIRECTION"


@dataclass(frozen=True)
class OrderStatusEvidence:
    order_id: int
    status: str
    filled: Decimal
    remaining: Decimal
    avg_fill_price: Decimal | None
    perm_id: int | None
    parent_id: int | None
    last_fill_price: Decimal | None
    client_id: int | None
    why_held: str | None
    market_cap_price: Decimal | None
    received_at: datetime
    transmitted_to_broker: bool
    time_in_force: str | None = None
    cancellation_cause: CancellationCause | None = None


@dataclass(frozen=True)
class OpenOrderEvidence:
    order_id: int
    perm_id: int | None
    client_id: int | None
    order_ref: str
    raw_status: str
    total_quantity: Decimal
    limit_price: Decimal | None
    time_in_force: str
    transmit: bool
    received_at: datetime


@dataclass(frozen=True)
class BrokerErrorEvidence:
    request_or_order_id: int
    error_code: int
    message: str
    advanced_rejection_json: str | None
    received_at: datetime
    order_rejected: bool
    transmitted_to_broker: bool | None = None
    perm_id: int | None = None


@dataclass(frozen=True)
class ExecutionEvidence:
    exec_id: str
    order_id: int
    perm_id: int | None
    shares: Decimal
    cumulative_quantity: Decimal
    remaining_quantity: Decimal
    price: Decimal
    side: str
    exchange: str
    execution_time: datetime
    received_at: datetime
    liquidation: bool | None = None
    combo_bid_near_fill: Decimal | None = None
    combo_ask_near_fill: Decimal | None = None
    execution_delay_seconds: Decimal | None = None
    slippage_vs_decision_midpoint: Decimal | None = None
    slippage_vs_executable_quote: Decimal | None = None
    partial_fill_sequence: int | None = None
    execution_environment: str = "IBKR_PAPER_SIMULATOR"
    fill_evidence: str = "PAPER_SIMULATED_FILL"


@dataclass(frozen=True)
class CommissionEvidence:
    exec_id: str
    commission: Decimal
    currency: str
    received_at: datetime
    realized_pnl: Decimal | None = None
    yield_value: Decimal | None = None
    yield_redemption_date: int | None = None


@dataclass(frozen=True)
class ExecutionDiagnosticSnapshot:
    ticker: str
    candidate_id: str | None
    strategy: str
    quantity: int
    legs: tuple[dict[str, Any], ...]
    market_data_type: str
    snapshot_timestamp: datetime
    data_freshness: str
    combo_bid: Decimal | None
    combo_ask: Decimal | None
    combo_midpoint: Decimal | None
    synthetic_combo_bid: Decimal | None
    synthetic_combo_ask: Decimal | None
    signed_price_convention_verified: bool
    requested_limit: Decimal
    cash_flow_type: CashFlowType
    expected_commission: Decimal | None
    capital_required: Decimal | None
    maximum_loss: Decimal | None
    spread_absolute: Decimal | None
    spread_percent: Decimal | None
    quote_age_seconds: Decimal | None

    def as_payload(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "candidate_id": self.candidate_id,
            "strategy": self.strategy,
            "quantity": self.quantity,
            "legs": list(self.legs),
            "market_data_type": self.market_data_type,
            "snapshot_timestamp": _utc_text(self.snapshot_timestamp),
            "data_freshness": self.data_freshness,
            "combo_bid": _decimal(self.combo_bid),
            "combo_ask": _decimal(self.combo_ask),
            "combo_midpoint": _decimal(self.combo_midpoint),
            "synthetic_combo_bid": _decimal(self.synthetic_combo_bid),
            "synthetic_combo_ask": _decimal(self.synthetic_combo_ask),
            "signed_price_convention_status": (
                "VERIFIED" if self.signed_price_convention_verified else "UNVERIFIED"
            ),
            "requested_limit": _decimal(self.requested_limit),
            "cash_flow_type": self.cash_flow_type.value,
            "expected_commission": _decimal(self.expected_commission),
            "capital_required": _decimal(self.capital_required),
            "maximum_loss": _decimal(self.maximum_loss),
            "spread_absolute": _decimal(self.spread_absolute),
            "spread_percent": _decimal(self.spread_percent),
            "quote_age_seconds": _decimal(self.quote_age_seconds),
        }


@dataclass(frozen=True)
class MarketabilityInput:
    cash_flow_type: CashFlowType
    requested_limit: Decimal
    combo_bid: Decimal | None
    combo_ask: Decimal | None
    market_data_type: str
    combo_freshness: str
    option_freshness: str
    underlying_freshness: str
    fx_freshness: str | None
    fx_required: bool
    price_convention_verified: bool


@dataclass(frozen=True)
class RepriceRequest:
    cash_flow_type: CashFlowType
    current_limit: Decimal
    proposed_limit: Decimal
    combo_bid: Decimal | None
    combo_ask: Decimal | None
    quantity: int
    multiplier: Decimal
    maximum_debit_policy: Decimal | None
    minimum_credit_policy: Decimal | None
    remaining_hard_budget_headroom: Decimal | None
    remaining_max_loss_headroom: Decimal | None
    current_estimated_pnl: Decimal | None
    original_order_shape_hash: str
    proposed_order_shape_hash: str
    market_data_type: str
    combo_freshness: str
    option_freshness: str
    underlying_freshness: str
    fx_freshness: str | None
    fx_required: bool
    price_convention_verified: bool


@dataclass(frozen=True)
class RepriceProposal:
    status: RepriceStatus
    cash_flow_type: CashFlowType
    current_limit: Decimal
    proposed_limit: Decimal
    price_difference: Decimal
    incremental_capital_impact: Decimal
    remaining_hard_budget_headroom: Decimal | None
    authorized_boundary: Decimal | None
    new_estimated_pnl_economics: Decimal | None
    original_order_shape_hash: str
    proposed_order_shape_hash: str
    automatic_action_allowed: bool = False

    def as_payload(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "cash_flow_type": self.cash_flow_type.value,
            "current_limit": _decimal(self.current_limit),
            "proposed_limit": _decimal(self.proposed_limit),
            "price_difference": _decimal(self.price_difference),
            "incremental_capital_impact": _decimal(self.incremental_capital_impact),
            "remaining_hard_budget_headroom": _decimal(self.remaining_hard_budget_headroom),
            "authorized_boundary": _decimal(self.authorized_boundary),
            "new_estimated_pnl_economics": _decimal(self.new_estimated_pnl_economics),
            "original_order_shape_hash": self.original_order_shape_hash,
            "proposed_order_shape_hash": self.proposed_order_shape_hash,
            "automatic_action_allowed": False,
        }


def _decimal(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("broker evidence timestamp must include a timezone")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _evidence_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode()).hexdigest()


_ACCOUNT_PATTERN = re.compile(r"\b(?:DU|U|F|DF)\d{4,}\b", re.IGNORECASE)
_SECRET_PATTERN = re.compile(r"(?i)(password|passwd|token|secret|api[_ -]?key)\s*[:=]\s*[^\s,;]+")


def redact_broker_message(message: str, maximum_length: int = 2_000) -> str:
    normalized = " ".join(message.replace("\x00", " ").split())
    normalized = _ACCOUNT_PATTERN.sub("[REDACTED_ACCOUNT]", normalized)
    normalized = _SECRET_PATTERN.sub(lambda item: f"{item.group(1)}=[REDACTED]", normalized)
    return normalized[:maximum_length]


def _redact_json(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(marker in lowered for marker in ("account", "password", "secret", "token")):
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = _redact_json(item)
        return redacted
    if isinstance(value, list):
        return [_redact_json(item) for item in value[:100]]
    if isinstance(value, str):
        return redact_broker_message(value)
    return value


def redact_advanced_rejection_json(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return _canonical_json({"unparsed_redacted": redact_broker_message(value)})
    return _canonical_json(_redact_json(parsed))[:8_000]


def classify_rejection(error_code: int, message: str) -> RejectionCategory:
    text = message.casefold()
    exact_codes = {
        100: RejectionCategory.MESSAGE_RATE,
        101: RejectionCategory.TICKER_LIMIT,
        103: RejectionCategory.DUPLICATE_ORDER,
        106: RejectionCategory.INVALID_ORDER,
        107: RejectionCategory.INVALID_ORDER,
        109: RejectionCategory.ORDER_PRECAUTION,
        110: RejectionCategory.INVALID_TICK,
        111: RejectionCategory.INCOMPATIBLE_TIF,
        116: RejectionCategory.EXCHANGE_RESTRICTION,
        133: RejectionCategory.SUBMISSION_FAILED,
        134: RejectionCategory.MODIFICATION_FAILED,
        154: RejectionCategory.HALTED_SECURITY,
        160: RejectionCategory.INVALID_SIZE,
        163: RejectionCategory.ORDER_PRECAUTION,
        164: RejectionCategory.ORDER_PRECAUTION,
        200: RejectionCategory.INVALID_CONTRACT,
        202: RejectionCategory.CANCELLATION,
        203: RejectionCategory.ACCOUNT_PERMISSION,
        312: RejectionCategory.INVALID_COMBO,
        313: RejectionCategory.INVALID_COMBO,
        314: RejectionCategory.INVALID_COMBO,
        315: RejectionCategory.EXCHANGE_RESTRICTION,
        354: RejectionCategory.MARKET_DATA_PERMISSION,
        355: RejectionCategory.INVALID_SIZE,
        360: RejectionCategory.WHAT_IF_UNSUPPORTED,
        10002: RejectionCategory.COMBO_GUARANTEE,
        10015: RejectionCategory.API_TRADING_NOT_ALLOWED,
        10089: RejectionCategory.MARKET_DATA_PERMISSION,
        10090: RejectionCategory.MARKET_DATA_PERMISSION,
        10091: RejectionCategory.MARKET_DATA_PERMISSION,
        10186: RejectionCategory.MARKET_DATA_PERMISSION,
        10197: RejectionCategory.SESSION_STATE,
    }
    if error_code in exact_codes:
        return exact_codes[error_code]
    if "duplicate order" in text:
        return RejectionCategory.DUPLICATE_ORDER
    if "precaution" in text or "percentage setting" in text:
        return RejectionCategory.ORDER_PRECAUTION
    if "price protection" in text or "outside allowed" in text or "price cap" in text:
        return RejectionCategory.LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE
    if "security definition" in text or "invalid contract" in text:
        return RejectionCategory.INVALID_CONTRACT
    if "combo" in text and any(word in text for word in ("invalid", "rejected", "ratio")):
        return RejectionCategory.INVALID_COMBO
    if "buying power" in text or "insufficient" in text and "fund" in text:
        return RejectionCategory.INSUFFICIENT_BUYING_POWER
    if "market data" in text and any(word in text for word in ("permission", "subscription")):
        return RejectionCategory.MARKET_DATA_PERMISSION
    if "permission" in text or "not allowed for this account" in text:
        return RejectionCategory.ACCOUNT_PERMISSION
    if "order type" in text and any(word in text for word in ("unsupported", "not supported")):
        return RejectionCategory.UNSUPPORTED_ORDER_TYPE
    if "exchange" in text and any(word in text for word in ("restrict", "not available")):
        return RejectionCategory.EXCHANGE_RESTRICTION
    if "account" in text and any(word in text for word in ("closed", "restricted", "state")):
        return RejectionCategory.ACCOUNT_STATE
    if error_code in {503, 504} or "not connected" in text or "session" in text:
        return RejectionCategory.SESSION_STATE
    return RejectionCategory.UNKNOWN_BROKER_REJECTION


def _canonical_raw_status(raw_status: str) -> CanonicalExecutionStatus:
    mapping = {
        "pendingsubmit": CanonicalExecutionStatus.PENDING_SUBMIT,
        "presubmitted": CanonicalExecutionStatus.PRE_SUBMITTED,
        "submitted": CanonicalExecutionStatus.WORKING,
        "pendingcancel": CanonicalExecutionStatus.PENDING_CANCEL,
        "precancelled": CanonicalExecutionStatus.PENDING_CANCEL,
        "cancelled": CanonicalExecutionStatus.CANCELLED,
        "apicancelled": CanonicalExecutionStatus.API_CANCELLED,
        "filled": CanonicalExecutionStatus.FILLED,
        "inactive": CanonicalExecutionStatus.INACTIVE,
    }
    return mapping.get(
        raw_status.replace("_", "").casefold(), CanonicalExecutionStatus.AMBIGUOUS
    )


def canonical_order_status(evidence: OrderStatusEvidence) -> CanonicalExecutionStatus:
    if not evidence.transmitted_to_broker:
        return CanonicalExecutionStatus.LOCAL_NOT_TRANSMITTED
    if evidence.filled > 0 and evidence.remaining == 0:
        return CanonicalExecutionStatus.FILLED
    if evidence.filled > 0 and evidence.remaining > 0:
        return CanonicalExecutionStatus.PARTIALLY_FILLED
    return _canonical_raw_status(evidence.status)


def execution_condition(
    status: CanonicalExecutionStatus,
    evidence: OrderStatusEvidence,
) -> ExecutionCondition:
    if evidence.why_held and status not in {
        CanonicalExecutionStatus.FILLED,
        CanonicalExecutionStatus.CANCELLED,
        CanonicalExecutionStatus.API_CANCELLED,
    }:
        return ExecutionCondition.BROKER_HELD
    if (
        status is CanonicalExecutionStatus.WORKING
        and evidence.filled == 0
        and evidence.remaining > 0
    ):
        return ExecutionCondition.WORKING_NO_FILL_YET
    if status is CanonicalExecutionStatus.PARTIALLY_FILLED:
        return ExecutionCondition.PARTIAL_FILL_ACTIVE
    if (
        status in {CanonicalExecutionStatus.CANCELLED, CanonicalExecutionStatus.API_CANCELLED}
        and evidence.cancellation_cause is CancellationCause.TIF_EXPIRED
    ):
        return ExecutionCondition.TIF_CONDITION_NOT_SATISFIED
    if status in {
        CanonicalExecutionStatus.AMBIGUOUS,
        CanonicalExecutionStatus.RECONCILIATION_REQUIRED,
    }:
        return ExecutionCondition.STATE_UNKNOWN
    return ExecutionCondition.NONE


class IBKRBrokerExecutionNormalizer:
    """Broker-specific evidence mapper with no broker mutation capability."""

    @staticmethod
    def _event(
        event_type: str,
        occurred_at: datetime,
        raw: dict[str, Any],
        *,
        order_id: int | None = None,
        perm_id: int | None = None,
        exec_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> GatewayEvent:
        digest = _evidence_hash(raw)
        return GatewayEvent(
            broker_event_key=f"ibkr:{event_type.casefold()}:{digest[:32]}",
            event_type=event_type,
            occurred_at=occurred_at,
            broker_order_id=order_id,
            broker_perm_id=perm_id,
            broker_exec_id=exec_id,
            detail={**(detail or {}), "raw_evidence_hash": digest},
        )

    def order_status(self, evidence: OrderStatusEvidence) -> GatewayEvent:
        status = canonical_order_status(evidence)
        condition = execution_condition(status, evidence)
        raw = {
            "callback": "orderStatus",
            "order_id": evidence.order_id,
            "status": evidence.status,
            "filled": str(evidence.filled),
            "remaining": str(evidence.remaining),
            "avg_fill_price": str(evidence.avg_fill_price),
            "perm_id": evidence.perm_id,
            "parent_id": evidence.parent_id,
            "last_fill_price": str(evidence.last_fill_price),
            "client_id": evidence.client_id,
            "why_held": evidence.why_held,
            "market_cap_price": str(evidence.market_cap_price),
            "received_at": _utc_text(evidence.received_at),
        }
        detail = {
            "callback": "orderStatus",
            "raw_broker_status": evidence.status,
            "canonical_execution_status": status.value,
            "execution_condition": condition.value,
            "filled": _decimal(evidence.filled),
            "remaining": _decimal(evidence.remaining),
            "average_fill_price": _decimal(evidence.avg_fill_price),
            "parent_id": evidence.parent_id,
            "last_fill_price": _decimal(evidence.last_fill_price),
            "client_id": evidence.client_id,
            "why_held": redact_broker_message(evidence.why_held or "") or None,
            "market_cap_price": _decimal(evidence.market_cap_price),
            "transmitted_to_broker": evidence.transmitted_to_broker,
            "time_in_force": evidence.time_in_force,
            "cancellation_cause": (
                evidence.cancellation_cause.value if evidence.cancellation_cause else None
            ),
        }
        return self._event(
            "ORDER_STATUS",
            evidence.received_at,
            raw,
            order_id=evidence.order_id,
            perm_id=evidence.perm_id,
            detail=detail,
        )

    def submission_attempted(
        self,
        snapshot: ExecutionDiagnosticSnapshot,
        attempted_at: datetime,
        *,
        order_id: int | None = None,
    ) -> GatewayEvent:
        snapshot_payload = snapshot.as_payload()
        raw = {
            "callback": "localSubmissionAttempt",
            "order_id": order_id,
            "attempted_at": _utc_text(attempted_at),
            "market_snapshot": snapshot_payload,
        }
        return self._event(
            "SUBMISSION_ATTEMPTED",
            attempted_at,
            raw,
            order_id=order_id,
            detail={
                "callback": "localSubmissionAttempt",
                "raw_broker_status": None,
                "canonical_execution_status": None,
                "execution_condition": ExecutionCondition.NONE.value,
                "transmitted_to_broker": None,
                "market_snapshot": snapshot_payload,
            },
        )

    def reprice_proposal(
        self,
        proposal: RepriceProposal,
        proposal_id: str,
        created_at: datetime,
    ) -> GatewayEvent:
        if not re.fullmatch(r"broker-reprice_[A-Za-z0-9._-]+", proposal_id):
            raise ValueError("invalid reprice proposal identity")
        payload = {
            "proposal_id": proposal_id,
            "created_at": _utc_text(created_at),
            **proposal.as_payload(),
        }
        return self._event(
            "REPRICE_PROPOSAL",
            created_at,
            {"callback": "localRepricePreview", **payload},
            detail=payload,
        )

    def open_order(self, evidence: OpenOrderEvidence) -> GatewayEvent:
        canonical = (
            CanonicalExecutionStatus.LOCAL_NOT_TRANSMITTED
            if not evidence.transmit
            else _canonical_raw_status(evidence.raw_status)
        )
        broker_received = (
            False
            if not evidence.transmit
            else canonical
            in {
                CanonicalExecutionStatus.PRE_SUBMITTED,
                CanonicalExecutionStatus.WORKING,
                CanonicalExecutionStatus.PARTIALLY_FILLED,
                CanonicalExecutionStatus.FILLED,
                CanonicalExecutionStatus.PENDING_CANCEL,
                CanonicalExecutionStatus.CANCELLED,
                CanonicalExecutionStatus.API_CANCELLED,
            }
            or None
        )
        raw = {
            "callback": "openOrder",
            "order_id": evidence.order_id,
            "perm_id": evidence.perm_id,
            "client_id": evidence.client_id,
            "order_ref": evidence.order_ref,
            "raw_status": evidence.raw_status,
            "total_quantity": str(evidence.total_quantity),
            "limit_price": str(evidence.limit_price),
            "time_in_force": evidence.time_in_force,
            "transmit": evidence.transmit,
        }
        return self._event(
            "OPEN_ORDER",
            evidence.received_at,
            raw,
            order_id=evidence.order_id,
            perm_id=evidence.perm_id,
            detail={
                "callback": "openOrder",
                "order_ref": evidence.order_ref,
                "raw_broker_status": evidence.raw_status,
                "canonical_execution_status": canonical.value,
                "execution_condition": (
                    ExecutionCondition.STATE_UNKNOWN.value
                    if canonical is CanonicalExecutionStatus.AMBIGUOUS
                    else ExecutionCondition.NONE.value
                ),
                "total_quantity": _decimal(evidence.total_quantity),
                "limit_price": _decimal(evidence.limit_price),
                "time_in_force": evidence.time_in_force,
                "transmit_flag": evidence.transmit,
                "transmitted_to_broker": broker_received,
            },
        )

    def error(self, evidence: BrokerErrorEvidence) -> GatewayEvent:
        redacted_message = redact_broker_message(evidence.message)
        category = classify_rejection(evidence.error_code, redacted_message)
        precaution = category is RejectionCategory.ORDER_PRECAUTION
        if precaution and evidence.transmitted_to_broker is False:
            canonical = CanonicalExecutionStatus.LOCAL_NOT_TRANSMITTED
        elif evidence.order_rejected:
            canonical = CanonicalExecutionStatus.REJECTED
        elif (
            category is RejectionCategory.SESSION_STATE
            and evidence.request_or_order_id >= 0
        ):
            canonical = CanonicalExecutionStatus.RECONCILIATION_REQUIRED
        else:
            canonical = None
        raw = {
            "callback": "error",
            "request_or_order_id": evidence.request_or_order_id,
            "error_code": evidence.error_code,
            "message": evidence.message,
            "advanced_rejection_json": evidence.advanced_rejection_json,
            "received_at": _utc_text(evidence.received_at),
        }
        return self._event(
            "ERROR",
            evidence.received_at,
            raw,
            order_id=evidence.request_or_order_id if evidence.request_or_order_id >= 0 else None,
            perm_id=evidence.perm_id,
            detail={
                "callback": "error",
                "broker_error_code": evidence.error_code,
                "redacted_broker_message": redacted_message,
                "advanced_rejection_json": redact_advanced_rejection_json(
                    evidence.advanced_rejection_json
                ),
                "normalized_category": category.value,
                "precaution": precaution,
                "order_rejected": evidence.order_rejected,
                "transmitted_to_broker": evidence.transmitted_to_broker,
                "canonical_execution_status": canonical.value if canonical else None,
                "execution_condition": (
                    ExecutionCondition.STATE_UNKNOWN.value
                    if canonical is CanonicalExecutionStatus.RECONCILIATION_REQUIRED
                    else ExecutionCondition.NONE.value
                ),
            },
        )

    def execution(self, evidence: ExecutionEvidence) -> GatewayEvent:
        canonical = (
            CanonicalExecutionStatus.FILLED
            if evidence.remaining_quantity == 0
            else CanonicalExecutionStatus.PARTIALLY_FILLED
        )
        condition = (
            ExecutionCondition.NONE
            if canonical is CanonicalExecutionStatus.FILLED
            else ExecutionCondition.PARTIAL_FILL_ACTIVE
        )
        raw = {
            "callback": "execDetails",
            "exec_id": evidence.exec_id,
            "order_id": evidence.order_id,
            "perm_id": evidence.perm_id,
            "shares": str(evidence.shares),
            "cumulative_quantity": str(evidence.cumulative_quantity),
            "remaining_quantity": str(evidence.remaining_quantity),
            "price": str(evidence.price),
            "side": evidence.side,
            "exchange": evidence.exchange,
            "execution_time": _utc_text(evidence.execution_time),
            "combo_bid_near_fill": str(evidence.combo_bid_near_fill),
            "combo_ask_near_fill": str(evidence.combo_ask_near_fill),
            "execution_delay_seconds": str(evidence.execution_delay_seconds),
            "slippage_vs_decision_midpoint": str(evidence.slippage_vs_decision_midpoint),
            "slippage_vs_executable_quote": str(evidence.slippage_vs_executable_quote),
            "partial_fill_sequence": evidence.partial_fill_sequence,
        }
        return self._event(
            "EXECUTION",
            evidence.execution_time,
            raw,
            order_id=evidence.order_id,
            perm_id=evidence.perm_id,
            exec_id=evidence.exec_id,
            detail={
                "callback": "execDetails",
                "canonical_execution_status": canonical.value,
                "execution_condition": condition.value,
                "shares": _decimal(evidence.shares),
                "cumulative_quantity": _decimal(evidence.cumulative_quantity),
                "remaining": _decimal(evidence.remaining_quantity),
                "price": _decimal(evidence.price),
                "side": evidence.side,
                "exchange": evidence.exchange,
                "execution_time": _utc_text(evidence.execution_time),
                "liquidation": evidence.liquidation,
                "combo_bid_near_fill": _decimal(evidence.combo_bid_near_fill),
                "combo_ask_near_fill": _decimal(evidence.combo_ask_near_fill),
                "execution_delay_seconds": _decimal(evidence.execution_delay_seconds),
                "slippage_vs_decision_midpoint": _decimal(
                    evidence.slippage_vs_decision_midpoint
                ),
                "slippage_vs_executable_quote": _decimal(
                    evidence.slippage_vs_executable_quote
                ),
                "partial_fill_sequence": evidence.partial_fill_sequence,
                "transmitted_to_broker": True,
                "execution_environment": evidence.execution_environment,
                "fill_evidence": evidence.fill_evidence,
            },
        )

    def commission(self, evidence: CommissionEvidence) -> GatewayEvent:
        raw = {
            "callback": "commissionReport",
            "exec_id": evidence.exec_id,
            "commission": str(evidence.commission),
            "currency": evidence.currency,
            "realized_pnl": str(evidence.realized_pnl),
            "yield_value": str(evidence.yield_value),
            "yield_redemption_date": evidence.yield_redemption_date,
        }
        return self._event(
            "COMMISSION_REPORT",
            evidence.received_at,
            raw,
            exec_id=evidence.exec_id,
            detail={
                "callback": "commissionReport",
                "exec_id": evidence.exec_id,
                "commission": _decimal(evidence.commission),
                "currency": evidence.currency,
                "realized_pnl": _decimal(evidence.realized_pnl),
                "yield_value": _decimal(evidence.yield_value),
                "yield_redemption_date": evidence.yield_redemption_date,
            },
        )

    def callback_boundary(
        self,
        callback: str,
        received_at: datetime,
        request_id: int | None = None,
    ) -> GatewayEvent:
        mapping = {
            "openOrderEnd": "OPEN_ORDER_END",
            "execDetailsEnd": "EXECUTION_END",
            "completedOrdersEnd": "COMPLETED_ORDERS_END",
        }
        if callback not in mapping:
            raise ValueError("unsupported lifecycle callback boundary")
        raw = {"callback": callback, "request_id": request_id}
        return self._event(
            mapping[callback],
            received_at,
            raw,
            detail={"callback": callback, "request_id": request_id},
        )


def classify_marketability(value: MarketabilityInput) -> MarketabilityDiagnostic:
    if not value.price_convention_verified:
        return MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_PRICE_CONVENTION_UNVERIFIED
    if value.market_data_type.casefold() != "live":
        return MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_DATA_NOT_LIVE
    required_freshness = [
        value.combo_freshness,
        value.option_freshness,
        value.underlying_freshness,
    ]
    if value.fx_required:
        required_freshness.append(value.fx_freshness or "MISSING")
    if any(item != "FRESH" for item in required_freshness):
        return MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_DATA_STALE
    if value.combo_bid is None or value.combo_ask is None:
        return MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_NO_COMBO_QUOTE
    if value.combo_bid < 0 or value.combo_ask < 0 or value.combo_bid > value.combo_ask:
        return MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_INVALID_QUOTE
    midpoint = (value.combo_bid + value.combo_ask) / 2
    if value.cash_flow_type is CashFlowType.DEBIT:
        if value.requested_limit >= value.combo_ask:
            return MarketabilityDiagnostic.IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE
        if value.requested_limit <= value.combo_bid:
            return MarketabilityDiagnostic.WORKING_AT_BID_SIDE
        if value.requested_limit >= midpoint:
            return MarketabilityDiagnostic.WORKING_NEAR_ASK
        return MarketabilityDiagnostic.WORKING_INSIDE_SPREAD
    if value.requested_limit <= value.combo_bid:
        return MarketabilityDiagnostic.IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE
    if value.requested_limit >= value.combo_ask:
        return MarketabilityDiagnostic.WORKING_AT_ASK_SIDE
    if value.requested_limit <= midpoint:
        return MarketabilityDiagnostic.WORKING_NEAR_BID
    return MarketabilityDiagnostic.WORKING_INSIDE_SPREAD


def propose_reprice(value: RepriceRequest) -> RepriceProposal:
    impact_per_unit = abs(value.proposed_limit - value.current_limit)
    capital_impact = impact_per_unit * value.multiplier * value.quantity
    status = RepriceStatus.READY_FOR_HUMAN_PREVIEW
    boundary = (
        value.maximum_debit_policy
        if value.cash_flow_type is CashFlowType.DEBIT
        else value.minimum_credit_policy
    )
    freshness = [value.combo_freshness, value.option_freshness, value.underlying_freshness]
    if value.fx_required:
        freshness.append(value.fx_freshness or "MISSING")
    if value.original_order_shape_hash != value.proposed_order_shape_hash:
        status = RepriceStatus.BLOCKED_ORDER_SHAPE_CHANGED
    elif not value.price_convention_verified:
        status = RepriceStatus.REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED
    elif (
        value.market_data_type.casefold() != "live"
        or any(item != "FRESH" for item in freshness)
        or value.combo_bid is None
        or value.combo_ask is None
        or value.combo_bid < 0
        or value.combo_ask < value.combo_bid
    ):
        status = RepriceStatus.REPRICE_UNAVAILABLE_DATA_STALE
    elif value.cash_flow_type is CashFlowType.DEBIT and value.proposed_limit < value.current_limit:
        status = RepriceStatus.BLOCKED_DIRECTION
    elif value.cash_flow_type is CashFlowType.CREDIT and value.proposed_limit > value.current_limit:
        status = RepriceStatus.BLOCKED_DIRECTION
    elif boundary is None:
        status = RepriceStatus.BLOCKED_AUTHORIZED_BOUND
    elif value.cash_flow_type is CashFlowType.DEBIT and value.proposed_limit > boundary:
        status = RepriceStatus.BLOCKED_AUTHORIZED_BOUND
    elif value.cash_flow_type is CashFlowType.CREDIT and value.proposed_limit < boundary:
        status = RepriceStatus.BLOCKED_AUTHORIZED_BOUND
    elif (
        value.remaining_hard_budget_headroom is None
        or capital_impact > value.remaining_hard_budget_headroom
    ):
        status = RepriceStatus.BLOCKED_HARD_BUDGET
    elif (
        value.remaining_max_loss_headroom is None
        or capital_impact > value.remaining_max_loss_headroom
    ):
        status = RepriceStatus.BLOCKED_MAX_LOSS
    new_pnl = (
        None
        if value.current_estimated_pnl is None
        else value.current_estimated_pnl - capital_impact
    )
    return RepriceProposal(
        status=status,
        cash_flow_type=value.cash_flow_type,
        current_limit=value.current_limit,
        proposed_limit=value.proposed_limit,
        price_difference=value.proposed_limit - value.current_limit,
        incremental_capital_impact=capital_impact,
        remaining_hard_budget_headroom=value.remaining_hard_budget_headroom,
        authorized_boundary=boundary,
        new_estimated_pnl_economics=new_pnl,
        original_order_shape_hash=value.original_order_shape_hash,
        proposed_order_shape_hash=value.proposed_order_shape_hash,
    )
