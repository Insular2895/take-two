"""Deterministic Phase-10 release-evidence audit for the research-only engine."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.reporting.evidence_grade import FinalDecisionEvidenceReport


class ReleaseEvidenceReview(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    reviewed_on: Literal["2026-08-08"] = "2026-08-08"
    research_release_status: Literal["READY_RESEARCH_ONLY", "BLOCKED"]
    financial_promotion_status: Literal["BLOCKED_MISSING_REAL_EVIDENCE"]
    maximum_decision_claim: Literal["software_tested_only"]
    formula_count: int = Field(ge=1)
    source_count: int = Field(ge=1)
    formula_status_counts: dict[str, int]
    source_status_counts: dict[str, int]
    invalid_promoted_claims: list[str]
    active_experiment_manifests: list[str]
    reproduced_experiment_manifests: list[str]
    contaminated_holdouts: list[str]
    final_holdout_status: str
    example_report_id: str
    example_decision_status: str
    reproducibility_status: Literal[
        "STRUCTURAL_ONLY_NO_ACTIVE_EXPERIMENT_MANIFESTS",
        "ACTIVE_MANIFESTS_REQUIRE_REPLAY",
    ]
    release_blockers: list[str] = Field(min_length=1)
    missing_data: list[str] = Field(min_length=1)
    technical_debt: list[str] = Field(min_length=1)
    order_capability: Literal["forbidden"] = "forbidden"


def _yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return cast(dict[str, Any], payload)


def build_release_evidence_review(root: Path) -> ReleaseEvidenceReview:
    """Audit authoritative artifacts without opening or fabricating a final holdout."""
    formulas = cast(
        list[dict[str, Any]],
        _yaml_mapping(root / "docs/research/formula_registry.yaml").get("formulas", []),
    )
    source_payload = _yaml_mapping(root / "docs/research/source_registry.yaml")
    sources = cast(list[dict[str, Any]], source_payload.get("sources", []))
    maximum = str(source_payload.get("policy", {}).get("current_maximum_claim", ""))
    allowed_formula_statuses = {"proposed", "sourced", "implemented", "tested", maximum}
    invalid_promotions = sorted(
        {
            f"formula:{formula['formula_id']}:{formula.get('validation_status')}"
            for formula in formulas
            if str(formula.get("validation_status")) not in allowed_formula_statuses
        }
        | {
            f"source:{source['source_id']}:{source.get('validation_status')}"
            for source in sources
            if str(source.get("validation_status"))
            not in allowed_formula_statuses
        }
    )
    active_manifests = sorted(
        str(path.relative_to(root))
        for path in (root / "experiments").rglob("*.json")
        if "legacy" not in path.parts
    )
    contaminated = json.loads(
        (root / "validation/contaminated_holdouts/v7_v8_v9/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    holdout_status_text = (root / "validation/HOLDOUT_LEDGER_STATUS.md").read_text(
        encoding="utf-8"
    )
    final_holdout_status = (
        "not_created_no_dataset"
        if "`not_created_no_dataset`" in holdout_status_text
        else "unknown"
    )
    example = FinalDecisionEvidenceReport.model_validate_json(
        (root / "reports/examples/phase9_final_evidence.json").read_text(encoding="utf-8")
    )
    blockers = [
        "No authorized real point-in-time TTWO option dataset is committed.",
        "No active experiment manifest can be replayed; only legacy contaminated runs exist.",
        "The fresh final holdout has not been created or sealed.",
        "No minimum-duration paper campaign has been completed.",
        "Live combo quotes, realized slippage, fill and rejection evidence are absent.",
    ]
    if invalid_promotions:
        blockers.append("At least one registry claim exceeds the configured maximum.")
    research_status: Literal["READY_RESEARCH_ONLY", "BLOCKED"] = (
        "BLOCKED" if invalid_promotions else "READY_RESEARCH_ONLY"
    )
    return ReleaseEvidenceReview(
        research_release_status=research_status,
        financial_promotion_status="BLOCKED_MISSING_REAL_EVIDENCE",
        maximum_decision_claim="software_tested_only",
        formula_count=len(formulas),
        source_count=len(sources),
        formula_status_counts=dict(
            sorted(Counter(str(item.get("validation_status")) for item in formulas).items())
        ),
        source_status_counts=dict(
            sorted(Counter(str(item.get("validation_status")) for item in sources).items())
        ),
        invalid_promoted_claims=invalid_promotions,
        active_experiment_manifests=active_manifests,
        reproduced_experiment_manifests=[],
        contaminated_holdouts=list(contaminated["contaminated_holdouts"]),
        final_holdout_status=final_holdout_status,
        example_report_id=example.report_id,
        example_decision_status=example.decision_status,
        reproducibility_status=(
            "ACTIVE_MANIFESTS_REQUIRE_REPLAY"
            if active_manifests
            else "STRUCTURAL_ONLY_NO_ACTIVE_EXPERIMENT_MANIFESTS"
        ),
        release_blockers=blockers,
        missing_data=[
            "licensed point-in-time TTWO option chains with bid/ask, OI, volume and timestamps",
            "aligned spot, corporate actions, dividends, rates and EUR/USD vintages",
            "reviewed event labels with availability timestamps and source dependency groups",
            "real combo quote, fill, rejection, commission, spread and slippage observations",
            "an untouched final holdout identity/hash and a later paper-trading log",
        ],
        technical_debt=[
            "legacy Bayesian* schema names remain for compatibility",
            "daily exit checkpoints can miss intraday barrier crossings",
            "PBO full-text conformance remains to_review",
            "real SVI/Heston calibration and structural-break diagnostics remain unexercised",
            "the candidate BOOK alias still awaits user confirmation",
        ],
    )
