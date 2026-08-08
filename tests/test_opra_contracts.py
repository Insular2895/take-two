from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from take_two_options.opra.contracts import (
    LiveChainRequest,
    LiveOptionChainSnapshot,
    LiveOptionMarketDataProvider,
    LiveOptionQuote,
    OpraConfigurationError,
    OpraProviderConfig,
    ProviderHealth,
    assess_provider_readiness,
)


class DummyReadOnlyProvider:
    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider="dummy",
            checked_at=datetime(2026, 8, 8, tzinfo=UTC),
            status="available_read_only",
            entitlement_confirmed=True,
            message="fixture",
        )

    def get_option_chain(self, request: LiveChainRequest) -> LiveOptionChainSnapshot:
        quote = LiveOptionQuote(
            option_symbol="TTWO270115C00250000",
            ticker=request.ticker,
            option_type="call",
            strike=250,
            expiration=date(2027, 1, 15),
            quote_timestamp=request.as_of,
            received_at=request.as_of,
            bid=10,
            ask=10.5,
            multiplier=100,
        )
        return LiveOptionChainSnapshot(
            snapshot_id="dummy-1",
            provider="dummy",
            ticker=request.ticker,
            requested_at=request.as_of,
            received_at=request.as_of,
            underlying_price=240,
            quotes=[quote],
            provider_metadata_hash="a" * 64,
            raw_snapshot_hash="b" * 64,
            source_latency_milliseconds=0,
        )


def test_provider_protocol_is_read_only_and_contains_no_order_methods() -> None:
    provider = DummyReadOnlyProvider()
    assert isinstance(provider, LiveOptionMarketDataProvider)
    methods = set(LiveOptionMarketDataProvider.__dict__)
    assert {"health", "get_option_chain"} <= methods
    assert not methods & {"submit", "modify", "cancel", "exercise", "roll"}


def test_opra_environment_contract_masks_secrets_and_fails_closed() -> None:
    with pytest.raises(OpraConfigurationError, match="OPRA_API_KEY"):
        OpraProviderConfig.from_environment({"OPRA_PROVIDER": "future-provider"})
    config = OpraProviderConfig.from_environment(
        {
            "OPRA_PROVIDER": "future-provider",
            "OPRA_API_KEY": "secret-key",
            "OPRA_API_SECRET": "secret-value",
            "OPRA_ACCOUNT_OR_SESSION": "session-value",
        }
    )
    assert "secret-key" not in repr(config)
    assert config.api_key.get_secret_value() == "secret-key"
    assert config.transmit is False
    assert config.what_if is True
    assert config.order_capability == "forbidden"


def test_readiness_never_attempts_connection_or_phase_m() -> None:
    report = assess_provider_readiness({})
    assert report.status == "MISSING_CONFIGURATION"
    assert report.connection_attempted is False
    assert report.phase_m_started is False
    assert report.missing_variables
    complete = assess_provider_readiness(
        {
            "OPRA_PROVIDER": "future-provider",
            "OPRA_API_KEY": "x",
            "OPRA_API_SECRET": "y",
            "OPRA_ACCOUNT_OR_SESSION": "z",
        }
    )
    assert complete.status == "ADAPTER_READY_NOT_CONNECTED"
    assert complete.missing_variables == []


def test_live_quote_rejects_crossed_market() -> None:
    with pytest.raises(ValidationError, match="ask cannot be below bid"):
        LiveOptionQuote(
            option_symbol="TTWO270115C00250000",
            ticker="TTWO",
            option_type="call",
            strike=250,
            expiration=date(2027, 1, 15),
            quote_timestamp=datetime(2026, 8, 8, tzinfo=UTC),
            received_at=datetime(2026, 8, 8, tzinfo=UTC),
            bid=11,
            ask=10,
            multiplier=100,
        )
