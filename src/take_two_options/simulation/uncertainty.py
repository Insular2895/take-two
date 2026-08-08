"""Measured uncertainty and variance-reduction diagnostics for simulation outputs."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from random import Random
from statistics import fmean, variance
from typing import Literal

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.research_statistics import empirical_quantile, wilson_interval
from take_two_options.simulation.path_execution import PathExecutionResult


class ProbabilityEstimate(StrictModel):
    estimate: float = Field(ge=0, le=1)
    successes: int = Field(ge=0)
    paths: int = Field(gt=0)
    effective_sample_size: float = Field(gt=0)
    minimum_paths: int = Field(gt=0)
    sufficient_paths: bool
    interval_method: Literal["wilson_binomial_iid", "not_available_for_weighted_paths"]
    confidence: float = Field(gt=0, lt=1)
    lower: float | None = Field(default=None, ge=0, le=1)
    upper: float | None = Field(default=None, ge=0, le=1)


class VarianceReductionReport(StrictModel):
    method: Literal["control_variate", "antithetic"]
    observations: int = Field(gt=1)
    independent_replications: int = Field(gt=1)
    baseline_mean: float
    adjusted_mean: float
    baseline_replication_variance: float = Field(ge=0)
    adjusted_replication_variance: float = Field(ge=0)
    baseline_standard_error: float = Field(ge=0)
    adjusted_standard_error: float = Field(ge=0)
    variance_reduction_factor: float | None = Field(default=None, ge=0)
    coefficient: float | None = None


class BlockBootstrapReport(StrictModel):
    estimate: float
    lower: float
    upper: float
    confidence: float = Field(gt=0, lt=1)
    samples: int = Field(ge=100)
    block_size: int = Field(gt=0)
    observations: int = Field(gt=1)
    seed: int
    method: Literal["circular_moving_block_bootstrap"] = "circular_moving_block_bootstrap"


class ExitDiscretizationReport(StrictModel):
    paths: int = Field(gt=0)
    reason_mismatches: int = Field(ge=0)
    day_mismatches: int = Field(ge=0)
    mean_pnl_difference: float
    maximum_absolute_pnl_difference: float = Field(ge=0)
    materiality_tolerance: float = Field(ge=0)
    material_gap: bool


class SimulationProbabilityReport(StrictModel):
    maximum_loss_basis: float = Field(gt=0)
    probabilities: dict[str, ProbabilityEstimate]


def effective_sample_size(weights: Sequence[float]) -> float:
    if not weights:
        raise ValueError("effective sample size requires weights")
    if any(not math.isfinite(weight) or weight <= 0 for weight in weights):
        raise ValueError("weights must be finite and strictly positive")
    total = sum(weights)
    return total * total / sum(weight * weight for weight in weights)


def estimate_probability(
    outcomes: Sequence[bool],
    *,
    weights: Sequence[float] | None = None,
    confidence: float = 0.95,
    minimum_paths: int = 1_000,
) -> ProbabilityEstimate:
    """Estimate a binary probability without pretending weighted paths are iid trials."""

    if not outcomes:
        raise ValueError("probability estimation requires outcomes")
    if minimum_paths <= 0:
        raise ValueError("minimum_paths must be positive")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be strictly between zero and one")
    successes = sum(outcomes)
    if weights is None:
        estimate = successes / len(outcomes)
        ess = float(len(outcomes))
        lower, upper = wilson_interval(successes, len(outcomes), confidence)
        method = "wilson_binomial_iid"
    else:
        if len(weights) != len(outcomes):
            raise ValueError("weights and outcomes must have equal length")
        ess = effective_sample_size(weights)
        weighted_successes = sum(
            weight * outcome for weight, outcome in zip(weights, outcomes, strict=True)
        )
        estimate = weighted_successes / sum(weights)
        lower, upper = None, None
        method = "not_available_for_weighted_paths"
    return ProbabilityEstimate(
        estimate=estimate,
        successes=successes,
        paths=len(outcomes),
        effective_sample_size=ess,
        minimum_paths=minimum_paths,
        sufficient_paths=ess >= minimum_paths,
        interval_method=method,
        confidence=confidence,
        lower=lower,
        upper=upper,
    )


def estimate_path_probabilities(
    results: Sequence[PathExecutionResult],
    *,
    maximum_loss: float,
    confidence: float = 0.95,
    minimum_paths: int = 1_000,
) -> SimulationProbabilityReport:
    """Build interval-bearing sidecars for every canonical path probability."""

    if not results:
        raise ValueError("path probability estimation requires results")
    if maximum_loss <= 0:
        raise ValueError("maximum_loss must be positive")
    pnls = [result.pnl for result in results]
    returns = [pnl / maximum_loss for pnl in pnls]
    outcomes = {
        "probability_profit": [value > 0 for value in pnls],
        "probability_gain_50": [value > 0.5 for value in returns],
        "probability_gain_80": [value > 0.8 for value in returns],
        "probability_gain_100": [value > 1.0 for value in returns],
        "probability_loss_50": [value < -0.5 for value in returns],
        "probability_loss_70": [value < -0.7 for value in returns],
        "probability_near_total_loss": [value < -0.95 for value in returns],
        "take_profit_frequency": [result.exit_reason == "profit_target" for result in results],
        "stop_frequency": [result.exit_reason == "stop_loss" for result in results],
    }
    return SimulationProbabilityReport(
        maximum_loss_basis=maximum_loss,
        probabilities={
            name: estimate_probability(
                values,
                confidence=confidence,
                minimum_paths=minimum_paths,
            )
            for name, values in outcomes.items()
        },
    )


def _reduction_factor(baseline: float, adjusted: float) -> float | None:
    if adjusted == 0:
        return None
    return baseline / adjusted


def control_variate_estimate(
    payoffs: Sequence[float],
    controls: Sequence[float],
    *,
    expected_control: float,
) -> VarianceReductionReport:
    if len(payoffs) != len(controls) or len(payoffs) < 3:
        raise ValueError("control variates require at least three aligned observations")
    if any(not math.isfinite(value) for value in (*payoffs, *controls, expected_control)):
        raise ValueError("control-variate inputs must be finite")
    control_variance = variance(controls)
    if control_variance == 0:
        raise ValueError("control variate must have non-zero sample variance")
    payoff_mean = fmean(payoffs)
    control_mean = fmean(controls)
    covariance = sum(
        (payoff - payoff_mean) * (control - control_mean)
        for payoff, control in zip(payoffs, controls, strict=True)
    ) / (len(payoffs) - 1)
    coefficient = covariance / control_variance
    adjusted = [
        payoff - coefficient * (control - expected_control)
        for payoff, control in zip(payoffs, controls, strict=True)
    ]
    baseline_variance = variance(payoffs)
    adjusted_variance = variance(adjusted)
    count = len(payoffs)
    return VarianceReductionReport(
        method="control_variate",
        observations=count,
        independent_replications=count,
        baseline_mean=payoff_mean,
        adjusted_mean=fmean(adjusted),
        baseline_replication_variance=baseline_variance,
        adjusted_replication_variance=adjusted_variance,
        baseline_standard_error=math.sqrt(baseline_variance / count),
        adjusted_standard_error=math.sqrt(adjusted_variance / count),
        variance_reduction_factor=_reduction_factor(baseline_variance, adjusted_variance),
        coefficient=coefficient,
    )


def antithetic_estimate(
    payoff_pairs: Sequence[tuple[float, float]],
) -> VarianceReductionReport:
    if len(payoff_pairs) < 2:
        raise ValueError("antithetic estimation requires at least two pairs")
    flattened = [value for pair in payoff_pairs for value in pair]
    if any(not math.isfinite(value) for value in flattened):
        raise ValueError("antithetic payoffs must be finite")
    pair_means = [(left + right) / 2 for left, right in payoff_pairs]
    pairs = len(payoff_pairs)
    baseline_pair_variance = variance(flattened) / 2
    adjusted_pair_variance = variance(pair_means)
    return VarianceReductionReport(
        method="antithetic",
        observations=2 * pairs,
        independent_replications=pairs,
        baseline_mean=fmean(flattened),
        adjusted_mean=fmean(pair_means),
        baseline_replication_variance=baseline_pair_variance,
        adjusted_replication_variance=adjusted_pair_variance,
        baseline_standard_error=math.sqrt(baseline_pair_variance / pairs),
        adjusted_standard_error=math.sqrt(adjusted_pair_variance / pairs),
        variance_reduction_factor=_reduction_factor(baseline_pair_variance, adjusted_pair_variance),
    )


def circular_block_bootstrap(
    values: Sequence[float],
    statistic: Callable[[Sequence[float]], float] = fmean,
    *,
    block_size: int,
    confidence: float = 0.95,
    samples: int = 2_000,
    seed: int = 17,
) -> BlockBootstrapReport:
    if len(values) < 2:
        raise ValueError("block bootstrap requires at least two observations")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("block-bootstrap values must be finite")
    if not 1 <= block_size <= len(values):
        raise ValueError("block_size must be between one and the sample length")
    if samples < 100:
        raise ValueError("block bootstrap requires at least 100 samples")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be strictly between zero and one")
    rng = Random(seed)
    count = len(values)
    estimates: list[float] = []
    for _ in range(samples):
        resampled: list[float] = []
        while len(resampled) < count:
            start = rng.randrange(count)
            resampled.extend(values[(start + offset) % count] for offset in range(block_size))
        estimates.append(statistic(resampled[:count]))
    alpha = (1 - confidence) / 2
    return BlockBootstrapReport(
        estimate=statistic(values),
        lower=empirical_quantile(estimates, alpha),
        upper=empirical_quantile(estimates, 1 - alpha),
        confidence=confidence,
        samples=samples,
        block_size=block_size,
        observations=count,
        seed=seed,
    )


def compare_exit_discretizations(
    coarse: Sequence[PathExecutionResult],
    fine: Sequence[PathExecutionResult],
    *,
    materiality_tolerance: float,
) -> ExitDiscretizationReport:
    if len(coarse) != len(fine) or not coarse:
        raise ValueError("coarse and fine results must be non-empty and aligned")
    if materiality_tolerance < 0:
        raise ValueError("materiality_tolerance cannot be negative")
    pnl_differences = [
        fine_result.pnl - coarse_result.pnl
        for coarse_result, fine_result in zip(coarse, fine, strict=True)
    ]
    reason_mismatches = sum(
        left.exit_reason != right.exit_reason for left, right in zip(coarse, fine, strict=True)
    )
    day_mismatches = sum(
        left.exit_day != right.exit_day for left, right in zip(coarse, fine, strict=True)
    )
    maximum_difference = max(abs(value) for value in pnl_differences)
    return ExitDiscretizationReport(
        paths=len(coarse),
        reason_mismatches=reason_mismatches,
        day_mismatches=day_mismatches,
        mean_pnl_difference=fmean(pnl_differences),
        maximum_absolute_pnl_difference=maximum_difference,
        materiality_tolerance=materiality_tolerance,
        material_gap=(reason_mismatches > 0 or maximum_difference > materiality_tolerance),
    )
