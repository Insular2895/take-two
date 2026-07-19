from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

import pytest

from take_two_options.american import HistoricalOptionAnalytics
from take_two_options.domain import (
    EvidenceReference,
    EvidenceStatus,
    OptionType,
    StrategyKind,
)
from take_two_options.marketdata_data import (
    MarketDataChainExport,
    MarketDataOptionRecord,
    MarketDataRateLimit,
)
from take_two_options.marketdata_panel import (
    MarketDataPanelObservationSpec,
    MarketDataPanelSpec,
    estimate_selected_risk,
    run_marketdata_panel,
    select_marketdata_strategies,
)

EXPIRATION_DATE = date(2026, 2, 20)
EXPIRATION = datetime(2026, 2, 20, 21, 0, tzinfo=UTC)
OBSERVATIONS = [
    ("train-1", "train", date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 8)),
    ("train-2", "train", date(2026, 1, 9), date(2026, 1, 12), date(2026, 1, 15)),
    ("test-1", "test", date(2026, 1, 16), date(2026, 1, 20), date(2026, 1, 22)),
    ("test-2", "test", date(2026, 1, 23), date(2026, 1, 26), date(2026, 1, 29)),
]


def _symbol(option_type: OptionType, strike: float) -> str:
    right = "C" if option_type is OptionType.CALL else "P"
    return f"TTWO260220{right}{round(strike * 1000):08d}"


def _analytics(delta: float, target: float) -> HistoricalOptionAnalytics:
    return HistoricalOptionAnalytics(
        target_price=target,
        model_price=target,
        implied_volatility=0.4,
        delta=delta,
        gamma=0.01,
        theta=-0.05,
        vega=0.2,
        rho=0.1,
        risk_free_rate=0.04,
        continuous_dividend_yield=0.0,
        dividend_count=0,
    )


def _record(
    quote_date: date,
    option_type: OptionType,
    strike: float,
    bid: float,
    ask: float,
    *,
    delta: float | None = None,
    open_interest: float = 100,
) -> MarketDataOptionRecord:
    return MarketDataOptionRecord(
        option_symbol=_symbol(option_type, strike),
        underlying="TTWO",
        expiration=EXPIRATION,
        option_type=option_type,
        strike=strike,
        dte=(EXPIRATION_DATE - quote_date).days,
        quote_timestamp=datetime(
            quote_date.year, quote_date.month, quote_date.day, 20, 0, tzinfo=UTC
        ),
        bid=bid,
        ask=ask,
        bid_size=10,
        ask_size=10,
        mid=(bid + ask) / 2,
        last=(bid + ask) / 2,
        volume=20,
        open_interest=open_interest,
        underlying_price=100,
        computed_analytics=(_analytics(delta, (bid + ask) / 2) if delta is not None else None),
    )


def _signal_records(quote_date: date) -> list[MarketDataOptionRecord]:
    return [
        _record(quote_date, OptionType.CALL, 100, 4.8, 5.2, delta=0.55),
        _record(quote_date, OptionType.CALL, 110, 1.8, 2.2, delta=0.30),
        _record(quote_date, OptionType.PUT, 100, 4.8, 5.2, delta=-0.55),
        _record(quote_date, OptionType.PUT, 90, 1.8, 2.2, delta=-0.30),
    ]


def _execution_records(
    quote_date: date, *, exit_index: int | None = None
) -> list[MarketDataOptionRecord]:
    if exit_index is None:
        call_long_bid, call_short_ask = 4.8, 2.2
        put_long_bid, put_short_ask = 4.8, 2.2
    else:
        call_long_bid = [7.0, 6.5, 8.0, 7.5][exit_index]
        call_short_ask = [3.0, 2.8, 3.2, 3.0][exit_index]
        put_long_bid = [3.0, 3.5, 2.5, 3.0][exit_index]
        put_short_ask = [1.0, 1.2, 0.8, 1.0][exit_index]
    return [
        _record(quote_date, OptionType.CALL, 100, call_long_bid, call_long_bid + 0.2),
        _record(quote_date, OptionType.CALL, 110, call_short_ask - 0.2, call_short_ask),
        _record(quote_date, OptionType.PUT, 100, put_long_bid, put_long_bid + 0.2),
        _record(quote_date, OptionType.PUT, 90, put_short_ask - 0.2, put_short_ask),
    ]


class FakePanelClient:
    def __init__(self) -> None:
        self.calls: list[tuple[date, str | None, tuple[float, ...] | None]] = []
        self.records: dict[date, list[MarketDataOptionRecord]] = {}
        for index, (_, _, signal_date, entry_date, exit_date) in enumerate(OBSERVATIONS):
            self.records[signal_date] = _signal_records(signal_date)
            self.records[entry_date] = _execution_records(entry_date)
            self.records[exit_date] = _execution_records(exit_date, exit_index=index)

    def historical_chain(
        self,
        *,
        ticker: str,
        quote_date: date,
        expiration: date,
        side: Literal["call", "put"] | None,
        strikes: list[float] | None,
        strike_limit: int | None,
        min_open_interest: int | None,
        min_volume: int | None,
        risk_free_rate: float,
        continuous_dividend_yield: float,
        dividends: tuple[tuple[date, float], ...],
        time_grid: int,
        price_grid: int,
        force_refresh: bool,
        retrieved_at: datetime,
    ) -> MarketDataChainExport:
        del (
            strike_limit,
            min_open_interest,
            min_volume,
            risk_free_rate,
            continuous_dividend_yield,
            dividends,
            time_grid,
            price_grid,
            force_refresh,
        )
        assert ticker == "TTWO"
        assert expiration == EXPIRATION_DATE
        self.calls.append((quote_date, side, tuple(strikes) if strikes else None))
        records = self.records[quote_date]
        if side is not None:
            records = [record for record in records if record.option_type.value == side]
        if strikes is not None:
            records = [record for record in records if record.strike in strikes]
        return MarketDataChainExport(
            ticker="TTWO",
            requested_date=quote_date,
            retrieved_at=retrieved_at,
            provider_fetched_at=retrieved_at,
            params={"date": quote_date.isoformat()},
            source=EvidenceReference(
                id=f"fixture-{quote_date}",
                title="Fixture MarketData.app chain",
                source_type="test_fixture",
                uri="fixture://marketdata-panel",
                status=EvidenceStatus.READ_ONLY_GATE,
                accessed_at=retrieved_at,
            ),
            usage=MarketDataRateLimit(consumed=1, remaining=99),
            cache_hit=False,
            contracts=records,
        )


def _spec(**overrides: object) -> MarketDataPanelSpec:
    values: dict[str, object] = {
        "ticker": "TTWO",
        "expiration": EXPIRATION_DATE,
        "risk_free_rate": 0.04,
        "observations": [
            MarketDataPanelObservationSpec(
                observation_id=observation_id,
                split=split,
                signal_quote_date=signal_date,
                entry_quote_date=entry_date,
                exit_quote_date=exit_date,
            )
            for observation_id, split, signal_date, entry_date, exit_date in OBSERVATIONS
        ],
        "min_open_interest": 20,
        "max_bid_ask_ratio": 0.5,
        "multiplier": 100,
        "commission_per_contract_per_side": 0,
        "slippage_per_contract_per_side": 0.1,
        "minimum_train_observations": 2,
        "minimum_test_observations": 2,
        "minimum_coverage_ratio": 1,
        "maximum_stability_gap": 1,
    }
    values.update(overrides)
    return MarketDataPanelSpec.model_validate(values)


def test_panel_selects_prior_signals_and_ranks_out_of_sample_returns() -> None:
    client = FakePanelClient()
    report = run_marketdata_panel(
        client,
        _spec(),
        retrieved_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    assert report.provider_requests == 20
    assert report.execution_price_quality == "historical_eod_bid_ask"
    assert report.ranked_strategy_ids[:2] == [
        StrategyKind.LONG_CALL,
        StrategyKind.BULL_CALL_SPREAD,
    ]
    assert report.comparison_order.index(StrategyKind.NO_TRADE) < (
        report.comparison_order.index(StrategyKind.LONG_PUT)
    )
    assert StrategyKind.LONG_PUT not in report.ranked_strategy_ids
    long_call = next(
        result for result in report.strategies if result.strategy is StrategyKind.LONG_CALL
    )
    assert long_call.eligible_for_ranking is True
    assert long_call.test_metrics is not None
    assert long_call.test_metrics.median_return > 0
    assert long_call.latest_selection[0].strike == 100
    assert long_call.backtest is not None
    assert long_call.backtest.execution_price_quality == "historical_eod_bid_ask"
    assert all(case.skipped_reason is None for case in long_call.cases)
    assert long_call.test_metrics.win_rate_ci_low < long_call.test_metrics.win_rate
    assert long_call.test_metrics.win_rate_ci_high == long_call.test_metrics.win_rate
    assert long_call.test_metrics.return_volatility > 0
    completed = next(case for case in long_call.cases if case.net_return is not None)
    assert completed.execution_legs
    assert completed.gross_pnl is not None
    assert completed.costs is not None
    assert completed.slippage_stress_return_2x is not None


def test_panel_keeps_no_trade_when_liquidity_blocks_every_option() -> None:
    report = run_marketdata_panel(
        FakePanelClient(),
        _spec(min_open_interest=1_000),
        retrieved_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    assert report.provider_requests == 4
    assert report.ranked_strategy_ids == [StrategyKind.NO_TRADE]
    option_results = [
        result for result in report.strategies if result.strategy is not StrategyKind.NO_TRADE
    ]
    assert all(result.status == "insufficient_data" for result in option_results)
    assert all(result.coverage_ratio == 0 for result in option_results)


def test_panel_skips_historical_structures_above_eur_budget() -> None:
    report = run_marketdata_panel(
        FakePanelClient(),
        _spec(
            strategies=[StrategyKind.NO_TRADE, StrategyKind.LONG_CALL],
            budget_plan_id="single_long",
            budget_bucket="long",
            budget_eur=1,
            eur_usd_rate=1,
            eur_usd_rate_date=date(2026, 1, 30),
        ),
        retrieved_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    long_call = next(
        result for result in report.strategies if result.strategy is StrategyKind.LONG_CALL
    )
    assert long_call.coverage_ratio == 0
    assert all(
        case.skipped_reason == "selected structure exceeds configured EUR risk budget"
        for case in long_call.cases
    )


def test_panel_rejects_same_day_signal_and_entry() -> None:
    with pytest.raises(ValueError, match="signal < entry < exit"):
        MarketDataPanelObservationSpec(
            observation_id="invalid",
            split="train",
            signal_quote_date=date(2026, 1, 2),
            entry_quote_date=date(2026, 1, 2),
            exit_quote_date=date(2026, 1, 8),
        )


def test_real_panel_fixture_remains_valid() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "marketdata_tt_options_panel_v1.json"

    spec = MarketDataPanelSpec.model_validate_json(fixture_path.read_text(encoding="utf-8"))

    assert len(spec.observations) == 10
    assert spec.minimum_train_observations == 6
    assert spec.minimum_test_observations == 4
    assert StrategyKind.NO_TRADE in spec.strategies


def test_selector_builds_exact_butterfly_condor_and_moneyness_recipes() -> None:
    quote_date = date(2026, 1, 2)
    records = [
        _record(quote_date, OptionType.CALL, 80, 21, 22, delta=0.80),
        _record(quote_date, OptionType.CALL, 90, 12, 13, delta=0.65),
        _record(quote_date, OptionType.CALL, 100, 6, 7, delta=0.50),
        _record(quote_date, OptionType.CALL, 110, 4, 4.5, delta=0.30),
        _record(quote_date, OptionType.CALL, 120, 1, 1.5, delta=0.15),
        _record(quote_date, OptionType.PUT, 80, 1, 1.5, delta=-0.15),
        _record(quote_date, OptionType.PUT, 90, 4, 4.5, delta=-0.30),
        _record(quote_date, OptionType.PUT, 100, 6, 7, delta=-0.50),
        _record(quote_date, OptionType.PUT, 110, 12, 13, delta=-0.65),
        _record(quote_date, OptionType.PUT, 120, 21, 22, delta=-0.80),
    ]
    spec = _spec(
        strategies=[
            StrategyKind.CALL_BUTTERFLY,
            StrategyKind.IRON_CONDOR,
            StrategyKind.LONG_STRADDLE,
            StrategyKind.LEAPS_PUT,
        ],
        selection_mode="moneyness",
        long_moneyness_offset=0.10,
        wing_width_pct=0.10,
    )

    selected = select_marketdata_strategies(records, spec)

    butterfly, butterfly_reason = selected[StrategyKind.CALL_BUTTERFLY]
    assert butterfly_reason is None
    assert [(leg.strike, leg.position_side.value, leg.quantity) for leg in butterfly] == [
        (90, "long", 1),
        (100, "short", 2),
        (110, "long", 1),
    ]
    condor, condor_reason = selected[StrategyKind.IRON_CONDOR]
    assert condor_reason is None
    assert [leg.strike for leg in condor] == [80, 90, 110, 120]
    assert [leg.position_side.value for leg in condor] == [
        "long",
        "short",
        "short",
        "long",
    ]
    straddle, straddle_reason = selected[StrategyKind.LONG_STRADDLE]
    assert straddle_reason is None
    assert {leg.strike for leg in straddle} == {100}
    leaps_put, leaps_reason = selected[StrategyKind.LEAPS_PUT]
    assert leaps_reason is None
    assert leaps_put[0].strike == 110

    unavailable = select_marketdata_strategies(
        records,
        _spec(
            strategies=[StrategyKind.LEAPS_PUT],
            selection_mode="moneyness",
            long_moneyness_offset=0.30,
            maximum_moneyness_target_gap=0.05,
        ),
    )
    unavailable_legs, unavailable_reason = unavailable[StrategyKind.LEAPS_PUT]
    assert unavailable_legs == []
    assert unavailable_reason == "no listed put within 5% of target K+30%"

    debit_credit, risk_capital, maximum_gain, maximum_loss = estimate_selected_risk(condor, spec)
    assert debit_credit is not None and debit_credit < 0
    assert risk_capital is not None and risk_capital > 0
    assert maximum_gain is not None and maximum_gain > 0
    assert maximum_loss == risk_capital


def test_selector_builds_calendar_and_diagonal_across_expirations() -> None:
    quote_date = date(2026, 1, 2)
    back = _signal_records(quote_date)
    front_expiration = date(2026, 1, 30)
    front_timestamp = datetime(2026, 1, 30, 21, 0, tzinfo=UTC)
    front = [
        record.model_copy(
            update={
                "option_symbol": (
                    f"TTWO260130{'C' if record.option_type is OptionType.CALL else 'P'}"
                    f"{round(record.strike * 1000):08d}"
                ),
                "expiration": front_timestamp,
                "dte": (front_expiration - quote_date).days,
            }
        )
        for record in back
    ]
    spec = _spec(
        expiration=None,
        target_dte=49,
        holding_sessions=2,
        front_target_dte=28,
        strategies=[StrategyKind.LONG_CALL_CALENDAR, StrategyKind.CALL_DIAGONAL],
    )

    selected = select_marketdata_strategies([*front, *back], spec)

    calendar, calendar_reason = selected[StrategyKind.LONG_CALL_CALENDAR]
    assert calendar_reason is None
    assert calendar[0].expiration > calendar[1].expiration
    assert calendar[0].strike == calendar[1].strike
    diagonal, diagonal_reason = selected[StrategyKind.CALL_DIAGONAL]
    assert diagonal_reason is None
    assert diagonal[0].expiration > diagonal[1].expiration
    assert diagonal[0].strike < diagonal[1].strike


def test_profit_target_uses_first_complete_eod_threshold_crossing() -> None:
    client = FakePanelClient()
    observations = []
    first_monitors: dict[str, date] = {}
    for observation_id, split, signal_date, entry_date, exit_date in OBSERVATIONS:
        monitor = entry_date + timedelta(days=1)
        while monitor.weekday() >= 5:
            monitor += timedelta(days=1)
        first_monitors[observation_id] = monitor
        client.records[monitor] = [
            _record(monitor, OptionType.CALL, 100, 10.0, 10.2),
        ]
        observations.append(
            MarketDataPanelObservationSpec(
                observation_id=observation_id,
                split=split,
                signal_quote_date=signal_date,
                entry_quote_date=entry_date,
                exit_quote_date=exit_date,
                monitor_quote_dates=[monitor, exit_date],
            )
        )
    report = run_marketdata_panel(
        client,
        _spec(
            observations=observations,
            strategies=[StrategyKind.NO_TRADE, StrategyKind.LONG_CALL],
            profit_target=0.80,
            exit_policy_id="tp80_or_time",
        ),
        retrieved_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    long_call = next(
        result for result in report.strategies if result.strategy is StrategyKind.LONG_CALL
    )
    assert all(case.exit_reason == "profit_target" for case in long_call.cases)
    assert all(
        case.actual_exit_quote_date == first_monitors[case.observation_id]
        for case in long_call.cases
    )
