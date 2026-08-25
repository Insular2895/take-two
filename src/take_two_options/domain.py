"""Typed contracts shared by the research engine."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.models import StrictModel as StrictModel
from take_two_options.trade_economics_models import (
    DividendTreatmentMode,
    ExecutionEstimateStatus,
    IntradayPrecisionStatus,
    MarginStatus,
    RiskFreeCurve,
    TradeEconomicsConfiguration,
    TradeEconomicsTicket,
)


class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> int:
        return 1 if self is PositionSide.LONG else -1


class ExerciseStyle(StrEnum):
    AMERICAN = "american"
    EUROPEAN = "european"


class FreshnessStatus(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class EvidenceStatus(StrEnum):
    VALIDATED = "validated"
    READ_ONLY_GATE = "read_only_gate"
    DRAFT_TO_VALIDATE = "draft_to_validate"
    TO_REVIEW = "to_review"
    EXTRACTED = "extracted"
    BLOCKED = "blocked"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    UNEXTRACTABLE = "unextractable"
    IMAGE_ONLY = "image_only"
    CONTRADICTED = "contradicted"
    DEPRECATED = "deprecated"

    @property
    def can_authorize_research(self) -> bool:
        return self in {EvidenceStatus.VALIDATED, EvidenceStatus.READ_ONLY_GATE}


class StrategyKind(StrEnum):
    NO_TRADE = "no_trade"
    STOCK = "stock"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    LONG_STRADDLE = "long_straddle"
    LONG_STRANGLE = "long_strangle"
    CALL_BUTTERFLY = "call_butterfly"
    PUT_BUTTERFLY = "put_butterfly"
    IRON_CONDOR = "iron_condor"
    LONG_CALL_CALENDAR = "long_call_calendar"
    CALL_DIAGONAL = "call_diagonal"
    LEAPS_CALL = "leaps_call"
    LEAPS_PUT = "leaps_put"
    PROTECTIVE_PUT = "protective_put"
    COVERED_CALL = "covered_call"
    COLLAR = "collar"
    GAMMA_SCALPING = "gamma_scalping"
    SHORT_STRADDLE = "short_straddle"
    SHORT_STRANGLE = "short_strangle"
    RATIO_SPREAD = "ratio_spread"
    RATIO_BACKSPREAD = "ratio_backspread"


class CandidateStatus(StrEnum):
    NO_TRADE = "no_trade"
    BLOCKED = "blocked"
    RESEARCH_CANDIDATE = "research_candidate"
    PAPER_CANDIDATE = "paper_candidate"
    HUMAN_REVIEW_REQUIRED = "human_review_required"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class PricingModel(StrEnum):
    BLACK_SCHOLES_EUROPEAN = "black_scholes_european"
    QUANTLIB_FD_AMERICAN = "quantlib_fd_american"


class SimulationModel(StrEnum):
    GBM = "gbm"
    MERTON_JUMP_DIFFUSION = "merton_jump_diffusion"
    HESTON_FULL_TRUNCATION = "heston_full_truncation"


class CalibrationStatus(StrEnum):
    CALIBRATED = "calibrated"
    ILLUSTRATIVE = "illustrative"
    INSUFFICIENT_DATA = "insufficient_data"
    FAILED = "failed"


class ModelReadiness(StrEnum):
    SCREEN_GRADE = "screen_grade"
    VALIDATION_PENDING = "validation_pending"
    RESEARCH_GRADE = "research_grade"


class DataFreshness(StrictModel):
    source: str = Field(min_length=1)
    as_of: datetime
    accessed_at: datetime
    status: FreshnessStatus
    is_stale: bool = False
    max_age_seconds: int | None = Field(default=None, gt=0)


class EvidenceReference(StrictModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    status: EvidenceStatus
    accessed_at: datetime
    confidence_level: Literal["low", "medium", "high"] = "medium"
    notes: str = ""
    used_for_decision: bool = True


class DividendForecast(StrictModel):
    ex_date: date
    payment_date: date | None = None
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    freshness: DataFreshness
    source: EvidenceReference

    @model_validator(mode="after")
    def validate_dates(self) -> DividendForecast:
        if self.payment_date is not None and self.payment_date < self.ex_date:
            raise ValueError("dividend payment date cannot precede ex-date")
        return self


class VolatilitySurfaceNode(StrictModel):
    expiration: datetime
    strike: float = Field(gt=0)
    option_type: OptionType
    implied_volatility: float = Field(gt=0, lt=5)


class VolatilitySurface(StrictModel):
    as_of: datetime
    freshness: DataFreshness
    source: EvidenceReference
    nodes: list[VolatilitySurfaceNode] = Field(min_length=2)


class PricingConfiguration(StrictModel):
    american_model: PricingModel = PricingModel.QUANTLIB_FD_AMERICAN
    time_grid: int = Field(default=100, ge=25, le=1000)
    price_grid: int = Field(default=100, ge=25, le=1000)


class JumpDiffusionParameters(StrictModel):
    jump_intensity: float = Field(default=0.8, ge=0)
    jump_mean: float = Field(default=-0.08)
    jump_volatility: float = Field(default=0.16, ge=0)
    diffusion_volatility: float | None = Field(default=None, gt=0)
    calibration_status: CalibrationStatus = CalibrationStatus.ILLUSTRATIVE
    source: EvidenceReference | None = None


class HestonParameters(StrictModel):
    mean_reversion: float = Field(default=2.0, gt=0)
    long_run_variance: float = Field(default=0.1225, gt=0)
    vol_of_variance: float = Field(default=0.65, gt=0)
    correlation: float = Field(default=-0.6, ge=-1, le=1)
    initial_variance: float = Field(default=0.1225, gt=0)
    calibration_status: CalibrationStatus = CalibrationStatus.ILLUSTRATIVE
    source: EvidenceReference | None = None


class SimulationConfiguration(StrictModel):
    models: list[SimulationModel] = Field(
        default_factory=lambda: [SimulationModel.GBM], min_length=1
    )
    steps: int = Field(default=120, ge=1, le=2000)
    jump: JumpDiffusionParameters = Field(default_factory=JumpDiffusionParameters)
    heston: HestonParameters = Field(default_factory=HestonParameters)


class CorporateAction(StrictModel):
    action_type: str = Field(min_length=1)
    effective_date: date
    description: str = Field(min_length=1)
    source: EvidenceReference
    handled: bool = False


class MarketEvent(StrictModel):
    event_type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    start: datetime
    end: datetime
    source: EvidenceReference
    handled: bool = False
    critical: bool = True


class UnderlyingSnapshot(StrictModel):
    ticker: str = Field(min_length=1)
    name: str = Field(min_length=1)
    exchange: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    price: float = Field(gt=0)
    timestamp: datetime
    freshness: DataFreshness
    sources: list[EvidenceReference] = Field(min_length=1)
    corporate_actions: list[CorporateAction] = Field(default_factory=list)
    events: list[MarketEvent] = Field(default_factory=list)


class FundamentalScenario(StrictModel):
    name: str = Field(min_length=1)
    direction: Literal["bullish", "neutral", "bearish"]
    target_price: float = Field(gt=0)
    probability: float = Field(ge=0, le=1)
    drivers: list[str] = Field(default_factory=list)


class FundamentalSnapshot(StrictModel):
    ticker: str = Field(min_length=1)
    as_of: datetime
    freshness: DataFreshness
    direction: Literal["bullish", "neutral", "bearish"]
    thesis: str = Field(min_length=1)
    catalyst: str = Field(min_length=1)
    catalyst_window_start: datetime
    catalyst_window_end: datetime
    invalidation: str = Field(min_length=1)
    scenarios: list[FundamentalScenario] = Field(min_length=1)
    sources: list[EvidenceReference] = Field(min_length=1)
    latest_filings: list[str] = Field(default_factory=list)
    expectations_implied: str | None = None
    valuation_method: str | None = None
    growth_assumptions: list[str] = Field(default_factory=list)
    margin_assumptions: list[str] = Field(default_factory=list)
    cash_flow_assumptions: list[str] = Field(default_factory=list)
    debt: str | None = None
    dilution: str | None = None
    buybacks: str | None = None
    risks: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scenario_probabilities(self) -> FundamentalSnapshot:
        total = sum(scenario.probability for scenario in self.scenarios)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("fundamental scenario probabilities must sum to 1")
        if self.catalyst_window_end < self.catalyst_window_start:
            raise ValueError("catalyst window end must follow its start")
        return self


class OptionContract(StrictModel):
    underlying: str = Field(min_length=1)
    con_id: int = Field(gt=0)
    local_symbol: str = Field(min_length=1)
    trading_class: str = Field(min_length=1)
    exchange: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    expiration: datetime
    strike: float = Field(gt=0)
    option_type: OptionType
    multiplier: float = Field(gt=0)
    deliverable: str = Field(min_length=1)
    exercise_style: ExerciseStyle
    settlement_cycle: str = Field(min_length=1)
    adjusted_contract: bool = False
    adjustment_understood: bool = True


class OptionQuote(StrictModel):
    contract: OptionContract
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    last: float | None = Field(default=None, ge=0)
    bid_size: int | None = Field(default=None, ge=0)
    ask_size: int | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)
    open_interest: int | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0)
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None
    timestamp: datetime
    freshness: DataFreshness
    source: EvidenceReference

    @property
    def mid(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2


class PortfolioState(StrictModel):
    as_of: datetime
    freshness: DataFreshness
    source: EvidenceReference
    currency: str = Field(min_length=3, max_length=3)
    max_loss_budget: float = Field(gt=0)
    research_share_quantity: int = Field(default=10, gt=0)
    commission_per_option_contract: float | None = Field(default=None, ge=0)
    slippage_per_option_contract: float | None = Field(default=None, ge=0)
    stock_commission: float | None = Field(default=None, ge=0)
    stock_slippage_bps: float | None = Field(default=None, ge=0)
    margin_available: float | None = Field(default=None, ge=0)
    margin_known: bool = False
    broker_margin_requirement: float | None = Field(default=None, gt=0)
    account_permissions: list[str] = Field(default_factory=list)


class StrategyLeg(StrictModel):
    instrument_type: Literal["stock", "option"]
    side: PositionSide
    quantity: int = Field(gt=0)
    option_quote: OptionQuote | None = None
    underlying_symbol: str = ""
    stock_price: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_instrument(self) -> StrategyLeg:
        if self.instrument_type == "option" and self.option_quote is None:
            raise ValueError("an option leg requires option_quote")
        if self.instrument_type == "stock" and (
            not self.underlying_symbol or self.stock_price is None
        ):
            raise ValueError("a stock leg requires underlying_symbol and stock_price")
        return self


class ExecutionEstimate(StrictModel):
    theoretical_mid: float
    executable_debit: float = Field(ge=0)
    executable_credit: float = Field(ge=0)
    fees: float = Field(ge=0)
    slippage: float = Field(ge=0)
    total_entry_cost: float
    margin_requirement: float | None = Field(default=None, ge=0)
    liquidity_score: float = Field(ge=0, le=1)
    notes: list[str] = Field(default_factory=list)
    premium_paid: float = Field(default=0.0, ge=0)
    premium_received: float = Field(default=0.0, ge=0)
    net_premium: float = 0.0
    bid_ask_cost: float = Field(default=0.0, ge=0)
    fx_conversion_cost: float | None = Field(default=None, ge=0)
    total_capital_required: float | None = Field(default=None, ge=0)
    margin_status: MarginStatus = MarginStatus.NOT_REQUIRED
    execution_status: ExecutionEstimateStatus = ExecutionEstimateStatus.INDICATIVE
    combo_execution_status: Literal["INDICATIVE", "OBSERVED_COMBO"] = "INDICATIVE"
    theoretical_mid_premium_paid: float | None = Field(default=None, ge=0)
    theoretical_mid_premium_received: float | None = Field(default=None, ge=0)
    theoretical_mid_net_premium: float | None = None
    executable_premium_paid: float | None = Field(default=None, ge=0)
    executable_premium_received: float | None = Field(default=None, ge=0)
    executable_net_premium: float | None = None
    total_entry_cash_flow: float | None = None

    @model_validator(mode="after")
    def reconcile_explicit_entry_economics(self) -> ExecutionEstimate:
        theoretical_paid = (
            self.theoretical_mid_premium_paid
            if self.theoretical_mid_premium_paid is not None
            else self.premium_paid
        )
        theoretical_received = (
            self.theoretical_mid_premium_received
            if self.theoretical_mid_premium_received is not None
            else self.premium_received
        )
        theoretical_net = theoretical_paid - theoretical_received
        theoretical_net_value = self.theoretical_mid_net_premium
        if theoretical_net_value is None:
            theoretical_net_value = theoretical_net
            object.__setattr__(self, "theoretical_mid_net_premium", theoretical_net_value)
        object.__setattr__(self, "theoretical_mid_premium_paid", theoretical_paid)
        object.__setattr__(self, "theoretical_mid_premium_received", theoretical_received)
        if abs(theoretical_net_value - theoretical_net) > 1e-8:
            raise ValueError("theoretical midpoint premiums do not reconcile")
        executable_paid = (
            self.executable_premium_paid
            if self.executable_premium_paid is not None
            else theoretical_paid + (self.bid_ask_cost if theoretical_net >= 0 else 0.0)
        )
        executable_received = (
            self.executable_premium_received
            if self.executable_premium_received is not None
            else theoretical_received - (self.bid_ask_cost if theoretical_net < 0 else 0.0)
        )
        executable_net = executable_paid - executable_received
        executable_net_value = self.executable_net_premium
        if executable_net_value is None:
            executable_net_value = executable_net
            object.__setattr__(self, "executable_net_premium", executable_net_value)
        object.__setattr__(self, "executable_premium_paid", executable_paid)
        object.__setattr__(self, "executable_premium_received", executable_received)
        if abs(executable_net_value - executable_net) > 1e-8:
            raise ValueError("executable premiums do not reconcile")
        if abs(executable_net - theoretical_net - self.bid_ask_cost) > 1e-8:
            raise ValueError("entry bid/ask cost does not reconcile")
        known_cash_flow = (
            executable_net + self.slippage + self.fees + (self.fx_conversion_cost or 0.0)
        )
        total_entry_cash_flow = self.total_entry_cash_flow
        if total_entry_cash_flow is None:
            total_entry_cash_flow = self.total_entry_cost
            object.__setattr__(self, "total_entry_cash_flow", total_entry_cash_flow)
        if abs(total_entry_cash_flow - known_cash_flow) > 1e-8:
            raise ValueError("total entry cash flow does not reconcile")
        if abs(self.total_entry_cost - total_entry_cash_flow) > 1e-8:
            raise ValueError("deprecated total_entry_cost must equal total_entry_cash_flow")
        return self


class PayoffPoint(StrictModel):
    spot: float = Field(ge=0)
    pnl: float


class RiskMetrics(StrictModel):
    max_gain: float | None = Field(default=None, ge=0)
    max_loss: float | None = Field(default=None, ge=0)
    break_even_points: list[float] = Field(default_factory=list)
    net_delta: float
    net_gamma: float
    net_theta: float
    net_vega: float
    net_rho: float
    debit_credit_mid: float
    debit_credit_executable: float
    unbounded_risk: bool
    payoff_points: list[PayoffPoint] = Field(default_factory=list)


class RuleEvaluation(StrictModel):
    rule_id: str = Field(min_length=1)
    status: EvidenceStatus
    passed: bool
    severity: Severity
    message: str = Field(min_length=1)
    blocks: bool = False
    evidence_ids: list[str] = Field(default_factory=list)


class ScenarioResult(StrictModel):
    name: str = Field(min_length=1)
    spot: float = Field(ge=0)
    days_forward: int = Field(ge=0)
    iv_shift: float
    pnl: float
    estimated_value: float
    assumptions: list[str] = Field(default_factory=list)
    attribution: ScenarioAttribution | None = None


class ScenarioAttribution(StrictModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    execution_costs: float
    residual: float


class AmericanPricingResult(StrictModel):
    contract_symbol: str = Field(min_length=1)
    valuation_time: datetime
    model: PricingModel
    price: float = Field(ge=0)
    european_benchmark: float = Field(ge=0)
    analytic_european_benchmark_exact: float | None = Field(default=None, ge=0)
    early_exercise_premium: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    dividend_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    exact_time_to_expiry_years: float | None = Field(default=None, ge=0)
    intraday_precision_status: IntradayPrecisionStatus = (
        IntradayPrecisionStatus.APPROXIMATED_DATE_ENGINE
    )
    intraday_precision_warning: str | None = None


class ExerciseRiskAssessment(StrictModel):
    contract_symbol: str = Field(min_length=1)
    side: PositionSide
    assignment_risk: RiskLevel
    pin_risk: RiskLevel
    intrinsic_value: float = Field(ge=0)
    extrinsic_value: float = Field(ge=0)
    days_to_expiry: int = Field(ge=0)
    next_ex_dividend_date: date | None = None
    reasons: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    early_exercise_risk: RiskLevel = RiskLevel.UNKNOWN
    adjusted_contract: bool = False


class SurfaceDiagnostics(StrictModel):
    available: bool
    expiry_count: int = Field(ge=0)
    strike_count: int = Field(ge=0)
    interpolated_contracts: int = Field(ge=0)
    extrapolated_contracts: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class ScoreBreakdown(StrictModel):
    thesis_fit: float = Field(ge=0, le=1)
    catalyst_coverage: float = Field(ge=0, le=1)
    expected_payoff: float = Field(ge=0, le=1)
    payoff_quality: float = Field(ge=0, le=1)
    max_loss_quality: float = Field(ge=0, le=1)
    assumption_sensitivity: float = Field(ge=0, le=1)
    liquidity: float = Field(ge=0, le=1)
    cost_quality: float = Field(ge=0, le=1)
    complexity: float = Field(ge=0, le=1)
    assignment_early_exercise: float = Field(ge=0, le=1)
    iv_rv_context: float = Field(ge=0, le=1)
    skew_term_structure: float = Field(ge=0, le=1)
    margin: float = Field(ge=0, le=1)
    carry: float = Field(ge=0, le=1)
    adverse_robustness: float = Field(ge=0, le=1)
    data_confidence: float = Field(ge=0, le=1)
    total: float = Field(ge=0, le=1)


class StrategyCandidate(StrictModel):
    id: str = Field(min_length=1)
    kind: StrategyKind
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    legs: list[StrategyLeg] = Field(default_factory=list)
    status: CandidateStatus = CandidateStatus.RESEARCH_CANDIDATE
    evidence: list[EvidenceReference] = Field(default_factory=list)
    rule_evaluations: list[RuleEvaluation] = Field(default_factory=list)
    risk_metrics: RiskMetrics | None = None
    execution_estimate: ExecutionEstimate | None = None
    scenarios: list[ScenarioResult] = Field(default_factory=list)
    pricing_results: list[AmericanPricingResult] = Field(default_factory=list)
    exercise_risks: list[ExerciseRiskAssessment] = Field(default_factory=list)
    score: ScoreBreakdown | None = None
    veto_reasons: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    human_validation_required: bool = False
    trade_economics: TradeEconomicsTicket | None = None


class MarketDataBundle(StrictModel):
    underlying: UnderlyingSnapshot
    fundamental: FundamentalSnapshot
    portfolio: PortfolioState
    option_quotes: list[OptionQuote]
    risk_free_rate: float
    risk_free_rate_freshness: DataFreshness
    risk_free_rate_source: EvidenceReference
    analysis_timestamp: datetime
    monte_carlo_paths: int = Field(default=512, ge=32)
    monte_carlo_seed: int = 42
    monte_carlo_horizon_days: int = Field(default=120, gt=0)
    annualized_volatility: float = Field(default=0.35, gt=0)
    volatility_freshness: DataFreshness
    volatility_source: EvidenceReference
    continuous_dividend_yield: float = Field(default=0.0, ge=0, lt=1)
    dividend_treatment_mode: DividendTreatmentMode = DividendTreatmentMode.DISCRETE_CASH
    dividend_overlap_explanation: str | None = None
    dividend_yield_freshness: DataFreshness | None = None
    dividend_yield_source: EvidenceReference | None = None
    dividends: list[DividendForecast] = Field(default_factory=list)
    volatility_surface: VolatilitySurface | None = None
    risk_free_curve: RiskFreeCurve | None = None
    pricing: PricingConfiguration = Field(default_factory=PricingConfiguration)
    simulation: SimulationConfiguration = Field(default_factory=SimulationConfiguration)
    trade_economics: TradeEconomicsConfiguration = Field(
        default_factory=TradeEconomicsConfiguration
    )


class DecisionReport(StrictModel):
    report_id: str = Field(min_length=1)
    created_at: datetime
    decision_posture: Literal["read_only_research"] = "read_only_research"
    bundle: MarketDataBundle
    candidates: list[StrategyCandidate]
    ranked_candidate_ids: list[str]
    pareto_candidate_ids: list[str]
    global_warnings: list[str] = Field(default_factory=list)
    data_issues: list[str] = Field(default_factory=list)
    model_readiness: ModelReadiness = ModelReadiness.SCREEN_GRADE
    model_limitations: list[str] = Field(default_factory=list)
    surface_diagnostics: SurfaceDiagnostics | None = None
