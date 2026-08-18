"""Deterministic observation-to-event normalization with auditable rule proofs."""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from take_two_options.intelligence.schemas import (
    DataDomain,
    EventNormalizationReport,
    EventNormalizationRule,
    HumanReviewStatus,
    NormalizedEvidenceEvent,
    UnifiedObservation,
)
from take_two_options.knowledge.provenance import stable_hash


def _matches(value: float | int | str | bool, rule: EventNormalizationRule) -> bool:
    threshold = rule.threshold
    if rule.operator == "greater_than":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and (
            float(value) > float(threshold)
        )
    if rule.operator == "less_than":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and (
            float(value) < float(threshold)
        )
    if rule.operator == "equals":
        return value == threshold
    if not isinstance(value, str) or not isinstance(threshold, str):
        return False
    tokens = {token.casefold() for token in threshold.split() if token.strip()}
    words = {token.strip(".,:;!?()[]{}\"'").casefold() for token in value.split()}
    return bool(tokens) and tokens.issubset(words)


def _canonical_fact(
    observation: UnifiedObservation,
    rule: EventNormalizationRule,
) -> str:
    selected_metadata = {
        key: observation.metadata.get(key)
        for key in rule.canonical_metadata_fields
    }
    identity = {
        "rule": rule.rule_id,
        "event_type": rule.event_type.value,
        "entity": rule.entity,
        "series": observation.series,
        "timestamp": observation.timestamp,
        "value": (
            observation.value.strip().casefold()
            if isinstance(observation.value, str)
            else observation.value
        ),
        "metadata": selected_metadata,
    }
    return f"fact-{stable_hash(identity)[:20]}"


def normalize_observations_to_events(
    observations: list[UnifiedObservation],
    rules: list[EventNormalizationRule],
    *,
    cutoff: datetime,
) -> EventNormalizationReport:
    """Create reviewable events without an LLM or implicit headline sentiment."""
    rule_proofs: dict[str, dict[str, Any]] = {}
    events: list[NormalizedEvidenceEvent] = []
    expired: list[str] = []
    unmatched: list[str] = []
    duplicate_observations: list[str] = []
    seen_raw_hashes: set[str] = set()
    fact_events: dict[str, str] = {}
    event_rule_groups: dict[str, str] = {}

    for observation in sorted(
        observations,
        key=lambda item: (item.timestamp, item.series, item.observation_id),
    ):
        if not observation.point_in_time_valid or observation.timestamp > cutoff:
            unmatched.append(observation.observation_id)
            continue
        if observation.raw_hash is not None and observation.raw_hash in seen_raw_hashes:
            duplicate_observations.append(observation.observation_id)
            continue
        if observation.raw_hash is not None:
            seen_raw_hashes.add(observation.raw_hash)
        matched_rule = False
        for rule in rules:
            if not fnmatch.fnmatchcase(observation.series, rule.series_pattern):
                continue
            if rule.expected_unit is not None and observation.unit != rule.expected_unit:
                continue
            if not _matches(observation.value, rule):
                continue
            matched_rule = True
            canonical_fact_id = _canonical_fact(observation, rule)
            event_id = (
                f"event-{stable_hash((observation.observation_id, rule.rule_id))[:20]}"
            )
            expires_at = observation.timestamp + timedelta(days=rule.ttl_days)
            if expires_at < cutoff:
                expired.append(event_id)
                continue
            text_requires_review = (
                isinstance(observation.value, str)
                or observation.domain is DataDomain.CATALYST
            )
            review_status = (
                HumanReviewStatus.PENDING
                if rule.requires_human_review or text_requires_review
                else HumanReviewStatus.NOT_REQUIRED
            )
            duplicate_cluster_id = fact_events.get(canonical_fact_id)
            fact_is_new = duplicate_cluster_id is None
            if duplicate_cluster_id is None:
                duplicate_cluster_id = f"duplicate-{stable_hash(canonical_fact_id)[:16]}"
                fact_events[canonical_fact_id] = duplicate_cluster_id
            event = NormalizedEvidenceEvent(
                event_id=event_id,
                event_type=rule.event_type,
                family=rule.family,
                occurred_at=observation.timestamp,
                observed_at=observation.retrieved_at or observation.timestamp,
                canonical_fact_id=canonical_fact_id,
                source_ids=[observation.source_id],
                confidence=rule.confidence,
                direction=rule.direction,
                entity=rule.entity,
                severity=rule.severity,
                novelty=1.0 if fact_is_new else 0.0,
                duplicate_cluster_id=duplicate_cluster_id,
                normalization_rule_id=rule.rule_id,
                human_review_status=review_status,
                quality_multiplier={
                    "official": 1.0,
                    "opra": 1.0,
                    "live_broker": 0.95,
                    "eod": 0.75,
                    "delayed": 0.65,
                    "indicative": 0.50,
                    "synthetic": 0.0,
                    "unknown": 0.0,
                }[observation.quality.value],
                freshness_multiplier=(
                    1.0
                    if observation.freshness_status.value == "fresh"
                    else 0.5
                    if observation.freshness_status.value == "stale"
                    else 0.0
                ),
                expires_at=expires_at,
                notes=[
                    "Deterministic rule match; no external LLM was used.",
                    (
                        "Human review is required before Bayesian impact."
                        if review_status is HumanReviewStatus.PENDING
                        else "Quantitative rule does not require human text interpretation."
                    ),
                ],
                metadata={
                    "observation_id": observation.observation_id,
                    "series": observation.series,
                    "unit": observation.unit,
                    "raw_hash": observation.raw_hash,
                },
            )
            events.append(event)
            event_rule_groups[event.event_id] = rule.contradiction_group or ""
            rule_proof = rule_proofs.setdefault(
                rule.rule_id,
                {
                    "normalization_rule_id": rule.rule_id,
                    "series_pattern": rule.series_pattern,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "matches": [],
                },
            )
            rule_proof["matches"].append(
                {
                    "event_id": event.event_id,
                    "observation_id": observation.observation_id,
                    "series": observation.series,
                    "observed_value": observation.value,
                    "source_id": observation.source_id,
                    "raw_hash": observation.raw_hash,
                    "human_review_status": review_status.value,
                }
            )
        if not matched_rule:
            unmatched.append(observation.observation_id)

    contradiction_members: dict[str, list[int]] = defaultdict(list)
    for index, event in enumerate(events):
        group = event_rule_groups.get(event.event_id)
        if group:
            contradiction_members[group].append(index)
    contradiction_clusters: dict[str, list[str]] = {}
    for group, indices in contradiction_members.items():
        directions = {events[index].direction for index in indices}
        if len(directions) < 2:
            continue
        cluster_id = f"contradiction-{stable_hash(group)[:16]}"
        event_ids = [events[index].event_id for index in indices]
        contradiction_clusters[cluster_id] = event_ids
        for index in indices:
            event = events[index]
            other_sources = sorted(
                {
                    source_id
                    for other_index in indices
                    if other_index != index
                    for source_id in events[other_index].source_ids
                }
            )
            events[index] = event.model_copy(
                update={
                    "contradiction_cluster_id": cluster_id,
                    "contradictory_source_ids": other_sources,
                    "human_review_status": HumanReviewStatus.PENDING,
                }
            )

    return EventNormalizationReport(
        cutoff=cutoff,
        events=events,
        duplicate_observation_ids=duplicate_observations,
        contradiction_clusters=contradiction_clusters,
        expired_event_ids=expired,
        unmatched_observation_ids=unmatched,
        rule_proofs=rule_proofs,
        warnings=[
            "Text and catalyst observations never affect Bayes before explicit human approval.",
            "Unmatched observations remain observations; they are not coerced into events.",
        ],
    )
