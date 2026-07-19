"""Executable-price backtesting with explicit train/test and look-ahead controls."""

from __future__ import annotations

from datetime import datetime
from statistics import fmean, median
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import EvidenceReference, ModelReadiness, PositionSide, StrictModel


class HistoricalOptionQuote(StrictModel):
    timestamp: datetime
    data_available_at: datetime
    bid: float = Field(ge=0)
    ask: float = Field(ge=0)
    bid_size: float | None = Field(default=None, ge=0)
    ask_size: float | None = Field(default=None, ge=0)
    volume: float | None = Field(default=None, ge=0)
    open_interest: float | None = Field(default=None, ge=0)
    underlying_price: float | None = Field(default=None, gt=0)
    price_basis: Literal["nbbo", "eod_bid_ask", "option_bar_close_proxy"] = "nbbo"
    source_symbol: str = ""
    source_feed: str = ""

    @model_validator(mode="after")
    def validate_market(self) -> HistoricalOptionQuote:
        if self.ask < self.bid:
            raise ValueError("historical ask cannot be below bid")
        return self


class BacktestLeg(StrictModel):
    side: PositionSide
    quantity: int = Field(gt=0)
    multiplier: float = Field(default=100.0, gt=0)
    entry_quote: HistoricalOptionQuote
    exit_quote: HistoricalOptionQuote


BacktestSplit = Literal["train", "test", "holdout"]


class BacktestCase(StrictModel):
    case_id: str = Field(min_length=1)
    split: BacktestSplit
    entry_timestamp: datetime
    exit_timestamp: datetime
    model_calibrated_through: datetime
    legs: list[BacktestLeg] = Field(min_length=1)
    commission_per_contract_per_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_per_side: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_timeline(self) -> BacktestCase:
        if self.exit_timestamp <= self.entry_timestamp:
            raise ValueError("backtest exit must follow entry")
        if self.model_calibrated_through >= self.entry_timestamp:
            raise ValueError("model calibration must end before backtest entry")
        for leg in self.legs:
            if leg.entry_quote.timestamp > self.entry_timestamp:
                raise ValueError("entry quote timestamp follows the declared entry")
            if leg.entry_quote.data_available_at > self.entry_timestamp:
                raise ValueError("look-ahead detected in entry quote")
            if leg.exit_quote.timestamp > self.exit_timestamp:
                raise ValueError("exit quote timestamp follows the declared exit")
            if leg.exit_quote.data_available_at > self.exit_timestamp:
                raise ValueError("look-ahead detected in exit quote")
        return self


class BacktestDataset(StrictModel):
    ticker: str = Field(min_length=1)
    as_of: datetime
    evidence_class: Literal["illustrative_backtest", "source_backed_backtest"]
    source: EvidenceReference
    cases: list[BacktestCase] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_splits(self) -> BacktestDataset:
        splits = {case.split for case in self.cases}
        if not {"train", "test"}.issubset(splits):
            raise ValueError("backtest dataset requires train and test cases")
        if (
            self.evidence_class == "source_backed_backtest"
            and not self.source.status.can_authorize_research
        ):
            raise ValueError("source-backed backtest requires authorizing evidence")
        return self


class BacktestCaseResult(StrictModel):
    case_id: str
    split: BacktestSplit
    entry_outlay: float
    exit_value: float
    gross_pnl: float
    costs: float = Field(ge=0)
    net_pnl: float


class BacktestMetrics(StrictModel):
    split: BacktestSplit
    observations: int = Field(ge=1)
    total_pnl: float
    mean_pnl: float
    median_pnl: float
    win_rate: float = Field(ge=0, le=1)
    maximum_drawdown: float = Field(ge=0)


class BacktestReport(StrictModel):
    ticker: str
    created_at: datetime
    evidence_class: Literal["illustrative_backtest", "source_backed_backtest"]
    model_readiness: ModelReadiness
    execution_price_quality: Literal[
        "historical_nbbo", "historical_eod_bid_ask", "bar_close_proxy", "mixed"
    ]
    cases: list[BacktestCaseResult]
    train_metrics: BacktestMetrics
    test_metrics: BacktestMetrics
    holdout_metrics: BacktestMetrics | None = None
    warnings: list[str] = Field(default_factory=list)


def _case_result(case: BacktestCase) -> BacktestCaseResult:
    entry_outlay = 0.0
    exit_value = 0.0
    contract_sides = 0
    for leg in case.legs:
        contracts = leg.quantity
        contract_sides += contracts * 2
        entry_price = leg.entry_quote.ask if leg.side is PositionSide.LONG else leg.entry_quote.bid
        exit_price = leg.exit_quote.bid if leg.side is PositionSide.LONG else leg.exit_quote.ask
        scale = leg.quantity * leg.multiplier
        entry_outlay += leg.side.sign * scale * entry_price
        exit_value += leg.side.sign * scale * exit_price
    gross_pnl = exit_value - entry_outlay
    costs = contract_sides * (
        case.commission_per_contract_per_side + case.slippage_per_contract_per_side
    )
    return BacktestCaseResult(
        case_id=case.case_id,
        split=case.split,
        entry_outlay=round(entry_outlay, 6),
        exit_value=round(exit_value, 6),
        gross_pnl=round(gross_pnl, 6),
        costs=round(costs, 6),
        net_pnl=round(gross_pnl - costs, 6),
    )


def _metrics(split: BacktestSplit, results: list[BacktestCaseResult]) -> BacktestMetrics:
    pnls = [result.net_pnl for result in results]
    cumulative = 0.0
    peak = 0.0
    maximum_drawdown = 0.0
    for pnl in pnls:
        cumulative += pnl
        peak = max(peak, cumulative)
        maximum_drawdown = max(maximum_drawdown, peak - cumulative)
    return BacktestMetrics(
        split=split,
        observations=len(pnls),
        total_pnl=round(sum(pnls), 6),
        mean_pnl=round(fmean(pnls), 6),
        median_pnl=round(median(pnls), 6),
        win_rate=round(sum(pnl > 0 for pnl in pnls) / len(pnls), 6),
        maximum_drawdown=round(maximum_drawdown, 6),
    )


def run_backtest(dataset: BacktestDataset) -> BacktestReport:
    ordered = sorted(dataset.cases, key=lambda case: case.entry_timestamp)
    results = [_case_result(case) for case in ordered]
    train = [result for result in results if result.split == "train"]
    test = [result for result in results if result.split == "test"]
    holdout = [result for result in results if result.split == "holdout"]
    price_bases = {
        quote.price_basis
        for case in dataset.cases
        for leg in case.legs
        for quote in (leg.entry_quote, leg.exit_quote)
    }
    if price_bases == {"nbbo"}:
        execution_price_quality = "historical_nbbo"
    elif price_bases == {"eod_bid_ask"}:
        execution_price_quality = "historical_eod_bid_ask"
    elif price_bases == {"option_bar_close_proxy"}:
        execution_price_quality = "bar_close_proxy"
    else:
        execution_price_quality = "mixed"
    readiness = (
        ModelReadiness.VALIDATION_PENDING
        if dataset.evidence_class == "source_backed_backtest"
        and execution_price_quality == "historical_nbbo"
        else ModelReadiness.SCREEN_GRADE
    )
    warnings = [
        "Backtest results do not authorize execution or position sizing",
        "Explicit costs are used; market impact beyond configured slippage is absent",
    ]
    if dataset.evidence_class == "illustrative_backtest":
        warnings.append("Synthetic cases validate mechanics only, not strategy performance")
    if execution_price_quality != "historical_nbbo":
        if execution_price_quality == "historical_eod_bid_ask":
            warnings.append(
                "End-of-day bid/ask improves spread modeling but does not replay intraday NBBO"
            )
        else:
            warnings.append(
                "Historical option bars are transaction aggregates, not NBBO; close prices are "
                "execution proxies"
            )
    return BacktestReport(
        ticker=dataset.ticker,
        created_at=dataset.as_of,
        evidence_class=dataset.evidence_class,
        model_readiness=readiness,
        execution_price_quality=execution_price_quality,
        cases=results,
        train_metrics=_metrics("train", train),
        test_metrics=_metrics("test", test),
        holdout_metrics=_metrics("holdout", holdout) if holdout else None,
        warnings=warnings,
    )


def render_backtest_markdown(report: BacktestReport) -> str:
    lines = [
        "# TTWO options backtest",
        "",
        f"- Evidence class: `{report.evidence_class}`",
        f"- Model readiness: `{report.model_readiness.value}`",
        f"- Execution-price quality: `{report.execution_price_quality}`",
        "- Order capability: `forbidden`",
        "",
        "## Split metrics",
        "",
    ]
    for metrics in (report.train_metrics, report.test_metrics, report.holdout_metrics):
        if metrics is None:
            continue
        lines.append(
            f"- `{metrics.split}`: n={metrics.observations}, total={metrics.total_pnl:.2f}, "
            f"mean={metrics.mean_pnl:.2f}, win_rate={metrics.win_rate:.1%}, "
            f"max_drawdown={metrics.maximum_drawdown:.2f}"
        )
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    lines.append("")
    return "\n".join(lines)
