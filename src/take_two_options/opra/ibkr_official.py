"""Official TWS API transport for read-only IBKR option market data.

The official ``ibapi`` package is intentionally not declared as a PyPI dependency.  IBKR
distributes it with the user-accepted TWS API download; this module imports it only when a
human explicitly invokes the live read-only command.

This file contains market-data requests only.  It imports no order type and has no order,
cancel, exercise or account-mutation method.
"""

from __future__ import annotations

import ipaddress
import math
import threading
import time
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from typing import Any

from take_two_options.opra.contracts import (
    IbkrTwsProviderConfig,
    LiveChainRequest,
    LiveComboQuoteRequest,
)
from take_two_options.opra.ibkr_provider import (
    IbkrProviderError,
    IbkrTransientError,
    RawIbkrChainSnapshot,
    RawIbkrComboQuote,
    RawIbkrHealth,
    RawIbkrOptionContract,
    RawIbkrOptionQuote,
)

_INFORMATIONAL_CODES = {2104, 2106, 2107, 2108, 2158}
_TRANSIENT_CODES = {502, 504, 1100, 1101, 1102, 1300}
_MARKET_DATA_TYPES = {
    1: "live",
    2: "frozen",
    3: "delayed",
    4: "delayed_frozen",
}
_REQUESTED_DATA_TYPES = {
    "live": 1,
    "frozen": 2,
    "delayed": 3,
    "delayed_frozen": 4,
}


class OfficialIbkrReadOnlyTransport:
    """One-session-per-operation transport with bounded snapshot batches."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        quote_batch_size: int = 35,
        request_spacing_seconds: float = 0.025,
        combo_price_convention_verified: bool = False,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds < 2:
            raise ValueError("timeout_seconds must be finite and at least 2")
        if quote_batch_size < 1 or quote_batch_size > 50:
            raise ValueError("quote_batch_size must be between 1 and 50")
        if not math.isfinite(request_spacing_seconds) or request_spacing_seconds < 0:
            raise ValueError("request_spacing_seconds must be finite and non-negative")
        self._timeout = timeout_seconds
        self._batch_size = quote_batch_size
        self._spacing = request_spacing_seconds
        self._combo_price_convention_verified = combo_price_convention_verified
        self._now = now or (lambda: datetime.now(UTC))

    def health(self, config: IbkrTwsProviderConfig) -> RawIbkrHealth:
        session, thread = self._connect(config)
        try:
            return RawIbkrHealth(
                connected=session.isConnected(),
                paper_account_verified=_paper_account(session.accounts),
                checked_at=self._now(),
                message_code="IBKR_PAPER_READ_ONLY_CONNECTED",
            )
        finally:
            _disconnect(session, thread)

    def fetch_chain(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveChainRequest,
    ) -> RawIbkrChainSnapshot:
        session, thread = self._connect(config)
        requested_at = self._now()
        try:
            session.reqMarketDataType(_REQUESTED_DATA_TYPES[config.market_data_type])
            underlying = self._qualify_underlying(session, request.ticker)
            underlying_quote = self._market_snapshot(session, underlying, request_id=10_000)
            underlying_price = _representative_price(underlying_quote)
            if underlying_price is None:
                raise IbkrProviderError("IBKR_UNDERLYING_SNAPSHOT_INCOMPLETE")

            session.option_parameters = []
            session.option_parameters_ready.clear()
            session.reqSecDefOptParams(
                11_000,
                request.ticker.upper(),
                "",
                "STK",
                int(getattr(underlying, "conId", 0)),
            )
            _wait(session.option_parameters_ready, self._timeout, "IBKR_OPTION_PARAMS_TIMEOUT")
            expirations = _requested_expirations(session.option_parameters, request)
            if not expirations:
                raise IbkrProviderError("IBKR_NO_EXPIRATIONS_IN_REQUEST_RANGE")
            if len(expirations) > request.maximum_expirations:
                raise IbkrProviderError("IBKR_EXPIRATION_RANGE_EXCEEDS_MAXIMUM")
            trading_classes = _trading_classes(session.option_parameters)
            if len(trading_classes) > 8:
                raise IbkrProviderError("IBKR_TRADING_CLASS_SET_EXCEEDS_MAXIMUM")
            details = self._qualify_options(
                session,
                ticker=request.ticker.upper(),
                expirations=expirations,
                trading_classes=trading_classes,
                request=request,
            )
            contracts = _normalise_contract_details(details, request=request)
            details = [
                detail
                for detail in details
                if int(getattr(detail.contract, "conId", 0)) in contracts
            ]
            if not contracts:
                raise IbkrProviderError("IBKR_NO_QUALIFIED_OPTION_CONTRACTS")
            if len(contracts) > request.maximum_contracts:
                raise IbkrProviderError("IBKR_CHAIN_EXCEEDS_MAXIMUM_CONTRACTS")
            contract_discovery_complete = not _material_error_codes(session.error_codes)
            pre_quote_error_codes = set(_material_error_codes(session.error_codes))
            quotes = self._collect_option_quotes(
                session,
                details,
                contracts,
                include_greeks=request.include_greeks,
            )
            received_at = self._now()
            missing = len(contracts) - len(quotes)
            quote_error_codes = (
                set(_material_error_codes(session.error_codes)) - pre_quote_error_codes
            )
            warnings: list[str] = []
            if missing:
                warnings.append(f"{missing} contract snapshot(s) did not complete before timeout.")
            warnings.extend(_error_warnings(session.error_codes))
            return RawIbkrChainSnapshot(
                requested_at=requested_at,
                received_at=received_at,
                underlying_price=underlying_price,
                underlying_quote_timestamp=None,
                underlying_received_at=underlying_quote["received_at"],
                underlying_timestamp_source="client_received_at",
                underlying_market_data_type=underlying_quote["market_data_type"],
                quotes=tuple(quotes),
                discovered_contract_count=len(contracts),
                contract_discovery_complete=contract_discovery_complete,
                quote_collection_complete=missing == 0 and not quote_error_codes,
                server_version=str(session.serverVersion()),
                warnings=tuple(warnings),
            )
        finally:
            _disconnect(session, thread)

    def fetch_combo_quote(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveComboQuoteRequest,
    ) -> RawIbkrComboQuote:
        session, thread = self._connect(config)
        try:
            from ibapi.contract import ComboLeg, Contract  # type: ignore[import-not-found]

            session.reqMarketDataType(_REQUESTED_DATA_TYPES[config.market_data_type])
            contract = Contract()
            contract.symbol = request.ticker.upper()
            contract.secType = "BAG"
            contract.currency = "USD"
            contract.exchange = "SMART"
            contract.comboLegs = []
            for item in request.legs:
                leg = ComboLeg()
                leg.conId = item.con_id
                leg.ratio = item.ratio
                leg.action = item.action
                leg.exchange = item.exchange
                contract.comboLegs.append(leg)
            quote = self._market_snapshot(session, contract, request_id=40_000)
            return RawIbkrComboQuote(
                bid_net_debit=quote.get("bid"),
                ask_net_debit=quote.get("ask"),
                quote_timestamp=None,
                received_at=quote["received_at"],
                market_data_type=quote["market_data_type"],
                price_convention_verified=self._combo_price_convention_verified,
                warnings=tuple(_error_warnings(session.error_codes)),
                timestamp_source="client_received_at",
                collection_complete=not _material_error_codes(session.error_codes),
            )
        finally:
            _disconnect(session, thread)

    def _connect(self, config: IbkrTwsProviderConfig) -> tuple[Any, threading.Thread]:
        _require_loopback(config.host)
        try:
            session = _new_session(self._now)
        except ImportError as error:
            raise IbkrProviderError("OFFICIAL_IBAPI_NOT_INSTALLED") from error
        try:
            session.connect(config.host, config.port, clientId=config.client_id)
            thread = threading.Thread(
                target=session.run,
                daemon=True,
                name="ibkr-opra-read-only",
            )
            thread.start()
            _wait_all(
                (session.ready, session.accounts_ready),
                self._timeout,
                "IBKR_HANDSHAKE_TIMEOUT",
            )
            if not _paper_account(session.accounts):
                raise IbkrProviderError("IBKR_PAPER_ACCOUNT_REQUIRED")
            if any(code in _TRANSIENT_CODES for code in session.error_codes):
                raise IbkrTransientError("IBKR_TRANSIENT_CONNECTION_ERROR")
            return session, thread
        except Exception:
            if session.isConnected():
                session.disconnect()
            raise

    def _qualify_underlying(self, session: Any, ticker: str) -> Any:
        from ibapi.contract import Contract

        request_id = 12_000
        contract = Contract()
        contract.symbol = ticker.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        session.contract_details[request_id] = []
        session.contract_detail_events[request_id] = threading.Event()
        session.reqContractDetails(request_id, contract)
        _wait(
            session.contract_detail_events[request_id],
            self._timeout,
            "IBKR_UNDERLYING_QUALIFICATION_TIMEOUT",
        )
        matches = [
            item.contract
            for item in session.contract_details[request_id]
            if str(getattr(item.contract, "symbol", "")).upper() == ticker.upper()
            and str(getattr(item.contract, "secType", "")) == "STK"
        ]
        if len(matches) != 1:
            raise IbkrProviderError("IBKR_UNDERLYING_QUALIFICATION_AMBIGUOUS")
        return matches[0]

    def _qualify_options(
        self,
        session: Any,
        *,
        ticker: str,
        expirations: list[str],
        trading_classes: list[str],
        request: LiveChainRequest,
    ) -> list[Any]:
        from ibapi.contract import Contract

        request_ids: list[int] = []
        request_id = 13_000
        classes = trading_classes or [ticker]
        for expiration in expirations:
            for trading_class in classes:
                contract = Contract()
                contract.symbol = ticker
                contract.secType = "OPT"
                contract.exchange = "SMART"
                contract.currency = "USD"
                contract.lastTradeDateOrContractMonth = expiration
                contract.tradingClass = trading_class
                session.contract_details[request_id] = []
                session.contract_detail_events[request_id] = threading.Event()
                session.reqContractDetails(request_id, contract)
                request_ids.append(request_id)
                request_id += 1
                time.sleep(self._spacing)
        _wait_all(
            tuple(session.contract_detail_events[item] for item in request_ids),
            self._timeout,
            "IBKR_OPTION_QUALIFICATION_TIMEOUT",
        )
        details = [
            detail
            for item in request_ids
            for detail in session.contract_details[item]
            if _detail_in_request(detail, request)
        ]
        unique: dict[int, Any] = {}
        for detail in details:
            con_id = int(getattr(detail.contract, "conId", 0))
            if con_id > 0:
                unique[con_id] = detail
        return list(unique.values())

    def _collect_option_quotes(
        self,
        session: Any,
        details: list[Any],
        contracts: dict[int, RawIbkrOptionContract],
        *,
        include_greeks: bool,
    ) -> list[RawIbkrOptionQuote]:
        completed: list[RawIbkrOptionQuote] = []
        for batch_start in range(0, len(details), self._batch_size):
            batch = details[batch_start : batch_start + self._batch_size]
            request_ids: list[int] = []
            for offset, detail in enumerate(batch):
                request_id = 20_000 + batch_start + offset
                request_ids.append(request_id)
                session.market_events[request_id] = threading.Event()
                session.market_values[request_id] = {}
                session.market_received_at[request_id] = self._now()
                session.reqMktData(
                    request_id,
                    detail.contract,
                    "100,101,106,221" if include_greeks else "100,101,221",
                    True,
                    False,
                    [],
                )
                time.sleep(self._spacing)
            _wait_until_deadline(
                tuple(session.market_events[item] for item in request_ids),
                self._timeout,
            )
            for request_id, detail in zip(request_ids, batch, strict=True):
                con_id = int(getattr(detail.contract, "conId", 0))
                values = session.market_values.get(request_id, {})
                if session.market_events[request_id].is_set():
                    completed.append(
                        _raw_option_quote(
                            contracts[con_id],
                            values,
                            session.market_received_at[request_id],
                            session.market_data_types.get(request_id),
                        )
                    )
                if session.isConnected():
                    session.cancelMktData(request_id)
        return completed

    def _market_snapshot(self, session: Any, contract: Any, *, request_id: int) -> dict[str, Any]:
        session.market_events[request_id] = threading.Event()
        session.market_values[request_id] = {}
        session.market_received_at[request_id] = self._now()
        session.reqMktData(request_id, contract, "221", True, False, [])
        _wait(session.market_events[request_id], self._timeout, "IBKR_MARKET_SNAPSHOT_TIMEOUT")
        if session.isConnected():
            session.cancelMktData(request_id)
        values = dict(session.market_values.get(request_id, {}))
        values["received_at"] = session.market_received_at[request_id]
        values["market_data_type"] = _MARKET_DATA_TYPES.get(
            session.market_data_types.get(request_id),
            "unknown",
        )
        return values


def _new_session(now: Callable[[], datetime]) -> Any:
    from ibapi.client import EClient  # type: ignore[import-not-found]
    from ibapi.wrapper import EWrapper  # type: ignore[import-not-found]

    class Session(EWrapper, EClient):  # type: ignore[misc]
        def __init__(self) -> None:
            EClient.__init__(self, self)
            self.ready = threading.Event()
            self.accounts_ready = threading.Event()
            self.accounts: tuple[str, ...] = ()
            self.contract_details: dict[int, list[Any]] = {}
            self.contract_detail_events: dict[int, threading.Event] = {}
            self.option_parameters: list[dict[str, Any]] = []
            self.option_parameters_ready = threading.Event()
            self.market_values: dict[int, dict[str, float]] = {}
            self.market_events: dict[int, threading.Event] = {}
            self.market_data_types: dict[int, int] = {}
            self.market_received_at: dict[int, datetime] = {}
            self.error_codes: list[int] = []

        def nextValidId(self, orderId: int) -> None:
            self.ready.set()

        def managedAccounts(self, accountsList: str) -> None:
            self.accounts = tuple(
                account.strip() for account in accountsList.split(",") if account.strip()
            )
            self.accounts_ready.set()

        def contractDetails(self, reqId: int, contractDetails: object) -> None:
            self.contract_details.setdefault(reqId, []).append(contractDetails)

        def contractDetailsEnd(self, reqId: int) -> None:
            event = self.contract_detail_events.get(reqId)
            if event is not None:
                event.set()

        def securityDefinitionOptionParameter(
            self,
            reqId: int,
            exchange: str,
            underlyingConId: int,
            tradingClass: str,
            multiplier: str,
            expirations: set[str],
            strikes: set[float],
        ) -> None:
            self.option_parameters.append(
                {
                    "exchange": exchange,
                    "underlying_con_id": underlyingConId,
                    "trading_class": tradingClass,
                    "multiplier": multiplier,
                    "expirations": set(expirations),
                    "strikes": set(strikes),
                }
            )

        def securityDefinitionOptionParameterEnd(self, reqId: int) -> None:
            self.option_parameters_ready.set()

        def marketDataType(self, reqId: int, marketDataType: int) -> None:
            self.market_data_types[reqId] = marketDataType

        def tickPrice(self, reqId: int, tickType: int, price: float, attrib: object) -> None:
            field = {1: "bid", 2: "ask", 4: "last", 9: "close", 37: "mark"}.get(tickType)
            if field is not None and _valid_market_number(price):
                self.market_values.setdefault(reqId, {})[field] = price
                self.market_received_at[reqId] = now()

        def tickSize(self, reqId: int, tickType: int, size: object) -> None:
            numeric = _number_or_none(size)
            if numeric is None:
                return
            field = {
                0: "bid_size",
                3: "ask_size",
                8: "volume",
                27: "call_open_interest",
                28: "put_open_interest",
                29: "call_volume",
                30: "put_volume",
            }.get(tickType)
            if field is not None:
                self.market_values.setdefault(reqId, {})[field] = numeric
                self.market_received_at[reqId] = now()

        def tickGeneric(self, reqId: int, tickType: int, value: float) -> None:
            field = {23: "historical_volatility", 24: "implied_volatility"}.get(tickType)
            if field is not None and _valid_market_number(value):
                self.market_values.setdefault(reqId, {})[field] = value
                self.market_received_at[reqId] = now()

        def tickOptionComputation(self, reqId: int, tickType: int, *args: object) -> None:
            if len(args) < 8:
                return
            names = (
                "implied_volatility",
                "delta",
                "option_price",
                "pv_dividend",
                "gamma",
                "vega",
                "theta",
                "underlying_price",
            )
            target = self.market_values.setdefault(reqId, {})
            for name, value in zip(names, args[-8:], strict=True):
                numeric = _number_or_none(value)
                if numeric is not None:
                    if tickType == 13 or name not in target:
                        target[name] = numeric
            self.market_received_at[reqId] = now()

        def tickSnapshotEnd(self, reqId: int) -> None:
            event = self.market_events.get(reqId)
            if event is not None:
                event.set()

        def error(self, reqId: int, *args: object) -> None:
            code = next(
                (
                    int(value)
                    for value in args
                    if isinstance(value, int) and value >= 100
                ),
                -1,
            )
            self.error_codes.append(code)
            if code not in _INFORMATIONAL_CODES:
                event = self.contract_detail_events.get(reqId) or self.market_events.get(reqId)
                if event is not None:
                    event.set()

    return Session()


def _normalise_contract_details(
    details: Iterable[Any],
    *,
    request: LiveChainRequest,
) -> dict[int, RawIbkrOptionContract]:
    result: dict[int, RawIbkrOptionContract] = {}
    for detail in details:
        contract = detail.contract
        con_id = int(getattr(contract, "conId", 0))
        expiration = _parse_expiration(str(getattr(contract, "lastTradeDateOrContractMonth", "")))
        strike = float(getattr(contract, "strike", 0))
        right = str(getattr(contract, "right", "")).upper()
        multiplier_text = str(getattr(contract, "multiplier", ""))
        if con_id <= 0 or expiration is None or strike <= 0 or right not in {"C", "P"}:
            continue
        try:
            multiplier = int(float(multiplier_text))
        except ValueError:
            continue
        if multiplier <= 0 or not request.expiration_start <= expiration <= request.expiration_end:
            continue
        if request.minimum_strike is not None and strike < request.minimum_strike:
            continue
        if request.maximum_strike is not None and strike > request.maximum_strike:
            continue
        result[con_id] = RawIbkrOptionContract(
            con_id=con_id,
            ticker=str(getattr(contract, "symbol", "")).upper(),
            local_symbol=str(getattr(contract, "localSymbol", "")),
            trading_class=str(getattr(contract, "tradingClass", "")),
            expiration=expiration,
            strike=strike,
            right=right,  # type: ignore[arg-type]
            multiplier=multiplier,
            exchange=str(getattr(contract, "exchange", "SMART") or "SMART"),
            currency=str(getattr(contract, "currency", "USD") or "USD"),
            exercise_style="american",
            deliverable=None,
            adjusted_contract=None,
        )
    return result


def _raw_option_quote(
    contract: RawIbkrOptionContract,
    values: dict[str, float],
    received_at: datetime,
    market_data_type: int | None,
) -> RawIbkrOptionQuote:
    right_prefix = "call" if contract.right == "C" else "put"
    return RawIbkrOptionQuote(
        contract=contract,
        bid=values.get("bid"),
        ask=values.get("ask"),
        bid_size=values.get("bid_size"),
        ask_size=values.get("ask_size"),
        volume=values.get(f"{right_prefix}_volume", values.get("volume")),
        open_interest=values.get(f"{right_prefix}_open_interest"),
        implied_volatility=values.get("implied_volatility"),
        delta=values.get("delta"),
        gamma=values.get("gamma"),
        vega=values.get("vega"),
        theta=values.get("theta"),
        rho=None,
        quote_timestamp=None,
        received_at=received_at,
        timestamp_source="client_received_at",
        market_data_type=_MARKET_DATA_TYPES.get(market_data_type, "unknown"),  # type: ignore[arg-type]
        provider_greek_convention=(
            "IBKR model-option computation; convention requires live validation"
        ),
        provider_stream="TWS_API_SNAPSHOT",
    )


def _detail_in_request(detail: Any, request: LiveChainRequest) -> bool:
    contract = detail.contract
    expiration = _parse_expiration(str(getattr(contract, "lastTradeDateOrContractMonth", "")))
    strike = float(getattr(contract, "strike", 0))
    if expiration is None or not request.expiration_start <= expiration <= request.expiration_end:
        return False
    if request.minimum_strike is not None and strike < request.minimum_strike:
        return False
    return request.maximum_strike is None or strike <= request.maximum_strike


def _requested_expirations(
    parameters: list[dict[str, Any]],
    request: LiveChainRequest,
) -> list[str]:
    values = {
        expiration
        for item in parameters
        if item.get("exchange") in {"SMART", ""}
        for expiration in item.get("expirations", set())
        if (parsed := _parse_expiration(str(expiration))) is not None
        and request.expiration_start <= parsed <= request.expiration_end
    }
    return sorted(values)


def _trading_classes(parameters: list[dict[str, Any]]) -> list[str]:
    smart = {
        str(item.get("trading_class", ""))
        for item in parameters
        if item.get("exchange") in {"SMART", ""} and item.get("trading_class")
    }
    return sorted(smart)


def _representative_price(values: dict[str, Any]) -> float | None:
    bid = values.get("bid")
    ask = values.get("ask")
    if isinstance(bid, (int, float)) and isinstance(ask, (int, float)) and ask >= bid > 0:
        return (bid + ask) / 2
    for key in ("last", "mark", "close"):
        value = values.get(key)
        if isinstance(value, (int, float)) and _valid_market_number(float(value)):
            return float(value)
    return None


def _paper_account(accounts: tuple[str, ...]) -> bool:
    return len(accounts) == 1 and accounts[0].startswith("DU")


def _require_loopback(host: str) -> None:
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback:
        raise IbkrProviderError("IBKR_HOST_MUST_BE_LOOPBACK")


def _parse_expiration(value: str) -> date | None:
    cleaned = value[:8]
    try:
        return datetime.strptime(cleaned, "%Y%m%d").date()
    except ValueError:
        return None


def _valid_market_number(value: float) -> bool:
    return math.isfinite(value) and value >= 0 and value < 1e100


def _number_or_none(value: object) -> float | None:
    try:
        numeric = float(str(value))
    except (TypeError, ValueError):
        return None
    return numeric if _valid_market_number(numeric) else None


def _error_warnings(codes: list[int]) -> list[str]:
    material = _material_error_codes(codes)
    return [
        f"IBKR reported error code {code}; consult redacted operator logs."
        for code in material
    ]


def _material_error_codes(codes: list[int]) -> list[int]:
    return sorted({code for code in codes if code not in _INFORMATIONAL_CODES and code >= 0})


def _wait(event: threading.Event, timeout: float, code: str) -> None:
    if not event.wait(timeout):
        raise IbkrTransientError(code)


def _wait_all(events: tuple[threading.Event, ...], timeout: float, code: str) -> None:
    _wait_until_deadline(events, timeout)
    if not all(event.is_set() for event in events):
        raise IbkrTransientError(code)


def _wait_until_deadline(events: tuple[threading.Event, ...], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not all(event.is_set() for event in events):
        time.sleep(0.02)


def _disconnect(session: Any, thread: threading.Thread) -> None:
    if session.isConnected():
        session.disconnect()
    thread.join(timeout=2)
