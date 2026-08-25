from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from take_two_options.validation.experiment_protocol import (
    HoldoutAccessLedger,
    PointInTimeObservation,
    build_point_in_time_split,
    create_experiment_manifest,
    verify_experiment_manifest,
)
from take_two_options.validation.pbo import probability_of_backtest_overfitting
from take_two_options.validation.placebo import placebo_diagnostics


def test_placebo_uses_signal_alignment_and_has_power_on_synthetic_signal() -> None:
    rng = random.Random(17)
    signals = [1.0 if rng.random() > 0.5 else -1.0 for _ in range(160)]
    returns = [0.015 * signal + rng.gauss(0.0, 0.01) for signal in signals]

    results, passed = placebo_diagnostics(
        returns,
        signals=signals,
        seed=29,
        permutations=999,
    )

    assert passed is True
    assert results["permutation_p_value"] <= 0.05
    assert results["observed_signal_return_mean"] > results["permutation_null_mean"]


def test_placebo_refuses_mean_shuffle_without_signal_history() -> None:
    results, passed = placebo_diagnostics([0.01, -0.02] * 10, seed=7)
    assert results == {"available_observations": 20.0}
    assert passed is None


def test_placebo_null_is_deterministic_and_not_forced_to_pass() -> None:
    rng = random.Random(31)
    signals = [1.0 if rng.random() > 0.5 else -1.0 for _ in range(200)]
    returns = [rng.gauss(0.0, 0.01) for _ in signals]
    first = placebo_diagnostics(returns, signals=signals, seed=11, permutations=999)
    second = placebo_diagnostics(returns, signals=signals, seed=11, permutations=999)
    assert first == second
    assert first[1] is not True


def test_pbo_ties_are_order_invariant_and_midranked() -> None:
    matrix = [
        [0.1, 0.1, -0.1, -0.1],
        [0.1, 0.1, 0.1, 0.1],
        [-0.1, -0.1, 0.1, 0.1],
    ]
    original = probability_of_backtest_overfitting(matrix)
    reversed_order = probability_of_backtest_overfitting(list(reversed(matrix)))

    assert original is not None
    assert original == pytest.approx(reversed_order)
    assert 0 <= original <= 1


def test_experiment_manifest_hash_covers_code_config_data_seed_and_trials() -> None:
    manifest = create_experiment_manifest(
        manifest_id="experiment-001",
        created_at=datetime(2026, 8, 8, tzinfo=UTC),
        code_commit="abcdef1",
        code_version="0.11.1",
        config_hash="a" * 64,
        dataset_id="synthetic-validation",
        dataset_hash="b" * 64,
        split_policy_hash="c" * 64,
        trial_registry_hash="d" * 64,
        seed=17,
        synthetic=True,
    )
    assert verify_experiment_manifest(manifest)
    assert not verify_experiment_manifest(manifest.model_copy(update={"seed": 18}))


def _observations() -> list[PointInTimeObservation]:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        PointInTimeObservation(
            observation_id=f"observation-{index:03d}",
            feature_start=start + timedelta(days=index - 2),
            decision_time=start + timedelta(days=index),
            label_end=start + timedelta(days=index + 2),
            available_at=start + timedelta(days=index),
        )
        for index in range(40)
    ]


def test_point_in_time_split_purges_boundaries_and_hides_holdout_ids() -> None:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    closed = build_point_in_time_split(
        _observations(),
        train_end=start + timedelta(days=14),
        validation_end=start + timedelta(days=22),
        test_end=start + timedelta(days=30),
        final_holdout_end=start + timedelta(days=39),
        embargo_days=1,
    )
    opened = build_point_in_time_split(
        _observations(),
        train_end=start + timedelta(days=14),
        validation_end=start + timedelta(days=22),
        test_end=start + timedelta(days=30),
        final_holdout_end=start + timedelta(days=39),
        embargo_days=1,
        open_final_holdout=True,
    )

    assert closed.status == "completed"
    assert not closed.final_holdout_opened and closed.final_holdout_ids == ()
    assert closed.final_holdout_count == len(opened.final_holdout_ids)
    assert closed.purged_ids
    partitions = [
        set(closed.train_ids),
        set(closed.validation_ids),
        set(closed.test_ids),
        set(opened.final_holdout_ids),
    ]
    assert all(
        not left & right
        for index, left in enumerate(partitions)
        for right in partitions[index + 1 :]
    )


def test_point_in_time_observation_rejects_post_decision_availability() -> None:
    now = datetime(2025, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="look-ahead"):
        PointInTimeObservation(
            observation_id="leak",
            feature_start=now,
            decision_time=now,
            label_end=now + timedelta(days=1),
            available_at=now + timedelta(seconds=1),
        )


def test_holdout_ledger_is_hash_chained_one_time_and_blocks_retuning() -> None:
    ledger = HoldoutAccessLedger()
    now = datetime(2026, 8, 8, tzinfo=UTC)
    ledger.register(
        accessed_at=now,
        action="seal",
        holdout_id="fresh-holdout",
        dataset_hash="e" * 64,
        code_commit="abcdef1",
        purpose="seal before model selection",
    )
    ledger.register(
        accessed_at=now + timedelta(hours=1),
        action="evaluate",
        holdout_id="fresh-holdout",
        dataset_hash="e" * 64,
        code_commit="abcdef1",
        purpose="one authorized final evaluation",
    )
    ledger.register(
        accessed_at=now + timedelta(hours=2),
        action="report",
        holdout_id="fresh-holdout",
        dataset_hash="e" * 64,
        code_commit="abcdef1",
        purpose="publish unchanged result",
    )
    assert ledger.verify()
    with pytest.raises(ValueError, match="only once"):
        ledger.register(
            accessed_at=now + timedelta(hours=3),
            action="evaluate",
            holdout_id="fresh-holdout",
            dataset_hash="e" * 64,
            code_commit="abcdef1",
            purpose="second evaluation",
        )
    with pytest.raises(ValueError, match="tuning is forbidden"):
        ledger.register(
            accessed_at=now + timedelta(hours=3),
            action="tune",
            holdout_id="fresh-holdout",
            dataset_hash="e" * 64,
            code_commit="abcdef1",
            purpose="retune after viewing result",
        )
