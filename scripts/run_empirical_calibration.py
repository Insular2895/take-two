"""Run Phase-D diagnostics on a local Alpaca close-history extract."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.empirical_calibration import PriceObservation, calibrate_empirical_returns


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--ticker", default="TTWO")
    args = parser.parse_args()
    payload = cast(dict[str, Any], json.loads(args.dataset.read_text(encoding="utf-8")))
    observations = [
        PriceObservation(
            timestamp=point["timestamp"],
            available_at=point["data_available_at"],
            close=point["close"],
        )
        for point in cast(list[dict[str, Any]], payload["points"])
    ]
    source = cast(dict[str, Any], payload["source"])
    report = calibrate_empirical_returns(
        observations,
        ticker=args.ticker,
        decision_cutoff=datetime.fromisoformat(args.cutoff.replace("Z", "+00:00")),
        source_ids=[str(source["id"])],
        license_status="to_review",
    )
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
