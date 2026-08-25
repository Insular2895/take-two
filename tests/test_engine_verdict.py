from __future__ import annotations

from pathlib import Path

from take_two_options.decision.engine_verdict import (
    EngineValueVerdict,
    EngineVerdictReport,
    derive_engine_value_verdict,
)

ROOT = Path(__file__).resolve().parents[1]


def test_stable_development_and_oos_losses_derive_not_proven_superior() -> None:
    verdict, _ = derive_engine_value_verdict(
        full_engine_expected_return=-0.03,
        full_engine_total_return=-0.99,
        oos_engine_expected_return=-0.01,
        oos_engine_total_return=-0.90,
        cash_expected_return=0,
        holm_superiority_rejections=0,
        formal_sample_policy_satisfied=False,
        holdout_used=False,
    )
    assert verdict is EngineValueVerdict.ENGINE_NOT_PROVEN_SUPERIOR


def test_protocol_failure_has_priority_over_economic_result() -> None:
    verdict, _ = derive_engine_value_verdict(
        full_engine_expected_return=0.10,
        full_engine_total_return=0.20,
        oos_engine_expected_return=0.10,
        oos_engine_total_return=0.20,
        cash_expected_return=0,
        holm_superiority_rejections=4,
        formal_sample_policy_satisfied=True,
        holdout_used=True,
    )
    assert verdict is EngineValueVerdict.VALIDATION_FAILED


def test_committed_engine_verdict_is_derived_and_fail_closed() -> None:
    report = EngineVerdictReport.model_validate_json(
        (ROOT / "reports/pre_opra/engine_verdict_2026-08-08.json").read_text()
    )
    assert report.verdict is EngineValueVerdict.ENGINE_NOT_PROVEN_SUPERIOR
    assert report.engine_full_development.total_return < 0
    assert report.engine_walk_forward_oos.total_return < 0
    assert report.best_simple_baseline_oos.strategy == "buy_and_hold"
    assert report.holm_superiority_rejections == 0
    assert report.no_position_recommended
    assert report.holdout_state == "UNOPENED"
    assert report.holdout_used is False
