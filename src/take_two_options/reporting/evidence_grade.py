"""Monotone evidence grades and a complete research-decision sidecar report."""

from __future__ import annotations

import html
import math
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class EvidenceGrade(StrEnum):
    PROPOSED = "proposed"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    NUMERICALLY_VALIDATED = "numerically_validated"
    EMPIRICALLY_VALIDATED = "empirically_validated"
    HOLDOUT_VALIDATED = "holdout_validated"
    PAPER_VALIDATED = "paper_validated"


_GRADE_ORDER = tuple(EvidenceGrade)

DecisionClaimCap = Literal[
    "proposal_only",
    "software_implemented_only",
    "software_tested_only",
    "numerically_validated_research_only",
    "empirically_validated_research_only",
    "holdout_validated_research_only",
    "paper_validated_research_only",
]


class ComponentEvidenceClaim(StrictModel):
    component_id: str = Field(min_length=1)
    required_for_decision: bool = True
    implemented: bool = False
    tests_passed: bool = False
    source_ids: list[str] = Field(default_factory=list)
    numerical_validation_passed: bool = False
    empirical_validation_passed: bool = False
    dataset_hash: str | None = None
    out_of_sample_partition: Literal["validation", "final_holdout"] | None = None
    holdout_validation_passed: bool = False
    holdout_ledger_hash: str | None = None
    paper_validation_passed: bool = False
    paper_manifest_hash: str | None = None
    synthetic_only: bool = False
    fixture_only: bool = False
    blockers: list[str] = Field(default_factory=list)


class ComponentEvidenceGrade(StrictModel):
    component_id: str
    grade: EvidenceGrade
    grade_rank: int = Field(ge=0)
    required_for_decision: bool
    satisfied_prerequisites: list[str]
    missing_prerequisites: list[str]
    blockers: list[str]


class DecisionEvidenceGrade(StrictModel):
    overall_grade: EvidenceGrade
    overall_rank: int = Field(ge=0)
    decision_claim_cap: DecisionClaimCap
    components: list[ComponentEvidenceGrade] = Field(min_length=1)
    blockers: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def _grade_rank(grade: EvidenceGrade) -> int:
    return _GRADE_ORDER.index(grade)


def grade_component(claim: ComponentEvidenceClaim) -> ComponentEvidenceGrade:
    """Compute the highest grade with every lower prerequisite satisfied."""
    grade = EvidenceGrade.PROPOSED
    satisfied: list[str] = []
    missing: list[str] = []
    downstream_claimed = any(
        (
            claim.tests_passed,
            claim.numerical_validation_passed,
            claim.empirical_validation_passed,
            claim.holdout_validation_passed,
            claim.paper_validation_passed,
        )
    )
    if not claim.implemented:
        missing.append("implementation")
        if downstream_claimed:
            missing.append("downstream evidence ignored because implementation is absent")
    else:
        grade = EvidenceGrade.IMPLEMENTED
        satisfied.append("implementation")
        if not claim.tests_passed:
            missing.append("passing tests")
        else:
            grade = EvidenceGrade.TESTED
            satisfied.append("passing tests")
            if not claim.numerical_validation_passed:
                missing.append("numerical validation")
            elif not claim.source_ids:
                missing.append("documentary source for numerical validation")
            else:
                grade = EvidenceGrade.NUMERICALLY_VALIDATED
                satisfied.extend(["numerical validation", "documentary source"])
                empirical_lineage = (
                    claim.empirical_validation_passed
                    and claim.dataset_hash is not None
                    and claim.out_of_sample_partition is not None
                    and not claim.synthetic_only
                    and not claim.fixture_only
                )
                if not empirical_lineage:
                    missing.append("real out-of-sample empirical validation lineage")
                else:
                    grade = EvidenceGrade.EMPIRICALLY_VALIDATED
                    satisfied.append("real out-of-sample empirical validation")
                    holdout_lineage = (
                        claim.holdout_validation_passed
                        and claim.out_of_sample_partition == "final_holdout"
                        and claim.holdout_ledger_hash is not None
                    )
                    if not holdout_lineage:
                        missing.append("sealed final-holdout validation lineage")
                    else:
                        grade = EvidenceGrade.HOLDOUT_VALIDATED
                        satisfied.append("sealed final-holdout validation")
                        paper_lineage = (
                            claim.paper_validation_passed
                            and claim.paper_manifest_hash is not None
                        )
                        if not paper_lineage:
                            missing.append("paper-validation manifest")
                        else:
                            grade = EvidenceGrade.PAPER_VALIDATED
                            satisfied.append("paper-validation manifest")
    return ComponentEvidenceGrade(
        component_id=claim.component_id,
        grade=grade,
        grade_rank=_grade_rank(grade),
        required_for_decision=claim.required_for_decision,
        satisfied_prerequisites=satisfied,
        missing_prerequisites=missing,
        blockers=claim.blockers,
    )


def calculate_decision_evidence_grade(
    claims: list[ComponentEvidenceClaim],
) -> DecisionEvidenceGrade:
    """Use the weakest required component; optional strength cannot compensate for it."""
    if not claims:
        raise ValueError("at least one evidence component is required")
    if len({claim.component_id for claim in claims}) != len(claims):
        raise ValueError("evidence component ids must be unique")
    components = [grade_component(claim) for claim in claims]
    required = [component for component in components if component.required_for_decision]
    if not required:
        raise ValueError("at least one component must be required for the decision")
    weakest = min(required, key=lambda component: component.grade_rank)
    caps: dict[EvidenceGrade, DecisionClaimCap] = {
        EvidenceGrade.PROPOSED: "proposal_only",
        EvidenceGrade.IMPLEMENTED: "software_implemented_only",
        EvidenceGrade.TESTED: "software_tested_only",
        EvidenceGrade.NUMERICALLY_VALIDATED: "numerically_validated_research_only",
        EvidenceGrade.EMPIRICALLY_VALIDATED: "empirically_validated_research_only",
        EvidenceGrade.HOLDOUT_VALIDATED: "holdout_validated_research_only",
        EvidenceGrade.PAPER_VALIDATED: "paper_validated_research_only",
    }
    blockers = sorted(
        {
            blocker
            for component in required
            for blocker in (*component.missing_prerequisites, *component.blockers)
        }
    )
    return DecisionEvidenceGrade(
        overall_grade=weakest.grade,
        overall_rank=weakest.grade_rank,
        decision_claim_cap=caps[weakest.grade],
        components=components,
        blockers=blockers,
    )


class EstimateWithUncertainty(StrictModel):
    estimate_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    central: float | None
    interval: tuple[float, float] | None
    unit: str = Field(min_length=1)
    measure: Literal["P", "Q", "not_applicable"]
    uncertainty_diagnostic: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_uncertainty(self) -> EstimateWithUncertainty:
        if self.central is None:
            if self.interval is not None:
                raise ValueError("an unavailable estimate cannot have a numeric interval")
            return self
        if not math.isfinite(self.central) or self.interval is None:
            raise ValueError("a numeric estimate requires a finite value and interval")
        lower, upper = self.interval
        if not all(math.isfinite(value) for value in self.interval):
            raise ValueError("estimate interval must be finite")
        if not lower <= self.central <= upper:
            raise ValueError("estimate central value must lie inside its interval")
        return self


class ProbabilityWithUncertainty(StrictModel):
    probability_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    central: float | None = Field(default=None, ge=0, le=1)
    interval: tuple[float, float] | None = None
    origin: str = Field(min_length=1)
    uncertainty_diagnostic: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_probability_uncertainty(self) -> ProbabilityWithUncertainty:
        if self.central is None:
            if self.interval is not None:
                raise ValueError("an unavailable probability cannot have a numeric interval")
            return self
        if self.interval is None:
            raise ValueError("a displayed probability requires an interval")
        lower, upper = self.interval
        if not 0 <= lower <= self.central <= upper <= 1:
            raise ValueError("invalid probability interval")
        return self


class FinalDecisionEvidenceReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    report_id: str = Field(min_length=1)
    ticker: Literal["TTWO"] = "TTWO"
    as_of: datetime
    decision_status: Literal["NO_TRADE", "BLOCKED", "RESEARCH_CANDIDATE", "PAPER_REVIEW"]
    selected_candidate_id: str
    evidence_grade: DecisionEvidenceGrade
    estimates: list[EstimateWithUncertainty] = Field(min_length=1)
    probabilities: list[ProbabilityWithUncertainty] = Field(min_length=1)
    assumptions: list[str] = Field(min_length=1)
    favorable_scenarios: list[str] = Field(min_length=1)
    failure_scenarios: list[str] = Field(min_length=1)
    model_risks: list[str] = Field(min_length=1)
    data_limits: list[str] = Field(min_length=1)
    ranking_reasons: list[str] = Field(min_length=1)
    no_trade_reasons: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(min_length=1)
    synthetic_or_fixture_input: bool
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def validate_no_trade_explanation(self) -> FinalDecisionEvidenceReport:
        if self.decision_status in {"NO_TRADE", "BLOCKED"} and not self.no_trade_reasons:
            raise ValueError("NO_TRADE and BLOCKED reports require exact reasons")
        return self


def _display_estimate(estimate: EstimateWithUncertainty) -> str:
    if estimate.central is None:
        return f"unavailable — {estimate.uncertainty_diagnostic}"
    assert estimate.interval is not None
    return (
        f"{estimate.central:.6g} {estimate.unit} "
        f"[{estimate.interval[0]:.6g}, {estimate.interval[1]:.6g}]"
    )


def _display_probability(probability: ProbabilityWithUncertainty) -> str:
    if probability.central is None:
        return f"unavailable — {probability.uncertainty_diagnostic}"
    assert probability.interval is not None
    return (
        f"{probability.central:.2%} "
        f"[{probability.interval[0]:.2%}, {probability.interval[1]:.2%}]"
    )


def final_decision_markdown(report: FinalDecisionEvidenceReport) -> str:
    """Render every mandatory decision section in a stable order."""
    lines = [
        "# TTWO final research-decision evidence",
        "",
        f"- Status: `{report.decision_status}`",
        f"- Selected reference: `{report.selected_candidate_id}`",
        f"- Evidence grade: `{report.evidence_grade.overall_grade.value}`",
        f"- Claim cap: `{report.evidence_grade.decision_claim_cap}`",
        "- Execution: `forbidden`; human confirmation required",
        "",
        "## Estimates and uncertainty",
        "",
    ]
    lines.extend(
        f"- {item.label}: {_display_estimate(item)}; measure=`{item.measure}`; "
        f"diagnostic={item.uncertainty_diagnostic}"
        for item in report.estimates
    )
    lines.extend(["", "## Probabilities and uncertainty", ""])
    lines.extend(
        f"- {item.label}: {_display_probability(item)}; origin=`{item.origin}`; "
        f"diagnostic={item.uncertainty_diagnostic}"
        for item in report.probabilities
    )
    sections = (
        ("Assumptions", report.assumptions),
        ("Favorable scenarios", report.favorable_scenarios),
        ("Failure scenarios", report.failure_scenarios),
        ("Model risks", report.model_risks),
        ("Data limits", report.data_limits),
        ("Exact ranking reasons", report.ranking_reasons),
        ("Exact NO_TRADE reasons", report.no_trade_reasons or ["not selected"]),
        ("Evidence blockers", report.evidence_grade.blockers or ["none declared"]),
        ("Sources", report.source_ids),
    )
    for title, items in sections:
        lines.extend(["", f"## {title}", ""])
        lines.extend(f"- {item}" for item in items)
    return "\n".join(lines) + "\n"


def final_decision_html(report: FinalDecisionEvidenceReport) -> str:
    """Render a static network-free dashboard; no JavaScript is emitted."""
    def esc(value: object) -> str:
        return html.escape(str(value))

    def list_items(items: list[str]) -> str:
        return "".join(f"<li>{esc(item)}</li>" for item in items)

    estimate_rows = "".join(
        f"<tr><td>{esc(item.label)}</td><td>{esc(_display_estimate(item))}</td>"
        f"<td>{esc(item.measure)}</td><td>{esc(item.uncertainty_diagnostic)}</td></tr>"
        for item in report.estimates
    )
    probability_rows = "".join(
        f"<tr><td>{esc(item.label)}</td><td>{esc(_display_probability(item))}</td>"
        f"<td>{esc(item.origin)}</td><td>{esc(item.uncertainty_diagnostic)}</td></tr>"
        for item in report.probabilities
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer">
<title>TTWO final research-decision evidence</title><style>
body{{margin:auto;max-width:1100px;padding:2rem;font:15px/1.5 system-ui;background:#f5f1e8;
color:#172019}}h1,h2{{font-family:Georgia,serif}}.gate{{border:2px solid #8a2d2d;padding:1rem}}
table{{width:100%;border-collapse:collapse;background:#fffdf8}}th,td{{padding:.6rem;
border:1px solid #d9d2c3;text-align:left;vertical-align:top}}code{{font-weight:700}}
</style></head><body><h1>TTWO final research-decision evidence</h1>
<section class="gate"><p>Status: <code>{esc(report.decision_status)}</code> · candidate:
<code>{esc(report.selected_candidate_id)}</code></p><p>Evidence grade:
<code>{esc(report.evidence_grade.overall_grade.value)}</code> · claim cap:
<code>{esc(report.evidence_grade.decision_claim_cap)}</code></p>
<p><code>order_capability=forbidden</code> · human confirmation required</p></section>
<h2>Estimates and uncertainty</h2><table><thead><tr><th>Estimate</th><th>Value and
interval</th><th>Measure</th><th>Diagnostic</th></tr></thead><tbody>{estimate_rows}</tbody></table>
<h2>Probabilities and uncertainty</h2><table><thead><tr><th>Probability</th><th>Value and
interval</th><th>Origin</th><th>Diagnostic</th></tr></thead><tbody>{probability_rows}</tbody></table>
<h2>Assumptions</h2><ul>{list_items(report.assumptions)}</ul>
<h2>Favorable scenarios</h2><ul>{list_items(report.favorable_scenarios)}</ul>
<h2>Failure scenarios</h2><ul>{list_items(report.failure_scenarios)}</ul>
<h2>Model risks</h2><ul>{list_items(report.model_risks)}</ul>
<h2>Data limits</h2><ul>{list_items(report.data_limits)}</ul>
<h2>Exact ranking reasons</h2><ul>{list_items(report.ranking_reasons)}</ul>
<h2>Exact NO_TRADE reasons</h2><ul>{list_items(report.no_trade_reasons or ['not selected'])}</ul>
<h2>Evidence blockers</h2><ul>{list_items(report.evidence_grade.blockers or ['none declared'])}</ul>
<h2>Sources</h2><ul>{list_items(report.source_ids)}</ul>
</body></html>"""
