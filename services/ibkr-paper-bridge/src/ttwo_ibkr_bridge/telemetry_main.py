"""Persistent read-only IBKR telemetry entrypoint."""

from __future__ import annotations

import os
import signal
import sys
import threading

from .ibkr_readonly import IbkrReadOnlyAdapter, IbkrReadOnlyConfig
from .telemetry_client import SignedTelemetryClient, TelemetryControlPlaneConfig
from .telemetry_runtime import ReadOnlyTelemetryRuntime


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    interval = float(os.environ.get("TTWO_TELEMETRY_INTERVAL_SECONDS", "30"))
    if interval < 30 or interval > 300:
        raise RuntimeError("TTWO_TELEMETRY_INTERVAL_SECONDS must be between 30 and 300")
    adapter = IbkrReadOnlyAdapter(
        IbkrReadOnlyConfig(
            host=os.environ.get("TTWO_IBKR_HOST", "127.0.0.1"),
            port=int(os.environ.get("TTWO_IBKR_PORT", "4002")),
            client_id=int(os.environ.get("TTWO_IBKR_READONLY_CLIENT_ID", "901")),
            symbol="TTWO",
            timeout_seconds=float(os.environ.get("TTWO_IBKR_TIMEOUT_SECONDS", "15")),
        )
    )
    publisher = SignedTelemetryClient(
        TelemetryControlPlaneConfig(
            base_url=_required("TTWO_CONTROL_URL"),
            telemetry_id=_required("TTWO_TELEMETRY_ID"),
            shared_secret=_required("TTWO_TELEMETRY_SHARED_SECRET"),
            access_client_id=_required("CF_ACCESS_CLIENT_ID"),
            access_client_secret=_required("CF_ACCESS_CLIENT_SECRET"),
        )
    )
    runtime = ReadOnlyTelemetryRuntime(adapter, publisher)
    stopping = threading.Event()

    def stop(_signal: int, _frame: object) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping.is_set():
        try:
            count = runtime.tick()
            print(f"read-only telemetry published: positions={count}", flush=True)
        except Exception as error:
            # Never log payloads, accounts, URLs, headers, environment, or exception detail.
            print(
                f"read-only telemetry cycle failed safely: {type(error).__name__}",
                file=sys.stderr,
                flush=True,
            )
        stopping.wait(interval)
