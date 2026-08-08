"""Model/parameter ensemble contracts without heuristic-to-statistical promotion."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class EnsembleWeightBasis(StrEnum):
    EQUAL_SENSITIVITY = "equal_sensitivity"
    USER_ASSUMPTION = "user_assumption"
    VALIDATED_OOS = "validated_oos"


class EnsembleMemberEstimate(StrictModel):
    member_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    parameter_set_id: str = Field(min_length=1)
    weight: float = Field(gt=0, le=1)
    expected_value: float
    outcome_variance: float = Field(ge=0)
    mean_standard_error: float = Field(ge=0)
    probability_profit: float = Field(ge=0, le=1)
    observations: int = Field(gt=1)
    calibration_status: str = Field(min_length=1)


class ModelUncertaintyReport(StrictModel):
    members: tuple[EnsembleMemberEstimate, ...] = Field(min_length=1)
    weight_basis: EnsembleWeightBasis
    validation_dataset_hash: str | None = Field(default=None, min_length=1)
    claim_status: Literal["diagnostic_only", "oos_evidence_declared"]
    weighted_expected_value: float
    weighted_probability_profit: float = Field(ge=0, le=1)
    within_model_predictive_variance: float = Field(ge=0)
    between_model_predictive_variance: float = Field(ge=0)
    total_predictive_variance: float = Field(ge=0)
    monte_carlo_standard_error: float = Field(ge=0)
    expected_value_range: tuple[float, float]
    probability_profit_range: tuple[float, float]
    blockers: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_decomposition(self) -> ModelUncertaintyReport:
        if abs(sum(member.weight for member in self.members) - 1.0) > 1e-8:
            raise ValueError("ensemble member weights must sum to one")
        if not math.isclose(
            self.total_predictive_variance,
            self.within_model_predictive_variance + self.between_model_predictive_variance,
            rel_tol=1e-10,
            abs_tol=1e-10,
        ):
            raise ValueError("total variance must equal within plus between variance")
        return self


def summarize_model_ensemble(
    members: list[EnsembleMemberEstimate],
    *,
    weight_basis: EnsembleWeightBasis,
    validation_dataset_hash: str | None = None,
) -> ModelUncertaintyReport:
    if not members:
        raise ValueError("model uncertainty requires at least one ensemble member")
    if abs(sum(member.weight for member in members) - 1.0) > 1e-8:
        raise ValueError("ensemble member weights must sum to one")
    if len({member.member_id for member in members}) != len(members):
        raise ValueError("ensemble member IDs must be unique")

    expected_value = sum(member.weight * member.expected_value for member in members)
    probability_profit = sum(member.weight * member.probability_profit for member in members)
    within_variance = sum(member.weight * member.outcome_variance for member in members)
    between_variance = sum(
        member.weight * (member.expected_value - expected_value) ** 2 for member in members
    )
    monte_carlo_standard_error = math.sqrt(
        sum(member.weight**2 * member.mean_standard_error**2 for member in members)
    )
    blockers: list[str] = []
    if weight_basis is not EnsembleWeightBasis.VALIDATED_OOS:
        blockers.append("ensemble_weights_are_not_validated_oos")
    if validation_dataset_hash is None:
        blockers.append("validation_dataset_hash_missing")
    if any(member.calibration_status != "calibrated" for member in members):
        blockers.append("one_or_more_members_are_not_calibrated")
    claim_status = "oos_evidence_declared" if not blockers else "diagnostic_only"
    expected_values = [member.expected_value for member in members]
    probabilities = [member.probability_profit for member in members]
    return ModelUncertaintyReport(
        members=tuple(members),
        weight_basis=weight_basis,
        validation_dataset_hash=validation_dataset_hash,
        claim_status=claim_status,
        weighted_expected_value=expected_value,
        weighted_probability_profit=probability_profit,
        within_model_predictive_variance=within_variance,
        between_model_predictive_variance=between_variance,
        total_predictive_variance=within_variance + between_variance,
        monte_carlo_standard_error=monte_carlo_standard_error,
        expected_value_range=(min(expected_values), max(expected_values)),
        probability_profit_range=(min(probabilities), max(probabilities)),
        blockers=tuple(blockers),
        assumptions=(
            "Members form a predictive mixture; weights are not posterior model "
            "probabilities unless independently validated.",
            "Monte Carlo standard error assumes independent member simulations.",
            "Between-model variance is not reduced by increasing paths within a fixed member.",
        ),
    )
