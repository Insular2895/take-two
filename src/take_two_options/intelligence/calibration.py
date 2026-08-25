"""Offline historical-dataset contracts and fail-closed calibration workflow."""

from __future__ import annotations

import csv
import importlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Literal, cast

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.quantitative.contracts import DEFAULT_QUANT_CONVENTIONS

HistoricalRecordType = Literal[
    "underlying",
    "risk_free_rate",
    "dividend",
    "realized_volatility",
    "option_chain",
    "event",
    "market_factor",
    "trade",
]


class HistoricalRecord(StrictModel):
    record_type: HistoricalRecordType
    timestamp: datetime
    available_at: datetime
    series: str = Field(min_length=1)
    value: float | int | str | bool
    unit: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    symbol: str | None = None
    expiration: datetime | None = None
    strike: float | None = Field(default=None, gt=0)
    option_type: Literal["call", "put"] | None = None
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    split_adjustment: float | None = Field(default=None, gt=0)
    dividend_adjustment: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", "available_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("historical timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_quote(self) -> HistoricalRecord:
        if self.bid is not None and self.ask is not None and self.ask < self.bid:
            raise ValueError("historical option ask cannot be below bid")
        if self.record_type == "option_chain" and (
            self.symbol is None
            or self.expiration is None
            or self.strike is None
            or self.option_type is None
        ):
            raise ValueError("option-chain records require contract identity")
        return self


class HistoricalDataset(StrictModel):
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    created_at: datetime
    cutoff: datetime
    timezone: str
    provider: str
    license_or_usage_notes: str
    synthetic: bool
    split_adjustment_policy: str
    dividend_adjustment_policy: str
    records: list[HistoricalRecord]

    @field_validator("created_at", "cutoff")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("dataset timestamps must be timezone-aware")
        return value.astimezone(UTC)


class DatasetQualityReport(StrictModel):
    status: Literal[
        "READY_FOR_OFFLINE_CALIBRATION",
        "BLOCKED_MISSING_CALIBRATION_DATA",
        "BLOCKED_INVALID_CALIBRATION_DATA",
        "FIXTURE_ONLY_NOT_CALIBRATED",
    ]
    dataset_id: str | None = None
    dataset_version: str | None = None
    dataset_hash: str | None = None
    format: Literal["json", "csv", "parquet", "missing", "unsupported"]
    cutoff: datetime | None = None
    total_records: int = Field(ge=0)
    accepted_records: int = Field(ge=0)
    excluded_post_cutoff: int = Field(ge=0)
    excluded_lookahead: int = Field(ge=0)
    duplicate_records: int = Field(ge=0)
    record_counts: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    order_capability: Literal["forbidden"] = "forbidden"


class DatasetSplit(StrictModel):
    split_id: str
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    test_start: datetime
    test_end: datetime
    holdout_start: datetime | None = None
    holdout_end: datetime | None = None
    embargo_days: int = Field(ge=0)


class DatasetSplitPlan(StrictModel):
    status: Literal[
        "READY",
        "BLOCKED_MISSING_CALIBRATION_DATA",
        "BLOCKED_INSUFFICIENT_HISTORY",
    ]
    method: Literal["rolling", "expanding"]
    dataset_hash: str | None = None
    splits: list[DatasetSplit] = Field(default_factory=list)
    final_holdout_locked: bool = True
    warnings: list[str] = Field(default_factory=list)


class OfflineModelCalibration(StrictModel):
    model: Literal["gbm", "local_volatility", "heston", "heston_jump"]
    status: Literal[
        "calibrated_pending_validation",
        "experimental_fit",
        "insufficient_data",
        "blocked_synthetic_data",
    ]
    observations: int = Field(ge=0)
    parameters: dict[str, float] = Field(default_factory=dict)
    calibration_error: float | None = Field(default=None, ge=0)
    feller_condition_satisfied: bool | None = None
    diagnostics: list[str] = Field(default_factory=list)


class OfflineCalibrationReport(StrictModel):
    status: Literal[
        "CALIBRATION_FIT_PENDING_VALIDATION",
        "BLOCKED_MISSING_CALIBRATION_DATA",
        "BLOCKED_INVALID_CALIBRATION_DATA",
        "FIXTURE_ONLY_NOT_CALIBRATED",
    ]
    dataset_hash: str | None = None
    cutoff: datetime | None = None
    models: list[OfflineModelCalibration] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    order_capability: Literal["forbidden"] = "forbidden"


def _record_from_mapping(row: dict[str, Any]) -> HistoricalRecord:
    normalized = dict(row)
    for key in ("value", "strike", "bid", "ask", "split_adjustment", "dividend_adjustment"):
        value = normalized.get(key)
        if isinstance(value, str) and value.strip():
            try:
                normalized[key] = float(value)
            except ValueError:
                pass
        elif value == "":
            normalized[key] = None
    metadata = normalized.get("metadata")
    if isinstance(metadata, str):
        normalized["metadata"] = json.loads(metadata) if metadata.strip() else {}
    return HistoricalRecord.model_validate(normalized)


def load_historical_dataset(path: Path) -> HistoricalDataset:
    suffix = path.suffix.casefold()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("historical JSON must be an object with metadata and records")
        return HistoricalDataset.model_validate(payload)
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [_record_from_mapping(dict(row)) for row in csv.DictReader(handle)]
        if not rows:
            raise ValueError("historical CSV is empty")
        cutoff = max(record.available_at for record in rows)
        return HistoricalDataset(
            dataset_id=path.stem,
            dataset_version="csv-v1",
            created_at=cutoff,
            cutoff=cutoff,
            timezone="UTC",
            provider="CSV import; provider must be reviewed",
            license_or_usage_notes="Not supplied in CSV; validation required.",
            synthetic=True,
            split_adjustment_policy="must_be_documented_in_sidecar",
            dividend_adjustment_policy="must_be_documented_in_sidecar",
            records=rows,
        )
    if suffix in {".parquet", ".pq"}:
        try:
            pandas = importlib.import_module("pandas")
            frame = pandas.read_parquet(path)
        except (ImportError, OSError, ValueError) as error:
            raise ValueError(
                "Parquet support requires a compatible pandas/pyarrow installation"
            ) from error
        rows = [
            _record_from_mapping(cast(dict[str, Any], row))
            for row in frame.to_dict(orient="records")
        ]
        if not rows:
            raise ValueError("historical Parquet file is empty")
        cutoff = max(record.available_at for record in rows)
        return HistoricalDataset(
            dataset_id=path.stem,
            dataset_version="parquet-v1",
            created_at=cutoff,
            cutoff=cutoff,
            timezone="UTC",
            provider="Parquet import; provider must be reviewed",
            license_or_usage_notes="Not supplied in Parquet; validation required.",
            synthetic=True,
            split_adjustment_policy="must_be_documented_in_sidecar",
            dividend_adjustment_policy="must_be_documented_in_sidecar",
            records=rows,
        )
    raise ValueError(f"unsupported historical dataset format: {suffix or '<none>'}")


def validate_historical_dataset(
    path: Path | None,
) -> tuple[HistoricalDataset | None, DatasetQualityReport]:
    if path is None or not path.is_file():
        return None, DatasetQualityReport(
            status="BLOCKED_MISSING_CALIBRATION_DATA",
            format="missing",
            total_records=0,
            accepted_records=0,
            excluded_post_cutoff=0,
            excluded_lookahead=0,
            duplicate_records=0,
            errors=["No authorized historical dataset was supplied."],
            warnings=["Fixtures are never substituted for missing calibration data."],
        )
    suffix = path.suffix.casefold()
    dataset_format: Literal["json", "csv", "parquet", "unsupported"] = (
        "json"
        if suffix == ".json"
        else "csv"
        if suffix == ".csv"
        else "parquet"
        if suffix in {".parquet", ".pq"}
        else "unsupported"
    )
    if dataset_format == "unsupported":
        return None, DatasetQualityReport(
            status="BLOCKED_INVALID_CALIBRATION_DATA",
            format="unsupported",
            total_records=0,
            accepted_records=0,
            excluded_post_cutoff=0,
            excluded_lookahead=0,
            duplicate_records=0,
            errors=[f"Unsupported dataset format: {suffix or '<none>'}"],
        )
    try:
        dataset = load_historical_dataset(path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        return None, DatasetQualityReport(
            status="BLOCKED_INVALID_CALIBRATION_DATA",
            format=dataset_format,
            total_records=0,
            accepted_records=0,
            excluded_post_cutoff=0,
            excluded_lookahead=0,
            duplicate_records=0,
            errors=[str(error)],
        )
    excluded_post_cutoff = 0
    excluded_lookahead = 0
    duplicates = 0
    accepted: list[HistoricalRecord] = []
    seen: set[str] = set()
    units: dict[str, str] = {}
    errors: list[str] = []
    for record in sorted(dataset.records, key=lambda item: (item.timestamp, item.series)):
        if record.timestamp > dataset.cutoff:
            excluded_post_cutoff += 1
            continue
        if record.available_at > dataset.cutoff or record.available_at < record.timestamp:
            excluded_lookahead += 1
            continue
        expected_unit = units.setdefault(record.series, record.unit)
        if expected_unit != record.unit:
            errors.append(
                f"Unit mismatch for {record.series}: {expected_unit} vs {record.unit}."
            )
            continue
        identity = stable_hash(
            {
                "type": record.record_type,
                "timestamp": record.timestamp,
                "series": record.series,
                "value": record.value,
                "symbol": record.symbol,
                "source": record.source_id,
            }
        )
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        accepted.append(record)
    accepted_dataset = dataset.model_copy(update={"records": accepted})
    dataset_hash = stable_hash(accepted_dataset.model_dump(mode="json"))
    counts: dict[str, int] = {}
    for record in accepted:
        counts[record.record_type] = counts.get(record.record_type, 0) + 1
    if not accepted or "underlying" not in counts:
        errors.append("At least one look-ahead-safe underlying series is required.")
    status: Literal[
        "READY_FOR_OFFLINE_CALIBRATION",
        "BLOCKED_INVALID_CALIBRATION_DATA",
        "FIXTURE_ONLY_NOT_CALIBRATED",
    ] = (
        "BLOCKED_INVALID_CALIBRATION_DATA"
        if errors
        else "FIXTURE_ONLY_NOT_CALIBRATED"
        if dataset.synthetic
        else "READY_FOR_OFFLINE_CALIBRATION"
    )
    warnings = [
        "Dataset validation checks mechanics and lineage; it does not grant data rights.",
        "The final holdout must remain inaccessible to parameter selection.",
    ]
    if dataset.synthetic:
        warnings.append("Synthetic/fixture data cannot produce calibrated model status.")
    return accepted_dataset, DatasetQualityReport(
        status=status,
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.dataset_version,
        dataset_hash=dataset_hash,
        format=dataset_format,
        cutoff=dataset.cutoff,
        total_records=len(dataset.records),
        accepted_records=len(accepted),
        excluded_post_cutoff=excluded_post_cutoff,
        excluded_lookahead=excluded_lookahead,
        duplicate_records=duplicates,
        record_counts=counts,
        errors=errors,
        warnings=warnings,
    )


def build_dataset_splits(
    dataset: HistoricalDataset | None,
    quality: DatasetQualityReport,
    *,
    method: Literal["rolling", "expanding"] = "expanding",
    embargo_days: int = 5,
    minimum_train: int = 60,
    validation_size: int = 20,
    test_size: int = 20,
    holdout_size: int = 20,
) -> DatasetSplitPlan:
    if dataset is None:
        return DatasetSplitPlan(
            status="BLOCKED_MISSING_CALIBRATION_DATA",
            method=method,
            warnings=["No dataset was supplied; no fixture split was created."],
        )
    timestamps = sorted(
        {
            record.timestamp
            for record in dataset.records
            if record.record_type == "underlying"
        }
    )
    required = minimum_train + validation_size + test_size + holdout_size + embargo_days * 3
    if len(timestamps) < required:
        return DatasetSplitPlan(
            status="BLOCKED_INSUFFICIENT_HISTORY",
            method=method,
            dataset_hash=quality.dataset_hash,
            warnings=[
                f"Need at least {required} underlying timestamps; found {len(timestamps)}."
            ],
        )
    holdout_start_index = len(timestamps) - holdout_size
    test_end_index = holdout_start_index - embargo_days - 1
    test_start_index = test_end_index - test_size + 1
    validation_end_index = test_start_index - embargo_days - 1
    validation_start_index = validation_end_index - validation_size + 1
    train_end_index = validation_start_index - embargo_days - 1
    train_start_index = 0 if method == "expanding" else max(0, train_end_index - minimum_train + 1)
    split = DatasetSplit(
        split_id=f"{method}-{stable_hash(timestamps)[:12]}",
        train_start=timestamps[train_start_index],
        train_end=timestamps[train_end_index],
        validation_start=timestamps[validation_start_index],
        validation_end=timestamps[validation_end_index],
        test_start=timestamps[test_start_index],
        test_end=timestamps[test_end_index],
        holdout_start=timestamps[holdout_start_index],
        holdout_end=timestamps[-1],
        embargo_days=embargo_days,
    )
    return DatasetSplitPlan(
        status="READY",
        method=method,
        dataset_hash=quality.dataset_hash,
        splits=[split],
        warnings=[
            "The holdout interval is recorded as locked and must not tune parameters.",
            "Availability timestamps remain authoritative inside every interval.",
        ],
    )


def fit_offline_models(
    dataset: HistoricalDataset | None,
    quality: DatasetQualityReport,
) -> OfflineCalibrationReport:
    if dataset is None:
        return OfflineCalibrationReport(
            status="BLOCKED_MISSING_CALIBRATION_DATA",
            warnings=["No dataset supplied; fixtures were not substituted."],
        )
    if quality.status == "BLOCKED_INVALID_CALIBRATION_DATA":
        return OfflineCalibrationReport(
            status="BLOCKED_INVALID_CALIBRATION_DATA",
            dataset_hash=quality.dataset_hash,
            cutoff=dataset.cutoff,
            warnings=quality.errors,
        )
    underlying = sorted(
        (
            record
            for record in dataset.records
            if record.record_type == "underlying"
            and isinstance(record.value, (int, float))
            and not isinstance(record.value, bool)
        ),
        key=lambda item: item.timestamp,
    )
    prices = [float(record.value) for record in underlying if float(record.value) > 0]
    if len(prices) < 30:
        insufficient = [
            OfflineModelCalibration(
                model=model,
                status="blocked_synthetic_data" if dataset.synthetic else "insufficient_data",
                observations=len(prices),
                diagnostics=["At least 30 underlying closes are required."],
            )
            for model in ("gbm", "local_volatility", "heston", "heston_jump")
        ]
        return OfflineCalibrationReport(
            status=(
                "FIXTURE_ONLY_NOT_CALIBRATED"
                if dataset.synthetic
                else "BLOCKED_INVALID_CALIBRATION_DATA"
            ),
            dataset_hash=quality.dataset_hash,
            cutoff=dataset.cutoff,
            models=insufficient,
            warnings=["Insufficient look-ahead-safe underlying history."],
        )
    returns = [
        math.log(current / previous)
        for previous, current in zip(prices, prices[1:], strict=False)
    ]
    annual_volatility = DEFAULT_QUANT_CONVENTIONS.annualize_volatility(stdev(returns))
    annual_drift = DEFAULT_QUANT_CONVENTIONS.annualize_mean_return(fmean(returns))
    base_status: Literal[
        "calibrated_pending_validation",
        "experimental_fit",
        "blocked_synthetic_data",
    ] = (
        "blocked_synthetic_data"
        if dataset.synthetic
        else "calibrated_pending_validation"
    )
    gbm = OfflineModelCalibration(
        model="gbm",
        status=base_status,
        observations=len(returns),
        parameters={
            "annual_drift": annual_drift,
            "annual_volatility": annual_volatility,
        },
        diagnostics=[
            "Close-to-close log returns, annualized with 252 sessions.",
            "Fit status does not imply out-of-sample predictive validity.",
        ],
    )
    option_records = [
        record for record in dataset.records if record.record_type == "option_chain"
    ]
    option_dates = {record.timestamp.date() for record in option_records}
    strikes = {record.strike for record in option_records if record.strike is not None}
    local_ready = len(option_dates) >= 3 and len(strikes) >= 5
    local = OfflineModelCalibration(
        model="local_volatility",
        status=base_status if local_ready else "insufficient_data",
        observations=len(option_records),
        diagnostics=[
            (
                "Historical option surfaces are present for an offline fit."
                if local_ready
                else "Need at least three surface dates and five strikes."
            ),
            "Static-arbitrage checks are mandatory before promotion.",
        ],
    )
    heston = OfflineModelCalibration(
        model="heston",
        status="insufficient_data",
        observations=len(option_records),
        feller_condition_satisfied=None,
        diagnostics=[
            "A constrained Heston optimizer is intentionally not faked from close history.",
            "Timestamped option-surface history and calibration-error targets are required.",
        ],
    )
    centered = [value - fmean(returns) for value in returns]
    sigma = stdev(returns)
    jumps = [value for value in centered if abs(value) >= 3 * sigma]
    jump = OfflineModelCalibration(
        model="heston_jump",
        status="experimental_fit" if len(jumps) >= 5 and not dataset.synthetic else (
            "blocked_synthetic_data" if dataset.synthetic else "insufficient_data"
        ),
        observations=len(returns),
        parameters=(
            {
                "jump_intensity_per_year": len(jumps)
                / len(returns)
                * DEFAULT_QUANT_CONVENTIONS.trading_session_basis,
                "jump_log_mean": fmean(jumps),
                "jump_log_volatility": stdev(jumps) if len(jumps) > 1 else 0.0,
            }
            if jumps
            else {}
        ),
        diagnostics=[
            "Jump frequency, direction, and amplitude are reported separately.",
            "Threshold classification is experimental and requires walk-forward validation.",
        ],
    )
    return OfflineCalibrationReport(
        status=(
            "FIXTURE_ONLY_NOT_CALIBRATED"
            if dataset.synthetic
            else "CALIBRATION_FIT_PENDING_VALIDATION"
        ),
        dataset_hash=quality.dataset_hash,
        cutoff=dataset.cutoff,
        models=[gbm, local, heston, jump],
        warnings=[
            "No model is promoted by an in-sample fit.",
            "Holdout and walk-forward evaluation remain separate.",
        ],
    )


def default_missing_calibration_report() -> OfflineCalibrationReport:
    return fit_offline_models(
        None,
        DatasetQualityReport(
            status="BLOCKED_MISSING_CALIBRATION_DATA",
            format="missing",
            total_records=0,
            accepted_records=0,
            excluded_post_cutoff=0,
            excluded_lookahead=0,
            duplicate_records=0,
        ),
    )
