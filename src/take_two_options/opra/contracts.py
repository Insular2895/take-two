"""Provider-neutral, strictly read-only live option-market-data contracts.

IBKR TWS and IB Gateway authenticate the human user in the host application and
then expose a local socket identified by host, port, and client ID. They do not
use an ``OPRA_API_KEY``. Token credentials remain supported for a future
non-IBKR data vendor, but the two authentication modes are deliberately kept
separate so an absent subscription cannot be mistaken for an absent API key.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime
from typing import Literal, Protocol, cast, runtime_checkable

from pydantic import Field, SecretStr, field_validator, model_validator

from take_two_options.domain import OptionType, StrictModel

TOKEN_OPRA_ENVIRONMENT_VARIABLES = (
    "OPRA_PROVIDER",
    "OPRA_API_KEY",
    "OPRA_API_SECRET",
    "OPRA_ACCOUNT_OR_SESSION",
)
IBKR_TWS_ENVIRONMENT_VARIABLES = (
    "OPRA_PROVIDER",
    "IBKR_HOST",
    "IBKR_PORT",
    "IBKR_CLIENT_ID",
    "IBKR_SESSION_MODE",
    "IBKR_MARKET_DATA_TYPE",
)
OPRA_GOVERNANCE_VARIABLES = (
    "OPRA_ENTITLEMENT_CONFIRMED",
    "OPRA_LICENSE_REVIEWED",
)
IBKR_TWS_PROVIDERS = frozenset({"ibkr_tws", "ibkr_gateway"})


class OpraConfigurationError(ValueError):
    """Raised when the future provider configuration is incomplete."""


class OpraProviderConfig(StrictModel):
    """Credential-bearing configuration for a non-IBKR OPRA data vendor."""

    provider: str = Field(min_length=1)
    authentication_mode: Literal["api_credentials"] = "api_credentials"
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
        missing = [
            name for name in TOKEN_OPRA_ENVIRONMENT_VARIABLES if not environment.get(name)
        ]
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


class IbkrTwsProviderConfig(StrictModel):
    """Local read-only TWS/IB Gateway socket configuration without API secrets."""

    provider: Literal["ibkr_tws", "ibkr_gateway"]
    authentication_mode: Literal["tws_session"] = "tws_session"
    host: str = Field(min_length=1)
    port: int = Field(gt=0, le=65535)
    client_id: int = Field(ge=0)
    session_mode: Literal["paper", "live"]
    market_data_type: Literal["live", "frozen", "delayed", "delayed_frozen"]
    read_only_api: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> IbkrTwsProviderConfig:
        missing = [
            name for name in IBKR_TWS_ENVIRONMENT_VARIABLES if not environment.get(name)
        ]
        if missing:
            raise OpraConfigurationError(
                "Missing IBKR TWS configuration variables: " + ", ".join(missing)
            )
        provider = environment["OPRA_PROVIDER"].strip().lower()
        if provider not in IBKR_TWS_PROVIDERS:
            raise OpraConfigurationError(
                "IBKR TWS configuration requires OPRA_PROVIDER=ibkr_tws or "
                "ibkr_gateway"
            )
        try:
            port = int(environment["IBKR_PORT"])
            client_id = int(environment["IBKR_CLIENT_ID"])
        except ValueError as error:
            raise OpraConfigurationError(
                "IBKR_PORT and IBKR_CLIENT_ID must be integers"
            ) from error
        return cls(
            provider=cast(Literal["ibkr_tws", "ibkr_gateway"], provider),
            host=environment["IBKR_HOST"],
            port=port,
            client_id=client_id,
            session_mode=cast(
                Literal["paper", "live"],
                environment["IBKR_SESSION_MODE"].strip().lower(),
            ),
            market_data_type=cast(
                Literal["live", "frozen", "delayed", "delayed_frozen"],
                environment["IBKR_MARKET_DATA_TYPE"].strip().lower(),
            ),
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
    schema_version: Literal["1.1"] = "1.1"
    status: Literal[
        "ADAPTER_READY_NOT_CONNECTED",
        "CONFIGURED_NOT_ENTITLED",
        "MISSING_CONFIGURATION",
    ]
    provider: str | None
    authentication_mode: Literal["tws_session", "api_credentials"] | None
    provider_protocol: Literal["LiveOptionMarketDataProvider"] = (
        "LiveOptionMarketDataProvider"
    )
    paper_decision_contract: Literal["PaperDecisionRecord"] = "PaperDecisionRecord"
    paper_realization_contract: Literal["PaperRealizationRecord"] = (
        "PaperRealizationRecord"
    )
    required_variables: list[str]
    missing_variables: list[str]
    configuration_errors: list[str]
    credentials_required: bool
    credentials_present: bool
    entitlement_confirmed: bool
    license_reviewed: bool
    notes: list[str]
    exact_command: Literal[
        "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
    ] = "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
    connection_attempted: Literal[False] = False
    phase_m_started: Literal[False] = False
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


def _confirmed(environment: Mapping[str, str], name: str) -> bool:
    return environment.get(name, "").strip().lower() in {"1", "true", "yes"}


def assess_provider_readiness(environment: Mapping[str, str]) -> ProviderReadinessReport:
    provider_value = environment.get("OPRA_PROVIDER", "").strip()
    if not provider_value:
        return ProviderReadinessReport(
            status="MISSING_CONFIGURATION",
            provider=None,
            authentication_mode=None,
            required_variables=["OPRA_PROVIDER"],
            missing_variables=["OPRA_PROVIDER"],
            configuration_errors=[],
            credentials_required=False,
            credentials_present=False,
            entitlement_confirmed=False,
            license_reviewed=False,
            notes=[
                "Choose ibkr_tws/ibkr_gateway for a local IBKR session, or a "
                "credential-bearing data vendor."
            ],
        )

    provider = provider_value.lower()
    ibkr = provider in IBKR_TWS_PROVIDERS
    authentication_mode: Literal["tws_session", "api_credentials"] = (
        "tws_session" if ibkr else "api_credentials"
    )
    provider_variables = (
        IBKR_TWS_ENVIRONMENT_VARIABLES if ibkr else TOKEN_OPRA_ENVIRONMENT_VARIABLES
    )
    required = [*provider_variables, *OPRA_GOVERNANCE_VARIABLES]
    missing = [name for name in required if not environment.get(name)]
    errors: list[str] = []
    if not any(name in missing for name in provider_variables):
        try:
            if ibkr:
                IbkrTwsProviderConfig.from_environment(environment)
            else:
                OpraProviderConfig.from_environment(environment)
        except (OpraConfigurationError, ValueError) as error:
            errors.append(str(error))

    entitlement_confirmed = _confirmed(environment, "OPRA_ENTITLEMENT_CONFIRMED")
    license_reviewed = _confirmed(environment, "OPRA_LICENSE_REVIEWED")
    credentials_required = not ibkr
    credentials_present = (
        all(environment.get(name) for name in TOKEN_OPRA_ENVIRONMENT_VARIABLES[1:])
        if credentials_required
        else False
    )
    status: Literal[
        "ADAPTER_READY_NOT_CONNECTED",
        "CONFIGURED_NOT_ENTITLED",
        "MISSING_CONFIGURATION",
    ]
    if missing or errors:
        status = "MISSING_CONFIGURATION"
    elif not entitlement_confirmed or not license_reviewed:
        status = "CONFIGURED_NOT_ENTITLED"
    else:
        status = "ADAPTER_READY_NOT_CONNECTED"

    notes = (
        [
            "IBKR TWS/IB Gateway uses a locally authenticated socket session; "
            "no OPRA_API_KEY or OPRA_API_SECRET is expected.",
            "Keep the TWS Read-Only API setting enabled for this research-only port.",
        ]
        if ibkr
        else [
            "API credentials are loaded only for the selected data vendor and are "
            "never serialized."
        ]
    )
    return ProviderReadinessReport(
        status=status,
        provider=provider,
        authentication_mode=authentication_mode,
        required_variables=required,
        missing_variables=missing,
        configuration_errors=errors,
        credentials_required=credentials_required,
        credentials_present=credentials_present,
        entitlement_confirmed=entitlement_confirmed,
        license_reviewed=license_reviewed,
        notes=notes,
        connection_attempted=False,
        phase_m_started=False,
    )
