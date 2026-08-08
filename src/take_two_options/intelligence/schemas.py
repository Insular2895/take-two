"""Strict, auditable contracts for the modular V11 intelligence layer."""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class DataDomain(StrEnum):
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    MARKET = "market"
    OPTIONS = "options"
    CATALYST = "catalyst"
    ATTENTION = "attention"
    EXECUTION = "execution"


class DataQuality(StrEnum):
    LIVE_BROKER = "live_broker"
    OPRA = "opra"
    OFFICIAL = "official"
    DELAYED = "delayed"
    EOD = "eod"
    INDICATIVE = "indicative"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


class ConnectorState(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    NOT_CONFIGURED = "not_configured"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class FeatureStatus(StrEnum):
    PRODUCTION_READY_OFFLINE = "production_ready_offline"
    EXPERIMENTAL_OFFLINE = "experimental_offline"
    FIXTURE_ONLY = "fixture_only"
    ADAPTER_READY_NOT_CONNECTED = "adapter_ready_not_connected"
    REQUIRES_LIVE_MARKET_DATA = "requires_live_market_data"
    REQUIRES_HISTORICAL_CALIBRATION = "requires_historical_calibration"
    REQUIRES_PAPER_TRADING = "requires_paper_trading"
    BLOCKED_FOR_EXECUTION = "blocked_for_execution"


class FreshnessStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    FUTURE = "future"
    UNKNOWN = "unknown"
    BLOCKED_MISSING_TIMESTAMP = "blocked_missing_timestamp"


class HumanReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RobustnessVerdict(StrEnum):
    ROBUST = "robust"
    CONDITIONALLY_ROBUST = "conditionally_robust"
    FRAGILE = "fragile"
    MODEL_DEPENDENT = "model_dependent"
    DATA_INSUFFICIENT = "data_insufficient"


class NormalizedEventType(StrEnum):
    GTA_RELEASE_DATE_CONFIRMED = "GTA_RELEASE_DATE_CONFIRMED"
    GTA_DELAY_CONFIRMED = "EVENT_GTA_DELAY_CONFIRMED"
    RELEASE_DATE_MAINTAINED = "EVENT_RELEASE_DATE_MAINTAINED"
    GUIDANCE_RAISED = "GUIDANCE_RAISED"
    GUIDANCE_LOWERED = "GUIDANCE_LOWERED"
    GUIDANCE_UP = "EVENT_GUIDANCE_UP"
    GUIDANCE_DOWN = "EVENT_GUIDANCE_DOWN"
    INSIDER_BUY = "EVENT_INSIDER_BUY"
    INSIDER_SELL = "INSIDER_SELL"
    SEARCH_INTEREST_UP = "EVENT_SEARCH_INTEREST_UP"
    SEARCH_ATTENTION_UP = "SEARCH_ATTENTION_UP"
    SEARCH_ATTENTION_DOWN = "SEARCH_ATTENTION_DOWN"
    IV_SPIKE = "EVENT_IV_SPIKE"
    IMPLIED_VOLATILITY_SPIKE = "IMPLIED_VOLATILITY_SPIKE"
    IMPLIED_VOLATILITY_CRUSH = "IMPLIED_VOLATILITY_CRUSH"
    OPTIONS_FLOW_BULLISH = "EVENT_OPTIONS_FLOW_BULLISH"
    EARNINGS_BEAT = "EVENT_EARNINGS_BEAT"
    EARNINGS_MISS = "EVENT_EARNINGS_MISS"
    MATERIAL_8K = "MATERIAL_8K"
    MACRO_RISK_UP = "MACRO_RISK_UP"
    MACRO_RISK_DOWN = "MACRO_RISK_DOWN"
    LIQUIDITY_DETERIORATION = "LIQUIDITY_DETERIORATION"
    LIQUIDITY_IMPROVEMENT = "LIQUIDITY_IMPROVEMENT"
    LAUNCH_EXCEPTIONAL = "EVENT_LAUNCH_EXCEPTIONAL"
    LAUNCH_DISAPPOINTING = "EVENT_LAUNCH_DISAPPOINTING"


class EvidenceFamily(StrEnum):
    COMPANY_PRIMARY = "company_primary"
    REGULATORY = "regulatory"
    FUNDAMENTALS = "fundamentals"
    MARKET = "market"
    OPTIONS = "options"
    ATTENTION = "attention"
    NEWS = "news"
    SOCIAL = "social"


class SimulationRegime(StrEnum):
    NEUTRAL = "neutral"
    THESIS = "thesis"
    ADVERSE = "adverse"
    RUPTURE = "rupture"


class StochasticModel(StrEnum):
    GBM = "black_scholes_gbm"
    LOCAL_VOLATILITY = "local_volatility"
    HESTON = "heston"
    HESTON_JUMP = "heston_jump"


class ResearchPosture(StrEnum):
    BLOCKED = "blocked"
    NO_TRADE = "no_trade"
    WATCHLIST = "watchlist"
    PAPER_REVIEW = "paper_review"


class MonitorAction(StrEnum):
    HOLD = "HOLD"
    KEEP = "HOLD"
    WATCH = "WATCH"
    REDUCE = "REDUCE"
    EXIT_REVIEW = "EXIT_REVIEW"
    EXIT = "EXIT_REVIEW"
    THESIS_INVALIDATED = "THESIS_INVALIDATED"
    DATA_STALE = "DATA_STALE"
    BLOCKED_INSUFFICIENT_DATA = "BLOCKED_INSUFFICIENT_DATA"


class SourceProvenance(StrictModel):
    source_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    uri: str | None = None
    retrieved_at: datetime
    data_domain: DataDomain
    quality: DataQuality
    license_or_terms: str | None = None
    content_hash: str | None = None
    notes: list[str] = Field(default_factory=list)


class UnifiedObservation(StrictModel):
    observation_id: str = Field(min_length=1)
    series: str = Field(min_length=1)
    timestamp: datetime
    value: float | int | str | bool
    unit: str
    source_id: str
    domain: DataDomain
    quality: DataQuality
    retrieved_at: datetime | None = None
    cutoff: datetime | None = None
    provider: str | None = None
    source_uri: str | None = None
    freshness_status: FreshnessStatus = FreshnessStatus.UNKNOWN
    point_in_time_valid: bool = False
    raw_hash: str | None = None
    license_or_usage_notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectorStatus(StrictModel):
    connector_id: str
    state: ConnectorState
    checked_at: datetime
    observations: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class UnifiedDataSnapshot(StrictModel):
    schema_version: Literal["11.1"] = "11.1"
    snapshot_id: str
    ticker: str
    as_of: datetime
    sources: list[SourceProvenance]
    observations: list[UnifiedObservation]
    connectors: list[ConnectorStatus]
    missing_required_series: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_observation_lineage(self) -> UnifiedDataSnapshot:
        source_ids = {source.source_id for source in self.sources}
        for observation in self.observations:
            if observation.source_id not in source_ids:
                raise ValueError(
                    f"observation {observation.observation_id} references an unknown source"
                )
            if (
                observation.retrieved_at is None
                or observation.cutoff is None
                or observation.provider is None
                or observation.raw_hash is None
            ):
                raise ValueError(f"observation {observation.observation_id} lacks complete lineage")
            if not observation.point_in_time_valid:
                raise ValueError(
                    f"observation {observation.observation_id} is not point-in-time valid"
                )
        return self


class NormalizedEvidenceEvent(StrictModel):
    event_id: str
    event_type: NormalizedEventType
    family: EvidenceFamily
    occurred_at: datetime
    observed_at: datetime
    event_time: datetime | None = None
    first_seen_at: datetime | None = None
    canonical_fact_id: str = Field(
        min_length=1,
        description="Stable deduplication key shared by reports of the same underlying fact.",
    )
    source_ids: list[str] = Field(min_length=1)
    source_family: EvidenceFamily | None = None
    confidence: float = Field(ge=0, le=1)
    direction: Literal["supports", "contradicts", "neutral"] = "supports"
    entity: str = "TTWO"
    severity: float = Field(default=0.5, ge=0, le=1)
    novelty: float = Field(default=1.0, ge=0, le=1)
    duplicate_cluster_id: str | None = None
    contradiction_cluster_id: str | None = None
    normalization_rule_id: str = "explicit_normalized_input"
    human_review_status: HumanReviewStatus = HumanReviewStatus.APPROVED
    quality_multiplier: float = Field(default=1.0, ge=0, le=1)
    freshness_multiplier: float = Field(default=1.0, ge=0, le=1)
    expires_at: datetime | None = None
    contradictory_source_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event_timeline(self) -> NormalizedEvidenceEvent:
        if self.occurred_at > self.observed_at:
            raise ValueError("event cannot be observed before it occurred")
        if self.expires_at is not None and self.expires_at < self.observed_at:
            raise ValueError("event expiry cannot precede first observation")
        object.__setattr__(
            self,
            "event_time",
            self.event_time or self.occurred_at,
        )
        object.__setattr__(
            self,
            "first_seen_at",
            self.first_seen_at or self.observed_at,
        )
        object.__setattr__(
            self,
            "source_family",
            self.source_family or self.family,
        )
        return self


class EventNormalizationRule(StrictModel):
    rule_id: str = Field(min_length=1)
    series_pattern: str = Field(min_length=1)
    event_type: NormalizedEventType
    family: EvidenceFamily
    entity: str = "TTWO"
    operator: Literal[
        "greater_than",
        "less_than",
        "equals",
        "contains_all_tokens",
    ]
    threshold: float | int | str | bool
    expected_unit: str | None = None
    direction: Literal["supports", "contradicts", "neutral"] = "supports"
    severity: float = Field(default=0.5, ge=0, le=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    ttl_days: int = Field(default=30, ge=1)
    requires_human_review: bool = False
    contradiction_group: str | None = None
    canonical_metadata_fields: list[str] = Field(default_factory=list)


class EventNormalizationReport(StrictModel):
    cutoff: datetime
    events: list[NormalizedEvidenceEvent]
    duplicate_observation_ids: list[str] = Field(default_factory=list)
    contradiction_clusters: dict[str, list[str]] = Field(default_factory=dict)
    expired_event_ids: list[str] = Field(default_factory=list)
    unmatched_observation_ids: list[str] = Field(default_factory=list)
    rule_proofs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class LikelihoodRule(StrictModel):
    rule_id: str | None = None
    event_type: NormalizedEventType
    family: EvidenceFamily
    likelihood_by_scenario: dict[str, float]
    base_weight: float = Field(default=1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_likelihoods(self) -> LikelihoodRule:
        if not self.likelihood_by_scenario:
            raise ValueError("likelihood rule requires scenarios")
        if self.rule_id is not None and not self.rule_id.strip():
            raise ValueError("likelihood rule_id cannot be blank")
        if any(value <= 0 or value > 1 for value in self.likelihood_by_scenario.values()):
            raise ValueError("scenario likelihoods must be in (0, 1]")
        return self


class BayesianUpdateRecord(StrictModel):
    sequence: int = Field(ge=1)
    event_id: str
    canonical_fact_id: str
    family: EvidenceFamily
    prior: dict[str, float]
    likelihoods: dict[str, float]
    likelihood_ratios: dict[str, float]
    requested_weight: float = Field(ge=0, le=1)
    raw_weight: float = Field(ge=0, le=1)
    weight_after_quality: float = Field(ge=0, le=1)
    weight_after_freshness: float = Field(ge=0, le=1)
    weight_after_deduplication: float = Field(ge=0, le=1)
    family_cap: float = Field(ge=0, le=1)
    effective_weight: float = Field(ge=0, le=1)
    unnormalized_posterior: dict[str, float]
    posterior: dict[str, float]
    probability_delta: dict[str, float]
    confidence: float = Field(ge=0, le=1)
    confidence_after_contradiction: float = Field(ge=0, le=1)
    deduplicated: bool
    family_cap_applied: bool
    ignored_reason: str | None = None
    justification: str
    rule_id: str
    contradictory_source_ids: list[str] = Field(default_factory=list)


class BayesianSensitivityReport(StrictModel):
    posterior_minimum: dict[str, float]
    posterior_central: dict[str, float]
    posterior_maximum: dict[str, float]
    likelihood_weight_range: tuple[float, float]
    maximum_probability_swing: float = Field(ge=0, le=1)
    ranking_stable: bool
    warnings: list[str] = Field(default_factory=list)


class BayesianScenarioDistribution(StrictModel):
    scenario_probabilities: dict[str, float]
    updates: list[BayesianUpdateRecord]
    family_weight_used: dict[EvidenceFamily, float]
    ignored_event_ids: list[str] = Field(default_factory=list)
    sensitivity: BayesianSensitivityReport | None = None
    confidence_level: Literal["low", "medium", "high"] = "low"
    assumptions: list[str] = Field(default_factory=list)

    @property
    def semantic_type(self) -> Literal["configured_heuristic_belief"]:
        """Compatibility-safe label: this is not a fitted statistical posterior."""
        return "configured_heuristic_belief"

    @property
    def evidence_sufficiency_level(self) -> Literal["low", "medium", "high"]:
        return self.confidence_level

    @model_validator(mode="after")
    def validate_distribution(self) -> BayesianScenarioDistribution:
        if not self.scenario_probabilities:
            raise ValueError("Bayesian distribution requires scenarios")
        if abs(sum(self.scenario_probabilities.values()) - 1) > 1e-8:
            raise ValueError("posterior scenario probabilities must sum to one")
        if any(
            not math.isfinite(value) or value < 0 or value > 1
            for value in self.scenario_probabilities.values()
        ):
            raise ValueError("posterior probabilities must be finite and bounded")
        return self


class JumpParameters(StrictModel):
    intensity_per_year: float = Field(ge=0)
    log_mean: float
    log_volatility: float = Field(ge=0)


class HestonParameters(StrictModel):
    initial_variance: float = Field(gt=0)
    mean_reversion: float = Field(gt=0)
    long_run_variance: float = Field(gt=0)
    vol_of_variance: float = Field(gt=0)
    correlation: float = Field(ge=-1, le=1)
    calibration_status: Literal[
        "calibrated",
        "illustrative",
        "insufficient_data",
    ] = "illustrative"
    calibration_error: float | None = Field(default=None, ge=0)
    calibration_iterations: int | None = Field(default=None, ge=0)

    @property
    def feller_condition_satisfied(self) -> bool:
        return 2 * self.mean_reversion * self.long_run_variance >= self.vol_of_variance**2


class LocalVolatilityNode(StrictModel):
    time_years: float = Field(ge=0)
    moneyness: float = Field(gt=0)
    volatility: float = Field(gt=0, lt=5)


class LocalVolatilityCalibrationReport(StrictModel):
    status: Literal["calibrated", "partial", "insufficient_data"]
    method: Literal["dupire_total_variance_finite_difference"]
    expirations: int = Field(ge=0)
    moneyness_nodes: int = Field(ge=0)
    output_nodes: int = Field(ge=0)
    fallback_nodes: int = Field(ge=0)
    calendar_arbitrage_violations: int = Field(default=0, ge=0)
    butterfly_arbitrage_violations: int = Field(default=0, ge=0)
    arbitrage_free_input: bool = False
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SimulationRegimeConfig(StrictModel):
    regime: SimulationRegime
    probability: float = Field(ge=0, le=1)
    annual_drift: float
    volatility_multiplier: float = Field(gt=0)
    initial_iv_shift: float = Field(default=0, gt=-1)
    jump: JumpParameters
    description: str


class SimulationPolicy(StrictModel):
    paths: int = Field(ge=64)
    horizon_days: int = Field(gt=0)
    steps: int = Field(gt=1)
    seed: int
    initial_volatility: float = Field(gt=0)
    risk_free_rate: float
    dividend_yield: float = Field(ge=0, lt=1)
    models: list[StochasticModel] = Field(min_length=1)
    regimes: list[SimulationRegimeConfig] = Field(min_length=4)
    heston: HestonParameters
    local_volatility_nodes: list[LocalVolatilityNode] = Field(min_length=4)

    @model_validator(mode="after")
    def validate_simulation(self) -> SimulationPolicy:
        if set(item.regime for item in self.regimes) != set(SimulationRegime):
            raise ValueError("all four simulation regimes must be configured exactly once")
        if abs(sum(item.probability for item in self.regimes) - 1) > 1e-8:
            raise ValueError("simulation regime probabilities must sum to one")
        if len(set(self.models)) != len(self.models):
            raise ValueError("simulation models cannot be duplicated")
        return self


class CovarianceWindow(StrictModel):
    label: str
    observations: int = Field(ge=0)
    weight: float = Field(ge=0, le=1)
    covariance: list[list[float]]


class DynamicCovarianceReport(StrictModel):
    status: Literal["ready", "partial", "insufficient_data"]
    factors: list[str]
    windows: list[CovarianceWindow]
    shrunk_covariance: list[list[float]]
    correlation: list[list[float]]
    shrinkage_intensity: float = Field(ge=0, le=1)
    minimum_eigenvalue: float
    condition_number: float | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)


class ExitPolicyConfig(StrictModel):
    profit_target: float = Field(gt=0)
    partial_profit_target: float = Field(gt=0)
    operational_stop_loss: float = Field(gt=0, le=1)
    exit_days_before_expiration: int = Field(ge=0)
    iv_crush_threshold: float = Field(gt=0, le=1)
    trailing_drawdown: float = Field(gt=0, le=1)
    maximum_theta_loss_per_day_usd: float | None = Field(default=None, ge=0)
    minimum_liquidity_score: float = Field(default=0.0, ge=0, le=1)
    maximum_cvar_fraction: float = Field(default=0.80, gt=0)
    exit_if_expected_value_negative: bool = True
    exit_if_data_insufficient: bool = True
    exit_before_catalyst_days: int | None = Field(default=None, ge=0)
    exit_after_catalyst_days: int | None = Field(default=None, ge=0)


class ExitRuleDefinition(StrictModel):
    rule_id: str
    description: str
    threshold: float | int | str | bool
    severity: Literal["info", "warning", "critical"]
    suggested_action: MonitorAction
    required_data: list[str]
    human_confirmation_required: Literal[True] = True


class ExitRuleTrigger(StrictModel):
    rule_id: str
    observed_value: float | int | str | bool | None
    threshold: float | int | str | bool
    triggered_at: datetime
    severity: Literal["info", "warning", "critical"]
    suggested_action: MonitorAction
    required_data: list[str]
    confidence: float = Field(ge=0, le=1)


class CandidateExitPlan(StrictModel):
    candidate_id: str
    profit_target: float
    partial_profit_target: float
    operational_stop_loss: float
    exit_days_before_expiration: int = Field(ge=0)
    iv_crush_threshold: float = Field(gt=0, le=1)
    trailing_drawdown: float = Field(gt=0, le=1)
    fundamental_invalidations: list[str]
    temporal_invalidation: str
    iv_invalidation: str
    catalyst_rule: str
    trailing_rule: str
    rules: list[ExitRuleDefinition] = Field(default_factory=list)
    human_review_required: Literal[True] = True


class StrategyModelMetrics(StrictModel):
    candidate_id: str
    model: StochasticModel
    regime: SimulationRegime
    paths: int = Field(gt=0)
    seed: int
    steps: int = Field(gt=1)
    expected_pnl_usd: float
    median_pnl_usd: float
    standard_error_usd: float = Field(ge=0)
    confidence_interval_95_low_usd: float
    confidence_interval_95_high_usd: float
    convergence_status: Literal["converged", "unstable", "not_tested"]
    convergence_delta_fraction: float = Field(ge=0)
    model_valid: bool = True
    calibration_status: Literal[
        "calibrated",
        "illustrative",
        "partial",
        "insufficient_data",
    ] = "illustrative"
    probability_profit: float = Field(ge=0, le=1)
    probability_total_loss: float = Field(ge=0, le=1)
    probability_x2: float = Field(ge=0, le=1)
    probability_x3: float = Field(ge=0, le=1)
    probability_x5: float = Field(ge=0, le=1)
    var_95_usd: float = Field(ge=0)
    cvar_95_usd: float = Field(ge=0)
    maximum_drawdown_usd: float = Field(ge=0)
    reasonable_worst_pnl_usd: float
    reasonable_best_pnl_usd: float
    mean_days_to_profit: float | None = Field(default=None, ge=0)
    probability_exit_before_horizon: float = Field(ge=0, le=1)
    exit_reasons: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class CandidateRobustness(StrictModel):
    candidate_id: str
    profitable_model_fraction: float = Field(ge=0, le=1)
    worst_expected_pnl_usd: float
    neutral_model_dispersion_usd: float = Field(ge=0)
    adverse_cvar_usd: float = Field(ge=0)
    probability_profit_dispersion: float = Field(default=0, ge=0, le=1)
    expected_pnl_dispersion_usd: float = Field(default=0, ge=0)
    cvar_dispersion_usd: float = Field(default=0, ge=0)
    ranking_variation: float = Field(default=0, ge=0)
    invalid_model_count: int = Field(default=0, ge=0)
    robustness_score: float = Field(ge=0, le=100)
    verdict: RobustnessVerdict = RobustnessVerdict.DATA_INSUFFICIENT
    model_risk_flags: list[str] = Field(default_factory=list)


class StressTestResult(StrictModel):
    candidate_id: str
    stress_id: str
    status: Literal["passed", "failed", "data_insufficient", "diagnostic_only"]
    stressed_pnl_usd: float | None = None
    method: str
    assumptions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class CandidateValidationSummary(StrictModel):
    candidate_id: str
    walk_forward_status: Literal[
        "passed",
        "failed",
        "insufficient_data",
        "contaminated",
    ]
    holdout_status: Literal[
        "passed",
        "failed",
        "insufficient_data",
        "contaminated",
    ]
    stress_status: Literal["passed", "failed"]
    stress_results: dict[str, float]
    paper_status: Literal["passed", "failed", "not_run"]
    promotion_eligible: Literal[False] = False
    reasons: list[str] = Field(default_factory=list)


class OptimizerProfileConfig(StrictModel):
    risk_aversion: float = Field(ge=0)
    cvar_aversion: float = Field(ge=0)
    execution_penalty: float = Field(ge=0)
    model_risk_penalty: float = Field(ge=0)
    maximum_allocations: int = Field(default=5, ge=1)


class AllocationLine(StrictModel):
    candidate_id: str
    strategy_units: int = Field(gt=0)
    option_contracts: int = Field(gt=0)
    cost_eur: float = Field(ge=0)
    maximum_loss_eur: float = Field(ge=0)


class ContinuousDiagnostics(StrictModel):
    gradient: list[float]
    hessian: list[list[float]]
    hessian_eigenvalues: list[float]
    concave_quadratic_component: bool
    notes: list[str] = Field(default_factory=list)


class AllocationResult(StrictModel):
    allocation_id: str
    profile: Literal["prudent", "balanced", "aggressive"]
    rank: int = Field(ge=1)
    lines: list[AllocationLine]
    cash_reserve_eur: float = Field(ge=0)
    expected_pnl_eur: float
    volatility_eur: float = Field(ge=0)
    cvar_95_eur: float = Field(ge=0)
    execution_risk_eur: float = Field(ge=0)
    model_dispersion_eur: float = Field(ge=0)
    objective: float
    constraint_checks: dict[str, bool]
    diagnostics: ContinuousDiagnostics
    no_trade: bool = False
    active_constraints: list[str] = Field(default_factory=list)
    near_miss_allocations: list[str] = Field(default_factory=list)
    constraint_sensitivity: list[str] = Field(default_factory=list)
    cash_reason: str = ""
    reasons: list[str] = Field(default_factory=list)


class ComboQuote(StrictModel):
    candidate_id: str
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    currency: Literal["USD"] = "USD"
    timestamp: datetime | None = None
    source_id: str | None = None
    executable: bool = False
    warnings: list[str] = Field(default_factory=list)


class ExecutionPreview(StrictModel):
    candidate_id: str
    broker: Literal["IBKR"] = "IBKR"
    mode: Literal["preview"] = "preview"
    security_type: Literal["OPT", "BAG"]
    limit_debit_usd: float
    combo_quote: ComboQuote | None = None
    estimated_commission_usd: float | None = Field(default=None, ge=0)
    margin_what_if_usd: float | None = Field(default=None, ge=0)
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"
    blockers: list[str] = Field(default_factory=list)


class PositionDossier(StrictModel):
    dossier_id: str
    candidate_id: str
    opened_at: datetime
    initial_scenario_probabilities: dict[str, float]
    initial_distribution_source: str
    initial_decision: dict[str, Any] = Field(default_factory=dict)
    entry_quote: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    models_used: list[str] = Field(default_factory=list)
    catalyst_date: datetime | None = None
    horizon_days: int | None = Field(default=None, gt=0)
    contract_ids: list[str] = Field(default_factory=list)
    initial_spot: float = Field(gt=0)
    initial_iv: float
    initial_rate: float
    initial_greeks: dict[str, float]
    initial_regime: str
    expected_catalysts: list[str]
    invalidation_conditions: list[str]
    entry_price_usd: float
    actual_cost_usd: float
    actual_slippage_usd: float = Field(ge=0)
    exit_plan: CandidateExitPlan
    state: Literal["paper_open", "live_assisted_open"]
    human_actor: str


class PositionMonitorInput(StrictModel):
    as_of: datetime
    current_spot: float = Field(gt=0)
    market_value_usd: float = Field(ge=0)
    realized_pnl_usd: float
    current_iv: float = Field(gt=0)
    current_rate: float
    current_greeks: dict[str, float]
    current_scenario_probabilities: dict[str, float]
    thesis_invalidated: bool = False
    days_to_expiration: int = Field(ge=0)
    regime: str
    execution_impact_usd: float
    prudent_liquidation_value_usd: float | None = Field(default=None, ge=0)
    peak_prudent_liquidation_value_usd: float | None = Field(default=None, ge=0)
    expected_remaining_pnl_usd: float | None = None
    remaining_cvar_95_usd: float | None = Field(default=None, ge=0)
    liquidity_score: float | None = Field(default=None, ge=0, le=1)
    bid_ask_spread_fraction: float | None = Field(default=None, ge=0)
    data_fresh: bool = True
    data_sufficient: bool = True
    thesis_change: str = "unchanged"


class PositionMonitorReport(StrictModel):
    dossier_id: str
    as_of: datetime
    action: MonitorAction
    unrealized_pnl_usd: float
    prudent_liquidation_pnl_usd: float | None = None
    total_pnl_usd: float
    expected_remaining_pnl_usd: float | None = None
    remaining_cvar_95_usd: float | None = None
    current_greeks: dict[str, float] = Field(default_factory=dict)
    liquidity_status: str = "unknown"
    thesis_change: str = "unchanged"
    probability_changes: dict[str, float]
    greek_attribution: dict[str, float]
    iv_change: float
    execution_impact_usd: float
    regime_change: str
    thesis_market_divergence: str
    triggered_rules: list[str]
    rule_triggers: list[ExitRuleTrigger] = Field(default_factory=list)
    explanation: list[str]
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


class PositionTrajectoryFixture(StrictModel):
    fixture_id: str = Field(min_length=1)
    synthetic: Literal[True] = True
    dossier: PositionDossier
    snapshots: list[PositionMonitorInput] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_chronology(self) -> PositionTrajectoryFixture:
        timestamps = [snapshot.as_of for snapshot in self.snapshots]
        if any(timestamp < self.dossier.opened_at for timestamp in timestamps):
            raise ValueError("trajectory snapshots cannot precede the dossier opening time")
        if timestamps != sorted(timestamps) or len(set(timestamps)) != len(timestamps):
            raise ValueError("trajectory snapshots must be unique and chronological")
        return self


class PositionTrajectoryReplay(StrictModel):
    fixture_id: str
    status: Literal["FIXTURE_ONLY_REPLAY"]
    reports: list[PositionMonitorReport]
    deterministic: Literal[True] = True
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


class V11Policy(StrictModel):
    policy_id: str
    source_status: Literal["calibration_required", "experimental"]
    scenario_priors: dict[str, float]
    scenario_regime_map: dict[str, SimulationRegime]
    likelihood_rules: list[LikelihoodRule]
    family_weight_caps: dict[EvidenceFamily, float]
    event_normalization_rules: list[EventNormalizationRule] = Field(default_factory=list)
    simulation: SimulationPolicy
    covariance_windows: list[int] = Field(default_factory=lambda: [20, 60, 252])
    covariance_shrinkage: float = Field(default=0.25, ge=0, le=1)
    budget_eur: float = Field(gt=0)
    maximum_loss_eur: float = Field(gt=0)
    maximum_contracts: int = Field(gt=0)
    maximum_positions: int = Field(default=4, gt=0)
    maximum_concentration: float = Field(default=1.0, gt=0, le=1)
    minimum_liquidity_score: float = Field(default=0.0, ge=0, le=1)
    maximum_relative_spread: float = Field(default=1.0, gt=0)
    delta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0)
    gamma_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0)
    vega_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0)
    theta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0)
    allow_multiple_strategies: bool = True
    candidate_pool_size: int = Field(default=6, ge=1, le=12)
    optimizer_profiles: dict[
        Literal["prudent", "balanced", "aggressive"],
        OptimizerProfileConfig,
    ]
    exit_policy: ExitPolicyConfig
    required_series: list[str] = Field(default_factory=list)
    freshness_hours_by_domain: dict[DataDomain, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_policy(self) -> V11Policy:
        if not self.scenario_priors or abs(sum(self.scenario_priors.values()) - 1) > 1e-8:
            raise ValueError("scenario priors must exist and sum to one")
        if any(value <= 0 for value in self.scenario_priors.values()):
            raise ValueError("scenario priors must be strictly positive")
        scenarios = set(self.scenario_priors)
        if set(self.scenario_regime_map) != scenarios:
            raise ValueError("scenario_regime_map must cover every Bayesian scenario")
        for rule in self.likelihood_rules:
            if set(rule.likelihood_by_scenario) != scenarios:
                raise ValueError("each likelihood rule must cover every configured scenario")
        if self.maximum_loss_eur > self.budget_eur:
            raise ValueError("maximum loss cannot exceed budget")
        if set(self.optimizer_profiles) != {"prudent", "balanced", "aggressive"}:
            raise ValueError("all three optimizer profiles must be configured")
        if len(set(self.covariance_windows)) != len(self.covariance_windows):
            raise ValueError("covariance windows cannot be duplicated")
        if any(window < 2 for window in self.covariance_windows):
            raise ValueError("covariance windows require at least two observations")
        for lower, upper in (
            self.delta_exposure_range,
            self.gamma_exposure_range,
            self.vega_exposure_range,
            self.theta_exposure_range,
        ):
            if lower > upper:
                raise ValueError("Greek exposure ranges must be ordered")
        return self


class FeatureReadiness(StrictModel):
    feature: str
    status: FeatureStatus
    implemented: bool
    evidence: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class RunManifest(StrictModel):
    run_id: str
    profile: Literal["fast_fixture", "research", "validation", "exhaustive"]
    seed: int
    configuration_hash: str
    data_hash: str
    input_hash: str
    model_versions: dict[str, str]
    policy_version: str
    started_at: datetime
    completed_at: datetime
    stage_durations_seconds: dict[str, float]
    peak_memory_mb: float | None = Field(default=None, ge=0)
    deterministic_cache: bool
    resumed: bool = False


class MachineSummary(StrictModel):
    schema_version: str
    generated_at: datetime
    cutoff: datetime
    posture: ResearchPosture
    result_status: FeatureStatus
    calibration_status: str
    backtest_status: str
    promotion_eligible: bool
    order_capability: Literal["forbidden"] = "forbidden"
    blocking_reasons: list[str] = Field(default_factory=list)


class V11IntelligenceReport(StrictModel):
    schema_version: Literal["11.1"] = "11.1"
    report_id: str
    created_at: datetime
    ticker: str
    base_v10_report_id: str
    posture: ResearchPosture
    data_snapshot: UnifiedDataSnapshot
    event_normalization: EventNormalizationReport
    bayesian_distribution: BayesianScenarioDistribution
    offline_calibration: dict[str, Any]
    walk_forward_backtest: dict[str, Any]
    local_volatility_calibration: LocalVolatilityCalibrationReport
    covariance: DynamicCovarianceReport
    model_metrics: list[StrategyModelMetrics]
    robustness: list[CandidateRobustness]
    validation: list[CandidateValidationSummary]
    allocations: list[AllocationResult]
    stress_tests: list[StressTestResult] = Field(default_factory=list)
    exit_plans: list[CandidateExitPlan]
    execution_previews: list[ExecutionPreview]
    facts_verified: list[str]
    hypotheses_to_test: list[str]
    limitations: list[str]
    validations_required: list[str]
    readiness: list[FeatureReadiness]
    run_manifest: RunManifest
    machine_summary: MachineSummary
    order_capability: Literal["forbidden"] = "forbidden"
