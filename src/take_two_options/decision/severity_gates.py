"""Severe-loss ladder, payoff severity and decision-gate sensitivity."""

from __future__ import annotations

import math
from statistics import fmean, median
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.research_statistics import conditional_value_at_risk

LOSS_THRESHOLDS = (0.10, 0.25, 0.50, 0.70, 0.90, 0.99)


class SevereLossPoint(StrictModel):
    loss_threshold: float = Field(gt=0, le=1)
    probability: float = Field(ge=0, le=1)
    observations: int = Field(gt=0)


class PayoffSeverity(StrictModel):
    observations: int = Field(gt=0)
    mean_return: float
    median_return: float
    worst_return: float = Field(ge=-1)
    cvar_95_loss: float = Field(ge=0)
    probability_profit: float = Field(ge=0, le=1)
    severe_loss_ladder: list[SevereLossPoint] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def require_fixed_ladder(self) -> PayoffSeverity:
        if tuple(point.loss_threshold for point in self.severe_loss_ladder) != LOSS_THRESHOLDS:
            raise ValueError("severe loss ladder thresholds are fixed and ordered")
        probabilities = [point.probability for point in self.severe_loss_ladder]
        if any(
            left < right
            for left, right in zip(probabilities, probabilities[1:], strict=False)
        ):
            raise ValueError("loss probabilities must not increase with severity")
        return self


class FailedGate(StrictModel):
    name: str
    actual: float | None
    required: float | None
    direction: Literal["minimum", "maximum", "availability"]
    distance: float | None
    status: Literal["failed", "unavailable"]


class BestBlockedCandidate(StrictModel):
    candidate_id: str
    selection_status: Literal["identified", "unavailable"]
    selection_basis: str
    opportunity_score: float | None = Field(default=None, ge=0, le=100)
    failed_gates: list[FailedGate] = Field(min_length=1)


class CandidateGateInput(StrictModel):
    candidate_id: str
    opportunity_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    evidence_score: float = Field(ge=0, le=100)
    execution_quality_score: float = Field(ge=0, le=100)


class GateSetting(StrictModel):
    setting_id: str
    minimum_opportunity: float = Field(ge=0, le=100)
    maximum_risk: float = Field(ge=0, le=100)
    minimum_evidence: float = Field(ge=0, le=100)
    minimum_execution_quality: float = Field(ge=0, le=100)
    status: Literal["draft_to_validate", "validated"]


class GateSensitivityRow(StrictModel):
    setting: GateSetting
    passing_candidate_ids: list[str]
    best_candidate_id: str | None
    no_position_recommended: bool


class SeverityGateReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    status: Literal[
        "DEVELOPMENT_ANALYSIS_READY",
        "FIXTURE_ONLY_NOT_VALIDATED",
        "BLOCKED_NO_CANDIDATE_DISTRIBUTION",
    ]
    candidate_id: str | None
    payoff_severity: PayoffSeverity | None
    best_blocked_candidate: BestBlockedCandidate
    gate_sensitivity: list[GateSensitivityRow]
    no_position_frequency: float | None = Field(default=None, ge=0, le=1)
    sensitivity_interpretation: Literal[
        "candidate_pool_evaluated",
        "pipeline_blocked_empty_candidate_pool",
    ]
    blockers: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"


def payoff_severity(returns: list[float]) -> PayoffSeverity:
    if not returns or any(not math.isfinite(value) or value < -1 for value in returns):
        raise ValueError("returns must be finite, non-empty and bounded below by -100%")
    return PayoffSeverity(
        observations=len(returns),
        mean_return=fmean(returns),
        median_return=median(returns),
        worst_return=min(returns),
        cvar_95_loss=conditional_value_at_risk(returns),
        probability_profit=sum(value > 0 for value in returns) / len(returns),
        severe_loss_ladder=[
            SevereLossPoint(
                loss_threshold=threshold,
                probability=sum(value < -threshold for value in returns) / len(returns),
                observations=len(returns),
            )
            for threshold in LOSS_THRESHOLDS
        ],
    )


def evaluate_gate_sensitivity(
    candidates: list[CandidateGateInput], settings: list[GateSetting]
) -> tuple[list[GateSensitivityRow], float | None]:
    rows: list[GateSensitivityRow] = []
    for setting in settings:
        passing = [
            candidate
            for candidate in candidates
            if candidate.opportunity_score >= setting.minimum_opportunity
            and candidate.risk_score <= setting.maximum_risk
            and candidate.evidence_score >= setting.minimum_evidence
            and candidate.execution_quality_score >= setting.minimum_execution_quality
        ]
        ordered = sorted(
            passing,
            key=lambda candidate: (
                -candidate.opportunity_score,
                candidate.risk_score,
                candidate.candidate_id,
            ),
        )
        rows.append(
            GateSensitivityRow(
                setting=setting,
                passing_candidate_ids=[candidate.candidate_id for candidate in ordered],
                best_candidate_id=ordered[0].candidate_id if ordered else None,
                no_position_recommended=not ordered,
            )
        )
    frequency = sum(row.no_position_recommended for row in rows) / len(rows) if rows else None
    return rows, frequency
