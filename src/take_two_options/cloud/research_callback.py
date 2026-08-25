"""HMAC protocol shared by the GitHub research runner and Worker tests."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class SignedRequest:
    timestamp: str
    nonce: str
    content_sha256: str
    signature: str


def signature_payload(
    *,
    timestamp: str,
    nonce: str,
    analysis_request_id: str,
    method: str,
    pathname: str,
    content_sha256: str,
) -> bytes:
    return "\n".join(
        (
            timestamp,
            nonce,
            analysis_request_id,
            method.upper(),
            pathname,
            content_sha256,
        )
    ).encode("utf-8")


def sign_request(
    *,
    secret: str,
    analysis_request_id: str,
    method: str,
    pathname: str,
    body: bytes = b"",
    timestamp: int | None = None,
    nonce: str | None = None,
) -> SignedRequest:
    stamp = str(timestamp if timestamp is not None else int(time.time()))
    request_nonce = nonce or secrets.token_hex(16)
    content_hash = hashlib.sha256(body).hexdigest()
    signature = hmac.new(
        secret.encode("utf-8"),
        signature_payload(
            timestamp=stamp,
            nonce=request_nonce,
            analysis_request_id=analysis_request_id,
            method=method,
            pathname=pathname,
            content_sha256=content_hash,
        ),
        hashlib.sha256,
    ).hexdigest()
    return SignedRequest(stamp, request_nonce, content_hash, signature)
