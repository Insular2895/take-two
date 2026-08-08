import math
from statistics import fmean

import pytest

from take_two_options.simulation.exit_state import (
    ExitState,
    advance_exit_state,
    initial_exit_state,
)
from take_two_options.simulation.path_execution import PathExecutionResult
from take_two_options.simulation.uncertainty import (
    antithetic_estimate,
    circular_block_bootstrap,
    compare_exit_discretizations,
    control_variate_estimate,
    effective_sample_size,
    estimate_path_probabilities,
    estimate_probability,
)


def test_exit_state_machine_is_serializable_chronological_and_terminal() -> None:
    initial = initial_exit_state(-2.0)
    open_state = advance_exit_state(
        initial,
        day=1,
        pnl=1.0,
        return_on_risk=0.1,
        is_final_checkpoint=False,
        profit_target=0.5,
        stop_loss=0.4,
    )
    terminal = advance_exit_state(
        open_state,
        day=2,
        pnl=6.0,
        return_on_risk=0.6,
        is_final_checkpoint=False,
        profit_target=0.5,
        stop_loss=0.4,
    )

    assert terminal.state is ExitState.PROFIT_TARGET
    assert terminal.exit_day == 2
    assert terminal.model_dump(mode="json")["state"] == "profit_target"
    with pytest.raises(ValueError, match="terminal"):
        advance_exit_state(
            terminal,
            day=3,
            pnl=7.0,
            return_on_risk=0.7,
            is_final_checkpoint=True,
            profit_target=0.5,
            stop_loss=0.4,
        )
    with pytest.raises(ValueError, match="chronological"):
        advance_exit_state(
            open_state,
            day=1,
            pnl=0.0,
            return_on_risk=0.0,
            is_final_checkpoint=True,
            profit_target=None,
            stop_loss=None,
        )


def test_exit_state_tracks_drawdown_and_contractual_time_exit() -> None:
    first = advance_exit_state(
        initial_exit_state(-1.0),
        day=1,
        pnl=5.0,
        return_on_risk=0.25,
        is_final_checkpoint=False,
        profit_target=None,
        stop_loss=None,
    )
    final = advance_exit_state(
        first,
        day=2,
        pnl=2.0,
        return_on_risk=0.1,
        is_final_checkpoint=True,
        profit_target=None,
        stop_loss=None,
    )

    assert final.state is ExitState.TIME_EXIT
    assert final.maximum_drawdown == 3.0


def test_wilson_probability_exposes_rare_event_and_minimum_path_uncertainty() -> None:
    report = estimate_probability([False] * 50, minimum_paths=1_000)

    assert report.estimate == 0.0
    assert report.lower == 0.0
    assert report.upper is not None and report.upper > 0
    assert report.sufficient_paths is False
    assert report.interval_method == "wilson_binomial_iid"


def test_weighted_probability_reports_ess_without_fake_binomial_interval() -> None:
    report = estimate_probability(
        [True, False, True, False],
        weights=[100.0, 1.0, 1.0, 1.0],
        minimum_paths=2,
    )

    assert report.estimate == pytest.approx(101 / 103)
    assert report.effective_sample_size == pytest.approx(103**2 / 10003)
    assert report.sufficient_paths is False
    assert report.lower is None and report.upper is None
    assert report.interval_method == "not_available_for_weighted_paths"
    assert effective_sample_size([1.0, 1.0, 1.0]) == 3.0


def test_all_canonical_path_probabilities_receive_uncertainty_sidecars() -> None:
    results = [
        PathExecutionResult(60.0, 2, "profit_target", 1.0),
        PathExecutionResult(-80.0, 3, "stop_loss", 80.0),
        PathExecutionResult(10.0, 4, "time_exit", 3.0),
    ]
    report = estimate_path_probabilities(results, maximum_loss=100.0, minimum_paths=100)

    assert set(report.probabilities) == {
        "probability_profit",
        "probability_gain_50",
        "probability_gain_80",
        "probability_gain_100",
        "probability_loss_50",
        "probability_loss_70",
        "probability_near_total_loss",
        "take_profit_frequency",
        "stop_frequency",
    }
    assert report.probabilities["probability_profit"].estimate == pytest.approx(2 / 3)
    assert all(not value.sufficient_paths for value in report.probabilities.values())


def test_control_variate_reports_measured_variance_reduction() -> None:
    controls = [float(value) for value in range(-20, 21)]
    noise = [0.2 * math.sin(value) for value in controls]
    payoffs = [2.0 * control + error + 5.0 for control, error in zip(controls, noise, strict=True)]
    report = control_variate_estimate(payoffs, controls, expected_control=0.0)

    assert report.adjusted_mean == pytest.approx(5.0, abs=0.02)
    assert report.adjusted_replication_variance < report.baseline_replication_variance
    assert report.adjusted_standard_error < report.baseline_standard_error
    assert report.variance_reduction_factor is not None
    assert report.variance_reduction_factor > 1_000


def test_antithetic_pairs_are_independent_replications_for_standard_error() -> None:
    normals = [value / 10 for value in range(-30, 31)]
    pairs = [(math.exp(value), math.exp(-value)) for value in normals]
    report = antithetic_estimate(pairs)

    assert report.observations == 2 * len(pairs)
    assert report.independent_replications == len(pairs)
    assert report.adjusted_replication_variance < report.baseline_replication_variance
    assert report.adjusted_standard_error < report.baseline_standard_error


def test_circular_block_bootstrap_is_seeded_and_preserves_dependency_blocks() -> None:
    values = [float(index // 5) for index in range(100)]
    first = circular_block_bootstrap(values, fmean, block_size=5, samples=200, seed=23)
    second = circular_block_bootstrap(values, fmean, block_size=5, samples=200, seed=23)

    assert first == second
    assert first.lower < first.estimate < first.upper
    assert first.block_size == 5


def test_exit_discretization_gap_must_be_measured_before_lsm_expansion() -> None:
    coarse = [
        PathExecutionResult(10.0, 2, "time_exit", 1.0),
        PathExecutionResult(-5.0, 2, "stop_loss", 6.0),
    ]
    fine = [
        PathExecutionResult(12.0, 3, "profit_target", 1.0),
        PathExecutionResult(-5.5, 2, "stop_loss", 6.5),
    ]
    report = compare_exit_discretizations(coarse, fine, materiality_tolerance=1.0)

    assert report.reason_mismatches == 1
    assert report.day_mismatches == 1
    assert report.maximum_absolute_pnl_difference == 2.0
    assert report.material_gap is True
