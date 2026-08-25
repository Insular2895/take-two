"""Single-consumer polling runtime with durable recovery."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from time import monotonic
from typing import Any

from .cloudflare_client import SignedControlPlaneClient
from .contracts import GatewayEvent
from .gateway import PaperGateway
from .journal import BridgeJournal


class BridgeRuntime:
    def __init__(
        self,
        client: SignedControlPlaneClient,
        journal: BridgeJournal,
        gateway: PaperGateway,
    ) -> None:
        self._client = client
        self._journal = journal
        self._gateway = gateway
        self._last_heartbeat_at = float("-inf")
        self._last_health_signature: tuple[bool, bool] | None = None

    def flush_outbox(self) -> None:
        for intent_id, event_key, payload in self._journal.unposted_events():
            event = GatewayEvent(
                broker_event_key=str(payload["broker_event_key"]),
                event_type=str(payload["event_type"]),
                occurred_at=datetime.fromisoformat(
                    str(payload["occurred_at"]).replace("Z", "+00:00")
                ),
                broker_order_id=payload.get("broker_order_id"),
                broker_perm_id=payload.get("broker_perm_id"),
                broker_exec_id=payload.get("broker_exec_id"),
                detail=payload.get("detail") if isinstance(payload.get("detail"), Mapping) else {},
            )
            self._client.post_event(intent_id, event)
            self._journal.mark_event_posted(event_key)

    def recover(self) -> None:
        self.flush_outbox()
        for intent_id, event in self._gateway.recover(self._journal.unresolved_order_refs()):
            self._journal.remember_event(intent_id, event)
        self.flush_outbox()

    def tick(self) -> bool:
        unresolved = self._journal.unresolved_order_refs()
        health = self._gateway.health(len(unresolved))
        health_signature = (health.gateway_connected, health.paper_account_verified)
        now = monotonic()
        if now - self._last_heartbeat_at >= 30 or health_signature != self._last_health_signature:
            self._client.heartbeat(health)
            self._last_heartbeat_at = now
            self._last_health_signature = health_signature
        self.flush_outbox()
        if not health.gateway_connected or not health.paper_account_verified:
            return False
        if unresolved:
            for intent_id, event in self._gateway.recover(unresolved):
                self._journal.remember_event(intent_id, event)
            self.flush_outbox()
            if self._journal.unresolved_order_refs():
                return False
        claim = self._client.claim()
        if claim is None:
            return False
        raw_command: dict[str, Any] = {
            "intent_id": claim.command.intent_id,
            "intent_type": claim.command.intent_type,
            "position_id": claim.command.position_id,
            "preview_id": claim.command.preview_id,
            "order_ref": claim.command.order_ref,
            "ticker": claim.command.ticker,
            "native_currency": claim.command.native_currency,
            "requested_quantity": claim.command.requested_quantity,
            "legs": [vars(leg) for leg in claim.command.legs],
            "maximum_exit_slippage_policy": str(claim.command.maximum_exit_slippage_policy),
            "pricing_policy": claim.command.pricing_policy,
            "mode": "PAPER",
            "account_guard": {"required_prefix": "DU", "live_accounts_forbidden": True},
        }
        self._journal.remember_claim(claim.command, raw_command)
        self._journal.mark_dispatch_started(claim.command.intent_id)
        for event in self._gateway.execute_bounded_combo(claim.command):
            self._journal.remember_event(claim.command.intent_id, event)
        self.flush_outbox()
        return True
