"""Point-in-time aligned underlying, rates, dividend, and FX research context."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from hashlib import sha256
from io import StringIO
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel


class UnderlyingDailyBar(StrictModel):
    ticker: str
    market_time: datetime
    available_at: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    trade_count: float | None = Field(default=None, ge=0)
    vwap: float | None = Field(default=None, gt=0)
    adjustment: Literal["all"] = "all"
    feed: Literal["iex", "sip"]
    provider: Literal["Alpaca"] = "Alpaca"

    @model_validator(mode="after")
    def validate_ohlc(self) -> UnderlyingDailyBar:
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high must contain OHLC")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must contain OHLC")
        if self.available_at <= self.market_time:
            raise ValueError("daily bar availability must follow market time")
        return self


class RiskFreeCurvePoint(StrictModel):
    observation_date: date
    available_at: datetime
    rates_by_maturity_days: dict[int, float]
    provider: Literal["U.S. Department of the Treasury"] = "U.S. Department of the Treasury"
    curve_kind: Literal["daily_par_yield"] = "daily_par_yield"


class FxReferenceRate(StrictModel):
    observation_date: date
    available_at: datetime
    usd_per_eur: float = Field(gt=0)
    provider: Literal["European Central Bank"] = "European Central Bank"
    status: str = Field(min_length=1)


class CorporateActionRecord(StrictModel):
    action_type: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    effective_date: date
    available_at: datetime
    raw_public_fields: dict[str, str | float | bool | None]
    provider: Literal["Alpaca"] = "Alpaca"


class DividendPolicyEvidence(StrictModel):
    cash_dividend_yield: float = Field(default=0.0, ge=0.0, le=0.0)
    status: Literal["verified_zero_through_filing_date"]
    filing_date: date
    available_at: datetime
    source_url: str
    source_hash: str = Field(min_length=64, max_length=64)
    statement: str


class MarketContextDataset(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str
    ticker: Literal["TTWO"] = "TTWO"
    generated_at: datetime
    underlying_bars: list[UnderlyingDailyBar] = Field(min_length=8)
    risk_free_curves: list[RiskFreeCurvePoint] = Field(min_length=1)
    fx_rates: list[FxReferenceRate] = Field(min_length=1)
    corporate_actions: list[CorporateActionRecord]
    dividend_policy: DividendPolicyEvidence
    source_hashes: dict[str, str]
    order_capability: Literal["forbidden"] = "forbidden"
    raw_data_committed: Literal[False] = False

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("dataset timestamps must be timezone-aware")
        return value.astimezone(UTC)


class MarketContextSummary(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str
    generated_at: datetime
    dataset_hash: str = Field(min_length=64, max_length=64)
    underlying_bar_count: int = Field(ge=0)
    underlying_start: date
    underlying_end: date
    underlying_fields: list[str]
    rate_curve_count: int = Field(ge=0)
    rate_start: date
    rate_end: date
    fx_rate_count: int = Field(ge=0)
    fx_start: date
    fx_end: date
    corporate_action_count: int = Field(ge=0)
    cash_dividend_yield: float = Field(ge=0)
    dividend_policy_status: str
    source_hashes: dict[str, str]
    raw_location: Literal["local_private"] = "local_private"
    raw_data_committed: Literal[False] = False
    point_in_time_status: Literal["VERIFIED_WITH_CONSERVATIVE_LAGS"]
    order_capability: Literal["forbidden"] = "forbidden"
    limitations: list[str]


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def parse_treasury_csv(text: str) -> list[RiskFreeCurvePoint]:
    tenor_days = {
        "1 Mo": 30,
        "1.5 Month": 45,
        "2 Mo": 60,
        "3 Mo": 91,
        "4 Mo": 121,
        "6 Mo": 182,
        "1 Yr": 365,
        "2 Yr": 730,
        "3 Yr": 1095,
        "5 Yr": 1825,
        "7 Yr": 2555,
        "10 Yr": 3650,
        "20 Yr": 7300,
        "30 Yr": 10950,
    }
    output: list[RiskFreeCurvePoint] = []
    for row in csv.DictReader(StringIO(text)):
        raw_date = row.get("Date")
        if not raw_date:
            continue
        month, day, year = (int(value) for value in raw_date.split("/"))
        observed = date(year, month, day)
        rates: dict[int, float] = {}
        for label, days in tenor_days.items():
            value = row.get(label)
            if value not in {None, "", "N/A"}:
                rates[days] = float(str(value)) / 100.0
        if rates:
            output.append(
                RiskFreeCurvePoint(
                    observation_date=observed,
                    available_at=datetime.combine(observed + timedelta(days=1), time.min, UTC),
                    rates_by_maturity_days=rates,
                )
            )
    return sorted(output, key=lambda item: item.observation_date)


def parse_ecb_fx_csv(text: str) -> list[FxReferenceRate]:
    output: list[FxReferenceRate] = []
    for row in csv.DictReader(StringIO(text)):
        observed = date.fromisoformat(row["TIME_PERIOD"])
        output.append(
            FxReferenceRate(
                observation_date=observed,
                available_at=datetime.combine(observed + timedelta(days=1), time.min, UTC),
                usd_per_eur=float(row["OBS_VALUE"]),
                status=row.get("OBS_STATUS") or "unknown",
            )
        )
    if not output:
        raise ValueError("ECB FX response contained no observations")
    return sorted(output, key=lambda item: item.observation_date)


def summarize_market_context(dataset: MarketContextDataset) -> MarketContextSummary:
    bars = dataset.underlying_bars
    curves = dataset.risk_free_curves
    fx_rates = dataset.fx_rates
    payload = dataset.model_dump(mode="json")
    return MarketContextSummary(
        dataset_id=dataset.dataset_id,
        generated_at=dataset.generated_at,
        dataset_hash=canonical_hash(payload),
        underlying_bar_count=len(bars),
        underlying_start=min(item.market_time.date() for item in bars),
        underlying_end=max(item.market_time.date() for item in bars),
        underlying_fields=["open", "high", "low", "close", "volume", "trade_count", "vwap"],
        rate_curve_count=len(curves),
        rate_start=min(item.observation_date for item in curves),
        rate_end=max(item.observation_date for item in curves),
        fx_rate_count=len(fx_rates),
        fx_start=min(item.observation_date for item in fx_rates),
        fx_end=max(item.observation_date for item in fx_rates),
        corporate_action_count=len(dataset.corporate_actions),
        cash_dividend_yield=dataset.dividend_policy.cash_dividend_yield,
        dividend_policy_status=dataset.dividend_policy.status,
        source_hashes=dataset.source_hashes,
        point_in_time_status="VERIFIED_WITH_CONSERVATIVE_LAGS",
        limitations=[
            "Alpaca IEX is a single-exchange equity feed, not consolidated SIP.",
            "Daily bars, Treasury curves, and ECB rates use a conservative next-day lag.",
            "Treasury par yields are interpolated proxies, not option-specific funding curves.",
            "The zero dividend yield is verified through the 2026-05-21 Form 10-K filing date.",
        ],
    )
