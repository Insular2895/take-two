"""Read-only IBKR telemetry adapter.

This module deliberately lives outside the execution gateway boundary.  It can read the
paper account, TTWO positions, broker-reported P&L and market-data ticks, but it exposes no
place/modify/cancel operation and is not wired into intent claiming.
"""

from __future__ import annotations

import ipaddress
import math
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol


class ReadOnlyAdapterError(RuntimeError):
    """Fail-closed read-only adapter error with no account or credential detail."""


@dataclass(frozen=True)
class IbkrReadOnlyConfig:
    host: str = "127.0.0.1"
    port: int = 4002
    client_id: int = 901
    symbol: str = "TTWO"
    timeout_seconds: float = 15.0

    def validate(self) -> None:
        try:
            loopback = ipaddress.ip_address(self.host).is_loopback
        except ValueError:
            loopback = self.host == "localhost"
        if not loopback:
            raise ValueError("IBKR read-only telemetry must use a loopback host")
        if self.port != 4002:
            raise ValueError("IBKR read-only telemetry accepts only the paper Gateway port 4002")
        if self.client_id <= 0:
            raise ValueError("IBKR client_id must be positive")
        if self.symbol != "TTWO":
            raise ValueError("read-only telemetry is restricted to TTWO")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds < 2:
            raise ValueError("IBKR timeout_seconds must be finite and at least 2")


@dataclass(frozen=True)
class RawPosition:
    account: str
    con_id: int
    symbol: str
    security_type: str
    local_symbol: str
    currency: str
    expiry: str
    strike: Decimal | None
    right: str
    multiplier: str
    quantity: Decimal
    average_cost: Decimal | None


@dataclass(frozen=True)
class RawPositionPnl:
    account: str
    con_id: int
    daily_pnl: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal | None
    market_value: Decimal | None


@dataclass(frozen=True)
class RawQuote:
    con_id: int
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    close: Decimal | None
    mark: Decimal | None
    market_data_type: int | None
    observed_at: datetime


@dataclass(frozen=True)
class RawIbkrSnapshot:
    gateway_connected: bool
    accounts: tuple[str, ...]
    server_time_epoch: int | None
    positions: tuple[RawPosition, ...]
    position_pnl: tuple[RawPositionPnl, ...]
    quotes: tuple[RawQuote, ...]
    error_codes: tuple[int, ...]
    collected_at: datetime


class RawSnapshotCollector(Protocol):
    def collect(self) -> RawIbkrSnapshot: ...


@dataclass(frozen=True)
class QuoteTelemetry:
    bid: Decimal | None
    ask: Decimal | None
    last: Decimal | None
    close: Decimal | None
    mark: Decimal | None
    midpoint: Decimal | None
    market_data_type: str
    observed_at: datetime

    @property
    def bid_ask_complete(self) -> bool:
        return self.bid is not None and self.ask is not None

    def as_payload(self) -> dict[str, Any]:
        return {
            "bid": _decimal_text(self.bid),
            "ask": _decimal_text(self.ask),
            "last": _decimal_text(self.last),
            "close": _decimal_text(self.close),
            "mark": _decimal_text(self.mark),
            "midpoint": _decimal_text(self.midpoint),
            "market_data_type": self.market_data_type,
            "observed_at": _iso(self.observed_at),
            "bid_ask_complete": self.bid_ask_complete,
        }


@dataclass(frozen=True)
class PositionTelemetry:
    con_id: int
    security_type: str
    local_symbol: str
    currency: str
    expiry: str
    strike: Decimal | None
    right: str
    multiplier: str
    quantity: Decimal
    average_cost: Decimal | None
    market_value: Decimal | None
    daily_pnl: Decimal | None
    unrealized_pnl: Decimal | None
    realized_pnl: Decimal | None
    quote: QuoteTelemetry | None

    def as_payload(self) -> dict[str, Any]:
        return {
            "con_id": self.con_id,
            "security_type": self.security_type,
            "local_symbol": self.local_symbol,
            "currency": self.currency,
            "expiry": self.expiry,
            "strike": _decimal_text(self.strike),
            "right": self.right,
            "multiplier": self.multiplier,
            "quantity": _decimal_text(self.quantity),
            "average_cost": _decimal_text(self.average_cost),
            "market_value": _decimal_text(self.market_value),
            "daily_pnl": _decimal_text(self.daily_pnl),
            "unrealized_pnl": _decimal_text(self.unrealized_pnl),
            "realized_pnl": _decimal_text(self.realized_pnl),
            "quote": None if self.quote is None else self.quote.as_payload(),
        }


@dataclass(frozen=True)
class PortfolioTelemetry:
    gateway_connected: bool
    paper_account_verified: bool
    account_count: int
    symbol: str
    server_time: datetime
    collected_at: datetime
    positions: tuple[PositionTelemetry, ...]
    total_market_value: Decimal | None
    total_daily_pnl: Decimal | None
    total_unrealized_pnl: Decimal | None
    total_realized_pnl: Decimal | None
    quotes_complete: bool
    pnl_complete: bool
    fee_reconciliation_status: str
    error_codes: tuple[int, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "mode": "PAPER_READ_ONLY",
            "gateway_connected": self.gateway_connected,
            "paper_account_verified": self.paper_account_verified,
            "account_count": self.account_count,
            "symbol": self.symbol,
            "server_time": _iso(self.server_time),
            "collected_at": _iso(self.collected_at),
            "positions": [position.as_payload() for position in self.positions],
            "totals": {
                "market_value": _decimal_text(self.total_market_value),
                "daily_pnl": _decimal_text(self.total_daily_pnl),
                "unrealized_pnl": _decimal_text(self.total_unrealized_pnl),
                "realized_pnl": _decimal_text(self.total_realized_pnl),
            },
            "quotes_complete": self.quotes_complete,
            "pnl_complete": self.pnl_complete,
            "fee_reconciliation_status": self.fee_reconciliation_status,
            "error_codes": list(self.error_codes),
        }


class IbkrReadOnlyAdapter:
    """Validate and redact a one-shot official-IBKR telemetry snapshot."""

    def __init__(
        self,
        config: IbkrReadOnlyConfig,
        collector: RawSnapshotCollector | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._collector = collector or OfficialIbapiCollector(config)

    def snapshot(self) -> PortfolioTelemetry:
        raw = self._collector.collect()
        if not raw.gateway_connected:
            raise ReadOnlyAdapterError("IBKR_GATEWAY_NOT_CONNECTED")
        if len(raw.accounts) != 1:
            raise ReadOnlyAdapterError("IBKR_PAPER_ACCOUNT_SCOPE_AMBIGUOUS")
        if not raw.accounts[0].startswith("DU"):
            raise ReadOnlyAdapterError("IBKR_LIVE_ACCOUNT_FORBIDDEN")
        if raw.server_time_epoch is None or raw.server_time_epoch <= 0:
            raise ReadOnlyAdapterError("IBKR_SERVER_TIME_MISSING")

        account = raw.accounts[0]
        if any(position.account != account for position in raw.positions):
            raise ReadOnlyAdapterError("IBKR_POSITION_ACCOUNT_MISMATCH")
        if any(pnl.account != account for pnl in raw.position_pnl):
            raise ReadOnlyAdapterError("IBKR_PNL_ACCOUNT_MISMATCH")

        relevant = tuple(
            position
            for position in raw.positions
            if position.symbol == self._config.symbol and position.quantity != 0
        )
        con_ids = [position.con_id for position in relevant]
        if len(con_ids) != len(set(con_ids)):
            raise ReadOnlyAdapterError("IBKR_DUPLICATE_POSITION_CON_ID")

        pnl_by_con_id = {item.con_id: item for item in raw.position_pnl}
        quote_by_con_id = {item.con_id: item for item in raw.quotes}
        positions: list[PositionTelemetry] = []
        for position in relevant:
            pnl = pnl_by_con_id.get(position.con_id)
            quote = _normalise_quote(quote_by_con_id.get(position.con_id))
            positions.append(
                PositionTelemetry(
                    con_id=position.con_id,
                    security_type=position.security_type,
                    local_symbol=position.local_symbol,
                    currency=position.currency,
                    expiry=position.expiry,
                    strike=position.strike,
                    right=position.right,
                    multiplier=position.multiplier,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    market_value=None if pnl is None else pnl.market_value,
                    daily_pnl=None if pnl is None else pnl.daily_pnl,
                    unrealized_pnl=None if pnl is None else pnl.unrealized_pnl,
                    realized_pnl=None if pnl is None else pnl.realized_pnl,
                    quote=quote,
                )
            )

        position_tuple = tuple(positions)
        pnl_complete = all(
            position.market_value is not None
            and position.daily_pnl is not None
            and position.unrealized_pnl is not None
            and position.realized_pnl is not None
            for position in position_tuple
        )
        quotes_complete = all(
            position.quote is not None and position.quote.bid_ask_complete
            for position in position_tuple
        )
        return PortfolioTelemetry(
            gateway_connected=True,
            paper_account_verified=True,
            account_count=1,
            symbol=self._config.symbol,
            server_time=datetime.fromtimestamp(raw.server_time_epoch, tz=UTC),
            collected_at=raw.collected_at.astimezone(UTC),
            positions=position_tuple,
            total_market_value=_complete_sum(position_tuple, "market_value"),
            total_daily_pnl=_complete_sum(position_tuple, "daily_pnl"),
            total_unrealized_pnl=_complete_sum(position_tuple, "unrealized_pnl"),
            total_realized_pnl=_complete_sum(position_tuple, "realized_pnl"),
            quotes_complete=quotes_complete,
            pnl_complete=pnl_complete,
            fee_reconciliation_status="LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES",
            error_codes=tuple(sorted(set(raw.error_codes))),
        )


class OfficialIbapiCollector:
    """One-shot collector backed by the official locally installed ``ibapi`` package."""

    def __init__(self, config: IbkrReadOnlyConfig) -> None:
        config.validate()
        self._config = config

    def collect(self) -> RawIbkrSnapshot:
        try:
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
        except ImportError as error:
            raise ReadOnlyAdapterError("OFFICIAL_IBAPI_NOT_INSTALLED") from error

        config = self._config

        class Collector(EWrapper, EClient):  # type: ignore[misc, valid-type]
            def __init__(self) -> None:
                EClient.__init__(self, self)
                self.ready = threading.Event()
                self.accounts_ready = threading.Event()
                self.server_time_ready = threading.Event()
                self.positions_ready = threading.Event()
                self.accounts: tuple[str, ...] = ()
                self.server_time_epoch: int | None = None
                self.positions: list[RawPosition] = []
                self.contracts: dict[int, object] = {}
                self.pnl_request_keys: dict[int, tuple[str, int]] = {}
                self.pnl_events: dict[int, threading.Event] = {}
                self.pnl: dict[tuple[str, int], RawPositionPnl] = {}
                self.quote_request_keys: dict[int, int] = {}
                self.quote_events: dict[int, threading.Event] = {}
                self.quote_values: dict[int, dict[str, Decimal]] = {}
                self.market_data_types: dict[int, int] = {}
                self.quote_observed_at: dict[int, datetime] = {}
                self.error_codes: list[int] = []

            def nextValidId(self, orderId: int) -> None:
                self.ready.set()

            def managedAccounts(self, accountsList: str) -> None:
                self.accounts = tuple(
                    account.strip() for account in accountsList.split(",") if account.strip()
                )
                self.accounts_ready.set()

            def currentTime(self, server_time: int) -> None:
                self.server_time_epoch = server_time
                self.server_time_ready.set()

            def position(
                self,
                account: str,
                contract: object,
                quantity: object,
                avg_cost: float,
            ) -> None:
                symbol = str(getattr(contract, "symbol", "")).upper()
                con_id = int(getattr(contract, "conId", 0))
                if con_id <= 0:
                    self.error_codes.append(-1001)
                    return
                self.contracts[con_id] = contract
                self.positions.append(
                    RawPosition(
                        account=account,
                        con_id=con_id,
                        symbol=symbol,
                        security_type=str(getattr(contract, "secType", "")),
                        local_symbol=str(getattr(contract, "localSymbol", "")),
                        currency=str(getattr(contract, "currency", "")),
                        expiry=str(getattr(contract, "lastTradeDateOrContractMonth", "")),
                        strike=_decimal_or_none(getattr(contract, "strike", None)),
                        right=str(getattr(contract, "right", "")),
                        multiplier=str(getattr(contract, "multiplier", "")),
                        quantity=Decimal(str(quantity)),
                        average_cost=_decimal_or_none(avg_cost),
                    )
                )

            def positionEnd(self) -> None:
                self.positions_ready.set()

            def pnlSingle(
                self,
                reqId: int,
                pos: object,
                dailyPnL: float,
                unrealizedPnL: float,
                realizedPnL: float,
                value: float,
            ) -> None:
                key = self.pnl_request_keys.get(reqId)
                if key is None:
                    return
                self.pnl[key] = RawPositionPnl(
                    account=key[0],
                    con_id=key[1],
                    daily_pnl=_decimal_or_none(dailyPnL),
                    unrealized_pnl=_decimal_or_none(unrealizedPnL),
                    realized_pnl=_decimal_or_none(realizedPnL),
                    market_value=_decimal_or_none(value),
                )
                self.pnl_events[reqId].set()

            def marketDataType(self, reqId: int, marketDataType: int) -> None:
                self.market_data_types[reqId] = marketDataType

            def tickPrice(
                self,
                reqId: int,
                tickType: int,
                price: float,
                attrib: object,
            ) -> None:
                field = _TICK_PRICE_FIELDS.get(tickType)
                cleaned = _positive_decimal_or_none(price)
                if field is None or cleaned is None or reqId not in self.quote_events:
                    return
                self.quote_values.setdefault(reqId, {})[field] = cleaned
                self.quote_observed_at[reqId] = datetime.now(UTC)
                values = self.quote_values[reqId]
                if {"bid", "ask"} <= values.keys() or any(
                    name in values for name in ("last", "mark", "close")
                ):
                    self.quote_events[reqId].set()

            def error(
                self,
                reqId: int,
                errorTime: int,
                errorCode: int,
                errorString: str,
                advancedOrderRejectJson: str = "",
            ) -> None:
                self.error_codes.append(errorCode)

        app = Collector()
        thread: threading.Thread | None = None
        pnl_request_ids: list[int] = []
        quote_request_ids: list[int] = []
        try:
            app.connect(config.host, config.port, clientId=config.client_id)
            thread = threading.Thread(target=app.run, daemon=True, name="ibkr-readonly-api")
            thread.start()
            _wait_for(
                (app.ready, app.accounts_ready),
                config.timeout_seconds,
                "IBKR_HANDSHAKE_TIMEOUT",
            )
            if len(app.accounts) != 1:
                raise ReadOnlyAdapterError("IBKR_PAPER_ACCOUNT_SCOPE_AMBIGUOUS")
            if not app.accounts[0].startswith("DU"):
                raise ReadOnlyAdapterError("IBKR_LIVE_ACCOUNT_FORBIDDEN")
            app.reqCurrentTime()
            app.reqPositions()
            _wait_for(
                (app.server_time_ready, app.positions_ready),
                config.timeout_seconds,
                "IBKR_BASE_SNAPSHOT_TIMEOUT",
            )

            relevant = [
                position
                for position in app.positions
                if position.symbol == config.symbol and position.quantity != 0
            ]
            app.reqMarketDataType(3)
            for offset, position in enumerate(relevant):
                pnl_request_id = 20_000 + offset
                quote_request_id = 30_000 + offset
                pnl_request_ids.append(pnl_request_id)
                quote_request_ids.append(quote_request_id)
                app.pnl_request_keys[pnl_request_id] = (position.account, position.con_id)
                app.pnl_events[pnl_request_id] = threading.Event()
                app.quote_request_keys[quote_request_id] = position.con_id
                app.quote_events[quote_request_id] = threading.Event()
                app.reqPnLSingle(pnl_request_id, position.account, "", position.con_id)
                contract = app.contracts[position.con_id]
                if not getattr(contract, "exchange", "") and position.security_type in {
                    "OPT",
                    "STK",
                }:
                    contract.exchange = "SMART"
                app.reqMktData(quote_request_id, contract, "", False, False, [])

            _wait_until_deadline(
                tuple(app.pnl_events.values()) + tuple(app.quote_events.values()),
                config.timeout_seconds,
            )
            quotes = tuple(
                _raw_quote(app, request_id, con_id)
                for request_id, con_id in app.quote_request_keys.items()
            )
            return RawIbkrSnapshot(
                gateway_connected=app.isConnected(),
                accounts=app.accounts,
                server_time_epoch=app.server_time_epoch,
                positions=tuple(app.positions),
                position_pnl=tuple(app.pnl.values()),
                quotes=quotes,
                error_codes=tuple(app.error_codes),
                collected_at=datetime.now(UTC),
            )
        except ReadOnlyAdapterError:
            raise
        except Exception as error:
            raise ReadOnlyAdapterError("IBKR_READ_ONLY_COLLECTION_FAILED") from error
        finally:
            for request_id in pnl_request_ids:
                if app.isConnected():
                    app.cancelPnLSingle(request_id)
            for request_id in quote_request_ids:
                if app.isConnected():
                    app.cancelMktData(request_id)
            if app.isConnected():
                app.cancelPositions()
                app.disconnect()
            if thread is not None:
                thread.join(timeout=2)


def _raw_quote(app: Any, request_id: int, con_id: int) -> RawQuote:
    values: Mapping[str, Decimal] = app.quote_values.get(request_id, {})
    return RawQuote(
        con_id=con_id,
        bid=values.get("bid"),
        ask=values.get("ask"),
        last=values.get("last"),
        close=values.get("close"),
        mark=values.get("mark"),
        market_data_type=app.market_data_types.get(request_id),
        observed_at=app.quote_observed_at.get(request_id, datetime.now(UTC)),
    )


def _wait_for(events: Sequence[threading.Event], timeout: float, code: str) -> None:
    _wait_until_deadline(events, timeout)
    if not all(event.is_set() for event in events):
        raise ReadOnlyAdapterError(code)


def _wait_until_deadline(events: Sequence[threading.Event], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not all(event.is_set() for event in events):
        time.sleep(0.05)


def _normalise_quote(raw: RawQuote | None) -> QuoteTelemetry | None:
    if raw is None:
        return None
    midpoint = None
    if raw.bid is not None and raw.ask is not None and raw.ask >= raw.bid:
        midpoint = (raw.bid + raw.ask) / Decimal(2)
    return QuoteTelemetry(
        bid=raw.bid,
        ask=raw.ask,
        last=raw.last,
        close=raw.close,
        mark=raw.mark,
        midpoint=midpoint,
        market_data_type=_MARKET_DATA_TYPES.get(raw.market_data_type, "UNKNOWN"),
        observed_at=raw.observed_at.astimezone(UTC),
    )


def _complete_sum(positions: Sequence[PositionTelemetry], field: str) -> Decimal | None:
    values = [getattr(position, field) for position in positions]
    if any(value is None for value in values):
        return None
    return sum((value for value in values if value is not None), Decimal(0))


def _decimal_or_none(value: object) -> Decimal | None:
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not decimal.is_finite() or abs(decimal) > Decimal("1e100"):
        return None
    return decimal


def _positive_decimal_or_none(value: object) -> Decimal | None:
    decimal = _decimal_or_none(value)
    return decimal if decimal is not None and decimal > 0 else None


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


_TICK_PRICE_FIELDS = {
    1: "bid",
    2: "ask",
    4: "last",
    9: "close",
    37: "mark",
    66: "bid",
    67: "ask",
    68: "last",
    75: "close",
}

_MARKET_DATA_TYPES = {
    1: "REALTIME",
    2: "FROZEN",
    3: "DELAYED",
    4: "DELAYED_FROZEN",
}
