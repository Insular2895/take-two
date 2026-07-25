"""Non-negotiable validation gates with configured minimums preserved."""

from __future__ import annotations

from typing import Literal

from take_two_options.knowledge.schemas import (
    HoldoutPolicy,
    SampleGate,
    ValidationMetrics,
)
from take_two_options.research_statistics import deflated_sharpe_probability
from take_two_options.validation.holdout import holdout_status
from take_two_options.validation.pbo import probability_of_backtest_overfitting


def sample_gate(configured_minimum: int, available_observations: int) -> SampleGate:
    return SampleGate(
        configured_minimum=configured_minimum,
        available_observations=available_observations,
        status=(
            "PASSED"
            if available_observations >= configured_minimum
            else "INSUFFICIENT_DATA"
        ),
    )


def evaluate_validation_gates(
    *,
    policy: HoldoutPolicy,
    train_returns: list[float],
    validation_returns: list[float],
    test_returns: list[float],
    holdout_returns: list[float],
    contaminated_ids: set[str],
    performance_matrix: list[list[float]],
    nested_windows: int,
    purged_observations: int,
    embargo_days: int,
    stability: float | None,
    stress_ok: bool,
    placebo_ok: bool | None,
    real_trial_count: int,
) -> ValidationMetrics:
    train = sample_gate(policy.minimum_train_observations, len(train_returns))
    validation = sample_gate(
        policy.minimum_validation_observations, len(validation_returns)
    )
    test = sample_gate(policy.minimum_test_observations, len(test_returns))
    holdout = sample_gate(policy.minimum_holdout_observations, len(holdout_returns))
    holdout_state, holdout_reasons = holdout_status(
        requested_holdout_id=policy.locked_holdout_id,
        contaminated_ids=contaminated_ids,
        observations=len(holdout_returns),
        configured_minimum=policy.minimum_holdout_observations,
    )
    dsr = deflated_sharpe_probability(test_returns, real_trial_count)
    pbo = probability_of_backtest_overfitting(performance_matrix)
    gates: dict[
        str, Literal["passed", "failed", "insufficient_data", "not_calculable"]
    ] = {
        "sample_train": (
            "passed" if train.status == "PASSED" else "insufficient_data"
        ),
        "sample_validation": (
            "passed" if validation.status == "PASSED" else "insufficient_data"
        ),
        "sample_test": (
            "passed" if test.status == "PASSED" else "insufficient_data"
        ),
        "holdout": (
            "passed"
            if holdout_state == "PASSED"
            else "failed"
            if holdout_state == "CONTAMINATED"
            else "insufficient_data"
        ),
        "nested_walk_forward": "passed" if nested_windows >= 2 else "insufficient_data",
        "deflated_sharpe": "passed" if dsr is not None else "not_calculable",
        "pbo": "passed" if pbo is not None else "not_calculable",
        "parameter_stability": "passed" if stability is not None else "not_calculable",
        "stress": "passed" if stress_ok else "failed",
        "placebo": (
            "passed"
            if placebo_ok is True
            else "failed"
            if placebo_ok is False
            else "not_calculable"
        ),
    }
    insufficient = any(value in {"insufficient_data", "not_calculable"} for value in gates.values())
    failed = any(value == "failed" for value in gates.values())
    status = (
        "CONTAMINATED"
        if holdout_state == "CONTAMINATED"
        else "INSUFFICIENT_DATA"
        if insufficient
        else "FAILED"
        if failed
        else "PASSED"
    )
    reasons = list(holdout_reasons)
    for name, gate_status in gates.items():
        if gate_status != "passed":
            reasons.append(f"{name}={gate_status}")
    return ValidationMetrics(
        status=status,
        train=train,
        validation=validation,
        test=test,
        holdout=holdout,
        nested_walk_forward_windows=nested_windows,
        purged_observations=purged_observations,
        embargo_days=embargo_days,
        deflated_sharpe_probability=dsr,
        pbo=pbo,
        parameter_stability=stability,
        stress_passed=stress_ok,
        placebo_passed=placebo_ok is True,
        gates=gates,
        reasons=reasons,
    )
