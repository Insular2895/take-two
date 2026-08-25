"""Normalize private Market Data option caches without redistributing licensed rows."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import OptionType, StrictModel
from take_two_options.marketdata_data import parse_occ_option_symbol


class HistoricalOptionObservation(StrictModel):
    """One point-in-time EOD option quote retained in the private research dataset."""

    ticker: str = Field(min_length=1)
    option_symbol: str = Field(min_length=15)
    option_type: OptionType
    strike: float = Field(gt=0)
    expiration: date
    quote_time: datetime
    available_at: datetime
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    mid: float | None = Field(default=None, ge=0)
    volume: float | None = Field(default=None, ge=0)
    open_interest: float | None = Field(default=None, ge=0)
    underlying_price: float | None = Field(default=None, gt=0)
    implied_volatility: float | None = Field(default=None, gt=0)
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None
    rho: float | None = None
    multiplier: float = Field(gt=0)
    provider: Literal["Market Data"] = "Market Data"
    provenance: dict[str, str]
    quality_flags: list[str] = Field(default_factory=list)
    retrieved_at: datetime
    raw_hash: str = Field(min_length=64, max_length=64)

    @field_validator("quote_time", "available_at", "retrieved_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("historical option timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_quote(self) -> HistoricalOptionObservation:
        if self.ask is not None and self.bid is not None and self.ask < self.bid:
            raise ValueError("ask cannot be below bid")
        if self.available_at < self.quote_time:
            raise ValueError("available_at cannot precede quote_time")
        return self


class HistoricalOptionDatasetSummary(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    generated_at: datetime
    raw_envelopes: int = Field(ge=0)
    raw_rows: int = Field(ge=0)
    unique_observations: int = Field(ge=0)
    exact_duplicates_removed: int = Field(ge=0)
    conflicting_observations: int = Field(ge=0)
    requested_date_start: date | None
    requested_date_end: date | None
    quote_time_start: datetime | None
    quote_time_end: datetime | None
    observations_per_requested_date: dict[str, int]
    non_null_field_counts: dict[str, int]
    quality_flag_counts: dict[str, int]
    dataset_hash: str = Field(min_length=64, max_length=64)
    normalized_location: Literal["local_private"] = "local_private"
    raw_data_committed: Literal[False] = False
    availability_policy: str = Field(min_length=1)
    order_capability: Literal["forbidden"] = "forbidden"
    limitations: list[str]

    @field_validator("generated_at", "quote_time_start", "quote_time_end")
    @classmethod
    def require_summary_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("summary timestamps must be timezone-aware")
        return value.astimezone(UTC) if value is not None else None


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str | int | float) -> datetime:
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return datetime.fromtimestamp(value, UTC)


def _aligned(payload: dict[str, Any], name: str, count: int) -> list[Any]:
    values = payload.get(name)
    if values is None:
        return [None] * count
    if not isinstance(values, list) or len(values) != count:
        raise ValueError(f"Market Data field {name} is not aligned with optionSymbol")
    return values


def _row_fingerprint(observation: HistoricalOptionObservation) -> str:
    payload = observation.model_dump(mode="json", exclude={"retrieved_at", "raw_hash"})
    return _canonical_hash(payload)


def normalize_marketdata_cache(
    cache_dir: Path,
    *,
    availability_delay_hours: float = 24.0,
    generated_at: datetime | None = None,
) -> tuple[list[HistoricalOptionObservation], HistoricalOptionDatasetSummary]:
    """Verify, normalize, and exact-deduplicate all cache envelopes.

    Rows with conflicting values for the same requested date and OCC symbol are rejected.  The
    availability delay is a conservative, configurable research convention and is not presented
    as an exchange timestamp.
    """

    if availability_delay_hours < 0:
        raise ValueError("availability_delay_hours cannot be negative")
    files = sorted(cache_dir.glob("*.json"))
    if not files:
        raise ValueError(f"no Market Data cache envelopes found in {cache_dir}")
    keyed: dict[tuple[date, str], tuple[str, HistoricalOptionObservation]] = {}
    requested_dates: Counter[str] = Counter()
    quality_flags: Counter[str] = Counter()
    raw_rows = 0
    duplicates = 0
    conflicts: list[str] = []
    delay = timedelta(hours=availability_delay_hours)
    for path in files:
        envelope = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        payload = cast(dict[str, Any], envelope["payload"])
        payload_hash = _canonical_hash(payload)
        if payload_hash != str(envelope["payload_sha256"]):
            raise ValueError(f"cache payload hash mismatch: {path.name}")
        symbols = _aligned(payload, "optionSymbol", len(cast(list[Any], payload["optionSymbol"])))
        count = len(symbols)
        raw_rows += count
        params = cast(dict[str, str], envelope["params"])
        requested_date = date.fromisoformat(params["date"])
        retrieved_at = _parse_timestamp(str(envelope["fetched_at"]))
        arrays = {
            name: _aligned(payload, name, count)
            for name in (
                "underlying",
                "expiration",
                "side",
                "strike",
                "updated",
                "bid",
                "ask",
                "mid",
                "volume",
                "openInterest",
                "underlyingPrice",
                "iv",
                "delta",
                "gamma",
                "vega",
                "theta",
            )
        }
        for index, raw_symbol in enumerate(symbols):
            parsed = parse_occ_option_symbol(str(raw_symbol))
            quote_time = _parse_timestamp(cast(int | float, arrays["updated"][index]))
            bid = _optional_float(arrays["bid"][index])
            ask = _optional_float(arrays["ask"][index])
            vendor_mid = _optional_float(arrays["mid"][index])
            derived_mid = (bid + ask) / 2.0 if bid is not None and ask is not None else vendor_mid
            flags: list[str] = []
            if bid is None or ask is None:
                flags.append("incomplete_bid_ask")
            if (
                vendor_mid is not None
                and derived_mid is not None
                and abs(vendor_mid - derived_mid) > 0.011
            ):
                flags.append("vendor_mid_mismatch")
            analytics_values = [
                arrays[name][index] for name in ("iv", "delta", "gamma", "vega", "theta")
            ]
            if all(value is None for value in analytics_values):
                flags.append("vendor_analytics_unavailable")
            provenance = {
                "ticker": "observed:underlying",
                "option_symbol": "observed:optionSymbol",
                "option_type": "derived:OCC_symbol",
                "strike": "derived:OCC_symbol;cross_checked:strike",
                "expiration": "derived:OCC_symbol;cross_checked:expiration",
                "quote_time": "observed:updated",
                "available_at": f"derived:quote_time_plus_{availability_delay_hours:g}h",
                "bid": "observed:bid",
                "ask": "observed:ask",
                "mid": "derived:bid_ask_midpoint",
                "volume": "observed:volume",
                "open_interest": "observed:openInterest",
                "underlying_price": "observed:underlyingPrice",
                "implied_volatility": "observed:iv_or_missing",
                "delta": "observed:delta_or_missing",
                "gamma": "observed:gamma_or_missing",
                "vega": "observed:vega_or_missing",
                "theta": "observed:theta_or_missing",
                "rho": "unavailable_from_source",
                "multiplier": "derived:standard_contract_filter_nonstandard_false",
            }
            observation = HistoricalOptionObservation(
                ticker=str(arrays["underlying"][index] or parsed.root).upper(),
                option_symbol=parsed.symbol,
                option_type=parsed.option_type,
                strike=parsed.strike,
                expiration=parsed.expiration,
                quote_time=quote_time,
                available_at=quote_time + delay,
                bid=bid,
                ask=ask,
                mid=derived_mid,
                volume=_optional_float(arrays["volume"][index]),
                open_interest=_optional_float(arrays["openInterest"][index]),
                underlying_price=_optional_float(arrays["underlyingPrice"][index]),
                implied_volatility=_optional_float(arrays["iv"][index]),
                delta=_optional_float(arrays["delta"][index]),
                gamma=_optional_float(arrays["gamma"][index]),
                vega=_optional_float(arrays["vega"][index]),
                theta=_optional_float(arrays["theta"][index]),
                rho=None,
                multiplier=100.0,
                provenance=provenance,
                quality_flags=flags,
                retrieved_at=retrieved_at,
                raw_hash=payload_hash,
            )
            key = (requested_date, parsed.symbol)
            fingerprint = _row_fingerprint(observation)
            prior = keyed.get(key)
            if prior is not None:
                if prior[0] == fingerprint:
                    duplicates += 1
                    continue
                conflicts.append(f"{requested_date.isoformat()}:{parsed.symbol}")
                continue
            keyed[key] = (fingerprint, observation)
            requested_dates[requested_date.isoformat()] += 1
            quality_flags.update(flags)
    if conflicts:
        preview = ", ".join(sorted(conflicts)[:5])
        raise ValueError(f"conflicting duplicate option observations: {preview}")
    observations = [item[1] for _, item in sorted(keyed.items())]
    serialized = [item.model_dump(mode="json") for item in observations]
    field_names = (
        "bid",
        "ask",
        "mid",
        "volume",
        "open_interest",
        "underlying_price",
        "implied_volatility",
        "delta",
        "gamma",
        "vega",
        "theta",
        "rho",
    )
    quote_times = [item.quote_time for item in observations]
    dates = [date.fromisoformat(value) for value in requested_dates]
    summary = HistoricalOptionDatasetSummary(
        dataset_id="ttwo-marketdata-private-normalized-v1",
        ticker="TTWO",
        generated_at=(generated_at or datetime.now(UTC)).astimezone(UTC),
        raw_envelopes=len(files),
        raw_rows=raw_rows,
        unique_observations=len(observations),
        exact_duplicates_removed=duplicates,
        conflicting_observations=0,
        requested_date_start=min(dates),
        requested_date_end=max(dates),
        quote_time_start=min(quote_times),
        quote_time_end=max(quote_times),
        observations_per_requested_date=dict(sorted(requested_dates.items())),
        non_null_field_counts={
            name: sum(getattr(item, name) is not None for item in observations)
            for name in field_names
        },
        quality_flag_counts=dict(sorted(quality_flags.items())),
        dataset_hash=_canonical_hash(serialized),
        availability_policy=(
            f"Conservative research convention: available_at = quote_time + "
            f"{availability_delay_hours:g} hours; configurable and sensitivity-tested."
        ),
        limitations=[
            "Historical EOD quotes are not evidence of simultaneous executable fills.",
            "Vendor IV and Greeks are absent and remain null at normalization.",
            "Raw and normalized licensed observations remain local and are not committed.",
        ],
    )
    return observations, summary


def write_private_jsonl(path: Path, observations: list[HistoricalOptionObservation]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(item.model_dump_json() + "\n" for item in observations)
    path.write_text(payload, encoding="utf-8")


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
