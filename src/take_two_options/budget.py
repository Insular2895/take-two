"""Versioned budget policies and the single capital-eligibility evaluator."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Literal, TypeAlias

from pydantic import Field, computed_field, field_validator, model_validator

from take_two_options.models import StrictModel


class MinimumSpendPolicy(StrEnum):
    SOFT = "SOFT"
    HARD = "HARD"
    OFF = "OFF"


class CapitalCapMode(StrEnum):
    AUTO = "AUTO"
    EXPLICIT = "EXPLICIT"


class BudgetStatus(StrEnum):
    BELOW_PREFERRED_RANGE = "BELOW_PREFERRED_RANGE"
    WITHIN_PREFERRED_RANGE = "WITHIN_PREFERRED_RANGE"
    ABOVE_TARGET_WITHIN_TOLERANCE = "ABOVE_TARGET_WITHIN_TOLERANCE"
    AT_HARD_CEILING = "AT_HARD_CEILING"
    EXCEEDS_HARD_BUDGET_CEILING = "EXCEEDS_HARD_BUDGET_CEILING"
    MAXIMUM_LOSS_EXCEEDED = "MAXIMUM_LOSS_EXCEEDED"
    BUYING_POWER_EXCEEDED = "BUYING_POWER_EXCEEDED"
    CAPITAL_REQUIREMENT_UNKNOWN = "CAPITAL_REQUIREMENT_UNKNOWN"
    FX_REQUIRED = "FX_REQUIRED"
    BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN = "BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN"


class LifecycleCapitalStatus(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    BROKER_BUYING_POWER = "BROKER_BUYING_POWER"
    ESTIMATED_ANALYTICAL_BOUND = "ESTIMATED_ANALYTICAL_BOUND"
    UNKNOWN = "UNKNOWN"
    LEGACY_COMMON_EXPIRY_PROXY = "LEGACY_COMMON_EXPIRY_PROXY"


class CapitalRequirementStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    KNOWN_BROKER = "KNOWN_BROKER"
    ESTIMATED_ANALYTICAL_BOUND = "ESTIMATED_ANALYTICAL_BOUND"
    UNKNOWN = "UNKNOWN"


class BudgetGuaranteeStatus(StrEnum):
    PROVEN = "PROVEN"
    UNPROVEN = "UNPROVEN"


class FXExecutionCostStatus(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class FXAccountMode(StrEnum):
    CONVERT_AT_ENTRY_AND_EXIT = "CONVERT_AT_ENTRY_AND_EXIT"
    MAINTAIN_UNDERLYING_CURRENCY_CASH = "MAINTAIN_UNDERLYING_CURRENCY_CASH"
    ACCOUNT_BASE_TRANSLATION_ONLY = "ACCOUNT_BASE_TRANSLATION_ONLY"
    UNKNOWN = "UNKNOWN"


class MixedExpiryLifecycleConfiguration(StrictModel):
    policy: Literal["CLOSE_BEFORE_FIRST_EXPIRY"] = "CLOSE_BEFORE_FIRST_EXPIRY"
    close_buffer_calendar_days: int = Field(default=1, ge=0)
    source: str = Field(default="trade_economics_configuration", min_length=1)
    version: str = Field(default="1.1", min_length=1)

    def managed_exit_deadline(self, first_expiry: date | datetime) -> date | datetime:
        return first_expiry - timedelta(days=self.close_buffer_calendar_days)


class CapitalCap(StrictModel):
    mode: CapitalCapMode = CapitalCapMode.AUTO
    value: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_mode_and_value(self) -> CapitalCap:
        if self.mode is CapitalCapMode.AUTO and self.value is not None:
            raise ValueError("AUTO capital caps must have a null value")
        if self.mode is CapitalCapMode.EXPLICIT and self.value is None:
            raise ValueError("EXPLICIT capital caps require a positive value")
        return self


class BudgetPolicyV1Legacy(StrictModel):
    """Historical budget semantics retained for reproducibility only."""

    budget_policy_version: Literal["1.0"] = "1.0"
    currency: str = Field(min_length=3, max_length=3)
    budget: float = Field(gt=0)
    maximum_loss: float = Field(gt=0)
    safety_reserve_fraction: float = Field(default=0.05, ge=0, lt=1)
    maximum_contracts: int = Field(gt=0)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_legacy_limits(self) -> BudgetPolicyV1Legacy:
        if self.maximum_loss > self.budget:
            raise ValueError("legacy maximum loss cannot exceed budget")
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def deployable_budget(self) -> float:
        return self.budget * (1 - self.safety_reserve_fraction)


class FlexibleBudgetPolicyV2(StrictModel):
    """Explicit target budget with asymmetric lower and upper tolerances."""

    version: Literal["2.0"] = "2.0"
    currency: str = Field(min_length=3, max_length=3)
    target_budget: float = Field(gt=0)
    under_target_tolerance: float = Field(ge=0)
    max_overspend: float = Field(ge=0)
    minimum_spend_policy: MinimumSpendPolicy = MinimumSpendPolicy.SOFT
    maximum_loss_cap: CapitalCap = Field(default_factory=CapitalCap)
    buying_power_cap: CapitalCap = Field(default_factory=CapitalCap)
    maximum_contracts: int = Field(gt=0)
    account_available_capital: float | None = Field(default=None, ge=0)
    account_liquidity_reserve: float = Field(default=0.0, ge=0)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def require_account_capital_for_reserve(self) -> FlexibleBudgetPolicyV2:
        if self.account_liquidity_reserve > 0 and self.account_available_capital is None:
            raise ValueError(
                "account_available_capital is required when account_liquidity_reserve is positive"
            )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def budget_policy_version(self) -> Literal["2.0"]:
        return "2.0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def preferred_lower_bound(self) -> float:
        return max(0.0, self.target_budget - self.under_target_tolerance)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hard_authorized_ceiling(self) -> float:
        return self.target_budget + self.max_overspend

    @computed_field  # type: ignore[prop-decorator]
    @property
    def account_deployable_capital(self) -> float | None:
        if self.account_available_capital is None:
            return None
        return max(0.0, self.account_available_capital - self.account_liquidity_reserve)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def effective_hard_budget_ceiling(self) -> float:
        if self.account_deployable_capital is None:
            return self.hard_authorized_ceiling
        return min(self.hard_authorized_ceiling, self.account_deployable_capital)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def maximum_loss_cap_effective(self) -> float:
        if self.maximum_loss_cap.mode is CapitalCapMode.AUTO:
            return self.effective_hard_budget_ceiling
        assert self.maximum_loss_cap.value is not None
        return self.maximum_loss_cap.value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def buying_power_cap_effective(self) -> float:
        if self.buying_power_cap.mode is CapitalCapMode.AUTO:
            return self.effective_hard_budget_ceiling
        assert self.buying_power_cap.value is not None
        return self.buying_power_cap.value


# Public short name requested by the product contract.
FlexibleBudgetPolicy = FlexibleBudgetPolicyV2
BudgetPolicy: TypeAlias = BudgetPolicyV1Legacy | FlexibleBudgetPolicyV2


class FXRate(StrictModel):
    """Point-in-time conversion expressed as policy currency per source unit."""

    source_currency: str = Field(min_length=3, max_length=3)
    policy_currency: str = Field(min_length=3, max_length=3)
    rate_to_policy_currency: float = Field(gt=0)
    timestamp: datetime
    source: str = Field(min_length=1)

    @field_validator("source_currency", "policy_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("timestamp")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("point-in-time FX timestamps must be timezone-aware")
        return value


class FXExecutionCost(StrictModel):
    """Entry FX transaction cost, distinct from the economic conversion rate."""

    mode: FXAccountMode
    status: FXExecutionCostStatus
    cost_amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cost_basis_points: float | None = Field(default=None, ge=0)
    source: str | None = None
    timestamp: datetime | None = None
    validated_underlying_currency_cash: bool = False
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("timestamp")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("FX execution-cost timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_evidence(self) -> FXExecutionCost:
        valued = self.status in {
            FXExecutionCostStatus.KNOWN,
            FXExecutionCostStatus.ESTIMATED,
        }
        if valued:
            if self.mode is not FXAccountMode.CONVERT_AT_ENTRY_AND_EXIT:
                raise ValueError("valued FX costs require CONVERT_AT_ENTRY_AND_EXIT mode")
            if (self.cost_amount is None) == (self.cost_basis_points is None):
                raise ValueError("valued FX costs require exactly one fixed amount or bps input")
            if self.cost_amount is not None and self.currency is None:
                raise ValueError("fixed FX costs require a currency")
            if self.source is None or self.timestamp is None:
                raise ValueError("known or estimated FX costs require source and timestamp")
        elif self.status is FXExecutionCostStatus.NOT_APPLICABLE:
            if self.mode not in {
                FXAccountMode.MAINTAIN_UNDERLYING_CURRENCY_CASH,
                FXAccountMode.ACCOUNT_BASE_TRANSLATION_ONLY,
            }:
                raise ValueError("NOT_APPLICABLE requires an explicit no-conversion account mode")
            if self.cost_amount != 0 or self.cost_basis_points is not None:
                raise ValueError("NOT_APPLICABLE must carry an explicit zero fixed cost")
            if self.source is None or self.timestamp is None:
                raise ValueError("NOT_APPLICABLE requires source and timestamp evidence")
            if (
                self.mode is FXAccountMode.MAINTAIN_UNDERLYING_CURRENCY_CASH
                and not self.validated_underlying_currency_cash
            ):
                raise ValueError("maintained underlying-currency cash must be explicitly validated")
        elif self.cost_amount is not None or self.cost_basis_points is not None:
            raise ValueError("UNKNOWN FX cost must remain null")
        return self


class BrokerCapitalContext(StrictModel):
    buying_power_requirement: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source: str | None = None
    timestamp: datetime | None = None
    validated: bool = False

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("timestamp")
    @classmethod
    def require_timezone_aware_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("broker capital timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def require_evidence_for_validated_requirement(self) -> BrokerCapitalContext:
        if self.validated and self.buying_power_requirement is not None:
            if self.currency is None or self.source is None or self.timestamp is None:
                raise ValueError(
                    "validated broker buying power requires currency, source, and timestamp"
                )
        return self


class BudgetCandidate(StrictModel):
    candidate_id: str = Field(min_length=1)
    architecture: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    required_entry_cash: float
    maximum_loss: float | None = Field(default=None, ge=0)
    buying_power_requirement: float | None = Field(default=None, ge=0)
    buying_power_required: bool = False
    buying_power_status: CapitalRequirementStatus = CapitalRequirementStatus.NOT_REQUIRED
    quantity: int = Field(default=1, ge=0)
    as_of: datetime | None = None
    mixed_expiry: bool = False
    first_expiry: date | datetime | None = None
    managed_exit_deadline: date | datetime | None = None
    mixed_expiry_lifecycle: MixedExpiryLifecycleConfiguration | None = None
    analytical_loss_bound: float | None = Field(default=None, ge=0)
    analytical_bound_validated: bool = False
    legacy_common_expiry_maximum_loss: float | None = Field(default=None, ge=0)
    is_no_position: bool = False

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("as_of")
    @classmethod
    def require_timezone_aware_cutoff(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("candidate cutoffs must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_capital_inputs(self) -> BudgetCandidate:
        if self.buying_power_requirement is not None and not self.buying_power_required:
            raise ValueError("buying-power values require buying_power_required=true")
        if self.buying_power_required and self.buying_power_requirement == 0:
            raise ValueError("unknown buying power must be null, never zero")
        if not self.buying_power_required and self.buying_power_status is not (
            CapitalRequirementStatus.NOT_REQUIRED
        ):
            raise ValueError("non-required buying power must use NOT_REQUIRED status")
        if self.buying_power_required and self.buying_power_requirement is None and (
            self.buying_power_status is not CapitalRequirementStatus.UNKNOWN
        ):
            raise ValueError("missing required buying power must use UNKNOWN status")
        if (
            self.buying_power_requirement is not None
            and self.buying_power_status
            is not CapitalRequirementStatus.ESTIMATED_ANALYTICAL_BOUND
        ):
            raise ValueError(
                "candidate buying power requires an analytical status; "
                "broker values must use BrokerCapitalContext"
            )
        if self.analytical_bound_validated and self.analytical_loss_bound is None:
            raise ValueError("validated analytical bounds require a value")
        if self.mixed_expiry:
            if (
                self.first_expiry is None
                or self.managed_exit_deadline is None
                or self.mixed_expiry_lifecycle is None
            ):
                raise ValueError(
                    "mixed-expiry candidates require first expiry, deadline, and lifecycle config"
                )
            expected = self.mixed_expiry_lifecycle.managed_exit_deadline(self.first_expiry)
            if self.managed_exit_deadline != expected:
                raise ValueError("MIXED_EXPIRY_LIFECYCLE_CONFIG_MISMATCH")
        if self.is_no_position and self.quantity != 0:
            raise ValueError("no-position candidates must have quantity zero")
        return self


class LifecycleCapitalRequirement(StrictModel):
    policy: Literal["CLOSE_BEFORE_FIRST_EXPIRY"]
    managed_exit_deadline: date | datetime
    entry_cash_required: float = Field(ge=0)
    analytical_loss_bound: float | None = Field(default=None, ge=0)
    broker_buying_power: float | None = Field(default=None, ge=0)
    effective_budget_requirement: float | None = Field(default=None, ge=0)
    calculation_status: LifecycleCapitalStatus
    mixed_expiry_close_buffer_calendar_days: int | None = Field(default=None, ge=0)
    lifecycle_config_source: str | None = None
    lifecycle_config_version: str | None = None
    warnings: list[str] = Field(default_factory=list)


class BudgetDiagnostics(StrictModel):
    currency: str = Field(min_length=3, max_length=3)
    target_budget: float = Field(gt=0)
    preferred_lower_bound: float = Field(ge=0)
    hard_authorized_ceiling: float = Field(gt=0)
    maximum_loss_cap_effective: float = Field(ge=0)
    buying_power_cap_effective: float = Field(ge=0)
    account_available_capital: float | None = Field(default=None, ge=0)
    account_liquidity_reserve: float = Field(default=0.0, ge=0)
    account_deployable_capital: float | None = Field(default=None, ge=0)
    configured_hard_authorized_ceiling: float | None = Field(default=None, gt=0)
    effective_hard_budget_ceiling: float | None = Field(default=None, ge=0)
    account_headroom_after_trade: float | None = None
    native_currency: str | None = Field(default=None, min_length=3, max_length=3)
    native_entry_cash: float | None = None
    converted_entry_cash_before_fx_cost: float | None = Field(default=None, ge=0)
    entry_fx_cost: float | None = Field(default=None, ge=0)
    entry_fx_cost_status: FXExecutionCostStatus | None = None
    required_entry_cash_after_fx: float | None = Field(default=None, ge=0)
    required_entry_cash: float | None = Field(default=None, ge=0)
    maximum_loss: float | None = Field(default=None, ge=0)
    buying_power_requirement: float | None = Field(default=None, ge=0)
    buying_power_status: CapitalRequirementStatus
    effective_capital_requirement: float | None = Field(default=None, ge=0)
    budget_delta_to_target: float | None = None
    budget_delta_percentage: float | None = None
    headroom_to_hard_ceiling: float | None = None
    capital_utilization_of_target: float | None = Field(default=None, ge=0)
    capital_utilization_of_hard_ceiling: float | None = Field(default=None, ge=0)
    budget_status: BudgetStatus
    minimum_spend_policy: MinimumSpendPolicy
    budget_policy_version: Literal["1.0", "2.0"]
    eligible: bool
    research_eligible: bool
    paper_eligible: bool
    budget_guarantee_status: BudgetGuaranteeStatus
    reason_codes: list[str] = Field(default_factory=list)
    fx_rate_to_policy_currency: float | None = Field(default=None, gt=0)
    fx_rate: float | None = Field(default=None, gt=0)
    fx_source: str | None = None
    fx_rate_source: str | None = None
    fx_cost_source: str | None = None
    fx_timestamp: datetime | None = None
    warnings: list[str] = Field(default_factory=list)


class BudgetEvaluation(StrictModel):
    diagnostics: BudgetDiagnostics
    lifecycle_capital_requirement: LifecycleCapitalRequirement | None = None


def _policy_values(
    policy: BudgetPolicy,
) -> tuple[float, float, float, float, MinimumSpendPolicy, Literal["1.0", "2.0"]]:
    if isinstance(policy, FlexibleBudgetPolicyV2):
        return (
            policy.preferred_lower_bound,
            policy.target_budget,
            policy.effective_hard_budget_ceiling,
            policy.maximum_loss_cap_effective,
            policy.minimum_spend_policy,
            "2.0",
        )
    return (
        0.0,
        policy.budget,
        policy.deployable_budget,
        policy.maximum_loss,
        MinimumSpendPolicy.OFF,
        "1.0",
    )


def _buying_power_cap(policy: BudgetPolicy) -> float:
    if isinstance(policy, FlexibleBudgetPolicyV2):
        return policy.buying_power_cap_effective
    return policy.deployable_budget


def _machine_tolerance(left: float, right: float) -> float:
    """Permit representation noise only, never an economic allowance."""
    return max(math.ulp(left), math.ulp(right), math.ulp(1.0)) * 4


def _convert_amount(
    value: float | None,
    *,
    source_currency: str,
    policy_currency: str,
    fx: FXRate | None,
) -> float | None:
    if value is None:
        return None
    if source_currency == policy_currency:
        return value
    if fx is None or fx.source_currency != source_currency or fx.policy_currency != policy_currency:
        return None
    return value * fx.rate_to_policy_currency


def _resolve_fx_execution_cost(
    *,
    candidate: BudgetCandidate,
    policy_currency: str,
    converted_native_entry_cash: float,
    fx_required: bool,
    fx_cost: FXExecutionCost | None,
) -> tuple[float | None, FXExecutionCostStatus, str | None, list[str]]:
    warnings: list[str] = []
    if not fx_required or candidate.is_no_position:
        if fx_cost is not None and fx_cost.status is not FXExecutionCostStatus.NOT_APPLICABLE:
            warnings.append(
                "FX execution-cost input was ignored because no entry conversion applies."
            )
        return 0.0, FXExecutionCostStatus.NOT_APPLICABLE, "no_entry_conversion", warnings
    if fx_cost is None or fx_cost.status is FXExecutionCostStatus.UNKNOWN:
        return None, FXExecutionCostStatus.UNKNOWN, fx_cost.source if fx_cost else None, warnings
    if (
        candidate.as_of is None
        or fx_cost.timestamp is None
        or fx_cost.timestamp > candidate.as_of
    ):
        warnings.append("FX execution-cost evidence is not point-in-time valid at the cutoff.")
        return None, FXExecutionCostStatus.UNKNOWN, fx_cost.source, warnings
    if fx_cost.status is FXExecutionCostStatus.NOT_APPLICABLE:
        return 0.0, fx_cost.status, fx_cost.source, warnings
    if fx_cost.cost_amount is not None:
        if fx_cost.currency != policy_currency:
            warnings.append("Fixed FX execution cost must be expressed in policy currency.")
            return None, FXExecutionCostStatus.UNKNOWN, fx_cost.source, warnings
        return fx_cost.cost_amount, fx_cost.status, fx_cost.source, warnings
    assert fx_cost.cost_basis_points is not None
    cost = abs(converted_native_entry_cash) * fx_cost.cost_basis_points / 10_000.0
    return cost, fx_cost.status, fx_cost.source, warnings


def evaluate_budget_policy(
    candidate: BudgetCandidate,
    policy: BudgetPolicy,
    fx: FXRate | None,
    broker_context: BrokerCapitalContext | None,
    fx_cost: FXExecutionCost | None = None,
) -> BudgetEvaluation:
    """Evaluate entry cash, loss, and buying power as parallel capital gates."""
    lower, target, hard, maximum_loss_cap, minimum_policy, version = _policy_values(policy)
    buying_power_cap = _buying_power_cap(policy)
    warnings: list[str] = []
    reason_codes: list[str] = []
    policy_currency = policy.currency
    configured_hard = (
        policy.hard_authorized_ceiling
        if isinstance(policy, FlexibleBudgetPolicyV2)
        else policy.deployable_budget
    )
    account_available = (
        policy.account_available_capital
        if isinstance(policy, FlexibleBudgetPolicyV2)
        else None
    )
    account_reserve = (
        policy.account_liquidity_reserve
        if isinstance(policy, FlexibleBudgetPolicyV2)
        else 0.0
    )
    account_deployable = (
        policy.account_deployable_capital
        if isinstance(policy, FlexibleBudgetPolicyV2)
        else None
    )
    fx_required = candidate.currency != policy_currency
    fx_valid = not fx_required or (
        fx is not None
        and candidate.as_of is not None
        and fx.source_currency == candidate.currency
        and fx.policy_currency == policy_currency
        and fx.timestamp <= candidate.as_of
    )
    if fx_required and candidate.as_of is None:
        warnings.append("Candidate cutoff is required for point-in-time FX validation.")
    if fx_required and fx is not None and candidate.as_of is not None and fx.timestamp > (
        candidate.as_of
    ):
        warnings.append("FX timestamp is after the candidate cutoff and was rejected.")

    broker_buying_power = None
    broker_currency = candidate.currency
    buying_power_status = candidate.buying_power_status
    if broker_context is not None and broker_context.buying_power_requirement is not None:
        broker_is_point_in_time = (
            candidate.as_of is not None
            and broker_context.timestamp is not None
            and broker_context.timestamp <= candidate.as_of
        )
        if broker_context.validated and broker_is_point_in_time:
            broker_buying_power = broker_context.buying_power_requirement
            broker_currency = broker_context.currency or candidate.currency
            buying_power_status = CapitalRequirementStatus.KNOWN_BROKER
        elif broker_context.validated:
            warnings.append(
                "Broker buying-power evidence lacks a valid timestamp at or before the "
                "candidate cutoff."
            )
        else:
            warnings.append("Unvalidated broker buying-power input was ignored.")

    if broker_buying_power is not None and broker_currency != candidate.currency:
        fx_valid = fx_valid and broker_currency == policy_currency
        if broker_currency != policy_currency:
            warnings.append("Broker buying-power currency requires a separate FX conversion.")
            broker_buying_power = None

    if not fx_valid:
        diagnostics = BudgetDiagnostics(
            currency=policy_currency,
            target_budget=target,
            preferred_lower_bound=lower,
            hard_authorized_ceiling=configured_hard,
            maximum_loss_cap_effective=maximum_loss_cap,
            buying_power_cap_effective=buying_power_cap,
            account_available_capital=account_available,
            account_liquidity_reserve=account_reserve,
            account_deployable_capital=account_deployable,
            configured_hard_authorized_ceiling=configured_hard,
            effective_hard_budget_ceiling=hard,
            native_entry_cash=candidate.required_entry_cash,
            native_currency=candidate.currency,
            entry_fx_cost_status=FXExecutionCostStatus.UNKNOWN,
            buying_power_status=buying_power_status,
            budget_status=BudgetStatus.FX_REQUIRED,
            minimum_spend_policy=minimum_policy,
            budget_policy_version=version,
            eligible=False,
            research_eligible=True,
            paper_eligible=False,
            budget_guarantee_status=BudgetGuaranteeStatus.UNPROVEN,
            reason_codes=[BudgetStatus.FX_REQUIRED.value],
            warnings=[
                *warnings,
                "Point-in-time FX is required before capital can be compared with the policy.",
            ],
        )
        return BudgetEvaluation(diagnostics=diagnostics)

    converted_native_entry_cash = _convert_amount(
        candidate.required_entry_cash,
        source_currency=candidate.currency,
        policy_currency=policy_currency,
        fx=fx,
    )
    assert converted_native_entry_cash is not None
    converted_entry_cash = max(converted_native_entry_cash, 0.0)
    entry_fx_cost, entry_fx_cost_status, fx_cost_source, fx_cost_warnings = (
        _resolve_fx_execution_cost(
            candidate=candidate,
            policy_currency=policy_currency,
            converted_native_entry_cash=converted_native_entry_cash,
            fx_required=fx_required,
            fx_cost=fx_cost,
        )
    )
    warnings.extend(fx_cost_warnings)
    entry_cash = (
        converted_entry_cash + entry_fx_cost
        if entry_fx_cost is not None
        else converted_entry_cash
    )
    maximum_loss = _convert_amount(
        candidate.maximum_loss,
        source_currency=candidate.currency,
        policy_currency=policy_currency,
        fx=fx,
    )
    analytical_bound = _convert_amount(
        candidate.analytical_loss_bound,
        source_currency=candidate.currency,
        policy_currency=policy_currency,
        fx=fx,
    )
    candidate_buying_power = _convert_amount(
        candidate.buying_power_requirement,
        source_currency=candidate.currency,
        policy_currency=policy_currency,
        fx=fx,
    )
    buying_power = (
        broker_buying_power
        if broker_buying_power is not None and broker_currency == policy_currency
        else _convert_amount(
            broker_buying_power,
            source_currency=candidate.currency,
            policy_currency=policy_currency,
            fx=fx,
        )
        if broker_buying_power is not None
        else candidate_buying_power
    )

    lifecycle: LifecycleCapitalRequirement | None = None
    mixed_unproven = False
    if candidate.mixed_expiry:
        if candidate.managed_exit_deadline is None or candidate.mixed_expiry_lifecycle is None:
            raise ValueError("mixed-expiry candidates require a managed deadline and config")
        lifecycle_status = LifecycleCapitalStatus.UNKNOWN
        selected_requirement: float | None = None
        lifecycle_warnings = [
            "Common-expiry terminal payoff is not a valid BudgetPolicyV2 maximum-loss bound."
        ]
        if broker_buying_power is not None and buying_power is not None:
            lifecycle_status = LifecycleCapitalStatus.BROKER_BUYING_POWER
            selected_requirement = buying_power
            buying_power_status = CapitalRequirementStatus.KNOWN_BROKER
        elif candidate.analytical_bound_validated and analytical_bound is not None:
            lifecycle_status = LifecycleCapitalStatus.ESTIMATED_ANALYTICAL_BOUND
            selected_requirement = analytical_bound
            buying_power_status = CapitalRequirementStatus.ESTIMATED_ANALYTICAL_BOUND
        else:
            mixed_unproven = True
            lifecycle_warnings.append(
                "No validated analytical bound or broker buying-power requirement is available."
            )
            if candidate.legacy_common_expiry_maximum_loss is not None:
                lifecycle_warnings.append(
                    "LEGACY_COMMON_EXPIRY_PROXY is retained for V1 reproduction only and was "
                    "excluded from this V2 decision."
                )
        lifecycle_effective = (
            max(entry_cash or 0.0, selected_requirement)
            if selected_requirement is not None
            else None
        )
        lifecycle = LifecycleCapitalRequirement(
            policy="CLOSE_BEFORE_FIRST_EXPIRY",
            managed_exit_deadline=candidate.managed_exit_deadline,
            entry_cash_required=entry_cash or 0.0,
            analytical_loss_bound=analytical_bound,
            broker_buying_power=buying_power if broker_buying_power is not None else None,
            effective_budget_requirement=lifecycle_effective,
            calculation_status=lifecycle_status,
            mixed_expiry_close_buffer_calendar_days=(
                candidate.mixed_expiry_lifecycle.close_buffer_calendar_days
            ),
            lifecycle_config_source=candidate.mixed_expiry_lifecycle.source,
            lifecycle_config_version=candidate.mixed_expiry_lifecycle.version,
            warnings=lifecycle_warnings,
        )
        maximum_loss = None
        if selected_requirement is not None:
            buying_power = selected_requirement

    known_requirements = [entry_cash or 0.0]
    if maximum_loss is not None:
        known_requirements.append(maximum_loss)
    if buying_power is not None:
        known_requirements.append(buying_power)
    if lifecycle is not None and lifecycle.effective_budget_requirement is not None:
        known_requirements.append(lifecycle.effective_budget_requirement)
    effective = max(known_requirements) if known_requirements else None

    status: BudgetStatus
    eligible = True
    research_eligible = True
    paper_eligible = True
    uncertainty_reasons: list[str] = []
    if candidate.mixed_expiry and mixed_unproven:
        uncertainty_reasons.append(BudgetStatus.BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN.value)
    elif (
        maximum_loss is None and not candidate.is_no_position and not candidate.mixed_expiry
    ) or (candidate.buying_power_required and buying_power is None):
        uncertainty_reasons.append(BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN.value)
    if (
        entry_fx_cost_status is FXExecutionCostStatus.UNKNOWN
        and fx_required
        and not candidate.is_no_position
    ):
        uncertainty_reasons.append("FX_EXECUTION_COST_UNKNOWN")
    guarantee = (
        BudgetGuaranteeStatus.UNPROVEN
        if uncertainty_reasons
        else BudgetGuaranteeStatus.PROVEN
    )
    hard_tolerance = _machine_tolerance(effective or 0.0, hard)

    if entry_cash is not None and entry_cash > hard + _machine_tolerance(entry_cash, hard):
        status = BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING
        eligible = False
        paper_eligible = False
        reason_codes.append(status.value)
    elif maximum_loss is not None and maximum_loss > maximum_loss_cap + _machine_tolerance(
        maximum_loss, maximum_loss_cap
    ):
        status = BudgetStatus.MAXIMUM_LOSS_EXCEEDED
        eligible = False
        paper_eligible = False
        reason_codes.append(status.value)
    elif buying_power is not None and buying_power > buying_power_cap + _machine_tolerance(
        buying_power, buying_power_cap
    ):
        status = BudgetStatus.BUYING_POWER_EXCEEDED
        eligible = False
        paper_eligible = False
        reason_codes.append(status.value)
    elif effective is not None and effective > hard + hard_tolerance:
        status = BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING
        eligible = False
        paper_eligible = False
        reason_codes.append(status.value)
    elif candidate.mixed_expiry and mixed_unproven:
        status = BudgetStatus.BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN
        eligible = False
        paper_eligible = False
        guarantee = BudgetGuaranteeStatus.UNPROVEN
        reason_codes.append(status.value)
    elif maximum_loss is None and not candidate.is_no_position and not candidate.mixed_expiry:
        status = BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN
        eligible = False
        paper_eligible = False
        guarantee = BudgetGuaranteeStatus.UNPROVEN
        reason_codes.append(status.value)
    elif candidate.buying_power_required and buying_power is None:
        status = BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN
        eligible = False
        paper_eligible = False
        guarantee = BudgetGuaranteeStatus.UNPROVEN
        reason_codes.append(status.value)
    elif effective is None:
        status = BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN
        eligible = False
        paper_eligible = False
        guarantee = BudgetGuaranteeStatus.UNPROVEN
        reason_codes.append(status.value)
    elif abs(effective - hard) <= hard_tolerance:
        status = BudgetStatus.AT_HARD_CEILING
    elif effective > target + _machine_tolerance(effective, target):
        status = BudgetStatus.ABOVE_TARGET_WITHIN_TOLERANCE
    elif minimum_policy is not MinimumSpendPolicy.OFF and effective < lower - _machine_tolerance(
        effective, lower
    ):
        status = BudgetStatus.BELOW_PREFERRED_RANGE
        if minimum_policy is MinimumSpendPolicy.HARD and not candidate.is_no_position:
            eligible = False
            paper_eligible = False
            reason_codes.append("BELOW_HARD_MINIMUM_SPEND")
        elif minimum_policy is MinimumSpendPolicy.SOFT:
            warnings.append("Lower bound is SOFT; the candidate remains budget-eligible.")
        elif candidate.is_no_position:
            warnings.append("No-position remains eligible regardless of minimum-spend policy.")
    else:
        status = BudgetStatus.WITHIN_PREFERRED_RANGE

    for uncertainty_reason in uncertainty_reasons:
        if uncertainty_reason not in reason_codes:
            reason_codes.append(uncertainty_reason)
    if "FX_EXECUTION_COST_UNKNOWN" in uncertainty_reasons:
        paper_eligible = False

    account_constrains_policy = (
        account_deployable is not None
        and account_deployable < configured_hard - _machine_tolerance(
            account_deployable, configured_hard
        )
    )
    if (
        account_constrains_policy
        and effective is not None
        and effective > hard + _machine_tolerance(effective, hard)
        and "ACCOUNT_DEPLOYABLE_CAPITAL_EXCEEDED" not in reason_codes
    ):
        reason_codes.append("ACCOUNT_DEPLOYABLE_CAPITAL_EXCEEDED")

    if version == "1.0":
        warnings.append(
            "LEGACY_POLICY uses budget, maximum_loss, and safety_reserve_fraction semantics."
        )
    if isinstance(policy, FlexibleBudgetPolicyV2) and policy.account_liquidity_reserve:
        warnings.append(
            "Account liquidity reserve is explicitly subtracted from known account capital; "
            "the lower account or configured ceiling controls deployment."
        )

    delta = effective - target if effective is not None else None
    diagnostics = BudgetDiagnostics(
        currency=policy_currency,
        target_budget=target,
        preferred_lower_bound=lower,
        hard_authorized_ceiling=configured_hard,
        maximum_loss_cap_effective=maximum_loss_cap,
        buying_power_cap_effective=buying_power_cap,
        account_available_capital=account_available,
        account_liquidity_reserve=account_reserve,
        account_deployable_capital=account_deployable,
        configured_hard_authorized_ceiling=configured_hard,
        effective_hard_budget_ceiling=hard,
        account_headroom_after_trade=(
            account_deployable - effective
            if account_deployable is not None and effective is not None
            else None
        ),
        native_entry_cash=candidate.required_entry_cash,
        native_currency=candidate.currency,
        converted_entry_cash_before_fx_cost=converted_entry_cash,
        entry_fx_cost=entry_fx_cost,
        entry_fx_cost_status=entry_fx_cost_status,
        required_entry_cash_after_fx=entry_cash,
        required_entry_cash=entry_cash,
        maximum_loss=maximum_loss,
        buying_power_requirement=buying_power,
        buying_power_status=buying_power_status,
        effective_capital_requirement=effective,
        budget_delta_to_target=delta,
        budget_delta_percentage=(delta / target if delta is not None else None),
        headroom_to_hard_ceiling=(hard - effective if effective is not None else None),
        capital_utilization_of_target=(effective / target if effective is not None else None),
        capital_utilization_of_hard_ceiling=(
            effective / hard if effective is not None and hard > 0 else None
        ),
        budget_status=status,
        minimum_spend_policy=minimum_policy,
        budget_policy_version=version,
        eligible=eligible,
        research_eligible=research_eligible,
        paper_eligible=paper_eligible,
        budget_guarantee_status=guarantee,
        reason_codes=reason_codes,
        fx_rate_to_policy_currency=(fx.rate_to_policy_currency if fx_required and fx else None),
        fx_rate=(fx.rate_to_policy_currency if fx_required and fx else None),
        fx_source=(fx.source if fx_required and fx else None),
        fx_rate_source=(fx.source if fx_required and fx else None),
        fx_cost_source=fx_cost_source,
        fx_timestamp=(fx.timestamp if fx_required and fx else None),
        warnings=warnings,
    )
    return BudgetEvaluation(
        diagnostics=diagnostics,
        lifecycle_capital_requirement=lifecycle,
    )
