"""Derive the pre-OPRA V10 engine-value verdict from committed aggregate evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from take_two_options.decision.engine_verdict import (
    EngineVerdictReport,
    VerdictMetricSnapshot,
    derive_engine_value_verdict,
)


def _snapshot(role: str, row: dict[str, Any]) -> VerdictMetricSnapshot:
    return VerdictMetricSnapshot(
        dataset_role=role,
        strategy=str(row["strategy"]),
        observations=int(row["observations"]),
        total_return=float(row["total_return"]),
        expected_return=float(row["expected_return"]),
        cvar_95=float(row["cvar_95"]),
        maximum_drawdown=float(row["maximum_drawdown"]),
        probability_profit=float(row["probability_profit"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--walk-forward", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = cast(dict[str, Any], json.loads(args.baseline.read_text(encoding="utf-8")))
    walk_forward = cast(
        dict[str, Any], json.loads(args.walk_forward.read_text(encoding="utf-8"))
    )
    scores = cast(dict[str, Any], json.loads(args.scores.read_text(encoding="utf-8")))
    full_rows = cast(list[dict[str, Any]], baseline["rows"])
    oos_comparison = cast(dict[str, Any], walk_forward["oos_strategy_comparison"])
    oos_rows = cast(list[dict[str, Any]], oos_comparison["rows"])
    full_engine = next(row for row in full_rows if row["strategy"] == "engine_candidate")
    oos_engine = next(row for row in oos_rows if row["strategy"] == "engine_candidate")
    full_cash = next(row for row in full_rows if row["strategy"] == "cash")
    full_baselines = [row for row in full_rows if row["strategy"] != "engine_candidate"]
    oos_baselines = [row for row in oos_rows if row["strategy"] != "engine_candidate"]
    best_full = max(full_baselines, key=lambda row: float(row["total_return"]))
    best_oos = max(oos_baselines, key=lambda row: float(row["total_return"]))
    deltas = cast(list[dict[str, Any]], oos_comparison["deltas"])
    superiority_rejections = sum(bool(row["statistically_distinguishable"]) for row in deltas)
    adequacy = cast(dict[str, Any], walk_forward["sample_adequacy"])
    verdict, rule = derive_engine_value_verdict(
        full_engine_expected_return=float(full_engine["expected_return"]),
        full_engine_total_return=float(full_engine["total_return"]),
        oos_engine_expected_return=float(oos_engine["expected_return"]),
        oos_engine_total_return=float(oos_engine["total_return"]),
        cash_expected_return=float(full_cash["expected_return"]),
        holm_superiority_rejections=superiority_rejections,
        formal_sample_policy_satisfied=bool(adequacy["formal_policy_satisfied"]),
        holdout_used=bool(walk_forward["holdout_touched"]),
    )
    multiple = cast(dict[str, Any], oos_comparison["multiple_testing"])
    report = EngineVerdictReport(
        report_id="ttwo-engine-value-verdict-v1",
        ticker="TTWO",
        status="DERIVED_DEVELOPMENT_VERDICT",
        verdict=verdict,
        derivation_rule_version="pre-opra-engine-value-v1",
        derivation_rule=rule,
        engine_full_development=_snapshot("full_development", full_engine),
        engine_walk_forward_oos=_snapshot("walk_forward_oos", oos_engine),
        best_simple_baseline_full=_snapshot("full_development", best_full),
        best_simple_baseline_oos=_snapshot("walk_forward_oos", best_oos),
        compared_baselines=[str(row["strategy"]) for row in full_baselines],
        holm_superiority_rejections=superiority_rejections,
        deflated_sharpe_probability=float(multiple["deflated_sharpe_probability"]),
        probability_backtest_overfitting=float(
            multiple["probability_backtest_overfitting"]
        ),
        formal_sample_policy_satisfied=bool(adequacy["formal_policy_satisfied"]),
        development_classification=str(scores["classification"]),
        no_position_recommended=True,
        blockers=[
            "Formal strategy sample policy is not satisfied (25 available; 41 required).",
            "The final holdout remains UNOPENED.",
            "Historical option-data rights still require human confirmation.",
            "Live OPRA execution evidence is absent by design.",
        ],
        holdout_state="UNOPENED",
        holdout_used=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
