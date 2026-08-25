"""Chronological calibrate-freeze-predict-observe-score protocol."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime
from statistics import fmean, stdev
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.validation.baseline_comparison import (
    MANDATORY_STRATEGIES,
    BaselineComparisonReport,
    ComparableStrategy,
    ComparisonConventions,
    EffectiveSearchSpace,
    StrategyReturnSeries,
    compare_with_baselines,
)
from take_two_options.validation.comparable_panel import (
    ComparablePanelDataset,
    ComparablePanelObservation,
    PanelOutcome,
)


class ChronologicalReturn(StrictModel):
    observation_id: str
    timestamp: datetime
    available_at: datetime
    log_return: float

    @field_validator("timestamp", "available_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("walk-forward timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_availability(self) -> ChronologicalReturn:
        if self.available_at < self.timestamp:
            raise ValueError("return availability cannot precede its timestamp")
        if not math.isfinite(self.log_return):
            raise ValueError("return must be finite")
        return self


class WalkForwardProtocolConfig(StrictModel):
    protocol_id: str
    method: Literal["rolling", "expanding"]
    minimum_train_observations: int = Field(gt=1)
    rolling_train_observations: int | None = Field(default=None, gt=1)
    validation_observations: int = Field(gt=0)
    test_observations: int = Field(gt=0)
    step_observations: int = Field(gt=0)
    purge_observations: int = Field(ge=0)
    embargo_observations: int = Field(ge=0)
    model_id: Literal["historical_gaussian_reference"]
    probability_floor: float = Field(gt=0, lt=0.5)

    @model_validator(mode="after")
    def validate_rolling_size(self) -> WalkForwardProtocolConfig:
        if self.method == "rolling" and self.rolling_train_observations is None:
            raise ValueError("rolling method requires rolling_train_observations")
        return self


class PredictionSummary(StrictModel):
    observations: int = Field(gt=0)
    mean_predicted_probability_profit: float = Field(ge=0, le=1)
    realized_probability_profit: float = Field(ge=0, le=1)
    mean_realized_log_return: float
    brier_score: float = Field(ge=0)
    log_loss: float = Field(ge=0)


class WalkForwardWindowManifest(StrictModel):
    window_id: str
    method: Literal["rolling", "expanding"]
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    test_start: datetime
    test_end: datetime
    calibrated_through: datetime
    dataset_hash: str = Field(min_length=64, max_length=64)
    configuration_hash: str = Field(min_length=64, max_length=64)
    model_id: str
    model_parameters: dict[str, float]
    frozen_model_hash: str = Field(min_length=64, max_length=64)
    train_observations: int = Field(gt=0)
    purged_observation_ids: list[str]
    embargoed_observation_ids: list[str]
    validation_summary: PredictionSummary
    test_summary: PredictionSummary
    private_prediction_records_hash: str = Field(min_length=64, max_length=64)
    prediction_record_disclosure: Literal["aggregate_only_license_restricted"]
    recalibrated_after_test: Literal[False]

    @model_validator(mode="after")
    def validate_chronology(self) -> WalkForwardWindowManifest:
        if not (
            self.train_start
            <= self.train_end
            < self.validation_start
            <= self.validation_end
            < self.test_start
            <= self.test_end
        ):
            raise ValueError("walk-forward intervals must be strictly chronological")
        if self.calibrated_through >= self.validation_start:
            raise ValueError("model must be frozen before validation starts")
        return self


class StrategyWalkForwardWindow(StrictModel):
    window_id: str
    train_start: date
    train_end: date
    validation_date: date
    test_date: date
    train_observations: int = Field(gt=0)
    purged_observation_ids: list[str]
    embargoed_observation_ids: list[str]
    selected_training_leader: ComparableStrategy
    frozen_policy_hash: str = Field(min_length=64, max_length=64)
    private_test_record_hash: str = Field(min_length=64, max_length=64)
    recalibrated_after_test: Literal[False] = False

    @model_validator(mode="after")
    def require_strict_order(self) -> StrategyWalkForwardWindow:
        if not self.train_start <= self.train_end < self.validation_date < self.test_date:
            raise ValueError("strategy walk-forward dates must be strictly chronological")
        return self


class StrategySampleAdequacy(StrictModel):
    available_observations: int = Field(gt=0)
    diagnostic_train_observations: int = Field(gt=0)
    diagnostic_validation_observations: int = Field(gt=0)
    diagnostic_test_observations: int = Field(gt=0)
    diagnostic_purge_observations: int = Field(ge=0)
    diagnostic_embargo_observations: int = Field(ge=0)
    formal_minimum_train_observations: int = Field(gt=0)
    formal_minimum_validation_observations: int = Field(gt=0)
    formal_minimum_test_observations: int = Field(gt=0)
    formal_embargo_observations: int = Field(ge=0)
    formal_policy_satisfied: bool


class WalkForwardProtocolReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    generated_at: datetime
    dataset_hash: str = Field(min_length=64, max_length=64)
    configuration_hash: str = Field(min_length=64, max_length=64)
    method: Literal["rolling", "expanding"]
    status: Literal[
        "DIAGNOSTIC_ONLY_LICENSE_REVIEW",
        "DEVELOPMENT_ONLY_INSUFFICIENT_FINAL_SAMPLE",
        "WALK_FORWARD_EVALUATED",
        "BLOCKED_INSUFFICIENT_HISTORY",
    ]
    windows: list[WalkForwardWindowManifest]
    strategy_windows: list[StrategyWalkForwardWindow] = Field(default_factory=list)
    oos_strategy_comparison: BaselineComparisonReport | None = None
    sample_adequacy: StrategySampleAdequacy | None = None
    holdout_touched: Literal[False]
    license_status: Literal["authorized_internal", "to_review"]
    blockers: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def _normal_probability_positive(mean: float, sigma: float) -> float:
    if sigma <= 0:
        return float(mean > 0)
    return 0.5 * (1.0 + math.erf(mean / (sigma * math.sqrt(2.0))))


def _summarize_predictions(
    observations: list[ChronologicalReturn],
    *,
    probability: float,
) -> tuple[PredictionSummary, list[dict[str, object]]]:
    outcomes = [float(item.log_return > 0) for item in observations]
    epsilon = 1e-12
    records = [
        {
            "observation_id": item.observation_id,
            "timestamp": item.timestamp,
            "available_at": item.available_at,
            "predicted_probability_profit": probability,
            "realized_log_return": item.log_return,
        }
        for item in observations
    ]
    return (
        PredictionSummary(
            observations=len(observations),
            mean_predicted_probability_profit=probability,
            realized_probability_profit=fmean(outcomes),
            mean_realized_log_return=fmean(item.log_return for item in observations),
            brier_score=fmean((probability - outcome) ** 2 for outcome in outcomes),
            log_loss=-fmean(
                outcome * math.log(max(probability, epsilon))
                + (1 - outcome) * math.log(max(1 - probability, epsilon))
                for outcome in outcomes
            ),
        ),
        records,
    )


def run_walk_forward_protocol(
    observations: list[ChronologicalReturn],
    *,
    ticker: str,
    dataset_hash: str,
    config: WalkForwardProtocolConfig,
    generated_at: datetime,
    license_status: Literal["authorized_internal", "to_review"],
) -> WalkForwardProtocolReport:
    ordered = sorted(observations, key=lambda item: (item.timestamp, item.observation_id))
    configuration_hash = stable_hash(config.model_dump(mode="json"))
    required = (
        config.minimum_train_observations
        + config.purge_observations
        + config.validation_observations
        + config.embargo_observations
        + config.test_observations
    )
    if len(ordered) < required:
        return WalkForwardProtocolReport(
            schema_version="1.0",
            report_id=f"{ticker.casefold()}-walk-forward-{config.method}-v1",
            ticker=ticker,
            generated_at=generated_at,
            dataset_hash=dataset_hash,
            configuration_hash=configuration_hash,
            method=config.method,
            status="BLOCKED_INSUFFICIENT_HISTORY",
            windows=[],
            holdout_touched=False,
            license_status=license_status,
            blockers=[f"Need at least {required} returns; found {len(ordered)}."],
        )
    windows: list[WalkForwardWindowManifest] = []
    cursor = config.minimum_train_observations + config.purge_observations
    window_number = 1
    while (
        cursor
        + config.validation_observations
        + config.embargo_observations
        + config.test_observations
        <= len(ordered)
    ):
        raw_train = ordered[:cursor]
        if config.method == "rolling":
            assert config.rolling_train_observations is not None
            rolling_raw_size = (
                config.rolling_train_observations + config.purge_observations
            )
            raw_train = raw_train[-rolling_raw_size:]
        purge_count = min(config.purge_observations, len(raw_train) - 2)
        purged = raw_train[-purge_count:] if purge_count else []
        train = raw_train[:-purge_count] if purge_count else raw_train
        validation_start_index = cursor
        validation_end_index = cursor + config.validation_observations
        validation = ordered[validation_start_index:validation_end_index]
        embargo_end_index = validation_end_index + config.embargo_observations
        embargo = ordered[validation_end_index:embargo_end_index]
        test_end_index = embargo_end_index + config.test_observations
        test = ordered[embargo_end_index:test_end_index]
        calibrated_through = max(item.available_at for item in train)
        if calibrated_through >= validation[0].timestamp:
            raise ValueError("training information was not available before validation")
        values = [item.log_return for item in train]
        mean = fmean(values)
        sigma = stdev(values)
        probability = min(
            1.0 - config.probability_floor,
            max(config.probability_floor, _normal_probability_positive(mean, sigma)),
        )
        parameters = {"mean": mean, "standard_deviation": sigma}
        frozen_hash = stable_hash(
            {
                "model_id": config.model_id,
                "parameters": parameters,
                "calibrated_through": calibrated_through,
            }
        )
        validation_summary, validation_records = _summarize_predictions(
            validation, probability=probability
        )
        test_summary, test_records = _summarize_predictions(test, probability=probability)
        windows.append(
            WalkForwardWindowManifest(
                window_id=f"wf-{config.method}-{window_number:03d}",
                method=config.method,
                train_start=train[0].timestamp,
                train_end=train[-1].timestamp,
                validation_start=validation[0].timestamp,
                validation_end=validation[-1].timestamp,
                test_start=test[0].timestamp,
                test_end=test[-1].timestamp,
                calibrated_through=calibrated_through,
                dataset_hash=dataset_hash,
                configuration_hash=configuration_hash,
                model_id=config.model_id,
                model_parameters=parameters,
                frozen_model_hash=frozen_hash,
                train_observations=len(train),
                purged_observation_ids=[item.observation_id for item in purged],
                embargoed_observation_ids=[item.observation_id for item in embargo],
                validation_summary=validation_summary,
                test_summary=test_summary,
                private_prediction_records_hash=stable_hash(
                    [*validation_records, *test_records]
                ),
                prediction_record_disclosure="aggregate_only_license_restricted",
                recalibrated_after_test=False,
            )
        )
        window_number += 1
        cursor += config.step_observations
    blockers = [
        "Reference model validates chronology only; candidate models remain to compare.",
        "Final holdout is not touched by this protocol.",
        "Prediction records stay private because the realized series is license-restricted.",
    ]
    if license_status == "to_review":
        blockers.insert(0, "Account-specific historical-data rights remain to review.")
    return WalkForwardProtocolReport(
        schema_version="1.0",
        report_id=f"{ticker.casefold()}-walk-forward-{config.method}-v1",
        ticker=ticker,
        generated_at=generated_at,
        dataset_hash=dataset_hash,
        configuration_hash=configuration_hash,
        method=config.method,
        status=(
            "DIAGNOSTIC_ONLY_LICENSE_REVIEW"
            if license_status == "to_review"
            else "WALK_FORWARD_EVALUATED"
        ),
        windows=windows,
        holdout_touched=False,
        license_status=license_status,
        blockers=blockers,
    )


def _outcome_map(
    observation: ComparablePanelObservation,
) -> dict[ComparableStrategy, PanelOutcome]:
    return {outcome.strategy: outcome for outcome in observation.outcomes}


def run_strategy_walk_forward(
    panel: ComparablePanelDataset,
    *,
    generated_at: datetime,
    minimum_train_observations: int = 12,
    validation_observations: int = 1,
    test_observations: int = 1,
    purge_observations: int = 1,
    embargo_observations: int = 1,
    step_observations: int = 1,
    formal_minimum_train: int = 20,
    formal_minimum_validation: int = 8,
    formal_minimum_test: int = 8,
    formal_embargo: int = 5,
    seed: int = 20_260_808,
) -> WalkForwardProtocolReport:
    """Evaluate all frozen panel strategies on future observations without opening holdout."""

    ordered = sorted(panel.observations, key=lambda item: item.signal_date)
    required = (
        minimum_train_observations
        + purge_observations
        + validation_observations
        + embargo_observations
        + test_observations
    )
    config_payload = {
        "method": "expanding",
        "minimum_train_observations": minimum_train_observations,
        "validation_observations": validation_observations,
        "test_observations": test_observations,
        "purge_observations": purge_observations,
        "embargo_observations": embargo_observations,
        "step_observations": step_observations,
        "seed": seed,
        "frozen_rules": panel.frozen_rules,
    }
    configuration_hash = stable_hash(config_payload)
    if len(ordered) < required:
        return WalkForwardProtocolReport(
            schema_version="1.0",
            report_id="ttwo-strategy-walk-forward-v2",
            ticker=panel.ticker,
            generated_at=generated_at,
            dataset_hash=panel.dataset_hash,
            configuration_hash=configuration_hash,
            method="expanding",
            status="BLOCKED_INSUFFICIENT_HISTORY",
            windows=[],
            strategy_windows=[],
            oos_strategy_comparison=None,
            sample_adequacy=None,
            holdout_touched=False,
            license_status="to_review",
            blockers=[f"Need at least {required} strategy observations; found {len(ordered)}."],
        )

    windows: list[StrategyWalkForwardWindow] = []
    oos_observations: list[ComparablePanelObservation] = []
    cursor = minimum_train_observations + purge_observations
    window_number = 1
    while (
        cursor + validation_observations + embargo_observations + test_observations
        <= len(ordered)
    ):
        raw_train = ordered[:cursor]
        purged = raw_train[-purge_observations:] if purge_observations else []
        train = raw_train[:-purge_observations] if purge_observations else raw_train
        validation_end = cursor + validation_observations
        validation = ordered[cursor:validation_end]
        embargo_end = validation_end + embargo_observations
        embargo = ordered[validation_end:embargo_end]
        test_end = embargo_end + test_observations
        test = ordered[embargo_end:test_end]
        train_means = {
            strategy: fmean(
                float(_outcome_map(observation)[strategy].net_return)
                for observation in train
            )
            for strategy in MANDATORY_STRATEGIES
        }
        leader = max(MANDATORY_STRATEGIES, key=lambda strategy: train_means[strategy])
        frozen_hash = stable_hash(
            {
                "panel_rules": panel.frozen_rules,
                "training_leader": leader,
                "calibrated_through": train[-1].decision_cutoff,
                "validation_ids": [item.observation_id for item in validation],
            }
        )
        windows.append(
            StrategyWalkForwardWindow(
                window_id=f"strategy-wf-{window_number:03d}",
                train_start=train[0].signal_date,
                train_end=train[-1].signal_date,
                validation_date=validation[0].signal_date,
                test_date=test[0].signal_date,
                train_observations=len(train),
                purged_observation_ids=[item.observation_id for item in purged],
                embargoed_observation_ids=[item.observation_id for item in embargo],
                selected_training_leader=leader,
                frozen_policy_hash=frozen_hash,
                private_test_record_hash=stable_hash(
                    [item.model_dump(mode="json") for item in test]
                ),
                recalibrated_after_test=False,
            )
        )
        oos_observations.extend(test)
        cursor += step_observations
        window_number += 1

    if len({item.observation_id for item in oos_observations}) != len(oos_observations):
        raise ValueError("strategy walk-forward test observations must not overlap")
    series = []
    for strategy in MANDATORY_STRATEGIES:
        outcomes = [_outcome_map(item)[strategy] for item in oos_observations]
        series.append(
            StrategyReturnSeries(
                strategy=strategy,
                observation_ids=[item.observation_id for item in oos_observations],
                gross_returns=[float(outcome.gross_return) for outcome in outcomes],
                net_returns=[float(outcome.net_return) for outcome in outcomes],
                transaction_costs=[
                    float(outcome.transaction_cost_eur) for outcome in outcomes
                ],
            )
        )
    comparison = compare_with_baselines(
        series,
        ticker=panel.ticker,
        dataset_hash=panel.dataset_hash,
        conventions=ComparisonConventions(
            horizon="one signal-to-entry-to-exit chain interval",
            capital=1000.0,
            currency="EUR",
            fees="same frozen per-contract round-trip fees as comparable panel",
            spread_assumption="long ask/exit bid; short bid/exit ask",
            fx_policy="point-in-time ECB EUR/USD reference rate",
            entry_convention="next full-chain date after signal",
            exit_convention="following full-chain date",
            target_return=0.90,
            large_loss_threshold=0.70,
        ),
        search_space=EffectiveSearchSpace(
            strategies_considered=len(MANDATORY_STRATEGIES),
            contracts_considered=1,
            expirations_considered=1,
            parameter_sets_considered=1,
            model_sets_considered=1,
            exit_rules_considered=1,
            actual_trials=len(MANDATORY_STRATEGIES),
            cartesian_upper_bound=len(MANDATORY_STRATEGIES),
        ),
        alpha=0.05,
        minimum_material_uplift=0.02,
        bootstrap_samples=2_000,
        permutation_samples=4_000,
        seed=seed,
        synthetic=False,
        license_status="to_review",
    ).model_copy(update={"report_id": "ttwo-walk-forward-oos-comparison-v2"})
    formal_required = (
        formal_minimum_train
        + formal_minimum_validation
        + formal_embargo
        + formal_minimum_test
    )
    adequacy = StrategySampleAdequacy(
        available_observations=len(ordered),
        diagnostic_train_observations=minimum_train_observations,
        diagnostic_validation_observations=validation_observations,
        diagnostic_test_observations=len(oos_observations),
        diagnostic_purge_observations=purge_observations,
        diagnostic_embargo_observations=embargo_observations,
        formal_minimum_train_observations=formal_minimum_train,
        formal_minimum_validation_observations=formal_minimum_validation,
        formal_minimum_test_observations=formal_minimum_test,
        formal_embargo_observations=formal_embargo,
        formal_policy_satisfied=len(ordered) >= formal_required,
    )
    return WalkForwardProtocolReport(
        schema_version="1.0",
        report_id="ttwo-strategy-walk-forward-v2",
        ticker=panel.ticker,
        generated_at=generated_at,
        dataset_hash=panel.dataset_hash,
        configuration_hash=configuration_hash,
        method="expanding",
        status="DEVELOPMENT_ONLY_INSUFFICIENT_FINAL_SAMPLE",
        windows=[],
        strategy_windows=windows,
        oos_strategy_comparison=comparison,
        sample_adequacy=adequacy,
        holdout_touched=False,
        license_status="to_review",
        blockers=[
            "Only 25 aligned option observations exist; the formal 20/8/5/8 policy needs 41.",
            "Ten non-overlapping future test observations are development diagnostics only.",
            "Historical option-data rights remain to_review.",
            "The final holdout ledger remains UNOPENED and was not read by this protocol.",
        ],
    )
