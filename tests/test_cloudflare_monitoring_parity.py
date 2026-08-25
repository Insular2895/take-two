from __future__ import annotations

import json
from pathlib import Path

import pytest

from take_two_options.intelligence.monitoring import monitor_position
from take_two_options.intelligence.schemas import PositionDossier, PositionMonitorInput

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "fixtures/cloudflare/monitoring_parity.json").read_text(encoding="utf-8")
)


def _dossier() -> PositionDossier:
    rule = lambda rule_id, threshold, action: {  # noqa: E731
        "rule_id": rule_id,
        "description": f"Synthetic parity rule: {rule_id}",
        "threshold": threshold,
        "severity": "warning",
        "suggested_action": action,
        "required_data": [],
    }
    return PositionDossier.model_validate(
        {
            "dossier_id": FIXTURE["fixture_id"],
            "candidate_id": "synthetic-bull-call-spread",
            "opened_at": "2026-08-01T14:30:00Z",
            "initial_scenario_probabilities": {"bear": 0.2, "base": 0.5, "bull": 0.3},
            "initial_distribution_source": "SYNTHETIC_PARITY_FIXTURE",
            "initial_spot": 245.0,
            "initial_iv": 0.39,
            "initial_rate": 0.04,
            "initial_greeks": {
                "delta": 0.61,
                "gamma": 0.012,
                "theta": -0.21,
                "vega": 0.34,
                "rho": 0.15,
            },
            "initial_regime": "base",
            "expected_catalysts": [],
            "invalidation_conditions": [],
            "entry_price_usd": FIXTURE["entry_cash"],
            "actual_cost_usd": FIXTURE["entry_cash"],
            "actual_slippage_usd": 3.0,
            "exit_plan": {
                "candidate_id": "synthetic-bull-call-spread",
                "profit_target": 0.50,
                "partial_profit_target": 0.45,
                "operational_stop_loss": 0.30,
                "exit_days_before_expiration": 21,
                "iv_crush_threshold": 0.30,
                "trailing_drawdown": 0.20,
                "fundamental_invalidations": [],
                "temporal_invalidation": "none",
                "iv_invalidation": "30 percent crush",
                "catalyst_rule": "none",
                "trailing_rule": "20 percent of entry cost",
                "rules": [
                    rule("fundamental_invalidation", True, "THESIS_INVALIDATED"),
                    rule("data_insufficient", True, "BLOCKED_INSUFFICIENT_DATA"),
                    rule("data_stale", False, "DATA_STALE"),
                    rule("operational_stop_loss", 0.30, "EXIT_REVIEW"),
                    rule("time_exit", 21, "EXIT_REVIEW"),
                    rule("profit_target", 0.50, "EXIT_REVIEW"),
                    rule("partial_profit_target", 0.45, "REDUCE"),
                    rule("iv_crush", 0.30, "EXIT_REVIEW"),
                    rule("theta_limit", 0.50, "WATCH"),
                    rule("trailing_drawdown", 0.20, "EXIT_REVIEW"),
                ],
            },
            "state": "paper_open",
            "human_actor": "synthetic-test",
        }
    )


def _input(overrides: dict[str, object]) -> PositionMonitorInput:
    baseline: dict[str, object] = {
        "as_of": "2026-08-24T14:30:30Z",
        "current_spot": 268.0,
        "market_value_usd": FIXTURE["baseline"]["market_value"],
        "realized_pnl_usd": 0.0,
        "current_iv": 0.37,
        "current_rate": 0.04,
        "current_greeks": {"theta": -0.19},
        "current_scenario_probabilities": {"bear": 0.2, "base": 0.5, "bull": 0.3},
        "days_to_expiration": 144,
        "regime": "base",
        "execution_impact_usd": 9.0,
        "prudent_liquidation_value_usd": FIXTURE["baseline"]["liquidation_value"],
        "peak_prudent_liquidation_value_usd": FIXTURE["baseline"]["liquidation_value"],
        "expected_remaining_pnl_usd": FIXTURE["baseline"]["expected_remaining_pnl"],
        "data_fresh": True,
        "data_sufficient": True,
    }
    return PositionMonitorInput.model_validate({**baseline, **overrides})


@pytest.mark.parametrize("case", FIXTURE["cases"], ids=lambda case: case["case_id"])
def test_python_monitor_matches_cross_language_golden(case: dict[str, object]) -> None:
    report = monitor_position(_dossier(), _input(case["overrides"]))
    assert report.action.value == case["expected_action"]
    if case["case_id"] == "hold":
        assert report.unrealized_pnl_usd == pytest.approx(FIXTURE["baseline"]["mtm_pnl"])
        assert report.prudent_liquidation_pnl_usd == pytest.approx(
            FIXTURE["baseline"]["liquidation_pnl"]
        )
