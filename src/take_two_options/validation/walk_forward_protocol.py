"""Chronological calibrate-freeze-predict-observe-score protocol."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from statistics import fmean, stdev
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash


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
        "WALK_FORWARD_EVALUATED",
        "BLOCKED_INSUFFICIENT_HISTORY",
    ]
    windows: list[WalkForwardWindowManifest]
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
