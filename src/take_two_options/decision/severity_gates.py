"""Severe-loss ladder, payoff severity and decision-gate sensitivity."""

from __future__ import annotations

import math
import random
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
    wilson_interval_95: tuple[float, float]
    bootstrap_interval_95: tuple[float, float]
    bootstrap_samples: int = Field(gt=0)


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


class OpportunityRiskFrontierPoint(StrictModel):
    candidate_id: str
    opportunity: float = Field(ge=0, le=100)
    risk: float = Field(ge=0, le=100)
    evidence: float = Field(ge=0, le=100)
    model_agreement: float | None = Field(default=None, ge=0, le=100)
    execution_quality: float = Field(ge=0, le=100)
    pareto_efficient: bool
    dominated_by: list[str]
    basis: str


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
    opportunity_risk_frontier: list[OpportunityRiskFrontierPoint] = Field(
        default_factory=list
    )
    no_position_frequency: float | None = Field(default=None, ge=0, le=1)
    sensitivity_interpretation: Literal[
        "candidate_pool_evaluated",
        "pipeline_blocked_empty_candidate_pool",
    ]
    blockers: list[str]
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"


def _wilson_interval(successes: int, observations: int) -> tuple[float, float]:
    z = 1.959963984540054
    probability = successes / observations
    denominator = 1.0 + z**2 / observations
    center = (probability + z**2 / (2 * observations)) / denominator
    half_width = (
        z
        * math.sqrt(
            probability * (1 - probability) / observations
            + z**2 / (4 * observations**2)
        )
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _bootstrap_probability_interval(
    indicators: list[bool], *, samples: int, seed: int
) -> tuple[float, float]:
    generator = random.Random(seed)
    observations = len(indicators)
    estimates = sorted(
        sum(indicators[generator.randrange(observations)] for _ in range(observations))
        / observations
        for _ in range(samples)
    )
    return (
        estimates[math.floor(0.025 * (samples - 1))],
        estimates[math.ceil(0.975 * (samples - 1))],
    )


def payoff_severity(
    returns: list[float], *, bootstrap_samples: int = 2_000, seed: int = 20_260_808
) -> PayoffSeverity:
    if not returns or any(not math.isfinite(value) or value < -1 for value in returns):
        raise ValueError("returns must be finite, non-empty and bounded below by -100%")
    if bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be positive")
    ladder = []
    for index, threshold in enumerate(LOSS_THRESHOLDS):
        indicators = [value < -threshold for value in returns]
        successes = sum(indicators)
        ladder.append(
            SevereLossPoint(
                loss_threshold=threshold,
                probability=successes / len(returns),
                observations=len(returns),
                wilson_interval_95=_wilson_interval(successes, len(returns)),
                bootstrap_interval_95=_bootstrap_probability_interval(
                    indicators, samples=bootstrap_samples, seed=seed + index
                ),
                bootstrap_samples=bootstrap_samples,
            )
        )
    return PayoffSeverity(
        observations=len(returns),
        mean_return=fmean(returns),
        median_return=median(returns),
        worst_return=min(returns),
        cvar_95_loss=conditional_value_at_risk(returns),
        probability_profit=sum(value > 0 for value in returns) / len(returns),
        severe_loss_ladder=ladder,
    )


def mark_pareto_frontier(
    points: list[OpportunityRiskFrontierPoint],
) -> list[OpportunityRiskFrontierPoint]:
    output = []
    for point in points:
        dominating = [
            other.candidate_id
            for other in points
            if other.candidate_id != point.candidate_id
            and other.opportunity >= point.opportunity
            and other.risk <= point.risk
            and (other.opportunity > point.opportunity or other.risk < point.risk)
        ]
        output.append(
            point.model_copy(
                update={"pareto_efficient": not dominating, "dominated_by": dominating}
            )
        )
    return output


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
