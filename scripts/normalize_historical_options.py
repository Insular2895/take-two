"""Normalize private historical option cache and publish only an aggregate audit."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from take_two_options.config.loader import load_pre_opra_config
from take_two_options.historical_data.option_observations import (
    normalize_marketdata_cache,
    write_private_jsonl,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    config_path = arguments.config.resolve()
    config = load_pre_opra_config(config_path)
    settings = config.extensions.get("option_normalization", {})
    cache_dir = ROOT / str(settings.get("cache_dir", "data/marketdata/cache"))
    output_path = ROOT / str(
        settings.get("private_output", "data/pre_opra/normalized_options.jsonl")
    )
    summary_path = ROOT / str(
        settings.get("aggregate_summary", "reports/pre_opra/option_normalization_2026-08-08.json")
    )
    observations, summary = normalize_marketdata_cache(
        cache_dir,
        availability_delay_hours=float(settings.get("availability_delay_hours", 24)),
        generated_at=datetime.combine(config.research_request.as_of, datetime.min.time(), UTC),
    )
    write_private_jsonl(output_path, observations)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Normalized {summary.unique_observations} private observations; "
        f"aggregate audit: {summary_path.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
