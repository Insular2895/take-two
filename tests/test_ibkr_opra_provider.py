from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from take_two_options.cli import app
from take_two_options.opra import ibkr_official
from take_two_options.opra.contracts import (
    BrokerWhatIfEvidence,
    IbkrTwsProviderConfig,
    LiveChainRequest,
    LiveComboLeg,
    LiveComboQuoteRequest,
)
from take_two_options.opra.ibkr_provider import (
    IbkrGovernanceError,
    IbkrProviderError,
    IbkrReadOnlyMarketDataProvider,
    IbkrReadPolicy,
    IbkrTransientError,
    RawIbkrChainSnapshot,
    RawIbkrComboQuote,
    RawIbkrHealth,
    RawIbkrOptionContract,
    RawIbkrOptionQuote,
    live_chain_to_market_snapshot,
)

NOW = datetime(2026, 9, 16, 19, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeTransport:
    def __init__(self, snapshot: RawIbkrChainSnapshot) -> None:
        self.snapshot = snapshot
        self.chain_calls = 0
        self.health_calls = 0
        self.combo_calls = 0
        self.transient_failures = 0

    def health(self, config: IbkrTwsProviderConfig) -> RawIbkrHealth:
        self.health_calls += 1
        return RawIbkrHealth(True, True, NOW, "OK")

    def fetch_chain(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveChainRequest,
    ) -> RawIbkrChainSnapshot:
        self.chain_calls += 1
        if self.transient_failures:
            self.transient_failures -= 1
            raise IbkrTransientError("temporary")
        return self.snapshot

    def fetch_combo_quote(
        self,
        config: IbkrTwsProviderConfig,
        request: LiveComboQuoteRequest,
    ) -> RawIbkrComboQuote:
        self.combo_calls += 1
        return RawIbkrComboQuote(
            bid_net_debit=5.05,
            ask_net_debit=5.45,
            quote_timestamp=NOW - timedelta(seconds=1),
            received_at=NOW,
            market_data_type="live",
            price_convention_verified=True,
        )


def config() -> IbkrTwsProviderConfig:
    return IbkrTwsProviderConfig(
        provider="ibkr_gateway",
        host="127.0.0.1",
        port=4002,
        client_id=17,
        session_mode="paper",
        market_data_type="live",
    )


def contract(con_id: int = 101, *, right: str = "C") -> RawIbkrOptionContract:
    return RawIbkrOptionContract(
        con_id=con_id,
        ticker="TTWO",
        local_symbol=f"TTWO  270115{right}00250000",
        trading_class="TTWO",
        expiration=date(2027, 1, 15),
        strike=250,
        right=right,  # type: ignore[arg-type]
        multiplier=100,
        exchange="SMART",
        currency="USD",
    )


def quote(con_id: int = 101, *, right: str = "C") -> RawIbkrOptionQuote:
    return RawIbkrOptionQuote(
        contract=contract(con_id, right=right),
        bid=6.2,
        ask=6.4,
        bid_size=12,
        ask_size=10,
        volume=300,
        open_interest=1_200,
        implied_volatility=0.42,
        delta=0.55,
        gamma=0.01,
        vega=0.25,
        theta=-0.08,
        rho=None,
        quote_timestamp=NOW - timedelta(seconds=1),
        received_at=NOW,
        timestamp_source="provider",
        market_data_type="live",
        provider_greek_convention="fixture",
        provider_stream="fixture",
    )


def raw_chain(*quotes: RawIbkrOptionQuote) -> RawIbkrChainSnapshot:
    values = quotes or (quote(),)
    return RawIbkrChainSnapshot(
        requested_at=NOW - timedelta(seconds=2),
        received_at=NOW,
        underlying_price=240,
        underlying_quote_timestamp=NOW - timedelta(seconds=1),
        underlying_received_at=NOW,
        underlying_timestamp_source="provider",
        underlying_market_data_type="live",
        quotes=tuple(values),
        discovered_contract_count=len(values),
        contract_discovery_complete=True,
        quote_collection_complete=True,
        server_version="fixture",
    )


def chain_request() -> LiveChainRequest:
    return LiveChainRequest(
        ticker="TTWO",
        as_of=NOW,
        expiration_start=date(2027, 1, 1),
        expiration_end=date(2027, 2, 1),
        maximum_quote_age_seconds=10,
        minimum_strike=200,
        maximum_strike=300,
    )


def provider(
    transport: FakeTransport,
    *,
    entitlement: bool = True,
    licence: bool = True,
    clock: FakeClock | None = None,
) -> IbkrReadOnlyMarketDataProvider:
    clock = clock or FakeClock()
    return IbkrReadOnlyMarketDataProvider(
        config(),
        transport,
        entitlement_confirmed=entitlement,
        license_reviewed=licence,
        policy=IbkrReadPolicy(
            maximum_attempts=2,
            retry_delay_seconds=0.1,
            minimum_request_interval_seconds=0.1,
            cache_ttl_seconds=5,
        ),
        now=lambda: NOW,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


def test_governance_gates_block_before_transport() -> None:
    transport = FakeTransport(raw_chain())
    with pytest.raises(IbkrGovernanceError, match="ENTITLEMENT"):
        provider(transport, entitlement=False).get_option_chain(chain_request())
    with pytest.raises(IbkrGovernanceError, match="LICENSE"):
        provider(transport, licence=False).get_option_chain(chain_request())
    assert transport.chain_calls == 0


def test_live_session_and_non_allowlisted_ticker_are_rejected() -> None:
    live = config().model_copy(update={"session_mode": "live"})
    with pytest.raises(IbkrGovernanceError, match="LIVE_SESSION_FORBIDDEN"):
        IbkrReadOnlyMarketDataProvider(
            live,
            FakeTransport(raw_chain()),
            entitlement_confirmed=True,
            license_reviewed=True,
        )
    request = chain_request().model_copy(update={"ticker": "AAPL"})
    with pytest.raises(IbkrGovernanceError, match="ALLOWLIST"):
        provider(FakeTransport(raw_chain())).get_option_chain(request)


def test_chain_is_qualified_normalised_hashed_and_promotion_eligible() -> None:
    result = provider(FakeTransport(raw_chain())).get_option_chain(chain_request())
    assert result.ticker == "TTWO"
    assert result.contract_discovery_complete is True
    assert result.quote_collection_complete is True
    assert result.promotion_eligible is True
    assert result.missing_quote_count == 0
    assert result.quotes[0].con_id == 101
    assert result.quotes[0].volume == 300
    assert result.quotes[0].open_interest == 1_200
    assert result.quotes[0].delta == 0.55
    assert len(result.provider_metadata_hash) == 64
    assert len(result.raw_snapshot_hash) == 64


def test_client_receipt_timestamp_and_delayed_data_cannot_be_promoted() -> None:
    item = quote()
    changed = RawIbkrOptionQuote(
        **{
            **item.__dict__,
            "quote_timestamp": None,
            "timestamp_source": "client_received_at",
            "market_data_type": "delayed",
        }
    )
    result = provider(FakeTransport(raw_chain(changed))).get_option_chain(chain_request())
    assert result.promotion_eligible is False
    assert any("client receipt" in warning for warning in result.warnings)
    assert any("not labelled as live" in warning for warning in result.warnings)


def test_underlying_timestamp_and_market_type_are_required_for_promotion() -> None:
    changed = RawIbkrChainSnapshot(
        **{
            **raw_chain().__dict__,
            "underlying_quote_timestamp": None,
            "underlying_timestamp_source": "client_received_at",
            "underlying_market_data_type": "delayed",
        }
    )
    result = provider(FakeTransport(changed)).get_option_chain(chain_request())
    assert result.promotion_eligible is False
    assert any("Underlying freshness" in warning for warning in result.warnings)
    assert any("Underlying snapshot" in warning for warning in result.warnings)


def test_live_capture_rejects_a_stale_as_of_before_transport() -> None:
    transport = FakeTransport(raw_chain())
    request = chain_request().model_copy(update={"as_of": NOW - timedelta(minutes=5)})
    with pytest.raises(IbkrGovernanceError, match="AS_OF_OUTSIDE_CAPTURE_WINDOW"):
        provider(transport).get_option_chain(request)
    assert transport.chain_calls == 0


def test_missing_or_crossed_quotes_remain_visible_as_incomplete() -> None:
    good = quote()
    bad = quote(102, right="P")
    bad = RawIbkrOptionQuote(**{**bad.__dict__, "bid": 7.0, "ask": 6.0})
    result = provider(FakeTransport(raw_chain(good, bad))).get_option_chain(chain_request())
    assert result.returned_quote_count == 1
    assert result.missing_quote_count == 1
    assert result.quote_collection_complete is False
    assert result.promotion_eligible is False


def test_duplicate_contract_identity_fails_closed() -> None:
    transport = FakeTransport(raw_chain(quote(), quote()))
    with pytest.raises(IbkrProviderError, match="DUPLICATE_OPTION_CON_ID"):
        provider(transport).get_option_chain(chain_request())


def test_cache_and_bounded_transient_retry_are_deterministic() -> None:
    clock = FakeClock()
    transport = FakeTransport(raw_chain())
    current = provider(transport, clock=clock)
    transport.transient_failures = 1
    first = current.get_option_chain(chain_request())
    second = current.get_option_chain(chain_request())
    assert first is second
    assert transport.chain_calls == 2
    clock.value += 6
    current.get_option_chain(chain_request())
    assert transport.chain_calls == 3
    diagnostics = current.diagnostics()
    assert diagnostics.read_operations == 2
    assert diagnostics.transport_attempts == 3
    assert diagnostics.transient_failures == 1
    assert diagnostics.retry_exhaustions == 0
    assert diagnostics.cache_hits == 1
    assert diagnostics.cache_misses == 2
    assert diagnostics.cache_expirations == 1
    assert diagnostics.stale_fallbacks == 0


def test_retry_exhaustion_never_returns_an_expired_cache_entry() -> None:
    clock = FakeClock()
    transport = FakeTransport(raw_chain())
    current = provider(transport, clock=clock)
    captured = current.get_option_chain(chain_request())
    clock.value += 6
    transport.transient_failures = 2
    with pytest.raises(IbkrProviderError, match="READ_RETRY_EXHAUSTED"):
        current.get_option_chain(chain_request())
    diagnostics = current.diagnostics()
    assert captured.snapshot_id
    assert diagnostics.retry_exhaustions == 1
    assert diagnostics.cache_expirations == 1
    assert diagnostics.stale_fallbacks == 0


def test_chain_converts_to_canonical_market_snapshot_without_inventing_inputs() -> None:
    chain = provider(FakeTransport(raw_chain())).get_option_chain(chain_request())
    snapshot = live_chain_to_market_snapshot(chain)
    assert snapshot.quote_quality == "live_broker"
    assert snapshot.quotes[0].multiplier == 100
    assert snapshot.quotes[0].multiplier_status.value == "KNOWN"
    assert snapshot.risk_free_rate is None
    assert snapshot.continuous_dividend_yield is None
    assert snapshot.lineage is not None
    assert snapshot.lineage.dataset_hash == chain.raw_snapshot_hash or len(
        snapshot.lineage.dataset_hash
    ) == 64


def test_combo_quote_compares_bag_with_executable_leg_synthetic() -> None:
    transport = FakeTransport(raw_chain())
    request = LiveComboQuoteRequest(
        candidate_id="candidate-1",
        ticker="TTWO",
        requested_at=NOW,
        maximum_quote_age_seconds=10,
        legs=[
            LiveComboLeg(con_id=101, action="BUY", bid=6.2, ask=6.4),
            LiveComboLeg(con_id=102, action="SELL", bid=1.0, ask=1.1),
        ],
    )
    result = provider(transport).get_combo_quote(request)
    assert result.synthetic_bid_net_debit == pytest.approx(5.1)
    assert result.synthetic_ask_net_debit == pytest.approx(5.4)
    assert result.maximum_absolute_divergence == pytest.approx(0.05)
    assert result.comparison_confirmed is True
    assert result.quote_freshness_verified is True
    assert result.price_convention_verified is True
    assert result.transmit is False


def test_unverified_combo_keeps_observed_prices_but_not_confirmation() -> None:
    transport = FakeTransport(raw_chain())
    transport.fetch_combo_quote = lambda config, request: RawIbkrComboQuote(  # type: ignore[method-assign]
        bid_net_debit=5.05,
        ask_net_debit=5.45,
        quote_timestamp=None,
        received_at=NOW,
        market_data_type="delayed",
        price_convention_verified=False,
    )
    request = LiveComboQuoteRequest(
        candidate_id="candidate-2",
        ticker="TTWO",
        requested_at=NOW,
        maximum_quote_age_seconds=10,
        legs=[
            LiveComboLeg(con_id=101, action="BUY", bid=6.2, ask=6.4),
            LiveComboLeg(con_id=102, action="SELL", bid=1.0, ask=1.1),
        ],
    )
    result = provider(transport).get_combo_quote(request)
    assert result.bid_net_debit == pytest.approx(5.05)
    assert result.maximum_absolute_divergence == pytest.approx(0.05)
    assert result.broker_quote_complete is True
    assert result.quote_freshness_verified is False
    assert result.comparison_confirmed is False


def test_what_if_evidence_is_ingestion_only_and_preserves_unknowns() -> None:
    evidence = BrokerWhatIfEvidence(
        candidate_id="candidate-1",
        observed_at=NOW,
        currency="USD",
        estimated_commission=None,
        initial_margin_change=None,
        source_id="future-redacted-observation",
        complete=False,
        warnings=["Not requested by this read-only code path."],
    )
    assert evidence.estimated_commission is None
    assert evidence.transmit is False
    assert evidence.what_if is True


def test_official_transport_source_contains_no_order_capability() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src/take_two_options/opra/ibkr_official.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "placeOrder(",
        "cancelOrder(",
        "reqGlobalCancel(",
        "exerciseOptions(",
        "ibapi.order",
    ):
        assert forbidden not in source


def test_official_transport_restricts_hosts_and_paper_account_shape() -> None:
    ibkr_official._require_loopback("127.0.0.1")
    ibkr_official._require_loopback("::1")
    ibkr_official._require_loopback("localhost")
    with pytest.raises(IbkrProviderError, match="HOST_MUST_BE_LOOPBACK"):
        ibkr_official._require_loopback("192.0.2.12")
    assert ibkr_official._paper_account(("DU123",)) is True
    assert ibkr_official._paper_account(("U123",)) is False
    assert ibkr_official._paper_account(("DU123", "DU456")) is False


def test_official_expiration_discovery_is_filtered_and_sorted() -> None:
    request = chain_request().model_copy(update={"maximum_expirations": 2})
    parameters = [
        {
            "exchange": "SMART",
            "trading_class": "TTWO",
            "expirations": {"20261218", "20270115", "20270122", "invalid"},
        },
        {
            "exchange": "CBOE",
            "trading_class": "OTHER",
            "expirations": {"20270129"},
        },
    ]
    assert ibkr_official._requested_expirations(parameters, request) == [
        "20270115",
        "20270122",
    ]
    assert ibkr_official._trading_classes(parameters) == ["TTWO"]


def test_official_contract_details_are_normalised_without_guessing() -> None:
    raw_contract = SimpleNamespace(
        conId=501,
        symbol="TTWO",
        localSymbol="TTWO  270115C00250000",
        tradingClass="TTWO",
        lastTradeDateOrContractMonth="20270115",
        strike=250.0,
        right="C",
        multiplier="100",
        exchange="SMART",
        currency="USD",
    )
    malformed = SimpleNamespace(
        conId=0,
        symbol="TTWO",
        lastTradeDateOrContractMonth="invalid",
        strike=0,
        right="",
        multiplier="",
    )
    details = [SimpleNamespace(contract=raw_contract), SimpleNamespace(contract=malformed)]
    result = ibkr_official._normalise_contract_details(details, request=chain_request())
    assert list(result) == [501]
    assert result[501].multiplier == 100
    assert result[501].expiration == date(2027, 1, 15)


def test_official_raw_quote_maps_option_specific_volume_and_oi() -> None:
    result = ibkr_official._raw_option_quote(
        contract(),
        {
            "bid": 6.2,
            "ask": 6.4,
            "volume": 99,
            "call_volume": 300,
            "call_open_interest": 1_200,
            "implied_volatility": 0.42,
            "delta": 0.55,
        },
        NOW,
        1,
    )
    assert result.volume == 300
    assert result.open_interest == 1_200
    assert result.market_data_type == "live"
    assert result.timestamp_source == "client_received_at"


def test_cli_requires_explicit_connection_flag_before_importing_ibapi(tmp_path: Path) -> None:
    output = tmp_path / "chain.json"
    result = CliRunner().invoke(
        app,
        [
            "data",
            "ibkr-chain",
            "--expiration-start",
            "2027-01-01",
            "--expiration-end",
            "2027-02-01",
            "--json-out",
            str(output),
        ],
    )
    assert result.exit_code == 2
    assert "connection not attempted" in result.output
    assert not output.exists()
