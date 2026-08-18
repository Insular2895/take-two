from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from take_two_options.domain import OptionType
from take_two_options.intelligence._numpy import np
from take_two_options.intelligence.backtesting import (
    WalkForwardCase,
    WalkForwardDataset,
    run_walk_forward,
)
from take_two_options.intelligence.bayesian import update_scenario_distribution
from take_two_options.intelligence.calibration import (
    build_dataset_splits,
    fit_offline_models,
    validate_historical_dataset,
)
from take_two_options.intelligence.data_hub import UnifiedDataHub
from take_two_options.intelligence.event_normalization import (
    normalize_observations_to_events,
)
from take_two_options.intelligence.execution import (
    assert_all_execution_paths_forbidden,
)
from take_two_options.intelligence.optimizer import _integer_vectors
from take_two_options.intelligence.schemas import (
    DataDomain,
    DataQuality,
    EventNormalizationRule,
    EvidenceFamily,
    FeatureStatus,
    FreshnessStatus,
    HumanReviewStatus,
    LikelihoodRule,
    NormalizedEventType,
    NormalizedEvidenceEvent,
    SourceProvenance,
    UnifiedObservation,
)
from take_two_options.intelligence.valuation import _black_scholes


def _source(source_id: str = "official-source") -> SourceProvenance:
    return SourceProvenance(
        source_id=source_id,
        provider="official test provider",
        uri="https://example.invalid/source",
        retrieved_at=datetime(2026, 7, 28, 12, tzinfo=UTC),
        data_domain=DataDomain.MARKET,
        quality=DataQuality.OFFICIAL,
        license_or_terms="test-only",
    )


def _observation(
    observation_id: str,
    *,
    timestamp: datetime,
    series: str = "TTWO.test",
    value: float | int | str | bool = 1.0,
    unit: str = "decimal",
    source_id: str = "official-source",
    domain: DataDomain = DataDomain.MARKET,
) -> UnifiedObservation:
    return UnifiedObservation(
        observation_id=observation_id,
        series=series,
        timestamp=timestamp,
        value=value,
        unit=unit,
        source_id=source_id,
        domain=domain,
        quality=DataQuality.OFFICIAL,
    )


def test_data_hub_enforces_lineage_cutoff_units_duplicates_and_unknown_sources() -> None:
    cutoff = datetime(2026, 7, 28, 12, tzinfo=UTC)
    valid = _observation("valid", timestamp=cutoff - timedelta(hours=1))
    duplicate = _observation("duplicate", timestamp=valid.timestamp)
    bad_unit = _observation(
        "bad-unit",
        timestamp=cutoff - timedelta(hours=2),
        value=2.0,
        unit="USD",
    )
    future = _observation("future", timestamp=cutoff + timedelta(seconds=1))
    unknown = _observation(
        "unknown",
        timestamp=cutoff - timedelta(hours=3),
        source_id="unknown-source",
    )
    snapshot = UnifiedDataHub(["TTWO.test"]).collect(
        ticker="TTWO",
        as_of=cutoff,
        connectors=[],
        seed_sources=[_source()],
        seed_observations=[valid, duplicate, bad_unit, future, unknown],
        checked_at=cutoff,
    )
    assert [item.observation_id for item in snapshot.observations] == ["valid"]
    enriched = snapshot.observations[0]
    assert enriched.provider == "official test provider"
    assert enriched.cutoff == cutoff
    assert enriched.point_in_time_valid
    assert enriched.raw_hash
    assert enriched.freshness_status is FreshnessStatus.FRESH
    warnings = " ".join(snapshot.warnings)
    assert "duplicate" in warnings
    assert "unit mismatch" in warnings
    assert "future/post-cutoff" in warnings
    assert "unknown source" in warnings


def test_stale_required_series_is_visible_not_silently_refreshed() -> None:
    cutoff = datetime(2026, 7, 28, 12, tzinfo=UTC)
    snapshot = UnifiedDataHub(
        ["TTWO.test"],
        freshness_hours_by_domain={DataDomain.MARKET: 1},
    ).collect(
        ticker="TTWO",
        as_of=cutoff,
        connectors=[],
        seed_sources=[_source()],
        seed_observations=[
            _observation("stale", timestamp=cutoff - timedelta(hours=2))
        ],
        checked_at=cutoff,
    )
    assert snapshot.observations[0].freshness_status is FreshnessStatus.STALE
    assert any("Required series are stale" in warning for warning in snapshot.warnings)


def test_event_normalization_is_deterministic_reviewable_and_contradiction_aware() -> None:
    cutoff = datetime(2026, 7, 28, 12, tzinfo=UTC)
    snapshot = UnifiedDataHub().collect(
        ticker="TTWO",
        as_of=cutoff,
        connectors=[],
        seed_sources=[_source()],
        seed_observations=[
            _observation(
                "attention",
                timestamp=cutoff - timedelta(hours=1),
                series="GOOGLE_TRENDS.GTA VI",
                value=80,
                unit="index",
                domain=DataDomain.ATTENTION,
            )
        ],
        checked_at=cutoff,
    )
    rules = [
        EventNormalizationRule(
            rule_id="attention-support",
            series_pattern="GOOGLE_TRENDS.*",
            event_type=NormalizedEventType.SEARCH_ATTENTION_UP,
            family=EvidenceFamily.ATTENTION,
            operator="greater_than",
            threshold=60,
            expected_unit="index",
            direction="supports",
            contradiction_group="attention",
        ),
        EventNormalizationRule(
            rule_id="attention-contradiction",
            series_pattern="GOOGLE_TRENDS.*",
            event_type=NormalizedEventType.SEARCH_ATTENTION_DOWN,
            family=EvidenceFamily.ATTENTION,
            operator="greater_than",
            threshold=60,
            expected_unit="index",
            direction="contradicts",
            contradiction_group="attention",
        ),
    ]
    first = normalize_observations_to_events(snapshot.observations, rules, cutoff=cutoff)
    second = normalize_observations_to_events(snapshot.observations, rules, cutoff=cutoff)
    assert first == second
    assert len(first.events) == 2
    assert first.contradiction_clusters
    assert all(
        event.human_review_status is HumanReviewStatus.PENDING
        for event in first.events
    )
    assert all(event.normalization_rule_id in first.rule_proofs for event in first.events)


def test_text_event_never_receives_automatic_bayesian_impact() -> None:
    now = datetime(2026, 7, 28, tzinfo=UTC)
    event = NormalizedEvidenceEvent(
        event_id="pending-headline",
        event_type=NormalizedEventType.GTA_DELAY_CONFIRMED,
        family=EvidenceFamily.COMPANY_PRIMARY,
        occurred_at=now,
        observed_at=now,
        canonical_fact_id="delay",
        source_ids=["official"],
        confidence=1,
        human_review_status=HumanReviewStatus.PENDING,
    )
    rule = LikelihoodRule(
        event_type=NormalizedEventType.GTA_DELAY_CONFIRMED,
        family=EvidenceFamily.COMPANY_PRIMARY,
        likelihood_by_scenario={"success": 0.01, "delay": 0.99},
    )
    result = update_scenario_distribution(
        priors={"success": 0.5, "delay": 0.5},
        events=[event],
        rules=[rule],
        family_caps={EvidenceFamily.COMPANY_PRIMARY: 1},
        as_of=now,
    )
    assert result.scenario_probabilities == {"success": 0.5, "delay": 0.5}
    assert result.updates[0].effective_weight == 0
    assert result.updates[0].ignored_reason == "human_review_pending"


def test_bayesian_audit_contains_weight_waterfall_and_sensitivity() -> None:
    now = datetime(2026, 7, 28, tzinfo=UTC)
    event = NormalizedEvidenceEvent(
        event_id="quantitative",
        event_type=NormalizedEventType.IV_SPIKE,
        family=EvidenceFamily.OPTIONS,
        occurred_at=now,
        observed_at=now,
        canonical_fact_id="iv-spike",
        source_ids=["opra"],
        confidence=0.8,
        quality_multiplier=0.9,
        freshness_multiplier=0.8,
        novelty=0.75,
        human_review_status=HumanReviewStatus.NOT_REQUIRED,
        normalization_rule_id="iv-rule-v1",
    )
    rule = LikelihoodRule(
        event_type=NormalizedEventType.IV_SPIKE,
        family=EvidenceFamily.OPTIONS,
        likelihood_by_scenario={"base": 0.3, "rupture": 0.8},
        base_weight=0.5,
    )
    result = update_scenario_distribution(
        priors={"base": 0.7, "rupture": 0.3},
        events=[event],
        rules=[rule],
        family_caps={EvidenceFamily.OPTIONS: 0.6},
        as_of=now,
    )
    update = result.updates[0]
    assert update.raw_weight == pytest.approx(0.3)
    assert update.weight_after_quality == pytest.approx(0.27)
    assert update.weight_after_freshness == pytest.approx(0.216)
    assert update.effective_weight == pytest.approx(0.216)
    assert update.rule_id == "likelihood:EVENT_IV_SPIKE:options"
    assert sum(update.posterior.values()) == pytest.approx(1)
    assert result.sensitivity is not None
    assert 0 <= result.sensitivity.maximum_probability_swing <= 1


def _historical_payload(*, synthetic: bool, points: int) -> dict[str, object]:
    start = datetime(2025, 1, 1, 21, tzinfo=UTC)
    records = []
    for index in range(points):
        timestamp = start + timedelta(days=index)
        records.append(
            {
                "record_type": "underlying",
                "timestamp": timestamp.isoformat(),
                "available_at": timestamp.isoformat(),
                "series": "TTWO.close",
                "value": 200 + index * 0.2 + math.sin(index / 3),
                "unit": "USD_per_share",
                "provider": "licensed-test",
                "source_id": "history",
            }
        )
    return {
        "dataset_id": "ttwo-history",
        "dataset_version": "1",
        "created_at": (start + timedelta(days=points)).isoformat(),
        "cutoff": (start + timedelta(days=points)).isoformat(),
        "timezone": "UTC",
        "provider": "licensed-test",
        "license_or_usage_notes": "test fixture",
        "synthetic": synthetic,
        "split_adjustment_policy": "explicit",
        "dividend_adjustment_policy": "explicit",
        "records": records,
    }


def test_calibration_missing_data_is_blocked_without_fixture_fallback() -> None:
    dataset, quality = validate_historical_dataset(None)
    fit = fit_offline_models(dataset, quality)
    splits = build_dataset_splits(dataset, quality)
    assert quality.status == "BLOCKED_MISSING_CALIBRATION_DATA"
    assert fit.status == "BLOCKED_MISSING_CALIBRATION_DATA"
    assert splits.status == "BLOCKED_MISSING_CALIBRATION_DATA"


def test_synthetic_calibration_can_test_mechanics_but_never_claim_calibrated(
    tmp_path: Path,
) -> None:
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(_historical_payload(synthetic=True, points=150)), encoding="utf-8")
    dataset, quality = validate_historical_dataset(path)
    fit = fit_offline_models(dataset, quality)
    splits = build_dataset_splits(dataset, quality)
    assert quality.status == "FIXTURE_ONLY_NOT_CALIBRATED"
    assert fit.status == "FIXTURE_ONLY_NOT_CALIBRATED"
    assert all(model.status != "calibrated_pending_validation" for model in fit.models)
    assert splits.status == "READY"
    assert splits.final_holdout_locked


def test_authorized_history_produces_fit_pending_validation_not_promotion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "history.json"
    path.write_text(json.dumps(_historical_payload(synthetic=False, points=150)), encoding="utf-8")
    dataset, quality = validate_historical_dataset(path)
    fit = fit_offline_models(dataset, quality)
    assert quality.status == "READY_FOR_OFFLINE_CALIBRATION"
    assert fit.status == "CALIBRATION_FIT_PENDING_VALIDATION"
    assert next(model for model in fit.models if model.model == "heston").status == (
        "insufficient_data"
    )


def _walk_case(
    case_id: str,
    strategy: str,
    *,
    split: str = "test",
    pnl_up: bool = True,
) -> WalkForwardCase:
    decision = datetime(2026, 1, 2, 15, tzinfo=UTC)
    expiration = datetime(2026, 6, 19, 20, tzinfo=UTC)
    return WalkForwardCase(
        case_id=case_id,
        window_id="window-1",
        split=split,
        strategy=strategy,
        decision_time=decision,
        entry_time=decision + timedelta(minutes=1),
        exit_time=decision + timedelta(days=5),
        calibrated_through=decision - timedelta(days=1),
        data_available_at=decision,
        contract_first_seen_at=decision - timedelta(days=30),
        expiration=expiration,
        strike=230,
        available_expirations=[expiration],
        available_strikes=[230],
        entry_bid=4.8,
        entry_ask=5.0,
        exit_bid=6.0 if pnl_up else 3.0,
        exit_ask=6.2 if pnl_up else 3.2,
        side="long",
        predicted_probability_profit=0.6,
        oracle_non_exploitable=strategy == "oracle_hindsight",
    )


def test_walk_forward_uses_prudent_prices_and_reports_missing_baselines() -> None:
    dataset = WalkForwardDataset(
        dataset_id="walk",
        created_at=datetime(2026, 2, 1, tzinfo=UTC),
        cutoff=datetime(2026, 2, 1, tzinfo=UTC),
        synthetic=True,
        window_method="rolling",
        cases=[
            _walk_case("model", "model_candidate"),
            _walk_case("cash", "cash"),
            _walk_case("underlying", "underlying", pnl_up=False),
        ],
    )
    report = run_walk_forward(dataset)
    model = next(result for result in report.results if result.case_id == "model")
    assert model.pnl_usd == pytest.approx((6.0 - 5.0) * 100)
    assert report.status == "FIXTURE_ONLY_NOT_VALIDATED"
    assert "oracle_hindsight" in report.missing_baselines
    assert report.final_holdout_used_for_tuning is False


def test_walk_forward_rejects_lookahead_and_unavailable_contracts() -> None:
    future_payload = _walk_case("future-data", "model_candidate").model_dump()
    future_payload["data_available_at"] = datetime(2026, 1, 3, 15, tzinfo=UTC)
    with pytest.raises(ValueError, match="look-ahead"):
        WalkForwardCase.model_validate(future_payload)
    strike_payload = _walk_case("strike", "model_candidate").model_dump()
    strike_payload["available_strikes"] = [220.0]
    with pytest.raises(ValueError, match="selected strike was unavailable"):
        WalkForwardCase.model_validate(strike_payload)


@settings(max_examples=40, deadline=None)
@given(
    lower=st.floats(min_value=1, max_value=500, allow_nan=False, allow_infinity=False),
    increment=st.floats(min_value=0, max_value=200, allow_nan=False, allow_infinity=False),
    strike=st.floats(min_value=1, max_value=500, allow_nan=False, allow_infinity=False),
    volatility=st.floats(min_value=0.01, max_value=2, allow_nan=False, allow_infinity=False),
)
def test_property_european_call_value_is_monotone_in_spot(
    lower: float,
    increment: float,
    strike: float,
    volatility: float,
) -> None:
    spots = np.asarray([lower, lower + increment], dtype=float)
    values = _black_scholes(
        spot=spots,
        strike=strike,
        time_years=0.5,
        volatility=np.asarray([volatility, volatility]),
        rate=0.03,
        dividend_yield=0.0,
        option_type=OptionType.CALL,
    )
    assert float(values[1]) + 1e-10 >= float(values[0])


@settings(max_examples=40, deadline=None)
@given(
    contract_counts=st.lists(st.integers(min_value=1, max_value=4), min_size=1, max_size=5),
    maximum=st.integers(min_value=0, max_value=8),
)
def test_property_integer_enumerator_never_emits_fractional_or_over_cap_allocations(
    contract_counts: list[int],
    maximum: int,
) -> None:
    vectors = list(_integer_vectors(contract_counts, maximum_contracts=maximum))
    assert vectors
    for vector in vectors:
        assert all(isinstance(quantity, int) and quantity >= 0 for quantity in vector)
        assert sum(
            quantity * contract_count
            for quantity, contract_count in zip(vector, contract_counts, strict=True)
        ) <= maximum


def test_global_execution_boundary_scan_passes_and_is_explicit() -> None:
    result = assert_all_execution_paths_forbidden()
    assert result["status"] == "all_execution_paths_forbidden"
    assert result["order_capability"] == "forbidden"
    assert result["python_files_scanned"] > 0


def test_readiness_enum_contains_only_the_documented_product_states() -> None:
    assert {status.value for status in FeatureStatus} == {
        "production_ready_offline",
        "experimental_offline",
        "fixture_only",
        "adapter_ready_not_connected",
        "requires_live_market_data",
        "requires_historical_calibration",
        "requires_paper_trading",
        "blocked_for_execution",
    }
