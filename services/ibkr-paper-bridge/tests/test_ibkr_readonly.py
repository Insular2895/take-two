from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from ttwo_ibkr_bridge.ibkr_readonly import (
    IbkrReadOnlyAdapter,
    IbkrReadOnlyConfig,
    RawIbkrSnapshot,
    RawPosition,
    RawPositionPnl,
    RawQuote,
    ReadOnlyAdapterError,
)


class FakeCollector:
    def __init__(self, snapshot: RawIbkrSnapshot) -> None:
        self._snapshot = snapshot

    def collect(self) -> RawIbkrSnapshot:
        return self._snapshot


def raw_snapshot(
    *,
    accounts: tuple[str, ...] = ("DU_REDACTED",),
    include_second_pnl: bool = True,
) -> RawIbkrSnapshot:
    observed = datetime(2026, 8, 25, 20, 0, tzinfo=UTC)
    positions = (
        RawPosition(
            account=accounts[0],
            con_id=101,
            symbol="TTWO",
            security_type="OPT",
            local_symbol="TTWO  270115C00250000",
            currency="USD",
            expiry="20270115",
            strike=Decimal("250"),
            right="C",
            multiplier="100",
            quantity=Decimal("2"),
            average_cost=Decimal("550.25"),
        ),
        RawPosition(
            account=accounts[0],
            con_id=102,
            symbol="TTWO",
            security_type="OPT",
            local_symbol="TTWO  270115C00300000",
            currency="USD",
            expiry="20270115",
            strike=Decimal("300"),
            right="C",
            multiplier="100",
            quantity=Decimal("-2"),
            average_cost=Decimal("95.10"),
        ),
    )
    pnl = [
        RawPositionPnl(
            account=accounts[0],
            con_id=101,
            daily_pnl=Decimal("20"),
            unrealized_pnl=Decimal("125"),
            realized_pnl=Decimal("0"),
            market_value=Decimal("1250"),
        )
    ]
    if include_second_pnl:
        pnl.append(
            RawPositionPnl(
                account=accounts[0],
                con_id=102,
                daily_pnl=Decimal("-5"),
                unrealized_pnl=Decimal("-25"),
                realized_pnl=Decimal("0"),
                market_value=Decimal("-210"),
            )
        )
    return RawIbkrSnapshot(
        gateway_connected=True,
        accounts=accounts,
        server_time_epoch=1_777_147_200,
        positions=positions,
        position_pnl=tuple(pnl),
        quotes=(
            RawQuote(
                con_id=101,
                bid=Decimal("6.10"),
                ask=Decimal("6.40"),
                last=Decimal("6.25"),
                close=Decimal("6.00"),
                mark=Decimal("6.25"),
                market_data_type=1,
                observed_at=observed,
            ),
            RawQuote(
                con_id=102,
                bid=Decimal("0.95"),
                ask=Decimal("1.15"),
                last=Decimal("1.05"),
                close=Decimal("1.00"),
                mark=Decimal("1.05"),
                market_data_type=3,
                observed_at=observed,
            ),
        ),
        error_codes=(2104, 2106),
        collected_at=observed,
    )


def test_configuration_rejects_non_loopback_live_ports_and_other_symbols() -> None:
    with pytest.raises(ValueError, match="loopback"):
        IbkrReadOnlyConfig(host="198.51.100.10").validate()
    with pytest.raises(ValueError, match="paper Gateway port"):
        IbkrReadOnlyConfig(port=4001).validate()
    with pytest.raises(ValueError, match="restricted to TTWO"):
        IbkrReadOnlyConfig(symbol="AAPL").validate()


def test_adapter_rejects_live_or_ambiguous_account_scope() -> None:
    live = raw_snapshot(accounts=("U_REDACTED",))
    with pytest.raises(ReadOnlyAdapterError, match="LIVE_ACCOUNT_FORBIDDEN"):
        IbkrReadOnlyAdapter(IbkrReadOnlyConfig(), FakeCollector(live)).snapshot()

    ambiguous = raw_snapshot(accounts=("DU_ONE", "DU_TWO"))
    with pytest.raises(ReadOnlyAdapterError, match="SCOPE_AMBIGUOUS"):
        IbkrReadOnlyAdapter(IbkrReadOnlyConfig(), FakeCollector(ambiguous)).snapshot()


def test_snapshot_is_redacted_and_aggregates_only_complete_broker_values() -> None:
    telemetry = IbkrReadOnlyAdapter(IbkrReadOnlyConfig(), FakeCollector(raw_snapshot())).snapshot()
    payload = telemetry.as_payload()

    assert telemetry.paper_account_verified is True
    assert telemetry.total_market_value == Decimal("1040")
    assert telemetry.total_daily_pnl == Decimal("15")
    assert telemetry.total_unrealized_pnl == Decimal("100")
    assert telemetry.quotes_complete is True
    assert telemetry.pnl_complete is True
    assert telemetry.positions[0].quote is not None
    assert telemetry.positions[0].quote.midpoint == Decimal("6.25")
    assert payload["mode"] == "PAPER_READ_ONLY"
    assert "DU_REDACTED" not in str(payload)
    assert payload["fee_reconciliation_status"] == (
        "LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES"
    )


def test_incomplete_pnl_never_becomes_a_false_total() -> None:
    telemetry = IbkrReadOnlyAdapter(
        IbkrReadOnlyConfig(),
        FakeCollector(raw_snapshot(include_second_pnl=False)),
    ).snapshot()
    assert telemetry.pnl_complete is False
    assert telemetry.total_market_value is None
    assert telemetry.total_daily_pnl is None
    assert telemetry.total_unrealized_pnl is None


def test_zero_positions_are_complete_zero_totals() -> None:
    raw = raw_snapshot()
    empty = RawIbkrSnapshot(
        gateway_connected=raw.gateway_connected,
        accounts=raw.accounts,
        server_time_epoch=raw.server_time_epoch,
        positions=(),
        position_pnl=(),
        quotes=(),
        error_codes=(),
        collected_at=raw.collected_at,
    )
    telemetry = IbkrReadOnlyAdapter(IbkrReadOnlyConfig(), FakeCollector(empty)).snapshot()
    assert telemetry.positions == ()
    assert telemetry.total_market_value == Decimal(0)
    assert telemetry.pnl_complete is True
    assert telemetry.quotes_complete is True


def test_readonly_adapter_is_not_wired_to_order_transmission() -> None:
    service_root = Path(__file__).resolve().parents[1]
    adapter_source = (service_root / "src/ttwo_ibkr_bridge/ibkr_readonly.py").read_text()
    main_source = (service_root / "src/ttwo_ibkr_bridge/main.py").read_text()

    for forbidden_call in (
        "placeOrder(",
        "cancelOrder(",
        "reqGlobalCancel(",
        "exerciseOptions(",
    ):
        assert forbidden_call not in adapter_source
    assert "DisabledGateway()" in main_source
    assert "IbkrReadOnlyAdapter" not in main_source
