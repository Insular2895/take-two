"""Strict contracts for knowledge, research runs, candidates, and decisions."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from take_two_options.budget import (
    BudgetDiagnostics,
    FlexibleBudgetPolicyV2,
    LifecycleCapitalRequirement,
)
from take_two_options.domain import ExerciseStyle, OptionType, PositionSide, StrictModel
from take_two_options.quantitative.contracts import (
    EvidenceLevel,
    Measure,
    ModelEligibility,
)


class KnowledgeKind(StrEnum):
    MECHANISM = "mechanism"
    HEURISTIC = "heuristic"
    RULE = "rule"
    STRATEGY_RECIPE = "strategy_recipe"
    WARNING = "warning"
    FORMULA = "formula"


class KnowledgeLifecycle(StrEnum):
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    COMPILABLE = "COMPILABLE"
    BLOCKED = "BLOCKED"
    DEPRECATED = "DEPRECATED"
    CONTRADICTED = "CONTRADICTED"


class MarketValidity(StrEnum):
    HISTORICAL_ONLY = "HISTORICAL_ONLY"
    THEORETICALLY_VALID = "THEORETICALLY_VALID"
    CURRENT_MARKET_VALID = "CURRENT_MARKET_VALID"
    UNKNOWN = "UNKNOWN"


class EmpiricalStatus(StrEnum):
    NOT_TESTED = "NOT_TESTED"
    BACKTESTED = "BACKTESTED"
    ROBUST = "ROBUST"
    FAILED = "FAILED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ExecutionStatus(StrEnum):
    NOT_CONSTRUCTIBLE = "NOT_CONSTRUCTIBLE"
    TTWO_TESTABLE = "TTWO_TESTABLE"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"
    LIVE_ASSISTED_ELIGIBLE = "LIVE_ASSISTED_ELIGIBLE"


class ParameterOrigin(StrEnum):
    SOURCED = "sourced"
    CALIBRATED = "calibrated"
    EXPERIMENTAL = "experimental"
    CALIBRATION_REQUIRED = "calibration_required"
    UNKNOWN = "unknown"


class Architecture(StrEnum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    CALL_BUTTERFLY = "call_butterfly"
    PUT_BUTTERFLY = "put_butterfly"
    CALL_BROKEN_WING_BUTTERFLY = "call_broken_wing_butterfly"
    PUT_BROKEN_WING_BUTTERFLY = "put_broken_wing_butterfly"
    CALL_CALENDAR = "call_calendar"
    PUT_CALENDAR = "put_calendar"
    CALL_DIAGONAL = "call_diagonal"
    PUT_DIAGONAL = "put_diagonal"
    LONG_STRADDLE = "long_straddle"
    LONG_STRANGLE = "long_strangle"
    IRON_CONDOR = "iron_condor"


class SourceReference(StrictModel):
    source_id: str = Field(min_length=1)
    author: str | None = None
    title: str = Field(min_length=1)
    edition_or_date: str | None = None
    chapter: str | None = None
    page: str | None = None
    accessed_at: date
    source_type: Literal[
        "book",
        "academic",
        "official",
        "company",
        "broker",
        "data_provider",
        "internal",
    ]
    uri: str | None = None
    confidence: Literal["low", "medium", "high"]
    excerpt_hash: str | None = None


class ParameterDefinition(StrictModel):
    name: str = Field(min_length=1)
    value: float | int | str | bool | list[float] | list[int] | None = None
    unit: str | None = None
    origin: ParameterOrigin
    source_id: str | None = None
    notes: str = ""


class ValidationHistoryEntry(StrictModel):
    checked_at: date
    status: Literal["passed", "failed", "insufficient_data", "to_review"]
    method: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class KnowledgeItem(StrictModel):
    object_type: Literal["knowledge_item"] = "knowledge_item"
    knowledge_id: str = Field(min_length=1)
    kind: KnowledgeKind
    lifecycle: KnowledgeLifecycle
    market_validity: MarketValidity
    empirical_status: EmpiricalStatus
    execution_status: ExecutionStatus
    sources: list[SourceReference] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    units: dict[str, str] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    action: str | None = None
    exceptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    parameters_provided: list[ParameterDefinition] = Field(default_factory=list)
    parameters_missing: list[str] = Field(default_factory=list)
    parameters_to_calibrate: list[str] = Field(default_factory=list)
    validation_history: list[ValidationHistoryEntry] = Field(default_factory=list)
    statement: str = Field(min_length=1)


class NumericRange(StrictModel):
    minimum: float | int | None = None
    maximum: float | int | None = None
    values: list[float] = Field(default_factory=list)
    unit: str | None = None
    origin: ParameterOrigin
    source_id: str | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> NumericRange:
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("range minimum cannot exceed maximum")
        if self.minimum is None and self.maximum is None and not self.values:
            raise ValueError("a range requires bounds or explicit values")
        return self


class StrategyLegTemplate(StrictModel):
    leg_id: str = Field(min_length=1)
    option_type: OptionType
    side: PositionSide
    quantity_ratio: int = Field(default=1, gt=0)
    expiration_role: Literal["same", "front", "back"]
    strike_role: Literal[
        "any",
        "lower",
        "center",
        "upper",
        "atm",
        "otm",
        "itm",
    ]


class StrategyRecipe(StrictModel):
    object_type: Literal["strategy_recipe"] = "strategy_recipe"
    recipe_id: str = Field(min_length=1)
    architecture: Architecture
    name: str = Field(min_length=1)
    lifecycle: KnowledgeLifecycle
    market_validity: MarketValidity
    empirical_status: EmpiricalStatus
    execution_status: ExecutionStatus
    allowed_theses: list[Literal["bullish", "bearish", "neutral", "volatile"]] = Field(min_length=1)
    legs: list[StrategyLegTemplate] = Field(min_length=1)
    sources: list[SourceReference] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    units: dict[str, str] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    action: str = Field(min_length=1)
    exceptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    parameters_provided: list[ParameterDefinition] = Field(default_factory=list)
    parameters_missing: list[str] = Field(default_factory=list)
    parameters_to_calibrate: list[str] = Field(default_factory=list)
    validation_history: list[ValidationHistoryEntry] = Field(default_factory=list)
    dte: NumericRange
    front_dte: NumericRange | None = None
    moneyness: NumericRange
    spread_width: NumericRange | None = None
    profit_targets: NumericRange
    stops: NumericRange
    holding_days: NumericRange
    rolling_rules: list[str] = Field(default_factory=lambda: ["none"])
    capital_recovery_rules: list[str] = Field(default_factory=lambda: ["none"])
    bounded_risk_required: Literal[True] = True

    @model_validator(mode="after")
    def disallow_leaps_architecture(self) -> StrategyRecipe:
        if "leaps" in self.architecture.value:
            raise ValueError("LEAPS is a maturity class, not an architecture")
        return self


class ModernValidationCheck(StrictModel):
    check_id: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    status: Literal["passed", "failed", "not_applicable", "insufficient_data", "to_review"]
    book_statement: str | None = None
    unchanged: str | None = None
    modernization: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class ModernValidationRecord(StrictModel):
    object_type: Literal["modern_validation"] = "modern_validation"
    validation_id: str = Field(min_length=1)
    target_ids: list[str] = Field(min_length=1)
    checked_at: date
    sources: list[SourceReference] = Field(min_length=1)
    checks: list[ModernValidationCheck] = Field(min_length=1)
    contradictions: list[str] = Field(default_factory=list)
    overall_status: Literal["passed", "blocked", "to_review", "insufficient_data"]


class CompiledRule(StrictModel):
    rule_id: str = Field(min_length=1)
    source_knowledge_id: str
    condition: str
    action: str
    parameter_values: dict[str, float | int | str | bool | list[float] | list[int] | None]
    parameter_origins: dict[str, ParameterOrigin]
    source_ids: list[str]
    blocking_reasons: list[str] = Field(default_factory=list)


class StrategyCatalog(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    compiled_at: datetime
    knowledge_hash: str = Field(min_length=64, max_length=64)
    rules: list[CompiledRule]
    recipes: list[StrategyRecipe]
    blocked_items: dict[str, list[str]] = Field(default_factory=dict)
    contradictions: list[str] = Field(default_factory=list)


class Catalyst(StrictModel):
    catalyst_id: str
    name: str
    start: date
    end: date
    source_ids: list[str] = Field(default_factory=list)


class LiquidityPolicy(StrictModel):
    policy_id: str
    minimum_open_interest: int = Field(ge=0)
    minimum_volume: int = Field(ge=0)
    maximum_relative_spread: float = Field(gt=0)
    allow_missing_volume: bool = False
    provenance: str
    status: Literal["sourced", "calibration_required", "experimental"]


class ExecutionPolicy(StrictModel):
    policy_id: str
    long_entry_side: Literal["ask"] = "ask"
    short_entry_side: Literal["bid"] = "bid"
    long_exit_side: Literal["bid"] = "bid"
    short_exit_side: Literal["ask"] = "ask"
    commission_per_contract_side: float = Field(ge=0)
    slippage_per_contract_side: float = Field(ge=0)
    quote_quality_required: Literal["live_broker", "combo", "eod_bid_ask", "indicative"]
    preview_only: Literal[True] = True
    provenance: str


class HoldoutPolicy(StrictModel):
    policy_id: str
    minimum_train_observations: int = Field(ge=1)
    minimum_validation_observations: int = Field(ge=1)
    minimum_test_observations: int = Field(ge=1)
    minimum_holdout_observations: int = Field(ge=1)
    contaminated_dataset_ids: list[str] = Field(default_factory=list)
    locked_holdout_id: str | None = None
    provenance: str


class DataRefreshPolicy(StrictModel):
    policy_id: str
    providers: list[Literal["marketdata", "alpaca", "cache"]] = Field(min_length=1)
    maximum_age_days: int = Field(ge=0)
    allow_cache_fallback: bool = True
    marketdata_strike_limit: int = Field(default=40, ge=1, le=100)


class MaintenancePreferences(StrictModel):
    allow_rolling: bool = True
    allow_capital_recovery: bool = True
    allow_scaling_out: bool = True
    review_frequency_days: int = Field(default=7, ge=1)


class TradeRequest(StrictModel):
    object_type: Literal["trade_request"] = "trade_request"
    request_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    as_of: date
    currency: str = Field(min_length=3, max_length=3)
    budget: float = Field(gt=0)
    maximum_loss: float = Field(gt=0)
    directional_thesis: Literal["bullish", "bearish", "neutral", "volatile"]
    thesis_summary: str = Field(min_length=1)
    thesis_invalidation_conditions: list[str] = Field(min_length=1)
    horizon_min_days: int = Field(gt=0)
    horizon_max_days: int = Field(gt=0)
    catalysts: list[Catalyst] = Field(default_factory=list)
    allowed_risk: Literal["bounded_only"] = "bounded_only"
    allowed_structures: list[Architecture] = Field(min_length=1)
    forbidden_structures: list[str] = Field(default_factory=list)
    maximum_contracts: int = Field(gt=0)
    existing_positions: list[dict[str, Any]] = Field(default_factory=list)
    event_constraints: list[str] = Field(default_factory=list)
    liquidity_policy: LiquidityPolicy
    execution_policy: ExecutionPolicy
    maintenance_preferences: MaintenancePreferences
    data_refresh_policy: DataRefreshPolicy
    final_holdout_policy: HoldoutPolicy
    fx_rate_to_usd: float | None = Field(default=None, gt=0)
    fx_rate_as_of: date | None = None
    safety_reserve_fraction: float = Field(default=0.05, ge=0, lt=1)

    @model_validator(mode="after")
    def validate_request(self) -> TradeRequest:
        if self.horizon_max_days < self.horizon_min_days:
            raise ValueError("horizon maximum must follow horizon minimum")
        if self.maximum_loss > self.budget:
            raise ValueError("maximum loss cannot exceed budget")
        if (self.fx_rate_to_usd is None) != (self.fx_rate_as_of is None):
            raise ValueError("FX rate and FX date must either both be set or both be null")
        return self


class QuoteSnapshot(StrictModel):
    symbol: str
    expiration: date
    option_type: OptionType
    strike: float = Field(gt=0)
    exercise_style: ExerciseStyle | None = None
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    bid_size: int | None = Field(default=None, ge=0)
    ask_size: int | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)
    open_interest: int | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0)
    delta: float | None = None
    quote_timestamp: datetime
    multiplier: int | None = Field(gt=0)
    multiplier_status: EvidenceLevel = EvidenceLevel.HEURISTIC
    contract_adjustment_status: EvidenceLevel = EvidenceLevel.UNKNOWN
    deliverable_description: str | None = None
    exchange_timestamp: datetime | None = None
    provider_timestamp: datetime | None = None
    received_at: datetime | None = None
    price_quality: Literal["live_broker", "combo", "eod_bid_ask", "indicative", "modeled"]
    source_id: str

    @model_validator(mode="after")
    def validate_quote(self) -> QuoteSnapshot:
        if self.ask is not None and self.bid is not None and self.ask < self.bid:
            raise ValueError("ask cannot be below bid")
        if self.multiplier_status is EvidenceLevel.UNKNOWN and self.multiplier is not None:
            raise ValueError("unknown multiplier status cannot carry a multiplier")
        if self.multiplier_status in {EvidenceLevel.KNOWN, EvidenceLevel.ESTIMATED} and (
            self.multiplier is None
        ):
            raise ValueError("known or estimated multiplier status requires a value")
        if (
            self.contract_adjustment_status is EvidenceLevel.KNOWN
            and self.deliverable_description is None
        ):
            raise ValueError("known contract adjustment status requires a deliverable")
        return self


class DividendCashFlowSnapshot(StrictModel):
    ex_date: date
    amount: float = Field(gt=0)
    source_id: str = Field(min_length=1)


class DatasetLineage(StrictModel):
    dataset_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    range_start: datetime | None = None
    range_end: datetime | None = None
    ingested_at: datetime
    schema_version: str = Field(min_length=1)
    dataset_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class MarketSnapshot(StrictModel):
    snapshot_id: str
    ticker: str
    as_of: datetime
    spot: float = Field(gt=0)
    spot_bid: float | None = Field(default=None, ge=0)
    spot_ask: float | None = Field(default=None, ge=0)
    spot_timestamp: datetime
    exchange_timestamp: datetime | None = None
    provider_timestamp: datetime | None = None
    received_at: datetime | None = None
    freshness_age_seconds: float | None = Field(default=None, ge=0)
    freshness_status: EvidenceLevel = EvidenceLevel.UNKNOWN
    risk_free_rate: float | None = None
    risk_free_rate_status: EvidenceLevel = EvidenceLevel.UNKNOWN
    risk_free_rate_source_id: str | None = None
    continuous_dividend_yield: float | None = Field(default=None, ge=0)
    discrete_dividends: list[DividendCashFlowSnapshot] = Field(default_factory=list)
    dividend_status: EvidenceLevel = EvidenceLevel.UNKNOWN
    quote_quality: Literal["live_broker", "eod_bid_ask", "indicative", "mixed"]
    source_ids: list[str] = Field(min_length=1)
    quotes: list[QuoteSnapshot] = Field(min_length=1)
    available_expirations: list[date]
    data_warnings: list[str] = Field(default_factory=list)
    cache_path: str | None = None
    lineage: DatasetLineage | None = None

    @model_validator(mode="after")
    def validate_economic_inputs(self) -> MarketSnapshot:
        if self.risk_free_rate_status is EvidenceLevel.UNKNOWN and self.risk_free_rate is not None:
            raise ValueError("unknown rate status cannot carry a rate")
        if self.risk_free_rate_status in {EvidenceLevel.KNOWN, EvidenceLevel.ESTIMATED} and (
            self.risk_free_rate is None or self.risk_free_rate_source_id is None
        ):
            raise ValueError("known or estimated rates require a value and source")
        if self.dividend_status is EvidenceLevel.UNKNOWN and (
            self.continuous_dividend_yield is not None or self.discrete_dividends
        ):
            raise ValueError("unknown dividend status cannot carry dividend inputs")
        if (
            self.dividend_status in {EvidenceLevel.KNOWN, EvidenceLevel.ESTIMATED}
            and self.continuous_dividend_yield is None
            and not self.discrete_dividends
        ):
            raise ValueError("known or estimated dividends require an explicit input")
        if self.dividend_status is EvidenceLevel.NOT_APPLICABLE and (
            self.continuous_dividend_yield is not None or self.discrete_dividends
        ):
            raise ValueError("not-applicable dividends cannot carry dividend inputs")
        return self


class CandidateLeg(StrictModel):
    side: PositionSide
    quantity: int = Field(gt=0)
    quote: QuoteSnapshot
    entry_price: float = Field(ge=0)


class ExitPolicy(StrictModel):
    policy_id: str
    profit_target: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    maximum_holding_days: int = Field(gt=0)
    trailing_stop: float | None = Field(default=None, gt=0)
    origin: ParameterOrigin


class MaintenancePolicy(StrictModel):
    rolling_rule: str
    capital_recovery_rule: str
    review_frequency_days: int = Field(gt=0)
    partial_recovery_feasible: bool


class CandidateRisk(StrictModel):
    theoretical_mid_entry: float | None = None
    entry_bid_ask_cost: float | None = Field(default=None, ge=0)
    entry_debit: float
    fees: float = Field(ge=0)
    slippage: float = Field(ge=0)
    total_cost: float
    maximum_loss: float | None = Field(default=None, ge=0)
    maximum_loss_status: EvidenceLevel = EvidenceLevel.UNKNOWN
    diagnostic_common_expiry_maximum_loss: float | None = Field(default=None, ge=0)
    maximum_gain: float | None = Field(default=None, ge=0)
    break_even_points: list[float] = Field(default_factory=list)
    budget_remaining: float | None = None
    bounded: bool
    executable_sides_used: bool

    @model_validator(mode="before")
    @classmethod
    def label_legacy_maximum_loss(cls, data: Any) -> Any:
        if isinstance(data, dict) and "maximum_loss_status" not in data:
            migrated = dict(data)
            migrated["maximum_loss_status"] = (
                EvidenceLevel.UNVALIDATED
                if migrated.get("maximum_loss") is not None
                else EvidenceLevel.UNKNOWN
            )
            return migrated
        return data

    @model_validator(mode="after")
    def validate_maximum_loss_evidence(self) -> CandidateRisk:
        unavailable = {
            EvidenceLevel.UNKNOWN,
            EvidenceLevel.INSUFFICIENT_DATA,
            EvidenceLevel.BLOCKED,
            EvidenceLevel.NOT_APPLICABLE,
        }
        if self.maximum_loss_status in unavailable and self.maximum_loss is not None:
            raise ValueError("unavailable maximum loss must remain null")
        if self.maximum_loss_status not in unavailable and self.maximum_loss is None:
            raise ValueError("available maximum loss evidence requires a value")
        return self


class ModelMetrics(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    model_id: str
    measure: Measure
    eligibility: ModelEligibility
    eligibility_reasons: list[str] = Field(default_factory=list)
    paths: int = Field(gt=0)
    seed: int
    probability_profit: float = Field(ge=0, le=1)
    probability_gain_50: float | None = Field(default=None, ge=0, le=1)
    probability_gain_80: float | None = Field(default=None, ge=0, le=1)
    probability_gain_100: float | None = Field(default=None, ge=0, le=1)
    probability_loss_50: float | None = Field(default=None, ge=0, le=1)
    probability_loss_70: float | None = Field(default=None, ge=0, le=1)
    probability_near_total_loss: float | None = Field(default=None, ge=0, le=1)
    expected_pnl: float
    median_pnl: float
    quantiles: dict[str, float]
    var_95: float = Field(ge=0)
    cvar_95: float = Field(ge=0)
    simulated_drawdown: float = Field(ge=0)
    mean_exit_days: float = Field(ge=0)
    take_profit_frequency: float = Field(ge=0, le=1)
    stop_frequency: float = Field(ge=0, le=1)
    exit_reasons: dict[str, int]

    @model_validator(mode="after")
    def prevent_q_measure_decisions(self) -> ModelMetrics:
        if (
            self.eligibility is ModelEligibility.DECISION_ELIGIBLE
            and self.measure is not Measure.REAL_WORLD
        ):
            raise ValueError("decision-eligible probability metrics require measure P")
        return self


class SampleGate(StrictModel):
    configured_minimum: int = Field(gt=0)
    available_observations: int = Field(ge=0)
    status: Literal["PASSED", "INSUFFICIENT_DATA"]


class ValidationMetrics(StrictModel):
    status: Literal["PASSED", "FAILED", "INSUFFICIENT_DATA", "CONTAMINATED"]
    train: SampleGate
    validation: SampleGate
    test: SampleGate
    holdout: SampleGate
    nested_walk_forward_windows: int = Field(ge=0)
    purged_observations: int = Field(ge=0)
    embargo_days: int = Field(ge=0)
    deflated_sharpe_probability: float | None = Field(default=None, ge=0, le=1)
    pbo: float | None = Field(default=None, ge=0, le=1)
    parameter_stability: float | None = Field(default=None, ge=0, le=1)
    stress_passed: bool
    placebo_passed: bool
    gates: dict[str, Literal["passed", "failed", "insufficient_data", "not_calculable"]]
    reasons: list[str] = Field(default_factory=list)


class CandidateEvaluation(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    model_metrics: list[ModelMetrics] = Field(default_factory=list)
    conservative_expected_pnl: float | None = None
    model_dispersion: float | None = Field(default=None, ge=0)
    decision_status: ModelEligibility = ModelEligibility.BLOCKED
    decision_reasons: list[str] = Field(default_factory=list)
    numerical_failures: list[str] = Field(default_factory=list)
    validation: ValidationMetrics | None = None
    complexity_penalty: float = Field(default=0, ge=0)
    local_stability: float | None = Field(default=None, ge=0, le=1)
    stress_results: dict[str, float] = Field(default_factory=dict)
    placebo_results: dict[str, float] = Field(default_factory=dict)


class CompiledStrategyCandidate(StrictModel):
    candidate_id: str = Field(min_length=1)
    architecture: Architecture
    recipe_id: str
    legs: list[CandidateLeg] = Field(min_length=1)
    exit_policy: ExitPolicy
    maintenance_policy: MaintenancePolicy
    risk: CandidateRisk
    horizon_compatible: bool
    thesis_compatible: bool
    liquidity_compatible: bool
    broker_constructible: bool
    source_ids: list[str]
    assumptions: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    hard_vetoes: list[str] = Field(default_factory=list)
    research_restrictions: list[str] = Field(default_factory=list)
    budget_diagnostics: BudgetDiagnostics | None = None
    lifecycle_capital_requirement: LifecycleCapitalRequirement | None = None
    phase_m_context_id: str | None = Field(
        default=None,
        pattern=r"^phase-m-context-[a-f0-9]{16}$",
    )
    phase_m_context_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evaluation: CandidateEvaluation = Field(default_factory=CandidateEvaluation)
    pareto_rank: int | None = Field(default=None, ge=1)
    explanatory_score: float | None = Field(default=None, ge=0, le=100)
    status: Literal["generated", "pruned", "blocked", "watchlist", "admissible"] = "generated"


class TrialRecord(StrictModel):
    trial_id: str
    run_id: str
    stage: Literal[
        "generation",
        "pruning",
        "coarse_search",
        "fine_search",
        "stress",
        "placebo",
        "validation",
        "ranking",
    ]
    architecture: Architecture | None = None
    candidate_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    outcome: Literal["generated", "pruned", "evaluated", "failed", "selected", "rejected"]
    reason: str = ""
    seed: int
    config_hash: str = Field(min_length=64, max_length=64)


class ResearchRun(StrictModel):
    object_type: Literal["research_run"] = "research_run"
    run_id: str
    started_at: datetime
    completed_at: datetime | None = None
    seed: int
    config_hash: str = Field(min_length=64, max_length=64)
    code_version: str
    request_id: str
    knowledge_hash: str = Field(min_length=64, max_length=64)
    data_snapshot_id: str | None = None
    dataset_id: str | None = None
    dataset_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    model_versions: dict[str, str] = Field(default_factory=dict)
    total_trials: int = Field(default=0, ge=0)
    trials_by_stage: dict[str, int] = Field(default_factory=dict)
    status: Literal["running", "completed", "blocked", "failed"] = "running"


class ReportAnalysis(StrictModel):
    ticker: str
    budget: float
    currency: str
    thesis: str
    horizon_days: tuple[int, int]
    data_date: datetime | None = None
    data_quality: str
    holdout_status: str
    total_trials: int = Field(ge=0)


class Verdict(StrEnum):
    TRADE_ADMISSIBLE = "TRADE_ADMISSIBLE"
    WATCHLIST = "WATCHLIST"
    WAIT = "WAIT"
    NO_TRADE = "NO_TRADE"
    BLOCKED_INSUFFICIENT_DATA = "BLOCKED_INSUFFICIENT_DATA"


class DecisionReport(StrictModel):
    object_type: Literal["decision_report"] = "decision_report"
    schema_version: Literal["1.0"] = "1.0"
    report_id: str
    created_at: datetime
    budget_policy: FlexibleBudgetPolicyV2 | None = None
    phase_m_context_id: str | None = Field(
        default=None,
        pattern=r"^phase-m-context-[a-f0-9]{16}$",
    )
    phase_m_context_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    analysis: ReportAnalysis
    verdict: Verdict
    request: TradeRequest
    research_run: ResearchRun
    candidates: list[CompiledStrategyCandidate] = Field(default_factory=list)
    pareto_candidate_ids: list[str] = Field(default_factory=list)
    candidate_comparison: list[dict[str, Any]] = Field(default_factory=list)
    no_trade_reasons: list[str] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    data_used: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    audit_files: list[str] = Field(default_factory=list)
    visualization_files: list[str] = Field(default_factory=list)
    ibkr_ticket_path: str | None = None
    order_capability: Literal["forbidden"] = "forbidden"
