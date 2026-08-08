"""Build the evidence-backed JSON, Markdown, and standalone HTML pre-OPRA report."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from take_two_options.config.loader import load_pre_opra_config, pre_opra_config_hash
from take_two_options.reporting.pre_opra_final import (
    FinalBaselineRow,
    FinalGateRow,
    FinalLossPoint,
    FinalPreOpraReport,
    FinalScoreSummary,
    ReportSection,
    RunManifest,
    TopCandidate,
    render_html,
    render_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "pre_opra"
DEFAULT_CONFIG = ROOT / "configs" / "pre_opra" / "v1" / "ttwo_research.yaml"


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _read(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads((REPORTS / name).read_text(encoding="utf-8")),
    )


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section(
    section_id: str, title: str, status: str, summary: str, artifact: str
) -> ReportSection:
    return ReportSection(
        section_id=section_id,
        title=title,
        status=status,
        summary=summary,
        artifact=artifact,
    )


def build(generated_at: datetime, *, config_path: Path = DEFAULT_CONFIG) -> FinalPreOpraReport:
    config = load_pre_opra_config(config_path)
    normalization = _read("option_normalization_2026-08-08.json")
    rights = _read("data_usage_rights_2026-08-08.json")
    market = _read("market_context_2026-08-08.json")
    events = _read("event_regime_dataset_2026-08-08.json")
    baseline = _read("baseline_comparison_2026-08-08.json")
    surfaces = _read("historical_surfaces_2026-08-08.json")
    empirical = _read("empirical_calibration_2026-08-08.json")
    walk_forward = _read("walk_forward_protocol_2026-08-08.json")
    scores = _read("five_scores_2026-08-08.json")
    severity = _read("severity_and_gate_sensitivity_2026-08-08.json")
    verdict = _read("engine_verdict_2026-08-08.json")
    input_names = [
        "option_normalization_2026-08-08.json",
        "data_usage_rights_2026-08-08.json",
        "market_context_2026-08-08.json",
        "event_regime_dataset_2026-08-08.json",
        "baseline_comparison_2026-08-08.json",
        "historical_surfaces_2026-08-08.json",
        "empirical_calibration_2026-08-08.json",
        "walk_forward_protocol_2026-08-08.json",
        "five_scores_2026-08-08.json",
        "severity_and_gate_sensitivity_2026-08-08.json",
        "engine_verdict_2026-08-08.json",
    ]
    artifact_hashes = {name: _file_hash(REPORTS / name) for name in input_names}
    dataset_hash = hashlib.sha256(
        json.dumps(artifact_hashes, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest = RunManifest(
        schema_version="2.0",
        generated_at=generated_at,
        code_commit=_commit(),
        configuration_hash=pre_opra_config_hash(config),
        dataset_hash=dataset_hash,
        seed=20_260_808,
        python_version=platform.python_version(),
        platform=platform.platform(),
        dependencies={
            name: importlib.metadata.version(name)
            for name in ("numpy", "pydantic", "PyYAML", "QuantLib")
        },
        schema_versions={
            "final_pre_opra_report": "2.0",
            "baseline_comparison": str(baseline["schema_version"]),
            "historical_surfaces": str(surfaces["schema_version"]),
            "empirical_calibration": str(empirical["schema_version"]),
            "walk_forward": str(walk_forward["schema_version"]),
            "five_scores": str(scores["schema_version"]),
            "severity_gates": str(severity["schema_version"]),
            "engine_verdict": str(verdict["schema_version"]),
        },
        score_versions={
            name: str(scores[name]["formula_version"])
            for name in (
                "opportunity",
                "risk",
                "evidence",
                "model_agreement",
                "execution_quality",
            )
        },
        artifact_hashes=artifact_hashes,
        command="ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml",
        holdout_used=False,
    )
    oos = cast(dict[str, Any], walk_forward["oos_strategy_comparison"])
    baseline_rows = [
        FinalBaselineRow(
            strategy=str(row["strategy"]),
            observations=int(row["observations"]),
            total_return=float(row["total_return"]),
            expected_return=float(row["expected_return"]),
            median_return=float(row["median_return"]),
            cvar_95=float(row["cvar_95"]),
            maximum_drawdown=float(row["maximum_drawdown"]),
            probability_profit=float(row["probability_profit"]),
            probability_target=float(row["probability_target"]),
            probability_loss_50=float(row["probability_loss_50"]),
            probability_loss_70=float(row["probability_loss_70"]),
            probability_loss_90=float(row["probability_loss_90"]),
            sharpe=float(row["sharpe"]) if row["sharpe"] is not None else None,
            sortino=float(row["sortino"]) if row["sortino"] is not None else None,
            transaction_costs_eur=float(row["transaction_costs"]),
            evidence=str(row["evidence"]),
        )
        for row in oos["rows"]
    ]
    score_summaries = [
        FinalScoreSummary(
            kind=name,
            score_value=float(scores[name]["score_value"]),
            score_coverage=float(scores[name]["score_coverage"]),
            missing_components=[str(item) for item in scores[name]["missing_components"]],
            confidence=str(scores[name]["confidence"]),
            formula_version=str(scores[name]["formula_version"]),
        )
        for name in (
            "opportunity",
            "risk",
            "evidence",
            "model_agreement",
            "execution_quality",
        )
    ]
    loss_points = [
        FinalLossPoint(
            threshold=float(item["loss_threshold"]),
            probability=float(item["probability"]),
            wilson_interval_95=tuple(item["wilson_interval_95"]),
            bootstrap_interval_95=tuple(item["bootstrap_interval_95"]),
        )
        for item in severity["payoff_severity"]["severe_loss_ladder"]
    ]
    gate_rows = [
        FinalGateRow(
            setting_id=str(item["setting"]["setting_id"]),
            passed=not bool(item["no_position_recommended"]),
            best_candidate_id=(
                str(item["best_candidate_id"])
                if item["best_candidate_id"] is not None
                else None
            ),
            minimum_opportunity=float(item["setting"]["minimum_opportunity"]),
            maximum_risk=float(item["setting"]["maximum_risk"]),
            minimum_evidence=float(item["setting"]["minimum_evidence"]),
            minimum_execution_quality=float(
                item["setting"]["minimum_execution_quality"]
            ),
        )
        for item in severity["gate_sensitivity"]
    ]
    top_candidates = [
        TopCandidate(
            label="BEST_RISK_ADJUSTED",
            candidate_id="buy_and_hold",
            classification="DEVELOPMENT_LEADER",
            rationale="Meilleur compromis OOS observé : +25,1% composé, CVaR 7,9%.",
        ),
        TopCandidate(
            label="HIGHEST_UPSIDE",
            candidate_id="atm_long_call",
            classification="HIGH_RISK",
            rationale="E[R] OOS la plus haute, mais -65,5% composé et CVaR 64,7%.",
        ),
        TopCandidate(
            label="LOWEST_RISK",
            candidate_id="no_position",
            classification="LOWEST_RISK",
            rationale="Rendement et perte nuls dans le panel ; aucune exposition optionnelle.",
        ),
        TopCandidate(
            label="BEST_BLOCKED_CANDIDATE",
            candidate_id="engine_candidate",
            classification=str(scores["classification"]),
            rationale="Meilleur candidat moteur visible ; échoue le gate central d'opportunité.",
        ),
        TopCandidate(
            label="BEST_SIMPLE_BASELINE",
            candidate_id="buy_and_hold",
            classification="BASELINE",
            rationale="Baseline simple supérieure à V10 sur développement complet et OOS.",
        ),
    ]
    sections = [
        _section(
            "A",
            "DATA COVERAGE",
            "LOCAL_PRIVATE_DATA_USED",
            "20 884 observations options uniques, 631 barres spot, taux, FX et 14 événements.",
            "option_normalization_2026-08-08.json",
        ),
        _section(
            "B",
            "CALIBRATION",
            "DEVELOPMENT_CALIBRATED_HESTON_BLOCKED",
            "Empirique, EWMA, GARCH/GJR et 535 tranches SVI ; Heston reste non identifiable.",
            "empirical_calibration_2026-08-08.json",
        ),
        _section(
            "C",
            "WALK-FORWARD",
            "REAL_DEVELOPMENT_OOS_LIMITED",
            "10 tests futurs non chevauchants ; DSR 5,7 %, PBO 77,8 %.",
            "walk_forward_protocol_2026-08-08.json",
        ),
        _section(
            "D",
            "HOLDOUT",
            "UNOPENED",
            "Ledger intact ; aucun holdout artificiel n'a été créé ou consulté.",
            "../../validation/final_holdout_ledger.jsonl",
        ),
        _section(
            "E",
            "BASELINES",
            "NINE_REAL_ALIGNED_STRATEGIES",
            "Même capital EUR, mêmes dates, mêmes coûts prudents et même politique FX.",
            "baseline_comparison_2026-08-08.json",
        ),
        _section(
            "F",
            "TOP CANDIDATES",
            "EXPOSED_WITH_NO_POSITION",
            "Le no-position ne masque ni l'upside mesuré ni le meilleur candidat bloqué.",
            "severity_and_gate_sensitivity_2026-08-08.json",
        ),
        _section(
            "G",
            "FIVE SCORES",
            "CALCULATED_PARTIAL_AWARE",
            "Cinq dimensions calculées sans redistribuer les poids manquants.",
            "five_scores_2026-08-08.json",
        ),
        _section(
            "H",
            "RAW METRICS",
            "DISPLAYED",
            "Rendements, coûts, CVaR, drawdown, DSR, PBO et diagnostics sont conservés.",
            "engine_verdict_2026-08-08.json",
        ),
        _section(
            "I",
            "SEVERE-LOSS LADDER",
            "CALCULATED_WITH_INTERVALS",
            "Six seuils avec intervalles Wilson et bootstrap ; dix observations seulement.",
            "severity_and_gate_sensitivity_2026-08-08.json",
        ),
        _section(
            "J",
            "GATE SENSITIVITY",
            "GATE_INSTABILITY",
            "Le candidat passe le réglage permissif mais échoue central et strict.",
            "severity_and_gate_sensitivity_2026-08-08.json",
        ),
        _section(
            "K",
            "V10 VS BASELINES",
            "V10_UNDERPERFORMS",
            "V10 perd sur le panel complet et OOS ; aucune supériorité ajustée Holm.",
            "engine_verdict_2026-08-08.json",
        ),
        _section(
            "L",
            "ENGINE VERDICT",
            "ENGINE_NOT_PROVEN_SUPERIOR",
            "Verdict mécanique ; aucun retuning après observation du résultat.",
            "engine_verdict_2026-08-08.json",
        ),
        _section(
            "M",
            "REMAINING BLOCKERS",
            "THREE_EXTERNAL_OR_FUTURE_DEPENDENCIES",
            "Droits humains, nouvel échantillon/holdout et OPRA restent irréductibles localement.",
            "../../docs/LIMITATIONS.md",
        ),
        _section(
            "N",
            "OPRA READINESS",
            "CONTRACT_DEFINED_NOT_CONNECTED",
            "Phase M non démarrée ; aucune connexion ou simulation OPRA n'a été effectuée.",
            "../../docs/validation/OPRA_FINAL_VALIDATION_PLAN.md",
        ),
    ]
    multiple = cast(dict[str, Any], oos["multiple_testing"])
    construction = cast(dict[str, Any], surfaces["construction"])
    empirical_summary = cast(dict[str, Any], empirical["empirical"])
    remaining_blockers = [
        (
            "Confirmation humaine du type d'abonnement et des droits de recherche/stockage "
            "des fournisseurs historiques."
        ),
        (
            "Échantillon options formel et holdout réellement futur : 25 observations "
            "disponibles contre 41 requises ; il ne peut pas être fabriqué sans fuite."
        ),
        (
            "Entitlement et identifiants OPRA live requis pour la future Phase M "
            "prospective read-only/paper."
        ),
    ]
    return FinalPreOpraReport(
        schema_version="2.0",
        report_id="ttwo-final-pre-opra-v2",
        ticker="TTWO",
        generated_at=generated_at,
        overall_status="PRE_OPRA_RESEARCH_COMPLETE",
        evidence_grade="development_oos_limited",
        decision="NO_POSITION_RECOMMENDED",
        decision_scope="research_only_not_investment_advice",
        engine_verdict=str(verdict["verdict"]),
        run_manifest=manifest,
        sections=sections,
        data_coverage={
            "raw_option_envelopes": int(normalization["raw_envelopes"]),
            "raw_option_rows": int(normalization["raw_rows"]),
            "unique_option_observations": int(normalization["unique_observations"]),
            "option_dates": len(normalization["observations_per_requested_date"]),
            "underlying_bars": int(market["underlying_bar_count"]),
            "risk_free_curves": int(market["rate_curve_count"]),
            "fx_rates": int(market["fx_rate_count"]),
            "governed_events": len(events["accepted_events"]),
            "rights_status": str(rights["legal_review_status"]),
        },
        calibration_status={
            "return_observations": int(empirical_summary["return_observations"]),
            "annualized_realized_volatility": float(
                empirical_summary["annualized_realized_volatility"]
            ),
            "excess_kurtosis": float(empirical_summary["excess_kurtosis"]),
            "iv_inversions_succeeded": int(construction["iv_inversions_succeeded"]),
            "surface_slices": int(construction["eligible_slices"]),
            "fitted_surface_dates": int(surfaces["stability"]["fitted_snapshots"]),
            "heston_status": str(empirical["heston_status"]),
        },
        walk_forward_status={
            "available_panel_observations": int(
                walk_forward["sample_adequacy"]["available_observations"]
            ),
            "oos_test_observations": int(
                walk_forward["sample_adequacy"]["diagnostic_test_observations"]
            ),
            "formal_policy_satisfied": bool(
                walk_forward["sample_adequacy"]["formal_policy_satisfied"]
            ),
            "deflated_sharpe_probability": float(
                multiple["deflated_sharpe_probability"]
            ),
            "probability_backtest_overfitting": float(
                multiple["probability_backtest_overfitting"]
            ),
            "holdout_touched": bool(walk_forward["holdout_touched"]),
        },
        baseline_table=baseline_rows,
        top_candidates=top_candidates,
        five_scores=score_summaries,
        raw_metrics={
            "v10_full_total_return": float(
                verdict["engine_full_development"]["total_return"]
            ),
            "v10_oos_total_return": float(verdict["engine_walk_forward_oos"]["total_return"]),
            "v10_oos_expected_return": float(
                verdict["engine_walk_forward_oos"]["expected_return"]
            ),
            "v10_oos_cvar_95": float(verdict["engine_walk_forward_oos"]["cvar_95"]),
            "best_simple_oos_total_return": float(
                verdict["best_simple_baseline_oos"]["total_return"]
            ),
            "holm_superiority_rejections": int(verdict["holm_superiority_rejections"]),
            "classification": str(scores["classification"]),
            "payoff_severity_classification": "AGGRESSIVE",
            "payoff_severity_rule": "CVaR95 >= 50% or P(loss>50%) >= 20%",
        },
        severe_loss_ladder=loss_points,
        gate_sensitivity=gate_rows,
        best_blocked_candidate=cast(dict[str, object], severity["best_blocked_candidate"]),
        remaining_blockers=remaining_blockers,
        opra_readiness=[
            "Contrat de provider live read-only prévu ; aucune méthode d'ordre autorisée.",
            "Chaînes, bid/ask, timestamps, fraîcheur et spreads devront être journalisés.",
            "Chaque décision paper sera gelée avant réalisation et reliée par hash.",
            "La Phase M comparera V10 aux mêmes baselines avec coûts et slippage observés.",
        ],
        exact_opra_variables=[
            "OPRA_PROVIDER",
            "OPRA_API_KEY",
            "OPRA_API_SECRET",
            "OPRA_ACCOUNT_OR_SESSION",
        ],
        exact_command_after_opra=(
            "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
        ),
        external_source_ids=[
            "https://www.marketdata.app/terms/",
            "https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf",
            "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files",
            "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html",
            "https://www.sec.gov/Archives/edgar/data/946581/000162828026037434/ttwo-20260331.htm",
        ],
        holdout_state="UNOPENED",
        holdout_used=False,
        phase_m_started=False,
        transmit=False,
        what_if=True,
        order_capability="forbidden",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--generated-at", default="2026-08-08T20:30:00+02:00")
    args = parser.parse_args()
    report = build(datetime.fromisoformat(args.generated_at), config_path=args.config)
    REPORTS.mkdir(parents=True, exist_ok=True)
    stem = REPORTS / "final_pre_opra_report_2026-08-08"
    stem.with_suffix(".json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    stem.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    stem.with_suffix(".html").write_text(render_html(report), encoding="utf-8")
    (REPORTS / "run_manifest_2026-08-08.json").write_text(
        json.dumps(report.run_manifest.model_dump(mode="json"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
