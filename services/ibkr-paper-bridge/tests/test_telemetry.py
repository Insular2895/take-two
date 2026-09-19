from __future__ import annotations

import hashlib
import hmac
import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request

import pytest

from ttwo_ibkr_bridge.telemetry_client import (
    SignedTelemetryClient,
    TelemetryControlPlaneConfig,
)
from ttwo_ibkr_bridge.telemetry_runtime import ReadOnlyTelemetryRuntime


@dataclass(frozen=True)
class FakeTelemetry:
    positions: tuple[object, ...] = ()

    def as_payload(self) -> dict[str, Any]:
        return {
            "mode": "PAPER_READ_ONLY",
            "paper_account_verified": True,
            "positions": [],
        }


class FakeAdapter:
    def snapshot(self) -> FakeTelemetry:
        return FakeTelemetry()


class FakePublisher:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def publish(self, payload: dict[str, object]) -> None:
        self.payloads.append(payload)


class FakeResponse(AbstractContextManager["FakeResponse"]):
    status = 200

    def read(self, _limit: int) -> bytes:
        return b'{"accepted":true}'

    def __exit__(self, *args: object) -> None:
        return None


def test_runtime_only_publishes_redacted_snapshot() -> None:
    publisher = FakePublisher()
    count = ReadOnlyTelemetryRuntime(FakeAdapter(), publisher).tick()  # type: ignore[arg-type]
    assert count == 0
    assert publisher.payloads == [
        {"mode": "PAPER_READ_ONLY", "paper_account_verified": True, "positions": []}
    ]


def test_dedicated_client_signs_only_telemetry_route(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[Request] = []

    def urlopen(request: Request, timeout: float) -> FakeResponse:
        assert timeout == 15
        captured.append(request)
        return FakeResponse()

    monkeypatch.setattr("ttwo_ibkr_bridge.telemetry_client.time.time", lambda: 1_777_147_200)
    monkeypatch.setattr(
        "ttwo_ibkr_bridge.telemetry_client.secrets.token_urlsafe",
        lambda _length: "fixedtelemetrynonce1234567890",
    )
    monkeypatch.setattr("ttwo_ibkr_bridge.telemetry_client.urllib.request.urlopen", urlopen)
    secret = "telemetry-test-secret-that-is-longer-than-thirty-two-bytes"
    client = SignedTelemetryClient(
        TelemetryControlPlaneConfig(
            base_url="https://control.example",
            telemetry_id="oci-a1-paper-telemetry-01",
            shared_secret=secret,
            access_client_id="access-id",
            access_client_secret="access-secret",
        )
    )
    client.publish({"mode": "PAPER_READ_ONLY", "positions": []})

    assert len(captured) == 1
    request = captured[0]
    assert request.full_url == "https://control.example/internal/broker/telemetry"
    headers = {name.lower(): value for name, value in request.header_items()}
    body = request.data or b""
    digest = hashlib.sha256(body).hexdigest()
    canonical = "\n".join(
        (
            "1777147200",
            "fixedtelemetrynonce1234567890",
            "POST",
            "/internal/broker/telemetry",
            digest,
        )
    ).encode()
    assert headers["x-ttwo-telemetry-signature"] == hmac.new(
        secret.encode(), canonical, hashlib.sha256
    ).hexdigest()
    assert headers["cf-access-client-id"] == "access-id"
    assert headers["accept"] == "application/json"
    assert headers["user-agent"] == "Take-Two-IBKR-Telemetry/1.0"
    assert "x-ttwo-bridge-id" not in headers
    assert not hasattr(client, "claim")
    assert not hasattr(client, "post_event")


def test_python_signature_matches_shared_cloudflare_conformance_vector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_path = (
        Path(__file__).resolve().parents[3] / "fixtures/telemetry_hmac_v1.json"
    )
    vector = json.loads(fixture_path.read_text(encoding="utf-8"))
    monkeypatch.setattr(
        "ttwo_ibkr_bridge.telemetry_client.time.time",
        lambda: int(vector["timestamp"]),
    )
    monkeypatch.setattr(
        "ttwo_ibkr_bridge.telemetry_client.secrets.token_urlsafe",
        lambda _length: vector["nonce"],
    )
    client = SignedTelemetryClient(
        TelemetryControlPlaneConfig(
            base_url="https://control.example",
            telemetry_id=vector["telemetry_id"],
            shared_secret=vector["shared_secret"],
            access_client_id="test-access-id",
            access_client_secret="test-access-secret",
        )
    )
    body = vector["body"].encode()
    headers = client._headers(body)
    assert hashlib.sha256(body).hexdigest() == vector["payload_sha256"]
    assert headers["X-TTWO-Telemetry-Signature"] == vector["signature"]


def test_telemetry_entrypoint_has_no_execution_import_or_call() -> None:
    root = Path(__file__).resolve().parents[1] / "src/ttwo_ibkr_bridge"
    source = "\n".join(
        (root / name).read_text()
        for name in ("telemetry_client.py", "telemetry_runtime.py", "telemetry_main.py")
    )
    for forbidden in (
        "placeOrder(",
        "cancelOrder(",
        "reqGlobalCancel(",
        "exerciseOptions(",
        "claim(",
        "post_event(",
        "execute_bounded_combo(",
    ):
        assert forbidden not in source
    assert "from .gateway" not in source
    assert "from .runtime" not in source
