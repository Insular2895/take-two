"""Walk-forward research panels built from MarketData.app historical EOD bid/ask."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from math import isfinite
from statistics import fmean, median
from typing import Literal, Protocol

from pydantic import Field, model_validator

from take_two_options.backtesting import (
    BacktestCase,
    BacktestDataset,
    BacktestLeg,
    BacktestReport,
    run_backtest,
)
from take_two_options.domain import (
    EvidenceReference,
    EvidenceStatus,
    ModelReadiness,
    OptionType,
    PositionSide,
    StrategyKind,
    StrictModel,
)
from take_two_options.marketdata_data import (
    MARKETDATA_BASE_URL,
    MarketDataChainExport,
    MarketDataDividendInput,
    MarketDataError,
    MarketDataOptionRecord,
    historical_option_quote,
)
from take_two_options.research_statistics import (
    bootstrap_interval,
    conditional_value_at_risk,
    deflated_sharpe_probability,
    downside_deviation,
    payoff_ratio,
    profit_factor,
    sample_volatility,
    value_at_risk,
    wilson_interval,
)

_PANEL_STRATEGIES = {
    StrategyKind.NO_TRADE,
    StrategyKind.LONG_CALL,
    StrategyKind.BULL_CALL_SPREAD,
    StrategyKind.LONG_PUT,
    StrategyKind.BEAR_PUT_SPREAD,
    StrategyKind.LONG_STRADDLE,
    StrategyKind.LONG_STRANGLE,
    StrategyKind.CALL_BUTTERFLY,
    StrategyKind.PUT_BUTTERFLY,
    StrategyKind.IRON_CONDOR,
    StrategyKind.LONG_CALL_CALENDAR,
    StrategyKind.CALL_DIAGONAL,
    StrategyKind.LEAPS_CALL,
    StrategyKind.LEAPS_PUT,
}

_TERM_STRATEGIES = {
    StrategyKind.LONG_CALL_CALENDAR,
    StrategyKind.CALL_DIAGONAL,
}

PanelSplit = Literal["train", "test", "holdout"]


class MarketDataPanelObservationSpec(StrictModel):
    observation_id: str = Field(min_length=1)
    split: PanelSplit
    signal_quote_date: date
    entry_quote_date: date
    exit_quote_date: date
    monitor_quote_dates: list[date] = Field(default_factory=list)
    expiration: date | None = None
    risk_free_rate: float | None = Field(default=None, gt=-0.2, lt=1)
    regime: str = "ordinary"
    signal_momentum_20: float | None = None
    signal_realized_volatility_20: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_timeline(self) -> MarketDataPanelObservationSpec:
        if not self.signal_quote_date < self.entry_quote_date < self.exit_quote_date:
            raise ValueError("panel dates must satisfy signal < entry < exit")
        if len(set(self.monitor_quote_dates)) != len(self.monitor_quote_dates):
            raise ValueError("panel monitor dates must be unique")
        if any(
            item <= self.entry_quote_date or item > self.exit_quote_date
            for item in self.monitor_quote_dates
        ):
            raise ValueError("panel monitor dates must satisfy entry < monitor <= exit")
        return self


class MarketDataPanelSpec(StrictModel):
    ticker: str = Field(min_length=1)
    experiment_id: str = "baseline"
    expiration: date | None = None
    risk_free_rate: float = Field(gt=-0.2, lt=1)
    continuous_dividend_yield: float = Field(default=0.0, ge=0, lt=1)
    dividends: list[MarketDataDividendInput] = Field(default_factory=list)
    strategies: list[StrategyKind] = Field(
        default_factory=lambda: [
            StrategyKind.NO_TRADE,
            StrategyKind.LONG_CALL,
            StrategyKind.BULL_CALL_SPREAD,
            StrategyKind.LONG_PUT,
            StrategyKind.BEAR_PUT_SPREAD,
        ],
        min_length=1,
    )
    observations: list[MarketDataPanelObservationSpec] = Field(min_length=2)
    long_delta_target: float = Field(default=0.55, gt=0, lt=1)
    short_delta_target: float = Field(default=0.30, gt=0, lt=1)
    selection_mode: Literal["delta", "moneyness"] = "delta"
    long_moneyness_offset: float = Field(default=0.0, ge=-0.75, le=2.0)
    maximum_moneyness_target_gap: float = Field(default=0.05, gt=0, le=0.50)
    wing_width_pct: float = Field(default=0.10, gt=0, le=0.50)
    front_target_dte: int = Field(default=45, ge=7, le=365)
    front_expiry_buffer_days: int = Field(default=7, ge=1, le=60)
    strike_limit: int = Field(default=14, ge=4, le=100)
    min_open_interest: int = Field(default=20, ge=0)
    min_volume: int = Field(default=0, ge=0)
    max_bid_ask_ratio: float = Field(default=0.30, gt=0, le=2)
    multiplier: float = Field(gt=0)
    commission_per_contract_per_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_per_side: float = Field(gt=0)
    minimum_train_observations: int = Field(default=6, ge=1)
    minimum_test_observations: int = Field(default=3, ge=1)
    minimum_coverage_ratio: float = Field(default=0.75, gt=0, le=1)
    minimum_test_median_return: float = Field(default=0.0, ge=-1, le=10)
    maximum_test_drawdown: float = Field(default=0.35, gt=0, le=10)
    maximum_test_worst_loss: float = Field(default=0.35, gt=0, le=1)
    maximum_stability_gap: float = Field(default=0.15, ge=0, le=10)
    minimum_holdout_observations: int = Field(default=0, ge=0)
    minimum_embargo_days: int = Field(default=0, ge=0, le=365)
    multiple_testing_trials: int = Field(default=1, ge=1)
    minimum_deflated_sharpe_probability: float = Field(default=0.0, ge=0, le=1)
    bootstrap_samples: int = Field(default=2_000, ge=100, le=100_000)
    target_dte: int | None = Field(default=None, ge=1, le=1_500)
    holding_sessions: int | None = Field(default=None, ge=1, le=252)
    profit_target: float | None = Field(default=None, gt=0, le=10)
    stop_loss: float | None = Field(default=None, gt=0, le=1)
    exit_policy_id: str = "time_exit"
    budget_plan_id: str | None = None
    budget_bucket: str | None = None
    budget_eur: float | None = Field(default=None, gt=0)
    eur_usd_rate: float | None = Field(default=None, gt=0)
    eur_usd_rate_date: date | None = None
    time_grid: int = Field(default=100, ge=25, le=1000)
    price_grid: int = Field(default=100, ge=25, le=1000)
    notes: str = ""

    @model_validator(mode="after")
    def validate_panel(self) -> MarketDataPanelSpec:
        if self.short_delta_target >= self.long_delta_target:
            raise ValueError("short delta target must be below long delta target")
        if len(set(self.strategies)) != len(self.strategies):
            raise ValueError("panel strategies must be unique")
        unsupported = set(self.strategies) - _PANEL_STRATEGIES
        if unsupported:
            raise ValueError(f"unsupported panel strategies: {sorted(unsupported)}")
        if len({item.observation_id for item in self.observations}) != len(self.observations):
            raise ValueError("panel observation IDs must be unique")
        splits = {item.split for item in self.observations}
        if not {"train", "test"}.issubset(splits):
            raise ValueError("panel requires train and test observations")
        for item in self.observations:
            expiration = item.expiration or self.expiration
            if expiration is None and self.target_dte is None:
                raise ValueError("panel requires a default/observation expiration or target_dte")
            if expiration is not None and item.exit_quote_date >= expiration:
                raise ValueError("panel expiration must follow every exit date")
        if set(self.strategies) & _TERM_STRATEGIES and self.expiration is not None:
            raise ValueError("term-spread panels require rolling expirations")
        budget_fields = (
            self.budget_plan_id,
            self.budget_bucket,
            self.budget_eur,
            self.eur_usd_rate,
            self.eur_usd_rate_date,
        )
        if any(value is not None for value in budget_fields) and any(
            value is None for value in budget_fields
        ):
            raise ValueError("budget panels require plan, bucket, EUR budget, FX rate and date")
        self._validate_embargo("train", "test")
        if "holdout" in splits:
            self._validate_embargo("test", "holdout")
        return self

    def _validate_embargo(self, earlier: PanelSplit, later: PanelSplit) -> None:
        if self.minimum_embargo_days == 0:
            return
        earlier_items = [item for item in self.observations if item.split == earlier]
        later_items = [item for item in self.observations if item.split == later]
        if not earlier_items or not later_items:
            return
        latest_exit = max(item.exit_quote_date for item in earlier_items)
        earliest_signal = min(item.signal_quote_date for item in later_items)
        if earliest_signal <= latest_exit + timedelta(days=self.minimum_embargo_days):
            raise ValueError(f"panel {earlier}/{later} boundary violates the configured embargo")


class MarketDataPanelClient(Protocol):
    def historical_chain(
        self,
        *,
        ticker: str,
        quote_date: date,
        expiration: date | Literal["all"],
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
    ) -> MarketDataChainExport: ...


class MarketDataPanelSelectedLeg(StrictModel):
    symbol: str
    option_type: OptionType
    position_side: PositionSide
    quantity: int = Field(default=1, gt=0)
    strike: float = Field(gt=0)
    expiration: date
    signal_dte: int | None = Field(default=None, ge=0)
    signal_timestamp: datetime
    signal_bid: float = Field(gt=0)
    signal_ask: float = Field(gt=0)
    signal_delta: float
    signal_gamma: float | None = None
    signal_theta: float | None = None
    signal_vega: float | None = None
    signal_rho: float | None = None
    signal_implied_volatility: float | None = Field(default=None, gt=0)
    signal_underlying_price: float | None = Field(default=None, gt=0)
    signal_open_interest: float | None = Field(default=None, ge=0)
    signal_volume: float | None = Field(default=None, ge=0)
    bid_ask_ratio: float = Field(ge=0)


class MarketDataPanelExecutionLeg(StrictModel):
    symbol: str
    option_type: OptionType
    position_side: PositionSide
    quantity: int = Field(default=1, gt=0)
    strike: float = Field(gt=0)
    expiration: date
    entry_bid: float = Field(ge=0)
    entry_ask: float = Field(ge=0)
    exit_bid: float = Field(ge=0)
    exit_ask: float = Field(ge=0)
    entry_underlying_price: float | None = Field(default=None, gt=0)
    exit_underlying_price: float | None = Field(default=None, gt=0)
    gross_pnl: float


class MarketDataPanelCaseResult(StrictModel):
    observation_id: str
    split: PanelSplit
    signal_quote_date: date
    entry_quote_date: date
    exit_quote_date: date
    actual_exit_quote_date: date | None = None
    exit_reason: Literal["profit_target", "stop_loss", "time_exit"] | None = None
    regime: str = "ordinary"
    signal_momentum_20: float | None = None
    signal_realized_volatility_20: float | None = Field(default=None, ge=0)
    signal_iv_to_rv: float | None = Field(default=None, ge=0)
    legs: list[MarketDataPanelSelectedLeg] = Field(default_factory=list)
    execution_legs: list[MarketDataPanelExecutionLeg] = Field(default_factory=list)
    skipped_reason: str | None = None
    entry_outlay: float | None = None
    risk_capital: float | None = Field(default=None, gt=0)
    estimated_max_gain: float | None = Field(default=None, ge=0)
    estimated_max_loss: float | None = Field(default=None, gt=0)
    exit_value: float | None = None
    gross_pnl: float | None = None
    costs: float | None = Field(default=None, ge=0)
    net_pnl: float | None = None
    net_return: float | None = None
    return_per_calendar_day: float | None = None
    slippage_stress_return_2x: float | None = None
    spread_stress_return_1_5x: float | None = None
    winner: bool | None = None


class MarketDataPanelReturnMetrics(StrictModel):
    split: PanelSplit
    observations: int = Field(ge=1)
    effective_observations: int = Field(ge=1)
    total_net_pnl: float
    mean_return: float
    median_return: float
    win_rate: float = Field(ge=0, le=1)
    win_rate_ci_low: float = Field(ge=0, le=1)
    win_rate_ci_high: float = Field(ge=0, le=1)
    mean_return_ci_low: float
    mean_return_ci_high: float
    median_return_ci_low: float
    median_return_ci_high: float
    return_volatility: float = Field(ge=0)
    downside_deviation: float = Field(ge=0)
    return_to_volatility: float | None = None
    sortino_ratio: float | None = None
    profit_factor: float | None = Field(default=None, ge=0)
    payoff_ratio: float | None = Field(default=None, ge=0)
    value_at_risk_95: float = Field(ge=0)
    conditional_value_at_risk_95: float = Field(ge=0)
    deflated_sharpe_probability: float | None = Field(default=None, ge=0, le=1)
    maximum_drawdown: float = Field(ge=0)
    worst_return: float


class MarketDataPanelStrategyResult(StrictModel):
    strategy: StrategyKind
    status: Literal["eligible", "insufficient_data"]
    rank: int | None = Field(default=None, ge=1)
    eligible_for_ranking: bool
    eligibility_reasons: list[str] = Field(default_factory=list)
    coverage_ratio: float = Field(ge=0, le=1)
    train_metrics: MarketDataPanelReturnMetrics | None = None
    test_metrics: MarketDataPanelReturnMetrics | None = None
    holdout_metrics: MarketDataPanelReturnMetrics | None = None
    holdout_passed: bool | None = None
    stability_gap: float | None = Field(default=None, ge=0)
    latest_selection: list[MarketDataPanelSelectedLeg] = Field(default_factory=list)
    cases: list[MarketDataPanelCaseResult]
    backtest: BacktestReport | None = None


class MarketDataPanelReport(StrictModel):
    ticker: str
    experiment_id: str = "baseline"
    expiration: date | None = None
    target_dte: int | None = None
    holding_sessions: int | None = None
    created_at: datetime
    source: EvidenceReference
    evidence_class: Literal["source_backed_backtest"] = "source_backed_backtest"
    model_readiness: ModelReadiness = ModelReadiness.SCREEN_GRADE
    execution_price_quality: Literal["historical_eod_bid_ask"] = "historical_eod_bid_ask"
    provider_requests: int = Field(ge=0)
    cache_hits: int = Field(ge=0)
    strategies: list[MarketDataPanelStrategyResult]
    ranked_strategy_ids: list[StrategyKind]
    comparison_order: list[StrategyKind]
    ranking_basis: list[str]
    warnings: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def run_marketdata_panel(
    client: MarketDataPanelClient,
    spec: MarketDataPanelSpec,
    *,
    force_refresh: bool = False,
    retrieved_at: datetime | None = None,
) -> MarketDataPanelReport:
    """Select contracts on prior EOD signals and evaluate later EOD executions."""

    retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
    dividends = tuple((item.ex_date, item.amount) for item in spec.dividends)
    request_count = 0
    cache_hits = 0
    selections: dict[
        tuple[StrategyKind, str], tuple[list[MarketDataPanelSelectedLeg], str | None]
    ] = {}

    signal_side = _signal_side(spec.strategies)
    for observation in sorted(spec.observations, key=lambda item: item.signal_quote_date):
        expiration = _signal_expiration(spec, observation)
        risk_free_rate = (
            observation.risk_free_rate
            if observation.risk_free_rate is not None
            else spec.risk_free_rate
        )
        try:
            export = client.historical_chain(
                ticker=spec.ticker.upper(),
                quote_date=observation.signal_quote_date,
                expiration=expiration,
                side=signal_side,
                strikes=None,
                strike_limit=spec.strike_limit,
                min_open_interest=spec.min_open_interest or None,
                min_volume=spec.min_volume or None,
                risk_free_rate=risk_free_rate,
                continuous_dividend_yield=spec.continuous_dividend_yield,
                dividends=dividends,
                time_grid=spec.time_grid,
                price_grid=spec.price_grid,
                force_refresh=force_refresh,
                retrieved_at=retrieved,
            )
        except MarketDataError as error:
            request_count += 1
            for strategy in spec.strategies:
                if strategy is StrategyKind.NO_TRADE:
                    continue
                selections[(strategy, observation.observation_id)] = (
                    [],
                    f"signal chain unavailable: {error}",
                )
            continue
        request_count += 1
        cache_hits += int(export.cache_hit)
        signal_records = (
            export.contracts
            if set(spec.strategies) & _TERM_STRATEGIES
            else _target_expiration_records(export.contracts, observation, spec)
        )
        observation_selections = select_marketdata_strategies(signal_records, spec)
        for strategy in spec.strategies:
            if strategy is StrategyKind.NO_TRADE:
                continue
            selections[(strategy, observation.observation_id)] = observation_selections.get(
                strategy, ([], "strategy selection unavailable")
            )

    requirements: dict[tuple[date, date, OptionType], set[float]] = {}
    for observation in spec.observations:
        for strategy in spec.strategies:
            selected, reason = selections.get(
                (strategy, observation.observation_id), ([], "strategy selection unavailable")
            )
            if reason is not None:
                continue
            for leg in selected:
                monitor_dates = observation.monitor_quote_dates or [observation.exit_quote_date]
                for quote_date in [observation.entry_quote_date, *monitor_dates]:
                    requirements.setdefault(
                        (quote_date, leg.expiration, leg.option_type), set()
                    ).add(leg.strike)

    records: dict[tuple[date, str], MarketDataOptionRecord] = {}
    for (quote_date, expiration, option_type), strikes in sorted(
        requirements.items(), key=lambda item: (item[0][0], item[0][1], item[0][2].value)
    ):
        try:
            export = client.historical_chain(
                ticker=spec.ticker.upper(),
                quote_date=quote_date,
                expiration=expiration,
                side=option_type.value,
                strikes=sorted(strikes),
                strike_limit=None,
                min_open_interest=None,
                min_volume=None,
                risk_free_rate=spec.risk_free_rate,
                continuous_dividend_yield=spec.continuous_dividend_yield,
                dividends=dividends,
                time_grid=spec.time_grid,
                price_grid=spec.price_grid,
                force_refresh=force_refresh,
                retrieved_at=retrieved,
            )
        except MarketDataError:
            request_count += 1
            continue
        request_count += 1
        cache_hits += int(export.cache_hit)
        for record in export.contracts:
            records[(quote_date, record.option_symbol)] = record

    source = _panel_source(spec, retrieved, request_count, cache_hits)
    strategy_results = [
        _no_trade_result(spec)
        if strategy is StrategyKind.NO_TRADE
        else _option_strategy_result(
            strategy=strategy,
            spec=spec,
            selections=selections,
            records=records,
            source=source,
            retrieved=retrieved,
        )
        for strategy in spec.strategies
    ]
    ranked = sorted(
        (result for result in strategy_results if result.eligible_for_ranking),
        key=_ranking_key,
    )
    comparison = sorted(
        (
            result
            for result in strategy_results
            if result.train_metrics is not None and result.test_metrics is not None
        ),
        key=_ranking_key,
    )
    for rank, result in enumerate(ranked, start=1):
        result.rank = rank

    return MarketDataPanelReport(
        ticker=spec.ticker.upper(),
        experiment_id=spec.experiment_id,
        expiration=spec.expiration,
        target_dte=spec.target_dte,
        holding_sessions=spec.holding_sessions,
        created_at=retrieved,
        source=source,
        provider_requests=request_count,
        cache_hits=cache_hits,
        strategies=strategy_results,
        ranked_strategy_ids=[result.strategy for result in ranked],
        comparison_order=[result.strategy for result in comparison],
        ranking_basis=[
            (
                "Eligibility requires configured evidence, return, drawdown, "
                "worst-loss, and stability gates"
            ),
            "Higher out-of-sample median net return",
            "Lower out-of-sample normalized maximum drawdown",
            "Smaller train/test mean-return stability gap",
        ],
        warnings=[
            "Research ranking only; it does not authorize execution or position sizing",
            "Signals use an earlier EOD chain than the entry quote to limit look-ahead",
            "EOD bid/ask does not replay intraday NBBO, combo fills, or market impact",
            "Delta selection depends on supplied rate and dividend assumptions",
            (
                "Profit targets and stops use the first complete EOD executable-side mark; "
                "intraday crossings are not observed"
            ),
            "No-trade is retained as a zero-return baseline",
        ],
    )


def render_marketdata_panel_markdown(report: MarketDataPanelReport) -> str:
    lines = [
        "# TTWO MarketData.app walk-forward panel",
        "",
        f"- Created: `{report.created_at.isoformat()}`",
        f"- Experiment: `{report.experiment_id}`",
        f"- Expiration: `{report.expiration.isoformat() if report.expiration else 'rolling'}`",
        f"- Price quality: `{report.execution_price_quality}`",
        f"- Model readiness: `{report.model_readiness.value}`",
        f"- Provider requests: `{report.provider_requests}` ({report.cache_hits} cache hits)",
        "- Order capability: `forbidden`",
        "",
        "## Ranking",
        "",
    ]
    if not report.ranked_strategy_ids:
        lines.append("No strategy met the configured minimum evidence thresholds.")
    for result in sorted(report.strategies, key=lambda item: item.rank or 10_000):
        if result.rank is None:
            continue
        assert result.test_metrics is not None
        lines.append(
            f"{result.rank}. `{result.strategy.value}`: test median "
            f"{result.test_metrics.median_return:.2%}, win rate "
            f"{result.test_metrics.win_rate:.1%} "
            f"[{result.test_metrics.win_rate_ci_low:.1%}, "
            f"{result.test_metrics.win_rate_ci_high:.1%}], max drawdown "
            f"{result.test_metrics.maximum_drawdown:.2%}"
        )
    lines.extend(["", "## Coverage", ""])
    for result in report.strategies:
        reason = "; ".join(result.eligibility_reasons) or "eligible"
        lines.append(f"- `{result.strategy.value}`: coverage {result.coverage_ratio:.1%}, {reason}")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    lines.append("")
    return "\n".join(lines)


def _signal_side(strategies: Sequence[StrategyKind]) -> Literal["call", "put"] | None:
    needs_calls = any(
        strategy
        in {
            StrategyKind.LONG_CALL,
            StrategyKind.BULL_CALL_SPREAD,
            StrategyKind.LONG_STRADDLE,
            StrategyKind.LONG_STRANGLE,
            StrategyKind.CALL_BUTTERFLY,
            StrategyKind.IRON_CONDOR,
            StrategyKind.LONG_CALL_CALENDAR,
            StrategyKind.CALL_DIAGONAL,
            StrategyKind.LEAPS_CALL,
        }
        for strategy in strategies
    )
    needs_puts = any(
        strategy
        in {
            StrategyKind.LONG_PUT,
            StrategyKind.BEAR_PUT_SPREAD,
            StrategyKind.LONG_STRADDLE,
            StrategyKind.LONG_STRANGLE,
            StrategyKind.PUT_BUTTERFLY,
            StrategyKind.IRON_CONDOR,
            StrategyKind.LEAPS_PUT,
        }
        for strategy in strategies
    )
    if needs_calls and not needs_puts:
        return "call"
    if needs_puts and not needs_calls:
        return "put"
    return None


def select_marketdata_strategies(
    records: Sequence[MarketDataOptionRecord], spec: MarketDataPanelSpec
) -> dict[StrategyKind, tuple[list[MarketDataPanelSelectedLeg], str | None]]:
    back_records = _records_nearest_dte(records, spec.target_dte)
    calls = _eligible_records(back_records, OptionType.CALL, spec)
    puts = _eligible_records(back_records, OptionType.PUT, spec)
    selected: dict[StrategyKind, tuple[list[MarketDataPanelSelectedLeg], str | None]] = {}

    long_call = _long_anchor(calls, spec, OptionType.CALL)
    if long_call is None:
        reason = _anchor_unavailable_reason(spec, "call")
        selected[StrategyKind.LONG_CALL] = ([], reason)
        selected[StrategyKind.BULL_CALL_SPREAD] = ([], reason)
        selected[StrategyKind.LEAPS_CALL] = ([], reason)
    else:
        selected[StrategyKind.LONG_CALL] = (
            [_selected_leg(long_call, PositionSide.LONG)],
            None,
        )
        selected[StrategyKind.LEAPS_CALL] = (
            [_selected_leg(long_call, PositionSide.LONG)],
            None,
        )
        short_call = _closest_delta(
            [record for record in calls if record.strike > long_call.strike],
            spec.short_delta_target,
        )
        selected[StrategyKind.BULL_CALL_SPREAD] = (
            [
                _selected_leg(long_call, PositionSide.LONG),
                _selected_leg(short_call, PositionSide.SHORT),
            ]
            if short_call is not None
            else [],
            None if short_call is not None else "no eligible higher-strike short call",
        )

    long_put = _long_anchor(puts, spec, OptionType.PUT)
    if long_put is None:
        reason = _anchor_unavailable_reason(spec, "put")
        selected[StrategyKind.LONG_PUT] = ([], reason)
        selected[StrategyKind.BEAR_PUT_SPREAD] = ([], reason)
        selected[StrategyKind.LEAPS_PUT] = ([], reason)
    else:
        selected[StrategyKind.LONG_PUT] = (
            [_selected_leg(long_put, PositionSide.LONG)],
            None,
        )
        selected[StrategyKind.LEAPS_PUT] = (
            [_selected_leg(long_put, PositionSide.LONG)],
            None,
        )
        short_put = _closest_delta(
            [record for record in puts if record.strike < long_put.strike],
            -spec.short_delta_target,
        )
        selected[StrategyKind.BEAR_PUT_SPREAD] = (
            [
                _selected_leg(long_put, PositionSide.LONG),
                _selected_leg(short_put, PositionSide.SHORT),
            ]
            if short_put is not None
            else [],
            None if short_put is not None else "no eligible lower-strike short put",
        )

    straddle = _straddle_legs(calls, puts)
    selected[StrategyKind.LONG_STRADDLE] = (
        straddle,
        None if straddle else "no eligible common ATM strike for straddle",
    )
    strangle = _strangle_legs(calls, puts, spec)
    selected[StrategyKind.LONG_STRANGLE] = (
        strangle,
        None if strangle else "no eligible OTM call/put anchors for strangle",
    )
    call_butterfly = _butterfly_legs(calls, spec)
    selected[StrategyKind.CALL_BUTTERFLY] = (
        call_butterfly,
        None if call_butterfly else "no eligible three-strike call butterfly",
    )
    put_butterfly = _butterfly_legs(puts, spec)
    selected[StrategyKind.PUT_BUTTERFLY] = (
        put_butterfly,
        None if put_butterfly else "no eligible three-strike put butterfly",
    )
    iron_condor = _iron_condor_legs(calls, puts, spec)
    selected[StrategyKind.IRON_CONDOR] = (
        iron_condor,
        None if iron_condor else "no eligible four-strike iron condor",
    )
    calendar, diagonal = _term_spread_legs(records, spec)
    selected[StrategyKind.LONG_CALL_CALENDAR] = (
        calendar,
        None if calendar else "no eligible front/back common-strike call calendar",
    )
    selected[StrategyKind.CALL_DIAGONAL] = (
        diagonal,
        None if diagonal else "no eligible front/back call diagonal",
    )
    return selected


def _records_nearest_dte(
    records: Sequence[MarketDataOptionRecord], target_dte: int | None
) -> list[MarketDataOptionRecord]:
    if not records or target_dte is None:
        return list(records)
    expirations = {record.expiration.date(): record.dte for record in records}
    target = min(
        expirations,
        key=lambda expiration: abs((expirations[expiration] or 0) - target_dte),
    )
    return [record for record in records if record.expiration.date() == target]


def _long_anchor(
    records: Sequence[MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
    option_type: OptionType,
) -> MarketDataOptionRecord | None:
    if spec.selection_mode == "delta":
        target = (
            spec.long_delta_target if option_type is OptionType.CALL else -spec.long_delta_target
        )
        return _closest_delta(records, target)
    spot = _underlying_spot(records)
    if spot is None:
        return None
    selected = _closest_strike(records, spot * (1 + spec.long_moneyness_offset))
    if selected is None:
        return None
    realized_offset = selected.strike / spot - 1
    if abs(realized_offset - spec.long_moneyness_offset) > spec.maximum_moneyness_target_gap:
        return None
    return selected


def _anchor_unavailable_reason(spec: MarketDataPanelSpec, option_label: str) -> str:
    if spec.selection_mode == "moneyness":
        return (
            f"no listed {option_label} within "
            f"{spec.maximum_moneyness_target_gap:.0%} of target "
            f"K{spec.long_moneyness_offset:+.0%}"
        )
    return f"no eligible long-{option_label} anchor"


def _straddle_legs(
    calls: Sequence[MarketDataOptionRecord], puts: Sequence[MarketDataOptionRecord]
) -> list[MarketDataPanelSelectedLeg]:
    spot = _underlying_spot([*calls, *puts])
    if spot is None:
        return []
    call_by_strike = {record.strike: record for record in calls}
    put_by_strike = {record.strike: record for record in puts}
    common = sorted(set(call_by_strike) & set(put_by_strike))
    if not common:
        return []
    strike = min(common, key=lambda value: abs(value - spot))
    return [
        _selected_leg(call_by_strike[strike], PositionSide.LONG),
        _selected_leg(put_by_strike[strike], PositionSide.LONG),
    ]


def _strangle_legs(
    calls: Sequence[MarketDataOptionRecord],
    puts: Sequence[MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
) -> list[MarketDataPanelSelectedLeg]:
    call = _closest_delta(calls, spec.short_delta_target)
    put = _closest_delta(puts, -spec.short_delta_target)
    spot = _underlying_spot([*calls, *puts])
    if call is None or put is None or spot is None:
        return []
    if not put.strike < spot < call.strike:
        return []
    return [
        _selected_leg(call, PositionSide.LONG),
        _selected_leg(put, PositionSide.LONG),
    ]


def _butterfly_legs(
    records: Sequence[MarketDataOptionRecord], spec: MarketDataPanelSpec
) -> list[MarketDataPanelSelectedLeg]:
    spot = _underlying_spot(records)
    if spot is None:
        return []
    center = _closest_strike(records, spot)
    if center is None:
        return []
    lower = _closest_strike(
        [record for record in records if record.strike < center.strike],
        center.strike * (1 - spec.wing_width_pct),
    )
    upper = _closest_strike(
        [record for record in records if record.strike > center.strike],
        center.strike * (1 + spec.wing_width_pct),
    )
    if lower is None or upper is None:
        return []
    return [
        _selected_leg(lower, PositionSide.LONG),
        _selected_leg(center, PositionSide.SHORT, quantity=2),
        _selected_leg(upper, PositionSide.LONG),
    ]


def _iron_condor_legs(
    calls: Sequence[MarketDataOptionRecord],
    puts: Sequence[MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
) -> list[MarketDataPanelSelectedLeg]:
    short_call = _closest_delta(calls, spec.short_delta_target)
    short_put = _closest_delta(puts, -spec.short_delta_target)
    if short_call is None or short_put is None or short_put.strike >= short_call.strike:
        return []
    long_call = _closest_strike(
        [record for record in calls if record.strike > short_call.strike],
        short_call.strike * (1 + spec.wing_width_pct),
    )
    long_put = _closest_strike(
        [record for record in puts if record.strike < short_put.strike],
        short_put.strike * (1 - spec.wing_width_pct),
    )
    if long_call is None or long_put is None:
        return []
    return [
        _selected_leg(long_put, PositionSide.LONG),
        _selected_leg(short_put, PositionSide.SHORT),
        _selected_leg(short_call, PositionSide.SHORT),
        _selected_leg(long_call, PositionSide.LONG),
    ]


def _term_spread_legs(
    records: Sequence[MarketDataOptionRecord], spec: MarketDataPanelSpec
) -> tuple[list[MarketDataPanelSelectedLeg], list[MarketDataPanelSelectedLeg]]:
    back_records = _records_nearest_dte(records, spec.target_dte)
    back_calls = _eligible_records(back_records, OptionType.CALL, spec)
    if not back_calls:
        return [], []
    back_expiration = back_calls[0].expiration.date()
    holding_calendar_days = ((spec.holding_sessions or 1) * 7 + 4) // 5
    minimum_front_dte = holding_calendar_days + spec.front_expiry_buffer_days
    front_pool = [
        record
        for record in records
        if record.expiration.date() < back_expiration and (record.dte or 0) > minimum_front_dte
    ]
    front_records = _records_nearest_dte(front_pool, spec.front_target_dte)
    front_calls = _eligible_records(front_records, OptionType.CALL, spec)
    if not front_calls:
        return [], []
    spot = _underlying_spot([*front_calls, *back_calls])
    if spot is None:
        return [], []
    front_by_strike = {record.strike: record for record in front_calls}
    back_by_strike = {record.strike: record for record in back_calls}
    common = sorted(set(front_by_strike) & set(back_by_strike))
    calendar: list[MarketDataPanelSelectedLeg] = []
    if common:
        strike = min(common, key=lambda value: abs(value - spot))
        calendar = [
            _selected_leg(back_by_strike[strike], PositionSide.LONG),
            _selected_leg(front_by_strike[strike], PositionSide.SHORT),
        ]
    back_anchor = _long_anchor(back_calls, spec, OptionType.CALL)
    diagonal: list[MarketDataPanelSelectedLeg] = []
    if back_anchor is not None:
        front_short = _closest_delta(
            [record for record in front_calls if record.strike > back_anchor.strike],
            spec.short_delta_target,
        )
        if front_short is not None:
            diagonal = [
                _selected_leg(back_anchor, PositionSide.LONG),
                _selected_leg(front_short, PositionSide.SHORT),
            ]
    return calendar, diagonal


def _underlying_spot(records: Sequence[MarketDataOptionRecord]) -> float | None:
    return next(
        (record.underlying_price for record in records if record.underlying_price is not None),
        None,
    )


def _closest_strike(
    records: Sequence[MarketDataOptionRecord], target: float
) -> MarketDataOptionRecord | None:
    if not records:
        return None
    return min(
        records,
        key=lambda record: (
            abs(record.strike - target),
            _bid_ask_ratio(record),
            -(record.open_interest or 0),
        ),
    )


def _eligible_records(
    records: Sequence[MarketDataOptionRecord],
    option_type: OptionType,
    spec: MarketDataPanelSpec,
) -> list[MarketDataOptionRecord]:
    eligible: list[MarketDataOptionRecord] = []
    for record in records:
        if record.option_type is not option_type or record.computed_analytics is None:
            continue
        if record.bid is None or record.ask is None or record.bid <= 0 or record.ask <= 0:
            continue
        if (record.open_interest or 0) < spec.min_open_interest:
            continue
        if (record.volume or 0) < spec.min_volume:
            continue
        if _bid_ask_ratio(record) > spec.max_bid_ask_ratio:
            continue
        eligible.append(record)
    return eligible


def _closest_delta(
    records: Sequence[MarketDataOptionRecord], target: float
) -> MarketDataOptionRecord | None:
    if not records:
        return None
    return min(
        records,
        key=lambda record: (
            abs(_delta(record) - target),
            _bid_ask_ratio(record),
            -(record.open_interest or 0),
            record.strike,
        ),
    )


def _selected_leg(
    record: MarketDataOptionRecord,
    position_side: PositionSide,
    *,
    quantity: int = 1,
) -> MarketDataPanelSelectedLeg:
    assert record.bid is not None
    assert record.ask is not None
    analytics = record.computed_analytics
    assert analytics is not None
    return MarketDataPanelSelectedLeg(
        symbol=record.option_symbol,
        option_type=record.option_type,
        position_side=position_side,
        quantity=quantity,
        strike=record.strike,
        expiration=record.expiration.date(),
        signal_dte=record.dte,
        signal_timestamp=record.quote_timestamp,
        signal_bid=record.bid,
        signal_ask=record.ask,
        signal_delta=analytics.delta,
        signal_gamma=analytics.gamma,
        signal_theta=analytics.theta,
        signal_vega=analytics.vega,
        signal_rho=analytics.rho,
        signal_implied_volatility=analytics.implied_volatility,
        signal_underlying_price=record.underlying_price,
        signal_open_interest=record.open_interest,
        signal_volume=record.volume,
        bid_ask_ratio=_bid_ask_ratio(record),
    )


def _execution_leg(
    selected: MarketDataPanelSelectedLeg,
    entry: MarketDataOptionRecord,
    exit: MarketDataOptionRecord,
    multiplier: float,
) -> MarketDataPanelExecutionLeg:
    assert entry.bid is not None and entry.ask is not None
    assert exit.bid is not None and exit.ask is not None
    entry_price = entry.ask if selected.position_side is PositionSide.LONG else entry.bid
    exit_price = exit.bid if selected.position_side is PositionSide.LONG else exit.ask
    gross_pnl = (
        selected.position_side.sign * selected.quantity * multiplier * (exit_price - entry_price)
    )
    return MarketDataPanelExecutionLeg(
        symbol=selected.symbol,
        option_type=selected.option_type,
        position_side=selected.position_side,
        quantity=selected.quantity,
        strike=selected.strike,
        expiration=selected.expiration,
        entry_bid=entry.bid,
        entry_ask=entry.ask,
        exit_bid=exit.bid,
        exit_ask=exit.ask,
        entry_underlying_price=entry.underlying_price,
        exit_underlying_price=exit.underlying_price,
        gross_pnl=round(gross_pnl, 6),
    )


def _delta(record: MarketDataOptionRecord) -> float:
    assert record.computed_analytics is not None
    return record.computed_analytics.delta


def _bid_ask_ratio(record: MarketDataOptionRecord) -> float:
    assert record.bid is not None
    assert record.ask is not None
    midpoint = (record.bid + record.ask) / 2
    return (record.ask - record.bid) / midpoint if midpoint > 0 else float("inf")


def _entry_outlay(
    legs: Sequence[MarketDataPanelSelectedLeg],
    records: Sequence[MarketDataOptionRecord],
    multiplier: float,
) -> float:
    return sum(
        leg.position_side.sign
        * leg.quantity
        * multiplier
        * (record.ask if leg.position_side is PositionSide.LONG else record.bid)
        for leg, record in zip(legs, records, strict=True)
        if record.ask is not None and record.bid is not None
    )


def _exit_value(
    legs: Sequence[MarketDataPanelSelectedLeg],
    records: Sequence[MarketDataOptionRecord],
    multiplier: float,
) -> float:
    return sum(
        leg.position_side.sign
        * leg.quantity
        * multiplier
        * (record.bid if leg.position_side is PositionSide.LONG else record.ask)
        for leg, record in zip(legs, records, strict=True)
        if record.ask is not None and record.bid is not None
    )


def _roundtrip_costs(
    legs: Sequence[MarketDataPanelSelectedLeg], spec: MarketDataPanelSpec
) -> float:
    contract_sides = sum(leg.quantity for leg in legs) * 2
    return contract_sides * (
        spec.commission_per_contract_per_side + spec.slippage_per_contract_per_side
    )


def _net_pnl_at_exit(
    legs: Sequence[MarketDataPanelSelectedLeg],
    entry_records: Sequence[MarketDataOptionRecord],
    exit_records: Sequence[MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
) -> float:
    return (
        _exit_value(legs, exit_records, spec.multiplier)
        - _entry_outlay(legs, entry_records, spec.multiplier)
        - _roundtrip_costs(legs, spec)
    )


def _risk_profile(
    legs: Sequence[MarketDataPanelSelectedLeg],
    entry_records: Sequence[MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
) -> tuple[float | None, float | None, float]:
    entry_outlay = _entry_outlay(legs, entry_records, spec.multiplier)
    costs = _roundtrip_costs(legs, spec)
    expirations = {leg.expiration for leg in legs}
    if entry_outlay > 0:
        maximum_loss = entry_outlay + costs
        if len(expirations) > 1:
            return maximum_loss, None, maximum_loss
    elif len(expirations) > 1:
        return None, None, 0.0

    strikes = sorted({leg.strike for leg in legs})
    if not strikes:
        return None, None, 0.0
    high_spot = strikes[-1] * 4
    spots = [0.0, *strikes, high_spot]
    terminal_pnls = [
        _terminal_exit_value(legs, spot, spec.multiplier) - entry_outlay - costs for spot in spots
    ]
    high_call_slope = sum(
        leg.position_side.sign * leg.quantity for leg in legs if leg.option_type is OptionType.CALL
    )
    if high_call_slope < 0:
        return None, None, 0.0
    terminal_max_loss = max(0.0, -min(terminal_pnls))
    maximum_loss = entry_outlay + costs if entry_outlay > 0 else terminal_max_loss
    if maximum_loss <= 0:
        return None, None, 0.0
    maximum_gain = None if high_call_slope > 0 else max(0.0, max(terminal_pnls))
    return maximum_loss, maximum_gain, maximum_loss


def estimate_selected_risk(
    legs: Sequence[MarketDataPanelSelectedLeg], spec: MarketDataPanelSpec
) -> tuple[float | None, float | None, float | None, float | None]:
    """Return net debit/credit, risk capital, maximum gain, and maximum loss."""

    if not legs:
        return None, None, None, None
    entry_outlay = sum(
        leg.position_side.sign
        * leg.quantity
        * spec.multiplier
        * (leg.signal_ask if leg.position_side is PositionSide.LONG else leg.signal_bid)
        for leg in legs
    )
    costs = _roundtrip_costs(legs, spec)
    expirations = {leg.expiration for leg in legs}
    if entry_outlay > 0 and len(expirations) > 1:
        risk = entry_outlay + costs
        return entry_outlay, risk, None, risk
    if entry_outlay <= 0 and len(expirations) > 1:
        return entry_outlay, None, None, None
    strikes = sorted({leg.strike for leg in legs})
    terminal_pnls = [
        _terminal_exit_value(legs, spot, spec.multiplier) - entry_outlay - costs
        for spot in [0.0, *strikes, strikes[-1] * 4]
    ]
    high_call_slope = sum(
        leg.position_side.sign * leg.quantity for leg in legs if leg.option_type is OptionType.CALL
    )
    if high_call_slope < 0:
        return entry_outlay, None, None, None
    risk = entry_outlay + costs if entry_outlay > 0 else max(0.0, -min(terminal_pnls))
    if risk <= 0:
        return entry_outlay, None, None, None
    maximum_gain = None if high_call_slope > 0 else max(0.0, max(terminal_pnls))
    return entry_outlay, risk, maximum_gain, risk


def _terminal_exit_value(
    legs: Sequence[MarketDataPanelSelectedLeg], spot: float, multiplier: float
) -> float:
    value = 0.0
    for leg in legs:
        intrinsic = (
            max(spot - leg.strike, 0.0)
            if leg.option_type is OptionType.CALL
            else max(leg.strike - spot, 0.0)
        )
        value += leg.position_side.sign * leg.quantity * multiplier * intrinsic
    return value


def _select_exit(
    observation: MarketDataPanelObservationSpec,
    legs: Sequence[MarketDataPanelSelectedLeg],
    entry_records: Sequence[MarketDataOptionRecord],
    records: dict[tuple[date, str], MarketDataOptionRecord],
    spec: MarketDataPanelSpec,
    risk_capital: float,
) -> (
    tuple[
        date,
        list[MarketDataOptionRecord],
        Literal["profit_target", "stop_loss", "time_exit"],
    ]
    | None
):
    exit_dates = sorted(
        {
            *observation.monitor_quote_dates,
            observation.exit_quote_date,
        }
    )
    for exit_date in exit_dates:
        exit_records = [records.get((exit_date, leg.symbol)) for leg in legs]
        if any(record is None for record in exit_records):
            continue
        concrete = [record for record in exit_records if record is not None]
        if any(
            record.bid is None or record.ask is None or record.bid <= 0 or record.ask <= 0
            for record in concrete
        ):
            continue
        net_return = _net_pnl_at_exit(legs, entry_records, concrete, spec) / risk_capital
        if spec.profit_target is not None and net_return >= spec.profit_target:
            return exit_date, concrete, "profit_target"
        if spec.stop_loss is not None and net_return <= -spec.stop_loss:
            return exit_date, concrete, "stop_loss"
        if exit_date == observation.exit_quote_date:
            return exit_date, concrete, "time_exit"
    return None


def _option_strategy_result(
    *,
    strategy: StrategyKind,
    spec: MarketDataPanelSpec,
    selections: dict[tuple[StrategyKind, str], tuple[list[MarketDataPanelSelectedLeg], str | None]],
    records: dict[tuple[date, str], MarketDataOptionRecord],
    source: EvidenceReference,
    retrieved: datetime,
) -> MarketDataPanelStrategyResult:
    cases: list[BacktestCase] = []
    audit_by_id: dict[str, MarketDataPanelCaseResult] = {}
    for observation in sorted(spec.observations, key=lambda item: item.signal_quote_date):
        selected, reason = selections.get(
            (strategy, observation.observation_id), ([], "strategy selection unavailable")
        )
        audit = MarketDataPanelCaseResult(
            observation_id=observation.observation_id,
            split=observation.split,
            signal_quote_date=observation.signal_quote_date,
            entry_quote_date=observation.entry_quote_date,
            exit_quote_date=observation.exit_quote_date,
            regime=observation.regime,
            signal_momentum_20=observation.signal_momentum_20,
            signal_realized_volatility_20=observation.signal_realized_volatility_20,
            legs=selected,
            skipped_reason=reason,
        )
        audit_by_id[observation.observation_id] = audit
        if reason is not None:
            continue
        if any(leg.expiration <= observation.exit_quote_date for leg in selected):
            audit.skipped_reason = "selected contract expires on or before planned exit"
            continue
        entry_records = [
            records.get((observation.entry_quote_date, leg.symbol)) for leg in selected
        ]
        if any(record is None for record in entry_records):
            audit.skipped_reason = "selected contract missing at entry"
            continue
        concrete_entry = [record for record in entry_records if record is not None]
        if any(
            record.bid is None or record.ask is None or record.bid <= 0 or record.ask <= 0
            for record in concrete_entry
        ):
            audit.skipped_reason = "positive bid/ask missing at entry"
            continue
        risk_capital, max_gain, max_loss = _risk_profile(
            selected,
            concrete_entry,
            spec,
        )
        if risk_capital is None:
            audit.skipped_reason = "selected structure does not prove bounded maximum risk"
            continue
        if (
            spec.budget_eur is not None
            and spec.eur_usd_rate is not None
            and risk_capital > spec.budget_eur * spec.eur_usd_rate
        ):
            audit.skipped_reason = "selected structure exceeds configured EUR risk budget"
            continue
        selected_exit = _select_exit(
            observation,
            selected,
            concrete_entry,
            records,
            spec,
            risk_capital,
        )
        if selected_exit is None:
            audit.skipped_reason = "selected contract missing a complete executable exit"
            continue
        actual_exit_date, concrete_exit, exit_reason = selected_exit
        audit.actual_exit_quote_date = actual_exit_date
        audit.exit_reason = exit_reason
        signal_ivs = [
            leg.signal_implied_volatility
            for leg in selected
            if leg.signal_implied_volatility is not None
        ]
        if signal_ivs and observation.signal_realized_volatility_20:
            audit.signal_iv_to_rv = round(
                (sum(signal_ivs) / len(signal_ivs)) / observation.signal_realized_volatility_20,
                8,
            )
        audit.risk_capital = round(risk_capital, 6)
        audit.estimated_max_gain = round(max_gain, 6) if max_gain is not None else None
        audit.estimated_max_loss = round(max_loss, 6)
        audit.execution_legs = [
            _execution_leg(leg, entry_record, exit_record, spec.multiplier)
            for leg, entry_record, exit_record in zip(
                selected, concrete_entry, concrete_exit, strict=True
            )
        ]
        backtest_legs = [
            BacktestLeg(
                side=leg.position_side,
                quantity=leg.quantity,
                multiplier=spec.multiplier,
                entry_quote=historical_option_quote(entry_record),
                exit_quote=historical_option_quote(exit_record),
            )
            for leg, entry_record, exit_record in zip(
                selected, concrete_entry, concrete_exit, strict=True
            )
        ]
        signal_available_at = max(leg.signal_timestamp for leg in selected) + timedelta(seconds=1)
        entry_timestamp = max(leg.entry_quote.data_available_at for leg in backtest_legs)
        exit_timestamp = max(leg.exit_quote.data_available_at for leg in backtest_legs)
        if signal_available_at >= entry_timestamp:
            audit.skipped_reason = "look-ahead: signal was not available before entry"
            continue
        cases.append(
            BacktestCase(
                case_id=f"{strategy.value}:{observation.observation_id}",
                split=observation.split,
                entry_timestamp=entry_timestamp,
                exit_timestamp=exit_timestamp,
                model_calibrated_through=signal_available_at,
                legs=backtest_legs,
                commission_per_contract_per_side=spec.commission_per_contract_per_side,
                slippage_per_contract_per_side=spec.slippage_per_contract_per_side,
            )
        )

    backtest: BacktestReport | None = None
    returns_by_split: dict[PanelSplit, list[float]] = {
        "train": [],
        "test": [],
        "holdout": [],
    }
    if {"train", "test"}.issubset({case.split for case in cases}):
        backtest = run_backtest(
            BacktestDataset(
                ticker=spec.ticker.upper(),
                as_of=retrieved,
                evidence_class="source_backed_backtest",
                source=source,
                cases=cases,
            )
        )
        case_by_id = {case.case_id: case for case in backtest.cases}
        for observation in spec.observations:
            case_id = f"{strategy.value}:{observation.observation_id}"
            result = case_by_id.get(case_id)
            if result is None:
                continue
            audit = audit_by_id[observation.observation_id]
            audit.entry_outlay = result.entry_outlay
            audit.exit_value = result.exit_value
            audit.gross_pnl = result.gross_pnl
            audit.costs = result.costs
            audit.net_pnl = result.net_pnl
            assert audit.risk_capital is not None
            audit.net_return = round(result.net_pnl / audit.risk_capital, 8)
            actual_exit_date = audit.actual_exit_quote_date or observation.exit_quote_date
            calendar_days = (actual_exit_date - observation.entry_quote_date).days
            audit.return_per_calendar_day = round(audit.net_return / calendar_days, 8)
            contract_sides = sum(leg.quantity for leg in audit.execution_legs) * 2
            extra_slippage = contract_sides * spec.slippage_per_contract_per_side
            audit.slippage_stress_return_2x = round(
                (result.net_pnl - extra_slippage) / audit.risk_capital, 8
            )
            extra_spread_cost = sum(
                0.25
                * ((leg.entry_ask - leg.entry_bid) + (leg.exit_ask - leg.exit_bid))
                * leg.quantity
                * spec.multiplier
                for leg in audit.execution_legs
            )
            audit.spread_stress_return_1_5x = round(
                (result.net_pnl - extra_spread_cost) / audit.risk_capital, 8
            )
            audit.winner = result.net_pnl > 0
            returns_by_split[observation.split].append(audit.net_return)

    train_metrics = _return_metrics(
        "train", returns_by_split["train"], list(audit_by_id.values()), spec
    )
    test_metrics = _return_metrics(
        "test", returns_by_split["test"], list(audit_by_id.values()), spec
    )
    holdout_metrics = _return_metrics(
        "holdout", returns_by_split["holdout"], list(audit_by_id.values()), spec
    )
    successful = sum(audit.net_return is not None for audit in audit_by_id.values())
    coverage = successful / len(spec.observations)
    reasons = _eligibility_reasons(spec, train_metrics, test_metrics, coverage)
    latest_selection = next(
        (
            audit.legs
            for audit in reversed(list(audit_by_id.values()))
            if audit.legs and audit.skipped_reason is None
        ),
        [],
    )
    stability_gap = (
        abs(train_metrics.mean_return - test_metrics.mean_return)
        if train_metrics is not None and test_metrics is not None
        else None
    )
    holdout_passed = _holdout_passed(spec, holdout_metrics)
    return MarketDataPanelStrategyResult(
        strategy=strategy,
        status="eligible" if not reasons else "insufficient_data",
        eligible_for_ranking=not reasons,
        eligibility_reasons=reasons,
        coverage_ratio=round(coverage, 8),
        train_metrics=train_metrics,
        test_metrics=test_metrics,
        holdout_metrics=holdout_metrics,
        holdout_passed=holdout_passed,
        stability_gap=round(stability_gap, 8) if stability_gap is not None else None,
        latest_selection=latest_selection,
        cases=list(audit_by_id.values()),
        backtest=backtest,
    )


def _no_trade_result(spec: MarketDataPanelSpec) -> MarketDataPanelStrategyResult:
    train_returns = [0.0 for item in spec.observations if item.split == "train"]
    test_returns = [0.0 for item in spec.observations if item.split == "test"]
    holdout_returns = [0.0 for item in spec.observations if item.split == "holdout"]
    empty_audits: list[MarketDataPanelCaseResult] = []
    train_metrics = _return_metrics("train", train_returns, empty_audits, spec)
    test_metrics = _return_metrics("test", test_returns, empty_audits, spec)
    holdout_metrics = _return_metrics("holdout", holdout_returns, empty_audits, spec)
    assert train_metrics is not None
    assert test_metrics is not None
    reasons = _eligibility_reasons(
        spec, train_metrics, test_metrics, 1.0, apply_multiple_testing=False
    )
    return MarketDataPanelStrategyResult(
        strategy=StrategyKind.NO_TRADE,
        status="eligible" if not reasons else "insufficient_data",
        eligible_for_ranking=not reasons,
        eligibility_reasons=reasons,
        coverage_ratio=1.0,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
        holdout_metrics=holdout_metrics,
        holdout_passed=True if holdout_metrics is not None else None,
        stability_gap=0.0,
        cases=[
            MarketDataPanelCaseResult(
                observation_id=item.observation_id,
                split=item.split,
                signal_quote_date=item.signal_quote_date,
                entry_quote_date=item.entry_quote_date,
                exit_quote_date=item.exit_quote_date,
                actual_exit_quote_date=item.exit_quote_date,
                exit_reason="time_exit",
                regime=item.regime,
                signal_momentum_20=item.signal_momentum_20,
                signal_realized_volatility_20=item.signal_realized_volatility_20,
                entry_outlay=0.0,
                exit_value=0.0,
                gross_pnl=0.0,
                costs=0.0,
                net_pnl=0.0,
                net_return=0.0,
                return_per_calendar_day=0.0,
                slippage_stress_return_2x=0.0,
                spread_stress_return_1_5x=0.0,
                winner=False,
            )
            for item in sorted(
                spec.observations,
                key=lambda observation: observation.signal_quote_date,
            )
        ],
    )


def _return_metrics(
    split: PanelSplit,
    values: Sequence[float],
    audits: Sequence[MarketDataPanelCaseResult],
    spec: MarketDataPanelSpec,
) -> MarketDataPanelReturnMetrics | None:
    if not values:
        return None
    cumulative = 0.0
    peak = 0.0
    maximum_drawdown = 0.0
    for value in values:
        cumulative += value
        peak = max(peak, cumulative)
        maximum_drawdown = max(maximum_drawdown, peak - cumulative)
    volatility = sample_volatility(values)
    downside = downside_deviation(values)
    successes = sum(value > 0 for value in values)
    win_low, win_high = wilson_interval(successes, len(values))
    seed = 17 + sum(ord(character) for character in f"{spec.experiment_id}:{split}")
    mean_low, mean_high = bootstrap_interval(
        values, fmean, samples=spec.bootstrap_samples, seed=seed
    )
    median_low, median_high = bootstrap_interval(
        values, median, samples=spec.bootstrap_samples, seed=seed + 1
    )
    split_audits = [
        audit for audit in audits if audit.split == split and audit.net_return is not None
    ]
    effective_observations = _effective_observations(split_audits) or len(values)
    factor = profit_factor(values)
    if factor is not None and not isfinite(factor):
        factor = None
    return MarketDataPanelReturnMetrics(
        split=split,
        observations=len(values),
        effective_observations=effective_observations,
        total_net_pnl=round(sum(audit.net_pnl or 0.0 for audit in split_audits), 6),
        mean_return=round(fmean(values), 8),
        median_return=round(median(values), 8),
        win_rate=round(successes / len(values), 8),
        win_rate_ci_low=round(win_low, 8),
        win_rate_ci_high=round(win_high, 8),
        mean_return_ci_low=round(mean_low, 8),
        mean_return_ci_high=round(mean_high, 8),
        median_return_ci_low=round(median_low, 8),
        median_return_ci_high=round(median_high, 8),
        return_volatility=round(volatility, 8),
        downside_deviation=round(downside, 8),
        return_to_volatility=(round(fmean(values) / volatility, 8) if volatility else None),
        sortino_ratio=(round(fmean(values) / downside, 8) if downside else None),
        profit_factor=round(factor, 8) if factor is not None else None,
        payoff_ratio=(round(ratio, 8) if (ratio := payoff_ratio(values)) is not None else None),
        value_at_risk_95=round(value_at_risk(values), 8),
        conditional_value_at_risk_95=round(conditional_value_at_risk(values), 8),
        deflated_sharpe_probability=(
            round(probability, 8)
            if (probability := deflated_sharpe_probability(values, spec.multiple_testing_trials))
            is not None
            else None
        ),
        maximum_drawdown=round(maximum_drawdown, 8),
        worst_return=round(min(values), 8),
    )


def _eligibility_reasons(
    spec: MarketDataPanelSpec,
    train: MarketDataPanelReturnMetrics | None,
    test: MarketDataPanelReturnMetrics | None,
    coverage: float,
    *,
    apply_multiple_testing: bool = True,
) -> list[str]:
    reasons: list[str] = []
    if train is None or train.effective_observations < spec.minimum_train_observations:
        reasons.append("insufficient train observations")
    if test is None or test.effective_observations < spec.minimum_test_observations:
        reasons.append("insufficient test observations")
    if coverage < spec.minimum_coverage_ratio:
        reasons.append("coverage below configured minimum")
    if test is not None and test.median_return < spec.minimum_test_median_return:
        reasons.append("test median return below configured minimum")
    if test is not None and test.maximum_drawdown > spec.maximum_test_drawdown:
        reasons.append("test drawdown above configured maximum")
    if test is not None and test.worst_return < -spec.maximum_test_worst_loss:
        reasons.append("test worst loss above configured maximum")
    if (
        apply_multiple_testing
        and test is not None
        and spec.minimum_deflated_sharpe_probability > 0
        and (
            test.deflated_sharpe_probability is None
            or test.deflated_sharpe_probability < spec.minimum_deflated_sharpe_probability
        )
    ):
        reasons.append("deflated Sharpe probability below configured minimum")
    if train is not None and test is not None:
        stability_gap = abs(train.mean_return - test.mean_return)
        if stability_gap > spec.maximum_stability_gap:
            reasons.append("train/test stability gap above configured maximum")
    return reasons


def _holdout_passed(
    spec: MarketDataPanelSpec, metrics: MarketDataPanelReturnMetrics | None
) -> bool | None:
    if metrics is None:
        return None
    if metrics.effective_observations < spec.minimum_holdout_observations:
        return False
    return (
        metrics.median_return >= spec.minimum_test_median_return
        and metrics.maximum_drawdown <= spec.maximum_test_drawdown
        and metrics.worst_return >= -spec.maximum_test_worst_loss
    )


def _effective_observations(audits: Sequence[MarketDataPanelCaseResult]) -> int:
    count = 0
    latest_exit: date | None = None
    for audit in sorted(audits, key=lambda item: item.entry_quote_date):
        if latest_exit is None or audit.entry_quote_date >= latest_exit:
            count += 1
            latest_exit = audit.exit_quote_date
        else:
            latest_exit = max(latest_exit, audit.exit_quote_date)
    return count


def _ranking_key(result: MarketDataPanelStrategyResult) -> tuple[float, float, float, str]:
    assert result.test_metrics is not None
    assert result.stability_gap is not None
    return (
        -result.test_metrics.median_return,
        result.test_metrics.maximum_drawdown,
        result.stability_gap,
        result.strategy.value,
    )


def _panel_source(
    spec: MarketDataPanelSpec,
    retrieved: datetime,
    request_count: int,
    cache_hits: int,
) -> EvidenceReference:
    return EvidenceReference(
        id=f"MARKETDATA-EOD-PANEL-{spec.ticker.upper()}-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
        title=f"MarketData.app EOD walk-forward option panel for {spec.ticker.upper()}",
        source_type="marketdata_app_historical_eod_walk_forward",
        uri=f"{MARKETDATA_BASE_URL}/v1/options/chain/{spec.ticker.upper()}/",
        status=EvidenceStatus.READ_ONLY_GATE,
        accessed_at=retrieved,
        confidence_level="medium",
        notes=(
            f"{request_count} filtered request(s), {cache_hits} cache hit(s); "
            "prior-session selection and later EOD bid/ask execution proxy"
        ),
        used_for_decision=True,
    )


def _signal_expiration(
    spec: MarketDataPanelSpec, observation: MarketDataPanelObservationSpec
) -> date | Literal["all"]:
    if set(spec.strategies) & _TERM_STRATEGIES:
        return "all"
    expiration = observation.expiration or spec.expiration
    return expiration if expiration is not None else "all"


def _target_expiration_records(
    records: Sequence[MarketDataOptionRecord],
    observation: MarketDataPanelObservationSpec,
    spec: MarketDataPanelSpec,
) -> list[MarketDataOptionRecord]:
    explicit = observation.expiration or spec.expiration
    if explicit is not None:
        return [record for record in records if record.expiration.date() == explicit]
    if spec.target_dte is None:
        return []
    target_dte = spec.target_dte
    expirations = {
        record.expiration.date()
        for record in records
        if record.expiration.date() > observation.exit_quote_date
    }
    if not expirations:
        return []
    target = min(
        expirations,
        key=lambda expiration: abs((expiration - observation.signal_quote_date).days - target_dte),
    )
    return [record for record in records if record.expiration.date() == target]


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("panel timestamps must be timezone-aware")
    return value.astimezone(UTC)
