"""Broker adapter boundary. The production adapter is deliberately not wired yet."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from .contracts import GatewayEvent, GatewayHealth, PaperCommand


class PaperGateway(Protocol):
    def health(self, open_intent_count: int) -> GatewayHealth: ...

    def recover(
        self, unresolved: Sequence[tuple[str, str]]
    ) -> Sequence[tuple[str, GatewayEvent]]: ...

    def execute_bounded_combo(self, command: PaperCommand) -> Sequence[GatewayEvent]: ...


class DisabledGateway:
    """Fail-closed adapter used until the official IBKR API is installed and paper-tested."""

    def health(self, open_intent_count: int) -> GatewayHealth:
        return GatewayHealth(
            gateway_connected=False,
            paper_account_verified=False,
            open_intent_count=open_intent_count,
            detail={"adapter": "DISABLED", "live_mode_available": False},
        )

    def recover(self, unresolved: Sequence[tuple[str, str]]) -> Sequence[tuple[str, GatewayEvent]]:
        return []

    def execute_bounded_combo(self, command: PaperCommand) -> Sequence[GatewayEvent]:
        raise RuntimeError("IBKR_PAPER_ADAPTER_NOT_CONFIGURED")
