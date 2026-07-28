"""Point-in-time walk-forward evaluation with explicit baselines and no-trade."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean, median
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel

BaselineName = Literal[
    "cash",
    "underlying",
    "long_call_atm",
    "long_call_fixed_delta",
    "bull_call_spread_standard",
    "random_admissible",
    "oracle_hindsight",
    "model_candidate",
    "NO_TRADE",
]
EvaluationSplit = Literal["train", "validation", "test", "holdout"]


class WalkForwardCase(StrictModel):
    case_id: str
    window_id: str
    split: EvaluationSplit
    strategy: BaselineName
    decision_time: datetime
    entry_time: datetime
    exit_time: datetime
    calibrated_through: datetime
    data_available_at: datetime
    contract_first_seen_at: datetime | None = None
    expiration: datetime | None = None
    strike: float | None = Field(default=None, gt=0)
    available_expirations: list[datetime] = Field(default_factory=list)
    available_strikes: list[float] = Field(default_factory=list)
    entry_bid: float = Field(ge=0)
    entry_ask: float = Field(ge=0)
    exit_bid: float = Field(ge=0)
    exit_ask: float = Field(ge=0)
    side: Literal["long", "short", "cash"] = "long"
    quantity: int = Field(default=1, ge=0)
    multiplier: float = Field(default=100, gt=0)
    commission_usd: float = Field(default=0, ge=0)
    slippage_usd: float = Field(default=0, ge=0)
    predicted_probability_profit: float | None = Field(default=None, ge=0, le=1)
    rejected_for_insufficient_data: bool = False
    oracle_non_exploitable: bool = False

    @field_validator(
        "decision_time",
        "entry_time",
        "exit_time",
        "calibrated_through",
        "data_available_at",
        "contract_first_seen_at",
        "expiration",
    )
    @classmethod
    def normalize_time(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("walk-forward timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_point_in_time(self) -> WalkForwardCase:
        if not self.decision_time <= self.entry_time < self.exit_time:
            raise ValueError("decision <= entry < exit is required")
        if self.calibrated_through >= self.decision_time:
            raise ValueError("calibration must end before the decision timestamp")
        if self.data_available_at > self.decision_time:
            raise ValueError("look-ahead: case data was unavailable at decision time")
        if self.entry_ask < self.entry_bid or self.exit_ask < self.exit_bid:
            raise ValueError("walk-forward bid/ask cannot be crossed")
        if (
            self.contract_first_seen_at is not None
            and self.contract_first_seen_at > self.decision_time
        ):
            raise ValueError("selected contract did not exist at decision time")
        if self.expiration is not None:
            if self.expiration not in self.available_expirations:
                raise ValueError("selected expiration was unavailable at decision time")
            if self.strike not in self.available_strikes:
                raise ValueError("selected strike was unavailable at decision time")
        if self.strategy == "oracle_hindsight" and not self.oracle_non_exploitable:
            raise ValueError("hindsight oracle must be marked non-exploitable")
        if self.split == "holdout" and self.strategy == "oracle_hindsight":
            raise ValueError("oracle results cannot participate in final holdout gates")
        return self


class WalkForwardDataset(StrictModel):
    dataset_id: str
    created_at: datetime
    cutoff: datetime
    synthetic: bool
    window_method: Literal["rolling", "expanding"]
    embargo_days: int = Field(default=5, ge=0)
    holdout_locked: bool = True
    cases: list[WalkForwardCase]


class WalkForwardCaseResult(StrictModel):
    case_id: str
    window_id: str
    split: EvaluationSplit
    strategy: BaselineName
    pnl_usd: float
    return_fraction: float
    costs_usd: float = Field(ge=0)
    profitable: bool
    total_loss: bool
    rejected_for_insufficient_data: bool


class WalkForwardMetrics(StrictModel):
    split: EvaluationSplit
    strategy: BaselineName
    observations: int = Field(ge=0)
    mean_return: float | None = None
    median_return: float | None = None
    probability_profit: float | None = Field(default=None, ge=0, le=1)
    total_loss_rate: float | None = Field(default=None, ge=0, le=1)
    maximum_drawdown_usd: float | None = Field(default=None, ge=0)
    var_95_usd: float | None = Field(default=None, ge=0)
    cvar_95_usd: float | None = Field(default=None, ge=0)
    brier_score: float | None = Field(default=None, ge=0)
    log_loss: float | None = Field(default=None, ge=0)
    expected_calibration_error: float | None = Field(default=None, ge=0, le=1)
    turnover: float = Field(ge=0)
    execution_costs_usd: float = Field(ge=0)
    no_trade_rate: float = Field(ge=0, le=1)
    insufficient_data_rejection_rate: float = Field(ge=0, le=1)


class WalkForwardReport(StrictModel):
    status: Literal[
        "WALK_FORWARD_EVALUATED",
        "BLOCKED_MISSING_CALIBRATION_DATA",
        "BLOCKED_INVALID_BACKTEST_DATA",
        "FIXTURE_ONLY_NOT_VALIDATED",
    ]
    dataset_id: str | None = None
    results: list[WalkForwardCaseResult] = Field(default_factory=list)
    metrics: list[WalkForwardMetrics] = Field(default_factory=list)
    baselines_present: list[BaselineName] = Field(default_factory=list)
    missing_baselines: list[BaselineName] = Field(default_factory=list)
    ranking_stability: float | None = Field(default=None, ge=0, le=1)
    regret_vs_best_exploitable_baseline_usd: float | None = None
    final_holdout_used_for_tuning: Literal[False] = False
    warnings: list[str] = Field(default_factory=list)
    order_capability: Literal["forbidden"] = "forbidden"


def load_walk_forward_dataset(path: Path) -> WalkForwardDataset:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("walk-forward dataset must be one JSON object")
    return WalkForwardDataset.model_validate(payload)


def _execute(case: WalkForwardCase) -> WalkForwardCaseResult:
    if case.strategy in {"cash", "NO_TRADE"} or case.quantity == 0:
        entry_outlay = 0.0
        exit_value = 0.0
    else:
        scale = case.quantity * case.multiplier
        if case.side == "long":
            entry_outlay = case.entry_ask * scale
            exit_value = case.exit_bid * scale
        elif case.side == "short":
            entry_outlay = -case.entry_bid * scale
            exit_value = -case.exit_ask * scale
        else:
            entry_outlay = 0.0
            exit_value = 0.0
    costs = case.commission_usd + case.slippage_usd
    pnl = exit_value - entry_outlay - costs
    risk_capital = max(abs(entry_outlay) + costs, 1.0)
    return WalkForwardCaseResult(
        case_id=case.case_id,
        window_id=case.window_id,
        split=case.split,
        strategy=case.strategy,
        pnl_usd=pnl,
        return_fraction=pnl / risk_capital,
        costs_usd=costs,
        profitable=pnl > 0,
        total_loss=pnl <= -0.95 * risk_capital,
        rejected_for_insufficient_data=case.rejected_for_insufficient_data,
    )


def _ece(probabilities: list[float], outcomes: list[float], bins: int = 10) -> float:
    if not probabilities:
        return 0.0
    total = len(probabilities)
    value = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            position
            for position, probability in enumerate(probabilities)
            if lower <= probability < upper or (index == bins - 1 and probability == 1)
        ]
        if not members:
            continue
        confidence = fmean(probabilities[position] for position in members)
        frequency = fmean(outcomes[position] for position in members)
        value += len(members) / total * abs(confidence - frequency)
    return value


def _metrics(
    split: EvaluationSplit,
    strategy: BaselineName,
    cases: list[WalkForwardCase],
    results: list[WalkForwardCaseResult],
) -> WalkForwardMetrics:
    if not results:
        return WalkForwardMetrics(
            split=split,
            strategy=strategy,
            observations=0,
            turnover=0,
            execution_costs_usd=0,
            no_trade_rate=0,
            insufficient_data_rejection_rate=0,
        )
    pnls = [result.pnl_usd for result in results]
    returns = [result.return_fraction for result in results]
    cumulative = 0.0
    peak = 0.0
    maximum_drawdown = 0.0
    for pnl in pnls:
        cumulative += pnl
        peak = max(peak, cumulative)
        maximum_drawdown = max(maximum_drawdown, peak - cumulative)
    sorted_pnls = sorted(pnls)
    quantile_index = max(math.ceil(0.05 * len(sorted_pnls)) - 1, 0)
    quantile = sorted_pnls[quantile_index]
    tail = [pnl for pnl in pnls if pnl <= quantile]
    probability_pairs = [
        (case.predicted_probability_profit, float(result.profitable))
        for case, result in zip(cases, results, strict=True)
        if case.predicted_probability_profit is not None
    ]
    probabilities = [float(item[0]) for item in probability_pairs]
    outcomes = [item[1] for item in probability_pairs]
    epsilon = 1e-12
    return WalkForwardMetrics(
        split=split,
        strategy=strategy,
        observations=len(results),
        mean_return=fmean(returns),
        median_return=median(returns),
        probability_profit=sum(result.profitable for result in results) / len(results),
        total_loss_rate=sum(result.total_loss for result in results) / len(results),
        maximum_drawdown_usd=maximum_drawdown,
        var_95_usd=max(0.0, -quantile),
        cvar_95_usd=max(0.0, -fmean(tail)),
        brier_score=(
            fmean((probability - outcome) ** 2 for probability, outcome in probability_pairs)
            if probability_pairs
            else None
        ),
        log_loss=(
            -fmean(
                outcome * math.log(max(probability, epsilon))
                + (1 - outcome) * math.log(max(1 - probability, epsilon))
                for probability, outcome in probability_pairs
            )
            if probability_pairs
            else None
        ),
        expected_calibration_error=(
            _ece(probabilities, outcomes) if probability_pairs else None
        ),
        turnover=sum(case.quantity > 0 for case in cases) / len(cases),
        execution_costs_usd=sum(result.costs_usd for result in results),
        no_trade_rate=sum(case.strategy in {"cash", "NO_TRADE"} for case in cases) / len(cases),
        insufficient_data_rejection_rate=(
            sum(result.rejected_for_insufficient_data for result in results)
            / len(results)
        ),
    )


def run_walk_forward(dataset: WalkForwardDataset | None) -> WalkForwardReport:
    if dataset is None:
        return WalkForwardReport(
            status="BLOCKED_MISSING_CALIBRATION_DATA",
            missing_baselines=[
                "cash",
                "underlying",
                "long_call_atm",
                "long_call_fixed_delta",
                "bull_call_spread_standard",
                "random_admissible",
                "oracle_hindsight",
            ],
            warnings=[
                "No historical walk-forward dataset supplied; fixtures were not substituted."
            ],
        )
    results = [_execute(case) for case in sorted(dataset.cases, key=lambda item: item.entry_time)]
    grouped_cases: dict[
        tuple[EvaluationSplit, BaselineName], list[WalkForwardCase]
    ] = defaultdict(list)
    grouped_results: dict[
        tuple[EvaluationSplit, BaselineName], list[WalkForwardCaseResult]
    ] = defaultdict(list)
    for case, result in zip(
        sorted(dataset.cases, key=lambda item: item.entry_time),
        results,
        strict=True,
    ):
        grouped_cases[(case.split, case.strategy)].append(case)
        grouped_results[(case.split, case.strategy)].append(result)
    metric_rows = [
        _metrics(split, strategy, grouped_cases[(split, strategy)], rows)
        for (split, strategy), rows in sorted(
            grouped_results.items(),
            key=lambda item: (item[0][0], item[0][1]),
        )
    ]
    required_baselines: list[BaselineName] = [
        "cash",
        "underlying",
        "long_call_atm",
        "long_call_fixed_delta",
        "bull_call_spread_standard",
        "random_admissible",
        "oracle_hindsight",
    ]
    present = sorted({case.strategy for case in dataset.cases})
    missing = [baseline for baseline in required_baselines if baseline not in present]
    ranks_by_window: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for result in results:
        if result.split != "holdout" and result.strategy != "oracle_hindsight":
            ranks_by_window[result.window_id].append((result.strategy, result.pnl_usd))
    top_strategies = [
        max(rows, key=lambda item: item[1])[0]
        for rows in ranks_by_window.values()
        if rows
    ]
    ranking_stability = (
        max(top_strategies.count(name) for name in set(top_strategies))
        / len(top_strategies)
        if top_strategies
        else None
    )
    test_or_holdout = [
        result
        for result in results
        if result.split in {"test", "holdout"}
        and result.strategy != "oracle_hindsight"
    ]
    candidate_total = sum(
        result.pnl_usd for result in test_or_holdout if result.strategy == "model_candidate"
    )
    baseline_totals: dict[str, float] = defaultdict(float)
    for result in test_or_holdout:
        if result.strategy != "model_candidate":
            baseline_totals[result.strategy] += result.pnl_usd
    regret = (
        max(baseline_totals.values()) - candidate_total
        if baseline_totals
        else None
    )
    return WalkForwardReport(
        status=(
            "FIXTURE_ONLY_NOT_VALIDATED"
            if dataset.synthetic
            else "WALK_FORWARD_EVALUATED"
        ),
        dataset_id=dataset.dataset_id,
        results=results,
        metrics=metric_rows,
        baselines_present=present,
        missing_baselines=missing,
        ranking_stability=ranking_stability,
        regret_vs_best_exploitable_baseline_usd=regret,
        warnings=[
            "Parameters must never be selected on the final holdout.",
            "Oracle hindsight is diagnostic and excluded from exploitable gates.",
            *(
                ["Synthetic walk-forward cases validate mechanics only."]
                if dataset.synthetic
                else []
            ),
            *(
                ["Some required baselines are absent: " + ", ".join(missing)]
                if missing
                else []
            ),
        ],
    )
