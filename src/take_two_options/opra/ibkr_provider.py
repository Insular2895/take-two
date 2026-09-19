"""Fail-closed IBKR/OPRA market-data provider.

The provider owns governance gates, retry/pacing, in-memory freshness caching and
normalisation.  Broker I/O is injected through :class:`IbkrReadOnlyTransport`, so the
complete decision boundary can be tested without TWS, credentials or a network.

No type in this module can submit, modify, cancel or exercise an order.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from typing import Literal, Protocol

from pydantic import Field, field_validator

from take_two_options.domain import ExerciseStyle, OptionType, StrictModel
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import DatasetLineage, MarketSnapshot, QuoteSnapshot
from take_two_options.opra.contracts import (
    FreshnessBasis,
    IbkrTwsProviderConfig,
    LiveChainRequest,
    LiveComboMarketDataProvider,
    LiveComboQuote,
    LiveComboQuoteRequest,
    LiveFreshnessStatus,
    LiveOptionChainSnapshot,
    LiveOptionMarketDataProvider,
    LiveOptionQuote,
    ProviderHealth,
    TimestampSource,
)
from take_two_options.quantitative.contracts import EvidenceLevel

MarketDataType = Literal["live", "frozen", "delayed", "delayed_frozen", "unknown"]


class IbkrProviderError(RuntimeError):
    """Redacted, fail-closed provider error."""


class IbkrGovernanceError(IbkrProviderError):
    """The human entitlement/licence gate is not satisfied."""


class IbkrTransientError(IbkrProviderError):
    """A read request may be retried without broker mutation."""


class IbkrProviderDiagnostics(StrictModel):
    """Non-secret counters proving retry, pacing and cache behavior for one provider instance."""

    captured_at: datetime
    read_operations: int = Field(ge=0)
    transport_attempts: int = Field(ge=0)
    transient_failures: int = Field(ge=0)
    retry_exhaustions: int = Field(ge=0)
    pacing_wait_count: int = Field(ge=0)
    pacing_wait_seconds: float = Field(ge=0)
    cache_hits: int = Field(ge=0)
    cache_misses: int = Field(ge=0)
    cache_expirations: int = Field(ge=0)
    stale_fallbacks: Literal[0] = 0

    @field_validator("captured_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("provider diagnostics timestamp must be timezone-aware")
        return value.astimezone(UTC)


@dataclass(frozen=True)
class IbkrReadPolicy:
    """Bounded runtime policy for read requests only."""

    maximum_attempts: int = 2
    retry_delay_seconds: float = 0.25
    minimum_request_interval_seconds: float = 0.10
    cache_ttl_seconds: float = 5.0
    allowed_tickers: tuple[str, ...] = ("TTWO",)

    def validate(self) -> None:
        if self.maximum_attempts < 1 or self.maximum_attempts > 5:
            raise ValueError("maximum_attempts must be between 1 and 5")
        for name, value in (
            ("retry_delay_seconds", self.retry_delay_seconds),
            ("minimum_request_interval_seconds", self.minimum_request_interval_seconds),
            ("cache_ttl_seconds", self.cache_ttl_seconds),
        ):
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        if not self.allowed_tickers:
            raise ValueError("allowed_tickers cannot be empty")


@dataclass(frozen=True)
class RawIbkrHealth:
    connected: bool
    paper_account_verified: bool
    checked_at: datetime
    message_code: str


@dataclass(frozen=True)
class RawIbkrOptionContract:
    con_id: int
    ticker: str
    local_symbol: str
    trading_class: str
    expiration: date
    strike: float
    right: Literal["C", "P"]
    multiplier: int
    exchange: str
    currency: str
    exercise_style: Literal["american", "european", "unknown"] = "american"
    deliverable: str | None = None
    adjusted_contract: bool | None = None


@dataclass(frozen=True)
class RawIbkrOptionQuote:
    contract: RawIbkrOptionContract
    bid: float | None
    ask: float | None
    bid_size: float | None
    ask_size: float | None
    volume: float | None
    open_interest: float | None
    implied_volatility: float | None
    delta: float | None
    gamma: float | None
    vega: float | None
    theta: float | None
    rho: float | None
    quote_timestamp: datetime | None
    received_at: datetime
    timestamp_source: TimestampSource
    market_data_type: MarketDataType
    provider_greek_convention: str | None = None
    provider_stream: str | None = None


@dataclass(frozen=True)
class RawIbkrChainSnapshot:
    requested_at: datetime
    received_at: datetime
    underlying_price: float
    underlying_quote_timestamp: datetime | None
    underlying_received_at: datetime
    underlying_timestamp_source: TimestampSource
    underlying_market_data_type: MarketDataType
    quotes: tuple[RawIbkrOptionQuote, ...]
    discovered_contract_count: int
    contract_discovery_complete: bool
    quote_collection_complete: bool
    server_version: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RawIbkrComboQuote:
    bid_net_debit: float | None
    ask_net_debit: float | None
    quote_timestamp: datetime | None
    received_at: datetime
    market_data_type: MarketDataType
    price_convention_verified: bool
    warnings: tuple[str, ...] = ()
    timestamp_source: TimestampSource = "client_received_at"
    collection_complete: bool = True


@dataclass(frozen=True)
class _FreshnessAssessment:
    basis: FreshnessBasis
    status: LiveFreshnessStatus
    verified: bool
    source_timestamp_verified: bool


class IbkrReadOnlyTransport(Protocol):
    """Broker-specific reads.  The protocol intentionally has no order operations."""

    def health(self, config: IbkrTwsProviderConfig) -> RawIbkrHealth: ...

    def fetch_chain(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveChainRequest,
    ) -> RawIbkrChainSnapshot: ...

    def fetch_combo_quote(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveComboQuoteRequest,
    ) -> RawIbkrComboQuote: ...


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    snapshot: LiveOptionChainSnapshot


class IbkrReadOnlyMarketDataProvider(LiveOptionMarketDataProvider, LiveComboMarketDataProvider):
    """Governed IBKR provider with safe read retry and no stale fallback."""

    def __init__(
        self,
        config: IbkrTwsProviderConfig,
        transport: IbkrReadOnlyTransport,
        *,
        entitlement_confirmed: bool,
        license_reviewed: bool,
        policy: IbkrReadPolicy | None = None,
        now: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        if config.session_mode != "paper":
            raise IbkrGovernanceError("IBKR_LIVE_SESSION_FORBIDDEN")
        paper_port = 4002 if config.provider == "ibkr_gateway" else 7497
        if config.port != paper_port:
            raise IbkrGovernanceError("IBKR_PAPER_PORT_REQUIRED")
        if not config.read_only_api or config.transmit or config.order_capability != "forbidden":
            raise IbkrGovernanceError("IBKR_READ_ONLY_INVARIANT_VIOLATION")
        self._config = config
        self._transport = transport
        self._entitlement_confirmed = entitlement_confirmed
        self._license_reviewed = license_reviewed
        self._policy = policy or IbkrReadPolicy()
        self._policy.validate()
        self._now = now or (lambda: datetime.now(UTC))
        self._monotonic = monotonic or time.monotonic
        self._sleep = sleep or time.sleep
        self._last_request_at: float | None = None
        self._cache: dict[str, _CacheEntry] = {}
        self._read_operations = 0
        self._transport_attempts = 0
        self._transient_failures = 0
        self._retry_exhaustions = 0
        self._pacing_wait_count = 0
        self._pacing_wait_seconds = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_expirations = 0

    def _require_governance(self) -> None:
        if not self._entitlement_confirmed:
            raise IbkrGovernanceError("OPRA_ENTITLEMENT_NOT_CONFIRMED")
        if not self._license_reviewed:
            raise IbkrGovernanceError("OPRA_LICENSE_NOT_REVIEWED")

    def _require_ticker(self, ticker: str) -> str:
        normalized = ticker.strip().upper()
        allowed = {item.upper() for item in self._policy.allowed_tickers}
        if normalized not in allowed:
            raise IbkrGovernanceError("IBKR_TICKER_OUTSIDE_ALLOWLIST")
        return normalized

    def _pace(self) -> None:
        current = self._monotonic()
        if self._last_request_at is not None:
            remaining = self._policy.minimum_request_interval_seconds - (
                current - self._last_request_at
            )
            if remaining > 0:
                self._pacing_wait_count += 1
                self._pacing_wait_seconds += remaining
                self._sleep(remaining)
                current = self._monotonic()
        self._last_request_at = current

    def _read_with_retry(self, operation: Callable[[], object]) -> object:
        self._read_operations += 1
        last_error: IbkrTransientError | None = None
        for attempt in range(self._policy.maximum_attempts):
            self._pace()
            self._transport_attempts += 1
            try:
                return operation()
            except IbkrTransientError as error:
                self._transient_failures += 1
                last_error = error
                if attempt + 1 < self._policy.maximum_attempts:
                    self._sleep(self._policy.retry_delay_seconds)
        self._retry_exhaustions += 1
        raise IbkrProviderError("IBKR_READ_RETRY_EXHAUSTED") from last_error

    def diagnostics(self) -> IbkrProviderDiagnostics:
        """Return one redacted metrics snapshot without contacting the broker."""

        return IbkrProviderDiagnostics(
            captured_at=_utc(self._now(), "IBKR_DIAGNOSTICS_TIMESTAMP_NAIVE"),
            read_operations=self._read_operations,
            transport_attempts=self._transport_attempts,
            transient_failures=self._transient_failures,
            retry_exhaustions=self._retry_exhaustions,
            pacing_wait_count=self._pacing_wait_count,
            pacing_wait_seconds=self._pacing_wait_seconds,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            cache_expirations=self._cache_expirations,
        )

    def health(self) -> ProviderHealth:
        self._require_governance()
        raw = self._read_with_retry(lambda: self._transport.health(self._config))
        if not isinstance(raw, RawIbkrHealth):
            raise IbkrProviderError("IBKR_HEALTH_CONTRACT_INVALID")
        available = raw.connected and raw.paper_account_verified
        return ProviderHealth(
            provider=self._config.provider,
            checked_at=_utc(raw.checked_at, "IBKR_HEALTH_TIMESTAMP_NAIVE"),
            status="available_read_only" if available else "unavailable",
            entitlement_confirmed=self._entitlement_confirmed,
            message=raw.message_code,
        )

    def get_option_chain(self, request: LiveChainRequest) -> LiveOptionChainSnapshot:
        self._require_governance()
        ticker = self._require_ticker(request.ticker)
        capture_now = _utc(self._now(), "IBKR_CAPTURE_TIMESTAMP_NAIVE")
        if abs((capture_now - request.as_of).total_seconds()) > request.maximum_quote_age_seconds:
            raise IbkrGovernanceError("LIVE_CHAIN_AS_OF_OUTSIDE_CAPTURE_WINDOW")
        cache_key = stable_hash(
            {
                "provider": self._config.provider,
                "ticker": ticker,
                "request": request.model_dump(mode="json"),
            }
        )
        cached = self._cache.get(cache_key)
        current_monotonic = self._monotonic()
        if cached is not None and current_monotonic <= cached.expires_at:
            self._cache_hits += 1
            return cached.snapshot
        self._cache_misses += 1
        if cached is not None:
            self._cache_expirations += 1
        raw = self._read_with_retry(lambda: self._transport.fetch_chain(self._config, request))
        if not isinstance(raw, RawIbkrChainSnapshot):
            raise IbkrProviderError("IBKR_CHAIN_CONTRACT_INVALID")
        snapshot = _normalise_chain(
            raw,
            request=request,
            ticker=ticker,
            provider=self._config.provider,
        )
        self._cache[cache_key] = _CacheEntry(
            expires_at=self._monotonic() + self._policy.cache_ttl_seconds,
            snapshot=snapshot,
        )
        return snapshot

    def get_combo_quote(self, request: LiveComboQuoteRequest) -> LiveComboQuote:
        self._require_governance()
        ticker = self._require_ticker(request.ticker)
        raw = self._read_with_retry(
            lambda: self._transport.fetch_combo_quote(self._config, request)
        )
        if not isinstance(raw, RawIbkrComboQuote):
            raise IbkrProviderError("IBKR_COMBO_CONTRACT_INVALID")
        return _normalise_combo(raw, request=request, ticker=ticker)


def build_official_ibkr_provider(
    environment: Mapping[str, str],
    *,
    policy: IbkrReadPolicy | None = None,
) -> IbkrReadOnlyMarketDataProvider:
    """Build the official transport without importing ``ibapi`` until the first read."""

    config = IbkrTwsProviderConfig.from_environment(environment)
    confirmed = environment.get("OPRA_ENTITLEMENT_CONFIRMED", "").strip().lower()
    reviewed = environment.get("OPRA_LICENSE_REVIEWED", "").strip().lower()
    from take_two_options.opra.ibkr_official import OfficialIbkrReadOnlyTransport

    return IbkrReadOnlyMarketDataProvider(
        config,
        OfficialIbkrReadOnlyTransport(),
        entitlement_confirmed=confirmed in {"1", "true", "yes"},
        license_reviewed=reviewed in {"1", "true", "yes"},
        policy=policy,
    )


def _component_freshness(
    *,
    timestamp_source: TimestampSource,
    source_timestamp: datetime | None,
    received_at: datetime,
    requested_at: datetime,
    collection_completed_at: datetime,
    maximum_age_seconds: int,
    market_data_type: MarketDataType,
    component_complete: bool,
    collection_complete: bool,
) -> _FreshnessAssessment:
    """Classify provenance and freshness without promoting receipt time to source time."""

    if not component_complete or not collection_complete:
        return _FreshnessAssessment("UNVERIFIED", "INCOMPLETE", False, False)
    if received_at < requested_at or collection_completed_at < received_at:
        return _FreshnessAssessment("UNVERIFIED", "INVALID", False, False)

    source_verified = timestamp_source in {"exchange", "provider"}
    if source_verified:
        if source_timestamp is None:
            return _FreshnessAssessment("UNVERIFIED", "INCOMPLETE", False, False)
        source_age = (received_at - source_timestamp).total_seconds()
        if source_age < 0:
            return _FreshnessAssessment("SOURCE_TIMESTAMP", "INVALID", False, False)
        if source_age > maximum_age_seconds:
            return _FreshnessAssessment("SOURCE_TIMESTAMP", "STALE", False, True)
        basis: FreshnessBasis = "SOURCE_TIMESTAMP"
    elif timestamp_source == "client_received_at":
        capture_age = (collection_completed_at - requested_at).total_seconds()
        component_capture_age = (received_at - requested_at).total_seconds()
        if capture_age < 0 or component_capture_age < 0:
            return _FreshnessAssessment("BOUNDED_CAPTURE_WINDOW", "INVALID", False, False)
        if capture_age > maximum_age_seconds or component_capture_age > maximum_age_seconds:
            return _FreshnessAssessment("BOUNDED_CAPTURE_WINDOW", "STALE", False, False)
        basis = "BOUNDED_CAPTURE_WINDOW"
    else:
        return _FreshnessAssessment("UNVERIFIED", "INVALID", False, False)

    if market_data_type == "delayed":
        return _FreshnessAssessment(basis, "DELAYED", False, source_verified)
    if market_data_type in {"frozen", "delayed_frozen"}:
        return _FreshnessAssessment(basis, "FROZEN", False, source_verified)
    if market_data_type != "live":
        return _FreshnessAssessment(basis, "INVALID", False, source_verified)
    status: LiveFreshnessStatus = (
        "LIVE_SOURCE_TIMESTAMP_FRESH"
        if basis == "SOURCE_TIMESTAMP"
        else "LIVE_CAPTURE_WINDOW_FRESH"
    )
    return _FreshnessAssessment(basis, status, True, source_verified)


def _aggregate_freshness(
    assessments: list[_FreshnessAssessment],
    *,
    complete: bool,
) -> _FreshnessAssessment:
    if not complete or not assessments:
        return _FreshnessAssessment("UNVERIFIED", "INCOMPLETE", False, False)
    statuses = {item.status for item in assessments}
    for status in ("INVALID", "INCOMPLETE", "DELAYED", "FROZEN", "STALE"):
        if status in statuses:
            return _FreshnessAssessment(
                "UNVERIFIED",
                status,
                False,
                all(item.source_timestamp_verified for item in assessments),
            )
    all_verified = all(item.verified for item in assessments)
    all_source = all(item.basis == "SOURCE_TIMESTAMP" for item in assessments)
    return _FreshnessAssessment(
        "SOURCE_TIMESTAMP" if all_source else "BOUNDED_CAPTURE_WINDOW",
        "LIVE_SOURCE_TIMESTAMP_FRESH" if all_source else "LIVE_CAPTURE_WINDOW_FRESH",
        all_verified,
        all(item.source_timestamp_verified for item in assessments),
    )


def _normalise_chain(
    raw: RawIbkrChainSnapshot,
    *,
    request: LiveChainRequest,
    ticker: str,
    provider: str,
) -> LiveOptionChainSnapshot:
    requested_at = _utc(raw.requested_at, "IBKR_REQUEST_TIMESTAMP_NAIVE")
    received_at = _utc(raw.received_at, "IBKR_RECEIPT_TIMESTAMP_NAIVE")
    if received_at < requested_at:
        raise IbkrProviderError("IBKR_RECEIPT_PRECEDES_REQUEST")
    if not math.isfinite(raw.underlying_price) or raw.underlying_price <= 0:
        raise IbkrProviderError("IBKR_UNDERLYING_PRICE_INVALID")
    if raw.discovered_contract_count > request.maximum_contracts:
        raise IbkrProviderError("IBKR_CHAIN_EXCEEDS_MAXIMUM_CONTRACTS")

    warnings = list(raw.warnings)
    quotes: list[LiveOptionQuote] = []
    quote_assessments: list[_FreshnessAssessment] = []
    missing = 0
    seen_con_ids: set[int] = set()
    for item in raw.quotes:
        contract = item.contract
        if contract.con_id in seen_con_ids:
            raise IbkrProviderError("IBKR_DUPLICATE_OPTION_CON_ID")
        seen_con_ids.add(contract.con_id)
        if contract.ticker.upper() != ticker:
            raise IbkrProviderError("IBKR_OPTION_TICKER_MISMATCH")
        if not request.expiration_start <= contract.expiration <= request.expiration_end:
            raise IbkrProviderError("IBKR_OPTION_EXPIRATION_OUTSIDE_REQUEST")
        if request.minimum_strike is not None and contract.strike < request.minimum_strike:
            raise IbkrProviderError("IBKR_OPTION_STRIKE_OUTSIDE_REQUEST")
        if request.maximum_strike is not None and contract.strike > request.maximum_strike:
            raise IbkrProviderError("IBKR_OPTION_STRIKE_OUTSIDE_REQUEST")
        source_timestamp = (
            _utc(item.quote_timestamp, "IBKR_QUOTE_TIMESTAMP_NAIVE")
            if item.quote_timestamp is not None
            else None
        )
        quote_received_at = _utc(item.received_at, "IBKR_QUOTE_RECEIPT_NAIVE")
        valid_market = (
            item.bid is not None
            and item.ask is not None
            and _finite_non_negative(item.bid)
            and _finite_non_negative(item.ask)
            and item.ask >= item.bid
        )
        if not valid_market:
            missing += 1
            continue
        assessment = _component_freshness(
            timestamp_source=item.timestamp_source,
            source_timestamp=source_timestamp,
            received_at=quote_received_at,
            requested_at=requested_at,
            collection_completed_at=received_at,
            maximum_age_seconds=request.maximum_quote_age_seconds,
            market_data_type=item.market_data_type,
            component_complete=True,
            collection_complete=raw.quote_collection_complete,
        )
        quote_assessments.append(assessment)
        effective_quote_timestamp = source_timestamp or quote_received_at
        quotes.append(
            LiveOptionQuote(
                option_symbol=contract.local_symbol,
                ticker=ticker,
                option_type=OptionType.CALL if contract.right == "C" else OptionType.PUT,
                strike=contract.strike,
                expiration=contract.expiration,
                quote_timestamp=effective_quote_timestamp,
                received_at=quote_received_at,
                bid=item.bid,
                ask=item.ask,
                bid_size=_optional_non_negative(item.bid_size),
                ask_size=_optional_non_negative(item.ask_size),
                volume=_optional_non_negative(item.volume),
                open_interest=_optional_non_negative(item.open_interest),
                implied_volatility=_optional_positive(item.implied_volatility),
                delta=_optional_finite(item.delta),
                gamma=_optional_finite(item.gamma),
                vega=_optional_finite(item.vega),
                theta=_optional_finite(item.theta),
                rho=_optional_finite(item.rho),
                multiplier=contract.multiplier,
                exchange=contract.exchange,
                con_id=contract.con_id,
                local_symbol=contract.local_symbol,
                trading_class=contract.trading_class,
                currency=contract.currency,
                deliverable=contract.deliverable,
                exercise_style=contract.exercise_style,
                adjusted_contract=contract.adjusted_contract,
                provider_greek_convention=item.provider_greek_convention,
                provider_stream=item.provider_stream,
                quote_timestamp_source=item.timestamp_source,
                market_data_type=item.market_data_type,
                freshness_basis=assessment.basis,
                freshness_status=assessment.status,
                freshness_verified=assessment.verified,
                source_timestamp_verified=assessment.source_timestamp_verified,
            )
        )
    missing += max(raw.discovered_contract_count - len(raw.quotes), 0)
    if not quotes:
        raise IbkrProviderError("IBKR_CHAIN_HAS_NO_USABLE_QUOTES")
    if missing:
        warnings.append(f"{missing} discovered contract(s) lacked a usable fresh two-sided quote.")
    quote_collection_complete = raw.quote_collection_complete and missing == 0
    underlying_quote_timestamp = (
        _utc(raw.underlying_quote_timestamp, "IBKR_UNDERLYING_TIMESTAMP_NAIVE")
        if raw.underlying_quote_timestamp is not None
        else None
    )
    underlying_received_at = _utc(
        raw.underlying_received_at,
        "IBKR_UNDERLYING_RECEIPT_NAIVE",
    )
    underlying_assessment = _component_freshness(
        timestamp_source=raw.underlying_timestamp_source,
        source_timestamp=underlying_quote_timestamp,
        received_at=underlying_received_at,
        requested_at=requested_at,
        collection_completed_at=received_at,
        maximum_age_seconds=request.maximum_quote_age_seconds,
        market_data_type=raw.underlying_market_data_type,
        component_complete=True,
        collection_complete=raw.quote_collection_complete,
    )
    chain_complete = raw.contract_discovery_complete and quote_collection_complete
    aggregate = _aggregate_freshness(
        [underlying_assessment, *quote_assessments],
        complete=chain_complete,
    )
    promotion_eligible = chain_complete and aggregate.verified
    if not aggregate.source_timestamp_verified:
        warnings.append(
            "At least one required component uses truthful client-receipt provenance; "
            "no provider/exchange timestamp was inferred."
        )
    if aggregate.status == "LIVE_CAPTURE_WINDOW_FRESH":
        warnings.append(
            "Freshness is verified by a bounded live capture window, not by source timestamps."
        )
    elif not aggregate.verified:
        warnings.append(f"Required-component freshness is {aggregate.status}.")

    raw_payload = asdict(raw)
    metadata_payload = [asdict(quote.contract) for quote in raw.quotes]
    snapshot_id = f"ibkr-{stable_hash(raw_payload)[:20]}"
    return LiveOptionChainSnapshot(
        snapshot_id=snapshot_id,
        provider=provider,
        ticker=ticker,
        requested_at=requested_at,
        received_at=received_at,
        underlying_price=raw.underlying_price,
        quotes=quotes,
        provider_metadata_hash=stable_hash(metadata_payload),
        raw_snapshot_hash=stable_hash(raw_payload),
        source_latency_milliseconds=(received_at - requested_at).total_seconds() * 1_000,
        underlying_quote_timestamp=underlying_quote_timestamp,
        underlying_received_at=underlying_received_at,
        underlying_timestamp_source=raw.underlying_timestamp_source,
        underlying_market_data_type=raw.underlying_market_data_type,
        requested_contract_count=raw.discovered_contract_count,
        returned_quote_count=len(quotes),
        missing_quote_count=missing,
        contract_discovery_complete=raw.contract_discovery_complete,
        quote_collection_complete=quote_collection_complete,
        freshness_basis=aggregate.basis,
        freshness_status=aggregate.status,
        freshness_verified=aggregate.verified,
        source_timestamp_verified=aggregate.source_timestamp_verified,
        underlying_freshness_basis=underlying_assessment.basis,
        underlying_freshness_status=underlying_assessment.status,
        underlying_source_timestamp_verified=underlying_assessment.source_timestamp_verified,
        required_component_freshness={
            "underlying": underlying_assessment.status,
            **{
                quote.option_symbol: quote.freshness_status
                for quote in quotes
            },
        },
        promotion_eligible=promotion_eligible,
        warnings=warnings,
    )


def _normalise_combo(
    raw: RawIbkrComboQuote,
    *,
    request: LiveComboQuoteRequest,
    ticker: str,
) -> LiveComboQuote:
    received_at = _utc(raw.received_at, "IBKR_COMBO_RECEIPT_NAIVE")
    quote_timestamp = (
        _utc(raw.quote_timestamp, "IBKR_COMBO_TIMESTAMP_NAIVE")
        if raw.quote_timestamp is not None
        else None
    )
    broker_complete = (
        raw.bid_net_debit is not None
        and raw.ask_net_debit is not None
        and _finite(raw.bid_net_debit)
        and _finite(raw.ask_net_debit)
        and raw.ask_net_debit >= raw.bid_net_debit
    )
    assessment = _component_freshness(
        timestamp_source=raw.timestamp_source,
        source_timestamp=quote_timestamp,
        received_at=received_at,
        requested_at=_utc(request.requested_at, "IBKR_COMBO_REQUEST_NAIVE"),
        collection_completed_at=received_at,
        maximum_age_seconds=request.maximum_quote_age_seconds,
        market_data_type=raw.market_data_type,
        component_complete=broker_complete,
        collection_complete=raw.collection_complete,
    )
    synthetic_bid, synthetic_ask = _synthetic_combo(request)
    synthetic_complete = synthetic_bid is not None and synthetic_ask is not None
    divergences: list[float] = []
    if broker_complete and synthetic_complete:
        assert raw.bid_net_debit is not None
        assert raw.ask_net_debit is not None
        assert synthetic_bid is not None
        assert synthetic_ask is not None
        divergences = [
            abs(raw.bid_net_debit - synthetic_bid),
            abs(raw.ask_net_debit - synthetic_ask),
        ]
    warnings = list(raw.warnings)
    if assessment.status == "LIVE_CAPTURE_WINDOW_FRESH":
        warnings.append(
            "Broker combo freshness uses a bounded client-receipt capture window; "
            "no provider/exchange timestamp was inferred."
        )
    elif not assessment.verified:
        warnings.append(f"Broker combo freshness is {assessment.status}.")
    if not raw.price_convention_verified:
        warnings.append("IBKR BAG signed-price convention is not yet verified on this session.")
    if not synthetic_complete:
        warnings.append("Synthetic combo comparison is incomplete because a leg quote is missing.")
    confirmed = (
        broker_complete
        and synthetic_complete
        and assessment.verified
        and raw.price_convention_verified
    )
    return LiveComboQuote(
        candidate_id=request.candidate_id,
        ticker=ticker,
        bid_net_debit=raw.bid_net_debit if broker_complete else None,
        ask_net_debit=raw.ask_net_debit if broker_complete else None,
        synthetic_bid_net_debit=synthetic_bid,
        synthetic_ask_net_debit=synthetic_ask,
        maximum_absolute_divergence=max(divergences) if divergences else None,
        quote_timestamp=quote_timestamp,
        received_at=received_at,
        timestamp_source=raw.timestamp_source,
        freshness_basis=assessment.basis,
        freshness_status=assessment.status,
        freshness_verified=assessment.verified,
        source_timestamp_verified=assessment.source_timestamp_verified,
        source_id=f"ibkr-combo-{stable_hash({'request': request, 'raw': asdict(raw)})[:20]}",
        market_data_type=raw.market_data_type,
        broker_quote_complete=broker_complete,
        synthetic_quote_complete=synthetic_complete,
        quote_freshness_verified=assessment.verified,
        price_convention_verified=raw.price_convention_verified,
        comparison_confirmed=confirmed,
        warnings=warnings,
    )


def _synthetic_combo(request: LiveComboQuoteRequest) -> tuple[float | None, float | None]:
    if any(leg.bid is None or leg.ask is None for leg in request.legs):
        return None, None
    bid = 0.0
    ask = 0.0
    for leg in request.legs:
        assert leg.bid is not None
        assert leg.ask is not None
        if leg.action == "BUY":
            bid += leg.ratio * leg.bid
            ask += leg.ratio * leg.ask
        else:
            bid -= leg.ratio * leg.ask
            ask -= leg.ratio * leg.bid
    return bid, ask


def live_chain_to_market_snapshot(snapshot: LiveOptionChainSnapshot) -> MarketSnapshot:
    """Translate the provider-neutral live contract into the canonical engine snapshot."""

    quotes = [
        QuoteSnapshot(
            symbol=quote.option_symbol,
            expiration=quote.expiration,
            option_type=quote.option_type,
            strike=quote.strike,
            exercise_style=(
                ExerciseStyle(quote.exercise_style)
                if quote.exercise_style in {"american", "european"}
                else None
            ),
            bid=quote.bid,
            ask=quote.ask,
            bid_size=int(quote.bid_size) if quote.bid_size is not None else None,
            ask_size=int(quote.ask_size) if quote.ask_size is not None else None,
            volume=int(quote.volume) if quote.volume is not None else None,
            open_interest=(int(quote.open_interest) if quote.open_interest is not None else None),
            implied_volatility=quote.implied_volatility,
            delta=quote.delta,
            quote_timestamp=quote.quote_timestamp,
            multiplier=int(quote.multiplier),
            multiplier_status=EvidenceLevel.KNOWN,
            contract_adjustment_status=(
                EvidenceLevel.KNOWN if quote.deliverable is not None else EvidenceLevel.UNKNOWN
            ),
            deliverable_description=quote.deliverable,
            exchange_timestamp=(
                quote.quote_timestamp
                if quote.quote_timestamp_source == "exchange"
                and quote.source_timestamp_verified
                else None
            ),
            provider_timestamp=(
                quote.quote_timestamp
                if quote.quote_timestamp_source == "provider"
                and quote.source_timestamp_verified
                else None
            ),
            received_at=quote.received_at,
            price_quality="live_broker",
            source_id=snapshot.snapshot_id,
        )
        for quote in snapshot.quotes
    ]
    lineage_hash = stable_hash(snapshot.model_dump(mode="json"))
    effective_component_timestamps = [
        quote.quote_timestamp for quote in snapshot.quotes
    ] + [
        snapshot.underlying_quote_timestamp
        or snapshot.underlying_received_at
        or snapshot.received_at
    ]
    earliest_quote = min(effective_component_timestamps)
    latest_quote = max(effective_component_timestamps)
    spot_timestamp = (
        snapshot.underlying_quote_timestamp
        or snapshot.underlying_received_at
        or snapshot.received_at
    )
    freshness_age = max((snapshot.received_at - earliest_quote).total_seconds(), 0.0)
    warnings = list(snapshot.warnings)
    if not snapshot.promotion_eligible:
        warnings.append("IBKR snapshot is research-only and not promotion eligible.")
    return MarketSnapshot(
        snapshot_id=snapshot.snapshot_id,
        ticker=snapshot.ticker,
        as_of=latest_quote,
        spot=snapshot.underlying_price,
        spot_timestamp=spot_timestamp,
        exchange_timestamp=(
            spot_timestamp
            if snapshot.underlying_timestamp_source == "exchange"
            and snapshot.underlying_source_timestamp_verified
            else None
        ),
        provider_timestamp=(
            spot_timestamp
            if snapshot.underlying_timestamp_source == "provider"
            and snapshot.underlying_source_timestamp_verified
            else None
        ),
        received_at=snapshot.received_at,
        freshness_age_seconds=freshness_age,
        freshness_status=(
            EvidenceLevel.KNOWN if snapshot.freshness_verified else EvidenceLevel.ESTIMATED
        ),
        quote_quality="live_broker",
        source_ids=[snapshot.snapshot_id],
        quotes=quotes,
        available_expirations=sorted({quote.expiration for quote in quotes}),
        data_warnings=warnings,
        lineage=DatasetLineage(
            dataset_id=snapshot.snapshot_id,
            source=f"{snapshot.provider}:read_only",
            range_start=earliest_quote,
            range_end=latest_quote,
            ingested_at=snapshot.received_at,
            schema_version="live-option-chain-1.0",
            dataset_hash=lineage_hash,
        ),
    )


def _utc(value: datetime, code: str) -> datetime:
    if value.tzinfo is None:
        raise IbkrProviderError(code)
    return value.astimezone(UTC)


def _finite(value: float) -> bool:
    return math.isfinite(value)


def _finite_non_negative(value: float) -> bool:
    return math.isfinite(value) and value >= 0


def _optional_finite(value: float | None) -> float | None:
    return value if value is not None and math.isfinite(value) else None


def _optional_non_negative(value: float | None) -> float | None:
    return value if value is not None and _finite_non_negative(value) else None


def _optional_positive(value: float | None) -> float | None:
    return value if value is not None and math.isfinite(value) and value > 0 else None
