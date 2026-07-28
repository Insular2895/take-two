"""Auditable Bayesian updates with evidence-family caps and fact deduplication."""

from __future__ import annotations

import math

from take_two_options.intelligence.schemas import (
    BayesianScenarioDistribution,
    BayesianUpdateRecord,
    EvidenceFamily,
    LikelihoodRule,
    NormalizedEvidenceEvent,
)


def _normalized(values: dict[str, float]) -> dict[str, float]:
    total = sum(values.values())
    if total <= 0 or not math.isfinite(total):
        raise ValueError("Bayesian mass must remain finite and positive")
    return {key: value / total for key, value in values.items()}


def update_scenario_distribution(
    *,
    priors: dict[str, float],
    events: list[NormalizedEvidenceEvent],
    rules: list[LikelihoodRule],
    family_caps: dict[EvidenceFamily, float],
) -> BayesianScenarioDistribution:
    """Apply fractional Bayes factors while preventing duplicate-news amplification."""
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
        if set(rule.likelihood_by_scenario) != set(posterior):
            raise ValueError(f"likelihood scenarios do not match priors for {event.event_id}")
        deduplicated = event.canonical_fact_id in used_facts
        requested_weight = (
            0.0
            if event.direction == "neutral"
            else rule.base_weight * event.confidence
        )
        remaining_family_weight = max(
            family_caps.get(event.family, 0.0) - family_used[event.family],
            0.0,
        )
        effective_weight = (
            0.0
            if deduplicated
            else min(requested_weight, remaining_family_weight)
        )
        family_cap_applied = effective_weight + 1e-12 < requested_weight and not deduplicated
        likelihoods = dict(rule.likelihood_by_scenario)
        if event.direction == "contradicts":
            likelihoods = {
                scenario: max(1.0 - likelihood, 1e-6)
                for scenario, likelihood in likelihoods.items()
            }
        prior = dict(posterior)
        if effective_weight > 0:
            posterior = _normalized(
                {
                    scenario: probability
                    * likelihoods[scenario] ** effective_weight
                    for scenario, probability in posterior.items()
                }
            )
            family_used[event.family] += effective_weight
            used_facts.add(event.canonical_fact_id)
        elif deduplicated:
            ignored.append(event.event_id)
        updates.append(
            BayesianUpdateRecord(
                sequence=len(updates) + 1,
                event_id=event.event_id,
                canonical_fact_id=event.canonical_fact_id,
                family=event.family,
                prior=prior,
                likelihoods=likelihoods,
                requested_weight=requested_weight,
                effective_weight=effective_weight,
                posterior=dict(posterior),
                confidence=event.confidence,
                deduplicated=deduplicated,
                family_cap_applied=family_cap_applied,
                contradictory_source_ids=event.contradictory_source_ids,
            )
        )
    return BayesianScenarioDistribution(
        scenario_probabilities=posterior,
        updates=updates,
        family_weight_used=family_used,
        ignored_event_ids=ignored,
        assumptions=[
            "Likelihoods and priors are explicit configuration inputs, not learned truth.",
            "Repeated reports with the same canonical_fact_id count once.",
            "Each evidence family has a cumulative fractional-weight cap.",
            "Posterior probabilities support research; they do not authorize execution.",
        ],
    )
