"""Point-in-time evidence and advisory sequential-decision contracts.

The module deliberately does not fit a Bayesian model and cannot execute an order.
It makes the assumptions needed by the configured belief updater inspectable.
"""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.intelligence.bayesian import update_heuristic_scenario_beliefs
from take_two_options.intelligence.schemas import (
    BayesianScenarioDistribution,
    EvidenceFamily,
    LikelihoodRule,
    NormalizedEvidenceEvent,
)


class ProbabilityOrigin(StrEnum):
    """Mutually exclusive semantics for scenario probability-like inputs."""

    USER_ASSUMPTION = "user_assumption"
    CONFIGURED_HEURISTIC = "configured_heuristic"
    HISTORICAL_ESTIMATE = "historical_estimate"
    MARKET_IMPLIED = "market_implied"
    EMPIRICALLY_CALIBRATED = "empirically_calibrated"


class EvidenceKind(StrEnum):
    OBSERVED_FACT = "observed_fact"
    HISTORICAL_ESTIMATE = "historical_estimate"
    USER_ASSUMPTION = "user_assumption"
    MODEL_INFERENCE = "model_inference"


class DependencyRelation(StrEnum):
    INDEPENDENT_ASSUMPTION = "independent_assumption"
    SAME_FACT = "same_fact"
    DERIVED_FROM = "derived_from"
    SHARED_DRIVER = "shared_driver"
    CONTRADICTS = "contradicts"


class ScenarioProbabilitySet(StrictModel):
    """Probability vector with mandatory uncertainty and provenance semantics."""

    set_id: str = Field(min_length=1)
    probabilities: dict[str, float]
    intervals: dict[str, tuple[float, float]]
    origin: ProbabilityOrigin
    as_of: datetime
    source_ids: list[str] = Field(min_length=1)
    uncertainty_diagnostic: str = Field(min_length=1)
    submitted_by: str | None = None
    configuration_hash: str | None = None
    dataset_hash: str | None = None
    experiment_manifest_hash: str | None = None
    calibration_report_hash: str | None = None
    sample_size: int | None = Field(default=None, ge=1)
    validation_partition: Literal["training", "validation", "final_holdout"] | None = None
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_semantics(self) -> ScenarioProbabilitySet:
        if not self.probabilities or set(self.probabilities) != set(self.intervals):
            raise ValueError("probabilities and intervals require the same non-empty scenarios")
        if any(
            not math.isfinite(value) or value < 0 or value > 1
            for value in self.probabilities.values()
        ):
            raise ValueError("scenario probabilities must be finite and bounded")
        if abs(sum(self.probabilities.values()) - 1.0) > 1e-8:
            raise ValueError("scenario probabilities must sum to one")
        for scenario, (lower, upper) in self.intervals.items():
            probability = self.probabilities[scenario]
            if not 0 <= lower <= probability <= upper <= 1:
                raise ValueError(f"invalid uncertainty interval for {scenario}")
        lowers = sum(bounds[0] for bounds in self.intervals.values())
        uppers = sum(bounds[1] for bounds in self.intervals.values())
        if lowers > 1 + 1e-8 or uppers < 1 - 1e-8:
            raise ValueError("probability intervals admit no vector summing to one")
        if self.origin is ProbabilityOrigin.USER_ASSUMPTION and not self.submitted_by:
            raise ValueError("user assumptions require submitted_by")
        if (
            self.origin is ProbabilityOrigin.CONFIGURED_HEURISTIC
            and not self.configuration_hash
        ):
            raise ValueError("configured heuristic probabilities require configuration_hash")
        if self.origin is ProbabilityOrigin.EMPIRICALLY_CALIBRATED:
            empirical_fields = (
                self.dataset_hash,
                self.experiment_manifest_hash,
                self.calibration_report_hash,
                self.sample_size,
                self.validation_partition,
            )
            if any(value is None for value in empirical_fields):
                raise ValueError("empirically calibrated probabilities require complete evidence")
            if self.validation_partition not in {"validation", "final_holdout"}:
                raise ValueError("calibrated probability evidence must be out of sample")
        elif self.origin is ProbabilityOrigin.HISTORICAL_ESTIMATE:
            if self.dataset_hash is None or self.sample_size is None:
                raise ValueError("historical estimates require dataset_hash and sample_size")
            if any(
                value is not None
                for value in (
                    self.experiment_manifest_hash,
                    self.calibration_report_hash,
                    self.validation_partition,
                )
            ):
                raise ValueError(
                    "historical estimates cannot carry calibrated OOS evidence fields"
                )
        elif any(
            value is not None
            for value in (
                self.dataset_hash,
                self.experiment_manifest_hash,
                self.calibration_report_hash,
                self.sample_size,
                self.validation_partition,
            )
        ):
            raise ValueError(
                "empirical calibration fields are reserved for empirically_calibrated sets"
            )
        return self


class EventEvidenceContract(StrictModel):
    """Binding between one normalized event and its decision-time assumptions."""

    event_id: str = Field(min_length=1)
    available_at: datetime
    decision_at: datetime
    evidence_kind: EvidenceKind
    source_ids: list[str] = Field(min_length=1)
    relation: DependencyRelation = DependencyRelation.INDEPENDENT_ASSUMPTION
    parent_event_ids: list[str] = Field(default_factory=list)
    dependence_multiplier: float = Field(default=1.0, ge=0, le=1)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_dependency_declaration(self) -> EventEvidenceContract:
        if self.available_at > self.decision_at:
            raise ValueError("evidence cannot be available after the decision cutoff")
        if self.event_id in self.parent_event_ids:
            raise ValueError("an event cannot depend on itself")
        if len(self.parent_event_ids) != len(set(self.parent_event_ids)):
            raise ValueError("parent event ids must be unique")
        if self.relation is DependencyRelation.INDEPENDENT_ASSUMPTION:
            if self.parent_event_ids or self.dependence_multiplier != 1:
                raise ValueError("independent evidence cannot have parents or a discount")
        elif not self.parent_event_ids:
            raise ValueError("dependent evidence requires at least one parent event")
        if self.relation in {DependencyRelation.SAME_FACT, DependencyRelation.DERIVED_FROM}:
            if self.dependence_multiplier != 0:
                raise ValueError("same-fact and derived evidence must be neutralized")
        if self.relation is DependencyRelation.SHARED_DRIVER and not (
            0 <= self.dependence_multiplier < 1
        ):
            raise ValueError("shared-driver evidence requires an explicit discount below one")
        return self


class SequentialEvidenceAudit(StrictModel):
    sequence: int = Field(ge=1)
    event_id: str
    available_at: datetime
    relation: DependencyRelation
    parent_event_ids: list[str]
    declared_multiplier: float = Field(ge=0, le=1)
    effective_novelty: float = Field(ge=0, le=1)
    accepted_for_update: bool
    reason: str


class SequentialBeliefReport(StrictModel):
    as_of: datetime
    distribution: BayesianScenarioDistribution
    probability_set: ScenarioProbabilitySet
    evidence_audit: list[SequentialEvidenceAudit]
    assumptions: list[str]
    order_capability: Literal["forbidden"] = "forbidden"


def _validate_evidence_graph(
    *,
    events: list[NormalizedEvidenceEvent],
    contracts: list[EventEvidenceContract],
    as_of: datetime,
) -> dict[str, EventEvidenceContract]:
    event_map = {event.event_id: event for event in events}
    if len(event_map) != len(events):
        raise ValueError("event ids must be unique")
    contract_map = {contract.event_id: contract for contract in contracts}
    if len(contract_map) != len(contracts) or set(contract_map) != set(event_map):
        raise ValueError("every event requires exactly one evidence contract")
    for event_id, contract in contract_map.items():
        event = event_map[event_id]
        if contract.decision_at != as_of:
            raise ValueError("all evidence contracts must use the requested decision cutoff")
        if contract.available_at != event.observed_at:
            raise ValueError("contract availability must equal the normalized observed_at")
        if set(contract.source_ids) != set(event.source_ids):
            raise ValueError("contract sources must match normalized event sources")
        for parent_id in contract.parent_event_ids:
            if parent_id not in event_map:
                raise ValueError(f"unknown parent event {parent_id}")
            if event_map[parent_id].observed_at > event.observed_at:
                raise ValueError("a dependency parent cannot become available after its child")
        if (
            contract.relation is DependencyRelation.CONTRADICTS
            and event.direction != "contradicts"
        ):
            raise ValueError("a contradiction dependency requires event direction=contradicts")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(event_id: str) -> None:
        if event_id in visiting:
            raise ValueError("event dependency graph must be acyclic")
        if event_id in visited:
            return
        visiting.add(event_id)
        for parent_id in contract_map[event_id].parent_event_ids:
            visit(parent_id)
        visiting.remove(event_id)
        visited.add(event_id)

    for event_id in contract_map:
        visit(event_id)
    return contract_map


def update_sequential_scenario_beliefs(
    *,
    priors: dict[str, float],
    events: list[NormalizedEvidenceEvent],
    evidence_contracts: list[EventEvidenceContract],
    rules: list[LikelihoodRule],
    family_caps: dict[EvidenceFamily, float],
    as_of: datetime,
    configuration_hash: str,
) -> SequentialBeliefReport:
    """Update configured beliefs after validating chronology and declared dependence."""
    contracts = _validate_evidence_graph(
        events=events,
        contracts=evidence_contracts,
        as_of=as_of,
    )
    adjusted: list[NormalizedEvidenceEvent] = []
    audit_inputs: list[
        tuple[int, NormalizedEvidenceEvent, EventEvidenceContract, float]
    ] = []
    for sequence, event in enumerate(
        sorted(events, key=lambda item: (item.observed_at, item.event_id)), start=1
    ):
        contract = contracts[event.event_id]
        effective_novelty = event.novelty * contract.dependence_multiplier
        changes: dict[str, Any] = {"novelty": effective_novelty}
        if contract.relation is DependencyRelation.CONTRADICTS:
            changes["contradiction_cluster_id"] = (
                event.contradiction_cluster_id or f"declared:{event.event_id}"
            )
        adjusted.append(event.model_copy(update=changes))
        audit_inputs.append((sequence, event, contract, effective_novelty))
    distribution = update_heuristic_scenario_beliefs(
        priors=priors,
        events=adjusted,
        rules=rules,
        family_caps=family_caps,
        as_of=as_of,
    )
    updates = {update.event_id: update for update in distribution.updates}
    audits: list[SequentialEvidenceAudit] = []
    for sequence, event, contract, effective_novelty in audit_inputs:
        update = updates.get(event.event_id)
        accepted = update is not None and update.effective_weight > 0
        reason = (
            "dependency_neutralized"
            if effective_novelty == 0
            else "no_compatible_likelihood_rule"
            if update is None
            else update.ignored_reason
            if update.ignored_reason is not None
            else "zero_after_caps_or_deduplication"
            if update.effective_weight == 0
            else "configured_update_applied"
        )
        audits.append(
            SequentialEvidenceAudit(
                sequence=sequence,
                event_id=event.event_id,
                available_at=contract.available_at,
                relation=contract.relation,
                parent_event_ids=contract.parent_event_ids,
                declared_multiplier=contract.dependence_multiplier,
                effective_novelty=effective_novelty,
                accepted_for_update=accepted,
                reason=reason,
            )
        )
    sensitivity = distribution.sensitivity
    intervals = {
        scenario: (
            sensitivity.posterior_minimum[scenario] if sensitivity else probability,
            sensitivity.posterior_maximum[scenario] if sensitivity else probability,
        )
        for scenario, probability in distribution.scenario_probabilities.items()
    }
    return SequentialBeliefReport(
        as_of=as_of,
        distribution=distribution,
        probability_set=ScenarioProbabilitySet(
            set_id=f"configured:{configuration_hash[:16]}:{as_of.isoformat()}",
            probabilities=distribution.scenario_probabilities,
            intervals=intervals,
            origin=ProbabilityOrigin.CONFIGURED_HEURISTIC,
            as_of=as_of,
            source_ids=sorted({source for event in events for source in event.source_ids}),
            uncertainty_diagnostic="Configured likelihood-weight sensitivity of ±25%.",
            configuration_hash=configuration_hash,
            assumptions=list(distribution.assumptions),
        ),
        evidence_audit=audits,
        assumptions=[
            "Declared independence is an assumption, not an empirically established fact.",
            "Same-fact and derived evidence contribute zero additional novelty.",
            "Shared-driver discounts are explicit human configuration, not fitted correlation.",
            "The result is advisory research output and cannot transmit an order.",
        ],
    )


class ResearchAdvisoryAction(StrEnum):
    RESEARCH_ELIGIBLE_NOW = "research_eligible_now"
    WAIT = "wait"
    NO_TRADE = "no_trade"
    REVALUE_ON_IV_THRESHOLD = "revalue_on_iv_threshold"
    REVALUE_AFTER_EVENT = "revalue_after_event"
    EXIT_REVIEW_PROFIT = "exit_review_profit"
    EXIT_REVIEW_STOP = "exit_review_stop"
    EXIT_REVIEW_INVALIDATION = "exit_review_invalidation"
    HOLD_UNTIL_REVIEW_DATE = "hold_until_review_date"
    ROLL_REVIEW = "roll_review"


class MetricCondition(StrictModel):
    metric: str = Field(min_length=1)
    operator: Literal["<", "<=", "==", ">=", ">"]
    threshold: float
    unit: str = Field(min_length=1)
    maximum_age_seconds: int | None = Field(default=None, ge=0)


class MetricObservation(StrictModel):
    metric: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    observed_at: datetime
    source_ids: list[str] = Field(min_length=1)


class SequentialResearchRule(StrictModel):
    rule_id: str = Field(min_length=1)
    conditions: list[MetricCondition] = Field(min_length=1)
    action_if_true: ResearchAdvisoryAction
    action_if_false: ResearchAdvisoryAction
    rationale: str = Field(min_length=1)
    human_confirmation_required: Literal[True] = True


class SequentialRuleEvaluation(StrictModel):
    rule_id: str
    as_of: datetime
    conditions_met: dict[str, bool]
    action: ResearchAdvisoryAction
    blockers: list[str]
    rationale: str
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


def evaluate_sequential_rule(
    rule: SequentialResearchRule,
    observations: list[MetricObservation],
    *,
    as_of: datetime,
) -> SequentialRuleEvaluation:
    """Evaluate a measurable research rule without scheduling or executing an action."""
    observation_map = {observation.metric: observation for observation in observations}
    if len(observation_map) != len(observations):
        raise ValueError("metric observations must be unique")
    comparisons = {
        "<": lambda value, threshold: value < threshold,
        "<=": lambda value, threshold: value <= threshold,
        "==": lambda value, threshold: value == threshold,
        ">=": lambda value, threshold: value >= threshold,
        ">": lambda value, threshold: value > threshold,
    }
    conditions_met: dict[str, bool] = {}
    blockers: list[str] = []
    for condition in rule.conditions:
        observation = observation_map.get(condition.metric)
        if observation is None:
            blockers.append(f"missing:{condition.metric}")
            conditions_met[condition.metric] = False
            continue
        if observation.observed_at > as_of:
            blockers.append(f"future:{condition.metric}")
            conditions_met[condition.metric] = False
            continue
        if observation.unit != condition.unit:
            blockers.append(f"unit_mismatch:{condition.metric}")
            conditions_met[condition.metric] = False
            continue
        age = (as_of - observation.observed_at).total_seconds()
        if condition.maximum_age_seconds is not None and age > condition.maximum_age_seconds:
            blockers.append(f"stale:{condition.metric}")
            conditions_met[condition.metric] = False
            continue
        conditions_met[condition.metric] = comparisons[condition.operator](
            observation.value, condition.threshold
        )
    passed = all(conditions_met.values()) and not blockers
    return SequentialRuleEvaluation(
        rule_id=rule.rule_id,
        as_of=as_of,
        conditions_met=conditions_met,
        action=rule.action_if_true if passed else rule.action_if_false,
        blockers=blockers,
        rationale=rule.rationale,
    )
