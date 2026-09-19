"""One-way read-only telemetry runtime."""

from __future__ import annotations

from typing import Protocol

from .ibkr_readonly import PortfolioTelemetry


class TelemetryAdapter(Protocol):
    def snapshot(self) -> PortfolioTelemetry: ...


class TelemetryPublisher(Protocol):
    def publish(self, payload: dict[str, object]) -> None: ...


class ReadOnlyTelemetryRuntime:
    def __init__(self, adapter: TelemetryAdapter, publisher: TelemetryPublisher) -> None:
        self._adapter = adapter
        self._publisher = publisher

    def tick(self) -> int:
        telemetry = self._adapter.snapshot()
        payload = telemetry.as_payload()
        self._publisher.publish(payload)
        return len(telemetry.positions)
