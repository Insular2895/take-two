"""Validate committed V11.1 fixtures against the runtime contracts."""

from __future__ import annotations

import json
from pathlib import Path

from take_two_options.intelligence.backtesting import (
    load_walk_forward_dataset,
    run_walk_forward,
)
from take_two_options.intelligence.calibration import validate_historical_dataset
from take_two_options.intelligence.monitoring import replay_position_trajectory
from take_two_options.intelligence.schemas import PositionTrajectoryFixture

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
    if len(schemas) != 6:
        raise RuntimeError(f"Expected six JSON Schemas; found {len(schemas)}.")
    for path in schemas:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise RuntimeError(f"{path.name} does not declare JSON Schema 2020-12.")

    calibration_path = ROOT / "fixtures/v11/historical_calibration.example.json"
    _dataset, calibration_quality = validate_historical_dataset(calibration_path)
    if calibration_quality.status != "FIXTURE_ONLY_NOT_CALIBRATED":
        raise RuntimeError("Synthetic calibration fixture was not kept fixture-only.")

    walk_forward = run_walk_forward(
        load_walk_forward_dataset(ROOT / "fixtures/v11/walk_forward.example.json")
    )
    if walk_forward.status != "FIXTURE_ONLY_NOT_VALIDATED":
        raise RuntimeError("Synthetic walk-forward fixture was not kept fixture-only.")

    trajectory = PositionTrajectoryFixture.model_validate_json(
        (ROOT / "fixtures/v11/position_trajectory.example.json").read_text(
            encoding="utf-8"
        )
    )
    replay = replay_position_trajectory(trajectory)
    if len(replay.reports) != len(trajectory.snapshots):
        raise RuntimeError("Position trajectory replay lost snapshots.")
    if replay.order_capability != "forbidden":
        raise RuntimeError("Position trajectory replay breached the execution boundary.")

    print(
        json.dumps(
            {
                "status": "passed",
                "schemas": len(schemas),
                "calibration": calibration_quality.status,
                "walk_forward": walk_forward.status,
                "trajectory_snapshots": len(replay.reports),
                "order_capability": replay.order_capability,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
