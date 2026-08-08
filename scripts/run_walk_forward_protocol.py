"""Run the Phase-E chronological reference protocol on local close history."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.validation.walk_forward_protocol import (
    ChronologicalReturn,
    WalkForwardProtocolConfig,
    run_walk_forward_protocol,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--dataset-hash", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--ticker", default="TTWO")
    parser.add_argument("--method", choices=("rolling", "expanding"), default="expanding")
    args = parser.parse_args()
    payload = cast(dict[str, Any], json.loads(args.dataset.read_text(encoding="utf-8")))
    points = cast(list[dict[str, Any]], payload["points"])
    observations = [
        ChronologicalReturn(
            observation_id=f"return-{index:04d}",
            timestamp=current["timestamp"],
            available_at=current["data_available_at"],
            log_return=math.log(float(current["close"]) / float(previous["close"])),
        )
        for index, (previous, current) in enumerate(
            zip(points[:-1], points[1:], strict=True), start=1
        )
    ]
    config = WalkForwardProtocolConfig(
        protocol_id="pre-opra-phase-e-v1",
        method=args.method,
        minimum_train_observations=252,
        rolling_train_observations=252 if args.method == "rolling" else None,
        validation_observations=40,
        test_observations=40,
        step_observations=40,
        purge_observations=5,
        embargo_observations=5,
        model_id="historical_gaussian_reference",
        probability_floor=0.01,
    )
    report = run_walk_forward_protocol(
        observations,
        ticker=args.ticker,
        dataset_hash=args.dataset_hash,
        config=config,
        generated_at=datetime.fromisoformat(args.generated_at.replace("Z", "+00:00")),
        license_status="to_review",
    )
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
