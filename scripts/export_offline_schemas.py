"""Export deterministic JSON Schemas for the V11.1 offline contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from take_two_options.config.contracts import PreOpraConfig
from take_two_options.decision.quality_scores import FiveScoreReport
from take_two_options.decision.severity_gates import SeverityGateReport
from take_two_options.empirical_calibration import EmpiricalCalibrationReport
from take_two_options.historical_data.contracts import HistoricalDatasetManifest
from take_two_options.historical_data.data_rights import DataUsageRightsReport
from take_two_options.historical_data.event_regimes import EventRegimeReport
from take_two_options.historical_data.option_observations import (
    HistoricalOptionDatasetSummary,
)
from take_two_options.historical_data.market_context import MarketContextSummary
from take_two_options.intelligence.backtesting import WalkForwardReport
from take_two_options.intelligence.calibration import OfflineCalibrationReport
from take_two_options.intelligence.schemas import (
    CandidateValidationSummary,
    FeatureReadiness,
    NormalizedEvidenceEvent,
    UnifiedObservation,
)
from take_two_options.quantitative.historical_surfaces import HistoricalSurfaceReport
from take_two_options.reporting.pre_opra_final import FinalPreOpraReport
from take_two_options.validation.baseline_comparison import BaselineComparisonReport
from take_two_options.validation.final_holdout import HoldoutLedgerEntry
from take_two_options.validation.walk_forward_protocol import WalkForwardProtocolReport

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIRECTORY = ROOT / "schemas"
SCHEMAS: dict[str, type[BaseModel]] = {
    "baseline_comparison.schema.json": BaselineComparisonReport,
    "data_usage_rights.schema.json": DataUsageRightsReport,
    "empirical_calibration.schema.json": EmpiricalCalibrationReport,
    "five_score_report.schema.json": FiveScoreReport,
    "final_pre_opra_report.schema.json": FinalPreOpraReport,
    "severity_gate_report.schema.json": SeverityGateReport,
    "pre_opra_config.schema.json": PreOpraConfig,
    "historical_dataset_manifest.schema.json": HistoricalDatasetManifest,
    "historical_option_dataset_summary.schema.json": HistoricalOptionDatasetSummary,
    "market_context_summary.schema.json": MarketContextSummary,
    "historical_surface_report.schema.json": HistoricalSurfaceReport,
    "holdout_ledger_entry.schema.json": HoldoutLedgerEntry,
    "readiness.schema.json": FeatureReadiness,
    "observation.schema.json": UnifiedObservation,
    "event.schema.json": NormalizedEvidenceEvent,
    "event_regime_report.schema.json": EventRegimeReport,
    "calibration_report.schema.json": OfflineCalibrationReport,
    "backtest_report.schema.json": WalkForwardReport,
    "model_validation.schema.json": CandidateValidationSummary,
    "walk_forward_protocol.schema.json": WalkForwardProtocolReport,
}


def _serialized_schema(name: str, model: type[BaseModel]) -> str:
    schema: dict[str, Any] = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://schemas.take-two-options.invalid/v11.1/{name}"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed schemas differ from the Pydantic contracts.",
    )
    arguments = parser.parse_args()
    failures: list[str] = []
    if not arguments.check:
        SCHEMA_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, model in SCHEMAS.items():
        target = SCHEMA_DIRECTORY / name
        expected = _serialized_schema(name, model)
        if arguments.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != expected:
                failures.append(str(target.relative_to(ROOT)))
        else:
            target.write_text(expected, encoding="utf-8")
    if failures:
        print("Schema drift: " + ", ".join(failures))
        return 1
    print(
        ("Verified" if arguments.check else "Exported") + f" {len(SCHEMAS)} offline JSON Schemas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
