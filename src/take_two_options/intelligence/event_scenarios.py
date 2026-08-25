"""Configured event shocks and belief-sensitive candidate evaluation."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.intelligence.sequential_decision import ScenarioProbabilitySet


class ScenarioEvidenceStatus(StrEnum):
    USER_ASSUMPTION = "user_assumption"
    HISTORICAL_ESTIMATE = "historical_estimate"
    MARKET_IMPLIED = "market_implied"


class ShockDistributionSpec(StrictModel):
    distribution: Literal["fixed", "normal", "triangular", "empirical"]
    center: float
    scale: float = Field(default=0, ge=0)
    lower: float
    upper: float
    unit: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_distribution(self) -> ShockDistributionSpec:
        if not all(
            math.isfinite(value)
            for value in (self.center, self.scale, self.lower, self.upper)
        ):
            raise ValueError("shock parameters must be finite")
        if not self.lower <= self.center <= self.upper:
            raise ValueError("shock center must be inside its declared bounds")
        if self.distribution == "fixed" and (
            self.scale != 0 or self.lower != self.center or self.upper != self.center
        ):
            raise ValueError("a fixed shock must have zero scale and identical bounds")
        if self.distribution != "fixed" and self.scale <= 0:
            raise ValueError("non-fixed shocks require positive scale")
        return self


class RecoveryDynamics(StrictModel):
    shape: Literal["none", "linear", "exponential"]
    duration_days: int = Field(ge=0)
    terminal_fraction: float = Field(ge=0, le=1)
    half_life_days: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_recovery(self) -> RecoveryDynamics:
        if self.shape == "exponential" and self.half_life_days is None:
            raise ValueError("exponential recovery requires a half-life")
        if self.shape != "exponential" and self.half_life_days is not None:
            raise ValueError("half-life is reserved for exponential recovery")
        if self.shape == "none" and (self.duration_days != 0 or self.terminal_fraction != 1):
            raise ValueError("no-recovery dynamics must be instantaneous and persistent")
        return self


class EventScenarioDefinition(StrictModel):
    scenario_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    spot_shock: ShockDistributionSpec
    volatility_level_shock: ShockDistributionSpec
    skew_shock: ShockDistributionSpec
    curvature_shock: ShockDistributionSpec
    liquidity_shock: ShockDistributionSpec
    recovery: RecoveryDynamics
    evidence_status: ScenarioEvidenceStatus
    measure: Literal["P", "Q"]
    source_ids: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(min_length=1)
    historical_sample_size: int | None = Field(default=None, ge=1)
    user_assumption_owner: str | None = None

    @model_validator(mode="after")
    def validate_evidence_status(self) -> EventScenarioDefinition:
        if (
            self.evidence_status is ScenarioEvidenceStatus.HISTORICAL_ESTIMATE
            and self.historical_sample_size is None
        ):
            raise ValueError("historical estimates require a sample size")
        if (
            self.evidence_status is ScenarioEvidenceStatus.USER_ASSUMPTION
            and not self.user_assumption_owner
        ):
            raise ValueError("user assumptions require an owner")
        if self.evidence_status is ScenarioEvidenceStatus.MARKET_IMPLIED and self.measure != "Q":
            raise ValueError("market-implied scenarios must be tagged Q")
        return self


class EventScenarioSet(StrictModel):
    set_id: str = Field(min_length=1)
    scenarios: list[EventScenarioDefinition] = Field(min_length=1)
    beliefs: ScenarioProbabilitySet

    @model_validator(mode="after")
    def validate_scenario_set(self) -> EventScenarioSet:
        scenario_ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(scenario_ids) != len(set(scenario_ids)):
            raise ValueError("scenario ids must be unique")
        if set(scenario_ids) != set(self.beliefs.probabilities):
            raise ValueError("scenario definitions and belief probabilities must match")
        return self


class CandidateScenarioOutcome(StrictModel):
    candidate_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    pnl_usd: float
    return_fraction: float
    source_ids: list[str] = Field(min_length=1)


class CandidateBeliefMetrics(StrictModel):
    candidate_id: str
    expected_pnl_usd: float
    expected_pnl_interval_usd: tuple[float, float]
    target_probability: float = Field(ge=0, le=1)
    target_probability_interval: tuple[float, float]
    large_loss_probability: float = Field(ge=0, le=1)
    large_loss_probability_interval: tuple[float, float]
    worst_scenario_pnl_usd: float
    score: float
    reasons: list[str]


class EventScenarioEvaluationReport(StrictModel):
    scenario_set_id: str
    objective: Literal[
        "maximize_expected_pnl",
        "maximize_target_probability",
        "minimize_large_loss_probability",
        "robust_worst_case",
    ]
    target_return_fraction: float
    large_loss_fraction: float = Field(gt=0, le=1)
    candidates: list[CandidateBeliefMetrics]
    selected_candidate_id: str
    no_trade_selected: bool
    probability_origin: str
    uncertainty_diagnostic: str
    assumptions: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def _bounded_probability_extreme(
    values: dict[str, float],
    beliefs: ScenarioProbabilitySet,
    *,
    maximize: bool,
) -> float:
    allocation = {scenario: beliefs.intervals[scenario][0] for scenario in values}
    remaining = 1.0 - sum(allocation.values())
    ordered = sorted(values, key=values.get, reverse=maximize)  # type: ignore[arg-type]
    for scenario in ordered:
        capacity = beliefs.intervals[scenario][1] - allocation[scenario]
        increment = min(max(remaining, 0.0), capacity)
        allocation[scenario] += increment
        remaining -= increment
    if remaining > 1e-8:
        raise ValueError("probability intervals cannot form a normalized vector")
    return sum(allocation[scenario] * values[scenario] for scenario in values)


def evaluate_event_scenarios(
    scenario_set: EventScenarioSet,
    outcomes: list[CandidateScenarioOutcome],
    *,
    objective: Literal[
        "maximize_expected_pnl",
        "maximize_target_probability",
        "minimize_large_loss_probability",
        "robust_worst_case",
    ],
    target_return_fraction: float,
    large_loss_fraction: float,
) -> EventScenarioEvaluationReport:
    """Aggregate already-priced outcomes; this function never fabricates option values."""
    scenario_ids = set(scenario_set.beliefs.probabilities)
    by_candidate: dict[str, dict[str, CandidateScenarioOutcome]] = {}
    for outcome in outcomes:
        if outcome.scenario_id not in scenario_ids:
            raise ValueError(f"unknown scenario {outcome.scenario_id}")
        candidate = by_candidate.setdefault(outcome.candidate_id, {})
        if outcome.scenario_id in candidate:
            raise ValueError("candidate/scenario outcomes must be unique")
        candidate[outcome.scenario_id] = outcome
    if not by_candidate:
        raise ValueError("at least one priced candidate outcome is required")
    for candidate_id, candidate_outcomes in by_candidate.items():
        if set(candidate_outcomes) != scenario_ids:
            raise ValueError(f"candidate {candidate_id} lacks complete scenario outcomes")

    metrics: list[CandidateBeliefMetrics] = []
    for candidate_id, candidate_outcomes in by_candidate.items():
        pnl = {scenario: item.pnl_usd for scenario, item in candidate_outcomes.items()}
        target = {
            scenario: float(item.return_fraction >= target_return_fraction)
            for scenario, item in candidate_outcomes.items()
        }
        loss = {
            scenario: float(item.return_fraction <= -large_loss_fraction)
            for scenario, item in candidate_outcomes.items()
        }
        probabilities = scenario_set.beliefs.probabilities
        expected = sum(probabilities[scenario] * pnl[scenario] for scenario in scenario_ids)
        target_probability = sum(
            probabilities[scenario] * target[scenario] for scenario in scenario_ids
        )
        loss_probability = sum(
            probabilities[scenario] * loss[scenario] for scenario in scenario_ids
        )
        expected_interval = (
            _bounded_probability_extreme(pnl, scenario_set.beliefs, maximize=False),
            _bounded_probability_extreme(pnl, scenario_set.beliefs, maximize=True),
        )
        target_interval = (
            _bounded_probability_extreme(target, scenario_set.beliefs, maximize=False),
            _bounded_probability_extreme(target, scenario_set.beliefs, maximize=True),
        )
        loss_interval = (
            _bounded_probability_extreme(loss, scenario_set.beliefs, maximize=False),
            _bounded_probability_extreme(loss, scenario_set.beliefs, maximize=True),
        )
        worst = min(pnl.values())
        score = (
            expected
            if objective == "maximize_expected_pnl"
            else target_probability
            if objective == "maximize_target_probability"
            else -loss_probability
            if objective == "minimize_large_loss_probability"
            else worst
        )
        metrics.append(
            CandidateBeliefMetrics(
                candidate_id=candidate_id,
                expected_pnl_usd=expected,
                expected_pnl_interval_usd=expected_interval,
                target_probability=target_probability,
                target_probability_interval=target_interval,
                large_loss_probability=loss_probability,
                large_loss_probability_interval=loss_interval,
                worst_scenario_pnl_usd=worst,
                score=score,
                reasons=[
                    f"objective={objective}; score={score:.8g}",
                    f"belief_origin={scenario_set.beliefs.origin.value}",
                    "probability bounds optimize over all normalized vectors inside "
                    "declared intervals",
                ],
            )
        )
    # Cash/NO_TRADE is a contractual zero-PnL reference, not invented market data.
    if "NO_TRADE" not in by_candidate:
        metrics.append(
            CandidateBeliefMetrics(
                candidate_id="NO_TRADE",
                expected_pnl_usd=0,
                expected_pnl_interval_usd=(0, 0),
                target_probability=float(target_return_fraction <= 0),
                target_probability_interval=(
                    float(target_return_fraction <= 0),
                    float(target_return_fraction <= 0),
                ),
                large_loss_probability=0,
                large_loss_probability_interval=(0, 0),
                worst_scenario_pnl_usd=0,
                score=(
                    0
                    if objective != "maximize_target_probability"
                    else float(target_return_fraction <= 0)
                ),
                reasons=["Cash/NO_TRADE contractual zero-PnL reference."],
            )
        )
    ranked = sorted(
        metrics,
        key=lambda item: (item.score, item.candidate_id == "NO_TRADE"),
        reverse=True,
    )
    selected = ranked[0]
    return EventScenarioEvaluationReport(
        scenario_set_id=scenario_set.set_id,
        objective=objective,
        target_return_fraction=target_return_fraction,
        large_loss_fraction=large_loss_fraction,
        candidates=ranked,
        selected_candidate_id=selected.candidate_id,
        no_trade_selected=selected.candidate_id == "NO_TRADE",
        probability_origin=scenario_set.beliefs.origin.value,
        uncertainty_diagnostic=scenario_set.beliefs.uncertainty_diagnostic,
        assumptions=[
            "Scenario outcomes must be priced upstream with explicit execution costs.",
            "Belief sensitivity is not a statistical confidence interval unless its "
            "origin is empirically_calibrated.",
            "Selection is research-only and retains cash/NO_TRADE as a first-class alternative.",
        ],
    )


class BeliefSwitchThreshold(StrictModel):
    scenario_id: str
    candidate_a: str
    candidate_b: str
    probability_threshold: float | None = Field(default=None, ge=0, le=1)
    preferred_below: str | None
    preferred_above: str | None
    method: Literal["one_scenario_probability_with_proportional_residual"]
    assumptions: list[str]


def scenario_probability_switch_threshold(
    scenario_set: EventScenarioSet,
    outcomes: list[CandidateScenarioOutcome],
    *,
    scenario_id: str,
    candidate_a: str,
    candidate_b: str,
) -> BeliefSwitchThreshold:
    """Find the expected-PnL indifference belief for one scenario.

    Other scenario probabilities retain their central relative proportions.
    """
    probabilities = scenario_set.beliefs.probabilities
    if scenario_id not in probabilities:
        raise ValueError("unknown threshold scenario")
    outcome_map = {(item.candidate_id, item.scenario_id): item.pnl_usd for item in outcomes}
    required = {
        (candidate, scenario)
        for candidate in (candidate_a, candidate_b)
        for scenario in probabilities
    }
    if not required.issubset(outcome_map):
        raise ValueError("threshold analysis requires complete outcomes for both candidates")
    residual_base = 1.0 - probabilities[scenario_id]
    if residual_base <= 0:
        threshold = None
    else:
        focus_difference = (
            outcome_map[(candidate_a, scenario_id)]
            - outcome_map[(candidate_b, scenario_id)]
        )
        residual_difference = sum(
            probabilities[scenario]
            / residual_base
            * (outcome_map[(candidate_a, scenario)] - outcome_map[(candidate_b, scenario)])
            for scenario in probabilities
            if scenario != scenario_id
        )
        denominator = residual_difference - focus_difference
        candidate_threshold = (
            residual_difference / denominator if abs(denominator) > 1e-12 else math.nan
        )
        threshold = candidate_threshold if 0 <= candidate_threshold <= 1 else None

    def preferred(probability: float) -> str:
        if residual_base <= 0:
            return (
                candidate_a
                if outcome_map[(candidate_a, scenario_id)]
                >= outcome_map[(candidate_b, scenario_id)]
                else candidate_b
            )
        difference = probability * (
            outcome_map[(candidate_a, scenario_id)] - outcome_map[(candidate_b, scenario_id)]
        ) + (1 - probability) * sum(
            probabilities[scenario]
            / residual_base
            * (outcome_map[(candidate_a, scenario)] - outcome_map[(candidate_b, scenario)])
            for scenario in probabilities
            if scenario != scenario_id
        )
        return candidate_a if difference >= 0 else candidate_b

    return BeliefSwitchThreshold(
        scenario_id=scenario_id,
        candidate_a=candidate_a,
        candidate_b=candidate_b,
        probability_threshold=threshold,
        preferred_below=preferred(0) if threshold is not None else None,
        preferred_above=preferred(1) if threshold is not None else None,
        method="one_scenario_probability_with_proportional_residual",
        assumptions=[
            "Only the selected scenario belief varies.",
            "All other beliefs retain their central relative proportions.",
            "Priced scenario PnLs remain fixed while beliefs vary.",
        ],
    )
