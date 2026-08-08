"""Run empirical, volatility-model, and chronological OOS diagnostics."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.empirical_calibration import PriceObservation, calibrate_empirical_returns
from take_two_options.historical_data.market_context import MarketContextDataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--surfaces", type=Path, required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ticker", default="TTWO")
    args = parser.parse_args()

    context = MarketContextDataset.model_validate_json(args.context.read_text(encoding="utf-8"))
    surfaces = cast(dict[str, Any], json.loads(args.surfaces.read_text(encoding="utf-8")))
    observations = [
        PriceObservation(
            timestamp=bar.market_time,
            available_at=bar.available_at,
            close=bar.close,
        )
        for bar in context.underlying_bars
    ]
    snapshot_statuses = [str(item["status"]) for item in surfaces["snapshots"]]
    report = calibrate_empirical_returns(
        observations,
        ticker=args.ticker,
        decision_cutoff=datetime.fromisoformat(args.cutoff.replace("Z", "+00:00")),
        source_ids=sorted(context.source_hashes),
        license_status="to_review",
        bootstrap_draws=2_000,
        seed=20_260_808,
        heston_surface_summary={
            "calendar_arbitrage_violations": snapshot_statuses.count("ARBITRAGE_VIOLATION"),
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
