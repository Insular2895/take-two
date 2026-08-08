"""Build deterministic JSON, Markdown and static HTML final pre-OPRA artifacts."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal

from take_two_options.config.loader import load_pre_opra_config, pre_opra_config_hash
from take_two_options.reporting.pre_opra_final import (
    FinalPreOpraReport,
    PhaseResult,
    RunManifest,
    render_html,
    render_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "pre_opra"
CONFIG_PATH = ROOT / "configs" / "pre_opra" / "v1" / "ttwo_research.yaml"
DATASET_HASH = "0b09a9a9b1de6a9132e2f0eaf1a9cc15152d2fce59e40baefd21812c9886f556"
PhaseLetter = Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _phase(
    letter: PhaseLetter,
    title: str,
    status: str,
    artifact: str,
    validated: str,
    remaining: str,
) -> PhaseResult:
    return PhaseResult(
        phase=letter,
        title=title,
        status=status,
        artifact=artifact,
        validated=[validated],
        remaining=[remaining],
    )


def build(generated_at: datetime) -> FinalPreOpraReport:
    config = load_pre_opra_config(CONFIG_PATH)
    manifest = RunManifest(
        schema_version="1.0",
        generated_at=generated_at,
        code_commit=_commit(),
        configuration_hash=pre_opra_config_hash(config),
        dataset_hash=DATASET_HASH,
        seed=20_260_808,
        python_version=platform.python_version(),
        platform=platform.platform(),
        dependencies={
            name: importlib.metadata.version(name)
            for name in ("numpy", "pydantic", "PyYAML", "QuantLib")
        },
        command=(
            ".venv/bin/python scripts/build_pre_opra_final_report.py "
            "--generated-at 2026-08-08T20:30:00+02:00"
        ),
        holdout_used=False,
    )
    phases = [
        _phase(
            "A",
            "audit des gaps",
            "READY_RESEARCH_ONLY",
            "../../docs/audits/PRE_OPRA_GAP_ANALYSIS.md",
            "frontière de preuve auditée",
            "validation financière",
        ),
        _phase(
            "B",
            "configuration",
            "CONFIG_READY",
            "../../docs/config/PRE_OPRA_CONFIG.md",
            "configuration unifiée et portable",
            "valider les hypothèses draft",
        ),
        _phase(
            "C",
            "données PIT",
            "BLOCKED",
            "data_inventory_2026-08-08.json",
            "inventaire et provenance",
            "licence et couverture complète",
        ),
        _phase(
            "D",
            "calibration",
            "DIAGNOSTIC_ONLY_LICENSE_REVIEW",
            "empirical_calibration_2026-08-08.json",
            "diagnostics empiriques",
            "surface IV réelle et erreurs standards",
        ),
        _phase(
            "E",
            "walk-forward",
            "DIAGNOSTIC_ONLY_LICENSE_REVIEW",
            "walk_forward_protocol_2026-08-08.json",
            "purge, embargo et gel",
            "rendements comparables réels",
        ),
        _phase(
            "F",
            "holdout final",
            "UNOPENED",
            "../../validation/final_holdout_ledger.jsonl",
            "ledger irréversible",
            "provisionner sans ouvrir avant prérequis",
        ),
        _phase(
            "G",
            "baselines",
            "BLOCKED_INCOMPARABLE_DATA",
            "baseline_comparison_2026-08-08.json",
            "mécanique appariée et tests multiples",
            "panel des neuf stratégies",
        ),
        _phase(
            "H",
            "surfaces",
            "BLOCKED_MISSING_GOVERNED_INPUTS",
            "historical_surfaces_2026-08-08.json",
            "SVI/arbitrage sur fixtures",
            "taux, dividendes, IV et licence",
        ),
        _phase(
            "I",
            "événements/régimes",
            "BLOCKED_MISSING_GOVERNED_EVENTS",
            "event_regime_dataset_2026-08-08.json",
            "anti-lookahead et conflits",
            "historique événementiel PIT",
        ),
        _phase(
            "J",
            "cinq scores",
            "BLOCKED_VALIDATION",
            "five_scores_2026-08-08.json",
            "formules distinctes et traçables",
            "valider poids, bornes et données",
        ),
        _phase(
            "K",
            "sévérité/gates",
            "BLOCKED_NO_CANDIDATE_DISTRIBUTION",
            "severity_and_gate_sensitivity_2026-08-08.json",
            "ladder et sensibilité testées",
            "distribution candidat gouvernée",
        ),
        _phase(
            "L",
            "rapport final",
            "BLOCKED_BY_DATA",
            "final_pre_opra_report_2026-08-08.html",
            "rendu statique cohérent",
            "lever les bloqueurs avant OPRA",
        ),
    ]
    return FinalPreOpraReport(
        schema_version="1.0",
        report_id="ttwo-final-pre-opra-v1",
        ticker="TTWO",
        overall_status="BLOCKED_BY_DATA",
        evidence_grade="software_tested_only",
        decision="NO_POSITION_RECOMMENDED",
        decision_scope="research_only_not_investment_advice",
        run_manifest=manifest,
        phase_results=phases,
        key_metrics={
            "private_option_envelopes": 1998,
            "private_option_rows": 46413,
            "option_dates": 250,
            "price_observations": 616,
            "return_observations": 615,
            "annualized_realized_volatility": 0.2965765,
            "excess_kurtosis": 6.96457,
            "maximum_drawdown": 0.27664,
            "walk_forward_windows": 7,
            "comparable_strategy_panels": 0,
            "validated_surface_dates": 0,
            "governed_events": 0,
        },
        score_status={
            "opportunity": "unavailable",
            "risk": "unavailable",
            "evidence": "unavailable",
            "model_agreement": "unavailable",
            "execution_quality": "unavailable",
        },
        best_blocked_candidate="UNAVAILABLE",
        blockers=[
            "Historical option-data licensing remains to_review.",
            "No aligned comparable panel exists for all nine mandatory strategies.",
            "Historical IV/delta, governed rates and dividends are incomplete.",
            "No governed point-in-time event history exists.",
            "The five score formulas and thresholds remain draft_to_validate.",
            "The final holdout is unprovisioned and intentionally UNOPENED.",
        ],
        opra_readiness=[
            "Obtain authorized OPRA access and document storage/redistribution rights.",
            "Ingest append-only raw snapshots with checksums and point-in-time timestamps.",
            "Run shadow/paper validation; do not add order capability.",
            "Keep Phase M separate and require explicit user validation before starting it.",
        ],
        external_source_ids=[
            "Market Data terms and option-chain documentation",
            "Alpaca historical options and subscription documentation",
            "SEC EDGAR API documentation",
        ],
        holdout_state="UNOPENED",
        holdout_used=False,
        phase_m_started=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at", required=True)
    args = parser.parse_args()
    report = build(datetime.fromisoformat(args.generated_at))
    REPORTS.mkdir(parents=True, exist_ok=True)
    stem = REPORTS / "final_pre_opra_report_2026-08-08"
    stem.with_suffix(".json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    stem.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    stem.with_suffix(".html").write_text(render_html(report), encoding="utf-8")
    (REPORTS / "run_manifest_2026-08-08.json").write_text(
        json.dumps(report.run_manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
