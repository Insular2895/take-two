from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from ttwo_ibkr_bridge.contracts import GatewayEvent, PaperCommand, RecoveryIdentity
from ttwo_ibkr_bridge.paper_gateway import (
    BrokerWhatIfStatus,
    IbkrPaperExecutionGateway,
    MarketRuleEvidence,
    MarketWindow,
    PaperExecutionPreflight,
    PaperGatewayBlocked,
    PaperGatewayConfig,
    PriceIncrementBand,
    QualifiedContractEvidence,
    SessionEvidence,
    WhatIfEvidence,
    WireBagContract,
    WireLimitOrder,
)

NOW = datetime(2026, 9, 19, 14, 30, tzinfo=UTC)
SHA = "a" * 64


def entry_payload() -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "intent_id": "paper-entry_123",
        "intent_type": "PAPER_ENTRY",
        "mode": "PAPER",
        "account_guard": {"required_prefix": "DU", "live_accounts_forbidden": True},
        "position_id": None,
        "preview_id": "paper-entry-preview_123",
        "order_ref": "TTWO-PE-123",
        "ticker": "TTWO",
        "native_currency": "USD",
        "requested_quantity": 1,
        "legs": [
            {
                "con_id": 900001,
                "ratio": 1,
                "action": "BUY_TO_OPEN",
                "wire_action": "BUY",
                "local_symbol": "TTWO  270115C00250000",
                "trading_class": "TTWO",
                "expiration": "20270115",
                "strike": "250",
                "right": "C",
                "multiplier": 100,
                "currency": "USD",
                "exchange": "SMART",
            }
        ],
        "maximum_exit_slippage_policy": 0,
        "pricing_policy": "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
        "time_in_force": "DAY",
        "transmit": True,
        "entry_authorization": {
            "candidate_approved": True,
            "dossier_current": True,
            "bag_semantics_verified": True,
            "original_analysis_id": "analysis-1",
            "candidate_id": "candidate-1",
            "selection_id": "selection-1",
            "dossier_id": "dossier-1",
            "revalidation_ticket_id": "revalidation-1",
            "revalidation_ticket_hash": SHA,
            "ticket_created_at": NOW.isoformat(),
            "ticket_expires_at": (NOW + timedelta(minutes=2)).isoformat(),
            "confirmation_id": "confirmation-1",
            "confirmation_hash": "b" * 64,
            "structure_type": "LONG_CALL",
            "structure_hash": "c" * 64,
            "current_market_snapshot_hash": "d" * 64,
            "current_git_commit": "f2bb94d",
            "current_config_hash": "e" * 64,
            "proposed_limit": "5.30",
            "valid_tick": "0.05",
            "capital_required_eur": "530",
            "maximum_loss_eur": "530",
            "expected_commissions_eur": "2",
            "cash_flow_type": "DEBIT",
            "combo_submission_mode": "WHOLE_BAG",
            "broker_combo_guarantee_mode": "GUARANTEED",
            "kill_switch_version": "kill-v1",
            "what_if_fallback_authorized": False,
        },
    }


def session(**updates: Any) -> SessionEvidence:
    values: dict[str, Any] = {
        "gateway_connected": True,
        "ib_server_connected": True,
        "market_data_farm_connected": True,
        "accounts": ("DU123456",),
        "client_id": 17,
        "session_username_hash": SHA,
        "next_valid_id": 100,
        "read_only_api": False,
        "maintain_and_resubmit_on_reconnect": False,
        "bypass_order_precautions": False,
        "override_percentage_constraints": False,
        "api_message_log_enabled": True,
        "logging_level": "Detail",
        "observed_at": NOW,
    }
    values.update(updates)
    return SessionEvidence(**values)


def preflight(**updates: Any) -> PaperExecutionPreflight:
    values: dict[str, Any] = {
        "captured_at": NOW + timedelta(seconds=1),
        "session": session(),
        "qualified_legs": (
            QualifiedContractEvidence(
                con_id=900001,
                local_symbol="TTWO  270115C00250000",
                trading_class="TTWO",
                expiration="20270115",
                strike=Decimal("250"),
                right="C",
                multiplier=100,
                currency="USD",
                exchange="SMART",
                valid_exchanges=("SMART", "CBOE"),
                supported_order_types=("LMT",),
                real_expiration_date="20270115",
                identity_match_count=1,
                adjusted_or_non_standard=False,
                market_rule_ids=(26,),
            ),
        ),
        "bag_exchange": "SMART",
        "bag_market_rule": MarketRuleEvidence(
            market_rule_id=26,
            price_increments=(PriceIncrementBand(Decimal("0"), Decimal("0.05")),),
            min_size=Decimal("1"),
            size_increment=Decimal("1"),
            suggested_size_increment=Decimal("1"),
        ),
        "combo_bid": Decimal("5.10"),
        "combo_ask": Decimal("5.40"),
        "bag_quote_fresh": True,
        "required_market_data_live": True,
        "signed_bag_price_convention_verified": True,
        "market_window": MarketWindow.LIQUID_HOURS,
        "trading_hours": "20260919:0930-20260919:1600",
        "liquid_hours": "20260919:0930-20260919:1600",
        "time_zone_id": "US/Eastern",
        "us_options_permission": True,
        "short_option_permission": True,
        "available_funds_eur": Decimal("5000"),
        "excess_liquidity_eur": Decimal("4000"),
        "buying_power_eur": Decimal("5000"),
        "account_currency": "EUR",
        "what_if_status": BrokerWhatIfStatus.BROKER_WHAT_IF_CONFIRMED,
        "what_if_margin_eur": Decimal("530"),
        "what_if_commission_eur": Decimal("2"),
        "broker_combo_guarantee_mode": "GUARANTEED",
        "outgoing_api_messages_last_second": 8,
        "active_market_data_subscriptions": 4,
        "maximum_market_data_lines": 100,
        "pacing_warning_active": False,
        "retry_not_before": None,
    }
    values.update(updates)
    return PaperExecutionPreflight(**values)


class FakeTransport:
    def __init__(self, evidence: PaperExecutionPreflight) -> None:
        self.evidence = evidence
        self.orders: list[tuple[int, WireBagContract, WireLimitOrder]] = []
        self.what_ifs: list[tuple[int, WireBagContract, WireLimitOrder]] = []

    def session_evidence(self) -> SessionEvidence:
        return self.evidence.session

    def preflight(self, _command: PaperCommand) -> PaperExecutionPreflight:
        return self.evidence

    def place_order(
        self,
        order_id: int,
        contract: WireBagContract,
        order: WireLimitOrder,
    ) -> None:
        self.orders.append((order_id, contract, order))

    def what_if(
        self,
        order_id: int,
        contract: WireBagContract,
        order: WireLimitOrder,
    ) -> WhatIfEvidence:
        self.what_ifs.append((order_id, contract, order))
        return WhatIfEvidence(
            status=BrokerWhatIfStatus.BROKER_WHAT_IF_CONFIRMED,
            margin_eur=Decimal("530"),
            commission_eur=Decimal("2"),
            raw_evidence_hash=SHA,
        )

    def recover(
        self,
        _unresolved: list[RecoveryIdentity],
    ) -> list[tuple[str, GatewayEvent]]:
        return []


def config(*, armed: bool = True, port: int = 7497) -> PaperGatewayConfig:
    return PaperGatewayConfig(
        host="127.0.0.1",
        port=port,
        client_id=17,
        paper_account="DU123456",
        session_username_hash=SHA,
        expected_kill_switch_version="kill-v1",
        expected_git_commit="f2bb94d",
        expected_config_hash="e" * 64,
        maximum_preflight_age_seconds=30,
        armed_for_governed_paper_entry=armed,
    )


def gateway(
    evidence: PaperExecutionPreflight | None = None,
    *,
    armed: bool = True,
) -> tuple[IbkrPaperExecutionGateway, FakeTransport]:
    transport = FakeTransport(evidence or preflight())
    return (
        IbkrPaperExecutionGateway(
            config(armed=armed),
            transport,
            now=lambda: NOW + timedelta(seconds=2),
        ),
        transport,
    )


def test_default_disarmed_and_non_paper_configuration_are_rejected() -> None:
    paper_gateway, transport = gateway(armed=False)
    assert paper_gateway.health(0).gateway_connected is False
    with pytest.raises(PaperGatewayBlocked, match="DISARMED"):
        paper_gateway.execute_bounded_combo(PaperCommand.from_mapping(entry_payload()))
    assert transport.orders == []

    with pytest.raises(ValueError, match="PORT"):
        config(port=7496)
    with pytest.raises(ValueError, match="DU"):
        replace(config(), paper_account="U123456")
    with pytest.raises(ValueError, match="LOOPBACK"):
        replace(config(), host="0.0.0.0")


def test_governed_entry_maps_application_open_actions_to_one_whole_bag() -> None:
    paper_gateway, transport = gateway()
    events = paper_gateway.execute_bounded_combo(PaperCommand.from_mapping(entry_payload()))
    assert len(transport.orders) == 1
    order_id, contract, order = transport.orders[0]
    assert order_id == 100
    assert contract.security_type == "BAG"
    assert contract.combo_legs[0].action == "BUY"
    assert order.action == "BUY"
    assert order.order_type == "LMT"
    assert order.transmit is True
    assert order.non_guaranteed is False
    assert order.bypass_order_precautions is False
    assert order.override_percentage_constraints is False
    assert events[0].event_type == "SUBMISSION_ATTEMPTED"
    assert events[0].detail is not None
    assert events[0].detail["execution_environment"] == "IBKR_PAPER_SIMULATOR"


def test_what_if_is_order_shaped_but_never_routed() -> None:
    paper_gateway, transport = gateway()
    transport.evidence = preflight(
        what_if_status=BrokerWhatIfStatus.BROKER_WHAT_IF_INCOMPLETE,
        what_if_margin_eur=None,
        what_if_commission_eur=None,
    )
    result = paper_gateway.request_what_if(PaperCommand.from_mapping(entry_payload()))
    assert result.status is BrokerWhatIfStatus.BROKER_WHAT_IF_CONFIRMED
    assert transport.orders == []
    assert len(transport.what_ifs) == 1
    assert transport.what_ifs[0][2].what_if is True
    assert transport.what_ifs[0][2].transmit is False


@pytest.mark.parametrize(
    ("evidence", "message"),
    [
        (preflight(session=session(read_only_api=True)), "READ_ONLY"),
        (preflight(session=session(maintain_and_resubmit_on_reconnect=True)), "CONFIGURATION"),
        (preflight(required_market_data_live=False), "MARKET_DATA_NOT_LIVE"),
        (preflight(bag_quote_fresh=False), "BAG_QUOTE"),
        (preflight(signed_bag_price_convention_verified=False), "SIGNED_BAG"),
        (preflight(market_window=MarketWindow.MARKET_CLOSED), "LIQUID_MARKET_WINDOW"),
        (preflight(us_options_permission=False), "SECURITY_NOT_ALLOWED"),
        (preflight(broker_combo_guarantee_mode="UNKNOWN"), "NON_GUARANTEED"),
        (preflight(pacing_warning_active=True), "MESSAGE_RATE_EXCEEDED"),
        (
            preflight(active_market_data_subscriptions=101),
            "MAX_TICKERS_REACHED",
        ),
        (
            preflight(retry_not_before=NOW + timedelta(seconds=10)),
            "PACING_BACKOFF_ACTIVE",
        ),
        (
            preflight(what_if_margin_eur=Decimal("5001")),
            "INSUFFICIENT_BROKER_WHAT_IF_FUNDS",
        ),
    ],
)
def test_preflight_failures_never_reach_order_primitive(
    evidence: PaperExecutionPreflight,
    message: str,
) -> None:
    paper_gateway, transport = gateway(evidence)
    with pytest.raises(PaperGatewayBlocked, match=message):
        paper_gateway.execute_bounded_combo(PaperCommand.from_mapping(entry_payload()))
    assert transport.orders == []


def test_invalid_tick_is_rejected_without_rounding() -> None:
    payload = entry_payload()
    payload["entry_authorization"]["proposed_limit"] = "5.32"
    paper_gateway, transport = gateway()
    with pytest.raises(PaperGatewayBlocked, match="MINIMUM_VARIATION"):
        paper_gateway.execute_bounded_combo(PaperCommand.from_mapping(payload))
    assert transport.orders == []


def test_entry_rejects_non_day_tif_and_exit_slippage_reuse() -> None:
    payload = entry_payload()
    payload["time_in_force"] = "IOC"
    with pytest.raises(ValueError, match="must use DAY"):
        PaperCommand.from_mapping(payload)

    payload = entry_payload()
    payload["maximum_exit_slippage_policy"] = 1
    with pytest.raises(ValueError, match="exit-slippage"):
        PaperCommand.from_mapping(payload)

    payload = entry_payload()
    payload["entry_authorization"]["what_if_fallback_authorized"] = True
    with pytest.raises(ValueError, match="fallback_policy_version"):
        PaperCommand.from_mapping(payload)


def test_execution_rejects_git_or_config_version_drift() -> None:
    command = PaperCommand.from_mapping(entry_payload())
    transport = FakeTransport(preflight())
    git_drift = IbkrPaperExecutionGateway(
        replace(config(), expected_git_commit="1234567"),
        transport,
        now=lambda: NOW + timedelta(seconds=2),
    )
    with pytest.raises(PaperGatewayBlocked, match="GIT_VERSION_MISMATCH"):
        git_drift.execute_bounded_combo(command)

    config_drift = IbkrPaperExecutionGateway(
        replace(config(), expected_config_hash="f" * 64),
        transport,
        now=lambda: NOW + timedelta(seconds=2),
    )
    with pytest.raises(PaperGatewayBlocked, match="CONFIG_VERSION_MISMATCH"):
        config_drift.execute_bounded_combo(command)


def test_order_ids_are_monotonic_from_next_valid_id() -> None:
    paper_gateway, transport = gateway()
    command = PaperCommand.from_mapping(entry_payload())
    paper_gateway.execute_bounded_combo(command)
    second = entry_payload()
    second["intent_id"] = "paper-entry_456"
    second["order_ref"] = "TTWO-PE-456"
    paper_gateway.execute_bounded_combo(PaperCommand.from_mapping(second))
    assert [item[0] for item in transport.orders] == [100, 101]


@pytest.mark.parametrize(
    ("architecture", "application_actions", "ratios", "cash_flow"),
    [
        ("LONG_CALL", ["BUY_TO_OPEN"], [1], "DEBIT"),
        ("LONG_PUT", ["BUY_TO_OPEN"], [1], "DEBIT"),
        ("BULL_CALL_SPREAD", ["BUY_TO_OPEN", "SELL_TO_OPEN"], [1, 1], "DEBIT"),
        ("BEAR_PUT_SPREAD", ["BUY_TO_OPEN", "SELL_TO_OPEN"], [1, 1], "DEBIT"),
        ("CALL_BUTTERFLY", ["BUY_TO_OPEN", "SELL_TO_OPEN", "BUY_TO_OPEN"], [1, 2, 1], "DEBIT"),
        ("PUT_BUTTERFLY", ["BUY_TO_OPEN", "SELL_TO_OPEN", "BUY_TO_OPEN"], [1, 2, 1], "DEBIT"),
        (
            "CALL_BROKEN_WING_BUTTERFLY",
            ["BUY_TO_OPEN", "SELL_TO_OPEN", "BUY_TO_OPEN"],
            [1, 2, 1],
            "CREDIT",
        ),
        ("STRADDLE", ["BUY_TO_OPEN", "BUY_TO_OPEN"], [1, 1], "DEBIT"),
        ("STRANGLE", ["BUY_TO_OPEN", "BUY_TO_OPEN"], [1, 1], "DEBIT"),
        (
            "IRON_CONDOR",
            ["BUY_TO_OPEN", "SELL_TO_OPEN", "SELL_TO_OPEN", "BUY_TO_OPEN"],
            [1, 1, 1, 1],
            "CREDIT",
        ),
        ("CALENDAR", ["SELL_TO_OPEN", "BUY_TO_OPEN"], [1, 1], "DEBIT"),
        ("DIAGONAL", ["SELL_TO_OPEN", "BUY_TO_OPEN"], [1, 1], "DEBIT"),
    ],
)
def test_supported_architectures_remain_one_whole_bag(
    architecture: str,
    application_actions: list[str],
    ratios: list[int],
    cash_flow: str,
) -> None:
    payload = entry_payload()
    base = payload["legs"][0]
    payload["legs"] = [
        {
            **base,
            "con_id": 900001 + index,
            "local_symbol": f"TTWO LEG {index + 1}",
            "action": action,
            "wire_action": "BUY" if action == "BUY_TO_OPEN" else "SELL",
            "ratio": ratio,
            "strike": str(250 + index * 5),
            "expiration": (
                "20270219"
                if architecture in {"CALENDAR", "DIAGONAL"} and index
                else "20270115"
            ),
        }
        for index, (action, ratio) in enumerate(zip(application_actions, ratios, strict=True))
    ]
    payload["entry_authorization"]["structure_type"] = architecture
    payload["entry_authorization"]["cash_flow_type"] = cash_flow
    command = PaperCommand.from_mapping(payload)
    paper_gateway, transport = gateway()
    assert command.entry_authorization is not None
    contract, order = paper_gateway._wire_shape(  # noqa: SLF001 - pure wire-shape contract test
        command,
        command.entry_authorization,
        "SMART",
        what_if=False,
    )
    assert transport.orders == []
    assert contract.security_type == "BAG"
    assert len(contract.combo_legs) == len(application_actions)
    assert [item.ratio for item in contract.combo_legs] == ratios
    assert [item.action for item in contract.combo_legs] == [
        "BUY" if item == "BUY_TO_OPEN" else "SELL" for item in application_actions
    ]
    assert order.total_quantity == 1
    assert order.action == ("BUY" if cash_flow == "DEBIT" else "SELL")
    assert command.entry_authorization.capital_required_eur == Decimal("530")
    assert command.entry_authorization.maximum_loss_eur == Decimal("530")
