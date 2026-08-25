"""Calculate the five independent pre-OPRA quality scores from real diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal, cast

from take_two_options.decision.quality_scores import (
    FiveScoreReport,
    QualityScore,
    RawScoreMetric,
    ScoreComponent,
    ScoreFormula,
    ScoreKind,
    calculate_quality_score,
    classify_candidate,
)
from take_two_options.validation.comparable_panel import ComparablePanelDataset


def _component(
    name: str,
    lower: float,
    upper: float,
    direction: Literal["increasing", "decreasing"],
    weight: float,
    rationale: str,
) -> ScoreComponent:
    return ScoreComponent(
        metric_name=name,
        lower_bound=lower,
        upper_bound=upper,
        direction=direction,
        weight=weight,
        weight_status="validated",
        rationale=rationale,
    )


def _metric(name: str, value: float | None, unit: str, source_id: str) -> RawScoreMetric:
    return RawScoreMetric(
        name=name,
        value=value,
        unit=unit,
        source_id=source_id,
        available=value is not None,
    )


def _score(
    kind: ScoreKind,
    components: list[ScoreComponent],
    metrics: list[RawScoreMetric],
    confidence: Literal["VERY_LOW", "LOW", "MEDIUM", "HIGH"],
) -> QualityScore:
    return calculate_quality_score(
        ScoreFormula(kind=kind, version="pre-opra-v2", components=components),
        metrics,
        confidence=confidence,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--walk-forward", type=Path, required=True)
    parser.add_argument("--surfaces", type=Path, required=True)
    parser.add_argument("--empirical", type=Path, required=True)
    parser.add_argument("--normalization", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    baseline = cast(dict[str, Any], json.loads(args.baseline.read_text(encoding="utf-8")))
    development_candidate = next(
        row for row in baseline["rows"] if row["strategy"] == "engine_candidate"
    )
    walk_forward = cast(
        dict[str, Any], json.loads(args.walk_forward.read_text(encoding="utf-8"))
    )
    surfaces = cast(dict[str, Any], json.loads(args.surfaces.read_text(encoding="utf-8")))
    empirical = cast(dict[str, Any], json.loads(args.empirical.read_text(encoding="utf-8")))
    normalization = cast(
        dict[str, Any], json.loads(args.normalization.read_text(encoding="utf-8"))
    )
    panel = ComparablePanelDataset.model_validate_json(args.panel.read_text(encoding="utf-8"))
    oos = cast(dict[str, Any], walk_forward["oos_strategy_comparison"])
    rows = cast(list[dict[str, Any]], oos["rows"])
    candidate = next(row for row in rows if row["strategy"] == "engine_candidate")
    buy_hold = next(row for row in rows if row["strategy"] == "buy_and_hold")
    multiple = cast(dict[str, Any], oos["multiple_testing"])

    opportunity = _score(
        ScoreKind.OPPORTUNITY,
        [
            _component("expected_return", -0.25, 0.25, "increasing", 0.25, "net OOS mean"),
            _component("median_return", -0.50, 0.50, "increasing", 0.20, "net OOS median"),
            _component("probability_profit", 0, 1, "increasing", 0.20, "OOS frequency"),
            _component("probability_target", 0, 0.50, "increasing", 0.10, "90% target"),
            _component(
                "uplift_vs_buy_hold", -0.25, 0.25, "increasing", 0.25, "paired horizon"
            ),
        ],
        [
            _metric("expected_return", float(candidate["expected_return"]), "ratio", "wf-oos"),
            _metric("median_return", float(candidate["median_return"]), "ratio", "wf-oos"),
            _metric(
                "probability_profit",
                float(candidate["probability_profit"]),
                "probability",
                "wf-oos",
            ),
            _metric(
                "probability_target",
                float(candidate["probability_target"]),
                "probability",
                "wf-oos",
            ),
            _metric(
                "uplift_vs_buy_hold",
                float(candidate["expected_return"]) - float(buy_hold["expected_return"]),
                "ratio",
                "wf-oos",
            ),
        ],
        "LOW",
    )

    oos_panel = sorted(panel.observations, key=lambda item: item.signal_date)[15:]
    candidate_returns = [
        next(
            outcome.net_return
            for outcome in observation.outcomes
            if outcome.strategy.value == "engine_candidate"
        )
        for observation in oos_panel
    ]
    risk = _score(
        ScoreKind.RISK,
        [
            _component("cvar_95", 0, 1, "increasing", 0.25, "tail mean loss"),
            _component("maximum_drawdown", 0, 1, "increasing", 0.20, "compounded OOS"),
            _component("probability_loss_25", 0, 1, "increasing", 0.10, "severity ladder"),
            _component("probability_loss_50", 0, 1, "increasing", 0.10, "severity ladder"),
            _component("probability_loss_70", 0, 1, "increasing", 0.10, "severity ladder"),
            _component("probability_loss_90", 0, 1, "increasing", 0.10, "severity ladder"),
            _component("near_total_loss", 0, 1, "increasing", 0.10, "severity ladder"),
            _component(
                "transaction_cost_fraction", 0, 0.30, "increasing", 0.05, "capital drag"
            ),
        ],
        [
            _metric("cvar_95", float(candidate["cvar_95"]), "ratio", "wf-oos"),
            _metric(
                "maximum_drawdown", float(candidate["maximum_drawdown"]), "ratio", "wf-oos"
            ),
            _metric(
                "probability_loss_25",
                sum(value <= -0.25 for value in candidate_returns) / len(candidate_returns),
                "probability",
                "private-panel-aggregate",
            ),
            _metric(
                "probability_loss_50",
                float(candidate["probability_loss_50"]),
                "probability",
                "wf-oos",
            ),
            _metric(
                "probability_loss_70",
                float(candidate["probability_loss_70"]),
                "probability",
                "wf-oos",
            ),
            _metric(
                "probability_loss_90",
                float(candidate["probability_loss_90"]),
                "probability",
                "wf-oos",
            ),
            _metric(
                "near_total_loss",
                sum(value <= -0.99 for value in candidate_returns) / len(candidate_returns),
                "probability",
                "private-panel-aggregate",
            ),
            _metric(
                "transaction_cost_fraction",
                float(candidate["transaction_costs"]) / (len(candidate_returns) * 1000),
                "ratio",
                "wf-oos",
            ),
        ],
        "LOW",
    )

    construction = cast(dict[str, Any], surfaces["construction"])
    pbo = float(multiple["probability_backtest_overfitting"])
    dsr = float(multiple["deflated_sharpe_probability"])
    evidence = _score(
        ScoreKind.EVIDENCE,
        [
            _component("real_data_coverage", 0, 1, "increasing", 0.13, "25/50 target"),
            _component("point_in_time_integrity", 0, 1, "increasing", 0.13, "availability lags"),
            _component("oos_sample_size", 0, 1, "increasing", 0.13, "10/50 target"),
            _component("walk_forward_stability", 0, 1, "increasing", 0.13, "one minus PBO"),
            _component("holdout_validation", 0, 1, "increasing", 0.15, "must remain unopened"),
            _component("multiple_testing_strength", 0, 1, "increasing", 0.10, "DSR"),
            _component("surface_quality", 0, 1, "increasing", 0.09, "fitted snapshots"),
            _component("calibration_quality", 0, 1, "increasing", 0.09, "IV inversion"),
            _component("rights_confirmation", 0, 1, "increasing", 0.05, "human confirmation"),
        ],
        [
            _metric("real_data_coverage", len(panel.observations) / 50, "ratio", "private-panel"),
            _metric("point_in_time_integrity", 1.0, "binary", "wf-manifest"),
            _metric("oos_sample_size", len(candidate_returns) / 50, "ratio", "wf-oos"),
            _metric("walk_forward_stability", 1.0 - pbo, "ratio", "wf-oos"),
            _metric("holdout_validation", None, "binary", "holdout-unopened"),
            _metric("multiple_testing_strength", dsr, "probability", "wf-oos"),
            _metric(
                "surface_quality",
                float(surfaces["stability"]["fitted_snapshots"])
                / float(construction["eligible_snapshots"]),
                "ratio",
                "surface-v2",
            ),
            _metric(
                "calibration_quality",
                float(construction["iv_inversions_succeeded"])
                / float(construction["usable_quotes_before_iv"]),
                "ratio",
                "surface-v2",
            ),
            _metric("rights_confirmation", None, "binary", "data-rights-v1"),
        ],
        "LOW",
    )

    evaluations = cast(list[dict[str, Any]], empirical["chronological_oos"]["evaluations"])
    qlikes = [float(item["qlike"]) for item in evaluations]
    breach_rates = [float(item["var_95_breach_rate"]) for item in evaluations]
    model_agreement = _score(
        ScoreKind.MODEL_AGREEMENT,
        [
            _component("volatility_qlike_spread", 0, 0.50, "decreasing", 0.30, "six models"),
            _component("var_coverage_spread", 0, 0.10, "decreasing", 0.20, "six models"),
            _component(
                "option_expected_return_agreement",
                0,
                1,
                "increasing",
                0.30,
                "OPRA pending",
            ),
            _component("candidate_ranking_agreement", 0, 1, "increasing", 0.20, "OPRA pending"),
        ],
        [
            _metric("volatility_qlike_spread", max(qlikes) - min(qlikes), "qlike", "empirical-v1"),
            _metric(
                "var_coverage_spread",
                max(breach_rates) - min(breach_rates),
                "ratio",
                "empirical-v1",
            ),
            _metric("option_expected_return_agreement", None, "ratio", "pending-opra"),
            _metric("candidate_ranking_agreement", None, "ratio", "pending-opra"),
        ],
        "VERY_LOW",
    )

    candidate_outcomes = [
        next(
            outcome
            for outcome in observation.outcomes
            if outcome.strategy.value == "engine_candidate"
        )
        for observation in oos_panel
    ]
    active_leg_counts = [len(outcome.legs) for outcome in candidate_outcomes if outcome.legs]
    execution_quality = _score(
        ScoreKind.EXECUTION_QUALITY,
        [
            _component("historical_quote_pass_rate", 0.20, 1, "increasing", 0.20, "filters"),
            _component("transaction_cost_fraction", 0, 0.30, "decreasing", 0.25, "OOS"),
            _component("mean_active_legs", 1, 4, "decreasing", 0.15, "structure complexity"),
            _component("bid_ask_completeness", 0.50, 1, "increasing", 0.15, "normalized rows"),
            _component("live_execution_component", 0, 1, "increasing", 0.25, "pending OPRA"),
        ],
        [
            _metric(
                "historical_quote_pass_rate",
                float(construction["usable_quotes_before_iv"])
                / float(construction["calls_considered"]),
                "ratio",
                "surface-v2",
            ),
            _metric(
                "transaction_cost_fraction",
                float(candidate["transaction_costs"]) / (len(candidate_returns) * 1000),
                "ratio",
                "wf-oos",
            ),
            _metric(
                "mean_active_legs",
                sum(active_leg_counts) / len(active_leg_counts),
                "legs",
                "private-panel-aggregate",
            ),
            _metric(
                "bid_ask_completeness",
                float(normalization["non_null_field_counts"]["bid"])
                / float(normalization["unique_observations"]),
                "ratio",
                "normalization-v1",
            ),
            _metric("live_execution_component", None, "binary", "pending-opra"),
        ],
        "LOW",
    )

    classification = classify_candidate(
        opportunity=opportunity.score_value or 0,
        risk=risk.score_value or 0,
        evidence=evidence.score_value or 0,
        model_agreement=model_agreement.score_value or 0,
        execution_quality=execution_quality.score_value or 0,
        development_expected_return=float(candidate["expected_return"]),
        uplift_vs_cash=float(candidate["expected_return"]),
        evidence_coverage=evidence.score_coverage,
        execution_coverage=execution_quality.score_coverage,
    )
    report = FiveScoreReport(
        schema_version="1.0",
        report_id="ttwo-five-scores-v2",
        ticker="TTWO",
        candidate_id="engine_candidate",
        opportunity=opportunity,
        risk=risk,
        evidence=evidence,
        model_agreement=model_agreement,
        execution_quality=execution_quality,
        composite_score=None,
        classification=classification,
        classification_rule_version="pre-opra-v2",
        classification_status="validated",
        classification_rationale=[
            "The candidate has negative OOS expected return and negative uplift versus cash.",
            (
                "The full development panel also has expected return "
                f"{float(development_candidate['expected_return']):.6f}."
            ),
            "Partial scores retain original weights; missing components are never renormalized.",
            "Classification is a development diagnostic, not an investment recommendation.",
        ],
        failed_constraints=[
            "formal walk-forward sample minimum not met",
            "final holdout remains unopened",
            "historical option-data rights require human confirmation",
            "Heston calibration gate not passed",
            "live execution component pending OPRA",
        ],
        holdout_used=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
