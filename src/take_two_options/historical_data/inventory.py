"""Inventory private historical caches without exposing licensed observations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from take_two_options.historical_data.contracts import (
    DatasetQualityStatus,
    LicenseStatus,
    PointInTimeStatus,
    SourceComponentManifest,
)
from take_two_options.knowledge.provenance import stable_hash


def _payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _epoch(value: int | float) -> datetime:
    return datetime.fromtimestamp(value, UTC)


def inventory_marketdata_cache(cache_dir: Path) -> SourceComponentManifest:
    files = sorted(cache_dir.glob("*.json"))
    if not files:
        return SourceComponentManifest(
            component_id="marketdata-options-cache",
            provider="Market Data",
            source_ids=["marketdata-options-chain-api"],
            data_class="options",
            record_count=0,
            coverage_start=None,
            coverage_end=None,
            retrieved_start=None,
            retrieved_end=None,
            content_hash=stable_hash([]),
            missing_fields=["all required option fields"],
            license_status=LicenseStatus.TO_REVIEW,
            license_notes=(
                "No local cache was found; account and redistribution rights are unknown."
            ),
            terms_uri="https://www.marketdata.app/terms/",
            point_in_time_status=PointInTimeStatus.TO_REVIEW,
            quality_status=DatasetQualityStatus.BLOCKED,
            raw_location="not_acquired",
            raw_data_committed=False,
            adjustment_policy=(
                "Provider states option history is as-traded; corporate actions require "
                "separate handling."
            ),
            limitations=["No observations available."],
        )
    payload_hashes: list[str] = []
    updated: list[int | float] = []
    retrieved: list[datetime] = []
    rows = 0
    missing = {field: 0 for field in ("bid", "ask", "openInterest", "volume", "iv", "delta")}
    for path in files:
        raw = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        payload = cast(dict[str, Any], raw["payload"])
        expected = str(raw["payload_sha256"])
        if _payload_hash(payload) != expected:
            raise ValueError(f"cache payload hash mismatch: {path.name}")
        payload_hashes.append(expected)
        retrieved.append(datetime.fromisoformat(str(raw["fetched_at"]).replace("Z", "+00:00")))
        count = len(cast(list[Any], payload.get("optionSymbol", [])))
        rows += count
        updated.extend(cast(list[int | float], payload.get("updated", [])))
        for field in missing:
            values = payload.get(field)
            missing[field] += count if values is None else sum(
                value is None for value in cast(list[Any], values)
            )
    complete = [field for field, count in missing.items() if count == 0]
    absent = [field for field, count in missing.items() if count == rows]
    partial = [
        f"{field} missing in {count}/{rows} rows"
        for field, count in missing.items()
        if 0 < count < rows
    ]
    return SourceComponentManifest(
        component_id="marketdata-options-cache",
        provider="Market Data",
        source_ids=["marketdata-options-chain-api"],
        data_class="options",
        record_count=rows,
        coverage_start=_epoch(min(updated)),
        coverage_end=_epoch(max(updated)),
        retrieved_start=min(retrieved),
        retrieved_end=max(retrieved),
        content_hash=stable_hash(payload_hashes),
        observed_fields=[
            "occ_symbol",
            "option_type",
            "strike",
            "expiration",
            "quote_timestamp",
            "underlying_price",
            *complete,
        ],
        derived_fields=["mid"],
        missing_fields=absent,
        license_status=LicenseStatus.REDISTRIBUTION_FORBIDDEN,
        license_notes=(
            "Private cache only. Self-service terms prohibit redistribution; account-specific "
            "professional/internal authorization still requires human confirmation."
        ),
        terms_uri="https://www.marketdata.app/docs/account/data-policies/data-redistribution/",
        point_in_time_status=PointInTimeStatus.PARTIAL,
        quality_status=DatasetQualityStatus.PARTIAL,
        raw_location="local_private",
        raw_data_committed=False,
        adjustment_policy="As-traded option history; split/dividend adjustments are not supplied.",
        limitations=[
            "EOD quotes do not prove a simultaneous executable combo fill.",
            "Provider IV and Greeks are absent in this cache.",
            *partial,
        ],
    )


def inventory_alpaca_underlying(path: Path) -> SourceComponentManifest:
    if not path.is_file():
        return SourceComponentManifest(
            component_id="alpaca-underlying-bars",
            provider="Alpaca",
            source_ids=["alpaca-stock-bars-api"],
            data_class="underlying",
            record_count=0,
            coverage_start=None,
            coverage_end=None,
            retrieved_start=None,
            retrieved_end=None,
            content_hash=stable_hash([]),
            missing_fields=["OHLCV", "corporate_actions", "dividends"],
            license_status=LicenseStatus.TO_REVIEW,
            license_notes="No local underlying dataset was found.",
            terms_uri="https://docs.alpaca.markets/us/docs/historical-stock-data-1",
            point_in_time_status=PointInTimeStatus.TO_REVIEW,
            quality_status=DatasetQualityStatus.BLOCKED,
            raw_location="not_acquired",
            raw_data_committed=False,
            adjustment_policy="Not established.",
            limitations=["No observations available."],
        )
    raw_bytes = path.read_bytes()
    payload = cast(dict[str, Any], json.loads(raw_bytes))
    points = cast(list[dict[str, Any]], payload.get("points", []))
    if not points:
        raise ValueError("Alpaca underlying dataset contains no points")
    market_times = [
        datetime.fromisoformat(str(point["timestamp"]).replace("Z", "+00:00"))
        for point in points
    ]
    available_times = [
        datetime.fromisoformat(str(point["data_available_at"]).replace("Z", "+00:00"))
        for point in points
    ]
    if any(
        available < market
        for market, available in zip(market_times, available_times, strict=True)
    ):
        raise ValueError("underlying availability precedes market timestamp")
    retrieved = datetime.fromisoformat(str(payload["as_of"]).replace("Z", "+00:00"))
    return SourceComponentManifest(
        component_id="alpaca-underlying-bars",
        provider="Alpaca",
        source_ids=[str(cast(dict[str, Any], payload["source"])["id"])],
        data_class="underlying",
        record_count=len(points),
        coverage_start=min(market_times),
        coverage_end=max(market_times),
        retrieved_start=retrieved,
        retrieved_end=retrieved,
        content_hash=sha256(raw_bytes).hexdigest(),
        observed_fields=["adjusted_close", "market_timestamp", "available_at"],
        derived_fields=[],
        missing_fields=["open", "high", "low", "volume", "unadjusted_close"],
        unavailable_fields=["corporate_actions", "dividends"],
        license_status=LicenseStatus.TO_REVIEW,
        license_notes=(
            "Private authenticated API extract. Technical access is documented, but "
            "account-specific retention and research-use rights require human confirmation."
        ),
        terms_uri="https://docs.alpaca.markets/us/docs/about-market-data-api",
        point_in_time_status=PointInTimeStatus.VERIFIED,
        quality_status=DatasetQualityStatus.PARTIAL,
        raw_location="local_private",
        raw_data_committed=False,
        adjustment_policy=(
            "Provider request declared adjustment=all; raw/unadjusted companion is absent."
        ),
        limitations=[
            "Only adjusted daily closes are present.",
            "The IEX equity feed is not full-market SIP coverage.",
        ],
    )
