"""Bridge process entrypoint."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

from .cloudflare_client import ControlPlaneConfig, SignedControlPlaneClient
from .gateway import DisabledGateway
from .journal import BridgeJournal
from .runtime import BridgeRuntime


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    config = ControlPlaneConfig(
        base_url=_required("TTWO_CONTROL_URL"),
        bridge_id=_required("TTWO_BRIDGE_ID"),
        shared_secret=_required("TTWO_BRIDGE_SHARED_SECRET"),
        access_client_id=_required("CF_ACCESS_CLIENT_ID"),
        access_client_secret=_required("CF_ACCESS_CLIENT_SECRET"),
    )
    journal_path = os.environ.get("TTWO_BRIDGE_JOURNAL", "/var/lib/ttwo-bridge/journal.sqlite3")
    journal = BridgeJournal(Path(journal_path))
    runtime = BridgeRuntime(SignedControlPlaneClient(config), journal, DisabledGateway())
    stopping = False

    def stop(_signal: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    runtime.recover()
    interval = max(float(os.environ.get("TTWO_BRIDGE_POLL_SECONDS", "5")), 2.0)
    try:
        while not stopping:
            try:
                runtime.tick()
            except Exception as error:
                # Never print request headers, bodies, accounts, or secret-bearing environment.
                print(
                    f"bridge cycle failed safely: {type(error).__name__}",
                    file=sys.stderr,
                    flush=True,
                )
            time.sleep(interval)
    finally:
        journal.close()
