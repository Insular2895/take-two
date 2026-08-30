from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from ttwo_ibkr_bridge.contracts import (
    ClaimedIntent,
    ContractError,
    GatewayEvent,
    GatewayHealth,
    PaperCommand,
)
from ttwo_ibkr_bridge.journal import BridgeJournal, JournalConflict
from ttwo_ibkr_bridge.runtime import BridgeRuntime


def command_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "intent_id": "broker-intent_123",
        "intent_type": "MANUAL_CLOSE",
        "mode": "PAPER",
        "account_guard": {"required_prefix": "DU", "live_accounts_forbidden": True},
        "position_id": "position-1",
        "preview_id": "preview-1",
        "order_ref": "TTWO-P-123",
        "ticker": "TTWO",
        "native_currency": "USD",
        "requested_quantity": 2,
        "legs": [
            {"con_id": 900001, "ratio": 1, "action": "SELL_TO_CLOSE"},
            {"con_id": 900002, "ratio": 1, "action": "BUY_TO_CLOSE"},
        ],
        "maximum_exit_slippage_policy": 25,
        "pricing_policy": "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
    }


def test_command_accepts_only_paper_close_combos() -> None:
    command = PaperCommand.from_mapping(command_payload())
    assert command.ticker == "TTWO"
    assert [leg.action for leg in command.legs] == ["SELL_TO_CLOSE", "BUY_TO_CLOSE"]

    live = command_payload()
    live["mode"] = "LIVE"
    with pytest.raises(ContractError, match="only PAPER"):
        PaperCommand.from_mapping(live)

    opening = command_payload()
    opening["legs"][0]["action"] = "BUY_TO_OPEN"
    with pytest.raises(ContractError, match="never open"):
        PaperCommand.from_mapping(opening)


def test_journal_detects_mutated_replays(tmp_path: Path) -> None:
    journal = BridgeJournal(tmp_path / "bridge.sqlite3")
    raw = command_payload()
    command = PaperCommand.from_mapping(raw)
    journal.remember_claim(command, raw)
    replay = command_payload()
    replay["requested_quantity"] = 1
    with pytest.raises(JournalConflict, match="immutable"):
        journal.remember_claim(command, replay)
    journal.close()


class FakeClient:
    def __init__(self, claim: ClaimedIntent | None) -> None:
        self.next_claim = claim
        self.heartbeats: list[GatewayHealth] = []
        self.events: list[tuple[str, GatewayEvent]] = []

    def heartbeat(self, health: GatewayHealth) -> None:
        self.heartbeats.append(health)

    def claim(self) -> ClaimedIntent | None:
        claim, self.next_claim = self.next_claim, None
        return claim

    def post_event(self, intent_id: str, event: GatewayEvent) -> None:
        self.events.append((intent_id, event))


class FakeGateway:
    def __init__(self, healthy: bool) -> None:
        self.healthy = healthy
        self.executed: list[PaperCommand] = []

    def health(self, open_intent_count: int) -> GatewayHealth:
        return GatewayHealth(self.healthy, self.healthy, open_intent_count, {"adapter": "FAKE"})

    def recover(self, unresolved: list[tuple[str, str]]) -> list[tuple[str, GatewayEvent]]:
        return []

    def execute_bounded_combo(self, command: PaperCommand) -> list[GatewayEvent]:
        self.executed.append(command)
        return [
            GatewayEvent(
                broker_event_key="test-ack-123456",
                event_type="BROKER_ACKNOWLEDGED",
                occurred_at=datetime.now(UTC),
                broker_order_id=42,
                broker_perm_id=84,
            )
        ]


def claimed_intent() -> ClaimedIntent:
    return ClaimedIntent(
        command=PaperCommand.from_mapping(command_payload()),
        claim_expires_at=datetime.now(UTC) + timedelta(seconds=45),
    )


def test_runtime_never_claims_while_gateway_is_unhealthy(tmp_path: Path) -> None:
    client = FakeClient(claimed_intent())
    gateway = FakeGateway(healthy=False)
    journal = BridgeJournal(tmp_path / "bridge.sqlite3")
    runtime = BridgeRuntime(client, journal, gateway)  # type: ignore[arg-type]
    assert runtime.tick() is False
    assert client.next_claim is not None
    assert gateway.executed == []
    journal.close()


def test_runtime_journals_before_execution_and_posts_events(tmp_path: Path) -> None:
    client = FakeClient(claimed_intent())
    gateway = FakeGateway(healthy=True)
    journal = BridgeJournal(tmp_path / "bridge.sqlite3")
    runtime = BridgeRuntime(client, journal, gateway)  # type: ignore[arg-type]
    assert runtime.tick() is True
    assert [command.intent_id for command in gateway.executed] == ["broker-intent_123"]
    assert [(intent_id, event.event_type) for intent_id, event in client.events] == [
        ("broker-intent_123", "BROKER_ACKNOWLEDGED")
    ]
    assert journal.unposted_events() == []
    assert journal.unresolved_order_refs() == [("broker-intent_123", "TTWO-P-123")]
    journal.close()
