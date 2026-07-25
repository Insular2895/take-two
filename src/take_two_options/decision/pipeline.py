"""End-to-end, read-only, knowledge-driven option decision pipeline."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from take_two_options.candidate_generation.enumerator import enumerate_candidates
from take_two_options.candidate_generation.pruning import prune_candidate
from take_two_options.decision.ranking import apply_explanatory_scores
from take_two_options.decision.request import load_trade_request
from take_two_options.decision.verdict import decide_verdict
from take_two_options.forecasting.price_distribution import (
    build_price_distribution,
    load_historical_series,
)
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import (
    CompiledStrategyCandidate,
    DecisionReport,
    MarketSnapshot,
    ReportAnalysis,
    ResearchRun,
    SourceReference,
    StrategyCatalog,
    TradeRequest,
)
from take_two_options.market_snapshot import (
    MarketSnapshotError,
    load_latest_market_snapshot,
    refresh_market_snapshot,
    snapshot_manifest,
)
from take_two_options.optimization.coarse_search import coarse_search
from take_two_options.optimization.fine_search import fine_search
from take_two_options.optimization.parameter_stability import local_stability
from take_two_options.optimization.pareto import pareto_rank
from take_two_options.optimization.trial_registry import TrialRegistry
from take_two_options.reporting.decision_report import write_decision_report
from take_two_options.reporting.ibkr_ticket import (
    write_blocked_ticket_status,
    write_ibkr_preview,
)
from take_two_options.simulation.conditional_monte_carlo import simulate_conditional_paths
from take_two_options.simulation.evaluation import evaluate_path_set
from take_two_options.simulation.model_ensemble import summarize_models
from take_two_options.validation.gates import evaluate_validation_gates
from take_two_options.validation.holdout import contaminated_holdout_ids
from take_two_options.validation.placebo import placebo_diagnostics
from take_two_options.validation.stress import stress_candidate, stress_passed


def _git_version() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _research_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("research configuration must be an object")
    return payload


def _historical_path(ticker: str) -> Path:
    candidates = sorted(
        Path("data/alpaca").glob(f"{ticker.lower()}_calibration_dataset_*.json")
    )
    if not candidates and ticker.upper() == "TTWO":
        candidates = sorted(Path("data/alpaca").glob("ttwo_calibration_dataset_*.json"))
    if not candidates:
        raise FileNotFoundError(f"no historical calibration dataset for {ticker}")
    return candidates[-1]


def _sources(catalog: StrategyCatalog, snapshot: MarketSnapshot) -> list[SourceReference]:
    source_by_id: dict[str, SourceReference] = {}
    for recipe in catalog.recipes:
        for source in recipe.sources:
            source_by_id[source.source_id] = source
    source_by_id["take-two-q2-fy2026"] = SourceReference(
        source_id="take-two-q2-fy2026",
        author="Take-Two Interactive",
        title="Fiscal second quarter 2026 results and GTA VI release timing",
        edition_or_date="2025-11-06",
        chapter=None,
        page=None,
        accessed_at=datetime.now(UTC).date(),
        source_type="company",
        uri=(
            "https://www.take2games.com/ir/news/"
            "take-two-interactive-software-inc-reports-results-fiscal-3"
        ),
        confidence="high",
        excerpt_hash=None,
    )
    source_by_id["ecb-eurusd-2026-07-17"] = SourceReference(
        source_id="ecb-eurusd-2026-07-17",
        author="European Central Bank",
        title="Dated EUR/USD reference rate used for budget normalization",
        edition_or_date="2026-07-17",
        chapter=None,
        page=None,
        accessed_at=datetime.now(UTC).date(),
        source_type="official",
        uri="https://data.ecb.europa.eu/currency-converter",
        confidence="high",
        excerpt_hash=None,
    )
    for source_id in snapshot.source_ids:
        source_by_id.setdefault(
            source_id,
            SourceReference(
                source_id=source_id,
                author="MarketData.app",
                title="Timestamped historical option-chain response",
                edition_or_date=snapshot.as_of.date().isoformat(),
                chapter=None,
                page=None,
                accessed_at=datetime.now(UTC).date(),
                source_type="data_provider",
                uri="https://www.marketdata.app/docs/api/options/chain/",
                confidence="medium",
                excerpt_hash=None,
            ),
        )
    return list(source_by_id.values())


def _progressive_final_evaluation(
    candidates: list[CompiledStrategyCandidate],
    *,
    request: TradeRequest,
    series_path: Path,
    snapshot: MarketSnapshot,
    initial_paths: int,
    maximum_paths: int,
    seed: int,
    registry: TrialRegistry,
) -> int:
    series = load_historical_series(series_path, ticker=request.ticker, cutoff=snapshot.as_of)
    previous: dict[str, float] = {}
    path_count = initial_paths
    used = path_count
    while path_count <= maximum_paths:
        path_sets = simulate_conditional_paths(
            series,
            spot=snapshot.spot,
            horizon_days=max(
                candidate.exit_policy.maximum_holding_days for candidate in candidates
            ),
            paths=path_count,
            seed=seed,
        )
        converged = bool(previous)
        for candidate in candidates:
            metrics = [
                evaluate_path_set(
                    candidate,
                    path_set,
                    request=request,
                    start_date=request.as_of,
                )
                for path_set in path_sets
            ]
            candidate.evaluation = summarize_models(metrics)
            current = candidate.evaluation.conservative_expected_pnl or 0.0
            if candidate.candidate_id in previous:
                tolerance = max(abs(current) * 0.05, 5.0)
                converged = (
                    converged
                    and abs(current - previous[candidate.candidate_id]) <= tolerance
                )
            else:
                converged = False
            previous[candidate.candidate_id] = current
            registry.register(
                stage="fine_search",
                outcome="evaluated",
                architecture=candidate.architecture,
                candidate_id=candidate.candidate_id,
                parameters={
                    "progressive_final_paths": path_count,
                    "models": [path_set.model_id for path_set in path_sets],
                },
            )
        used = path_count
        if converged:
            break
        path_count *= 2
    return used


def _blocked_report(
    *,
    request: TradeRequest,
    run: ResearchRun,
    reason: str,
    report_dir: Path,
) -> DecisionReport:
    report = DecisionReport(
        report_id=f"decision-{run.run_id}",
        created_at=datetime.now(UTC),
        analysis=ReportAnalysis(
            ticker=request.ticker,
            budget=request.budget,
            currency=request.currency,
            thesis=request.thesis_summary,
            horizon_days=(request.horizon_min_days, request.horizon_max_days),
            data_date=None,
            data_quality="unavailable",
            holdout_status="INSUFFICIENT_DATA",
            total_trials=run.total_trials,
        ),
        verdict="BLOCKED_INSUFFICIENT_DATA",
        request=request,
        research_run=run,
        no_trade_reasons=[reason],
        limitations=[reason],
        audit_files=[],
    )
    status_path = write_blocked_ticket_status(
        report, report_dir / "ibkr_ticket_status.json"
    )
    report.audit_files.append(str(status_path))
    return write_decision_report(report, report_dir)


def analyze_trade(
    *,
    request_path: Path,
    report_dir: Path,
    knowledge_dir: Path = Path("research/knowledge_items"),
    research_config_path: Path = Path("configs/research/default.yaml"),
    refresh_data: bool = False,
) -> DecisionReport:
    started = datetime.now(UTC)
    request = load_trade_request(request_path)
    config = _research_config(research_config_path)
    catalog = compile_knowledge(load_knowledge(knowledge_dir))
    config_hash = stable_hash(
        {"request": request, "research_config": config, "catalog": catalog.knowledge_hash}
    )
    seed = int(config["seed"])
    run_id = f"{request.ticker.lower()}-{started.strftime('%Y%m%dT%H%M%SZ')}-{config_hash[:8]}"
    run = ResearchRun(
        run_id=run_id,
        started_at=started,
        seed=seed,
        config_hash=config_hash,
        code_version=_git_version(),
        request_id=request.request_id,
        knowledge_hash=catalog.knowledge_hash,
    )
    registry = TrialRegistry(run_id=run_id, seed=seed, config_hash=config_hash)
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "strategy_catalog.json").write_text(
        catalog.model_dump_json(indent=2), encoding="utf-8"
    )

    refresh_warning: str | None = None
    try:
        snapshot = (
            refresh_market_snapshot(
                ticker=request.ticker,
                as_of=request.as_of,
                strike_limit=request.data_refresh_policy.marketdata_strike_limit,
            )
            if refresh_data
            else load_latest_market_snapshot(ticker=request.ticker, as_of=request.as_of)
        )
    except MarketSnapshotError as error:
        refresh_warning = str(error)
        try:
            snapshot = load_latest_market_snapshot(
                ticker=request.ticker, as_of=request.as_of
            )
        except MarketSnapshotError as fallback_error:
            run.status = "blocked"
            run.completed_at = datetime.now(UTC)
            return _blocked_report(
                request=request,
                run=run,
                reason=f"market data unavailable: {fallback_error}",
                report_dir=report_dir,
            )
    run.data_snapshot_id = snapshot.snapshot_id
    historical_path = _historical_path(request.ticker)
    series = load_historical_series(
        historical_path, ticker=request.ticker, cutoff=snapshot.as_of
    )
    forecast = build_price_distribution(
        series,
        horizon_days=max(
            int(value)
            for recipe in catalog.recipes
            for value in recipe.holding_days.values
        ),
    )
    (report_dir / "forecast.json").write_text(
        forecast.model_dump_json(indent=2), encoding="utf-8"
    )
    enumeration = enumerate_candidates(catalog, request, snapshot)
    for candidate in enumeration.candidates:
        registry.register(
            stage="generation",
            outcome="generated",
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters={
                "legs": [leg.quote.symbol for leg in candidate.legs],
                "quantity": [leg.quantity for leg in candidate.legs],
                "exit_policy": candidate.exit_policy.policy_id,
            },
        )
    feasible: list[CompiledStrategyCandidate] = []
    for candidate in enumeration.candidates:
        reasons = prune_candidate(candidate)
        if reasons:
            candidate.status = "pruned"
            candidate.hard_vetoes = reasons
            registry.register(
                stage="pruning",
                outcome="pruned",
                architecture=candidate.architecture,
                candidate_id=candidate.candidate_id,
                reason=";".join(reasons),
            )
        else:
            feasible.append(candidate)
            registry.register(
                stage="pruning",
                outcome="selected",
                architecture=candidate.architecture,
                candidate_id=candidate.candidate_id,
            )
    if not feasible:
        run.total_trials = len(registry.records)
        run.trials_by_stage = registry.counts()
        run.status = "completed"
        run.completed_at = datetime.now(UTC)
        registry_path = report_dir / "trial_registry.jsonl"
        registry.write_jsonl(registry_path)
        reasons = sorted(
            {
                reason
                for candidate in enumeration.candidates
                for reason in candidate.hard_vetoes
            }
        )
        reason_counts = Counter(
            reason
            for candidate in enumeration.candidates
            for reason in candidate.hard_vetoes
        )
        diagnostic_candidates: list[CompiledStrategyCandidate] = []
        seen_architectures: set[str] = set()
        for candidate in sorted(
            enumeration.candidates,
            key=lambda item: (
                len(item.hard_vetoes),
                item.risk.maximum_loss,
                item.candidate_id,
            ),
        ):
            if candidate.architecture.value in seen_architectures:
                continue
            diagnostic_candidates.append(candidate)
            seen_architectures.add(candidate.architecture.value)
            if len(diagnostic_candidates) == 5:
                break
        snapshot_path = report_dir / "data_snapshot_manifest.json"
        snapshot_path.write_text(snapshot_manifest(snapshot), encoding="utf-8")
        audit_path = report_dir / "audit_log.json"
        audit_path.write_text(
            json.dumps(
                {
                    "run_id": run.run_id,
                    "config_hash": run.config_hash,
                    "knowledge_hash": run.knowledge_hash,
                    "snapshot_id": snapshot.snapshot_id,
                    "enumerated": len(enumeration.candidates),
                    "generated_by_architecture": (
                        enumeration.combinations_by_architecture
                    ),
                    "structurally_feasible": 0,
                    "pruning_reasons": reasons,
                    "pruning_reason_counts": dict(reason_counts),
                    "trial_count": len(registry.records),
                    "trial_counts": registry.counts(),
                    "validation_status": "NOT_REACHED_AFTER_HARD_VETOES",
                    "order_capability": "forbidden",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        report = DecisionReport(
            report_id=f"decision-{run.run_id}",
            created_at=datetime.now(UTC),
            analysis=ReportAnalysis(
                ticker=request.ticker,
                budget=request.budget,
                currency=request.currency,
                thesis=request.thesis_summary,
                horizon_days=(request.horizon_min_days, request.horizon_max_days),
                data_date=snapshot.as_of,
                data_quality=snapshot.quote_quality,
                holdout_status="NOT_REACHED_AFTER_HARD_VETOES",
                total_trials=run.total_trials,
            ),
            verdict="NO_TRADE",
            request=request,
            research_run=run,
            no_trade_reasons=[
                "no candidate survived structural pruning",
                *[
                    f"{reason}: {reason_counts[reason]} of "
                    f"{len(enumeration.candidates)} generated candidates"
                    for reason in reasons
                ],
            ],
            candidate_comparison=[
                {
                    "candidate_id": candidate.candidate_id,
                    "architecture": candidate.architecture.value,
                    "legs": [
                        {
                            "side": leg.side.value,
                            "quantity": leg.quantity,
                            "symbol": leg.quote.symbol,
                            "strike": leg.quote.strike,
                            "expiration": leg.quote.expiration.isoformat(),
                        }
                        for leg in candidate.legs
                    ],
                    "maximum_loss_usd": candidate.risk.maximum_loss,
                    "budget_remaining_request_currency": (
                        candidate.risk.budget_remaining
                    ),
                    "hard_vetoes": candidate.hard_vetoes,
                    "uncertainties": candidate.uncertainties,
                    "status": "rejected_before_simulation",
                }
                for candidate in diagnostic_candidates
            ],
            sources=_sources(catalog, snapshot),
            assumptions=[
                "Hard vetoes run before simulation, validation, Pareto, and scoring",
                "The no-trade baseline is preferred to relaxing liquidity or budget",
            ],
            data_used=[str(historical_path), snapshot.cache_path or snapshot.snapshot_id],
            limitations=[
                *snapshot.data_warnings,
                "A live timestamped broker combo quote could differ from synthetic leg markets",
                (
                    "Statistical validation was not reached because all structures "
                    "failed earlier gates"
                ),
            ],
            audit_files=[str(registry_path), str(snapshot_path), str(audit_path)],
        )
        status_path = write_blocked_ticket_status(
            report, report_dir / "ibkr_ticket_status.json"
        )
        report.audit_files.append(str(status_path))
        return write_decision_report(report, report_dir)

    fine_paths = int(config["fine_paths"])
    path_sets = simulate_conditional_paths(
        series,
        spot=snapshot.spot,
        horizon_days=max(
            int(value)
            for recipe in catalog.recipes
            for value in recipe.holding_days.values
        ),
        paths=fine_paths,
        seed=seed,
    )
    coarse = coarse_search(
        feasible,
        path_sets,
        registry,
        maximum_per_architecture=int(config["coarse_maximum_per_architecture"]),
    )
    score_by_id = {score.candidate_id: score for score in coarse.scores}
    base_candidates = sorted(
        coarse.selected,
        key=lambda candidate: (
            -score_by_id[candidate.candidate_id].conservative_expected_pnl,
            score_by_id[candidate.candidate_id].worst_model_loss_probability,
        ),
    )[: int(config["fine_maximum_base_candidates"])]
    fine = fine_search(
        base_candidates,
        recipes={recipe.recipe_id: recipe for recipe in catalog.recipes},
        search_spaces={space.recipe_id: space for space in enumeration.search_spaces},
        path_sets=path_sets,
        request=request,
        registry=registry,
    )
    for candidate in fine:
        candidate.evaluation.local_stability = local_stability(candidate, fine)
        candidate.evaluation.stress_results.update(stress_candidate(candidate))
    fronts = pareto_rank(fine)
    weights = dict(config["ranking_policy"]["weights"])
    ranked = apply_explanatory_scores(fine, weights)
    finalists = ranked[:5]
    if finalists:
        final_paths = _progressive_final_evaluation(
            finalists,
            request=request,
            series_path=historical_path,
            snapshot=snapshot,
            initial_paths=int(config["final_paths_initial"]),
            maximum_paths=int(config["final_paths_maximum"]),
            seed=seed,
            registry=registry,
        )
    else:
        final_paths = 0

    contaminated = contaminated_holdout_ids(
        Path("validation/contaminated_holdouts/v7_v8_v9/manifest.json")
    ) | set(request.final_holdout_policy.contaminated_dataset_ids)
    for candidate in finalists:
        candidate.evaluation.local_stability = local_stability(candidate, fine)
        candidate.evaluation.stress_results.update(stress_candidate(candidate))
        stress_ok = stress_passed(candidate.evaluation.stress_results)
        placebo_results, placebo_ok = placebo_diagnostics([], seed=seed)
        candidate.evaluation.placebo_results = placebo_results
        candidate.evaluation.validation = evaluate_validation_gates(
            policy=request.final_holdout_policy,
            train_returns=[],
            validation_returns=[],
            test_returns=[],
            holdout_returns=[],
            contaminated_ids=contaminated,
            performance_matrix=[],
            nested_windows=0,
            purged_observations=0,
            embargo_days=max(candidate.exit_policy.maximum_holding_days, 1),
            stability=candidate.evaluation.local_stability,
            stress_ok=stress_ok,
            placebo_ok=placebo_ok,
            real_trial_count=max(len(registry.records), 1),
        )
        candidate.status = (
            "admissible"
            if candidate.evaluation.validation.status == "PASSED"
            else "blocked"
        )
        registry.register(
            stage="stress",
            outcome="evaluated",
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters=candidate.evaluation.stress_results,
        )
        registry.register(
            stage="placebo",
            outcome="failed" if placebo_ok is not True else "selected",
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters=placebo_results,
            reason="insufficient history" if placebo_ok is None else "",
        )
        registry.register(
            stage="validation",
            outcome=(
                "selected"
                if candidate.evaluation.validation.status == "PASSED"
                else "rejected"
            ),
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters={
                "status": candidate.evaluation.validation.status,
                "real_trial_count": len(registry.records),
            },
            reason=";".join(candidate.evaluation.validation.reasons),
        )
    pareto_rank(finalists)
    finalists = apply_explanatory_scores(finalists, weights)
    for candidate in finalists:
        registry.register(
            stage="ranking",
            outcome="selected",
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters={
                "pareto_rank": candidate.pareto_rank,
                "explanatory_score": candidate.explanatory_score,
            },
        )

    run.total_trials = len(registry.records)
    run.trials_by_stage = registry.counts()
    run.status = "completed"
    run.completed_at = datetime.now(UTC)
    registry_path = report_dir / "trial_registry.jsonl"
    registry.write_jsonl(registry_path)
    snapshot_path = report_dir / "data_snapshot_manifest.json"
    snapshot_path.write_text(snapshot_manifest(snapshot), encoding="utf-8")
    audit_path = report_dir / "audit_log.json"
    audit_payload = {
        "run_id": run.run_id,
        "config_hash": run.config_hash,
        "knowledge_hash": run.knowledge_hash,
        "snapshot_id": snapshot.snapshot_id,
        "refresh_warning": refresh_warning,
        "enumerated": len(enumeration.candidates),
        "structurally_feasible": len(feasible),
        "coarse_selected": len(base_candidates),
        "fine_evaluated": len(fine),
        "finalists": len(finalists),
        "final_paths_per_model": final_paths,
        "trial_count": len(registry.records),
        "trial_counts": registry.counts(),
        "order_capability": "forbidden",
    }
    audit_path.write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
    horizon_listed = any(not space.horizon_gap for space in enumeration.search_spaces)
    verdict = decide_verdict(
        finalists, data_available=True, horizon_listed=horizon_listed
    )
    holdout_status_value = (
        finalists[0].evaluation.validation.status
        if finalists and finalists[0].evaluation.validation
        else "INSUFFICIENT_DATA"
    )
    no_trade_reasons = sorted(
        {
            reason
            for candidate in finalists
            if candidate.evaluation.validation is not None
            for reason in candidate.evaluation.validation.reasons
        }
    )
    no_trade_reasons.extend(enumeration.warnings)
    if refresh_warning:
        no_trade_reasons.append(f"refresh warning: {refresh_warning}")
    report = DecisionReport(
        report_id=f"decision-{run.run_id}",
        created_at=datetime.now(UTC),
        analysis=ReportAnalysis(
            ticker=request.ticker,
            budget=request.budget,
            currency=request.currency,
            thesis=request.thesis_summary,
            horizon_days=(request.horizon_min_days, request.horizon_max_days),
            data_date=snapshot.as_of,
            data_quality=snapshot.quote_quality,
            holdout_status=holdout_status_value,
            total_trials=run.total_trials,
        ),
        verdict=verdict,
        request=request,
        research_run=run,
        candidates=finalists,
        pareto_candidate_ids=fronts[0] if fronts else [],
        candidate_comparison=[
            {
                "candidate_id": candidate.candidate_id,
                "architecture": candidate.architecture.value,
                "maximum_loss": candidate.risk.maximum_loss,
                "conservative_expected_pnl": candidate.evaluation.conservative_expected_pnl,
                "cvar_95": max(
                    (
                        metric.cvar_95
                        for metric in candidate.evaluation.model_metrics
                    ),
                    default=None,
                ),
                "pareto_rank": candidate.pareto_rank,
                "status": candidate.status,
            }
            for candidate in finalists
        ],
        no_trade_reasons=no_trade_reasons,
        sources=_sources(catalog, snapshot),
        assumptions=[
            "No LLM controls calculations, ranking, or the verdict",
            "Model results are kept separate; conservative expectation uses the worst model",
            "The explicit no-trade baseline wins whenever a major gate fails",
        ],
        contradictions=catalog.contradictions,
        data_used=[str(historical_path), snapshot.cache_path or snapshot.snapshot_id],
        limitations=[
            *snapshot.data_warnings,
            *forecast.limitations,
            "V7, V8, and V9 holdouts are contaminated and cannot authorize eligibility",
            "No fresh locked option-strategy holdout or paper-trading sample is available",
            "Detailed future IV-surface forecasting is not implemented in P0/P1",
        ],
        audit_files=[
            str(registry_path),
            str(snapshot_path),
            str(audit_path),
            str(report_dir / "strategy_catalog.json"),
            str(report_dir / "forecast.json"),
        ],
    )
    if any(candidate.status == "admissible" for candidate in finalists):
        admissible = next(
            candidate for candidate in finalists if candidate.status == "admissible"
        )
        ticket_path = write_ibkr_preview(
            report,
            admissible.candidate_id,
            report_dir / "ibkr_ticket_preview.json",
        )
        report.ibkr_ticket_path = str(ticket_path)
    else:
        status_path = write_blocked_ticket_status(
            report, report_dir / "ibkr_ticket_status.json"
        )
        report.audit_files.append(str(status_path))
    return write_decision_report(report, report_dir)
