"""Auditable configured belief updates; not a fitted Bayesian probability model."""

from __future__ import annotations

import math
from datetime import datetime

from take_two_options.intelligence.schemas import (
    BayesianScenarioDistribution,
    BayesianSensitivityReport,
    BayesianUpdateRecord,
    EvidenceFamily,
    HumanReviewStatus,
    LikelihoodRule,
    NormalizedEvidenceEvent,
)


def _normalized(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0 or not math.isfinite(total):
        raise ValueError("Bayesian mass must remain finite and positive")
    return {key: value / total for key, value in values.items()}


def _sensitivity_posterior(
    *,
    priors: dict[str, float],
    events: list[NormalizedEvidenceEvent],
    rules: list[LikelihoodRule],
    family_caps: dict[EvidenceFamily, float],
    weight_scale: float,
    as_of: datetime | None,
) -> dict[str, float]:
    posterior = _normalized(dict(priors))
    rule_map = {(rule.event_type, rule.family): rule for rule in rules}
    used_facts: set[str] = set()
    family_used = {family: 0.0 for family in EvidenceFamily}
    for event in sorted(events, key=lambda item: (item.observed_at, item.event_id)):
        rule = rule_map.get((event.event_type, event.family))
        if (
            rule is None
            or event.human_review_status in {HumanReviewStatus.PENDING, HumanReviewStatus.REJECTED}
            or (as_of is not None and event.observed_at > as_of)
            or (as_of is not None and event.expires_at is not None and event.expires_at < as_of)
            or event.canonical_fact_id in used_facts
            or event.direction == "neutral"
        ):
            continue
        contradiction_confidence = (
            event.confidence * 0.5
            if event.contradictory_source_ids or event.contradiction_cluster_id
            else event.confidence
        )
        raw_weight = rule.base_weight * contradiction_confidence * event.novelty * weight_scale
        weighted = raw_weight * event.quality_multiplier * event.freshness_multiplier
        remaining = max(
            family_caps.get(event.family, 0.0) - family_used[event.family],
            0.0,
        )
        effective = min(weighted, remaining, 1.0)
        if effective <= 0:
            continue
        likelihoods = dict(rule.likelihood_by_scenario)
        if event.direction == "contradicts":
            likelihoods = {
                scenario: max(1.0 - likelihood, 1e-6)
                for scenario, likelihood in likelihoods.items()
            }
        posterior = _normalized(
            {
                scenario: probability * likelihoods[scenario] ** effective
                for scenario, probability in posterior.items()
            }
        )
        family_used[event.family] += effective
        used_facts.add(event.canonical_fact_id)
    return posterior


def update_heuristic_scenario_beliefs(
    *,
    priors: dict[str, float],
    events: list[NormalizedEvidenceEvent],
    rules: list[LikelihoodRule],
    family_caps: dict[EvidenceFamily, float],
    as_of: datetime | None = None,
) -> BayesianScenarioDistribution:
    """Apply configured fractional weights while preventing duplicate-news amplification."""
    posterior = _normalized(dict(priors))
    rule_map = {(rule.event_type, rule.family): rule for rule in rules}
    used_facts: set[str] = set()
    family_used = {family: 0.0 for family in EvidenceFamily}
    ignored: list[str] = []
    updates: list[BayesianUpdateRecord] = []
    ordered_events = sorted(events, key=lambda item: (item.observed_at, item.event_id))
    for event in ordered_events:
        rule = rule_map.get((event.event_type, event.family))
        if rule is None:
            ignored.append(event.event_id)
            continue
        ignored_reason: str | None = None
        if event.human_review_status in {
            HumanReviewStatus.PENDING,
            HumanReviewStatus.REJECTED,
        }:
            ignored_reason = f"human_review_{event.human_review_status.value}"
        elif as_of is not None and event.observed_at > as_of:
            ignored_reason = "observed_after_cutoff"
        elif as_of is not None and event.expires_at is not None and event.expires_at < as_of:
            ignored_reason = "event_expired"
        if set(rule.likelihood_by_scenario) != set(posterior):
            raise ValueError(f"likelihood scenarios do not match priors for {event.event_id}")
        deduplicated = event.canonical_fact_id in used_facts
        confidence_after_contradiction = (
            event.confidence * 0.5
            if event.contradictory_source_ids or event.contradiction_cluster_id
            else event.confidence
        )
        requested_weight = (
            0.0 if event.direction == "neutral" else rule.base_weight * event.confidence
        )
        raw_weight = (
            0.0
            if ignored_reason is not None or event.direction == "neutral"
            else rule.base_weight * confidence_after_contradiction * event.novelty
        )
        weight_after_quality = raw_weight * event.quality_multiplier
        weight_after_freshness = weight_after_quality * event.freshness_multiplier
        weight_after_deduplication = 0.0 if deduplicated else weight_after_freshness
        family_cap = family_caps.get(event.family, 0.0)
        remaining_family_weight = max(
            family_cap - family_used[event.family],
            0.0,
        )
        effective_weight = (
            0.0
            if ignored_reason is not None
            else min(weight_after_deduplication, remaining_family_weight)
        )
        family_cap_applied = (
            effective_weight + 1e-12 < weight_after_deduplication
            and not deduplicated
            and ignored_reason is None
        )
        likelihoods = dict(rule.likelihood_by_scenario)
        if event.direction == "contradicts":
            likelihoods = {
                scenario: max(1.0 - likelihood, 1e-6)
                for scenario, likelihood in likelihoods.items()
            }
        likelihood_mean = sum(likelihoods.values()) / len(likelihoods)
        likelihood_ratios = {
            scenario: likelihood / max(likelihood_mean, 1e-12)
            for scenario, likelihood in likelihoods.items()
        }
        prior = dict(posterior)
        unnormalized = {
            scenario: probability * likelihoods[scenario] ** effective_weight
            for scenario, probability in posterior.items()
        }
        if effective_weight > 0:
            posterior = _normalized(unnormalized)
            family_used[event.family] += effective_weight
            used_facts.add(event.canonical_fact_id)
        elif deduplicated or ignored_reason is not None:
            ignored.append(event.event_id)
        updates.append(
            BayesianUpdateRecord(
                sequence=len(updates) + 1,
                event_id=event.event_id,
                canonical_fact_id=event.canonical_fact_id,
                family=event.family,
                prior=prior,
                likelihoods=likelihoods,
                likelihood_ratios=likelihood_ratios,
                requested_weight=requested_weight,
                raw_weight=raw_weight,
                weight_after_quality=weight_after_quality,
                weight_after_freshness=weight_after_freshness,
                weight_after_deduplication=weight_after_deduplication,
                family_cap=family_cap,
                effective_weight=effective_weight,
                unnormalized_posterior=unnormalized,
                posterior=dict(posterior),
                probability_delta={
                    scenario: posterior[scenario] - prior[scenario] for scenario in posterior
                },
                confidence=event.confidence,
                confidence_after_contradiction=confidence_after_contradiction,
                deduplicated=deduplicated,
                family_cap_applied=family_cap_applied,
                ignored_reason=ignored_reason,
                justification=(
                    "No automatic impact: " + ignored_reason
                    if ignored_reason is not None
                    else "Deterministic configured likelihood update with quality, "
                    "freshness, deduplication, and family-cap controls."
                ),
                rule_id=(rule.rule_id or f"likelihood:{rule.event_type.value}:{rule.family.value}"),
                contradictory_source_ids=event.contradictory_source_ids,
            )
        )
    low = _sensitivity_posterior(
        priors=priors,
        events=events,
        rules=rules,
        family_caps=family_caps,
        weight_scale=0.75,
        as_of=as_of,
    )
    high = _sensitivity_posterior(
        priors=priors,
        events=events,
        rules=rules,
        family_caps=family_caps,
        weight_scale=1.25,
        as_of=as_of,
    )
    minimum = {
        scenario: min(low[scenario], posterior[scenario], high[scenario]) for scenario in posterior
    }
    maximum = {
        scenario: max(low[scenario], posterior[scenario], high[scenario]) for scenario in posterior
    }
    rankings = [
        tuple(
            sorted(
                distribution,
                key=lambda scenario: distribution[scenario],
                reverse=True,
            )
        )
        for distribution in (low, posterior, high)
    ]
    unique_effective_events = sum(update.effective_weight > 0 for update in updates)
    evidence_sufficiency_level = (
        "high"
        if unique_effective_events >= 5
        and not any(update.contradictory_source_ids for update in updates)
        else "medium"
        if unique_effective_events >= 2
        else "low"
    )
    return BayesianScenarioDistribution(
        scenario_probabilities=posterior,
        updates=updates,
        family_weight_used=family_used,
        ignored_event_ids=ignored,
        sensitivity=BayesianSensitivityReport(
            posterior_minimum=minimum,
            posterior_central=posterior,
            posterior_maximum=maximum,
            likelihood_weight_range=(0.75, 1.25),
            maximum_probability_swing=max(
                maximum[scenario] - minimum[scenario] for scenario in posterior
            ),
            ranking_stable=len(set(rankings)) == 1,
            warnings=[
                "Sensitivity bounds vary configured likelihood weight by ±25%; "
                "they are not statistical confidence intervals."
            ],
        ),
        confidence_level=evidence_sufficiency_level,
        assumptions=[
            "This is a configured heuristic belief distribution, not a fitted "
            "statistical posterior.",
            "Likelihood-like scores and priors are explicit inputs, not learned truth.",
            "Repeated reports with the same canonical_fact_id count once.",
            "Each evidence family has a cumulative fractional-weight cap.",
            "Posterior probabilities support research; they do not authorize execution.",
        ],
    )


def update_scenario_distribution(
    *,
    priors: dict[str, float],
    events: list[NormalizedEvidenceEvent],
    rules: list[LikelihoodRule],
    family_caps: dict[EvidenceFamily, float],
    as_of: datetime | None = None,
) -> BayesianScenarioDistribution:
    """Backward-compatible alias for :func:`update_heuristic_scenario_beliefs`."""

    return update_heuristic_scenario_beliefs(
        priors=priors,
        events=events,
        rules=rules,
        family_caps=family_caps,
        as_of=as_of,
    )
