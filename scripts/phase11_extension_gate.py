"""Print and optionally verify the deterministic Phase-11 extension review."""

from __future__ import annotations

import argparse
from pathlib import Path

from take_two_options.validation.extension_evaluation import (
    build_phase11_extension_review,
)

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "validation/phase11_extension_review.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = build_phase11_extension_review().model_dump_json(indent=2) + "\n"
    if args.check:
        if not COMMITTED.is_file() or COMMITTED.read_text(encoding="utf-8") != rendered:
            print("Phase-11 extension review is stale.")
            return 1
        print("Verified deterministic Phase-11 extension review.")
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
