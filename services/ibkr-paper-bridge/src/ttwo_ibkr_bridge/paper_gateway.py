"""Isolated, Paper-only IBKR execution adapter.

The default process does not instantiate this class.  A future operator-authorized
composition root must provide one persistent official-API transport and complete
preflight evidence.  This module never enables a broker setting and has no Live mode.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from .contracts import (
    ComboLeg,
    GatewayEvent,
    GatewayHealth,
    PaperCommand,
    PaperEntryAuthorization,
    RecoveryIdentity,
)

PAPER_PORTS = frozenset({7497, 4002})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
GLOBAL_PAPER_HARD_CEILING_EUR = Decimal("1500")


class PaperGatewayBlocked(RuntimeError):
    """Raised before the broker primitive when a governed Paper gate fails."""


class MarketWindow(StrEnum):
    MARKET_OPEN = "MARKET_OPEN"
    LIQUID_HOURS = "LIQUID_HOURS"
    OUTSIDE_LIQUID_HOURS = "OUTSIDE_LIQUID_HOURS"
    MARKET_CLOSED = "MARKET_CLOSED"
    UNKNOWN = "UNKNOWN"


class BrokerWhatIfStatus(StrEnum):
    BROKER_WHAT_IF_CONFIRMED = "BROKER_WHAT_IF_CONFIRMED"
    BROKER_WHAT_IF_UNSUPPORTED = "BROKER_WHAT_IF_UNSUPPORTED"
    BROKER_WHAT_IF_INCOMPLETE = "BROKER_WHAT_IF_INCOMPLETE"
    BROKER_WHAT_IF_FAILED = "BROKER_WHAT_IF_FAILED"


@dataclass(frozen=True)
class PaperGatewayConfig:
    host: str
    port: int
    client_id: int
    paper_account: str
    session_username_hash: str
    expected_kill_switch_version: str
    expected_git_commit: str
    expected_config_hash: str
    maximum_preflight_age_seconds: int
    armed_for_governed_paper_entry: bool = False

    def __post_init__(self) -> None:
        if self.host not in LOOPBACK_HOSTS:
            raise ValueError("PAPER_GATEWAY_LOOPBACK_REQUIRED")
        if self.port not in PAPER_PORTS:
            raise ValueError("PAPER_GATEWAY_PORT_REQUIRED")
        if self.client_id <= 0:
            raise ValueError("PAPER_GATEWAY_STABLE_CLIENT_ID_REQUIRED")
        if not self.paper_account.startswith("DU"):
            raise ValueError("PAPER_GATEWAY_DU_ACCOUNT_REQUIRED")
        if len(self.session_username_hash) != 64:
            raise ValueError("PAPER_GATEWAY_USERNAME_HASH_REQUIRED")
        if not self.expected_kill_switch_version:
            raise ValueError("PAPER_GATEWAY_KILL_SWITCH_VERSION_REQUIRED")
        if not (
            7 <= len(self.expected_git_commit) <= 40
            and all(character in "0123456789abcdef" for character in self.expected_git_commit)
        ):
            raise ValueError("PAPER_GATEWAY_GIT_COMMIT_REQUIRED")
        if not (
            len(self.expected_config_hash) == 64
            and all(character in "0123456789abcdef" for character in self.expected_config_hash)
        ):
            raise ValueError("PAPER_GATEWAY_CONFIG_HASH_REQUIRED")
        if self.maximum_preflight_age_seconds <= 0:
            raise ValueError("PAPER_GATEWAY_PREFLIGHT_MAX_AGE_REQUIRED")


@dataclass(frozen=True)
class SessionEvidence:
    gateway_connected: bool
    ib_server_connected: bool
    market_data_farm_connected: bool
    accounts: tuple[str, ...]
    client_id: int
    session_username_hash: str
    next_valid_id: int | None
    read_only_api: bool
    maintain_and_resubmit_on_reconnect: bool
    bypass_order_precautions: bool
    override_percentage_constraints: bool
    api_message_log_enabled: bool
    logging_level: str
    observed_at: datetime


@dataclass(frozen=True)
class PriceIncrementBand:
    low_edge: Decimal
    increment: Decimal


@dataclass(frozen=True)
class MarketRuleEvidence:
    market_rule_id: int
    price_increments: tuple[PriceIncrementBand, ...]
    min_size: Decimal
    size_increment: Decimal
    suggested_size_increment: Decimal | None

    def increment_at(self, price: Decimal) -> Decimal | None:
        eligible = [band for band in self.price_increments if price >= band.low_edge]
        if not eligible:
            return None
        return max(eligible, key=lambda band: band.low_edge).increment

    def price_is_valid(self, price: Decimal) -> bool:
        increment = self.increment_at(price)
        return increment is not None and increment > 0 and price % increment == 0

    def quantity_is_valid(self, quantity: int) -> bool:
        value = Decimal(quantity)
        return (
            self.size_increment > 0
            and value >= self.min_size
            and (value - self.min_size) % self.size_increment == 0
        )


@dataclass(frozen=True)
class QualifiedContractEvidence:
    con_id: int
    local_symbol: str
    trading_class: str
    expiration: str
    strike: Decimal
    right: str
    multiplier: int
    currency: str
    exchange: str
    valid_exchanges: tuple[str, ...]
    supported_order_types: tuple[str, ...]
    real_expiration_date: str | None
    identity_match_count: int
    adjusted_or_non_standard: bool
    market_rule_ids: tuple[int, ...]


@dataclass(frozen=True)
class PaperExecutionPreflight:
    captured_at: datetime
    session: SessionEvidence
    qualified_legs: tuple[QualifiedContractEvidence, ...]
    bag_exchange: str
    bag_market_rule: MarketRuleEvidence
    combo_bid: Decimal | None
    combo_ask: Decimal | None
    bag_quote_fresh: bool
    required_market_data_live: bool
    signed_bag_price_convention_verified: bool
    market_window: MarketWindow
    trading_hours: str
    liquid_hours: str
    time_zone_id: str
    us_options_permission: bool
    short_option_permission: bool
    available_funds_eur: Decimal | None
    excess_liquidity_eur: Decimal | None
    buying_power_eur: Decimal | None
    account_currency: str
    what_if_status: BrokerWhatIfStatus
    what_if_margin_eur: Decimal | None
    what_if_commission_eur: Decimal | None
    broker_combo_guarantee_mode: str
    outgoing_api_messages_last_second: int
    active_market_data_subscriptions: int
    maximum_market_data_lines: int
    pacing_warning_active: bool
    retry_not_before: datetime | None


@dataclass(frozen=True)
class WireComboLeg:
    con_id: int
    ratio: int
    action: str
    exchange: str


@dataclass(frozen=True)
class WireBagContract:
    symbol: str
    security_type: str
    currency: str
    exchange: str
    combo_legs: tuple[WireComboLeg, ...]


@dataclass(frozen=True)
class WireLimitOrder:
    action: str
    order_type: str
    total_quantity: int
    limit_price: Decimal
    time_in_force: str
    order_ref: str
    account: str
    transmit: bool
    what_if: bool
    outside_regular_trading_hours: bool
    non_guaranteed: bool
    bypass_order_precautions: bool
    override_percentage_constraints: bool


@dataclass(frozen=True)
class WhatIfEvidence:
    status: BrokerWhatIfStatus
    margin_eur: Decimal | None
    commission_eur: Decimal | None
    raw_evidence_hash: str


class PersistentPaperTransport(Protocol):
    """Long-lived transport owned by one stable API client ID."""

    def session_evidence(self) -> SessionEvidence: ...

    def preflight(self, command: PaperCommand) -> PaperExecutionPreflight: ...

    def place_order(
        self,
        order_id: int,
        contract: WireBagContract,
        order: WireLimitOrder,
    ) -> None: ...

    def what_if(
        self,
        order_id: int,
        contract: WireBagContract,
        order: WireLimitOrder,
    ) -> WhatIfEvidence: ...

    def recover(
        self,
        unresolved: Sequence[RecoveryIdentity],
    ) -> Sequence[tuple[str, GatewayEvent]]: ...


class MonotonicOrderIdAllocator:
    def __init__(self) -> None:
        self._next: int | None = None
        self._lock = threading.Lock()

    def allocate(self, broker_next_valid_id: int | None) -> int:
        if broker_next_valid_id is None or broker_next_valid_id <= 0:
            raise PaperGatewayBlocked("NEXT_VALID_ID_NOT_ESTABLISHED")
        with self._lock:
            self._next = max(self._next or broker_next_valid_id, broker_next_valid_id)
            allocated = self._next
            self._next += 1
            return allocated


def _require_timezone(value: datetime, label: str) -> None:
    if value.tzinfo is None:
        raise PaperGatewayBlocked(f"{label}_TIMEZONE_REQUIRED")


def _matching_contract(leg: ComboLeg, qualified: QualifiedContractEvidence) -> bool:
    return (
        leg.con_id == qualified.con_id
        and leg.local_symbol == qualified.local_symbol
        and leg.trading_class == qualified.trading_class
        and leg.expiration == qualified.expiration
        and leg.strike == qualified.strike
        and leg.right == qualified.right
        and leg.multiplier == qualified.multiplier
        and leg.currency == qualified.currency
        and leg.exchange == qualified.exchange
    )


class IbkrPaperExecutionGateway:
    """Governed whole-BAG Paper adapter; disarmed unless explicitly composed."""

    def __init__(
        self,
        config: PaperGatewayConfig,
        transport: PersistentPaperTransport,
        *,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._transport = transport
        self._ids = MonotonicOrderIdAllocator()
        self._now = now or (lambda: datetime.now(UTC))

    def _session_blockers(self, evidence: SessionEvidence, *, execution: bool) -> list[str]:
        blockers: list[str] = []
        _require_timezone(evidence.observed_at, "SESSION_EVIDENCE")
        if not evidence.gateway_connected:
            blockers.append("GATEWAY_NOT_CONNECTED")
        if not evidence.ib_server_connected:
            blockers.append("IB_SERVER_NOT_CONNECTED")
        if not evidence.market_data_farm_connected:
            blockers.append("MARKET_DATA_FARM_NOT_CONNECTED")
        if evidence.accounts != (self._config.paper_account,):
            blockers.append("SINGLE_DU_ACCOUNT_NOT_PROVEN")
        if evidence.client_id != self._config.client_id:
            blockers.append("SESSION_CLIENT_ID_MISMATCH")
        if evidence.session_username_hash != self._config.session_username_hash:
            blockers.append("SESSION_USERNAME_MISMATCH")
        if evidence.maintain_and_resubmit_on_reconnect:
            blockers.append("PAPER_EXECUTION_BLOCKED_CONFIGURATION_DRIFT")
        if evidence.bypass_order_precautions or evidence.override_percentage_constraints:
            blockers.append("ORDER_PRECAUTION_BYPASS_FORBIDDEN")
        if not evidence.api_message_log_enabled or evidence.logging_level.casefold() != "detail":
            blockers.append("PAPER_API_DETAIL_LOG_ATTESTATION_REQUIRED")
        if execution and evidence.read_only_api:
            blockers.append("BROKER_READ_ONLY_API_STILL_ENABLED")
        if execution and (evidence.next_valid_id is None or evidence.next_valid_id <= 0):
            blockers.append("NEXT_VALID_ID_NOT_ESTABLISHED")
        return blockers

    def health(self, open_intent_count: int) -> GatewayHealth:
        evidence = self._transport.session_evidence()
        blockers = self._session_blockers(evidence, execution=True)
        if not self._config.armed_for_governed_paper_entry:
            blockers.append("PAPER_GATEWAY_DISARMED")
        healthy = not blockers
        return GatewayHealth(
            gateway_connected=healthy,
            paper_account_verified=healthy,
            open_intent_count=open_intent_count,
            detail={
                "adapter": "IBKR_PAPER_EXECUTION_DISARMED"
                if not self._config.armed_for_governed_paper_entry
                else "IBKR_PAPER_EXECUTION",
                "execution_environment": "IBKR_PAPER_SIMULATOR",
                "live_mode_available": False,
                "blockers": blockers,
            },
        )

    def recover(
        self,
        unresolved: Sequence[RecoveryIdentity],
    ) -> Sequence[tuple[str, GatewayEvent]]:
        if not unresolved:
            return []
        return self._transport.recover(unresolved)

    def _validate_entry(
        self,
        command: PaperCommand,
        evidence: PaperExecutionPreflight,
        *,
        require_what_if_result: bool = True,
    ) -> PaperEntryAuthorization:
        if not self._config.armed_for_governed_paper_entry:
            raise PaperGatewayBlocked("PAPER_GATEWAY_DISARMED")
        if command.intent_type != "PAPER_ENTRY" or not command.transmit:
            raise PaperGatewayBlocked("GOVERNED_PAPER_ENTRY_REQUIRED")
        authorization = command.entry_authorization
        if authorization is None:
            raise PaperGatewayBlocked("ENTRY_AUTHORIZATION_REQUIRED")
        now = self._now()
        _require_timezone(now, "CURRENT_TIME")
        _require_timezone(evidence.captured_at, "PREFLIGHT")
        if evidence.retry_not_before is not None:
            _require_timezone(evidence.retry_not_before, "PACING_RETRY")
        if authorization.ticket_created_at > now:
            raise PaperGatewayBlocked("EXECUTION_REVALIDATION_TICKET_FROM_FUTURE")
        if now > authorization.ticket_expires_at:
            raise PaperGatewayBlocked("EXECUTION_REVALIDATION_TICKET_STALE")
        preflight_age = (now - evidence.captured_at).total_seconds()
        if preflight_age < 0:
            raise PaperGatewayBlocked("PREFLIGHT_EVIDENCE_FROM_FUTURE")
        if preflight_age > self._config.maximum_preflight_age_seconds:
            raise PaperGatewayBlocked("PREFLIGHT_EVIDENCE_STALE")
        if authorization.kill_switch_version != self._config.expected_kill_switch_version:
            raise PaperGatewayBlocked("ACTIVE_KILL_SWITCH_VERSION_MISMATCH")
        if authorization.current_git_commit != self._config.expected_git_commit:
            raise PaperGatewayBlocked("EXECUTION_GIT_VERSION_MISMATCH")
        if authorization.current_config_hash != self._config.expected_config_hash:
            raise PaperGatewayBlocked("EXECUTION_CONFIG_VERSION_MISMATCH")
        blockers = self._session_blockers(evidence.session, execution=True)
        if blockers:
            raise PaperGatewayBlocked(blockers[0])
        if evidence.captured_at < authorization.ticket_created_at:
            raise PaperGatewayBlocked("PREFLIGHT_PREDATES_REVALIDATION_TICKET")
        if evidence.outgoing_api_messages_last_second < 0:
            raise PaperGatewayBlocked("INVALID_PACING_EVIDENCE")
        if (
            evidence.active_market_data_subscriptions < 0
            or evidence.maximum_market_data_lines <= 0
        ):
            raise PaperGatewayBlocked("INVALID_MARKET_DATA_LINE_EVIDENCE")
        if evidence.active_market_data_subscriptions > evidence.maximum_market_data_lines:
            raise PaperGatewayBlocked("MAX_TICKERS_REACHED")
        if evidence.pacing_warning_active:
            raise PaperGatewayBlocked("MESSAGE_RATE_EXCEEDED")
        if evidence.retry_not_before is not None and now < evidence.retry_not_before:
            raise PaperGatewayBlocked("PACING_BACKOFF_ACTIVE")
        if command.ticker != "TTWO":
            raise PaperGatewayBlocked("PAPER_ENTRY_TTWO_ONLY")
        if authorization.combo_submission_mode != "WHOLE_BAG":
            raise PaperGatewayBlocked("WHOLE_BAG_REQUIRED")
        if authorization.broker_combo_guarantee_mode != "GUARANTEED":
            raise PaperGatewayBlocked("BLOCKED_NON_GUARANTEED_COMBO")
        if evidence.broker_combo_guarantee_mode != "GUARANTEED":
            raise PaperGatewayBlocked("BLOCKED_NON_GUARANTEED_COMBO")
        if not evidence.required_market_data_live:
            raise PaperGatewayBlocked("MARKET_DATA_NOT_LIVE")
        if not evidence.bag_quote_fresh or evidence.combo_bid is None or evidence.combo_ask is None:
            raise PaperGatewayBlocked("BAG_QUOTE_MISSING_OR_STALE")
        if evidence.combo_bid > evidence.combo_ask:
            raise PaperGatewayBlocked("INVALID_BAG_QUOTE")
        if not evidence.signed_bag_price_convention_verified:
            raise PaperGatewayBlocked("UNVERIFIED_SIGNED_BAG_PRICE_CONVENTION")
        if evidence.market_window not in {MarketWindow.MARKET_OPEN, MarketWindow.LIQUID_HOURS}:
            raise PaperGatewayBlocked("OUTSIDE_GOVERNED_LIQUID_MARKET_WINDOW")
        if not evidence.trading_hours or not evidence.liquid_hours or not evidence.time_zone_id:
            raise PaperGatewayBlocked("CONTRACT_HOURS_EVIDENCE_INCOMPLETE")
        if len(evidence.qualified_legs) != len(command.legs):
            raise PaperGatewayBlocked("INCOMPLETE_CONTRACT_QUALIFICATION")
        for leg in command.legs:
            matches = [item for item in evidence.qualified_legs if item.con_id == leg.con_id]
            if len(matches) != 1 or not _matching_contract(leg, matches[0]):
                raise PaperGatewayBlocked("AMBIGUOUS_OR_CHANGED_CONTRACT_IDENTITY")
            qualified = matches[0]
            if qualified.identity_match_count != 1:
                raise PaperGatewayBlocked("AMBIGUOUS_CONTRACT_IDENTITY")
            if qualified.adjusted_or_non_standard:
                raise PaperGatewayBlocked("ADJUSTED_CONTRACT_REQUIRES_REVIEW")
            if "LMT" not in qualified.supported_order_types:
                raise PaperGatewayBlocked("LIMIT_ORDER_NOT_SUPPORTED")
            if qualified.exchange not in qualified.valid_exchanges:
                raise PaperGatewayBlocked("INVALID_CONTRACT_EXCHANGE")
            if evidence.bag_market_rule.market_rule_id not in qualified.market_rule_ids:
                raise PaperGatewayBlocked("MARKET_RULE_NOT_PROVEN_FOR_CONTRACT")
        currencies = {leg.currency for leg in command.legs}
        if currencies != {command.native_currency}:
            raise PaperGatewayBlocked("INCOMPATIBLE_COMBO_CURRENCIES")
        if not evidence.bag_market_rule.price_is_valid(authorization.proposed_limit):
            raise PaperGatewayBlocked("PRICE_DOES_NOT_CONFORM_TO_MINIMUM_VARIATION")
        expected_increment = evidence.bag_market_rule.increment_at(authorization.proposed_limit)
        if expected_increment != authorization.valid_tick:
            raise PaperGatewayBlocked("REVALIDATION_TICK_EVIDENCE_MISMATCH")
        if not evidence.bag_market_rule.quantity_is_valid(command.requested_quantity):
            raise PaperGatewayBlocked("SIZE_DOES_NOT_CONFORM_TO_MARKET_RULE")
        if not evidence.us_options_permission:
            raise PaperGatewayBlocked("SECURITY_NOT_ALLOWED_FOR_ACCOUNT")
        if any(leg.action == "SELL_TO_OPEN" for leg in command.legs):
            if not evidence.short_option_permission:
                raise PaperGatewayBlocked("SHORT_OPTION_PERMISSION_NOT_PROVEN")
        if authorization.capital_required_eur > GLOBAL_PAPER_HARD_CEILING_EUR:
            raise PaperGatewayBlocked("GLOBAL_PAPER_HARD_CEILING_EXCEEDED")
        if authorization.maximum_loss_eur > GLOBAL_PAPER_HARD_CEILING_EUR:
            raise PaperGatewayBlocked("MAXIMUM_LOSS_HARD_CEILING_EXCEEDED")
        if evidence.available_funds_eur is None:
            raise PaperGatewayBlocked("AVAILABLE_FUNDS_NOT_PROVEN")
        if evidence.available_funds_eur < authorization.capital_required_eur:
            raise PaperGatewayBlocked("INSUFFICIENT_AVAILABLE_FUNDS")
        if require_what_if_result:
            if evidence.what_if_status is BrokerWhatIfStatus.BROKER_WHAT_IF_CONFIRMED:
                if evidence.what_if_margin_eur is None or evidence.what_if_commission_eur is None:
                    raise PaperGatewayBlocked("BROKER_WHAT_IF_INCOMPLETE")
                if evidence.what_if_margin_eur > evidence.available_funds_eur:
                    raise PaperGatewayBlocked("INSUFFICIENT_BROKER_WHAT_IF_FUNDS")
            elif not (
                evidence.what_if_status is BrokerWhatIfStatus.BROKER_WHAT_IF_UNSUPPORTED
                and authorization.what_if_fallback_authorized
            ):
                raise PaperGatewayBlocked(evidence.what_if_status.value)
        return authorization

    def _wire_shape(
        self,
        command: PaperCommand,
        authorization: PaperEntryAuthorization,
        bag_exchange: str,
        *,
        what_if: bool,
    ) -> tuple[WireBagContract, WireLimitOrder]:
        contract = WireBagContract(
            symbol="TTWO",
            security_type="BAG",
            currency=command.native_currency,
            exchange=bag_exchange,
            combo_legs=tuple(
                WireComboLeg(
                    con_id=leg.con_id,
                    ratio=leg.ratio,
                    action=leg.wire_action,
                    exchange=leg.exchange or "SMART",
                )
                for leg in command.legs
            ),
        )
        order = WireLimitOrder(
            action="BUY" if authorization.cash_flow_type == "DEBIT" else "SELL",
            order_type="LMT",
            total_quantity=command.requested_quantity,
            limit_price=authorization.proposed_limit,
            time_in_force="DAY",
            order_ref=command.order_ref,
            account=self._config.paper_account,
            transmit=not what_if,
            what_if=what_if,
            outside_regular_trading_hours=False,
            non_guaranteed=False,
            bypass_order_precautions=False,
            override_percentage_constraints=False,
        )
        return contract, order

    def execute_bounded_combo(self, command: PaperCommand) -> Sequence[GatewayEvent]:
        evidence = self._transport.preflight(command)
        authorization = self._validate_entry(command, evidence)
        order_id = self._ids.allocate(evidence.session.next_valid_id)
        contract, order = self._wire_shape(
            command,
            authorization,
            evidence.bag_exchange,
            what_if=False,
        )
        attempted_at = self._now()
        event_hash = hashlib.sha256(
            f"{command.intent_id}:{order_id}:{authorization.revalidation_ticket_hash}".encode()
        ).hexdigest()
        self._transport.place_order(order_id, contract, order)
        return [
            GatewayEvent(
                broker_event_key=f"paper-submission-attempt:{event_hash}",
                event_type="SUBMISSION_ATTEMPTED",
                occurred_at=attempted_at,
                broker_order_id=order_id,
                detail={
                    "canonical_execution_status": "BROKER_SUBMISSION_ATTEMPTED",
                    "execution_environment": "IBKR_PAPER_SIMULATOR",
                    "order_ref": command.order_ref,
                    "client_id": self._config.client_id,
                    "combo_submission_mode": "WHOLE_BAG",
                    "broker_combo_guarantee_mode": "GUARANTEED",
                    "revalidation_ticket_id": authorization.revalidation_ticket_id,
                    "revalidation_ticket_hash": authorization.revalidation_ticket_hash,
                    "structure_hash": authorization.structure_hash,
                    "current_market_snapshot_hash": authorization.current_market_snapshot_hash,
                    "proposed_limit": float(authorization.proposed_limit),
                    "valid_tick": float(authorization.valid_tick),
                    "capital_required_eur": float(authorization.capital_required_eur),
                    "maximum_loss_eur": float(authorization.maximum_loss_eur),
                    "expected_commissions_eur": float(
                        authorization.expected_commissions_eur
                    ),
                    "cash_flow_type": authorization.cash_flow_type,
                    "combo_bid": (
                        float(evidence.combo_bid) if evidence.combo_bid is not None else None
                    ),
                    "combo_ask": (
                        float(evidence.combo_ask) if evidence.combo_ask is not None else None
                    ),
                    "preflight_captured_at": evidence.captured_at.isoformat(),
                    "what_if_status": evidence.what_if_status.value,
                    "transmitted_to_broker": None,
                    "raw_evidence_hash": event_hash,
                },
            )
        ]

    def request_what_if(self, command: PaperCommand) -> WhatIfEvidence:
        evidence = self._transport.preflight(command)
        authorization = self._validate_entry(
            command,
            evidence,
            require_what_if_result=False,
        )
        order_id = self._ids.allocate(evidence.session.next_valid_id)
        contract, order = self._wire_shape(
            command,
            authorization,
            evidence.bag_exchange,
            what_if=True,
        )
        if order.transmit or not order.what_if:
            raise AssertionError("what-if must remain non-routed")
        return self._transport.what_if(order_id, contract, order)
