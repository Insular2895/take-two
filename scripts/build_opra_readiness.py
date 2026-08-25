"""Write a secret-free OPRA interface readiness artifact without connecting."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from take_two_options.opra.contracts import assess_provider_readiness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = assess_provider_readiness(os.environ)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
