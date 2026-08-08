"""Comparable baseline metrics, paired uncertainty and multiple-testing controls."""

from __future__ import annotations

import math
import random
from enum import StrEnum
from statistics import fmean, stdev
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.research_statistics import (
    conditional_value_at_risk,
    deflated_sharpe_probability,
    downside_deviation,
)
from take_two_options.validation.pbo import probability_of_backtest_overfitting


class ComparableStrategy(StrEnum):
    CASH = "cash"
    NO_POSITION = "no_position"
    UNDERLYING = "underlying"
    BUY_AND_HOLD = "buy_and_hold"
    ATM_LONG_CALL = "atm_long_call"
    FIXED_DELTA_LONG_CALL = "fixed_delta_long_call"
    STANDARD_BULL_CALL_SPREAD = "standard_bull_call_spread"
    RANDOM_ADMISSIBLE = "random_admissible"
    ENGINE_CANDIDATE = "engine_candidate"


MANDATORY_STRATEGIES = tuple(ComparableStrategy)
ComparisonClassification = Literal[
    "statistically_and_economically_material",
    "statistically_distinguishable_not_material",
    "economically_material_not_statistically_distinguishable",
    "inconclusive",
    "worse_than_baseline",
]


class ComparisonConventions(StrictModel):
    horizon: str
    capital: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    fees: str
    spread_assumption: str
    fx_policy: str
    entry_convention: str
    exit_convention: str
    target_return: float
    large_loss_threshold: float = Field(gt=0, le=1)


class StrategyReturnSeries(StrictModel):
    strategy: ComparableStrategy
    observation_ids: list[str] = Field(min_length=4)
    gross_returns: list[float] = Field(min_length=4)
    net_returns: list[float] = Field(min_length=4)
    transaction_costs: list[float] = Field(min_length=4)

    @model_validator(mode="after")
    def require_aligned_finite_values(self) -> StrategyReturnSeries:
        lengths = {
            len(self.observation_ids),
            len(self.gross_returns),
            len(self.net_returns),
            len(self.transaction_costs),
        }
        if len(lengths) != 1:
            raise ValueError("strategy return and cost arrays must align")
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("observation IDs must be unique")
        if not all(
            math.isfinite(value)
            for value in [*self.gross_returns, *self.net_returns, *self.transaction_costs]
        ):
            raise ValueError("returns and costs must be finite")
        if any(value < 0 for value in self.transaction_costs):
            raise ValueError("transaction costs cannot be negative")
        if any(value < -1 for value in self.net_returns):
            raise ValueError("net period returns cannot be below -100%")
        return self


class BaselineMetricRow(StrictModel):
    strategy: ComparableStrategy
    role: Literal["baseline", "candidate"]
    observations: int = Field(gt=0)
    total_return: float
    expected_return: float
    cvar_95: float = Field(ge=0)
    maximum_drawdown: float = Field(ge=0)
    probability_profit: float = Field(ge=0, le=1)
    probability_target: float = Field(ge=0, le=1)
    probability_large_loss: float = Field(ge=0, le=1)
    sharpe: float | None
    sortino: float | None
    transaction_costs: float = Field(ge=0)
    status: Literal["baseline", "candidate"]


class PairedDelta(StrictModel):
    baseline: ComparableStrategy
    candidate: Literal[ComparableStrategy.ENGINE_CANDIDATE]
    observations: int = Field(gt=0)
    return_uplift: float
    expected_return_uplift: float
    cvar_improvement: float
    drawdown_improvement: float
    probability_profit_uplift: float
    probability_target_uplift: float
    probability_large_loss_improvement: float
    sharpe_uplift: float | None
    sortino_uplift: float | None
    transaction_cost_difference: float
    paired_mean_uplift_interval: tuple[float, float]
    raw_p_value: float = Field(ge=0, le=1)
    adjusted_p_value: float = Field(ge=0, le=1)
    statistically_distinguishable: bool
    economically_material: bool
    classification: ComparisonClassification


class EffectiveSearchSpace(StrictModel):
    strategies_considered: int = Field(gt=0)
    contracts_considered: int = Field(gt=0)
    expirations_considered: int = Field(gt=0)
    parameter_sets_considered: int = Field(gt=0)
    model_sets_considered: int = Field(gt=0)
    exit_rules_considered: int = Field(gt=0)
    actual_trials: int = Field(gt=0)
    cartesian_upper_bound: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_search_counts(self) -> EffectiveSearchSpace:
        expected = (
            self.strategies_considered
            * self.contracts_considered
            * self.expirations_considered
            * self.parameter_sets_considered
            * self.model_sets_considered
            * self.exit_rules_considered
        )
        if self.cartesian_upper_bound != expected:
            raise ValueError("cartesian_upper_bound must equal the declared search product")
        return self


class MultipleTestingDiagnostics(StrictModel):
    correction: Literal["holm"]
    alpha: float = Field(gt=0, lt=1)
    effective_search_space: EffectiveSearchSpace
    deflated_sharpe_probability: float | None = Field(default=None, ge=0, le=1)
    probability_backtest_overfitting: float | None = Field(default=None, ge=0, le=1)
    paired_permutation_samples: int = Field(gt=0)
    bootstrap_samples: int = Field(gt=0)
    seed: int


class BaselineComparisonReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    dataset_hash: str | None = Field(default=None, min_length=64, max_length=64)
    status: Literal[
        "EVALUATED",
        "FIXTURE_ONLY_NOT_VALIDATED",
        "DIAGNOSTIC_ONLY_LICENSE_REVIEW",
        "BLOCKED_INCOMPARABLE_DATA",
    ]
    conventions: ComparisonConventions
    rows: list[BaselineMetricRow]
    deltas: list[PairedDelta]
    missing_strategies: list[ComparableStrategy]
    regret_vs_best_simple_baseline: float | None
    multiple_testing: MultipleTestingDiagnostics | None
    blockers: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def require_complete_evaluated_table(self) -> BaselineComparisonReport:
        present = {row.strategy for row in self.rows}
        missing = [strategy for strategy in MANDATORY_STRATEGIES if strategy not in present]
        if self.missing_strategies != missing:
            raise ValueError("missing_strategies must exactly match absent rows")
        if self.status == "EVALUATED" and (missing or self.blockers):
            raise ValueError("evaluated baseline report cannot omit strategies or retain blockers")
        return self


def _maximum_drawdown(values: list[float]) -> float:
    wealth = 1.0
    peak = 1.0
    maximum = 0.0
    for value in values:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        maximum = max(maximum, 1.0 - wealth / peak) if peak > 0 else 1.0
    return maximum


def _total_return(values: list[float]) -> float:
    wealth = math.prod(1.0 + value for value in values)
    return wealth - 1.0


def _ratio(values: list[float], denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return fmean(values) / denominator


def strategy_metrics(
    series: StrategyReturnSeries,
    conventions: ComparisonConventions,
) -> BaselineMetricRow:
    values = series.net_returns
    volatility = stdev(values)
    downside = downside_deviation(values)
    candidate = series.strategy is ComparableStrategy.ENGINE_CANDIDATE
    role: Literal["baseline", "candidate"] = "candidate" if candidate else "baseline"
    return BaselineMetricRow(
        strategy=series.strategy,
        role=role,
        observations=len(values),
        total_return=_total_return(values),
        expected_return=fmean(values),
        cvar_95=conditional_value_at_risk(values),
        maximum_drawdown=_maximum_drawdown(values),
        probability_profit=sum(value > 0 for value in values) / len(values),
        probability_target=(
            sum(value >= conventions.target_return for value in values) / len(values)
        ),
        probability_large_loss=(
            sum(value <= -conventions.large_loss_threshold for value in values)
            / len(values)
        ),
        sharpe=_ratio(values, volatility),
        sortino=_ratio(values, downside),
        transaction_costs=sum(series.transaction_costs),
        status=role,
    )


def holm_adjust(p_values: list[float]) -> list[float]:
    if any(not 0 <= value <= 1 for value in p_values):
        raise ValueError("p-values must be in [0, 1]")
    count = len(p_values)
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * count
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[index] = running
    return adjusted


def _bootstrap_mean_interval(
    differences: list[float], *, samples: int, seed: int
) -> tuple[float, float]:
    generator = random.Random(seed)
    count = len(differences)
    estimates = sorted(
        fmean(differences[generator.randrange(count)] for _ in range(count))
        for _ in range(samples)
    )
    lower = estimates[math.floor(0.025 * (samples - 1))]
    upper = estimates[math.ceil(0.975 * (samples - 1))]
    return lower, upper


def _paired_permutation_p_value(
    differences: list[float], *, samples: int, seed: int
) -> float:
    generator = random.Random(seed)
    observed = abs(fmean(differences))
    exceedances = 0
    for _ in range(samples):
        permuted = fmean(
            value if generator.random() < 0.5 else -value for value in differences
        )
        exceedances += abs(permuted) >= observed
    return (exceedances + 1) / (samples + 1)


def _classification(
    uplift: float,
    *,
    statistically_distinguishable: bool,
    economically_material: bool,
) -> ComparisonClassification:
    if uplift < 0:
        return "worse_than_baseline"
    if statistically_distinguishable and economically_material:
        return "statistically_and_economically_material"
    if statistically_distinguishable:
        return "statistically_distinguishable_not_material"
    if economically_material:
        return "economically_material_not_statistically_distinguishable"
    return "inconclusive"


def compare_with_baselines(
    series: list[StrategyReturnSeries],
    *,
    ticker: str,
    dataset_hash: str,
    conventions: ComparisonConventions,
    search_space: EffectiveSearchSpace,
    alpha: float,
    minimum_material_uplift: float,
    bootstrap_samples: int = 1_000,
    permutation_samples: int = 2_000,
    seed: int = 20_260_808,
    synthetic: bool = False,
    license_status: Literal["authorized_internal", "to_review"] = "to_review",
) -> BaselineComparisonReport:
    if len({item.strategy for item in series}) != len(series):
        raise ValueError("strategy series must be unique")
    by_strategy = {item.strategy: item for item in series}
    missing = [strategy for strategy in MANDATORY_STRATEGIES if strategy not in by_strategy]
    if missing:
        return BaselineComparisonReport(
            schema_version="1.0",
            report_id=f"{ticker.casefold()}-baseline-comparison-v1",
            ticker=ticker,
            dataset_hash=dataset_hash,
            status="BLOCKED_INCOMPARABLE_DATA",
            conventions=conventions,
            rows=[strategy_metrics(item, conventions) for item in series],
            deltas=[],
            missing_strategies=missing,
            regret_vs_best_simple_baseline=None,
            multiple_testing=None,
            blockers=["All mandatory strategies require an aligned comparable return panel."],
            holdout_used=False,
        )
    reference_ids = series[0].observation_ids
    if any(item.observation_ids != reference_ids for item in series[1:]):
        raise ValueError("all strategy series must share identically ordered observation IDs")
    rows = [
        strategy_metrics(by_strategy[strategy], conventions)
        for strategy in MANDATORY_STRATEGIES
    ]
    rows_by_strategy = {row.strategy: row for row in rows}
    candidate_series = by_strategy[ComparableStrategy.ENGINE_CANDIDATE]
    candidate_row = rows_by_strategy[ComparableStrategy.ENGINE_CANDIDATE]
    baseline_strategies = [
        strategy
        for strategy in MANDATORY_STRATEGIES
        if strategy is not ComparableStrategy.ENGINE_CANDIDATE
    ]
    intervals: list[tuple[float, float]] = []
    raw_p_values: list[float] = []
    differences_by_baseline: list[list[float]] = []
    for index, strategy in enumerate(baseline_strategies):
        differences = [
            candidate - baseline
            for candidate, baseline in zip(
                candidate_series.net_returns,
                by_strategy[strategy].net_returns,
                strict=True,
            )
        ]
        differences_by_baseline.append(differences)
        intervals.append(
            _bootstrap_mean_interval(differences, samples=bootstrap_samples, seed=seed + index)
        )
        raw_p_values.append(
            _paired_permutation_p_value(
                differences,
                samples=permutation_samples,
                seed=seed + 10_000 + index,
            )
        )
    adjusted = holm_adjust(raw_p_values)
    deltas: list[PairedDelta] = []
    for index, strategy in enumerate(baseline_strategies):
        baseline = rows_by_strategy[strategy]
        mean_uplift = fmean(differences_by_baseline[index])
        interval = intervals[index]
        distinguishable = adjusted[index] <= alpha and not (interval[0] <= 0 <= interval[1])
        material = mean_uplift >= minimum_material_uplift
        deltas.append(
            PairedDelta(
                baseline=strategy,
                candidate=ComparableStrategy.ENGINE_CANDIDATE,
                observations=len(reference_ids),
                return_uplift=candidate_row.total_return - baseline.total_return,
                expected_return_uplift=mean_uplift,
                cvar_improvement=baseline.cvar_95 - candidate_row.cvar_95,
                drawdown_improvement=baseline.maximum_drawdown - candidate_row.maximum_drawdown,
                probability_profit_uplift=(
                    candidate_row.probability_profit - baseline.probability_profit
                ),
                probability_target_uplift=(
                    candidate_row.probability_target - baseline.probability_target
                ),
                probability_large_loss_improvement=(
                    baseline.probability_large_loss - candidate_row.probability_large_loss
                ),
                sharpe_uplift=(
                    candidate_row.sharpe - baseline.sharpe
                    if candidate_row.sharpe is not None and baseline.sharpe is not None
                    else None
                ),
                sortino_uplift=(
                    candidate_row.sortino - baseline.sortino
                    if candidate_row.sortino is not None and baseline.sortino is not None
                    else None
                ),
                transaction_cost_difference=(
                    candidate_row.transaction_costs - baseline.transaction_costs
                ),
                paired_mean_uplift_interval=interval,
                raw_p_value=raw_p_values[index],
                adjusted_p_value=adjusted[index],
                statistically_distinguishable=distinguishable,
                economically_material=material,
                classification=_classification(
                    mean_uplift,
                    statistically_distinguishable=distinguishable,
                    economically_material=material,
                ),
            )
        )
    simple = [
        row.total_return
        for row in rows
        if row.strategy is not ComparableStrategy.ENGINE_CANDIDATE
    ]
    fold_matrix = [by_strategy[strategy].net_returns for strategy in MANDATORY_STRATEGIES]
    multiple_testing = MultipleTestingDiagnostics(
        correction="holm",
        alpha=alpha,
        effective_search_space=search_space,
        deflated_sharpe_probability=deflated_sharpe_probability(
            candidate_series.net_returns, search_space.actual_trials
        ),
        probability_backtest_overfitting=probability_of_backtest_overfitting(fold_matrix),
        paired_permutation_samples=permutation_samples,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    if synthetic:
        status = "FIXTURE_ONLY_NOT_VALIDATED"
        blockers = ["Synthetic inputs validate comparison mechanics only."]
    elif license_status == "to_review":
        status = "DIAGNOSTIC_ONLY_LICENSE_REVIEW"
        blockers = ["Historical return panel licensing remains to_review."]
    else:
        status = "EVALUATED"
        blockers = []
    return BaselineComparisonReport(
        schema_version="1.0",
        report_id=f"{ticker.casefold()}-baseline-comparison-v1",
        ticker=ticker,
        dataset_hash=dataset_hash,
        status=status,
        conventions=conventions,
        rows=rows,
        deltas=deltas,
        missing_strategies=[],
        regret_vs_best_simple_baseline=max(simple) - candidate_row.total_return,
        multiple_testing=multiple_testing,
        blockers=blockers,
        holdout_used=False,
    )
