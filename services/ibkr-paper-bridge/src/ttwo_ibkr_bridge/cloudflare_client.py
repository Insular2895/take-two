"""Signed, outbound-only Cloudflare control-plane client."""

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

from .contracts import ClaimedIntent, GatewayEvent, GatewayHealth


class ControlPlaneError(RuntimeError):
    pass


@dataclass(frozen=True)
class ControlPlaneConfig:
    base_url: str
    bridge_id: str
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
            raise ValueError("control plane must use HTTPS")
        if len(self.shared_secret) < 32:
            raise ValueError("bridge shared secret must contain at least 32 characters")
        if not self.bridge_id or not self.access_client_id or not self.access_client_secret:
            raise ValueError(
                "bridge identity and Cloudflare Access service-token values are required"
            )


class SignedControlPlaneClient:
    def __init__(self, config: ControlPlaneConfig) -> None:
        config.validate()
        self._config = config

    def _headers(self, method: str, path: str, body: bytes) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(24)
        digest = hashlib.sha256(body).hexdigest()
        canonical = "\n".join((timestamp, nonce, method, path, digest)).encode()
        signature = hmac.new(
            self._config.shared_secret.encode(), canonical, hashlib.sha256
        ).hexdigest()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Take-Two-IBKR-Bridge/1.0",
            "CF-Access-Client-Id": self._config.access_client_id,
            "CF-Access-Client-Secret": self._config.access_client_secret,
            "X-TTWO-Bridge-Id": self._config.bridge_id,
            "X-TTWO-Bridge-Timestamp": timestamp,
            "X-TTWO-Bridge-Nonce": nonce,
            "X-TTWO-Bridge-Signature": signature,
        }

    def _post(self, path: str, payload: Mapping[str, Any]) -> dict[str, Any] | None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        request = urllib.request.Request(
            urljoin(self._config.base_url.rstrip("/") + "/", path.lstrip("/")),
            data=body,
            headers=self._headers("POST", path, body),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._config.timeout_seconds) as response:
                raw = response.read(128 * 1024)
                if response.status == 204:
                    return None
                decoded = json.loads(raw)
                if not isinstance(decoded, dict):
                    raise ControlPlaneError("control plane returned a non-object response")
                return decoded
        except urllib.error.HTTPError as error:
            raw = error.read(4096)
            try:
                detail = json.loads(raw).get("error", "UNKNOWN")
            except (json.JSONDecodeError, AttributeError):
                detail = "UNREADABLE"
            raise ControlPlaneError(f"control plane HTTP {error.code}: {detail}") from error

    def heartbeat(self, health: GatewayHealth) -> None:
        self._post(
            "/internal/broker/heartbeat",
            {
                "gateway_connected": health.gateway_connected,
                "paper_account_verified": health.paper_account_verified,
                "open_intent_count": health.open_intent_count,
                "detail": dict(health.detail),
            },
        )

    def claim(self) -> ClaimedIntent | None:
        payload = self._post("/internal/broker/intents/claim", {})
        return None if payload is None else ClaimedIntent.from_mapping(payload)

    def post_event(self, intent_id: str, event: GatewayEvent) -> None:
        self._post(f"/internal/broker/intents/{intent_id}/events", event.as_payload())
