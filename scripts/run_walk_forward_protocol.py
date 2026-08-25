"""Run the real option-strategy development walk-forward without touching holdout."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from take_two_options.validation.comparable_panel import ComparablePanelDataset
from take_two_options.validation.walk_forward_protocol import run_strategy_walk_forward


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    panel = ComparablePanelDataset.model_validate_json(args.panel.read_text(encoding="utf-8"))
    report = run_strategy_walk_forward(
        panel,
        generated_at=datetime.fromisoformat(args.generated_at.replace("Z", "+00:00")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
