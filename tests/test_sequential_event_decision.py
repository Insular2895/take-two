from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from take_two_options.intelligence.event_scenarios import (
    CandidateScenarioOutcome,
    EventScenarioDefinition,
    EventScenarioSet,
    RecoveryDynamics,
    ScenarioEvidenceStatus,
    ShockDistributionSpec,
    evaluate_event_scenarios,
    scenario_probability_switch_threshold,
)
from take_two_options.intelligence.schemas import (
    EvidenceFamily,
    LikelihoodRule,
    NormalizedEventType,
    NormalizedEvidenceEvent,
)
from take_two_options.intelligence.sequential_decision import (
    DependencyRelation,
    EventEvidenceContract,
    EvidenceKind,
    MetricCondition,
    MetricObservation,
    ProbabilityOrigin,
    ResearchAdvisoryAction,
    ScenarioProbabilitySet,
    SequentialResearchRule,
    evaluate_sequential_rule,
    update_sequential_scenario_beliefs,
)

NOW = datetime(2026, 8, 8, 12, tzinfo=UTC)


def _event(event_id: str, minute: int, *, direction: str = "supports") -> NormalizedEvidenceEvent:
    timestamp = NOW - timedelta(minutes=10 - minute)
    return NormalizedEvidenceEvent(
        event_id=event_id,
        event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
        family=EvidenceFamily.NEWS,
        occurred_at=timestamp,
        observed_at=timestamp,
        canonical_fact_id=f"fact-{event_id}",
        source_ids=[f"source-{event_id}"],
        confidence=0.8,
        direction=direction,
    )


def _contract(
    event: NormalizedEvidenceEvent,
    *,
    relation: DependencyRelation = DependencyRelation.INDEPENDENT_ASSUMPTION,
    parents: list[str] | None = None,
    multiplier: float = 1,
) -> EventEvidenceContract:
    return EventEvidenceContract(
        event_id=event.event_id,
        available_at=event.observed_at,
        decision_at=NOW,
        evidence_kind=EvidenceKind.OBSERVED_FACT,
        source_ids=event.source_ids,
        relation=relation,
        parent_event_ids=parents or [],
        dependence_multiplier=multiplier,
        rationale="Synthetic dependency declaration for invariant testing.",
    )


def _rule() -> LikelihoodRule:
    return LikelihoodRule(
        rule_id="trailer-news-v1",
        event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
        family=EvidenceFamily.NEWS,
        likelihood_by_scenario={"success": 0.8, "delay": 0.2},
        base_weight=0.5,
    )


def test_point_in_time_dependency_contract_neutralizes_derived_news() -> None:
    original = _event("original", 1)
    rewrite = _event("rewrite", 2)
    report = update_sequential_scenario_beliefs(
        priors={"success": 0.5, "delay": 0.5},
        events=[rewrite, original],
        evidence_contracts=[
            _contract(original),
            _contract(
                rewrite,
                relation=DependencyRelation.DERIVED_FROM,
                parents=[original.event_id],
                multiplier=0,
            ),
        ],
        rules=[_rule()],
        family_caps={EvidenceFamily.NEWS: 1},
        as_of=NOW,
        configuration_hash="a" * 64,
    )
    assert [item.event_id for item in report.evidence_audit] == ["original", "rewrite"]
    assert report.evidence_audit[1].reason == "dependency_neutralized"
    assert report.distribution.updates[1].effective_weight == 0
    assert report.probability_set.origin is ProbabilityOrigin.CONFIGURED_HEURISTIC
    assert report.order_capability == "forbidden"


def test_dependency_graph_rejects_future_availability_and_cycles() -> None:
    event_a = _event("a", 1)
    event_b = _event("b", 1)
    with pytest.raises(ValidationError, match="after the decision cutoff"):
        EventEvidenceContract(
            event_id="future",
            available_at=NOW + timedelta(seconds=1),
            decision_at=NOW,
            evidence_kind=EvidenceKind.OBSERVED_FACT,
            source_ids=["source"],
            rationale="Must fail closed.",
        )
    with pytest.raises(ValueError, match="acyclic"):
        update_sequential_scenario_beliefs(
            priors={"success": 0.5, "delay": 0.5},
            events=[event_a, event_b],
            evidence_contracts=[
                _contract(
                    event_a,
                    relation=DependencyRelation.SHARED_DRIVER,
                    parents=["b"],
                    multiplier=0.5,
                ),
                _contract(
                    event_b,
                    relation=DependencyRelation.SHARED_DRIVER,
                    parents=["a"],
                    multiplier=0.5,
                ),
            ],
            rules=[_rule()],
            family_caps={EvidenceFamily.NEWS: 1},
            as_of=NOW,
            configuration_hash="b" * 64,
        )


def test_probability_origin_cannot_claim_calibration_without_oos_evidence() -> None:
    base = dict(
        set_id="beliefs",
        probabilities={"success": 0.6, "delay": 0.4},
        intervals={"success": (0.4, 0.8), "delay": (0.2, 0.6)},
        as_of=NOW,
        source_ids=["user-form"],
        uncertainty_diagnostic="User-entered sensitivity range; not a confidence interval.",
    )
    with pytest.raises(ValidationError, match="complete evidence"):
        ScenarioProbabilitySet(
            **base,
            origin=ProbabilityOrigin.EMPIRICALLY_CALIBRATED,
        )
    user = ScenarioProbabilitySet(
        **base,
        origin=ProbabilityOrigin.USER_ASSUMPTION,
        submitted_by="researcher",
    )
    assert user.origin is ProbabilityOrigin.USER_ASSUMPTION
    historical = ScenarioProbabilitySet(
        **base,
        origin=ProbabilityOrigin.HISTORICAL_ESTIMATE,
        dataset_hash="c" * 64,
        sample_size=12,
    )
    assert historical.calibration_report_hash is None


def _fixed(center: float, unit: str) -> ShockDistributionSpec:
    return ShockDistributionSpec(
        distribution="fixed",
        center=center,
        scale=0,
        lower=center,
        upper=center,
        unit=unit,
        source_ids=["synthetic-fixture"],
    )


def _scenario_set() -> EventScenarioSet:
    beliefs = ScenarioProbabilitySet(
        set_id="user-sensitivity-v1",
        probabilities={"launch": 0.4, "delay": 0.6},
        intervals={"launch": (0.2, 0.7), "delay": (0.3, 0.8)},
        origin=ProbabilityOrigin.USER_ASSUMPTION,
        as_of=NOW,
        source_ids=["user-form"],
        uncertainty_diagnostic="User sensitivity bounds; not empirical confidence intervals.",
        submitted_by="researcher",
    )
    scenarios = [
        EventScenarioDefinition(
            scenario_id=scenario_id,
            event_type=scenario_id,
            spot_shock=_fixed(spot, "return_fraction"),
            volatility_level_shock=_fixed(iv, "volatility_point"),
            skew_shock=_fixed(0, "total_variance_slope"),
            curvature_shock=_fixed(0, "total_variance_curvature"),
            liquidity_shock=_fixed(0.1, "relative_spread_change"),
            recovery=RecoveryDynamics(shape="none", duration_days=0, terminal_fraction=1),
            evidence_status=ScenarioEvidenceStatus.USER_ASSUMPTION,
            measure="P",
            source_ids=["user-form"],
            assumptions=["Synthetic phase-8 example; not a TTWO forecast."],
            user_assumption_owner="researcher",
        )
        for scenario_id, spot, iv in [("launch", 0.25, 0.05), ("delay", -0.2, 0.15)]
    ]
    return EventScenarioSet(set_id="events-v1", scenarios=scenarios, beliefs=beliefs)


def _outcomes() -> list[CandidateScenarioOutcome]:
    return [
        CandidateScenarioOutcome(
            candidate_id=candidate,
            scenario_id=scenario,
            pnl_usd=pnl,
            return_fraction=ret,
            source_ids=["synthetic-pricer"],
        )
        for candidate, scenario, pnl, ret in [
            ("call", "launch", 200, 2.0),
            ("call", "delay", -100, -1.0),
            ("spread", "launch", 80, 0.8),
            ("spread", "delay", -20, -0.2),
        ]
    ]


def test_event_scenario_evaluation_propagates_belief_bounds_and_no_trade() -> None:
    report = evaluate_event_scenarios(
        _scenario_set(),
        _outcomes(),
        objective="maximize_expected_pnl",
        target_return_fraction=0.9,
        large_loss_fraction=0.7,
    )
    call = next(item for item in report.candidates if item.candidate_id == "call")
    assert call.expected_pnl_usd == pytest.approx(20)
    assert call.expected_pnl_interval_usd == pytest.approx((-40, 110))
    assert call.target_probability_interval == pytest.approx((0.2, 0.7))
    assert call.large_loss_probability_interval == pytest.approx((0.3, 0.8))
    assert report.selected_candidate_id == "call"
    assert any(item.candidate_id == "NO_TRADE" for item in report.candidates)


def test_belief_switch_threshold_is_analytic_and_explicit() -> None:
    threshold = scenario_probability_switch_threshold(
        _scenario_set(),
        _outcomes(),
        scenario_id="launch",
        candidate_a="call",
        candidate_b="spread",
    )
    assert threshold.probability_threshold == pytest.approx(0.4)
    assert threshold.preferred_below == "spread"
    assert threshold.preferred_above == "call"


def test_sequential_rule_is_point_in_time_measurable_and_advisory() -> None:
    rule = SequentialResearchRule(
        rule_id="research-eligible-v1",
        conditions=[
            MetricCondition(
                metric="relative_spread",
                operator="<=",
                threshold=0.08,
                unit="fraction",
                maximum_age_seconds=60,
            ),
            MetricCondition(
                metric="robust_target_probability_low",
                operator=">=",
                threshold=0.35,
                unit="probability",
                maximum_age_seconds=60,
            ),
        ],
        action_if_true=ResearchAdvisoryAction.RESEARCH_ELIGIBLE_NOW,
        action_if_false=ResearchAdvisoryAction.NO_TRADE,
        rationale="All research thresholds must be simultaneously satisfied.",
    )
    observations = [
        MetricObservation(
            metric="relative_spread",
            value=0.07,
            unit="fraction",
            observed_at=NOW,
            source_ids=["quote"],
        ),
        MetricObservation(
            metric="robust_target_probability_low",
            value=0.36,
            unit="probability",
            observed_at=NOW,
            source_ids=["scenario-report"],
        ),
    ]
    result = evaluate_sequential_rule(rule, observations, as_of=NOW)
    assert result.action is ResearchAdvisoryAction.RESEARCH_ELIGIBLE_NOW
    assert result.order_capability == "forbidden"
    stale = evaluate_sequential_rule(
        rule,
        [
            observations[0].model_copy(
                update={"observed_at": NOW - timedelta(minutes=2)}
            ),
            observations[1],
        ],
        as_of=NOW,
    )
    assert stale.action is ResearchAdvisoryAction.NO_TRADE
    assert stale.blockers == ["stale:relative_spread"]
