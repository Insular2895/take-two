"""Generate the deterministic synthetic M0 trade-economics golden ticket."""

from __future__ import annotations

from pathlib import Path

from take_two_options.candidates import generate_candidates
from take_two_options.data import FixtureDataProvider
from take_two_options.pricing import analyze_risk
from take_two_options.quantitative.trade_economics import build_trade_economics_ticket
from take_two_options.reporting.trade_economics import render_trade_economics_markdown

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
    candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-long-call"
    )
    analyze_risk(candidate, bundle)
    ticket = build_trade_economics_ticket(
        candidate,
        bundle,
        fixture_status="SYNTHETIC_TEST_FIXTURE",
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
    print("Generated synthetic M0 JSON and Markdown golden tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
