"""Validate source/formula/test lineage and the published matrix."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return cast(dict[str, Any], payload)


def _unique_ids(items: list[dict[str, Any]], key: str, failures: list[str]) -> set[str]:
    values = [str(item[key]) for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    failures.extend(f"duplicate {key}: {value}" for value in duplicates)
    return set(values)


def _symbol_exists(path: Path, symbol: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.search(rf"\b{re.escape(symbol)}\b", text) is not None


def validate_registry() -> list[str]:
    failures: list[str] = []
    formula_payload = _mapping(ROOT / "docs/research/formula_registry.yaml")
    source_payload = _mapping(ROOT / "docs/research/source_registry.yaml")
    errata_payload = _mapping(ROOT / "docs/research/errata_registry.yaml")
    formulas = cast(list[dict[str, Any]], formula_payload.get("formulas", []))
    sources = cast(list[dict[str, Any]], source_payload.get("sources", []))
    links = cast(list[dict[str, Any]], source_payload.get("formula_links", []))
    errata = cast(list[dict[str, Any]], errata_payload.get("errata", []))
    formula_ids = _unique_ids(formulas, "formula_id", failures)
    source_ids = _unique_ids(sources, "source_id", failures)
    link_ids = _unique_ids(links, "formula_id", failures)
    _unique_ids(errata, "erratum_id", failures)
    if formula_ids != link_ids:
        failures.append(
            "formula_registry/formula_links mismatch: "
            f"formula_only={sorted(formula_ids - link_ids)}; "
            f"link_only={sorted(link_ids - formula_ids)}"
        )
    for formula in formulas:
        formula_id = str(formula["formula_id"])
        references = cast(list[dict[str, Any]], formula.get("sources", []))
        if not references:
            failures.append(f"{formula_id}: missing documentary source")
        for reference in references:
            source_id = str(reference.get("source_id", ""))
            if source_id not in source_ids:
                failures.append(f"{formula_id}: unknown source {source_id}")
        for section in ("implementation", "tests"):
            entries = cast(list[dict[str, Any]], formula.get(section, []))
            if not entries:
                failures.append(f"{formula_id}: missing {section} lineage")
            for entry in entries:
                relative = Path(str(entry.get("file", "")))
                path = ROOT / relative
                if not path.is_file():
                    failures.append(f"{formula_id}: missing file {relative}")
                    continue
                for symbol in cast(list[str], entry.get("symbols", [])):
                    if not _symbol_exists(path, symbol):
                        failures.append(f"{formula_id}: {symbol} absent from {relative}")
    referenced_formula_ids = {
        str(formula_id)
        for source in sources
        for formula_id in cast(list[Any], source.get("formula_id") or [])
    }
    if not referenced_formula_ids.issubset(formula_ids):
        failures.append(
            "source registry references unknown formulas: "
            f"{sorted(referenced_formula_ids - formula_ids)}"
        )
    matrix = (ROOT / "docs/research/formula_lineage_matrix.md").read_text(
        encoding="utf-8"
    )
    matrix_ids = set(re.findall(r"\| `(FORM-[A-Z0-9-]+)` \|", matrix))
    if matrix_ids != formula_ids:
        failures.append(
            "formula lineage matrix mismatch: "
            f"registry_only={sorted(formula_ids - matrix_ids)}; "
            f"matrix_only={sorted(matrix_ids - formula_ids)}"
        )
    return failures


def main() -> int:
    failures = validate_registry()
    print(
        json.dumps(
            {
                "status": "failed" if failures else "passed",
                "failures": failures,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
