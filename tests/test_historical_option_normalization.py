from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from take_two_options.historical_data.option_observations import normalize_marketdata_cache


def _write_envelope(path: Path, *, bid: float = 10.0) -> None:
    payload = {
        "s": "ok",
        "optionSymbol": ["TTWO260320C00250000"],
        "underlying": ["TTWO"],
        "expiration": [1774036800],
        "side": ["call"],
        "strike": [250],
        "updated": [1767225600],
        "bid": [bid],
        "ask": [12.0],
        "mid": [11.0],
        "volume": [3],
        "openInterest": [42],
        "underlyingPrice": [255.0],
        "iv": [None],
        "delta": [None],
        "gamma": [None],
        "vega": [None],
        "theta": [None],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    envelope = {
        "fetched_at": "2026-07-19T00:00:00Z",
        "endpoint": "/v1/options/chain/TTWO/",
        "params": {"date": "2026-01-01", "nonstandard": "false"},
        "payload": payload,
        "payload_sha256": sha256(canonical.encode()).hexdigest(),
        "usage": {},
    }
    path.write_text(json.dumps(envelope), encoding="utf-8")


def test_normalization_preserves_missing_vendor_analytics_and_deduplicates(tmp_path: Path) -> None:
    _write_envelope(tmp_path / "a.json")
    _write_envelope(tmp_path / "b.json")
    rows, summary = normalize_marketdata_cache(
        tmp_path, generated_at=datetime(2026, 8, 8, tzinfo=UTC)
    )
    assert len(rows) == 1
    assert summary.exact_duplicates_removed == 1
    assert summary.raw_rows == 2
    assert rows[0].implied_volatility is None
    assert rows[0].rho is None
    assert rows[0].mid == 11.0
    assert rows[0].available_at > rows[0].quote_time
    assert "vendor_analytics_unavailable" in rows[0].quality_flags


def test_normalization_rejects_conflicting_duplicates(tmp_path: Path) -> None:
    _write_envelope(tmp_path / "a.json")
    _write_envelope(tmp_path / "b.json", bid=9.0)
    with pytest.raises(ValueError, match="conflicting duplicate"):
        normalize_marketdata_cache(tmp_path)


def test_normalization_rejects_payload_hash_drift(tmp_path: Path) -> None:
    _write_envelope(tmp_path / "a.json")
    raw = json.loads((tmp_path / "a.json").read_text())
    raw["payload"]["bid"] = [9.0]
    (tmp_path / "a.json").write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="payload hash mismatch"):
        normalize_marketdata_cache(tmp_path)
