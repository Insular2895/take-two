"""Build aggregate TTWO historical SVI diagnostics from private normalized quotes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from take_two_options.historical_data.market_context import MarketContextDataset
from take_two_options.historical_data.option_observations import HistoricalOptionObservation
from take_two_options.quantitative.historical_surfaces import build_historical_surface_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--options", type=Path, required=True)
    parser.add_argument("--option-summary", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--context-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    observations = [
        HistoricalOptionObservation.model_validate_json(line)
        for line in args.options.read_text(encoding="utf-8").splitlines()
        if line
    ]
    context = MarketContextDataset.model_validate_json(args.context.read_text(encoding="utf-8"))
    option_summary = cast(
        dict[str, Any], json.loads(args.option_summary.read_text(encoding="utf-8"))
    )
    context_summary = cast(
        dict[str, Any], json.loads(args.context_summary.read_text(encoding="utf-8"))
    )
    report = build_historical_surface_report(
        observations,
        context,
        option_dataset_hash=str(option_summary["dataset_hash"]),
        context_dataset_hash=str(context_summary["dataset_hash"]),
        license_authorized=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
