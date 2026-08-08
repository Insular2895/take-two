from __future__ import annotations

import json
from pathlib import Path

import pytest

from take_two_options.validation.baseline_comparison import (
    MANDATORY_STRATEGIES,
    BaselineComparisonReport,
    ComparableStrategy,
    ComparisonConventions,
    EffectiveSearchSpace,
    StrategyReturnSeries,
    compare_with_baselines,
    holm_adjust,
)

ROOT = Path(__file__).resolve().parents[1]


def _conventions() -> ComparisonConventions:
    return ComparisonConventions(
        horizon="20_sessions",
        capital=10_000,
        currency="USD",
        fees="same explicit fee schedule",
        spread_assumption="same half-spread convention",
        fx_policy="none: USD capital and instruments",
        entry_convention="decision close",
        exit_convention="twenty-session close",
        target_return=0.02,
        large_loss_threshold=0.10,
    )


def _space() -> EffectiveSearchSpace:
    return EffectiveSearchSpace(
        strategies_considered=9,
        contracts_considered=4,
        expirations_considered=3,
        parameter_sets_considered=2,
        model_sets_considered=2,
        exit_rules_considered=2,
        actual_trials=18,
        cartesian_upper_bound=864,
    )


def _series(strategy: ComparableStrategy, offset: float) -> StrategyReturnSeries:
    returns = [offset + (0.015 if index % 2 else -0.005) for index in range(20)]
    return StrategyReturnSeries(
        strategy=strategy,
        observation_ids=[f"obs-{index:02d}" for index in range(20)],
        gross_returns=[value + 0.001 for value in returns],
        net_returns=returns,
        transaction_costs=[0.001] * 20,
    )


def test_holm_adjustment_is_order_preserving_and_monotone() -> None:
    assert holm_adjust([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_complete_synthetic_panel_compares_every_baseline_without_holdout() -> None:
    panel = [
        _series(strategy, 0.01 if strategy is ComparableStrategy.ENGINE_CANDIDATE else 0.0)
        for strategy in MANDATORY_STRATEGIES
    ]
    report = compare_with_baselines(
        panel,
        ticker="XYZ",
        dataset_hash="a" * 64,
        conventions=_conventions(),
        search_space=_space(),
        alpha=0.05,
        minimum_material_uplift=0.005,
        bootstrap_samples=100,
        permutation_samples=200,
        seed=7,
        synthetic=True,
    )
    assert report.status == "FIXTURE_ONLY_NOT_VALIDATED"
    assert len(report.rows) == 9
    assert len(report.deltas) == 8
    assert all(delta.expected_return_uplift > 0 for delta in report.deltas)
    assert report.holdout_used is False


def test_missing_mandatory_strategies_fail_closed() -> None:
    report = compare_with_baselines(
        [_series(ComparableStrategy.CASH, 0.0)],
        ticker="XYZ",
        dataset_hash="b" * 64,
        conventions=_conventions(),
        search_space=_space(),
        alpha=0.05,
        minimum_material_uplift=0.005,
    )
    assert report.status == "BLOCKED_INCOMPARABLE_DATA"
    assert ComparableStrategy.ENGINE_CANDIDATE in report.missing_strategies


def test_misaligned_observations_are_rejected() -> None:
    panel = [_series(strategy, 0.0) for strategy in MANDATORY_STRATEGIES]
    panel[-1] = panel[-1].model_copy(update={"observation_ids": [f"x-{i}" for i in range(20)]})
    with pytest.raises(ValueError, match="identically ordered"):
        compare_with_baselines(
            panel,
            ticker="XYZ",
            dataset_hash="c" * 64,
            conventions=_conventions(),
            search_space=_space(),
            alpha=0.05,
            minimum_material_uplift=0.005,
        )


def test_committed_real_report_is_blocked_without_invented_performance() -> None:
    report = BaselineComparisonReport.model_validate_json(
        (ROOT / "reports/pre_opra/baseline_comparison_2026-08-08.json").read_text()
    )
    assert report.status == "BLOCKED_INCOMPARABLE_DATA"
    assert report.rows == []
    assert set(report.missing_strategies) == set(MANDATORY_STRATEGIES)
    raw = json.loads(
        (ROOT / "reports/pre_opra/baseline_comparison_2026-08-08.json").read_text()
    )
    assert raw["holdout_used"] is False
