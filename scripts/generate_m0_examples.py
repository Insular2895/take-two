"""Generate deterministic synthetic M0.1 trade-economics golden artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from take_two_options.candidates import generate_candidates
from take_two_options.data import FixtureDataProvider
from take_two_options.decision.quality_scores import FiveScoreReport
from take_two_options.pricing import analyze_risk
from take_two_options.quantitative.contracts import Measure
from take_two_options.quantitative.trade_economics import (
    build_trade_economics_ticket,
    calculate_distribution_pnl_metrics,
)
from take_two_options.reporting.trade_economics import render_trade_economics_markdown
from take_two_options.trade_economics_models import (
    ProbabilityPnLValuationRule,
    ProbabilityStatus,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    bundle = FixtureDataProvider(ROOT / "fixtures/ttwo_v1_fixture.json").load_bundle()
    config = bundle.trade_economics
    config.time_decay_horizons_days = [1, 7, 30, 60, 90]
    config.scenario_horizons_days = [7, 30, 60, 90]
    config.spot_grid.values = [0.70, 0.85, 1.0, 1.15, 1.30]
    config.volatility_scenarios = config.volatility_scenarios[:3]
    config.greek_bumps.grid_levels = [100, 200]
    config.breakeven_solver.grid_points = 401
    config.exit_cost_model.exercise_cost = 0.0
    config.exit_cost_model.assignment_cost = 0.0
    config.exit_cost_model.settlement_cost = 0.0
    candidate = next(item for item in generate_candidates(bundle) if item.id == "ttwo-long-call")
    analyze_risk(candidate, bundle)
    five_scores = FiveScoreReport.model_validate_json(
        (ROOT / "reports/pre_opra/five_scores_2026-08-08.json").read_text(encoding="utf-8")
    )
    ticket = build_trade_economics_ticket(
        candidate,
        bundle,
        fixture_status="SYNTHETIC_TEST_FIXTURE",
        canonical_five_score_report=five_scores,
    )
    output = ROOT / "reports/examples"
    output.mkdir(parents=True, exist_ok=True)
    (output / "m0_trade_economics_ticket.json").write_text(
        ticket.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "m0_trade_economics_ticket.md").write_text(
        render_trade_economics_markdown(ticket),
        encoding="utf-8",
    )
    probability_paths = [
        [257.79, 220.0],
        [257.79, 260.0],
        [257.79, 300.0],
        [257.79, 360.0],
    ]
    probability_fixture = calculate_distribution_pnl_metrics(
        candidate,
        bundle,
        close_exit_cost=ticket.exit_cost_estimate,
        spot_paths=probability_paths,
        spot_path_horizon_days=30,
        spot_path_valuation_rule=(ProbabilityPnLValuationRule.CONSTANT_LEG_IV_PATH_VALUATION),
        model="SYNTHETIC_EQUAL_WEIGHT_P_PATHS",
        measure=Measure.REAL_WORLD,
        calibration_status=ProbabilityStatus.MODEL_IMPLIED,
    )
    (output / "m0_1_probability_distribution_fixture.json").write_text(
        json.dumps(
            {
                "fixture_status": "SYNTHETIC_TEST_FIXTURE",
                "ticket_schema_version": "1.1",
                "probability_paths": probability_paths,
                "distribution_pnl": probability_fixture.model_dump(mode="json"),
                "holdout_used": False,
                "order_capability": "forbidden",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("Generated synthetic M0.1 JSON, Markdown, and probability artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
