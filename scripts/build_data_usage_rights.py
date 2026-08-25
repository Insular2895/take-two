"""Build the machine-readable pre-OPRA data-rights audit."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from take_two_options.historical_data.data_rights import pre_opra_data_usage_rights

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "pre_opra" / "data_usage_rights_2026-08-08.json"


def main() -> int:
    report = pre_opra_data_usage_rights(datetime(2026, 8, 8, tzinfo=UTC))
    OUTPUT.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(report.records)} providers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
