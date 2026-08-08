"""Build severe-loss, gate-sensitivity, and opportunity/risk frontier diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from take_two_options.decision.severity_gates import (
    BestBlockedCandidate,
    CandidateGateInput,
    FailedGate,
    GateSetting,
    OpportunityRiskFrontierPoint,
    SeverityGateReport,
    evaluate_gate_sensitivity,
    mark_pareto_frontier,
    payoff_severity,
)
from take_two_options.validation.comparable_panel import ComparablePanelDataset


def _bounded(value: float) -> float:
    return min(100.0, max(0.0, value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--walk-forward", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    walk_forward = cast(
        dict[str, Any], json.loads(args.walk_forward.read_text(encoding="utf-8"))
    )
    scores = cast(dict[str, Any], json.loads(args.scores.read_text(encoding="utf-8")))
    panel = ComparablePanelDataset.model_validate_json(args.panel.read_text(encoding="utf-8"))
    oos = cast(dict[str, Any], walk_forward["oos_strategy_comparison"])
    rows = cast(list[dict[str, Any]], oos["rows"])
    oos_panel = sorted(panel.observations, key=lambda item: item.signal_date)[15:]
    candidate_returns = [
        next(
            outcome.net_return
            for outcome in observation.outcomes
            if outcome.strategy.value == "engine_candidate"
        )
        for observation in oos_panel
    ]
    severity = payoff_severity(candidate_returns, bootstrap_samples=2_000, seed=20_260_808)
    opportunity_score = float(scores["opportunity"]["score_value"])
    risk_score = float(scores["risk"]["score_value"])
    evidence_score = float(scores["evidence"]["score_value"])
    agreement_score = float(scores["model_agreement"]["score_value"])
    execution_score = float(scores["execution_quality"]["score_value"])
    candidate_gate = CandidateGateInput(
        candidate_id="engine_candidate",
        opportunity_score=opportunity_score,
        risk_score=risk_score,
        evidence_score=evidence_score,
        execution_quality_score=execution_score,
    )
    settings = [
        GateSetting(
            setting_id="permissive-predefined",
            minimum_opportunity=30,
            maximum_risk=70,
            minimum_evidence=30,
            minimum_execution_quality=30,
            status="draft_to_validate",
        ),
        GateSetting(
            setting_id="central-predefined",
            minimum_opportunity=45,
            maximum_risk=50,
            minimum_evidence=40,
            minimum_execution_quality=50,
            status="draft_to_validate",
        ),
        GateSetting(
            setting_id="strict-predefined",
            minimum_opportunity=60,
            maximum_risk=35,
            minimum_evidence=60,
            minimum_execution_quality=70,
            status="draft_to_validate",
        ),
    ]
    gate_rows, no_position_frequency = evaluate_gate_sensitivity(
        [candidate_gate], settings
    )
    central = settings[1]
    failed = []
    gate_values = [
        ("opportunity", opportunity_score, central.minimum_opportunity, "minimum"),
        ("risk", risk_score, central.maximum_risk, "maximum"),
        ("evidence", evidence_score, central.minimum_evidence, "minimum"),
        (
            "execution_quality",
            execution_score,
            central.minimum_execution_quality,
            "minimum",
        ),
    ]
    for name, actual, required, direction in gate_values:
        is_failed = actual < required if direction == "minimum" else actual > required
        if is_failed:
            failed.append(
                FailedGate(
                    name=name,
                    actual=actual,
                    required=required,
                    direction=direction,
                    distance=(required - actual if direction == "minimum" else actual - required),
                    status="failed",
                )
            )

    frontier_points = []
    for row in rows:
        strategy = str(row["strategy"])
        expected = float(row["expected_return"])
        probability_profit = float(row["probability_profit"])
        opportunity = _bounded(
            50 * ((min(max(expected, -0.25), 0.25) + 0.25) / 0.50)
            + 50 * probability_profit
        )
        risk = _bounded(
            50 * float(row["cvar_95"])
            + 30 * float(row["maximum_drawdown"])
            + 20 * float(row["probability_loss_50"])
        )
        if strategy in {"cash", "no_position"}:
            execution = 100.0
        elif strategy in {"underlying", "buy_and_hold"}:
            execution = 85.0
        else:
            execution = execution_score
        frontier_points.append(
            OpportunityRiskFrontierPoint(
                candidate_id=strategy,
                opportunity=opportunity,
                risk=risk,
                evidence=evidence_score,
                model_agreement=agreement_score if strategy == "engine_candidate" else None,
                execution_quality=execution,
                pareto_efficient=False,
                dominated_by=[],
                basis=(
                    "Comparable OOS expected return, probability profit, CVaR, drawdown, "
                    "and P(loss>=50%); frontier indices are not the five-score formulas."
                ),
            )
        )
    frontier = mark_pareto_frontier(frontier_points)
    report = SeverityGateReport(
        schema_version="1.0",
        report_id="ttwo-severity-gates-v2",
        ticker="TTWO",
        status="DEVELOPMENT_ANALYSIS_READY",
        candidate_id="engine_candidate",
        payoff_severity=severity,
        best_blocked_candidate=BestBlockedCandidate(
            candidate_id="engine_candidate",
            selection_status="identified",
            selection_basis=(
                "Only scored engine candidate; closest candidate blocked by central "
                "predefined gate."
            ),
            opportunity_score=opportunity_score,
            failed_gates=failed,
        ),
        gate_sensitivity=gate_rows,
        opportunity_risk_frontier=frontier,
        no_position_frequency=no_position_frequency,
        sensitivity_interpretation="candidate_pool_evaluated",
        blockers=[
            "Only ten non-overlapping OOS option observations are available.",
            "Intervals are wide and are development diagnostics, not final probabilities.",
            "Final holdout remains unopened; historical rights remain to_review.",
            "Live execution quality remains pending OPRA.",
        ],
        holdout_used=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
