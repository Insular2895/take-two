from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from take_two_options.cli import app
from take_two_options.domain import OptionType
from take_two_options.opra.contracts import (
    LiveChainRequest,
    LiveComboQuote,
    LiveComboQuoteRequest,
    LiveOptionChainSnapshot,
    LiveOptionQuote,
    ProviderHealth,
)
from take_two_options.opra.ibkr_provider import IbkrProviderDiagnostics, IbkrProviderError
from take_two_options.opra.validation import (
    ComboValidationLeg,
    ComboValidationPlan,
    render_ibkr_validation_markdown,
    validate_ibkr_read_only,
)

NOW = datetime(2026, 9, 17, 8, 0, tzinfo=UTC)


def _quote(con_id: int, strike: float) -> LiveOptionQuote:
    return LiveOptionQuote(
        option_symbol=f"TTWO  270115C{int(strike * 1_000):08d}",
        ticker="TTWO",
        option_type=OptionType.CALL,
        strike=strike,
        expiration=date(2027, 1, 15),
        quote_timestamp=NOW - timedelta(seconds=1),
        received_at=NOW,
        bid=6.0 if strike == 240 else 2.0,
        ask=6.2 if strike == 240 else 2.2,
        bid_size=10,
        ask_size=12,
        volume=100,
        open_interest=500,
        implied_volatility=0.4,
        delta=0.55,
        gamma=0.01,
        vega=0.2,
        theta=-0.05,
        multiplier=100,
        exchange="SMART",
        con_id=con_id,
        local_symbol=f"TTWO  270115C{int(strike * 1_000):08d}",
        trading_class="TTWO",
        currency="USD",
        exercise_style="american",
        quote_timestamp_source="provider",
        market_data_type="live",
    )


def _snapshot(*, promotable: bool = True) -> LiveOptionChainSnapshot:
    quotes = [_quote(101, 240), _quote(102, 260)]
    return LiveOptionChainSnapshot(
        snapshot_id="ibkr-fixture-validation",
        provider="ibkr_gateway",
        ticker="TTWO",
        requested_at=NOW - timedelta(seconds=2),
        received_at=NOW,
        underlying_price=245,
        quotes=quotes,
        provider_metadata_hash="a" * 64,
        raw_snapshot_hash="b" * 64,
        source_latency_milliseconds=2_000,
        underlying_quote_timestamp=(NOW - timedelta(seconds=1) if promotable else None),
        underlying_received_at=NOW,
        underlying_timestamp_source="provider" if promotable else "client_received_at",
        underlying_market_data_type="live" if promotable else "delayed",
        requested_contract_count=2,
        returned_quote_count=2,
        missing_quote_count=0,
        contract_discovery_complete=True,
        quote_collection_complete=True,
        promotion_eligible=promotable,
    )


def _request() -> LiveChainRequest:
    return LiveChainRequest(
        ticker="TTWO",
        as_of=NOW,
        expiration_start=date(2027, 1, 1),
        expiration_end=date(2027, 2, 1),
        maximum_quote_age_seconds=30,
        minimum_strike=230,
        maximum_strike=270,
    )


class StubProvider:
    def __init__(self, snapshot: LiveOptionChainSnapshot) -> None:
        self.snapshot = snapshot
        self.health_calls = 0
        self.combo_request: LiveComboQuoteRequest | None = None

    def health(self) -> ProviderHealth:
        self.health_calls += 1
        return ProviderHealth(
            provider="ibkr_gateway",
            checked_at=NOW,
            status="available_read_only",
            entitlement_confirmed=True,
            message="OK",
        )

    def get_option_chain(self, request: LiveChainRequest) -> LiveOptionChainSnapshot:
        return self.snapshot

    def get_combo_quote(self, request: LiveComboQuoteRequest) -> LiveComboQuote:
        self.combo_request = request
        return LiveComboQuote(
            candidate_id=request.candidate_id,
            ticker=request.ticker,
            bid_net_debit=3.75,
            ask_net_debit=4.25,
            synthetic_bid_net_debit=3.8,
            synthetic_ask_net_debit=4.2,
            maximum_absolute_divergence=0.05,
            quote_timestamp=NOW - timedelta(seconds=1),
            received_at=NOW,
            source_id="ibkr-combo-fixture",
            market_data_type="live",
            broker_quote_complete=True,
            synthetic_quote_complete=True,
            quote_freshness_verified=True,
            price_convention_verified=True,
            comparison_confirmed=True,
        )

    def diagnostics(self) -> IbkrProviderDiagnostics:
        return IbkrProviderDiagnostics(
            captured_at=NOW,
            read_operations=1,
            transport_attempts=2,
            transient_failures=1,
            retry_exhaustions=0,
            pacing_wait_count=1,
            pacing_wait_seconds=0.1,
            cache_hits=0,
            cache_misses=1,
            cache_expirations=0,
        )


class FailedHealthProvider(StubProvider):
    def health(self) -> ProviderHealth:
        raise IbkrProviderError("IBKR_HANDSHAKE_TIMEOUT")


def _plan() -> ComboValidationPlan:
    return ComboValidationPlan(
        candidate_id="candidate-validation",
        ticker="TTWO",
        legs=[
            ComboValidationLeg(
                expiration=date(2027, 1, 15),
                strike=240,
                option_type=OptionType.CALL,
                action="BUY",
            ),
            ComboValidationLeg(
                expiration=date(2027, 1, 15),
                strike=260,
                option_type=OptionType.CALL,
                action="SELL",
            ),
        ],
    )


def test_validation_exercises_two_independent_sessions_and_chain() -> None:
    provider = StubProvider(_snapshot())
    outcome = validate_ibkr_read_only(
        provider,
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        now=lambda: NOW,
    )
    assert provider.health_calls == 2
    assert outcome.report.status == "CHAIN_PROMOTION_ELIGIBLE"
    assert outcome.report.independent_second_session_verified is True
    assert outcome.report.chain is not None
    assert outcome.report.chain.greeks_complete_count == 2
    assert outcome.report.request == _request()
    assert outcome.report.broker_read_observed is True
    assert outcome.report.provider_diagnostics is not None
    assert outcome.report.provider_diagnostics.transient_failures == 1
    assert outcome.report.order_capability == "forbidden"
    assert outcome.snapshot is provider.snapshot


def test_non_promotable_capture_is_observed_without_false_failure() -> None:
    outcome = validate_ibkr_read_only(
        StubProvider(_snapshot(promotable=False)),
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="delayed",
        exercise_second_session=False,
        now=lambda: NOW,
    )
    assert outcome.report.status == "CAPTURED_NOT_PROMOTABLE"
    assert any(
        item.check_id == "timestamp_provenance" and item.status == "WARN"
        for item in outcome.report.checks
    )


def test_combo_plan_resolves_contracts_and_confirms_bag_comparison() -> None:
    provider = StubProvider(_snapshot())
    outcome = validate_ibkr_read_only(
        provider,
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        combo_plan=_plan(),
        now=lambda: NOW,
    )
    assert outcome.report.status == "CHAIN_AND_COMBO_PROMOTION_ELIGIBLE"
    assert provider.combo_request is not None
    assert [leg.con_id for leg in provider.combo_request.legs] == [101, 102]
    assert provider.combo_request.legs[0].bid == 6.0
    assert outcome.report.combo is not None
    assert outcome.report.combo.comparison_confirmed is True


def test_unresolvable_requested_combo_fails_safe_but_preserves_chain_evidence() -> None:
    plan = _plan().model_copy(
        update={
            "legs": [
                _plan().legs[0],
                _plan().legs[1].model_copy(update={"strike": 250}),
            ]
        }
    )
    outcome = validate_ibkr_read_only(
        StubProvider(_snapshot()),
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        combo_plan=plan,
        now=lambda: NOW,
    )
    assert outcome.report.status == "FAILED_SAFE"
    assert outcome.report.failure_code == "IBKR_COMBO_LEG_RESOLUTION_NOT_UNIQUE"
    assert outcome.report.chain is not None
    assert outcome.snapshot is not None


def test_health_failure_produces_redacted_machine_report() -> None:
    outcome = validate_ibkr_read_only(
        FailedHealthProvider(_snapshot()),
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        now=lambda: NOW,
    )
    assert outcome.report.status == "FAILED_SAFE"
    assert outcome.report.failure_code == "IBKR_HANDSHAKE_TIMEOUT"
    assert outcome.report.maximum_claim == "software_only"
    assert outcome.report.broker_read_observed is False
    assert outcome.snapshot is None


def test_example_combo_plan_is_rejected_before_any_broker_read() -> None:
    provider = StubProvider(_snapshot())
    outcome = validate_ibkr_read_only(
        provider,
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        combo_plan=_plan().model_copy(update={"example_only": True}),
        now=lambda: NOW,
    )
    assert outcome.report.status == "FAILED_SAFE"
    assert outcome.report.failure_code == "IBKR_COMBO_PLAN_MARKED_EXAMPLE_ONLY"
    assert outcome.report.maximum_claim == "software_only"
    assert outcome.report.broker_read_observed is False
    assert provider.health_calls == 0


def test_combo_plan_outside_request_is_rejected_before_any_broker_read() -> None:
    provider = StubProvider(_snapshot())
    plan = _plan().model_copy(
        update={
            "legs": [
                _plan().legs[0],
                _plan().legs[1].model_copy(update={"strike": 999}),
            ]
        }
    )
    outcome = validate_ibkr_read_only(
        provider,
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        combo_plan=plan,
        now=lambda: NOW,
    )
    assert outcome.report.failure_code == "IBKR_COMBO_PLAN_STRIKE_OUTSIDE_REQUEST"
    assert provider.health_calls == 0


def test_combo_plan_rejects_the_same_contract_on_both_sides() -> None:
    with pytest.raises(ValidationError, match="legs must be distinct"):
        ComboValidationPlan(
            candidate_id="self-cancelling",
            ticker="TTWO",
            legs=[
                _plan().legs[0],
                _plan().legs[0].model_copy(update={"action": "SELL"}),
            ],
        )


def test_human_markdown_states_claim_boundary_and_contains_no_connection_identifiers() -> None:
    report = validate_ibkr_read_only(
        StubProvider(_snapshot()),
        _request(),
        provider_name="ibkr_gateway",
        requested_market_data_type="live",
        now=lambda: NOW,
    ).report
    markdown = render_ibkr_validation_markdown(report)
    assert "broker_read_only_chain_promotable" in markdown
    assert "Capacité d’ordre : `forbidden`" in markdown
    assert "Repli vers donnée périmée : `0`" in markdown
    assert "client_id" not in markdown
    assert "DU" not in markdown


def test_validation_cli_requires_explicit_connection_before_creating_reports(
    tmp_path: Path,
) -> None:
    report = tmp_path / "validation.json"
    result = CliRunner().invoke(
        app,
        [
            "data",
            "ibkr-validate",
            "--expiration-start",
            "2027-01-01",
            "--expiration-end",
            "2027-02-01",
            "--report-json-out",
            str(report),
        ],
    )
    assert result.exit_code == 2
    assert "connection not attempted" in result.output
    assert not report.exists()
