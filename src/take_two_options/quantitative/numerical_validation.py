"""Small, model-agnostic numerical comparison and convergence harness."""

from __future__ import annotations

import math
from enum import StrEnum

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class NumericalStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data"


class NumericalComparison(StrictModel):
    reference_name: str = Field(min_length=1)
    candidate_name: str = Field(min_length=1)
    reference_value: float
    candidate_value: float
    absolute_error: float = Field(ge=0)
    relative_error: float = Field(ge=0)
    absolute_tolerance: float = Field(ge=0)
    relative_tolerance: float = Field(ge=0)
    status: NumericalStatus


def compare_values(
    *,
    reference_name: str,
    candidate_name: str,
    reference_value: float,
    candidate_value: float,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> NumericalComparison:
    """Compare finite scalars using a combined absolute/relative tolerance."""
    values = (reference_value, candidate_value, absolute_tolerance, relative_tolerance)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("comparison inputs and tolerances must be finite")
    if absolute_tolerance < 0 or relative_tolerance < 0:
        raise ValueError("tolerances cannot be negative")
    absolute_error = abs(candidate_value - reference_value)
    scale = max(abs(reference_value), abs(candidate_value), 1e-15)
    relative_error = absolute_error / scale
    passed = absolute_error <= absolute_tolerance + relative_tolerance * scale
    return NumericalComparison(
        reference_name=reference_name,
        candidate_name=candidate_name,
        reference_value=reference_value,
        candidate_value=candidate_value,
        absolute_error=absolute_error,
        relative_error=relative_error,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
        status=NumericalStatus.PASSED if passed else NumericalStatus.FAILED,
    )


class FiniteDifferencePoint(StrictModel):
    time_steps: int = Field(gt=0)
    price_steps: int = Field(gt=0)
    value: float


class ConvergenceReport(StrictModel):
    points: tuple[FiniteDifferencePoint, ...] = Field(min_length=2)
    successive_absolute_errors: tuple[float, ...]
    final_absolute_error: float = Field(ge=0)
    tolerance: float = Field(ge=0)
    monotone_refinement: bool
    status: NumericalStatus
    notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_lengths(self) -> ConvergenceReport:
        if len(self.successive_absolute_errors) != len(self.points) - 1:
            raise ValueError("one successive error is required per refinement")
        return self


def assess_fd_convergence(
    points: tuple[FiniteDifferencePoint, ...], *, tolerance: float
) -> ConvergenceReport:
    """Assess a finite-difference refinement sequence without claiming an order."""
    if tolerance < 0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be finite and non-negative")
    if len(points) < 2:
        raise ValueError("at least two refinement points are required")
    if not all(math.isfinite(point.value) for point in points):
        raise ValueError("finite-difference values must be finite")
    monotone_refinement = all(
        current.time_steps >= previous.time_steps
        and current.price_steps >= previous.price_steps
        and (current.time_steps > previous.time_steps or current.price_steps > previous.price_steps)
        for previous, current in zip(points[:-1], points[1:], strict=True)
    )
    errors = tuple(
        abs(current.value - previous.value)
        for previous, current in zip(points[:-1], points[1:], strict=True)
    )
    final_error = errors[-1]
    passed = monotone_refinement and final_error <= tolerance
    notes: tuple[str, ...] = ()
    if not monotone_refinement:
        notes = ("Grid sequence is not a strict refinement.",)
    return ConvergenceReport(
        points=points,
        successive_absolute_errors=errors,
        final_absolute_error=final_error,
        tolerance=tolerance,
        monotone_refinement=monotone_refinement,
        status=NumericalStatus.PASSED if passed else NumericalStatus.FAILED,
        notes=notes,
    )
