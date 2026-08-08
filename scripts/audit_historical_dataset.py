"""Print a non-redistributive aggregate inventory of the private option cache."""

from __future__ import annotations

import argparse
from pathlib import Path

from take_two_options.historical_data.inventory import (
    inventory_alpaca_underlying,
    inventory_marketdata_cache,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("data/marketdata/cache"))
    parser.add_argument(
        "--underlying",
        type=Path,
        default=Path("data/alpaca/ttwo_calibration_dataset_2026-07-19.json"),
    )
    args = parser.parse_args()
    print(
        "[\n"
        + inventory_marketdata_cache(args.cache_dir).model_dump_json(indent=2)
        + ",\n"
        + inventory_alpaca_underlying(args.underlying).model_dump_json(indent=2)
        + "\n]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
