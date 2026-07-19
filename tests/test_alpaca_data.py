from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from take_two_options.alpaca_data import (
    AlpacaBacktestCaseSpec,
    AlpacaBacktestLegSpec,
    AlpacaCredentials,
    AlpacaDataError,
    AlpacaOptionBacktestSpec,
    AlpacaReadOnlyMarketData,
)
from take_two_options.backtesting import run_backtest
from take_two_options.domain import ModelReadiness, PositionSide


def _bar(symbol: str, timestamp: datetime, close: float) -> SimpleNamespace:
    return SimpleNamespace(
        symbol=symbol,
        timestamp=timestamp,
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=1_000.0,
        trade_count=50.0,
        vwap=close,
    )


class FakeStockClient:
    def __init__(self, bars: list[SimpleNamespace]) -> None:
        self.bars = bars
        self.last_request: object | None = None

    def get_stock_bars(self, request_params: object) -> SimpleNamespace:
        self.last_request = request_params
        return SimpleNamespace(data={"TTWO": self.bars})


class FakeOptionClient:
    def __init__(self, bars: dict[str, list[SimpleNamespace]]) -> None:
        self.bars = bars
        self.last_bars_request: object | None = None
        self.last_chain_request: object | None = None

    def get_option_bars(self, request_params: object) -> SimpleNamespace:
        self.last_bars_request = request_params
        return SimpleNamespace(data=self.bars)

    def get_option_chain(self, request_params: object) -> dict[str, SimpleNamespace]:
        self.last_chain_request = request_params
        quote = SimpleNamespace(
            timestamp=datetime(2026, 7, 19, 14, 0, tzinfo=UTC),
            bid_price=10.0,
            ask_price=10.5,
            bid_size=4.0,
            ask_size=6.0,
        )
        trade = SimpleNamespace(
            timestamp=datetime(2026, 7, 19, 13, 59, tzinfo=UTC),
            price=10.25,
        )
        greeks = SimpleNamespace(delta=0.5, gamma=0.01, theta=-0.05, vega=0.3, rho=0.2)
        return {
            "TTWO270115C00260000": SimpleNamespace(
                latest_quote=quote,
                latest_trade=trade,
                implied_volatility=0.36,
                greeks=greeks,
            )
        }


def _client(
    stock_bars: list[SimpleNamespace], option_bars: dict[str, list[SimpleNamespace]]
) -> AlpacaReadOnlyMarketData:
    return AlpacaReadOnlyMarketData(
        stock_client=FakeStockClient(stock_bars),
        option_client=FakeOptionClient(option_bars),
        options_feed_label="indicative",
    )


def test_credentials_are_environment_only_and_repr_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_API_SECRET", raising=False)

    with pytest.raises(AlpacaDataError, match="credentials are missing"):
        AlpacaCredentials.from_env()

    monkeypatch.setenv("APCA_API_KEY_ID", "key-id")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "super-secret")
    credentials = AlpacaCredentials.from_env()

    assert "key-id" not in repr(credentials)
    assert "super-secret" not in repr(credentials)


def test_real_stock_bars_become_source_backed_calibration_dataset() -> None:
    start = datetime(2026, 1, 2, tzinfo=UTC)
    bars = [_bar("TTWO", start + timedelta(days=index), 200.0 + index) for index in range(12)]
    client = _client(bars, {})

    dataset = client.calibration_dataset(
        ticker="TTWO",
        start=start,
        end=start + timedelta(days=20),
        training_cutoff=start + timedelta(days=15),
        retrieved_at=start + timedelta(days=30),
    )

    assert dataset.evidence_class == "source_backed_calibration"
    assert dataset.source.source_type == "alpaca_market_data_api"
    assert len(dataset.points) == 12
    assert dataset.points[0].data_available_at == dataset.points[0].timestamp + timedelta(days=1)


def test_option_bars_build_proxy_priced_screen_grade_backtest() -> None:
    symbol = "TTWO270115C00260000"
    bars = [
        _bar(symbol, datetime(2026, 5, 1, tzinfo=UTC), 10.0),
        _bar(symbol, datetime(2026, 5, 10, tzinfo=UTC), 14.0),
        _bar(symbol, datetime(2026, 6, 1, tzinfo=UTC), 9.0),
        _bar(symbol, datetime(2026, 6, 10, tzinfo=UTC), 7.0),
    ]
    client = _client([], {symbol: bars})
    leg = AlpacaBacktestLegSpec(symbol=symbol, side=PositionSide.LONG)
    spec = AlpacaOptionBacktestSpec(
        ticker="TTWO",
        timeframe="1Day",
        cases=[
            AlpacaBacktestCaseSpec(
                case_id="train",
                split="train",
                entry_timestamp=datetime(2026, 5, 3, tzinfo=UTC),
                exit_timestamp=datetime(2026, 5, 12, tzinfo=UTC),
                model_calibrated_through=datetime(2026, 4, 30, tzinfo=UTC),
                legs=[leg],
                slippage_per_contract_per_side=1.5,
            ),
            AlpacaBacktestCaseSpec(
                case_id="test",
                split="test",
                entry_timestamp=datetime(2026, 6, 3, tzinfo=UTC),
                exit_timestamp=datetime(2026, 6, 12, tzinfo=UTC),
                model_calibrated_through=datetime(2026, 5, 31, tzinfo=UTC),
                legs=[leg],
                slippage_per_contract_per_side=1.5,
            ),
        ],
    )

    dataset = client.option_backtest_dataset(spec, retrieved_at=datetime(2026, 7, 1, tzinfo=UTC))
    report = run_backtest(dataset)

    assert dataset.evidence_class == "source_backed_backtest"
    assert dataset.cases[0].legs[0].entry_quote.price_basis == "option_bar_close_proxy"
    assert report.execution_price_quality == "bar_close_proxy"
    assert report.model_readiness is ModelReadiness.SCREEN_GRADE
    assert any("not NBBO" in warning for warning in report.warnings)


def test_option_history_before_february_2024_is_rejected() -> None:
    symbol = "TTWO240119C00100000"
    client = _client([], {symbol: []})

    with pytest.raises(AlpacaDataError, match="starts in February 2024"):
        client.option_bars(
            symbols=[symbol],
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 2, 2, tzinfo=UTC),
            timeframe="1Day",
        )


def test_option_chain_normalizes_quotes_iv_and_greeks() -> None:
    client = _client([], {})

    export = client.option_chain(
        ticker="TTWO",
        feed="indicative",
        retrieved_at=datetime(2026, 7, 19, 14, 1, tzinfo=UTC),
    )

    assert export.order_capability == "forbidden"
    assert export.contracts[0].bid == 10.0
    assert export.contracts[0].implied_volatility == 0.36
    assert export.contracts[0].delta == 0.5
