import json
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from take_two_options.backtesting import run_backtest
from take_two_options.domain import ModelReadiness, OptionType, PositionSide
from take_two_options.marketdata_data import (
    MarketDataBacktestCaseSpec,
    MarketDataBacktestLegSpec,
    MarketDataCredentials,
    MarketDataError,
    MarketDataHttpResponse,
    MarketDataOptionBacktestSpec,
    MarketDataReadOnlyClient,
    parse_occ_option_symbol,
)

SYMBOL = "TTWO261120C00220000"
EXPIRATION = datetime(2026, 11, 20, 21, 0, tzinfo=UTC)


def _payload(
    quote_date: date,
    *,
    symbol: str = SYMBOL,
    bid: float | None = 19.0,
    ask: float | None = 21.0,
    spot: float = 220.0,
) -> dict[str, object]:
    updated = datetime(
        quote_date.year, quote_date.month, quote_date.day, 20, 0, tzinfo=UTC
    )
    return {
        "s": "ok",
        "optionSymbol": [symbol],
        "underlying": ["TTWO"],
        "expiration": [int(EXPIRATION.timestamp())],
        "side": ["call"],
        "strike": [220.0],
        "firstTraded": [int(datetime(2026, 1, 2, tzinfo=UTC).timestamp())],
        "dte": [(EXPIRATION.date() - quote_date).days],
        "ask": [ask],
        "askSize": [8],
        "bid": [bid],
        "bidSize": [6],
        "mid": [(bid + ask) / 2 if bid is not None and ask is not None else None],
        "last": [20.0],
        "volume": [125],
        "openInterest": [1_250],
        "underlyingPrice": [spot],
        "updated": [int(updated.timestamp())],
        "iv": [None],
        "delta": [None],
        "gamma": [None],
        "theta": [None],
        "vega": [None],
    }


class FakeTransport:
    def __init__(self, payloads: dict[date, dict[str, object]]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get_json(
        self, *, url: str, headers: dict[str, str], timeout: float
    ) -> MarketDataHttpResponse:
        del timeout
        self.calls.append((url, dict(headers)))
        query = parse_qs(urlparse(url).query)
        quote_date = date.fromisoformat(query["date"][0])
        return MarketDataHttpResponse(
            payload=self.payloads[quote_date],
            headers={
                "X-Api-Ratelimit-Consumed": "1",
                "X-Api-Ratelimit-Remaining": "99",
                "X-Api-Ratelimit-Limit": "100",
                "X-Api-Ratelimit-Reset": "1784549400",
            },
        )


def _client(tmp_path: Path, transport: FakeTransport) -> MarketDataReadOnlyClient:
    return MarketDataReadOnlyClient(
        credentials=MarketDataCredentials(token="secret-token"),
        transport=transport,
        cache_dir=tmp_path,
    )


def test_credentials_are_environment_only_and_repr_is_redacted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MARKETDATA_TOKEN", raising=False)
    monkeypatch.delenv("MARKETDATA_API_TOKEN", raising=False)
    with pytest.raises(MarketDataError, match="token is missing"):
        MarketDataCredentials.from_env()

    monkeypatch.setenv("MARKETDATA_TOKEN", "super-secret")
    credentials = MarketDataCredentials.from_env()
    assert "super-secret" not in repr(credentials)


def test_occ_symbol_parser_preserves_contract_identity() -> None:
    contract = parse_occ_option_symbol("O:TTWO261120C00220000")

    assert contract.symbol == SYMBOL
    assert contract.root == "TTWO"
    assert contract.expiration == date(2026, 11, 20)
    assert contract.option_type is OptionType.CALL
    assert contract.strike == 220.0

    with pytest.raises(ValueError, match="invalid OCC"):
        parse_occ_option_symbol("TTWO-CALL-220")


def test_historical_chain_is_normalized_analysed_and_cached(tmp_path: Path) -> None:
    quote_date = date(2026, 5, 1)
    transport = FakeTransport({quote_date: _payload(quote_date)})
    client = _client(tmp_path, transport)
    retrieved_at = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)

    first = client.historical_chain(
        ticker="TTWO",
        quote_date=quote_date,
        expiration=date(2026, 11, 20),
        side="call",
        strikes=[220.0],
        risk_free_rate=0.04,
        retrieved_at=retrieved_at,
    )
    second = client.historical_chain(
        ticker="TTWO",
        quote_date=quote_date,
        expiration=date(2026, 11, 20),
        side="call",
        strikes=[220.0],
        risk_free_rate=0.04,
        retrieved_at=retrieved_at,
    )

    record = first.contracts[0]
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert len(transport.calls) == 1
    assert record.bid == 19.0
    assert record.ask == 21.0
    assert record.open_interest == 1_250
    assert record.computed_analytics is not None
    assert record.computed_analytics.model_price == pytest.approx(20.0, abs=1e-5)
    assert first.usage.remaining == 99
    request_url, headers = transport.calls[0]
    assert "secret-token" not in request_url
    assert headers["Authorization"] == "Bearer secret-token"
    assert "secret-token" not in next(tmp_path.glob("*.json")).read_text(encoding="utf-8")


def test_cache_integrity_failure_is_blocking(tmp_path: Path) -> None:
    quote_date = date(2026, 5, 1)
    transport = FakeTransport({quote_date: _payload(quote_date)})
    client = _client(tmp_path, transport)
    client.historical_chain(ticker="TTWO", quote_date=quote_date)
    cache_path = next(tmp_path.glob("*.json"))
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    cached["payload"]["bid"] = [0.01]
    cache_path.write_text(json.dumps(cached), encoding="utf-8")

    with pytest.raises(MarketDataError, match="integrity check failed"):
        client.historical_chain(ticker="TTWO", quote_date=quote_date)


def test_malformed_cache_is_blocking_with_domain_error(tmp_path: Path) -> None:
    quote_date = date(2026, 5, 1)
    transport = FakeTransport({quote_date: _payload(quote_date)})
    client = _client(tmp_path, transport)
    client.historical_chain(ticker="TTWO", quote_date=quote_date)
    next(tmp_path.glob("*.json")).write_text("not-json", encoding="utf-8")

    with pytest.raises(MarketDataError, match="cache is invalid"):
        client.historical_chain(ticker="TTWO", quote_date=quote_date)


def test_wrong_session_and_crossed_quotes_are_rejected(tmp_path: Path) -> None:
    requested = date(2026, 5, 1)
    wrong_date_transport = FakeTransport({requested: _payload(date(2026, 4, 30))})
    with pytest.raises(MarketDataError, match="returned 2026-04-30"):
        _client(tmp_path / "wrong", wrong_date_transport).historical_chain(
            ticker="TTWO", quote_date=requested
        )

    crossed_transport = FakeTransport({requested: _payload(requested, bid=21.0, ask=19.0)})
    with pytest.raises(MarketDataError, match="crossed bid/ask"):
        _client(tmp_path / "crossed", crossed_transport).historical_chain(
            ticker="TTWO", quote_date=requested
        )


def test_eod_quotes_build_screen_grade_bid_ask_backtest(tmp_path: Path) -> None:
    dates_and_prices = {
        date(2026, 5, 1): (9.0, 10.0),
        date(2026, 5, 15): (13.0, 14.0),
        date(2026, 6, 1): (11.0, 12.0),
        date(2026, 6, 15): (8.0, 9.0),
    }
    transport = FakeTransport(
        {
            quote_date: _payload(quote_date, bid=prices[0], ask=prices[1])
            for quote_date, prices in dates_and_prices.items()
        }
    )
    leg = MarketDataBacktestLegSpec(
        symbol=SYMBOL,
        side=PositionSide.LONG,
        multiplier=100.0,
    )
    spec = MarketDataOptionBacktestSpec(
        ticker="TTWO",
        risk_free_rate=0.04,
        cases=[
            MarketDataBacktestCaseSpec(
                case_id="train",
                split="train",
                entry_quote_date=date(2026, 5, 1),
                exit_quote_date=date(2026, 5, 15),
                entry_timestamp=datetime(2026, 5, 1, 20, 1, tzinfo=UTC),
                exit_timestamp=datetime(2026, 5, 15, 20, 1, tzinfo=UTC),
                model_calibrated_through=datetime(2026, 4, 30, 20, 0, tzinfo=UTC),
                legs=[leg],
                slippage_per_contract_per_side=1.0,
            ),
            MarketDataBacktestCaseSpec(
                case_id="test",
                split="test",
                entry_quote_date=date(2026, 6, 1),
                exit_quote_date=date(2026, 6, 15),
                entry_timestamp=datetime(2026, 6, 1, 20, 1, tzinfo=UTC),
                exit_timestamp=datetime(2026, 6, 15, 20, 1, tzinfo=UTC),
                model_calibrated_through=datetime(2026, 5, 29, 20, 0, tzinfo=UTC),
                legs=[leg],
                slippage_per_contract_per_side=1.0,
            ),
        ],
    )

    dataset = _client(tmp_path, transport).option_backtest_dataset(
        spec, retrieved_at=datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
    )
    report = run_backtest(dataset)

    train = next(case for case in report.cases if case.case_id == "train")
    assert train.entry_outlay == 1_000.0
    assert train.exit_value == 1_300.0
    assert dataset.cases[0].legs[0].entry_quote.open_interest == 1_250
    assert dataset.cases[0].legs[0].entry_quote.price_basis == "eod_bid_ask"
    assert report.execution_price_quality == "historical_eod_bid_ask"
    assert report.model_readiness is ModelReadiness.SCREEN_GRADE
    assert any("does not replay intraday NBBO" in warning for warning in report.warnings)
    assert len(transport.calls) == 4


def test_example_backtest_spec_remains_valid() -> None:
    fixture_path = (
        Path(__file__).parents[1]
        / "fixtures"
        / "marketdata_tt_options_backtest_spec.example.json"
    )

    spec = MarketDataOptionBacktestSpec.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )

    assert spec.ticker == "TTWO"
    assert {case.split for case in spec.cases} == {"train", "test"}
    assert all(leg.multiplier == 100 for case in spec.cases for leg in case.legs)
