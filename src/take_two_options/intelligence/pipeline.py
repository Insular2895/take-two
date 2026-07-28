"""End-to-end V11 orchestration over the stable V10.1 structure engine."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import yaml

from take_two_options.intelligence.bayesian import update_scenario_distribution
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
from take_two_options.intelligence.execution import (
    assert_no_order_capability,
    build_execution_previews,
)
from take_two_options.intelligence.optimizer import optimize_allocations
from take_two_options.intelligence.reporting import write_reports
from take_two_options.intelligence.schemas import (
    AllocationResult,
    ConnectorState,
    ConnectorStatus,
    DataQuality,
    NormalizedEvidenceEvent,
    ResearchPosture,
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
    historical_returns_path: Path = Path(
        "data/alpaca/ttwo_calibration_dataset_2026-07-19.json"
    ),
    created_at: datetime | None = None,
) -> V11IntelligenceReport:
    """Run V11 without exposing any live-order submission operation."""
    scan_time = created_at or datetime.now(UTC)
    if scan_time.tzinfo is None:
        scan_time = scan_time.replace(tzinfo=UTC)
    base = ThesisScanReport.model_validate_json(base_report_path.read_text(encoding="utf-8"))
    policy = load_v11_policy(policy_path)
    events = load_events(events_path)
    seed_sources, seed_observations = seed_from_v10(base)
    connector_list = connectors or []
    for connector in connector_list:
        assert_no_order_capability(connector)
    data_snapshot = UnifiedDataHub(policy.required_series).collect(
        ticker=base.request.ticker,
        as_of=base.chain.as_of,
        connectors=connector_list,
        seed_sources=seed_sources,
        seed_observations=seed_observations,
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
    bayesian = update_scenario_distribution(
        priors=policy.scenario_priors,
        events=events,
        rules=policy.likelihood_rules,
        family_caps=policy.family_weight_caps,
    )
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
    ready_connectors = {
        item.connector_id
        for item in data_snapshot.connectors
        if item.state is ConnectorState.READY
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
                )
    path_sets = simulate_all_models(spot=base.chain.spot, policy=simulation_policy)
    valuations: dict[str, list[StrategyPathValuation]] = {}
    exit_plans = []
    robustness = []
    validation = []
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
        validation.append(
            validate_candidate(
                candidate,
                candidate_valuations,
                historical_evidence=base.historical_evidence,
            )
        )
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
        )
    ]
    previews = build_execution_previews(candidates, combo_quotes=combo_quotes)
    data_qualities = {source.quality for source in data_snapshot.sources}
    report_identity = {
        "base_report_id": base.report_id,
        "policy_id": policy.policy_id,
        "data_snapshot_id": data_snapshot.snapshot_id,
        "posterior": bayesian.scenario_probabilities,
        "created_at": scan_time,
    }
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
        bayesian_distribution=bayesian,
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
    )
    return write_reports(
        report,
        json_out=json_out,
        markdown_out=markdown_out,
        html_out=html_out,
    )
