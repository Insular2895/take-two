"""Redacted command-line probe for the read-only IBKR telemetry adapter."""

from __future__ import annotations

import json
import os
import sys

from .ibkr_readonly import IbkrReadOnlyAdapter, IbkrReadOnlyConfig, ReadOnlyAdapterError


def main() -> int:
    try:
        config = IbkrReadOnlyConfig(
            host=os.environ.get("TTWO_IBKR_HOST", "127.0.0.1"),
            port=int(os.environ.get("TTWO_IBKR_PORT", "4002")),
            client_id=int(os.environ.get("TTWO_IBKR_READONLY_CLIENT_ID", "901")),
            symbol="TTWO",
            timeout_seconds=float(os.environ.get("TTWO_IBKR_TIMEOUT_SECONDS", "15")),
        )
        payload = IbkrReadOnlyAdapter(config).snapshot().as_payload()
    except (ReadOnlyAdapterError, ValueError) as error:
        print(f"READ_ONLY_SNAPSHOT_FAILED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
