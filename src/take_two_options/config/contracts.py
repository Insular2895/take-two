"""Single configuration contract for pre-OPRA research runs.

The contract deliberately has no financial recommendation defaults. Every
research assumption must be supplied with provenance and a review status.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.schemas import Architecture, SourceReference

AssumptionStatus = Literal[
    "sourced",
    "calibrated",
    "calibration_required",
    "draft_to_validate",
]
AssumptionOrigin = Literal[
    "official_source",
    "authorized_market_data",
    "derived",
    "estimate",
    "user_assumption",
]


class GovernedValue(StrictModel):
    """A value that cannot be mistaken for a universal default."""

    value: float | int | str | bool | list[float] | list[int] | list[str]
    origin: AssumptionOrigin
    status: AssumptionStatus
    source_ids: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_source_for_validated_status(self) -> GovernedValue:
        if self.status == "sourced" and not self.source_ids:
            raise ValueError("sourced governed values require source_ids")
        return self


class ResearchRequestConfig(StrictModel):
    request_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    as_of: date
    directional_thesis: Literal["bullish", "bearish", "neutral", "volatile"]
    thesis_summary: str = Field(min_length=1)
    invalidation_conditions: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)


class MarketContextConfig(StrictModel):
    decision_cutoff: datetime
    base_currency: str = Field(min_length=3, max_length=3)
    historical_dataset_id: str | None
    data_providers: list[str] = Field(min_length=1)
    maximum_data_age_days: GovernedValue
    allow_cache_fallback: bool
    sources: list[SourceReference] = Field(default_factory=list)


class CapitalConstraintsConfig(StrictModel):
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    maximum_loss: float = Field(gt=0)
    maximum_contracts: int = Field(gt=0)
    safety_reserve_fraction: GovernedValue
    fx_rate_to_usd: float | None = Field(default=None, gt=0)
    fx_rate_as_of: date | None = None

    @model_validator(mode="after")
    def validate_capital(self) -> CapitalConstraintsConfig:
        if self.maximum_loss > self.amount:
            raise ValueError("maximum_loss cannot exceed capital amount")
        if (self.fx_rate_to_usd is None) != (self.fx_rate_as_of is None):
            raise ValueError("FX value and timestamp must both be supplied or both be null")
        reserve = self.safety_reserve_fraction.value
        if not isinstance(reserve, (int, float)) or isinstance(reserve, bool):
            raise ValueError("safety_reserve_fraction must be numeric")
        if not 0 <= float(reserve) < 1:
            raise ValueError("safety_reserve_fraction must be in [0, 1)")
        return self


class RiskProfileConfig(StrictModel):
    bounded_risk_only: Literal[True]
    loss_ladder_thresholds: list[float] = Field(min_length=1)
    large_loss_threshold: GovernedValue
    target_return: GovernedValue
    maximum_relative_spread: GovernedValue
    minimum_open_interest: GovernedValue
    minimum_volume: GovernedValue
    allow_missing_volume: bool

    @model_validator(mode="after")
    def validate_thresholds(self) -> RiskProfileConfig:
        thresholds = self.loss_ladder_thresholds
        if thresholds != sorted(set(thresholds)) or any(
            not 0 < value <= 1 for value in thresholds
        ):
            raise ValueError("loss ladder thresholds must be unique, sorted, and in (0, 1]")
        return self


class StrategyUniverseConfig(StrictModel):
    allowed_structures: list[Architecture] = Field(min_length=1)
    forbidden_structures: list[str] = Field(default_factory=list)
    horizon_min_days: int = Field(gt=0)
    horizon_max_days: int = Field(gt=0)
    strike_source: Literal["listed_chain"]
    expiration_source: Literal["listed_chain"]
    recipe_catalog_path: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_horizon(self) -> StrategyUniverseConfig:
        if self.horizon_max_days < self.horizon_min_days:
            raise ValueError("horizon_max_days must follow horizon_min_days")
        return self


class ModelDefinition(StrictModel):
    model_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    status: Literal["eligible", "experimental", "calibration_required", "blocked"]
    parameters: dict[str, GovernedValue] = Field(default_factory=dict)


class ModelUniverseConfig(StrictModel):
    models: list[ModelDefinition] = Field(min_length=1)
    selection_policy: Literal["pre_registered", "walk_forward_only"]
    model_addition_policy: Literal["deficiency_and_validation_required"]


class ScenarioDefinition(StrictModel):
    scenario_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    probability: GovernedValue | None
    inputs: dict[str, GovernedValue] = Field(default_factory=dict)


class ScenarioSetConfig(StrictModel):
    scenario_set_id: str = Field(min_length=1)
    scenarios: list[ScenarioDefinition] = Field(min_length=1)
    probability_measure: Literal["P", "Q", "none"]

    @model_validator(mode="after")
    def validate_probabilities(self) -> ScenarioSetConfig:
        values: list[float] = []
        for scenario in self.scenarios:
            if scenario.probability is None:
                continue
            value = scenario.probability.value
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError("scenario probabilities must be numeric")
            if not 0 <= float(value) <= 1:
                raise ValueError("scenario probabilities must be in [0, 1]")
            values.append(float(value))
        if values and len(values) != len(self.scenarios):
            raise ValueError("scenario probabilities must be supplied for all or none")
        if values and abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("scenario probabilities must sum to one")
        return self


class ExecutionAssumptionsConfig(StrictModel):
    scenario: Literal["optimistic", "base", "conservative", "stressed"]
    long_entry_side: Literal["ask"]
    short_entry_side: Literal["bid"]
    long_exit_side: Literal["bid"]
    short_exit_side: Literal["ask"]
    commission_per_contract_side: GovernedValue
    slippage_per_contract_side: GovernedValue
    quote_quality_required: Literal["live_broker", "combo", "eod_bid_ask", "indicative"]
    preview_only: Literal[True]
    order_capability: Literal["forbidden"]


class ValidationPolicyConfig(StrictModel):
    require_oos: Literal[True]
    walk_forward_method: Literal["rolling", "expanding"]
    minimum_train_observations: int = Field(gt=0)
    minimum_validation_observations: int = Field(gt=0)
    minimum_test_observations: int = Field(gt=0)
    minimum_holdout_observations: int = Field(gt=0)
    purge_days: int = Field(ge=0)
    embargo_days: int = Field(ge=0)
    final_holdout_id: str | None
    holdout_must_be_unopened: Literal[True]
    multiple_testing_method: Literal["holm", "benjamini_hochberg"]
    significance_level: GovernedValue
    minimum_economic_materiality: GovernedValue


class OptimizationObjectiveConfig(StrictModel):
    objective_type: Literal[
        "pareto_multi_objective",
        "maximize_probability_target_return",
    ]
    primary_metrics: list[str] = Field(min_length=1)
    secondary_ranking_weights: dict[str, GovernedValue] = Field(default_factory=dict)
    no_single_magic_score: Literal[True]


class ReportPolicyConfig(StrictModel):
    formats: list[Literal["json", "markdown", "html"]] = Field(min_length=1)
    display_raw_metrics: Literal[True]
    display_score_components: Literal[True]
    maximum_candidates: int = Field(gt=0)
    language: Literal["fr", "en"]
    score_versions: dict[str, str] = Field(min_length=5)


class PreOpraConfig(StrictModel):
    """The eleven mandatory configuration groups and no execution capability."""

    schema_version: Literal["1.0"]
    research_request: ResearchRequestConfig
    market_context: MarketContextConfig
    capital_constraints: CapitalConstraintsConfig
    risk_profile: RiskProfileConfig
    strategy_universe: StrategyUniverseConfig
    model_universe: ModelUniverseConfig
    scenario_set: ScenarioSetConfig
    execution_assumptions: ExecutionAssumptionsConfig
    validation_policy: ValidationPolicyConfig
    optimization_objective: OptimizationObjectiveConfig
    report_policy: ReportPolicyConfig
    extensions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cross_group_consistency(self) -> PreOpraConfig:
        if self.market_context.base_currency != self.capital_constraints.currency:
            raise ValueError("market and capital currencies must agree")
        if self.market_context.decision_cutoff.date() != self.research_request.as_of:
            raise ValueError("decision cutoff date must equal the request as_of date")
        return self
