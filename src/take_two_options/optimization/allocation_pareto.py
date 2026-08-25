"""Versioned integer objectives and non-compensatory allocation frontiers."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.intelligence.schemas import AllocationResult


class AllocationObjectiveKind(StrEnum):
    WEIGHTED_MEAN_RISK = "weighted_mean_risk"
    WORST_CASE_MEAN_RISK = "worst_case_mean_risk"


class OptimizationObjectiveContract(StrictModel):
    objective_id: str = Field(min_length=1)
    version: Literal["1.0"] = "1.0"
    kind: AllocationObjectiveKind
    risk_aversion: float = Field(ge=0)
    cvar_aversion: float = Field(ge=0)
    execution_penalty: float = Field(ge=0)
    model_risk_penalty: float = Field(ge=0)
    regime_weight_semantics: Literal["configured_heuristic_sensitivity", "validated_oos"]
    weight_evidence_hash: str | None = Field(default=None, min_length=1)
    whole_contracts_required: Literal[True] = True
    cash_no_trade_required: Literal[True] = True

    @model_validator(mode="after")
    def validate_weight_evidence(self) -> OptimizationObjectiveContract:
        if self.regime_weight_semantics == "validated_oos" and self.weight_evidence_hash is None:
            raise ValueError("validated OOS weights require an evidence hash")
        return self


class AllocationParetoPoint(StrictModel):
    allocation_id: str = Field(min_length=1)
    counts: tuple[int, ...]
    expected_return_fraction: float
    worst_case_return_fraction: float
    volatility_fraction: float = Field(ge=0)
    cvar_fraction: float = Field(ge=0)
    cost_fraction: float = Field(ge=0)
    maximum_loss_fraction: float = Field(ge=0)
    execution_risk_fraction: float = Field(ge=0)
    model_dispersion_fraction: float = Field(ge=0)
    scalar_objective: float
    no_trade: bool

    @model_validator(mode="after")
    def validate_counts(self) -> AllocationParetoPoint:
        if any(not isinstance(count, int) or count < 0 for count in self.counts):
            raise ValueError("allocation counts must be non-negative whole integers")
        if self.no_trade != (not any(self.counts)):
            raise ValueError("no_trade must exactly identify the all-zero allocation")
        return self


class AllocationOptimizationReport(StrictModel):
    objective: OptimizationObjectiveContract
    oracle_method: Literal["exhaustive_integer_enumeration"] = "exhaustive_integer_enumeration"
    feasible_allocations: int = Field(gt=0)
    pareto_frontier: tuple[AllocationParetoPoint, ...] = Field(min_length=1)
    selected_allocations: list[AllocationResult]
    no_trade_allocation_id: str = Field(min_length=1)
    assumptions: tuple[str, ...]

    @model_validator(mode="after")
    def validate_no_trade(self) -> AllocationOptimizationReport:
        matching = [
            point
            for point in self.pareto_frontier
            if point.allocation_id == self.no_trade_allocation_id and point.no_trade
        ]
        if len(matching) != 1:
            raise ValueError("Pareto frontier must contain the declared NO_TRADE point")
        return self


def evaluate_scalar_objective(
    contract: OptimizationObjectiveContract,
    *,
    weighted_expected_usd: float,
    worst_case_expected_usd: float,
    variance_usd2: float,
    cvar_usd: float,
    execution_risk_usd: float,
    model_dispersion_usd: float,
    budget_usd: float,
) -> float:
    if budget_usd <= 0:
        raise ValueError("objective normalization budget must be positive")
    if any(
        not math.isfinite(value)
        for value in (
            weighted_expected_usd,
            worst_case_expected_usd,
            variance_usd2,
            cvar_usd,
            execution_risk_usd,
            model_dispersion_usd,
        )
    ):
        raise ValueError("objective inputs must be finite")
    expectation = (
        weighted_expected_usd
        if contract.kind is AllocationObjectiveKind.WEIGHTED_MEAN_RISK
        else worst_case_expected_usd
    )
    return (
        expectation / budget_usd
        - contract.risk_aversion * variance_usd2 / budget_usd**2
        - contract.cvar_aversion * cvar_usd / budget_usd
        - contract.execution_penalty * execution_risk_usd / budget_usd
        - contract.model_risk_penalty * model_dispersion_usd / budget_usd
    )


def dominates_allocation(
    left: AllocationParetoPoint,
    right: AllocationParetoPoint,
    *,
    tolerance: float = 1e-12,
) -> bool:
    """Return true when left is no worse in every criterion and better in one."""

    left_minimization = (
        left.volatility_fraction,
        left.cvar_fraction,
        left.cost_fraction,
        left.maximum_loss_fraction,
        left.execution_risk_fraction,
        left.model_dispersion_fraction,
    )
    right_minimization = (
        right.volatility_fraction,
        right.cvar_fraction,
        right.cost_fraction,
        right.maximum_loss_fraction,
        right.execution_risk_fraction,
        right.model_dispersion_fraction,
    )
    no_worse = (
        left.expected_return_fraction + tolerance >= right.expected_return_fraction
        and left.worst_case_return_fraction + tolerance >= right.worst_case_return_fraction
        and all(
            left_value <= right_value + tolerance
            for left_value, right_value in zip(left_minimization, right_minimization, strict=True)
        )
    )
    strictly_better = (
        left.expected_return_fraction > right.expected_return_fraction + tolerance
        or left.worst_case_return_fraction > right.worst_case_return_fraction + tolerance
        or any(
            left_value + tolerance < right_value
            for left_value, right_value in zip(left_minimization, right_minimization, strict=True)
        )
    )
    return no_worse and strictly_better


def allocation_pareto_frontier(
    points: list[AllocationParetoPoint],
) -> tuple[AllocationParetoPoint, ...]:
    if not points:
        raise ValueError("Pareto frontier requires allocation points")
    if len({point.allocation_id for point in points}) != len(points):
        raise ValueError("allocation IDs must be unique")
    if sum(point.no_trade for point in points) != 1:
        raise ValueError("feasible set must contain exactly one cash/NO_TRADE point")
    frontier = [
        point
        for point in points
        if not any(
            dominates_allocation(other, point)
            for other in points
            if other.allocation_id != point.allocation_id
        )
    ]
    return tuple(
        sorted(
            frontier,
            key=lambda point: (
                -point.expected_return_fraction,
                point.cvar_fraction,
                point.volatility_fraction,
                point.cost_fraction,
                point.allocation_id,
            ),
        )
    )
