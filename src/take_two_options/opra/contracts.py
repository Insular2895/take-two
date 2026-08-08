"""Provider-neutral, strictly read-only live option-market-data contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Literal, Protocol, runtime_checkable

from pydantic import Field, SecretStr, field_validator, model_validator

from take_two_options.domain import OptionType, StrictModel

OPRA_ENVIRONMENT_VARIABLES = (
    "OPRA_PROVIDER",
    "OPRA_API_KEY",
    "OPRA_API_SECRET",
    "OPRA_ACCOUNT_OR_SESSION",
)


class OpraConfigurationError(ValueError):
    """Raised when the future provider configuration is incomplete."""


class OpraProviderConfig(StrictModel):
    provider: str = Field(min_length=1)
    api_key: SecretStr
    api_secret: SecretStr
    account_or_session: SecretStr
    endpoint: str | None = None
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> OpraProviderConfig:
        missing = [name for name in OPRA_ENVIRONMENT_VARIABLES if not environment.get(name)]
        if missing:
            raise OpraConfigurationError(
                "Missing OPRA configuration variables: " + ", ".join(missing)
            )
        return cls(
            provider=environment["OPRA_PROVIDER"],
            api_key=SecretStr(environment["OPRA_API_KEY"]),
            api_secret=SecretStr(environment["OPRA_API_SECRET"]),
            account_or_session=SecretStr(environment["OPRA_ACCOUNT_OR_SESSION"]),
            endpoint=environment.get("OPRA_ENDPOINT"),
        )


class LiveChainRequest(StrictModel):
    ticker: str = Field(min_length=1)
    as_of: datetime
    expiration_start: date
    expiration_end: date
    maximum_quote_age_seconds: int = Field(gt=0)
    include_greeks: bool = True

    @field_validator("as_of")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("live chain request as_of must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_expiration_order(self) -> LiveChainRequest:
        if self.expiration_start > self.expiration_end:
            raise ValueError("expiration_start cannot follow expiration_end")
        return self


class LiveOptionQuote(StrictModel):
    option_symbol: str = Field(min_length=15)
    ticker: str = Field(min_length=1)
    option_type: OptionType
    strike: float = Field(gt=0)
    expiration: date
    quote_timestamp: datetime
    received_at: datetime
    bid: float = Field(ge=0)
    ask: float = Field(ge=0)
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)
    volume: float | None = Field(default=None, ge=0)
    open_interest: float | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0, le=5)
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None
    multiplier: float = Field(gt=0)
    exchange: str | None = None

    @field_validator("quote_timestamp", "received_at")
    @classmethod
    def require_quote_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("live quote timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_market(self) -> LiveOptionQuote:
        if self.ask < self.bid:
            raise ValueError("live ask cannot be below bid")
        if self.received_at < self.quote_timestamp:
            raise ValueError("received_at cannot precede the provider quote timestamp")
        return self


class LiveOptionChainSnapshot(StrictModel):
    snapshot_id: str
    provider: str
    ticker: str
    requested_at: datetime
    received_at: datetime
    underlying_price: float = Field(gt=0)
    quotes: list[LiveOptionQuote] = Field(min_length=1)
    provider_metadata_hash: str = Field(min_length=64, max_length=64)
    raw_snapshot_hash: str = Field(min_length=64, max_length=64)
    source_latency_milliseconds: float = Field(ge=0)
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("requested_at", "received_at")
    @classmethod
    def require_snapshot_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("snapshot timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_snapshot(self) -> LiveOptionChainSnapshot:
        if self.received_at < self.requested_at:
            raise ValueError("snapshot receipt cannot precede request")
        if any(quote.ticker.upper() != self.ticker.upper() for quote in self.quotes):
            raise ValueError("all live quotes must match the snapshot ticker")
        return self


class ProviderHealth(StrictModel):
    provider: str
    checked_at: datetime
    status: Literal["available_read_only", "degraded", "unavailable"]
    entitlement_confirmed: bool
    message: str
    order_capability: Literal["forbidden"] = "forbidden"


@runtime_checkable
class LiveOptionMarketDataProvider(Protocol):
    """The only live port: health and market-data reads, with no order methods."""

    def health(self) -> ProviderHealth: ...

    def get_option_chain(self, request: LiveChainRequest) -> LiveOptionChainSnapshot: ...


class ProviderReadinessReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    status: Literal["ADAPTER_READY_NOT_CONNECTED", "MISSING_CONFIGURATION"]
    provider: str | None
    provider_protocol: Literal["LiveOptionMarketDataProvider"] = (
        "LiveOptionMarketDataProvider"
    )
    paper_decision_contract: Literal["PaperDecisionRecord"] = "PaperDecisionRecord"
    paper_realization_contract: Literal["PaperRealizationRecord"] = (
        "PaperRealizationRecord"
    )
    required_variables: list[str]
    missing_variables: list[str]
    exact_command: Literal[
        "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
    ] = "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
    connection_attempted: Literal[False] = False
    phase_m_started: Literal[False] = False
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


def assess_provider_readiness(environment: Mapping[str, str]) -> ProviderReadinessReport:
    missing = [name for name in OPRA_ENVIRONMENT_VARIABLES if not environment.get(name)]
    return ProviderReadinessReport(
        status=(
            "MISSING_CONFIGURATION" if missing else "ADAPTER_READY_NOT_CONNECTED"
        ),
        provider=environment.get("OPRA_PROVIDER"),
        required_variables=list(OPRA_ENVIRONMENT_VARIABLES),
        missing_variables=missing,
        connection_attempted=False,
        phase_m_started=False,
    )
