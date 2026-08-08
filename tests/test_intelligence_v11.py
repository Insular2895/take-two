from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml

from take_two_options.exceptions import ForbiddenOperation
from take_two_options.intelligence._numpy import np
from take_two_options.intelligence.bayesian import (
    update_heuristic_scenario_beliefs,
    update_scenario_distribution,
)
from take_two_options.intelligence.covariance import dynamic_covariance
from take_two_options.intelligence.data_hub import (
    FredConnector,
    GoogleTrendsAlphaConnector,
    IBKROpraConnector,
    MarketCalendarConnector,
    SecEdgarConnector,
    TakeTwoRssConnector,
    UnifiedDataHub,
    seed_from_v10,
)
from take_two_options.intelligence.execution import (
    assert_no_order_capability,
    build_execution_previews,
    execution_gateway,
)
from take_two_options.intelligence.monitoring import monitor_position
from take_two_options.intelligence.optimizer import optimize_allocations_with_frontier
from take_two_options.intelligence.pipeline import load_v11_policy, run_intelligence
from take_two_options.intelligence.schemas import (
    DataQuality,
    EvidenceFamily,
    LikelihoodRule,
    MonitorAction,
    NormalizedEventType,
    NormalizedEvidenceEvent,
    PositionDossier,
    PositionMonitorInput,
    SimulationRegime,
    StochasticModel,
)
from take_two_options.intelligence.stochastic import (
    simulate_all_models,
    simulate_path_set,
)
from take_two_options.intelligence.valuation import (
    generate_exit_plan,
    select_candidate_pool,
    summarize_robustness,
    summarize_valuation_ensemble,
    value_candidate_across_models,
)
from take_two_options.intelligence.volatility_calibration import (
    calibrate_local_volatility,
)
from take_two_options.quantitative.model_uncertainty import EnsembleWeightBasis
from take_two_options.thesis_scanner.schemas import ThesisScanReport

BASE_REPORT = Path("reports/examples/v10_thesis_scan.json")
POLICY = Path("configs/intelligence/v11.yaml")


def _base_report() -> ThesisScanReport:
    return ThesisScanReport.model_validate_json(BASE_REPORT.read_text(encoding="utf-8"))


def _small_policy():
    policy = load_v11_policy(POLICY)
    simulation = policy.simulation.model_copy(update={"paths": 64, "steps": 12, "horizon_days": 60})
    return policy.model_copy(update={"simulation": simulation, "candidate_pool_size": 2})


def test_v11_policy_covers_models_regimes_and_safety_profiles() -> None:
    policy = load_v11_policy(POLICY)
    assert set(policy.simulation.models) == set(StochasticModel)
    assert {item.regime for item in policy.simulation.regimes} == set(SimulationRegime)
    assert set(policy.optimizer_profiles) == {"prudent", "balanced", "aggressive"}
    assert policy.maximum_loss_eur <= policy.budget_eur
    assert policy.source_status == "calibration_required"


def test_bayesian_updates_deduplicate_fact_and_cap_family_weight() -> None:
    now = datetime(2026, 7, 28, tzinfo=UTC)
    rules = [
        LikelihoodRule(
            event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
            family=EvidenceFamily.COMPANY_PRIMARY,
            likelihood_by_scenario={"success": 0.9, "delay": 0.1},
            base_weight=1.0,
        )
    ]
    events = [
        NormalizedEvidenceEvent(
            event_id="first",
            event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
            family=EvidenceFamily.COMPANY_PRIMARY,
            occurred_at=now,
            observed_at=now,
            canonical_fact_id="same-announcement",
            source_ids=["official"],
            confidence=0.8,
        ),
        NormalizedEvidenceEvent(
            event_id="duplicate",
            event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
            family=EvidenceFamily.COMPANY_PRIMARY,
            occurred_at=now,
            observed_at=now + timedelta(minutes=1),
            canonical_fact_id="same-announcement",
            source_ids=["syndicated"],
            confidence=1.0,
        ),
        NormalizedEvidenceEvent(
            event_id="second-fact",
            event_type=NormalizedEventType.RELEASE_DATE_MAINTAINED,
            family=EvidenceFamily.COMPANY_PRIMARY,
            occurred_at=now,
            observed_at=now + timedelta(minutes=2),
            canonical_fact_id="different-announcement",
            source_ids=["official-2"],
            confidence=0.8,
        ),
    ]
    result = update_scenario_distribution(
        priors={"success": 0.5, "delay": 0.5},
        events=events,
        rules=rules,
        family_caps={EvidenceFamily.COMPANY_PRIMARY: 1.0},
    )
    assert result.scenario_probabilities["success"] > 0.5
    assert result.updates[1].deduplicated
    assert result.updates[1].effective_weight == 0
    assert result.updates[2].family_cap_applied
    assert result.updates[2].effective_weight == pytest.approx(0.2)
    assert sum(result.scenario_probabilities.values()) == pytest.approx(1)
    assert result.semantic_type == "configured_heuristic_belief"
    assert result.evidence_sufficiency_level == result.confidence_level
    explicitly_named = update_heuristic_scenario_beliefs(
        priors={"success": 0.5, "delay": 0.5},
        events=events,
        rules=rules,
        family_caps={EvidenceFamily.COMPANY_PRIMARY: 1.0},
    )
    assert explicitly_named == result


def test_dynamic_covariance_is_psd_and_uses_special_windows() -> None:
    rows = np.arange(300, dtype=float)
    history = {
        "ttwo": (np.sin(rows / 11) * 0.02).tolist(),
        "iv": (np.cos(rows / 13) * 0.03).tolist(),
        "nasdaq": (np.sin(rows / 17) * 0.01).tolist(),
        "eurusd": (np.cos(rows / 23) * 0.005).tolist(),
    }
    report = dynamic_covariance(
        history,
        windows=[20, 60, 252],
        shrinkage=0.3,
        event_indices=list(range(40, 65)),
        regime_indices=list(range(240, 300)),
    )
    eigenvalues = np.linalg.eigvalsh(np.asarray(report.shrunk_covariance))
    assert report.status == "ready"
    assert {window.label for window in report.windows} >= {
        "20_sessions",
        "60_sessions",
        "252_sessions",
        "comparable_events",
        "current_regime",
    }
    assert float(np.min(eigenvalues)) >= -1e-12
    assert report.minimum_eigenvalue > 0


def test_stochastic_models_are_seeded_positive_and_share_entry_iv() -> None:
    policy = _small_policy().simulation
    adverse = next(item for item in policy.regimes if item.regime is SimulationRegime.ADVERSE)
    first = simulate_path_set(
        spot=230,
        policy=policy,
        model=StochasticModel.HESTON_JUMP,
        regime=adverse,
    )
    second = simulate_path_set(
        spot=230,
        policy=policy,
        model=StochasticModel.HESTON_JUMP,
        regime=adverse,
    )
    assert np.array_equal(first.spots, second.spots)
    assert np.all(first.spots > 0)
    assert np.allclose(first.variances[:, 0], policy.heston.initial_variance)
    assert first.spots.shape == (64, 13)


def test_dupire_local_volatility_is_extracted_but_synthetic_surface_stays_partial() -> None:
    base = _base_report()
    nodes, report = calibrate_local_volatility(
        base.chain,
        rate=base.policy.risk_free_rate,
        dividend_yield=base.policy.continuous_dividend_yield,
    )
    assert report.status == "partial"
    assert report.expirations == 2
    assert report.output_nodes == len(nodes)
    assert len(nodes) >= 6
    assert all(0 < node.volatility < 5 for node in nodes)
    assert any("OPRA" in warning for warning in report.warnings)


def test_all_four_models_run_over_all_four_regimes() -> None:
    policy = _small_policy().simulation
    path_sets = simulate_all_models(spot=230, policy=policy)
    assert len(path_sets) == 16
    assert {(item.model, item.regime) for item in path_sets} == {
        (model, regime) for model in StochasticModel for regime in SimulationRegime
    }


def test_path_valuation_produces_full_risk_metrics_and_robustness() -> None:
    base = _base_report()
    policy = _small_policy()
    candidate = select_candidate_pool(base, 1)[0]
    path_sets = simulate_all_models(spot=base.chain.spot, policy=policy.simulation)
    valuations = value_candidate_across_models(
        candidate,
        path_sets,
        horizon_days=policy.simulation.horizon_days,
        rate=policy.simulation.risk_free_rate,
        dividend_yield=policy.simulation.dividend_yield,
        exit_policy=policy.exit_policy,
    )
    robustness = summarize_robustness(candidate, valuations)
    ensemble = summarize_valuation_ensemble(
        valuations,
        weight_basis=EnsembleWeightBasis.EQUAL_SENSITIVITY,
    )
    assert len(valuations) == 16
    assert len({item.parameter_set_id for item in valuations}) == 16
    assert all(0 <= item.metrics.probability_profit <= 1 for item in valuations)
    assert all(item.metrics.cvar_95_usd >= item.metrics.var_95_usd for item in valuations)
    assert all(
        item.metrics.reasonable_worst_pnl_usd <= item.metrics.median_pnl_usd for item in valuations
    )
    assert 0 <= robustness.robustness_score <= 100
    assert ensemble.claim_status == "diagnostic_only"
    assert ensemble.total_predictive_variance == pytest.approx(
        ensemble.within_model_predictive_variance + ensemble.between_model_predictive_variance
    )
    assert "ensemble_weights_are_not_validated_oos" in ensemble.blockers
    frontier = optimize_allocations_with_frontier(
        candidates=[candidate],
        valuations={candidate.candidate_id: valuations},
        regime_weights={regime: 0.25 for regime in SimulationRegime},
        profile_name="prudent",
        profile=policy.optimizer_profiles["prudent"],
        budget_eur=policy.budget_eur,
        maximum_loss_eur=policy.maximum_loss_eur,
        maximum_contracts=policy.maximum_contracts,
        eur_usd_rate=base.policy.eur_usd_rate,
        maximum_positions=policy.maximum_positions,
        maximum_concentration=policy.maximum_concentration,
        minimum_liquidity_score=policy.minimum_liquidity_score,
        maximum_relative_spread=policy.maximum_relative_spread,
        delta_exposure_range=policy.delta_exposure_range,
        gamma_exposure_range=policy.gamma_exposure_range,
        vega_exposure_range=policy.vega_exposure_range,
        theta_exposure_range=policy.theta_exposure_range,
        allow_multiple_strategies=policy.allow_multiple_strategies,
    )
    assert frontier.oracle_method == "exhaustive_integer_enumeration"
    assert any(point.no_trade for point in frontier.pareto_frontier)
    assert frontier.feasible_allocations >= len(frontier.pareto_frontier)


def test_exit_plan_is_created_at_candidate_selection() -> None:
    base = _base_report()
    policy = _small_policy()
    candidate = select_candidate_pool(base, 1)[0]
    plan = generate_exit_plan(candidate, policy=policy.exit_policy)
    assert plan.profit_target == 1.5
    assert plan.partial_profit_target == 0.8
    assert plan.operational_stop_loss == 0.7
    assert plan.exit_days_before_expiration == 60
    assert plan.human_review_required
    assert {
        "trailing_drawdown",
        "temporal_invalidation",
        "theta_limit",
        "exit_before_catalyst",
        "exit_after_catalyst",
    }.issubset({rule.rule_id for rule in plan.rules})


def test_v10_seed_preserves_provenance_and_required_series() -> None:
    base = _base_report()
    sources, observations = seed_from_v10(base)
    snapshot = UnifiedDataHub(
        ["TTWO.spot", "EURUSD", "USD.risk_free_rate", "TTWO.dividend_yield"]
    ).collect(
        ticker="TTWO",
        as_of=base.chain.as_of,
        connectors=[],
        seed_sources=sources,
        seed_observations=observations,
    )
    assert not snapshot.missing_required_series
    assert any(item.series == "TTWO.spot" for item in snapshot.observations)
    assert {source.quality for source in snapshot.sources} >= {DataQuality.SYNTHETIC}
    assert snapshot.connectors[0].connector_id == "v10_normalized_seed"


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_sec_connector_normalizes_official_filings() -> None:
    def opener(request: Any, **_kwargs: Any) -> _Response:
        if "submissions" in request.full_url:
            return _Response(
                {
                    "filings": {
                        "recent": {
                            "form": ["10-K"],
                            "accessionNumber": ["0001"],
                            "filingDate": ["2026-05-01"],
                        }
                    }
                }
            )
        return _Response({"entityName": "Take-Two Interactive", "facts": {}})

    connector = SecEdgarConnector(
        cik="946581",
        user_agent="research test test@example.com",
        opener=opener,
    )
    result = connector.fetch(ticker="TTWO", as_of=datetime(2026, 7, 28, tzinfo=UTC))
    assert result.source.quality is DataQuality.OFFICIAL
    assert {item.value for item in result.observations} >= {
        "10-K",
        "Take-Two Interactive",
    }


def test_fred_connector_requires_environment_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    connector = FredConnector(series_ids=["DGS10"], user_agent="research test")
    with pytest.raises(RuntimeError, match="FRED_API_KEY"):
        connector.fetch(ticker="TTWO", as_of=datetime(2026, 7, 28, tzinfo=UTC))


class _TrendsPort:
    def interest(self, **_kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "term": "GTA VI",
                "timestamp": "2026-07-27T00:00:00Z",
                "value": 42.0,
                "region": "US",
            }
        ]


def test_google_trends_alpha_is_capped_attention_data() -> None:
    connector = GoogleTrendsAlphaConnector(_TrendsPort(), terms=["GTA VI"])
    result = connector.fetch(ticker="TTWO", as_of=datetime(2026, 7, 28, tzinfo=UTC))
    assert result.observations[0].series == "GOOGLE_TRENDS.GTA VI"
    assert result.observations[0].value == 42.0
    assert "not absolute" in result.source.notes[0].lower()


def test_take_two_rss_excludes_post_cutoff_and_undated_items() -> None:
    raw = b"""<rss><channel>
      <item><title>Known at cutoff</title>
        <pubDate>Fri, 24 Jul 2026 20:00:00 GMT</pubDate></item>
      <item><title>Future item</title>
        <pubDate>Sat, 25 Jul 2026 20:00:00 GMT</pubDate></item>
      <item><title>Undated item</title></item>
    </channel></rss>"""

    class RssResponse:
        def __enter__(self) -> RssResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return raw

    connector = TakeTwoRssConnector(
        feed_url="https://example.invalid/rss",
        opener=lambda *_args, **_kwargs: RssResponse(),
    )
    result = connector.fetch(
        ticker="TTWO",
        as_of=datetime(2026, 7, 24, 20, tzinfo=UTC),
    )
    assert [item.value for item in result.observations] == ["Known at cutoff"]
    assert len(result.warnings) == 2


class _CalendarPort:
    def sessions(self, **_kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "timestamp": "2026-07-24T13:30:00Z",
                "is_open": True,
                "opens_at": "2026-07-24T13:30:00Z",
                "closes_at": "2026-07-24T20:00:00Z",
            },
            {
                "timestamp": "2026-07-25T13:30:00Z",
                "is_open": False,
            },
        ]


def test_market_calendar_connector_is_point_in_time() -> None:
    connector = MarketCalendarConnector(
        _CalendarPort(),
        provider="official exchange calendar test",
    )
    result = connector.fetch(
        ticker="TTWO",
        as_of=datetime(2026, 7, 24, 20, tzinfo=UTC),
    )
    assert [item.series for item in result.observations] == ["US.market_calendar"]
    assert result.observations[0].value is True
    assert result.warnings == ["1 post-cutoff calendar row(s) were excluded."]


class _IBKRPort:
    def option_chain_snapshot(self, ticker: str) -> dict[str, Any]:
        return {
            "source_id": "ibkr-test",
            "spot": 230,
            "spot_timestamp": "2026-07-24T20:00:00Z",
            "quotes": [
                {
                    "symbol": f"{ticker}270319C00300000",
                    "timestamp": "2026-07-24T20:00:00Z",
                    "bid": 3.5,
                    "ask": 3.7,
                    "implied_volatility": 0.36,
                    "volume": 10,
                    "open_interest": 100,
                }
            ],
        }

    def combo_quote(self, candidate_id: str, legs: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "bid": 3.4,
            "ask": 3.6,
            "timestamp": "2026-07-24T20:00:00Z",
            "source_id": "ibkr-combo-test",
            "executable": bool(legs),
        }


def test_ibkr_opra_port_is_market_data_only() -> None:
    connector = IBKROpraConnector(_IBKRPort())
    result = connector.fetch(ticker="TTWO", as_of=datetime(2026, 7, 28, tzinfo=UTC))
    combo = connector.quote_combo(candidate_id="candidate", legs=[{"ratio": 1}])
    assert result.source.quality is DataQuality.OPRA
    assert combo.executable
    assert not hasattr(connector, "submit_order")


def test_execution_previews_cannot_transmit() -> None:
    candidate = select_candidate_pool(_base_report(), 1)[0]
    preview = build_execution_previews([candidate])[0]
    assert preview.transmit is False
    assert preview.what_if is True
    assert preview.order_capability == "forbidden"
    assert preview.blockers
    gateway = execution_gateway()
    with pytest.raises(ForbiddenOperation):
        gateway.submit_order({"symbol": "TTWO"})


def test_order_capable_adapter_is_rejected() -> None:
    class Unsafe:
        def placeOrder(self) -> None:
            return None

    with pytest.raises(TypeError, match="order-capable"):
        assert_no_order_capability(Unsafe())


def _dossier() -> PositionDossier:
    base = _base_report()
    candidate = select_candidate_pool(base, 1)[0]
    policy = _small_policy()
    return PositionDossier(
        dossier_id="paper-1",
        candidate_id=candidate.candidate_id,
        opened_at=datetime(2026, 7, 28, tzinfo=UTC),
        initial_scenario_probabilities={"success": 0.6, "delay": 0.4},
        initial_distribution_source="v11-test",
        initial_spot=230,
        initial_iv=0.35,
        initial_rate=0.04,
        initial_greeks={"delta": 30, "gamma": 0.5, "theta": -5, "vega": 60, "rho": 20},
        initial_regime="neutral",
        expected_catalysts=["GTA VI"],
        invalidation_conditions=["official delay"],
        entry_price_usd=6.8,
        actual_cost_usd=680,
        actual_slippage_usd=0,
        exit_plan=generate_exit_plan(candidate, policy=policy.exit_policy),
        state="paper_open",
        human_actor="tester",
    )


def test_monitoring_marks_thesis_invalidation_before_pnl_rules() -> None:
    dossier = _dossier()
    current = PositionMonitorInput(
        as_of=dossier.opened_at + timedelta(days=10),
        current_spot=240,
        market_value_usd=900,
        realized_pnl_usd=0,
        current_iv=0.32,
        current_rate=0.04,
        current_greeks={"delta": 35},
        current_scenario_probabilities={"success": 0.4, "delay": 0.6},
        thesis_invalidated=True,
        days_to_expiration=150,
        regime="adverse",
        execution_impact_usd=-5,
    )
    report = monitor_position(dossier, current)
    assert report.action is MonitorAction.THESIS_INVALIDATED
    assert "fundamental_invalidation" in report.triggered_rules
    assert report.order_capability == "forbidden"


def test_monitoring_reduces_at_partial_profit_target() -> None:
    dossier = _dossier()
    current = PositionMonitorInput(
        as_of=dossier.opened_at + timedelta(days=10),
        current_spot=250,
        market_value_usd=680 * 1.9,
        realized_pnl_usd=0,
        current_iv=0.35,
        current_rate=0.04,
        current_greeks={"delta": 40},
        current_scenario_probabilities={"success": 0.6, "delay": 0.4},
        days_to_expiration=150,
        regime="neutral",
        execution_impact_usd=0,
    )
    report = monitor_position(dossier, current)
    assert report.action is MonitorAction.REDUCE
    assert "partial_profit_target" in report.triggered_rules


def test_monitoring_evaluates_theta_trailing_temporal_and_catalyst_rules() -> None:
    opened = datetime(2026, 7, 28, tzinfo=UTC)
    dossier = _dossier().model_copy(
        update={
            "opened_at": opened,
            "catalyst_date": opened + timedelta(days=12),
            "horizon_days": 5,
        }
    )
    current = PositionMonitorInput(
        as_of=opened + timedelta(days=10),
        current_spot=228,
        market_value_usd=610,
        realized_pnl_usd=0,
        current_iv=0.35,
        current_rate=0.04,
        current_greeks={"delta": 25, "theta": -250},
        current_scenario_probabilities={"success": 0.6, "delay": 0.4},
        days_to_expiration=150,
        regime="neutral",
        execution_impact_usd=0,
        prudent_liquidation_value_usd=600,
        peak_prudent_liquidation_value_usd=900,
        expected_remaining_pnl_usd=10,
        remaining_cvar_95_usd=100,
        liquidity_score=0.8,
    )
    report = monitor_position(dossier, current)
    assert report.action is MonitorAction.EXIT_REVIEW
    assert {
        "theta_limit",
        "trailing_drawdown",
        "temporal_invalidation",
        "exit_before_catalyst",
    }.issubset(report.triggered_rules)


def test_full_v11_pipeline_is_reproducible_and_writes_all_reports(
    tmp_path: Path,
) -> None:
    policy_payload = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    policy_payload["simulation"]["paths"] = 64
    policy_payload["simulation"]["steps"] = 12
    policy_payload["simulation"]["horizon_days"] = 60
    policy_payload["candidate_pool_size"] = 2
    for profile in policy_payload["optimizer_profiles"].values():
        profile["maximum_allocations"] = 2
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy_payload), encoding="utf-8")
    report = run_intelligence(
        base_report_path=BASE_REPORT,
        policy_path=policy_path,
        events_path=Path("fixtures/v11/events_empty.json"),
        json_out=tmp_path / "report.json",
        markdown_out=tmp_path / "report.md",
        html_out=tmp_path / "report.html",
        connectors=[IBKROpraConnector(_IBKRPort())],
        created_at=datetime(2026, 7, 28, 12, tzinfo=UTC),
    )
    assert len(report.model_metrics) == 32
    assert len(report.robustness) == 2
    assert len(report.validation) == 2
    assert all(not item.promotion_eligible for item in report.validation)
    assert report.local_volatility_calibration.status == "partial"
    assert len(report.allocations) == 6
    assert all(allocation.constraint_checks["whole_contracts"] for allocation in report.allocations)
    assert any(allocation.no_trade for allocation in report.allocations)
    assert all(item.transmit is False for item in report.execution_previews)
    assert all(item.combo_quote is not None for item in report.execution_previews)
    assert all(
        item.combo_quote is not None and item.combo_quote.executable
        for item in report.execution_previews
    )
    assert (tmp_path / "report.json").is_file()
    assert "V11" in (tmp_path / "report.md").read_text(encoding="utf-8")
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "transmit=false" in html
    assert "<script" not in html
    assert "fetch(" not in html
    assert "19. Readiness status" in html
    assert "20. Raisons de NO_TRADE ou blocage" in html
    assert report.schema_version == "11.1"
    assert report.machine_summary.promotion_eligible is False
    assert report.machine_summary.order_capability == "forbidden"
    assert report.offline_calibration["status"] == "BLOCKED_MISSING_CALIBRATION_DATA"
    assert report.walk_forward_backtest["status"] == ("BLOCKED_MISSING_CALIBRATION_DATA")
    assert all(
        item.status.value not in {"production_ready_offline"}
        for item in report.readiness
        if item.feature
        in {
            "bayesian_scenario_engine",
            "multi_model_simulation",
            "historical_calibration",
            "walk_forward_backtest",
            "live_market_data",
            "paper_trading_validation",
            "order_execution",
        }
    )
