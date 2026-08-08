"""V7 accuracy suites combining rolling panels, holdout validation, and current scans."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from math import log
from pathlib import Path
from statistics import stdev
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import (
    EvidenceReference,
    EvidenceStatus,
    ModelReadiness,
    StrategyKind,
    StrictModel,
)
from take_two_options.marketdata_data import (
    MarketDataChainExport,
    MarketDataError,
    parse_occ_option_symbol,
)
from take_two_options.marketdata_panel import (
    MarketDataPanelClient,
    MarketDataPanelObservationSpec,
    MarketDataPanelReport,
    MarketDataPanelReturnMetrics,
    MarketDataPanelSelectedLeg,
    MarketDataPanelSpec,
    estimate_selected_risk,
    run_marketdata_panel,
    select_marketdata_strategies,
)
from take_two_options.quantitative.contracts import DEFAULT_QUANT_CONVENTIONS
from take_two_options.treasury_data import TreasuryYieldCurve


class AccuracyEventSpec(StrictModel):
    event_date: date
    event_id: str = Field(min_length=1)
    category: str = Field(min_length=1)


class AccuracyDeltaProfile(StrictModel):
    profile_id: str = Field(min_length=1)
    long_delta_target: float = Field(gt=0, lt=1)
    short_delta_target: float = Field(gt=0, lt=1)
    selection_mode: Literal["delta", "moneyness"] = "delta"
    long_moneyness_offset: float = Field(default=0.0, ge=-0.75, le=2.0)
    maximum_moneyness_target_gap: float = Field(default=0.05, gt=0, le=0.50)
    wing_width_pct: float = Field(default=0.10, gt=0, le=0.50)

    @model_validator(mode="after")
    def validate_targets(self) -> AccuracyDeltaProfile:
        if self.short_delta_target >= self.long_delta_target:
            raise ValueError("short delta target must be below long delta target")
        return self


class AccuracyExperimentTemplate(StrictModel):
    experiment_id: str = Field(min_length=1)
    holding_sessions: int = Field(ge=1, le=252)
    target_dte: int = Field(ge=30, le=730)
    profile_ids: list[str] = Field(min_length=1)
    maximum_observations: int | None = Field(default=None, ge=6, le=100)
    minimum_train_observations: int = Field(default=8, ge=1)
    minimum_test_observations: int = Field(default=4, ge=1)
    minimum_holdout_observations: int = Field(default=2, ge=0)
    strategies: list[StrategyKind] | None = None
    front_target_dte: int = Field(default=45, ge=7, le=365)
    front_expiry_buffer_days: int = Field(default=7, ge=1, le=60)
    profit_target: float | None = Field(default=None, gt=0, le=10)
    stop_loss: float | None = Field(default=None, gt=0, le=1)
    exit_policy_id: str = "time_exit"
    regime_filter: str | None = None
    monitor_every_sessions: int = Field(default=1, ge=1, le=20)
    budget_plan_id: str | None = None
    budget_bucket: str | None = None
    budget_eur: float | None = Field(default=None, gt=0)


class AccuracyGeneratorSpec(StrictModel):
    ticker: str = "TTWO"
    start_date: date
    end_date: date
    split_train_ratio: float = Field(default=0.60, gt=0, lt=1)
    split_test_ratio: float = Field(default=0.25, gt=0, lt=1)
    embargo_observations: int = Field(default=1, ge=1, le=5)
    profiles: list[AccuracyDeltaProfile] = Field(min_length=1)
    experiments: list[AccuracyExperimentTemplate] = Field(min_length=1)
    events: list[AccuracyEventSpec] = Field(default_factory=list)
    strategies: list[StrategyKind] = Field(
        default_factory=lambda: [
            StrategyKind.NO_TRADE,
            StrategyKind.LONG_CALL,
            StrategyKind.BULL_CALL_SPREAD,
            StrategyKind.LONG_PUT,
            StrategyKind.BEAR_PUT_SPREAD,
        ]
    )
    current_quote_date: date
    min_open_interest: int = Field(default=20, ge=0)
    min_volume: int = Field(default=0, ge=0)
    max_bid_ask_ratio: float = Field(default=0.30, gt=0, le=2)
    strike_limit: int = Field(default=16, ge=4, le=100)
    multiplier: float = Field(default=100, gt=0)
    commission_per_contract_per_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_per_side: float = Field(default=1.50, ge=0)
    minimum_coverage_ratio: float = Field(default=0.75, gt=0, le=1)
    minimum_test_median_return: float = Field(default=0.0, ge=-1, le=10)
    maximum_test_drawdown: float = Field(default=0.35, gt=0, le=10)
    maximum_test_worst_loss: float = Field(default=0.35, gt=0, le=1)
    maximum_stability_gap: float = Field(default=0.15, ge=0, le=10)
    minimum_deflated_sharpe_probability: float = Field(default=0.80, ge=0, le=1)
    bootstrap_samples: int = Field(default=2_000, ge=100, le=100_000)
    bullish_momentum_threshold: float = Field(default=0.05, gt=0, le=1)
    bearish_momentum_threshold: float = Field(default=-0.05, ge=-1, lt=0)
    high_volatility_threshold: float = Field(default=0.45, gt=0, le=3)
    holdout_policy: Literal["fresh", "reused_exploratory"] = "fresh"
    eur_usd_rate: float = Field(default=1.0, gt=0)
    eur_usd_rate_date: date | None = None

    @model_validator(mode="after")
    def validate_generator(self) -> AccuracyGeneratorSpec:
        if self.start_date >= self.end_date:
            raise ValueError("accuracy start_date must precede end_date")
        if self.split_train_ratio + self.split_test_ratio >= 0.95:
            raise ValueError("accuracy split ratios must leave a holdout allocation")
        profile_ids = {profile.profile_id for profile in self.profiles}
        if len(profile_ids) != len(self.profiles):
            raise ValueError("accuracy profile IDs must be unique")
        for experiment in self.experiments:
            unknown = set(experiment.profile_ids) - profile_ids
            if unknown:
                raise ValueError(f"unknown accuracy profiles: {sorted(unknown)}")
            budget_fields = (
                experiment.budget_plan_id,
                experiment.budget_bucket,
                experiment.budget_eur,
            )
            if any(value is not None for value in budget_fields) and any(
                value is None for value in budget_fields
            ):
                raise ValueError("budget experiments require plan, bucket and EUR budget")
            if experiment.budget_eur is not None and self.eur_usd_rate_date is None:
                raise ValueError("budget experiments require an EUR/USD reference date")
        if len({item.experiment_id for item in self.experiments}) != len(self.experiments):
            raise ValueError("accuracy experiment IDs must be unique")
        return self


class AccuracyCurrentExpirationSpec(StrictModel):
    expiration: date
    risk_free_rate: float = Field(gt=-0.2, lt=1)


class AccuracyCurrentScanSpec(StrictModel):
    quote_date: date
    expirations: list[AccuracyCurrentExpirationSpec] = Field(min_length=1)


class MarketDataAccuracySuiteSpec(StrictModel):
    ticker: str
    panels: list[MarketDataPanelSpec] = Field(min_length=1)
    current_scan: AccuracyCurrentScanSpec
    treasury_source_url: str
    event_source_urls: list[str] = Field(default_factory=list)
    holdout_policy: Literal["fresh", "reused_exploratory"] = "fresh"
    research_version: str = "V7"
    notes: str = ""

    @model_validator(mode="after")
    def validate_suite(self) -> MarketDataAccuracySuiteSpec:
        if len({panel.experiment_id for panel in self.panels}) != len(self.panels):
            raise ValueError("accuracy panel experiment IDs must be unique")
        if any(panel.ticker.upper() != self.ticker.upper() for panel in self.panels):
            raise ValueError("accuracy suite panel ticker mismatch")
        return self


class AccuracyVariantSummary(StrictModel):
    variant_id: str
    experiment_id: str
    strategy: StrategyKind
    target_dte: int | None = None
    holding_sessions: int | None = None
    eligible_for_ranking: bool
    holdout_passed: bool | None = None
    eligibility_reasons: list[str] = Field(default_factory=list)
    train_metrics: MarketDataPanelReturnMetrics | None = None
    test_metrics: MarketDataPanelReturnMetrics | None = None
    holdout_metrics: MarketDataPanelReturnMetrics | None = None


class AccuracyCurrentCandidate(StrictModel):
    candidate_id: str
    experiment_id: str
    strategy: StrategyKind
    quote_date: date
    expiration: date | None = None
    status: Literal["eligible", "watchlist", "blocked", "no_trade"]
    reasons: list[str] = Field(default_factory=list)
    legs: list[MarketDataPanelSelectedLeg] = Field(default_factory=list)
    historical_test_metrics: MarketDataPanelReturnMetrics | None = None
    historical_holdout_metrics: MarketDataPanelReturnMetrics | None = None
    entry_rule: str = ""
    exit_rule: str = ""
    net_debit_credit: float | None = None
    risk_capital: float | None = Field(default=None, gt=0)
    estimated_max_gain: float | None = Field(default=None, ge=0)
    estimated_max_loss: float | None = Field(default=None, gt=0)
    signal_implied_volatility: float | None = Field(default=None, ge=0)
    net_delta: float | None = None
    max_bid_ask_ratio: float | None = Field(default=None, ge=0)
    minimum_open_interest: float | None = Field(default=None, ge=0)
    budget_plan_id: str | None = None
    budget_bucket: str | None = None
    budget_eur: float | None = Field(default=None, gt=0)
    eur_usd_rate: float | None = Field(default=None, gt=0)
    eur_usd_rate_date: date | None = None


class MarketDataAccuracyReport(StrictModel):
    ticker: str
    created_at: datetime
    source: EvidenceReference
    model_readiness: ModelReadiness = ModelReadiness.SCREEN_GRADE
    execution_price_quality: Literal["historical_eod_bid_ask"] = "historical_eod_bid_ask"
    panels: list[MarketDataPanelReport]
    variants: list[AccuracyVariantSummary]
    current_candidates: list[AccuracyCurrentCandidate]
    ranked_variant_ids: list[str]
    provider_requests: int = Field(ge=0)
    cache_hits: int = Field(ge=0)
    warnings: list[str]
    holdout_policy: Literal["fresh", "reused_exploratory"] = "fresh"
    research_version: str = "V7"
    order_capability: Literal["forbidden"] = "forbidden"


def load_market_sessions(calibration_dataset: Path) -> list[date]:
    return sorted(load_market_closes(calibration_dataset))


def load_market_closes(calibration_dataset: Path) -> dict[date, float]:
    import json

    payload = json.loads(calibration_dataset.read_text(encoding="utf-8"))
    points = payload.get("points")
    if not isinstance(points, list):
        raise ValueError("calibration dataset points are missing")
    closes = {
        datetime.fromisoformat(str(point["timestamp"]).replace("Z", "+00:00")).date(): float(
            point["close"]
        )
        for point in points
        if isinstance(point, dict) and point.get("timestamp") and point.get("close")
    }
    if not closes:
        raise ValueError("calibration dataset contains no market sessions")
    return closes


def load_current_expirations(alpaca_chain: Path, quote_date: date) -> list[date]:
    import json

    payload = json.loads(alpaca_chain.read_text(encoding="utf-8"))
    contracts = payload.get("contracts")
    if not isinstance(contracts, list):
        raise ValueError("Alpaca option chain contracts are missing")
    expirations = {
        parse_occ_option_symbol(str(contract["symbol"])).expiration
        for contract in contracts
        if isinstance(contract, dict) and contract.get("symbol")
    }
    eligible = sorted(expiration for expiration in expirations if expiration > quote_date)
    if not eligible:
        raise ValueError("Alpaca option chain contains no future expirations")
    return eligible


def generate_accuracy_suite_spec(
    config: AccuracyGeneratorSpec,
    sessions: Sequence[date],
    treasury_curve: TreasuryYieldCurve,
    *,
    current_expirations: Sequence[date] | None = None,
    market_closes: Mapping[date, float] | None = None,
) -> MarketDataAccuracySuiteSpec:
    eligible_sessions = [
        session for session in sessions if config.start_date <= session <= config.end_date
    ]
    if len(eligible_sessions) < 20:
        raise ValueError("accuracy generator requires at least 20 market sessions")
    profiles = {profile.profile_id: profile for profile in config.profiles}
    panels: list[MarketDataPanelSpec] = []
    for experiment in config.experiments:
        windows = _observation_windows(
            eligible_sessions,
            experiment.holding_sessions,
            experiment.maximum_observations,
        )
        if experiment.regime_filter is not None:
            windows = [
                window
                for window in windows
                if _regime_details(
                    window[0],
                    window[2],
                    config.events,
                    market_closes or {},
                    config,
                )[0]
                == experiment.regime_filter
            ]
        split_windows = _assign_splits(windows, config)
        for profile_id in experiment.profile_ids:
            profile = profiles[profile_id]
            observations = []
            for index, (split, signal, entry, exit_date) in enumerate(split_windows):
                regime, momentum, realized_volatility = _regime_details(
                    signal,
                    exit_date,
                    config.events,
                    market_closes or {},
                    config,
                )
                observations.append(
                    MarketDataPanelObservationSpec(
                        observation_id=f"{experiment.experiment_id}-{index + 1:02d}",
                        split=split,
                        signal_quote_date=signal,
                        entry_quote_date=entry,
                        exit_quote_date=exit_date,
                        monitor_quote_dates=_sample_monitor_dates(
                            _sessions_between(eligible_sessions, entry, exit_date),
                            experiment.monitor_every_sessions,
                        ),
                        expiration=None,
                        risk_free_rate=round(
                            treasury_curve.rate_for(signal, experiment.target_dte), 8
                        ),
                        regime=regime,
                        signal_momentum_20=momentum,
                        signal_realized_volatility_20=realized_volatility,
                    )
                )
            panels.append(
                MarketDataPanelSpec(
                    ticker=config.ticker.upper(),
                    experiment_id=f"{experiment.experiment_id}__{profile.profile_id}",
                    expiration=None,
                    risk_free_rate=0.04,
                    strategies=experiment.strategies or config.strategies,
                    observations=observations,
                    long_delta_target=profile.long_delta_target,
                    short_delta_target=profile.short_delta_target,
                    selection_mode=profile.selection_mode,
                    long_moneyness_offset=profile.long_moneyness_offset,
                    maximum_moneyness_target_gap=profile.maximum_moneyness_target_gap,
                    wing_width_pct=profile.wing_width_pct,
                    front_target_dte=experiment.front_target_dte,
                    front_expiry_buffer_days=experiment.front_expiry_buffer_days,
                    strike_limit=config.strike_limit,
                    min_open_interest=config.min_open_interest,
                    min_volume=config.min_volume,
                    max_bid_ask_ratio=config.max_bid_ask_ratio,
                    multiplier=config.multiplier,
                    commission_per_contract_per_side=config.commission_per_contract_per_side,
                    slippage_per_contract_per_side=config.slippage_per_contract_per_side,
                    minimum_train_observations=experiment.minimum_train_observations,
                    minimum_test_observations=experiment.minimum_test_observations,
                    minimum_holdout_observations=experiment.minimum_holdout_observations,
                    minimum_coverage_ratio=config.minimum_coverage_ratio,
                    minimum_test_median_return=config.minimum_test_median_return,
                    maximum_test_drawdown=config.maximum_test_drawdown,
                    maximum_test_worst_loss=config.maximum_test_worst_loss,
                    maximum_stability_gap=config.maximum_stability_gap,
                    minimum_embargo_days=1,
                    minimum_deflated_sharpe_probability=(
                        config.minimum_deflated_sharpe_probability
                    ),
                    bootstrap_samples=config.bootstrap_samples,
                    target_dte=experiment.target_dte,
                    holding_sessions=experiment.holding_sessions,
                    profit_target=experiment.profit_target,
                    stop_loss=experiment.stop_loss,
                    exit_policy_id=experiment.exit_policy_id,
                    budget_plan_id=experiment.budget_plan_id,
                    budget_bucket=experiment.budget_bucket,
                    budget_eur=experiment.budget_eur,
                    eur_usd_rate=(
                        config.eur_usd_rate if experiment.budget_eur is not None else None
                    ),
                    eur_usd_rate_date=(
                        config.eur_usd_rate_date if experiment.budget_eur is not None else None
                    ),
                    notes=(
                        "V9 rolling-expiration panel with Treasury rates, path exits, "
                        "market descriptors, and purged boundaries."
                    ),
                )
            )
    trial_count = sum(
        sum(strategy is not StrategyKind.NO_TRADE for strategy in panel.strategies)
        for panel in panels
    )
    panels = [panel.model_copy(update={"multiple_testing_trials": trial_count}) for panel in panels]
    available_current_expirations = sorted(set(current_expirations or []))
    current_target_dtes = {
        target
        for item in config.experiments
        for target in (
            item.target_dte,
            *(
                (item.front_target_dte,)
                if set(item.strategies or config.strategies)
                & {StrategyKind.LONG_CALL_CALENDAR, StrategyKind.CALL_DIAGONAL}
                else ()
            ),
        )
    }
    if available_current_expirations:
        selected_current_expirations = sorted(
            {
                min(
                    available_current_expirations,
                    key=lambda expiration: abs(
                        (expiration - config.current_quote_date).days - target_dte
                    ),
                )
                for target_dte in current_target_dtes
            }
        )
    else:
        selected_current_expirations = sorted(
            {
                _monthly_expiration(config.current_quote_date, target_dte)
                for target_dte in current_target_dtes
            }
        )
    current_scan = AccuracyCurrentScanSpec(
        quote_date=config.current_quote_date,
        expirations=[
            AccuracyCurrentExpirationSpec(
                expiration=expiration,
                risk_free_rate=round(
                    treasury_curve.rate_for(
                        config.current_quote_date,
                        (expiration - config.current_quote_date).days,
                    ),
                    8,
                ),
            )
            for expiration in selected_current_expirations
        ],
    )
    return MarketDataAccuracySuiteSpec(
        ticker=config.ticker.upper(),
        panels=panels,
        current_scan=current_scan,
        treasury_source_url=(
            "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
            "TextView?type=daily_treasury_yield_curve"
        ),
        event_source_urls=[
            "https://www.take2games.com/ir/news/",
            "https://www.take2games.com/ir",
        ],
        holdout_policy=config.holdout_policy,
        research_version="V9",
        notes=(
            "Generated from Alpaca sessions, official Treasury par yields, and explicitly "
            "declared Take-Two events. Event labels are descriptive, not causal proof."
        ),
    )


def run_accuracy_suite(
    client: MarketDataPanelClient,
    spec: MarketDataAccuracySuiteSpec,
    *,
    force_refresh: bool = False,
    retrieved_at: datetime | None = None,
) -> MarketDataAccuracyReport:
    retrieved = _ensure_utc(retrieved_at or datetime.now(UTC))
    memo_client = _MemoizingPanelClient(client)
    panel_reports = [
        run_marketdata_panel(
            memo_client,
            panel,
            force_refresh=force_refresh,
            retrieved_at=retrieved,
        )
        for panel in spec.panels
    ]
    variants = _variant_summaries(panel_reports)
    current_candidates, scan_requests, scan_cache_hits = _current_candidates(
        memo_client,
        spec,
        panel_reports,
        force_refresh=force_refresh,
        retrieved=retrieved,
    )
    eligible = sorted(
        (
            variant
            for variant in variants
            if variant.strategy is not StrategyKind.NO_TRADE
            and variant.eligible_for_ranking
            and variant.holdout_passed is True
            and spec.holdout_policy == "fresh"
            and variant.test_metrics is not None
        ),
        key=lambda item: (
            -item.test_metrics.median_return if item.test_metrics else 0,
            item.test_metrics.conditional_value_at_risk_95 if item.test_metrics else 0,
            item.variant_id,
        ),
    )
    ranked = [item.variant_id for item in eligible]
    if not ranked:
        ranked = ["no_trade"]
    source = EvidenceReference(
        id=f"TTWO-{spec.research_version}-ACCURACY-{retrieved.strftime('%Y%m%dT%H%M%SZ')}",
        title=(
            f"{spec.ticker.upper()} {spec.research_version} rolling "
            "MarketData.app opportunity suite"
        ),
        source_type="marketdata_app_eod_accuracy_suite",
        uri="https://api.marketdata.app/v1/options/chain/TTWO/",
        status=EvidenceStatus.READ_ONLY_GATE,
        accessed_at=retrieved,
        confidence_level="medium",
        notes=(
            "EOD bid/ask, purged chronological splits, "
            f"holdout policy {spec.holdout_policy}, no order capability"
        ),
        used_for_decision=True,
    )
    return MarketDataAccuracyReport(
        ticker=spec.ticker.upper(),
        created_at=retrieved,
        source=source,
        panels=panel_reports,
        variants=variants,
        current_candidates=current_candidates,
        ranked_variant_ids=ranked,
        provider_requests=sum(panel.provider_requests for panel in panel_reports) + scan_requests,
        cache_hits=sum(panel.cache_hits for panel in panel_reports) + scan_cache_hits,
        holdout_policy=spec.holdout_policy,
        research_version=spec.research_version,
        warnings=[
            "Research only; ranking and current candidates cannot authorize an order or size",
            "Forecast accuracy is observed net win rate with a 95% Wilson interval",
            "Holdout results do not remove regime, sample-size, or selection uncertainty",
            "MarketData.app EOD bid/ask is not an intraday NBBO or combo-fill replay",
            "Deflated Sharpe is a multiple-testing diagnostic at the observed holding-period scale",
            (
                "A reused exploratory holdout can populate a watchlist but cannot produce "
                "an eligible candidate"
            ),
            "No-trade remains the baseline when no option variant clears every gate",
        ],
    )


def render_accuracy_markdown(report: MarketDataAccuracyReport) -> str:
    lines = [
        f"# TTWO {report.research_version} options opportunity report",
        "",
        f"- Created: `{report.created_at.isoformat()}`",
        f"- Panels / variants: `{len(report.panels)}` / `{len(report.variants)}`",
        f"- Provider requests: `{report.provider_requests}` ({report.cache_hits} cache hits)",
        f"- Ranking: `{', '.join(report.ranked_variant_ids)}`",
        f"- Holdout policy: `{report.holdout_policy}`",
        "- Order capability: `forbidden`",
        "",
        "## Current candidates",
        "",
    ]
    for candidate in report.current_candidates:
        metrics = candidate.historical_test_metrics
        accuracy = (
            f"accuracy {metrics.win_rate:.1%} "
            f"[{metrics.win_rate_ci_low:.1%}, {metrics.win_rate_ci_high:.1%}]"
            if metrics is not None
            else "accuracy unavailable"
        )
        lines.append(
            f"- `{candidate.candidate_id}`: `{candidate.status}`, {accuracy}; "
            f"{' ; '.join(candidate.reasons) or 'all configured gates passed'}"
        )
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    lines.append("")
    return "\n".join(lines)


def _variant_summaries(
    panels: Sequence[MarketDataPanelReport],
) -> list[AccuracyVariantSummary]:
    return [
        AccuracyVariantSummary(
            variant_id=f"{panel.experiment_id}:{result.strategy.value}",
            experiment_id=panel.experiment_id,
            strategy=result.strategy,
            target_dte=panel.target_dte,
            holding_sessions=panel.holding_sessions,
            eligible_for_ranking=result.eligible_for_ranking,
            holdout_passed=result.holdout_passed,
            eligibility_reasons=result.eligibility_reasons,
            train_metrics=result.train_metrics,
            test_metrics=result.test_metrics,
            holdout_metrics=result.holdout_metrics,
        )
        for panel in panels
        for result in panel.strategies
    ]


def _current_candidates(
    client: MarketDataPanelClient,
    spec: MarketDataAccuracySuiteSpec,
    panels: Sequence[MarketDataPanelReport],
    *,
    force_refresh: bool,
    retrieved: datetime,
) -> tuple[list[AccuracyCurrentCandidate], int, int]:
    panel_specs = {panel.experiment_id: panel for panel in spec.panels}
    exports = {}
    requests = 0
    cache_hits = 0
    representative = spec.panels[0]
    for item in spec.current_scan.expirations:
        try:
            export = client.historical_chain(
                ticker=spec.ticker.upper(),
                quote_date=spec.current_scan.quote_date,
                expiration=item.expiration,
                side=None,
                strikes=None,
                strike_limit=representative.strike_limit,
                min_open_interest=representative.min_open_interest or None,
                min_volume=representative.min_volume or None,
                risk_free_rate=item.risk_free_rate,
                continuous_dividend_yield=representative.continuous_dividend_yield,
                dividends=tuple(
                    (dividend.ex_date, dividend.amount) for dividend in representative.dividends
                ),
                time_grid=representative.time_grid,
                price_grid=representative.price_grid,
                force_refresh=force_refresh,
                retrieved_at=retrieved,
            )
        except MarketDataError:
            requests += 1
            continue
        exports[item.expiration] = export
        requests += 1
        cache_hits += int(export.cache_hit)
    candidates: list[AccuracyCurrentCandidate] = [
        AccuracyCurrentCandidate(
            candidate_id="no_trade",
            experiment_id="baseline",
            strategy=StrategyKind.NO_TRADE,
            quote_date=spec.current_scan.quote_date,
            status="no_trade",
            reasons=["baseline retained until an option variant clears every gate"],
            entry_rule="No position",
            exit_rule="No position",
        )
    ]
    if not exports:
        return candidates, requests, cache_hits
    current_records = [record for export in exports.values() for record in export.contracts]
    for panel in panels:
        panel_spec = panel_specs[panel.experiment_id]
        selections = select_marketdata_strategies(current_records, panel_spec)
        for result in panel.strategies:
            if result.strategy is StrategyKind.NO_TRADE:
                continue
            legs, selection_reason = selections.get(
                result.strategy, ([], "current selection unavailable")
            )
            net_debit_credit, risk_capital, max_gain, max_loss = estimate_selected_risk(
                legs, panel_spec
            )
            reasons = list(result.eligibility_reasons)
            if result.holdout_passed is not True:
                reasons.append("holdout validation did not pass")
            if selection_reason is not None:
                reasons.append(selection_reason)
            if (
                panel_spec.budget_eur is not None
                and panel_spec.eur_usd_rate is not None
                and risk_capital is not None
                and risk_capital > panel_spec.budget_eur * panel_spec.eur_usd_rate
            ):
                reasons.append("current structure exceeds configured EUR risk budget")
            numerically_passed = not reasons and bool(legs)
            status: Literal["eligible", "watchlist", "blocked", "no_trade"]
            if numerically_passed and spec.holdout_policy == "fresh":
                status = "eligible"
            elif numerically_passed:
                status = "watchlist"
                reasons.append("holdout was reused after V7 inspection; fresh validation required")
            else:
                status = "blocked"
            expiration = max((leg.expiration for leg in legs), default=None)
            signal_ivs = [
                leg.signal_implied_volatility
                for leg in legs
                if leg.signal_implied_volatility is not None
            ]
            open_interest = [
                leg.signal_open_interest for leg in legs if leg.signal_open_interest is not None
            ]
            candidates.append(
                AccuracyCurrentCandidate(
                    candidate_id=f"{panel.experiment_id}:{result.strategy.value}",
                    experiment_id=panel.experiment_id,
                    strategy=result.strategy,
                    quote_date=spec.current_scan.quote_date,
                    expiration=expiration,
                    status=status,
                    reasons=reasons,
                    legs=legs,
                    historical_test_metrics=result.test_metrics,
                    historical_holdout_metrics=result.holdout_metrics,
                    entry_rule=_entry_rule(panel_spec),
                    exit_rule=_exit_rule(panel_spec),
                    net_debit_credit=(
                        round(net_debit_credit, 6) if net_debit_credit is not None else None
                    ),
                    risk_capital=round(risk_capital, 6) if risk_capital else None,
                    estimated_max_gain=round(max_gain, 6) if max_gain is not None else None,
                    estimated_max_loss=round(max_loss, 6) if max_loss else None,
                    signal_implied_volatility=(
                        round(sum(signal_ivs) / len(signal_ivs), 8) if signal_ivs else None
                    ),
                    net_delta=(
                        round(
                            sum(
                                leg.position_side.sign * leg.quantity * leg.signal_delta
                                for leg in legs
                            ),
                            8,
                        )
                        if legs
                        else None
                    ),
                    max_bid_ask_ratio=max((leg.bid_ask_ratio for leg in legs), default=None),
                    minimum_open_interest=min(open_interest) if open_interest else None,
                    budget_plan_id=panel_spec.budget_plan_id,
                    budget_bucket=panel_spec.budget_bucket,
                    budget_eur=panel_spec.budget_eur,
                    eur_usd_rate=panel_spec.eur_usd_rate,
                    eur_usd_rate_date=panel_spec.eur_usd_rate_date,
                )
            )
    return candidates, requests, cache_hits


def _observation_windows(
    sessions: Sequence[date], holding_sessions: int, maximum: int | None
) -> list[tuple[date, date, date]]:
    windows: list[tuple[date, date, date]] = []
    cursor = 0
    while cursor + holding_sessions + 1 < len(sessions):
        signal = sessions[cursor]
        entry = sessions[cursor + 1]
        exit_date = sessions[cursor + holding_sessions + 1]
        windows.append((signal, entry, exit_date))
        # The next position may enter on the prior position's exit close, but never before it.
        cursor += holding_sessions
    if maximum is not None and len(windows) > maximum:
        windows = windows[-maximum:]
    if len(windows) < 6:
        raise ValueError("accuracy experiment produced fewer than six observations")
    return windows


def _assign_splits(
    windows: Sequence[tuple[date, date, date]], config: AccuracyGeneratorSpec
) -> list[tuple[Literal["train", "test", "holdout"], date, date, date]]:
    total = len(windows)
    usable = total - 2 * config.embargo_observations
    if usable < 3:
        raise ValueError("accuracy split requires room for train, test, holdout, and embargoes")
    train_count = max(1, int(usable * config.split_train_ratio))
    test_count = max(1, int(usable * config.split_test_ratio))
    if train_count + test_count >= usable:
        test_count = max(1, usable - train_count - 1)
    first_test = train_count + config.embargo_observations
    first_holdout = first_test + test_count + config.embargo_observations
    assigned: list[tuple[Literal["train", "test", "holdout"], date, date, date]] = []
    for index, window in enumerate(windows):
        if train_count <= index < first_test:
            continue
        if first_test + test_count <= index < first_holdout:
            continue
        if index < train_count:
            split: Literal["train", "test", "holdout"] = "train"
        elif index < first_holdout:
            split = "test"
        else:
            split = "holdout"
        assigned.append((split, *window))
    if {item[0] for item in assigned} != {"train", "test", "holdout"}:
        raise ValueError("accuracy split assignment requires train, test, and holdout")
    return assigned


def _monthly_expiration(signal: date, target_dte: int) -> date:
    target = signal + timedelta(days=target_dte)
    candidates = []
    for offset in range(-2, 3):
        month_index = target.year * 12 + target.month - 1 + offset
        year, zero_based_month = divmod(month_index, 12)
        candidates.append(_third_friday(year, zero_based_month + 1))
    eligible = [candidate for candidate in candidates if candidate > signal]
    return min(eligible, key=lambda candidate: abs((candidate - signal).days - target_dte))


def _third_friday(year: int, month: int) -> date:
    first = date(year, month, 1)
    first_friday = first + timedelta(days=(4 - first.weekday()) % 7)
    return first_friday + timedelta(days=14)


def _regime(signal: date, exit_date: date, events: Sequence[AccuracyEventSpec]) -> str:
    relevant = [
        event
        for event in events
        if signal - timedelta(days=5) <= event.event_date <= exit_date + timedelta(days=1)
    ]
    if not relevant:
        return "ordinary"
    event = min(relevant, key=lambda item: abs((item.event_date - signal).days))
    return f"{event.category}:{event.event_id}"


def _regime_details(
    signal: date,
    exit_date: date,
    events: Sequence[AccuracyEventSpec],
    closes: Mapping[date, float],
    config: AccuracyGeneratorSpec,
) -> tuple[str, float | None, float | None]:
    event_regime = _regime(signal, exit_date, events)
    history = [(session, close) for session, close in sorted(closes.items()) if session <= signal]
    momentum: float | None = None
    realized_volatility: float | None = None
    if len(history) >= 21:
        values = [item[1] for item in history[-21:]]
        momentum = round(values[-1] / values[0] - 1, 8)
        returns = [log(current / prior) for prior, current in zip(values, values[1:], strict=False)]
        realized_volatility = round(
            DEFAULT_QUANT_CONVENTIONS.annualize_volatility(stdev(returns)), 8
        )
    if event_regime != "ordinary":
        return event_regime, momentum, realized_volatility
    if realized_volatility is not None and realized_volatility >= config.high_volatility_threshold:
        return "high_volatility", momentum, realized_volatility
    if momentum is not None and momentum >= config.bullish_momentum_threshold:
        return "bullish_momentum", momentum, realized_volatility
    if momentum is not None and momentum <= config.bearish_momentum_threshold:
        return "bearish_momentum", momentum, realized_volatility
    return "ordinary", momentum, realized_volatility


def _sessions_between(sessions: Sequence[date], entry: date, exit_date: date) -> list[date]:
    return [session for session in sessions if entry < session <= exit_date]


def _sample_monitor_dates(sessions: Sequence[date], every: int) -> list[date]:
    sampled = list(sessions[every - 1 :: every])
    if sessions and sessions[-1] not in sampled:
        sampled.append(sessions[-1])
    return sampled


def _entry_rule(panel: MarketDataPanelSpec) -> str:
    if panel.selection_mode == "moneyness":
        selection = (
            f"strike near spot {panel.long_moneyness_offset:+.0%} "
            f"(max gap {panel.maximum_moneyness_target_gap:.0%})"
        )
    else:
        selection = (
            f"long delta {panel.long_delta_target:.0%}; short delta {panel.short_delta_target:.0%}"
        )
    return f"{selection}; target {panel.target_dte or 'fixed'} DTE"


def _exit_rule(panel: MarketDataPanelSpec) -> str:
    rules = []
    if panel.profit_target is not None:
        rules.append(f"cash-out +{panel.profit_target:.0%}")
    if panel.stop_loss is not None:
        rules.append(f"stop -{panel.stop_loss:.0%}")
    rules.append(f"time exit {panel.holding_sessions or '?'} sessions")
    return "; ".join(rules)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("accuracy timestamps must be timezone-aware")
    return value.astimezone(UTC)


class _MemoizingPanelClient:
    def __init__(self, client: MarketDataPanelClient) -> None:
        self._client = client
        self._cache: dict[tuple[object, ...], MarketDataChainExport] = {}

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
    ) -> MarketDataChainExport:
        key = (
            ticker,
            quote_date,
            expiration,
            side,
            tuple(strikes or []),
            strike_limit,
            min_open_interest,
            min_volume,
            risk_free_rate,
            continuous_dividend_yield,
            dividends,
            time_grid,
            price_grid,
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached.model_copy(update={"cache_hit": True})
        export = self._client.historical_chain(
            ticker=ticker,
            quote_date=quote_date,
            expiration=expiration,
            side=side,
            strikes=strikes,
            strike_limit=strike_limit,
            min_open_interest=min_open_interest,
            min_volume=min_volume,
            risk_free_rate=risk_free_rate,
            continuous_dividend_yield=continuous_dividend_yield,
            dividends=dividends,
            time_grid=time_grid,
            price_grid=price_grid,
            force_refresh=force_refresh,
            retrieved_at=retrieved_at,
        )
        self._cache[key] = export
        return export
