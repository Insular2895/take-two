"""Strict, auditable contracts for the modular V11 intelligence layer."""

from __future__ import annotations

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


class NormalizedEventType(StrEnum):
    GTA_DELAY_CONFIRMED = "EVENT_GTA_DELAY_CONFIRMED"
    RELEASE_DATE_MAINTAINED = "EVENT_RELEASE_DATE_MAINTAINED"
    GUIDANCE_UP = "EVENT_GUIDANCE_UP"
    GUIDANCE_DOWN = "EVENT_GUIDANCE_DOWN"
    INSIDER_BUY = "EVENT_INSIDER_BUY"
    SEARCH_INTEREST_UP = "EVENT_SEARCH_INTEREST_UP"
    IV_SPIKE = "EVENT_IV_SPIKE"
    OPTIONS_FLOW_BULLISH = "EVENT_OPTIONS_FLOW_BULLISH"
    EARNINGS_BEAT = "EVENT_EARNINGS_BEAT"
    EARNINGS_MISS = "EVENT_EARNINGS_MISS"
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
    KEEP = "conserver"
    WATCH = "surveiller"
    REDUCE = "reduire"
    EXIT = "sortir"
    THESIS_INVALIDATED = "these_invalidee"


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
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectorStatus(StrictModel):
    connector_id: str
    state: ConnectorState
    checked_at: datetime
    observations: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class UnifiedDataSnapshot(StrictModel):
    schema_version: Literal["11.0"] = "11.0"
    snapshot_id: str
    ticker: str
    as_of: datetime
    sources: list[SourceProvenance]
    observations: list[UnifiedObservation]
    connectors: list[ConnectorStatus]
    missing_required_series: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class NormalizedEvidenceEvent(StrictModel):
    event_id: str
    event_type: NormalizedEventType
    family: EvidenceFamily
    occurred_at: datetime
    observed_at: datetime
    canonical_fact_id: str = Field(
        min_length=1,
        description="Stable deduplication key shared by reports of the same underlying fact.",
    )
    source_ids: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    direction: Literal["supports", "contradicts", "neutral"] = "supports"
    contradictory_source_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class LikelihoodRule(StrictModel):
    event_type: NormalizedEventType
    family: EvidenceFamily
    likelihood_by_scenario: dict[str, float]
    base_weight: float = Field(default=1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_likelihoods(self) -> LikelihoodRule:
        if not self.likelihood_by_scenario:
            raise ValueError("likelihood rule requires scenarios")
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
    requested_weight: float = Field(ge=0, le=1)
    effective_weight: float = Field(ge=0, le=1)
    posterior: dict[str, float]
    confidence: float = Field(ge=0, le=1)
    deduplicated: bool
    family_cap_applied: bool
    contradictory_source_ids: list[str] = Field(default_factory=list)


class BayesianScenarioDistribution(StrictModel):
    scenario_probabilities: dict[str, float]
    updates: list[BayesianUpdateRecord]
    family_weight_used: dict[EvidenceFamily, float]
    ignored_event_ids: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_distribution(self) -> BayesianScenarioDistribution:
        if not self.scenario_probabilities:
            raise ValueError("Bayesian distribution requires scenarios")
        if abs(sum(self.scenario_probabilities.values()) - 1) > 1e-8:
            raise ValueError("posterior scenario probabilities must sum to one")
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
    human_review_required: Literal[True] = True


class StrategyModelMetrics(StrictModel):
    candidate_id: str
    model: StochasticModel
    regime: SimulationRegime
    paths: int = Field(gt=0)
    expected_pnl_usd: float
    median_pnl_usd: float
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
    robustness_score: float = Field(ge=0, le=100)
    model_risk_flags: list[str] = Field(default_factory=list)


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


class PositionMonitorReport(StrictModel):
    dossier_id: str
    as_of: datetime
    action: MonitorAction
    unrealized_pnl_usd: float
    total_pnl_usd: float
    probability_changes: dict[str, float]
    greek_attribution: dict[str, float]
    iv_change: float
    execution_impact_usd: float
    regime_change: str
    thesis_market_divergence: str
    triggered_rules: list[str]
    explanation: list[str]
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"


class V11Policy(StrictModel):
    policy_id: str
    source_status: Literal["calibration_required", "experimental"]
    scenario_priors: dict[str, float]
    scenario_regime_map: dict[str, SimulationRegime]
    likelihood_rules: list[LikelihoodRule]
    family_weight_caps: dict[EvidenceFamily, float]
    simulation: SimulationPolicy
    covariance_windows: list[int] = Field(default_factory=lambda: [20, 60, 252])
    covariance_shrinkage: float = Field(default=0.25, ge=0, le=1)
    budget_eur: float = Field(gt=0)
    maximum_loss_eur: float = Field(gt=0)
    maximum_contracts: int = Field(gt=0)
    candidate_pool_size: int = Field(default=6, ge=1, le=12)
    optimizer_profiles: dict[
        Literal["prudent", "balanced", "aggressive"],
        OptimizerProfileConfig,
    ]
    exit_policy: ExitPolicyConfig
    required_series: list[str] = Field(default_factory=list)

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
        return self


class V11IntelligenceReport(StrictModel):
    schema_version: Literal["11.0"] = "11.0"
    report_id: str
    created_at: datetime
    ticker: str
    base_v10_report_id: str
    posture: ResearchPosture
    data_snapshot: UnifiedDataSnapshot
    bayesian_distribution: BayesianScenarioDistribution
    local_volatility_calibration: LocalVolatilityCalibrationReport
    covariance: DynamicCovarianceReport
    model_metrics: list[StrategyModelMetrics]
    robustness: list[CandidateRobustness]
    validation: list[CandidateValidationSummary]
    allocations: list[AllocationResult]
    exit_plans: list[CandidateExitPlan]
    execution_previews: list[ExecutionPreview]
    facts_verified: list[str]
    hypotheses_to_test: list[str]
    limitations: list[str]
    validations_required: list[str]
    order_capability: Literal["forbidden"] = "forbidden"
