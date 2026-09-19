"""Signed client restricted to the read-only telemetry endpoint."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse


class TelemetryPublishError(RuntimeError):
    """Safe outbound telemetry failure without credential or account detail."""


@dataclass(frozen=True)
class TelemetryControlPlaneConfig:
    base_url: str
    telemetry_id: str
    shared_secret: str
    access_client_id: str
    access_client_secret: str
    timeout_seconds: float = 15.0
    allow_http_localhost: bool = False

    def validate(self) -> None:
        parsed = urlparse(self.base_url)
        local_http = (
            self.allow_http_localhost
            and parsed.scheme == "http"
            and parsed.hostname in {"127.0.0.1", "localhost"}
        )
        if parsed.scheme != "https" and not local_http:
            raise ValueError("telemetry control plane must use HTTPS")
        if not self.telemetry_id or len(self.telemetry_id) > 80:
            raise ValueError("telemetry identity is required")
        if len(self.shared_secret) < 32:
            raise ValueError("telemetry shared secret must contain at least 32 characters")
        if not self.access_client_id or not self.access_client_secret:
            raise ValueError("Cloudflare Access service-token values are required")
        if self.timeout_seconds < 2 or self.timeout_seconds > 60:
            raise ValueError("telemetry timeout must be between 2 and 60 seconds")


class SignedTelemetryClient:
    """Can publish telemetry only; it has no intent-claim or event method."""

    _PATH = "/internal/broker/telemetry"

    def __init__(self, config: TelemetryControlPlaneConfig) -> None:
        config.validate()
        self._config = config

    def _headers(self, body: bytes) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(24)
        digest = hashlib.sha256(body).hexdigest()
        canonical = "\n".join((timestamp, nonce, "POST", self._PATH, digest)).encode()
        signature = hmac.new(
            self._config.shared_secret.encode(), canonical, hashlib.sha256
        ).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Take-Two-IBKR-Telemetry/1.0",
            "CF-Access-Client-Id": self._config.access_client_id,
            "CF-Access-Client-Secret": self._config.access_client_secret,
            "X-TTWO-Telemetry-Id": self._config.telemetry_id,
            "X-TTWO-Telemetry-Timestamp": timestamp,
            "X-TTWO-Telemetry-Nonce": nonce,
            "X-TTWO-Telemetry-Signature": signature,
        }

    def publish(self, payload: Mapping[str, Any]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        if len(body) > 64 * 1024:
            raise TelemetryPublishError("telemetry payload exceeds the signed route limit")
        request = urllib.request.Request(
            urljoin(self._config.base_url.rstrip("/") + "/", self._PATH.lstrip("/")),
            data=body,
            headers=self._headers(body),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._config.timeout_seconds) as response:
                raw = response.read(4096)
                if response.status != 200:
                    raise TelemetryPublishError(f"telemetry control plane HTTP {response.status}")
                decoded = json.loads(raw)
                if not isinstance(decoded, dict) or decoded.get("accepted") is not True:
                    raise TelemetryPublishError("telemetry control plane rejected the snapshot")
        except urllib.error.HTTPError as error:
            raw = error.read(4096)
            try:
                detail = json.loads(raw).get("error", "UNKNOWN")
            except (json.JSONDecodeError, AttributeError):
                detail = "UNREADABLE"
            raise TelemetryPublishError(
                f"telemetry control plane HTTP {error.code}: {detail}"
            ) from error
        except urllib.error.URLError as error:
            raise TelemetryPublishError("telemetry control plane is unreachable") from error
