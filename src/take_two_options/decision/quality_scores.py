"""Five independent, versioned quality scores with raw-metric lineage."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class ScoreKind(StrEnum):
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    EVIDENCE = "evidence"
    MODEL_AGREEMENT = "model_agreement"
    EXECUTION_QUALITY = "execution_quality"


class RawScoreMetric(StrictModel):
    name: str
    value: float | None
    unit: str
    source_id: str
    available: bool

    @model_validator(mode="after")
    def require_value_when_available(self) -> RawScoreMetric:
        if self.available != (self.value is not None):
            raise ValueError("metric availability must match value presence")
        return self


class ScoreComponent(StrictModel):
    metric_name: str
    lower_bound: float
    upper_bound: float
    direction: Literal["increasing", "decreasing"]
    weight: float = Field(gt=0, le=1)
    weight_status: Literal["draft_to_validate", "validated"]
    rationale: str

    @model_validator(mode="after")
    def require_ordered_bounds(self) -> ScoreComponent:
        if self.lower_bound >= self.upper_bound:
            raise ValueError("score component bounds must increase")
        return self


class ScoreFormula(StrictModel):
    kind: ScoreKind
    version: str
    components: list[ScoreComponent] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_normalized_weights(self) -> ScoreFormula:
        if len({component.metric_name for component in self.components}) != len(self.components):
            raise ValueError("score metric names must be unique")
        if abs(sum(component.weight for component in self.components) - 1) > 1e-9:
            raise ValueError("score weights must sum to one")
        return self


class ScoreContribution(StrictModel):
    metric_name: str
    raw_value: float
    normalized_value: float = Field(ge=0, le=1)
    weight: float = Field(gt=0, le=1)
    points: float = Field(ge=0, le=100)


class QualityScore(StrictModel):
    kind: ScoreKind
    formula_version: str
    formula_status: Literal["draft_to_validate", "validated", "unavailable"]
    score: float | None = Field(default=None, ge=0, le=100)
    score_value: float | None = Field(default=None, ge=0, le=100)
    score_coverage: float = Field(default=0, ge=0, le=1)
    missing_components: list[str] = Field(default_factory=list)
    confidence: Literal["VERY_LOW", "LOW", "MEDIUM", "HIGH"] = "VERY_LOW"
    raw_metrics: list[RawScoreMetric]
    contributions: list[ScoreContribution]
    sensitivity_interval: tuple[float, float] | None
    unavailable_reasons: list[str]

    @model_validator(mode="after")
    def prevent_score_without_evidence(self) -> QualityScore:
        complete = all(metric.available for metric in self.raw_metrics)
        if self.score is not None and (not complete or self.unavailable_reasons):
            raise ValueError("computed scores require all raw metrics and no blockers")
        if self.score is not None and self.score_value != self.score:
            raise ValueError("a fully covered score and score_value must agree")
        if self.score_coverage == 0 and self.score_value is not None:
            raise ValueError("zero coverage cannot publish a partial score value")
        if self.score_coverage < 1 and self.score is not None:
            raise ValueError("legacy score is reserved for complete coverage")
        if self.score_coverage == 1 and self.missing_components:
            raise ValueError("complete coverage cannot retain missing components")
        return self


CandidateClassification = Literal[
    "STRONG_CANDIDATE",
    "CANDIDATE",
    "SPECULATIVE",
    "HIGH_RISK",
    "AVOID",
    "BLOCKED_INSUFFICIENT_DATA",
    "BLOCKED_CALIBRATION",
    "BLOCKED_EXECUTION",
    "BLOCKED_VALIDATION",
]


class FiveScoreReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    candidate_id: str
    opportunity: QualityScore
    risk: QualityScore
    evidence: QualityScore
    model_agreement: QualityScore
    execution_quality: QualityScore
    composite_score: Literal[None] = None
    classification: CandidateClassification
    classification_rule_version: str
    classification_status: Literal["draft_to_validate", "validated"]
    classification_rationale: list[str] = Field(default_factory=list)
    failed_constraints: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def require_distinct_score_kinds(self) -> FiveScoreReport:
        expected = [
            ScoreKind.OPPORTUNITY,
            ScoreKind.RISK,
            ScoreKind.EVIDENCE,
            ScoreKind.MODEL_AGREEMENT,
            ScoreKind.EXECUTION_QUALITY,
        ]
        actual = [
            self.opportunity.kind,
            self.risk.kind,
            self.evidence.kind,
            self.model_agreement.kind,
            self.execution_quality.kind,
        ]
        if actual != expected:
            raise ValueError("the five score dimensions must remain separate and ordered")
        return self


def _normalize(value: float, component: ScoreComponent) -> float:
    scaled = (value - component.lower_bound) / (component.upper_bound - component.lower_bound)
    bounded = min(max(scaled, 0), 1)
    return bounded if component.direction == "increasing" else 1 - bounded


def _required_value(metric: RawScoreMetric) -> float:
    if metric.value is None:
        raise ValueError(f"metric {metric.name} has no value")
    return metric.value


def calculate_quality_score(
    formula: ScoreFormula,
    metrics: list[RawScoreMetric],
    *,
    weight_perturbation: float = 0.10,
    confidence: Literal["VERY_LOW", "LOW", "MEDIUM", "HIGH"] | None = None,
) -> QualityScore:
    if not 0 <= weight_perturbation < 1:
        raise ValueError("weight perturbation must be in [0, 1)")
    by_name = {metric.name: metric for metric in metrics}
    reasons = [
        f"missing raw metric: {component.metric_name}"
        for component in formula.components
        if component.metric_name not in by_name or not by_name[component.metric_name].available
    ]
    formula_status: Literal["draft_to_validate", "validated", "unavailable"] = (
        "validated"
        if all(component.weight_status == "validated" for component in formula.components)
        else "draft_to_validate"
    )
    available_components = [
        component
        for component in formula.components
        if component.metric_name in by_name and by_name[component.metric_name].available
    ]
    coverage = sum(component.weight for component in available_components)
    if not available_components:
        return QualityScore(
            kind=formula.kind,
            formula_version=formula.version,
            formula_status=formula_status,
            score=None,
            score_value=None,
            score_coverage=0,
            missing_components=[component.metric_name for component in formula.components],
            confidence=confidence or "VERY_LOW",
            raw_metrics=metrics,
            contributions=[],
            sensitivity_interval=None,
            unavailable_reasons=reasons,
        )
    normalized = [
        _normalize(_required_value(by_name[component.metric_name]), component)
        for component in available_components
    ]
    contributions = [
        ScoreContribution(
            metric_name=component.metric_name,
            raw_value=_required_value(by_name[component.metric_name]),
            normalized_value=value,
            weight=component.weight,
            points=100 * value * component.weight,
        )
        for component, value in zip(available_components, normalized, strict=True)
    ]
    score_value = sum(item.points for item in contributions)
    candidates = [score_value]
    for index in range(len(available_components)):
        weights = [component.weight for component in available_components]
        weights[index] *= 1 + weight_perturbation
        original_total = sum(component.weight for component in available_components)
        perturbed_total = sum(weights)
        candidates.append(
            100
            * original_total
            * sum(
                value * weight / perturbed_total
                for value, weight in zip(normalized, weights, strict=True)
            )
        )
    resolved_confidence = confidence or (
        "HIGH"
        if coverage >= 0.90
        else "MEDIUM"
        if coverage >= 0.70
        else "LOW"
        if coverage >= 0.40
        else "VERY_LOW"
    )
    return QualityScore(
        kind=formula.kind,
        formula_version=formula.version,
        formula_status=formula_status,
        score=score_value if not reasons else None,
        score_value=score_value,
        score_coverage=coverage,
        missing_components=[
            component.metric_name
            for component in formula.components
            if component not in available_components
        ],
        confidence=resolved_confidence,
        raw_metrics=metrics,
        contributions=contributions,
        sensitivity_interval=(min(candidates), max(candidates)),
        unavailable_reasons=reasons,
    )


def classify_candidate(
    *,
    opportunity: float,
    risk: float,
    evidence: float,
    model_agreement: float,
    execution_quality: float,
    development_expected_return: float | None = None,
    uplift_vs_cash: float | None = None,
    evidence_coverage: float = 1.0,
    execution_coverage: float = 1.0,
) -> CandidateClassification:
    """Apply pre-opra-v2 rules to separate poor evidence from poor economics."""
    if risk >= 80:
        return "HIGH_RISK"
    if execution_coverage < 0.50:
        return "BLOCKED_EXECUTION"
    if (
        development_expected_return is not None
        and uplift_vs_cash is not None
        and development_expected_return <= 0
        and uplift_vs_cash <= 0
    ):
        return "AVOID"
    if opportunity < 30:
        return "AVOID"
    if evidence_coverage < 0.50:
        return "BLOCKED_VALIDATION"
    if execution_quality < 30:
        return "BLOCKED_EXECUTION"
    if evidence < 30 or model_agreement < 30:
        return "SPECULATIVE"
    if opportunity >= 75 and risk <= 40 and min(evidence, model_agreement, execution_quality) >= 70:
        return "STRONG_CANDIDATE"
    return "CANDIDATE"
