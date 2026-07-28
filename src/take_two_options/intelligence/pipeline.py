"""End-to-end V11 orchestration over the stable V10.1 structure engine."""

from __future__ import annotations

import json
import math
import platform
import resource
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml

from take_two_options.intelligence._numpy import np
from take_two_options.intelligence.backtesting import (
    load_walk_forward_dataset,
    run_walk_forward,
)
from take_two_options.intelligence.bayesian import update_scenario_distribution
from take_two_options.intelligence.calibration import (
    fit_offline_models,
    validate_historical_dataset,
)
from take_two_options.intelligence.covariance import (
    CovarianceDataError,
    dynamic_covariance,
    load_factor_history,
)
from take_two_options.intelligence.data_hub import (
    DataConnector,
    IBKROpraConnector,
    UnifiedDataHub,
    seed_from_v10,
)
from take_two_options.intelligence.event_normalization import (
    normalize_observations_to_events,
)
from take_two_options.intelligence.execution import (
    assert_all_execution_paths_forbidden,
    assert_no_order_capability,
    build_execution_previews,
)
from take_two_options.intelligence.optimizer import optimize_allocations
from take_two_options.intelligence.readiness import build_readiness_inventory
from take_two_options.intelligence.reporting import write_reports
from take_two_options.intelligence.robustness import run_stress_suite
from take_two_options.intelligence.schemas import (
    AllocationResult,
    ConnectorState,
    ConnectorStatus,
    DataQuality,
    FeatureStatus,
    MachineSummary,
    NormalizedEvidenceEvent,
    ResearchPosture,
    RunManifest,
    SimulationRegime,
    V11IntelligenceReport,
    V11Policy,
)
from take_two_options.intelligence.stochastic import simulate_all_models
from take_two_options.intelligence.validation import validate_candidate
from take_two_options.intelligence.valuation import (
    StrategyPathValuation,
    generate_exit_plan,
    select_candidate_pool,
    summarize_robustness,
    value_candidate_across_models,
)
from take_two_options.intelligence.volatility_calibration import (
    calibrate_local_volatility,
)
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.thesis_scanner.schemas import ThesisScanReport


def load_v11_policy(path: Path) -> V11Policy:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("V11 policy must be one YAML object")
    return V11Policy.model_validate(payload)


def load_events(path: Path | None) -> list[NormalizedEvidenceEvent]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("normalized event file must be a JSON array")
    return [NormalizedEvidenceEvent.model_validate(item) for item in payload]


def _fallback_tt_returns(
    path: Path,
    *,
    cutoff: datetime,
) -> dict[str, list[float]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        points = [
            item
            for item in payload["points"]
            if datetime.fromisoformat(
                str(item.get("data_available_at", item["timestamp"])).replace("Z", "+00:00")
            )
            <= cutoff
        ]
        closes = [float(item["close"]) for item in points]
    except (OSError, KeyError, TypeError, ValueError):
        return {}
    returns = [
        math.log(current / previous)
        for previous, current in zip(closes, closes[1:], strict=False)
        if previous > 0 and current > 0
    ]
    return {"TTWO_return": returns} if len(returns) >= 2 else {}


def _regime_weights(
    policy: V11Policy,
    posterior: dict[str, float],
) -> dict[SimulationRegime, float]:
    weights = {regime: 0.0 for regime in SimulationRegime}
    for scenario, probability in posterior.items():
        weights[policy.scenario_regime_map[scenario]] += probability
    return weights


def _posture(
    *,
    candidates_available: bool,
    allocations: list[AllocationResult],
    data_qualities: set[DataQuality],
    missing_required_series: list[str],
    all_execution_blocked: bool,
) -> ResearchPosture:
    if not candidates_available:
        return ResearchPosture.BLOCKED
    top = [item for item in allocations if item.rank == 1]
    if top and all(item.no_trade for item in top):
        return ResearchPosture.NO_TRADE
    if (
        missing_required_series
        or DataQuality.SYNTHETIC in data_qualities
        or all_execution_blocked
    ):
        return ResearchPosture.WATCHLIST
    return ResearchPosture.PAPER_REVIEW


def run_intelligence(
    *,
    base_report_path: Path,
    policy_path: Path,
    json_out: Path,
    markdown_out: Path,
    html_out: Path,
    events_path: Path | None = None,
    factor_history_path: Path | None = None,
    connectors: list[DataConnector] | None = None,
    calibration_data_path: Path | None = None,
    walk_forward_path: Path | None = None,
    runtime_profile: Literal[
        "fast_fixture", "research", "validation", "exhaustive"
    ] = "fast_fixture",
    historical_returns_path: Path = Path(
        "data/alpaca/ttwo_calibration_dataset_2026-07-19.json"
    ),
    created_at: datetime | None = None,
) -> V11IntelligenceReport:
    """Run V11 without exposing any live-order submission operation."""
    started_at = datetime.now(UTC)
    last_stage = time.perf_counter()
    stage_durations: dict[str, float] = {}

    def mark_stage(name: str) -> None:
        nonlocal last_stage
        now = time.perf_counter()
        stage_durations[name] = round(now - last_stage, 6)
        last_stage = now

    assert_all_execution_paths_forbidden()
    scan_time = created_at or datetime.now(UTC)
    if scan_time.tzinfo is None:
        scan_time = scan_time.replace(tzinfo=UTC)
    base = ThesisScanReport.model_validate_json(base_report_path.read_text(encoding="utf-8"))
    policy = load_v11_policy(policy_path)
    explicit_events = load_events(events_path)
    mark_stage("load_inputs")
    seed_sources, seed_observations = seed_from_v10(base)
    connector_list = connectors or []
    for connector in connector_list:
        assert_no_order_capability(connector)
    data_snapshot = UnifiedDataHub(
        policy.required_series,
        freshness_hours_by_domain=policy.freshness_hours_by_domain,
    ).collect(
        ticker=base.request.ticker,
        as_of=base.chain.as_of,
        connectors=connector_list,
        seed_sources=seed_sources,
        seed_observations=seed_observations,
        checked_at=scan_time,
    )
    configured_connector_ids = {connector.connector_id for connector in connector_list}
    for connector_id, warning in (
        ("sec_edgar", "SEC connector is implemented but was not configured for this run."),
        ("fred", "FRED connector is implemented but FRED_API_KEY/run config is absent."),
        (
            "take_two_rss",
            "Official Take-Two RSS connector is implemented but no feed was configured.",
        ),
        (
            "google_trends_alpha",
            "Google Trends official API remains limited-alpha and was not configured.",
        ),
        (
            "market_calendar",
            "An official or licensed US exchange calendar port was not configured.",
        ),
        (
            "ibkr_opra_read_only",
            "IBKR/OPRA read-only port requires a running TWS/IB Gateway and entitlements.",
        ),
    ):
        if connector_id not in configured_connector_ids:
            data_snapshot.connectors.append(
                ConnectorStatus(
                    connector_id=connector_id,
                    state=ConnectorState.NOT_CONFIGURED,
                    checked_at=scan_time,
                    observations=0,
                    warnings=[warning],
                )
            )
    mark_stage("data_hub")
    event_normalization = normalize_observations_to_events(
        data_snapshot.observations,
        policy.event_normalization_rules,
        cutoff=base.chain.as_of,
    )
    if explicit_events:
        event_normalization.events.extend(explicit_events)
        for event in explicit_events:
            proof = event_normalization.rule_proofs.setdefault(
                event.normalization_rule_id,
                {
                    "normalization_rule_id": event.normalization_rule_id,
                    "source": "explicit_normalized_event_file",
                    "matches": [],
                },
            )
            proof["matches"].append(
                {
                    "event_id": event.event_id,
                    "source_ids": event.source_ids,
                    "human_review_status": event.human_review_status.value,
                }
            )
    bayesian = update_scenario_distribution(
        priors=policy.scenario_priors,
        events=event_normalization.events,
        rules=policy.likelihood_rules,
        family_caps=policy.family_weight_caps,
        as_of=base.chain.as_of,
    )
    mark_stage("events_and_bayes")
    historical_dataset, dataset_quality = validate_historical_dataset(
        calibration_data_path
    )
    offline_calibration = fit_offline_models(historical_dataset, dataset_quality)
    walk_forward = run_walk_forward(
        load_walk_forward_dataset(walk_forward_path)
        if walk_forward_path is not None
        else None
    )
    mark_stage("offline_calibration_and_backtest")
    if factor_history_path is not None:
        factor_history, event_indices, regime_indices = load_factor_history(
            factor_history_path,
            cutoff=base.chain.as_of,
        )
    else:
        factor_history = _fallback_tt_returns(
            historical_returns_path,
            cutoff=base.chain.as_of,
        )
        event_indices = []
        regime_indices = []
    try:
        covariance = dynamic_covariance(
            factor_history,
            windows=policy.covariance_windows,
            shrinkage=policy.covariance_shrinkage,
            event_indices=event_indices,
            regime_indices=regime_indices,
        )
    except CovarianceDataError as error:
        covariance = dynamic_covariance(
            {},
            windows=policy.covariance_windows,
            shrinkage=policy.covariance_shrinkage,
        )
        covariance.warnings.append(str(error))

    local_nodes, local_calibration = calibrate_local_volatility(
        base.chain,
        rate=policy.simulation.risk_free_rate,
        dividend_yield=policy.simulation.dividend_yield,
    )
    simulation_policy = (
        policy.simulation.model_copy(update={"local_volatility_nodes": local_nodes})
        if local_nodes
        else policy.simulation
    )
    candidates = select_candidate_pool(base, policy.candidate_pool_size)
    mark_stage("calibration_and_covariance")
    ready_connectors = {
        item.connector_id
        for item in data_snapshot.connectors
        if item.state in {ConnectorState.READY, ConnectorState.PARTIAL}
        and item.observations > 0
    }
    combo_quotes = {}
    for connector in connector_list:
        if (
            isinstance(connector, IBKROpraConnector)
            and connector.connector_id in ready_connectors
        ):
            for candidate in candidates:
                combo_quotes[candidate.candidate_id] = connector.quote_combo(
                    candidate_id=candidate.candidate_id,
                    legs=[
                        {
                            "symbol": leg.quote.symbol,
                            "action": "BUY" if leg.side.value == "long" else "SELL",
                            "ratio": leg.quantity,
                            "exchange": "SMART",
                        }
                        for leg in candidate.base_candidate.legs
                    ],
                    as_of=base.chain.as_of,
                )
    path_sets = simulate_all_models(spot=base.chain.spot, policy=simulation_policy)
    mark_stage("simulation")
    valuations: dict[str, list[StrategyPathValuation]] = {}
    exit_plans = []
    robustness = []
    validation = []
    stress_tests = []
    for candidate in candidates:
        exit_plans.append(generate_exit_plan(candidate, policy=policy.exit_policy))
        candidate_valuations = value_candidate_across_models(
            candidate,
            path_sets,
            horizon_days=simulation_policy.horizon_days,
            rate=simulation_policy.risk_free_rate,
            dividend_yield=simulation_policy.dividend_yield,
            exit_policy=policy.exit_policy,
        )
        valuations[candidate.candidate_id] = candidate_valuations
        robustness.append(summarize_robustness(candidate, candidate_valuations))
        stress_tests.extend(run_stress_suite(candidate, candidate_valuations))
        validation.append(
            validate_candidate(
                candidate,
                candidate_valuations,
                historical_evidence=base.historical_evidence,
            )
        )
    mark_stage("valuation_and_validation")
    regime_weights = _regime_weights(
        policy,
        bayesian.scenario_probabilities,
    )
    allocations = [
        allocation
        for profile_name, profile in policy.optimizer_profiles.items()
        for allocation in optimize_allocations(
            candidates=candidates,
            valuations=valuations,
            regime_weights=regime_weights,
            profile_name=profile_name,
            profile=profile,
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
    ]
    previews = build_execution_previews(candidates, combo_quotes=combo_quotes)
    mark_stage("allocation_and_previews")
    data_qualities = {source.quality for source in data_snapshot.sources}
    report_identity = {
        "base_report_id": base.report_id,
        "policy_id": policy.policy_id,
        "data_snapshot_id": data_snapshot.snapshot_id,
        "posterior": bayesian.scenario_probabilities,
        "created_at": scan_time,
    }
    readiness = build_readiness_inventory(
        data_snapshot=data_snapshot,
        local_volatility=local_calibration,
        calibration=offline_calibration,
        backtest=walk_forward,
    )
    configuration_hash = stable_hash(policy.model_dump(mode="json"))
    data_hash = stable_hash(data_snapshot.model_dump(mode="json"))
    input_hash = stable_hash(
        {
            "base": base.model_dump(mode="json"),
            "policy": policy.model_dump(mode="json"),
            "events": [event.model_dump(mode="json") for event in explicit_events],
            "factor_history": (
                factor_history_path.read_text(encoding="utf-8")
                if factor_history_path is not None
                else None
            ),
            "calibration_dataset_hash": dataset_quality.dataset_hash,
            "walk_forward_dataset": (
                walk_forward_path.read_text(encoding="utf-8")
                if walk_forward_path is not None
                else None
            ),
        }
    )
    peak_memory = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    peak_memory_mb = (
        peak_memory / 1024 / 1024
        if platform.system() == "Darwin"
        else peak_memory / 1024
    )
    completed_at = datetime.now(UTC)
    run_manifest = RunManifest(
        run_id=f"run-{stable_hash((report_identity, input_hash))[:20]}",
        profile=runtime_profile,
        seed=policy.simulation.seed,
        configuration_hash=configuration_hash,
        data_hash=data_hash,
        input_hash=input_hash,
        model_versions={
            "take_two_options": "0.11.1",
            "schema": "11.1",
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        policy_version=policy.policy_id,
        started_at=started_at,
        completed_at=completed_at,
        stage_durations_seconds=stage_durations,
        peak_memory_mb=max(peak_memory_mb, 0.0),
        deterministic_cache=True,
    )
    blocking_reasons = [
        *data_snapshot.missing_required_series,
        offline_calibration.status,
        walk_forward.status,
        "paper_trading_not_run",
        "execution_forbidden",
    ]
    report = V11IntelligenceReport(
        report_id=f"v11-{stable_hash(report_identity)[:20]}",
        created_at=scan_time,
        ticker=base.request.ticker,
        base_v10_report_id=base.report_id,
        posture=_posture(
            candidates_available=bool(candidates),
            allocations=allocations,
            data_qualities=data_qualities,
            missing_required_series=data_snapshot.missing_required_series,
            all_execution_blocked=all(bool(item.blockers) for item in previews),
        ),
        data_snapshot=data_snapshot,
        event_normalization=event_normalization,
        bayesian_distribution=bayesian,
        offline_calibration=offline_calibration.model_dump(mode="json"),
        walk_forward_backtest=walk_forward.model_dump(mode="json"),
        local_volatility_calibration=local_calibration,
        covariance=covariance,
        model_metrics=[
            item.metrics
            for candidate_valuations in valuations.values()
            for item in candidate_valuations
        ],
        robustness=robustness,
        validation=validation,
        allocations=allocations,
        stress_tests=stress_tests,
        exit_plans=exit_plans,
        execution_previews=previews,
        facts_verified=[
            "V10.1 remains the sole structure-construction and QuantLib American control engine.",
            "All V11 allocations use whole contracts, bounded debit risk, and may retain cash.",
            "Every IBKR artifact remains preview-only with transmit=false and what_if=true.",
            "Bayesian evidence is deduplicated by canonical fact and capped by source family.",
        ],
        hypotheses_to_test=[
            "Bayesian priors, likelihoods, and family caps are experimental inputs.",
            "Local-volatility and Heston parameters require point-in-time OPRA "
            "surface calibration.",
            "Simulation regime drifts, jumps, and probabilities require walk-forward validation.",
            "The option path repricer uses a conditional Black-Scholes control "
            "between V10 QuantLib checkpoints.",
        ],
        limitations=[
            *data_snapshot.warnings,
            *local_calibration.warnings,
            *covariance.warnings,
            "A single TTWO return series cannot estimate the requested cross-factor covariance; "
            "supply an aligned factor-history file for Nasdaq, gaming peers, rates, FX, "
            "volume, IV, OI, sentiment, news intensity, and catalyst proximity.",
            "Leg quotes do not prove a simultaneous combo fill.",
            "IBKR notes that account market-data entitlements are required and some smart "
            "combo orders do not support what-if commission/margin checks.",
            "Google Trends API access remains limited alpha and must not be replaced by "
            "an undocumented scraper in a production workflow.",
        ],
        validations_required=[
            "Freeze a live IBKR/OPRA chain with contract conIds, deliverables, combo quotes, "
            "commissions, and account-specific margin.",
            "Calibrate the local-volatility surface and Heston/jump parameters without look-ahead.",
            "Run nested walk-forward, event-window backtests, crisis stresses, "
            "and a new untouched holdout.",
            "Complete paper trading with human-reviewed entries, partial exits, "
            "rolls, and invalidations.",
            "Obtain explicit user approval before any future change to the "
            "forbidden execution boundary.",
        ],
        readiness=readiness,
        run_manifest=run_manifest,
        machine_summary=MachineSummary(
            schema_version="11.1",
            generated_at=scan_time,
            cutoff=base.chain.as_of,
            posture=_posture(
                candidates_available=bool(candidates),
                allocations=allocations,
                data_qualities=data_qualities,
                missing_required_series=data_snapshot.missing_required_series,
                all_execution_blocked=all(bool(item.blockers) for item in previews),
            ),
            result_status=(
                FeatureStatus.FIXTURE_ONLY
                if DataQuality.SYNTHETIC in data_qualities
                else FeatureStatus.EXPERIMENTAL_OFFLINE
            ),
            calibration_status=offline_calibration.status,
            backtest_status=walk_forward.status,
            promotion_eligible=False,
            blocking_reasons=blocking_reasons,
        ),
    )
    return write_reports(
        report,
        json_out=json_out,
        markdown_out=markdown_out,
        html_out=html_out,
    )
