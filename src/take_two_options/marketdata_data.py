"""Read-only historical EOD option data from MarketData.app.

The adapter is deliberately limited to pricing endpoints. It has no broker, account, portfolio,
order, exercise, or position capability.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pydantic import Field, ValidationError, model_validator

from take_two_options.american import HistoricalOptionAnalytics, historical_option_analytics
from take_two_options.backtesting import (
    BacktestCase,
    BacktestDataset,
    BacktestLeg,
    HistoricalOptionQuote,
)
from take_two_options.domain import (
    EvidenceReference,
    EvidenceStatus,
    OptionType,
    PositionSide,
    StrictModel,
)

MARKETDATA_BASE_URL = "https://api.marketdata.app"
MARKETDATA_CHAIN_PATH = "/v1/options/chain/{ticker}/"
_NEW_YORK = ZoneInfo("America/New_York")
_OCC_PATTERN = re.compile(
    r"^(?P<root>[A-Z0-9.]{1,6})(?P<date>\d{6})(?P<right>[CP])(?P<strike>\d{8})$"
)


class MarketDataError(RuntimeError):
    """Raised when MarketData.app ingestion cannot preserve its declared contract."""


@dataclass(frozen=True)
class MarketDataCredentials:
    token: str = field(repr=False)

    @classmethod
    def from_env(cls) -> MarketDataCredentials:
        token = os.getenv("MARKETDATA_TOKEN") or os.getenv("MARKETDATA_API_TOKEN")
        if not token:
            raise MarketDataError(
                "MarketData.app token is missing; set MARKETDATA_TOKEN in the environment"
            )
        return cls(token=token)


@dataclass(frozen=True)
class MarketDataHttpResponse:
    payload: dict[str, Any]
    headers: Mapping[str, str]


class MarketDataTransport(Protocol):
    def get_json(
        self, *, url: str, headers: Mapping[str, str], timeout: float
    ) -> MarketDataHttpResponse: ...


class UrllibMarketDataTransport:
    def get_json(
        self, *, url: str, headers: Mapping[str, str], timeout: float
    ) -> MarketDataHttpResponse:
        request = Request(url, headers=dict(headers), method="GET")  # noqa: S310
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                raw_payload = response.read()
                response_headers = dict(response.headers.items())
        except HTTPError as error:
            detail = _http_error_detail(error)
            raise MarketDataError(f"MarketData.app HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise MarketDataError(f"MarketData.app network error: {error.reason}") from error
        try:
            payload = json.loads(raw_payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise MarketDataError("MarketData.app returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise MarketDataError("MarketData.app returned a non-object JSON response")
        return MarketDataHttpResponse(
            payload=cast(dict[str, Any], payload), headers=response_headers
        )


class MarketDataRateLimit(StrictModel):
    consumed: int | None = None
    remaining: int | None = None
    limit: int | None = None
    reset_at: datetime | None = None


class MarketDataCacheEnvelope(StrictModel):
    fetched_at: datetime
    endpoint: str
    params: dict[str, str]
    payload: dict[str, Any]
    payload_sha256: str = Field(min_length=64, max_length=64)
    usage: MarketDataRateLimit


class MarketDataDividendInput(StrictModel):
    ex_date: date
    amount: float = Field(gt=0)


class MarketDataOptionRecord(StrictModel):
    option_symbol: str = Field(min_length=15)
    underlying: str = Field(min_length=1)
    expiration: datetime
    option_type: OptionType
    strike: float = Field(gt=0)
    first_traded: datetime | None = None
    dte: int | None = Field(default=None, ge=0)
    quote_timestamp: datetime
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)
    mid: float | None = Field(default=None, ge=0)
    last: float | None = Field(default=None, ge=0)
    volume: float | None = Field(default=None, ge=0)
    open_interest: float | None = Field(default=None, ge=0)
    underlying_price: float | None = Field(default=None, gt=0)
    vendor_implied_volatility: float | None = Field(default=None, gt=0)
    vendor_delta: float | None = None
    vendor_gamma: float | None = None
    vendor_theta: float | None = None
    vendor_vega: float | None = None
    computed_analytics: HistoricalOptionAnalytics | None = None
    analytics_warning: str | None = None

    @model_validator(mode="after")
    def validate_quote(self) -> MarketDataOptionRecord:
        if self.bid is not None and self.ask is not None and self.ask < self.bid:
            raise ValueError("MarketData.app ask cannot be below bid")
        return self


class MarketDataChainExport(StrictModel):
    ticker: str
    requested_date: date
    retrieved_at: datetime
    provider_fetched_at: datetime
    params: dict[str, str]
    source: EvidenceReference
    usage: MarketDataRateLimit
    cache_hit: bool
    contracts: list[MarketDataOptionRecord]
    order_capability: Literal["forbidden"] = "forbidden"


class MarketDataBacktestLegSpec(StrictModel):
    symbol: str = Field(min_length=15)
    side: PositionSide
    quantity: int = Field(default=1, gt=0)
    multiplier: float = Field(gt=0)


class MarketDataBacktestCaseSpec(StrictModel):
    case_id: str = Field(min_length=1)
    split: Literal["train", "test"]
    entry_quote_date: date
    exit_quote_date: date
    entry_timestamp: datetime
    exit_timestamp: datetime
    model_calibrated_through: datetime
    legs: list[MarketDataBacktestLegSpec] = Field(min_length=1)
    commission_per_contract_per_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_per_side: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timeline(self) -> MarketDataBacktestCaseSpec:
        if self.exit_quote_date <= self.entry_quote_date:
            raise ValueError("backtest exit quote date must follow entry quote date")
        if _ensure_utc(self.exit_timestamp) <= _ensure_utc(self.entry_timestamp):
            raise ValueError("backtest exit must follow entry")
        if _ensure_utc(self.model_calibrated_through) >= _ensure_utc(self.entry_timestamp):
            raise ValueError("model calibration must end before entry")
        return self


class MarketDataOptionBacktestSpec(StrictModel):
    ticker: str = Field(min_length=1)
    risk_free_rate: float = Field(gt=-0.2, lt=1)
    continuous_dividend_yield: float = Field(default=0.0, ge=0, lt=1)
    dividends: list[MarketDataDividendInput] = Field(default_factory=list)
    time_grid: int = Field(default=100, ge=25, le=1000)
    price_grid: int = Field(default=100, ge=25, le=1000)
    cases: list[MarketDataBacktestCaseSpec] = Field(min_length=2)
    notes: str = ""

    @model_validator(mode="after")
    def validate_contracts_and_splits(self) -> MarketDataOptionBacktestSpec:
        if {case.split for case in self.cases} != {"train", "test"}:
            raise ValueError("MarketData.app backtest spec requires train and test cases")
        ticker = self.ticker.upper()
        for case in self.cases:
            for leg in case.legs:
                contract = parse_occ_option_symbol(leg.symbol)
                if contract.root != ticker:
                    raise ValueError(
                        f"contract {contract.symbol} does not match underlying {ticker}"
                    )
                if contract.expiration < case.exit_quote_date:
                    raise ValueError(f"contract {contract.symbol} expires before backtest exit")
        return self


@dataclass(frozen=True)
class OccOptionSymbol:
    symbol: str
    root: str
    expiration: date
    option_type: OptionType
    strike: float


def parse_occ_option_symbol(value: str) -> OccOptionSymbol:
    normalized = value.strip().upper()
    if normalized.startswith("O:"):
        normalized = normalized[2:]
    match = _OCC_PATTERN.fullmatch(normalized)
    if match is None:
        raise ValueError(f"invalid OCC option symbol: {value}")
    expiration = datetime.strptime(match.group("date"), "%y%m%d").date()
    return OccOptionSymbol(
        symbol=normalized,
        root=match.group("root"),
        expiration=expiration,
        option_type=OptionType.CALL if match.group("right") == "C" else OptionType.PUT,
        strike=int(match.group("strike")) / 1000.0,
    )


class MarketDataReadOnlyClient:
    """Historical pricing facade with a content-verified local cache."""

    def __init__(
        self,
        *,
        credentials: MarketDataCredentials,
        transport: MarketDataTransport | None = None,
        cache_dir: Path = Path("data/marketdata/cache"),
        timeout: float = 30.0,
    ) -> None:
        self._credentials = credentials
        self._transport = transport or UrllibMarketDataTransport()
        self.cache_dir = cache_dir
        self.timeout = timeout

    @classmethod
    def from_env(
        cls,
        *,
        cache_dir: Path = Path("data/marketdata/cache"),
        timeout: float = 30.0,
    ) -> MarketDataReadOnlyClient:
        return cls(
            credentials=MarketDataCredentials.from_env(),
            cache_dir=cache_dir,
            timeout=timeout,
        )

    def historical_chain(
        self,
        *,
        ticker: str,
        quote_date: date,
        expiration: date | Literal["all"] | None = None,
        side: Literal["call", "put"] | None = None,
        strikes: list[float] | None = None,
        strike_limit: int | None = None,
        min_open_interest: int | None = None,
        min_volume: int | None = None,
        risk_free_rate: float | None = None,
        continuous_dividend_yield: float = 0.0,
        dividends: tuple[tuple[date, float], ...] = (),
        time_grid: int = 100,
        price_grid: int = 100,
        force_refresh: bool = False,
        retrieved_at: datetime | None = None,
    ) -> MarketDataChainExport:
        normalized_ticker = ticker.upper()
        endpoint = MARKETDATA_CHAIN_PATH.format(ticker=quote(normalized_ticker, safe=""))
        params = {"date": quote_date.isoformat(), "nonstandard": "false"}
        if expiration is not None:
            if expiration == "all":
                params["expiration"] = "all"
            else:
                params["expiration"] = expiration.isoformat()
        if side is not None:
            params["side"] = side
        if strikes:
            params["strike"] = ",".join(_format_number(value) for value in sorted(set(strikes)))
        if strike_limit is not None:
            if strike_limit <= 0:
                raise MarketDataError("strike_limit must be positive")
            params["strikeLimit"] = str(strike_limit)
        if min_open_interest is not None:
            params["minOpenInterest"] = str(min_open_interest)
        if min_volume is not None:
            params["minVolume"] = str(min_volume)

        payload, usage, cache_hit, provider_fetched_at = self._request(
            endpoint=endpoint,
            params=params,
            force_refresh=force_refresh,
            fetched_at=_ensure_utc(retrieved_at or datetime.now(UTC)),
        )
        status = payload.get("s")
        if status != "ok":
            message = payload.get("errmsg") or f"status={status}"
            raise MarketDataError(f"MarketData.app option-chain request failed: {message}")
        records = _normalize_chain(
            payload,
            ticker=normalized_ticker,
            requested_date=quote_date,
            risk_free_rate=risk_free_rate,
            continuous_dividend_yield=continuous_dividend_yield,
            dividends=dividends,
            time_grid=time_grid,
            price_grid=price_grid,
        )
        accessed_at = _ensure_utc(retrieved_at or datetime.now(UTC))
        query_uri = f"{MARKETDATA_BASE_URL}{endpoint}?{urlencode(sorted(params.items()))}"
        source = EvidenceReference(
            id=(
                f"MARKETDATA-EOD-CHAIN-{normalized_ticker}-"
                f"{quote_date.strftime('%Y%m%d')}-{provider_fetched_at.strftime('%Y%m%dT%H%M%SZ')}"
            ),
            title=f"MarketData.app historical EOD option chain for {normalized_ticker}",
            source_type="marketdata_app_historical_eod_api",
            uri=query_uri,
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=accessed_at,
            confidence_level="medium",
            notes=(
                "Historical EOD bid/ask and liquidity fields; personal non-commercial plan; "
                "not an intraday NBBO replay"
            ),
            used_for_decision=True,
        )
        return MarketDataChainExport(
            ticker=normalized_ticker,
            requested_date=quote_date,
            retrieved_at=accessed_at,
            provider_fetched_at=provider_fetched_at,
            params=params,
            source=source,
            usage=usage,
            cache_hit=cache_hit,
            contracts=records,
        )

    def option_backtest_dataset(
        self,
        spec: MarketDataOptionBacktestSpec,
        *,
        force_refresh: bool = False,
        retrieved_at: datetime | None = None,
    ) -> BacktestDataset:
        retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
        requirements: dict[tuple[date, date, OptionType], set[float]] = {}
        contracts: dict[str, OccOptionSymbol] = {}
        for case in spec.cases:
            for leg in case.legs:
                parsed = parse_occ_option_symbol(leg.symbol)
                contracts[parsed.symbol] = parsed
                for quote_date in (case.entry_quote_date, case.exit_quote_date):
                    key = (quote_date, parsed.expiration, parsed.option_type)
                    requirements.setdefault(key, set()).add(parsed.strike)

        records_by_date_and_symbol: dict[tuple[date, str], MarketDataOptionRecord] = {}
        cache_hits = 0
        request_count = 0
        dividends = tuple((item.ex_date, item.amount) for item in spec.dividends)
        for (quote_date, expiration, option_type), strikes in sorted(
            requirements.items(), key=lambda item: item[0]
        ):
            export = self.historical_chain(
                ticker=spec.ticker,
                quote_date=quote_date,
                expiration=expiration,
                side=option_type.value,
                strikes=sorted(strikes),
                risk_free_rate=spec.risk_free_rate,
                continuous_dividend_yield=spec.continuous_dividend_yield,
                dividends=dividends,
                time_grid=spec.time_grid,
                price_grid=spec.price_grid,
                force_refresh=force_refresh,
                retrieved_at=retrieved,
            )
            request_count += 1
            cache_hits += int(export.cache_hit)
            for record in export.contracts:
                records_by_date_and_symbol[(quote_date, record.option_symbol)] = record

        cases: list[BacktestCase] = []
        for case in spec.cases:
            legs: list[BacktestLeg] = []
            for leg in case.legs:
                symbol = parse_occ_option_symbol(leg.symbol).symbol
                entry = records_by_date_and_symbol.get((case.entry_quote_date, symbol))
                exit_record = records_by_date_and_symbol.get((case.exit_quote_date, symbol))
                if entry is None or exit_record is None:
                    missing_dates = [
                        quote_date.isoformat()
                        for quote_date, record in (
                            (case.entry_quote_date, entry),
                            (case.exit_quote_date, exit_record),
                        )
                        if record is None
                    ]
                    raise MarketDataError(
                        f"MarketData.app did not return {symbol} for: {', '.join(missing_dates)}"
                    )
                legs.append(
                    BacktestLeg(
                        side=leg.side,
                        quantity=leg.quantity,
                        multiplier=leg.multiplier,
                        entry_quote=historical_option_quote(entry),
                        exit_quote=historical_option_quote(exit_record),
                    )
                )
            cases.append(
                BacktestCase(
                    case_id=case.case_id,
                    split=case.split,
                    entry_timestamp=_ensure_utc(case.entry_timestamp),
                    exit_timestamp=_ensure_utc(case.exit_timestamp),
                    model_calibrated_through=_ensure_utc(case.model_calibrated_through),
                    legs=legs,
                    commission_per_contract_per_side=case.commission_per_contract_per_side,
                    slippage_per_contract_per_side=case.slippage_per_contract_per_side,
                )
            )
        source = EvidenceReference(
            id=f"MARKETDATA-EOD-BACKTEST-{spec.ticker.upper()}-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
            title=f"MarketData.app EOD option quotes for {spec.ticker.upper()} backtest",
            source_type="marketdata_app_historical_eod_api",
            uri=f"{MARKETDATA_BASE_URL}/v1/options/chain/{spec.ticker.upper()}/",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=retrieved,
            confidence_level="medium",
            notes=(
                f"{request_count} filtered historical chain request(s), {cache_hits} cache hit(s); "
                "EOD bid/ask is not intraday NBBO; IV/Greeks computed locally with QuantLib"
            ),
            used_for_decision=True,
        )
        return BacktestDataset(
            ticker=spec.ticker.upper(),
            as_of=retrieved,
            evidence_class="source_backed_backtest",
            source=source,
            cases=cases,
        )

    def _request(
        self,
        *,
        endpoint: str,
        params: dict[str, str],
        force_refresh: bool,
        fetched_at: datetime,
    ) -> tuple[dict[str, Any], MarketDataRateLimit, bool, datetime]:
        cache_path = self._cache_path(endpoint, params)
        if cache_path.exists() and not force_refresh:
            try:
                envelope = MarketDataCacheEnvelope.model_validate_json(
                    cache_path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeDecodeError, ValidationError) as error:
                raise MarketDataError(
                    f"MarketData.app cache is invalid: {cache_path.name}"
                ) from error
            if envelope.endpoint != endpoint or envelope.params != params:
                raise MarketDataError("MarketData.app cache key does not match cached request")
            if envelope.payload_sha256 != _payload_hash(envelope.payload):
                raise MarketDataError("MarketData.app cache integrity check failed")
            return envelope.payload, envelope.usage, True, envelope.fetched_at

        url = f"{MARKETDATA_BASE_URL}{endpoint}?{urlencode(sorted(params.items()))}"
        response = self._transport.get_json(
            url=url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self._credentials.token}",
                "User-Agent": "take-two-options-read-only/0.4",
            },
            timeout=self.timeout,
        )
        usage = _rate_limit(response.headers)
        envelope = MarketDataCacheEnvelope(
            fetched_at=fetched_at,
            endpoint=endpoint,
            params=params,
            payload=response.payload,
            payload_sha256=_payload_hash(response.payload),
            usage=usage,
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=cache_path.parent,
                prefix=f".{cache_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(envelope.model_dump_json(indent=2))
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.replace(cache_path)
        except OSError as error:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise MarketDataError("Unable to write MarketData.app cache") from error
        return response.payload, usage, False, fetched_at

    def _cache_path(self, endpoint: str, params: dict[str, str]) -> Path:
        request_key = json.dumps(
            {"endpoint": endpoint, "params": params}, sort_keys=True, separators=(",", ":")
        )
        return self.cache_dir / f"{sha256(request_key.encode('utf-8')).hexdigest()}.json"


def _normalize_chain(
    payload: dict[str, Any],
    *,
    ticker: str,
    requested_date: date,
    risk_free_rate: float | None,
    continuous_dividend_yield: float,
    dividends: tuple[tuple[date, float], ...],
    time_grid: int,
    price_grid: int,
) -> list[MarketDataOptionRecord]:
    symbols = _required_array(payload, "optionSymbol")
    if not symbols:
        raise MarketDataError("MarketData.app returned an empty option chain")
    array_fields = (
        "underlying",
        "expiration",
        "side",
        "strike",
        "firstTraded",
        "dte",
        "ask",
        "askSize",
        "bid",
        "bidSize",
        "mid",
        "last",
        "volume",
        "openInterest",
        "underlyingPrice",
        "updated",
        "iv",
        "delta",
        "gamma",
        "theta",
        "vega",
    )
    for name in array_fields:
        values = payload.get(name)
        if values is not None and (not isinstance(values, list) or len(values) != len(symbols)):
            raise MarketDataError(f"MarketData.app field {name} is not aligned with optionSymbol")

    records: list[MarketDataOptionRecord] = []
    for index, raw_symbol in enumerate(symbols):
        symbol = str(raw_symbol)
        parsed = parse_occ_option_symbol(symbol)
        expiration = _required_datetime(_array_item(payload, "expiration", index), "expiration")
        updated = _required_datetime(_array_item(payload, "updated", index), "updated")
        actual_date = updated.astimezone(_NEW_YORK).date()
        if actual_date != requested_date:
            raise MarketDataError(
                f"MarketData.app returned {actual_date} for requested date {requested_date}"
            )
        side = str(_array_item(payload, "side", index) or parsed.option_type.value).lower()
        if side not in {"call", "put"}:
            raise MarketDataError(f"MarketData.app returned invalid option side: {side}")
        option_type = OptionType(side)
        strike = _required_float(_array_item(payload, "strike", index), "strike")
        if option_type is not parsed.option_type or abs(strike - parsed.strike) > 0.0001:
            raise MarketDataError(
                f"MarketData.app contract fields disagree with OCC symbol {symbol}"
            )
        if expiration.astimezone(_NEW_YORK).date() != parsed.expiration:
            raise MarketDataError(f"MarketData.app expiration disagrees with OCC symbol {symbol}")

        bid = _optional_float(_array_item(payload, "bid", index))
        ask = _optional_float(_array_item(payload, "ask", index))
        if bid is not None and ask is not None and ask < bid:
            raise MarketDataError(f"MarketData.app returned crossed bid/ask for {symbol}")
        underlying_price = _optional_float(_array_item(payload, "underlyingPrice", index))
        analytics: HistoricalOptionAnalytics | None = None
        analytics_warning: str | None = None
        if risk_free_rate is not None:
            if bid is None or ask is None or bid <= 0 or ask <= 0:
                analytics_warning = "positive bid and ask are required for local IV"
            elif underlying_price is None:
                analytics_warning = "underlying price is required for local IV"
            else:
                try:
                    analytics = historical_option_analytics(
                        spot=underlying_price,
                        strike=strike,
                        valuation_date=actual_date,
                        expiration_date=parsed.expiration,
                        option_type=option_type,
                        target_price=(bid + ask) / 2.0,
                        rate=risk_free_rate,
                        dividend_yield=continuous_dividend_yield,
                        dividends=dividends,
                        time_grid=time_grid,
                        price_grid=price_grid,
                    )
                except ValueError as error:
                    analytics_warning = str(error)
        try:
            record = MarketDataOptionRecord(
                option_symbol=parsed.symbol,
                underlying=str(_array_item(payload, "underlying", index) or ticker),
                expiration=expiration,
                option_type=option_type,
                strike=strike,
                first_traded=_optional_datetime(_array_item(payload, "firstTraded", index)),
                dte=_optional_int(_array_item(payload, "dte", index)),
                quote_timestamp=updated,
                bid=bid,
                ask=ask,
                bid_size=_optional_float(_array_item(payload, "bidSize", index)),
                ask_size=_optional_float(_array_item(payload, "askSize", index)),
                mid=_optional_float(_array_item(payload, "mid", index)),
                last=_optional_float(_array_item(payload, "last", index)),
                volume=_optional_float(_array_item(payload, "volume", index)),
                open_interest=_optional_float(_array_item(payload, "openInterest", index)),
                underlying_price=underlying_price,
                vendor_implied_volatility=_optional_float(_array_item(payload, "iv", index)),
                vendor_delta=_optional_float(_array_item(payload, "delta", index)),
                vendor_gamma=_optional_float(_array_item(payload, "gamma", index)),
                vendor_theta=_optional_float(_array_item(payload, "theta", index)),
                vendor_vega=_optional_float(_array_item(payload, "vega", index)),
                computed_analytics=analytics,
                analytics_warning=analytics_warning,
            )
        except ValidationError as error:
            raise MarketDataError(
                f"MarketData.app returned invalid values for {parsed.symbol}"
            ) from error
        records.append(record)
    return sorted(records, key=lambda record: record.option_symbol)


def historical_option_quote(record: MarketDataOptionRecord) -> HistoricalOptionQuote:
    """Convert one normalized EOD record to the canonical executable-price proxy."""

    if record.bid is None or record.ask is None:
        raise MarketDataError(f"Missing bid/ask for {record.option_symbol}")
    if record.ask < record.bid:
        raise MarketDataError(f"Crossed bid/ask for {record.option_symbol}")
    return HistoricalOptionQuote(
        timestamp=record.quote_timestamp,
        data_available_at=record.quote_timestamp + timedelta(seconds=1),
        bid=record.bid,
        ask=record.ask,
        bid_size=record.bid_size,
        ask_size=record.ask_size,
        volume=record.volume,
        open_interest=record.open_interest,
        underlying_price=record.underlying_price,
        price_basis="eod_bid_ask",
        source_symbol=record.option_symbol,
        source_feed="marketdata_app_historical_eod",
    )


def _http_error_detail(error: HTTPError) -> str:
    try:
        payload = json.loads(error.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return error.reason or "request failed"
    if isinstance(payload, dict):
        return str(payload.get("errmsg") or payload.get("message") or error.reason)
    return error.reason or "request failed"


def _payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _rate_limit(headers: Mapping[str, str]) -> MarketDataRateLimit:
    normalized = {key.lower(): value for key, value in headers.items()}
    reset = _optional_int(normalized.get("x-api-ratelimit-reset"))
    return MarketDataRateLimit(
        consumed=_optional_int(normalized.get("x-api-ratelimit-consumed")),
        remaining=_optional_int(normalized.get("x-api-ratelimit-remaining")),
        limit=_optional_int(normalized.get("x-api-ratelimit-limit")),
        reset_at=datetime.fromtimestamp(reset, UTC) if reset is not None else None,
    )


def _required_array(payload: dict[str, Any], name: str) -> list[Any]:
    value = payload.get(name)
    if not isinstance(value, list):
        raise MarketDataError(f"MarketData.app field {name} must be an array")
    return value


def _array_item(payload: dict[str, Any], name: str, index: int) -> Any:
    values = payload.get(name)
    return values[index] if isinstance(values, list) else None


def _required_datetime(value: Any, name: str) -> datetime:
    parsed = _optional_datetime(value)
    if parsed is None:
        raise MarketDataError(f"MarketData.app field {name} is required")
    return parsed


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, UTC)
    if isinstance(value, str):
        try:
            return _ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError as error:
            raise MarketDataError(f"Invalid MarketData.app timestamp: {value}") from error
    raise MarketDataError(f"Invalid MarketData.app timestamp type: {type(value).__name__}")


def _required_float(value: Any, name: str) -> float:
    parsed = _optional_float(value)
    if parsed is None:
        raise MarketDataError(f"MarketData.app field {name} is required")
    return parsed


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise MarketDataError(f"Invalid numeric MarketData.app value: {value}") from error
    if not math.isfinite(parsed):
        raise MarketDataError(f"Non-finite MarketData.app value: {value}")
    return parsed


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise MarketDataError(f"Invalid integer MarketData.app value: {value}") from error


def _format_number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
