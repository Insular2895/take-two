"""Narrow, read-only Alpaca market-data integration.

This module deliberately imports historical market-data clients only. It contains no trading
client, order request, position mutation, or exercise endpoint.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Literal, Protocol, cast

from alpaca.common.enums import Sort
from alpaca.data.enums import Adjustment, DataFeed, OptionsFeed
from alpaca.data.historical import OptionHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import OptionBarsRequest, OptionChainRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.enums import ContractType
from pydantic import Field, model_validator

from take_two_options.backtesting import (
    BacktestCase,
    BacktestDataset,
    BacktestLeg,
    HistoricalOptionQuote,
)
from take_two_options.calibration import CalibrationDataset, HistoricalPricePoint
from take_two_options.domain import EvidenceReference, EvidenceStatus, PositionSide, StrictModel

ALPACA_OPTION_HISTORY_START = datetime(2024, 2, 1, tzinfo=UTC)


class AlpacaDataError(RuntimeError):
    """Raised when real-data ingestion cannot preserve its declared contract."""


@dataclass(frozen=True)
class AlpacaCredentials:
    key_id: str = field(repr=False)
    secret_key: str = field(repr=False)

    @classmethod
    def from_env(cls) -> AlpacaCredentials:
        key_id = os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET")
        if not key_id or not secret_key:
            raise AlpacaDataError(
                "Alpaca credentials are missing; set APCA_API_KEY_ID and "
                "APCA_API_SECRET_KEY in the environment"
            )
        return cls(key_id=key_id, secret_key=secret_key)


class StockBarsClient(Protocol):
    def get_stock_bars(self, request_params: Any) -> Any: ...


class OptionBarsClient(Protocol):
    def get_option_bars(self, request_params: Any) -> Any: ...

    def get_option_chain(self, request_params: Any) -> Any: ...


class AlpacaBarRecord(StrictModel):
    symbol: str = Field(min_length=1)
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    trade_count: float | None = Field(default=None, ge=0)
    vwap: float | None = Field(default=None, gt=0)


class AlpacaConnectionReport(StrictModel):
    connected: bool
    ticker: str
    stock_feed: str
    bars_received: int = Field(ge=0)
    newest_bar: datetime | None = None
    checked_at: datetime
    order_capability: Literal["forbidden"] = "forbidden"


class AlpacaOptionChainRecord(StrictModel):
    symbol: str = Field(min_length=1)
    quote_timestamp: datetime | None = None
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)
    trade_timestamp: datetime | None = None
    last: float | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0)
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


class AlpacaOptionChainExport(StrictModel):
    ticker: str
    feed: Literal["indicative", "opra"]
    retrieved_at: datetime
    source: EvidenceReference
    contracts: list[AlpacaOptionChainRecord]
    order_capability: Literal["forbidden"] = "forbidden"


class AlpacaBacktestLegSpec(StrictModel):
    symbol: str = Field(min_length=15)
    side: PositionSide
    quantity: int = Field(default=1, gt=0)
    multiplier: float = Field(default=100.0, gt=0)


class AlpacaBacktestCaseSpec(StrictModel):
    case_id: str = Field(min_length=1)
    split: Literal["train", "test"]
    entry_timestamp: datetime
    exit_timestamp: datetime
    model_calibrated_through: datetime
    legs: list[AlpacaBacktestLegSpec] = Field(min_length=1)
    commission_per_contract_per_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_per_side: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_timeline(self) -> AlpacaBacktestCaseSpec:
        if _ensure_utc(self.entry_timestamp) < ALPACA_OPTION_HISTORY_START:
            raise ValueError("Alpaca option history starts in February 2024")
        if self.exit_timestamp <= self.entry_timestamp:
            raise ValueError("backtest exit must follow entry")
        if self.model_calibrated_through >= self.entry_timestamp:
            raise ValueError("model calibration must end before entry")
        return self


class AlpacaOptionBacktestSpec(StrictModel):
    ticker: str = Field(min_length=1)
    timeframe: Literal["1Min", "1Hour", "1Day"] = "1Day"
    cases: list[AlpacaBacktestCaseSpec] = Field(min_length=2)
    notes: str = ""

    @model_validator(mode="after")
    def validate_splits(self) -> AlpacaOptionBacktestSpec:
        if {case.split for case in self.cases} != {"train", "test"}:
            raise ValueError("Alpaca backtest spec requires train and test cases")
        return self


_TIMEFRAMES = {
    "1Min": TimeFrame.Minute,
    "1Hour": TimeFrame.Hour,
    "1Day": TimeFrame.Day,
}

_AVAILABILITY_LAGS = {
    "1Min": timedelta(minutes=1),
    "1Hour": timedelta(hours=1),
    "1Day": timedelta(days=1),
}


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _field(source: Any, name: str, alias: str | None = None) -> Any:
    if isinstance(source, dict):
        if name in source:
            return source[name]
        if alias is not None and alias in source:
            return source[alias]
        return None
    return getattr(source, name, None)


def _response_data(response: Any) -> dict[str, list[Any]]:
    data = getattr(response, "data", None)
    if isinstance(data, dict):
        return data
    if isinstance(response, dict):
        bars = response.get("bars", response)
        if isinstance(bars, dict):
            return bars
    raise AlpacaDataError("Unexpected Alpaca bar response shape")


def _normalize_bars(response: Any) -> dict[str, list[AlpacaBarRecord]]:
    normalized: dict[str, list[AlpacaBarRecord]] = {}
    for symbol, raw_bars in _response_data(response).items():
        records = [
            AlpacaBarRecord(
                symbol=str(_field(bar, "symbol") or symbol),
                timestamp=_ensure_utc(_field(bar, "timestamp", "t")),
                open=float(_field(bar, "open", "o")),
                high=float(_field(bar, "high", "h")),
                low=float(_field(bar, "low", "l")),
                close=float(_field(bar, "close", "c")),
                volume=float(_field(bar, "volume", "v")),
                trade_count=_field(bar, "trade_count", "n"),
                vwap=_field(bar, "vwap", "vw"),
            )
            for bar in raw_bars
        ]
        normalized[symbol] = sorted(records, key=lambda record: record.timestamp)
    return normalized


class AlpacaReadOnlyMarketData:
    """Read-only facade over Alpaca stock and option market-data clients."""

    def __init__(
        self,
        *,
        stock_client: StockBarsClient,
        option_client: OptionBarsClient,
        options_feed_label: Literal["indicative", "opra"] = "indicative",
    ) -> None:
        self._stock_client = stock_client
        self._option_client = option_client
        self.options_feed_label = options_feed_label

    @classmethod
    def from_env(cls) -> AlpacaReadOnlyMarketData:
        credentials = AlpacaCredentials.from_env()
        feed_label = os.getenv("ALPACA_OPTIONS_FEED", "indicative").lower()
        if feed_label not in {"indicative", "opra"}:
            raise AlpacaDataError("ALPACA_OPTIONS_FEED must be indicative or opra")
        return cls(
            stock_client=StockHistoricalDataClient(
                api_key=credentials.key_id,
                secret_key=credentials.secret_key,
            ),
            option_client=OptionHistoricalDataClient(
                api_key=credentials.key_id,
                secret_key=credentials.secret_key,
            ),
            options_feed_label=cast(Literal["indicative", "opra"], feed_label),
        )

    def stock_bars(
        self,
        *,
        ticker: str,
        start: datetime,
        end: datetime,
        feed: Literal["iex", "sip"] = "iex",
    ) -> list[AlpacaBarRecord]:
        request = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=TimeFrame.Day,
            start=_ensure_utc(start),
            end=_ensure_utc(end),
            adjustment=Adjustment.ALL,
            feed=DataFeed(feed),
            sort=Sort.ASC,
        )
        response = self._stock_client.get_stock_bars(request)
        return _normalize_bars(response).get(ticker, [])

    def option_bars(
        self,
        *,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: Literal["1Min", "1Hour", "1Day"],
    ) -> dict[str, list[AlpacaBarRecord]]:
        if _ensure_utc(start) < ALPACA_OPTION_HISTORY_START:
            raise AlpacaDataError("Alpaca option history starts in February 2024")
        if len(symbols) > 100:
            raise AlpacaDataError("Alpaca option-bar requests support at most 100 symbols")
        request = OptionBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=_TIMEFRAMES[timeframe],
            start=_ensure_utc(start),
            end=_ensure_utc(end),
            sort=Sort.ASC,
        )
        response = self._option_client.get_option_bars(request)
        return _normalize_bars(response)

    def check_connection(
        self,
        *,
        ticker: str = "TTWO",
        feed: Literal["iex", "sip"] = "iex",
        checked_at: datetime | None = None,
    ) -> AlpacaConnectionReport:
        now = _ensure_utc(checked_at or datetime.now(UTC))
        bars = self.stock_bars(ticker=ticker, start=now - timedelta(days=14), end=now, feed=feed)
        if not bars:
            raise AlpacaDataError(f"Alpaca returned no daily bars for {ticker}")
        return AlpacaConnectionReport(
            connected=True,
            ticker=ticker,
            stock_feed=feed,
            bars_received=len(bars),
            newest_bar=bars[-1].timestamp,
            checked_at=now,
        )

    def calibration_dataset(
        self,
        *,
        ticker: str,
        start: datetime,
        end: datetime,
        training_cutoff: datetime,
        feed: Literal["iex", "sip"] = "iex",
        retrieved_at: datetime | None = None,
        jump_threshold_sigma: float = 2.5,
    ) -> CalibrationDataset:
        retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
        bars = self.stock_bars(ticker=ticker, start=start, end=end, feed=feed)
        if len(bars) < 8:
            raise AlpacaDataError("At least eight Alpaca daily bars are required for calibration")
        confidence: Literal["medium", "high"] = "high" if feed == "sip" else "medium"
        source = EvidenceReference(
            id=f"ALPACA-STOCK-BARS-{ticker}-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
            title=f"Alpaca adjusted daily bars for {ticker}",
            source_type="alpaca_market_data_api",
            uri="https://data.alpaca.markets/v2/stocks/bars",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=retrieved,
            confidence_level=confidence,
            notes=f"Real Alpaca {feed} daily bars; adjustment=all; no order capability",
            used_for_decision=True,
        )
        return CalibrationDataset(
            ticker=ticker,
            as_of=retrieved,
            training_cutoff=_ensure_utc(training_cutoff),
            evidence_class="source_backed_calibration",
            source=source,
            points=[
                HistoricalPricePoint(
                    timestamp=bar.timestamp,
                    data_available_at=bar.timestamp + timedelta(days=1),
                    close=bar.close,
                )
                for bar in bars
            ],
            jump_threshold_sigma=jump_threshold_sigma,
        )

    def option_backtest_dataset(
        self,
        spec: AlpacaOptionBacktestSpec,
        *,
        retrieved_at: datetime | None = None,
    ) -> BacktestDataset:
        retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
        symbols = sorted({leg.symbol for case in spec.cases for leg in case.legs})
        earliest = min(_ensure_utc(case.entry_timestamp) for case in spec.cases)
        latest = max(_ensure_utc(case.exit_timestamp) for case in spec.cases)
        lookback = timedelta(days=7) if spec.timeframe == "1Day" else timedelta(days=1)
        bars_by_symbol = self.option_bars(
            symbols=symbols,
            start=max(earliest - lookback, ALPACA_OPTION_HISTORY_START),
            end=latest,
            timeframe=spec.timeframe,
        )
        missing = [symbol for symbol in symbols if not bars_by_symbol.get(symbol)]
        if missing:
            raise AlpacaDataError(f"No Alpaca option bars returned for: {', '.join(missing)}")

        source = EvidenceReference(
            id=f"ALPACA-OPTION-BARS-{spec.ticker}-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
            title=f"Alpaca historical option bars for {spec.ticker}",
            source_type="alpaca_market_data_api",
            uri="https://data.alpaca.markets/v1beta1/options/bars",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=retrieved,
            confidence_level=("high" if self.options_feed_label == "opra" else "medium"),
            notes=(
                f"Real option transaction bars; declared entitlement={self.options_feed_label}; "
                "historical endpoint exposes no feed selector; closes are execution proxies"
            ),
            used_for_decision=True,
        )
        cases: list[BacktestCase] = []
        for case in spec.cases:
            legs: list[BacktestLeg] = []
            for leg in case.legs:
                entry_bar = _latest_available_bar(
                    bars_by_symbol[leg.symbol], case.entry_timestamp, spec.timeframe
                )
                exit_bar = _latest_available_bar(
                    bars_by_symbol[leg.symbol], case.exit_timestamp, spec.timeframe
                )
                if entry_bar is None or exit_bar is None:
                    raise AlpacaDataError(
                        f"No look-ahead-safe {spec.timeframe} bar for {leg.symbol} in "
                        f"case {case.case_id}"
                    )
                legs.append(
                    BacktestLeg(
                        side=leg.side,
                        quantity=leg.quantity,
                        multiplier=leg.multiplier,
                        entry_quote=_bar_proxy_quote(
                            entry_bar, spec.timeframe, self.options_feed_label
                        ),
                        exit_quote=_bar_proxy_quote(
                            exit_bar, spec.timeframe, self.options_feed_label
                        ),
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
        return BacktestDataset(
            ticker=spec.ticker,
            as_of=retrieved,
            evidence_class="source_backed_backtest",
            source=source,
            cases=cases,
        )

    def option_chain(
        self,
        *,
        ticker: str,
        feed: Literal["indicative", "opra"] = "indicative",
        expiration_date_gte: date | None = None,
        expiration_date_lte: date | None = None,
        strike_price_gte: float | None = None,
        strike_price_lte: float | None = None,
        option_type: Literal["call", "put"] | None = None,
        retrieved_at: datetime | None = None,
    ) -> AlpacaOptionChainExport:
        retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
        request = OptionChainRequest(
            underlying_symbol=ticker,
            feed=OptionsFeed(feed),
            expiration_date_gte=expiration_date_gte,
            expiration_date_lte=expiration_date_lte,
            strike_price_gte=strike_price_gte,
            strike_price_lte=strike_price_lte,
            type=ContractType(option_type) if option_type else None,
        )
        response = self._option_client.get_option_chain(request)
        if not isinstance(response, dict):
            raise AlpacaDataError("Unexpected Alpaca option-chain response shape")
        records = [_normalize_snapshot(symbol, snapshot) for symbol, snapshot in response.items()]
        source = EvidenceReference(
            id=f"ALPACA-OPTION-CHAIN-{ticker}-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
            title=f"Alpaca latest option chain for {ticker}",
            source_type="alpaca_market_data_api",
            uri=f"https://data.alpaca.markets/v1beta1/options/snapshots/{ticker}",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=retrieved,
            confidence_level="high" if feed == "opra" else "medium",
            notes=(
                "OPRA consolidated data" if feed == "opra" else "Free indicative derivative feed"
            ),
            used_for_decision=True,
        )
        return AlpacaOptionChainExport(
            ticker=ticker,
            feed=feed,
            retrieved_at=retrieved,
            source=source,
            contracts=sorted(records, key=lambda record: record.symbol),
        )


def _bar_available_at(bar: AlpacaBarRecord, timeframe: str) -> datetime:
    return bar.timestamp + _AVAILABILITY_LAGS[timeframe]


def _latest_available_bar(
    bars: list[AlpacaBarRecord], target: datetime, timeframe: str
) -> AlpacaBarRecord | None:
    cutoff = _ensure_utc(target)
    eligible = [bar for bar in bars if _bar_available_at(bar, timeframe) <= cutoff]
    return eligible[-1] if eligible else None


def _bar_proxy_quote(
    bar: AlpacaBarRecord,
    timeframe: str,
    source_feed: str,
) -> HistoricalOptionQuote:
    return HistoricalOptionQuote(
        timestamp=bar.timestamp,
        data_available_at=_bar_available_at(bar, timeframe),
        bid=bar.close,
        ask=bar.close,
        price_basis="option_bar_close_proxy",
        source_symbol=bar.symbol,
        source_feed=source_feed,
    )


def _normalize_snapshot(symbol: str, snapshot: Any) -> AlpacaOptionChainRecord:
    quote = _field(snapshot, "latest_quote")
    trade = _field(snapshot, "latest_trade")
    greeks = _field(snapshot, "greeks")
    return AlpacaOptionChainRecord(
        symbol=symbol,
        quote_timestamp=(
            _ensure_utc(_field(quote, "timestamp", "t")) if quote is not None else None
        ),
        bid=_field(quote, "bid_price", "bp") if quote is not None else None,
        ask=_field(quote, "ask_price", "ap") if quote is not None else None,
        bid_size=_field(quote, "bid_size", "bs") if quote is not None else None,
        ask_size=_field(quote, "ask_size", "as") if quote is not None else None,
        trade_timestamp=(
            _ensure_utc(_field(trade, "timestamp", "t")) if trade is not None else None
        ),
        last=_field(trade, "price", "p") if trade is not None else None,
        implied_volatility=_field(snapshot, "implied_volatility", "impliedVolatility"),
        delta=_field(greeks, "delta") if greeks is not None else None,
        gamma=_field(greeks, "gamma") if greeks is not None else None,
        theta=_field(greeks, "theta") if greeks is not None else None,
        vega=_field(greeks, "vega") if greeks is not None else None,
        rho=_field(greeks, "rho") if greeks is not None else None,
    )
