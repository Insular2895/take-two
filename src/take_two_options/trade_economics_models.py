"""Versioned, typed contracts for M0 trade economics and diagnostics."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.models import StrictModel


class AnalysisMode(StrEnum):
    SCREEN = "screen"
    DEEP_ANALYSIS = "deep_analysis"


class GreekConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNRELIABLE = "UNRELIABLE"


class IntradayPrecisionStatus(StrEnum):
    EXACT = "EXACT"
    APPROXIMATED_DATE_ENGINE = "APPROXIMATED_DATE_ENGINE"
    INSUFFICIENT_NEAR_EXPIRY = "INSUFFICIENT_NEAR_EXPIRY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DividendTreatmentMode(StrEnum):
    NONE = "NONE"
    CONTINUOUS_YIELD = "CONTINUOUS_YIELD"
    DISCRETE_CASH = "DISCRETE_CASH"
    HYBRID_EXPLICIT_NON_OVERLAPPING = "HYBRID_EXPLICIT_NON_OVERLAPPING"


class VolatilityScenarioType(StrEnum):
    CONSTANT_LEG_IV = "CONSTANT_LEG_IV"
    PARALLEL_ABSOLUTE_VOL_SHIFT = "PARALLEL_ABSOLUTE_VOL_SHIFT"
    RELATIVE_VOL_MULTIPLIER = "RELATIVE_VOL_MULTIPLIER"
    SKEW_STEEPENING = "SKEW_STEEPENING"
    SKEW_FLATTENING = "SKEW_FLATTENING"
    SHORT_END_CRUSH = "SHORT_END_CRUSH"
    LONG_END_STABLE = "LONG_END_STABLE"
    SHORT_END_EXPANSION = "SHORT_END_EXPANSION"
    EVENT_IV_CRUSH = "EVENT_IV_CRUSH"
    SPOT_UP_IV_DOWN = "SPOT_UP_IV_DOWN"
    SPOT_DOWN_IV_UP = "SPOT_DOWN_IV_UP"


class VolatilityScenarioStatus(StrEnum):
    CONFIGURED_STRESS = "CONFIGURED_STRESS"
    LEG_LEVEL_STRESS_ONLY = "LEG_LEVEL_STRESS_ONLY"
    SURFACE_STRESS_VALID = "SURFACE_STRESS_VALID"
    SURFACE_STRESS_INVALID = "SURFACE_STRESS_INVALID"


class EventScenarioStatus(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    OPTION_EXPIRES_BEFORE_EVENT = "OPTION_EXPIRES_BEFORE_EVENT"
    EVENT_NOT_OCCURRED_YET = "EVENT_NOT_OCCURRED_YET"
    EVENT_CRUSH_APPLIED = "EVENT_CRUSH_APPLIED"
    CONFIGURED_GENERIC_EVENT_STRESS_NO_DATE = "CONFIGURED_GENERIC_EVENT_STRESS_NO_DATE"
    MIXED_LEG_EVENT_EFFECTS = "MIXED_LEG_EVENT_EFFECTS"


class RateScenarioType(StrEnum):
    BASE_CURVE = "BASE_CURVE"
    PARALLEL_UP = "PARALLEL_UP"
    PARALLEL_DOWN = "PARALLEL_DOWN"
    STEEPENING = "STEEPENING"
    FLATTENING = "FLATTENING"


class MarginStatus(StrEnum):
    KNOWN_BROKER = "KNOWN_BROKER"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"
    NOT_REQUIRED = "NOT_REQUIRED"
    BLOCKED = "BLOCKED"


class ExecutionEstimateStatus(StrEnum):
    INDICATIVE = "INDICATIVE"
    ESTIMATED_CONFIGURED_EXECUTION_MODEL = "ESTIMATED_CONFIGURED_EXECUTION_MODEL"
    OBSERVED = "OBSERVED"
    BLOCKED_MISSING_EXECUTION_DATA = "BLOCKED_MISSING_EXECUTION_DATA"


class FXHandlingMode(StrEnum):
    CONVERT_AT_ENTRY_AND_EXIT = "CONVERT_AT_ENTRY_AND_EXIT"
    MAINTAIN_UNDERLYING_CURRENCY_CASH = "MAINTAIN_UNDERLYING_CURRENCY_CASH"
    ACCOUNT_BASE_TRANSLATION_ONLY = "ACCOUNT_BASE_TRANSLATION_ONLY"
    UNKNOWN = "UNKNOWN"


class TouchDirection(StrEnum):
    UPPER = "UPPER"
    LOWER = "LOWER"


class ProbabilityStatus(StrEnum):
    MODEL_IMPLIED = "MODEL_IMPLIED"
    EMPIRICALLY_CALIBRATED = "EMPIRICALLY_CALIBRATED"
    PAPER_OBSERVED = "PAPER_OBSERVED"
    PROBABILITY_MODEL_NOT_AVAILABLE = "PROBABILITY_MODEL_NOT_AVAILABLE"
    PROBABILITY_MODEL_NOT_PROMOTED = "PROBABILITY_MODEL_NOT_PROMOTED"


class DistributionAvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ProbabilityPnLValuationRule(StrEnum):
    CONSTANT_LEG_IV_PATH_VALUATION = "CONSTANT_LEG_IV_PATH_VALUATION"


class ExitPath(StrEnum):
    CLOSE_BEFORE_EXPIRY = "CLOSE_BEFORE_EXPIRY"
    HOLD_TO_EXPIRY = "HOLD_TO_EXPIRY"
    EXERCISE_ASSIGN_SETTLE = "EXERCISE_ASSIGN_SETTLE"
    MIXED_EXPIRY_MANAGED_CLOSE = "MIXED_EXPIRY_MANAGED_CLOSE"


class MixedExpiryLifecyclePolicy(StrEnum):
    CLOSE_BEFORE_FIRST_EXPIRY = "CLOSE_BEFORE_FIRST_EXPIRY"


class FiveScoreScope(StrEnum):
    CANDIDATE = "CANDIDATE"
    RUN_GLOBAL = "RUN_GLOBAL"
    UNAVAILABLE = "UNAVAILABLE"


class TargetArrivalStatus(StrEnum):
    LATEST_PROFITABLE_ARRIVAL = "LATEST_PROFITABLE_ARRIVAL"
    PROFITABLE_THROUGH_EXPIRY = "PROFITABLE_THROUGH_EXPIRY"
    NEVER_BREAKEVEN_AT_THIS_TARGET = "NEVER_BREAKEVEN_AT_THIS_TARGET"
    NON_MONOTONIC_TIME_RELATION = "NON_MONOTONIC_TIME_RELATION"
    TARGET_TOO_LATE_UNDER_MIXED_EXPIRY_POLICY = "TARGET_TOO_LATE_UNDER_MIXED_EXPIRY_POLICY"


class TradeIntensityCategory(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class RiskFreeCurveNode(StrictModel):
    maturity_days: int = Field(gt=0)
    annual_rate: float


class RiskFreeCurve(StrictModel):
    curve_id: str = Field(min_length=1)
    as_of: datetime
    currency: str = Field(min_length=3, max_length=3)
    source_instrument: str = Field(min_length=1)
    quote_type: Literal["par_yield", "zero_rate", "discount_factor"]
    compounding: str = Field(min_length=1)
    day_count: str = Field(min_length=1)
    bootstrap_method: str | None = None
    interpolation_method: str = Field(min_length=1)
    nodes: list[RiskFreeCurveNode] = Field(min_length=1)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_nodes(self) -> RiskFreeCurve:
        maturities = [node.maturity_days for node in self.nodes]
        if maturities != sorted(set(maturities)):
            raise ValueError("risk-free curve maturities must be unique and sorted")
        if self.quote_type == "zero_rate" and not self.bootstrap_method:
            raise ValueError("a zero-rate curve requires an explicit bootstrap method")
        return self

    def rate_for(self, maturity_days: int) -> float:
        """Linearly interpolate the declared quote type without relabeling it."""
        if maturity_days <= 0:
            raise ValueError("maturity_days must be positive")
        if maturity_days <= self.nodes[0].maturity_days:
            return self.nodes[0].annual_rate
        if maturity_days >= self.nodes[-1].maturity_days:
            return self.nodes[-1].annual_rate
        for left, right in zip(self.nodes, self.nodes[1:], strict=False):
            if left.maturity_days <= maturity_days <= right.maturity_days:
                weight = (maturity_days - left.maturity_days) / (
                    right.maturity_days - left.maturity_days
                )
                return left.annual_rate + weight * (right.annual_rate - left.annual_rate)
        raise RuntimeError("risk-free curve interpolation failed")


class VolatilityScenarioParameters(StrictModel):
    parallel_shift_vol_points: float | None = None
    relative_multiplier: float | None = Field(default=None, gt=0)
    skew_slope_vol_points: float | None = None
    short_end_max_days: int | None = Field(default=None, gt=0)
    long_end_min_days: int | None = Field(default=None, gt=0)
    front_expiry_shift_vol_points: float | None = None
    mid_expiry_shift_vol_points: float | None = None
    back_expiry_shift_vol_points: float | None = None
    spot_multiplier: float | None = Field(default=None, gt=0)
    relative_to_event_date: date | None = None


class VolatilityScenario(StrictModel):
    name: str = Field(min_length=1)
    scenario_type: VolatilityScenarioType
    unit: Literal["vol_points", "multiplier", "mixed", "none"]
    parameters: VolatilityScenarioParameters = Field(default_factory=VolatilityScenarioParameters)
    source: str = Field(min_length=1)
    status: VolatilityScenarioStatus = VolatilityScenarioStatus.CONFIGURED_STRESS
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_event_policy(self) -> VolatilityScenario:
        if self.scenario_type is not VolatilityScenarioType.EVENT_IV_CRUSH:
            return self
        parameters = self.parameters
        required = (
            parameters.short_end_max_days,
            parameters.long_end_min_days,
            parameters.front_expiry_shift_vol_points,
            parameters.mid_expiry_shift_vol_points,
            parameters.back_expiry_shift_vol_points,
        )
        if any(value is None for value in required):
            raise ValueError("EVENT_IV_CRUSH requires explicit tenor boundaries and shifts")
        if parameters.long_end_min_days <= parameters.short_end_max_days:  # type: ignore[operator]
            raise ValueError("event long-end boundary must follow short-end boundary")
        return self


class SpotGridConfiguration(StrictModel):
    mode: Literal["spot_multipliers", "absolute_spots"] = "spot_multipliers"
    values: list[float] = Field(default_factory=lambda: [0.70, 0.85, 1.0, 1.15, 1.30], min_length=2)

    @model_validator(mode="after")
    def validate_values(self) -> SpotGridConfiguration:
        if self.values != sorted(set(self.values)) or any(value <= 0 for value in self.values):
            raise ValueError("spot-grid values must be positive, unique, and sorted")
        return self


class RateScenario(StrictModel):
    name: str = Field(min_length=1)
    scenario_type: RateScenarioType
    short_end_shift_basis_points: float = 0.0
    long_end_shift_basis_points: float = 0.0
    short_end_max_days: int = Field(default=90, gt=0)
    long_end_min_days: int = Field(default=730, gt=0)
    source: str = Field(min_length=1)
    status: Literal["CONFIGURED_STRESS"] = "CONFIGURED_STRESS"
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_curve_boundaries(self) -> RateScenario:
        if self.long_end_min_days <= self.short_end_max_days:
            raise ValueError("long-end rate boundary must follow short-end boundary")
        if self.scenario_type is RateScenarioType.BASE_CURVE and (
            self.short_end_shift_basis_points != 0 or self.long_end_shift_basis_points != 0
        ):
            raise ValueError("BASE_CURVE cannot carry a rate shift")
        return self


class TradeEconomicsDisplayPolicy(StrictModel):
    show_raw_greeks: Literal[True] = True
    show_numerical_confidence: Literal[True] = True
    show_scenario_assumptions: Literal[True] = True


class AdvancedGreekPolicy(StrictModel):
    enabled: Literal[True] = True
    display_speed: bool = True
    display_color: bool = True


class GreekBumpConfiguration(StrictModel):
    spot_relative_bumps: list[float] = Field(
        default_factory=lambda: [0.0025, 0.005, 0.01], min_length=2
    )
    minimum_spot_bump: float = Field(default=0.01, gt=0)
    volatility_bumps_vol_points: list[float] = Field(
        default_factory=lambda: [0.5, 1.0, 2.0], min_length=2
    )
    rate_bumps_basis_points: list[float] = Field(default_factory=lambda: [10.0, 25.0], min_length=2)
    time_bump_calendar_days: int = Field(default=1, gt=0)
    grid_levels: list[int] = Field(default_factory=lambda: [100, 200], min_length=2)

    @model_validator(mode="after")
    def validate_bumps(self) -> GreekBumpConfiguration:
        for values, label in (
            (self.spot_relative_bumps, "spot"),
            (self.volatility_bumps_vol_points, "volatility"),
            (self.rate_bumps_basis_points, "rate"),
            (self.grid_levels, "grid"),
        ):
            if values != sorted(set(values)) or any(value <= 0 for value in values):
                raise ValueError(f"{label} bumps/levels must be positive, unique, and sorted")
        return self


class NumericalToleranceConfiguration(StrictModel):
    greek_high_relative_dispersion: float = Field(default=0.01, ge=0)
    greek_medium_relative_dispersion: float = Field(default=0.05, ge=0)
    greek_low_relative_dispersion: float = Field(default=0.20, ge=0)
    greek_absolute_scale_floor: float = Field(default=1e-8, gt=0)
    price_grid_tolerance: float = Field(default=0.02, ge=0)
    reconciliation_tolerance: float = Field(default=1e-5, gt=0)

    @model_validator(mode="after")
    def validate_dispersion_order(self) -> NumericalToleranceConfiguration:
        if not (
            self.greek_high_relative_dispersion
            <= self.greek_medium_relative_dispersion
            <= self.greek_low_relative_dispersion
        ):
            raise ValueError("Greek dispersion thresholds must be ordered")
        return self


class ExitCostModelConfiguration(StrictModel):
    spread_cost_multiplier: float = Field(default=1.0, ge=0)
    slippage_cost_multiplier: float = Field(default=1.0, ge=0)
    closing_commission_multiplier: float = Field(default=1.0, ge=0)
    fx_exit_cost_bps: float | None = Field(default=None, ge=0)
    assignment_or_exercise_cost: float | None = Field(default=None, ge=0)
    exercise_cost: float | None = Field(default=None, ge=0)
    assignment_cost: float | None = Field(default=None, ge=0)
    settlement_cost: float | None = Field(default=None, ge=0)
    status: ExecutionEstimateStatus = ExecutionEstimateStatus.ESTIMATED_CONFIGURED_EXECUTION_MODEL


class BreakevenSolverConfiguration(StrictModel):
    minimum_spot_multiplier: float = Field(default=0.0, ge=0)
    maximum_spot_multiplier: float = Field(default=3.0, gt=0)
    grid_points: int = Field(default=401, ge=51, le=5001)
    root_tolerance: float = Field(default=1e-5, gt=0)
    pnl_tolerance: float = Field(default=1e-4, gt=0)
    maximum_iterations: int = Field(default=100, gt=0)


class TradeIntensityThresholds(StrictModel):
    high_effective_leverage: float = Field(default=5.0, gt=0)
    extreme_effective_leverage: float = Field(default=10.0, gt=0)
    high_flat_spot_30d_loss_fraction: float = Field(default=0.20, gt=0)
    extreme_flat_spot_30d_loss_fraction: float = Field(default=0.40, gt=0)
    high_round_trip_cost_fraction: float = Field(default=0.08, gt=0)
    extreme_round_trip_cost_fraction: float = Field(default=0.15, gt=0)


def _default_volatility_scenarios() -> list[VolatilityScenario]:
    return [
        VolatilityScenario(
            name="base_constant_leg_iv",
            scenario_type=VolatilityScenarioType.CONSTANT_LEG_IV,
            unit="none",
            source="trade_economics_policy_v1",
            assumptions=["Each option leg retains its own current implied volatility."],
        ),
        VolatilityScenario(
            name="configured_iv_crush",
            scenario_type=VolatilityScenarioType.PARALLEL_ABSOLUTE_VOL_SHIFT,
            unit="vol_points",
            parameters=VolatilityScenarioParameters(parallel_shift_vol_points=-10.0),
            source="trade_economics_policy_v1",
            assumptions=["Configured stress; not a calibrated forecast."],
        ),
        VolatilityScenario(
            name="configured_iv_expansion",
            scenario_type=VolatilityScenarioType.PARALLEL_ABSOLUTE_VOL_SHIFT,
            unit="vol_points",
            parameters=VolatilityScenarioParameters(parallel_shift_vol_points=10.0),
            source="trade_economics_policy_v1",
            assumptions=["Configured stress; not a calibrated forecast."],
        ),
    ]


def _default_rate_scenarios() -> list[RateScenario]:
    source = "trade_economics_policy_v1"
    return [
        RateScenario(
            name="base_curve",
            scenario_type=RateScenarioType.BASE_CURVE,
            source=source,
        ),
        RateScenario(
            name="parallel_up",
            scenario_type=RateScenarioType.PARALLEL_UP,
            short_end_shift_basis_points=100.0,
            long_end_shift_basis_points=100.0,
            source=source,
            assumptions=["Configured +100 bp curve stress; not a rate forecast."],
        ),
        RateScenario(
            name="parallel_down",
            scenario_type=RateScenarioType.PARALLEL_DOWN,
            short_end_shift_basis_points=-100.0,
            long_end_shift_basis_points=-100.0,
            source=source,
            assumptions=["Configured -100 bp curve stress; not a rate forecast."],
        ),
        RateScenario(
            name="steepening",
            scenario_type=RateScenarioType.STEEPENING,
            short_end_shift_basis_points=-50.0,
            long_end_shift_basis_points=50.0,
            source=source,
            assumptions=["Configured maturity-dependent curve stress."],
        ),
        RateScenario(
            name="flattening",
            scenario_type=RateScenarioType.FLATTENING,
            short_end_shift_basis_points=50.0,
            long_end_shift_basis_points=-50.0,
            source=source,
            assumptions=["Configured maturity-dependent curve stress."],
        ),
    ]


class TradeEconomicsConfiguration(StrictModel):
    schema_version: Literal["1.0", "1.1"] = "1.1"
    analysis_mode: AnalysisMode = AnalysisMode.SCREEN
    deep_analysis_candidate_limit: int = Field(default=3, gt=0, le=20)
    time_decay_horizons_days: list[int] = Field(
        default_factory=lambda: [1, 7, 30, 60, 90], min_length=1
    )
    scenario_horizons_days: list[int] = Field(default_factory=lambda: [7, 30, 60, 90], min_length=1)
    spot_grid: SpotGridConfiguration = Field(default_factory=SpotGridConfiguration)
    target_spots: list[float] = Field(default_factory=list)
    volatility_scenarios: list[VolatilityScenario] = Field(
        default_factory=_default_volatility_scenarios, min_length=3
    )
    greek_bumps: GreekBumpConfiguration = Field(default_factory=GreekBumpConfiguration)
    numerical_tolerances: NumericalToleranceConfiguration = Field(
        default_factory=NumericalToleranceConfiguration
    )
    rate_stresses: list[RateScenario] = Field(default_factory=_default_rate_scenarios, min_length=5)
    fx_mode: FXHandlingMode = FXHandlingMode.UNKNOWN
    entry_fx_rate_usd_per_base: float | None = Field(default=None, gt=0)
    scenario_fx_rate_usd_per_base: float | None = Field(default=None, gt=0)
    exit_cost_model: ExitCostModelConfiguration = Field(default_factory=ExitCostModelConfiguration)
    mixed_expiry_lifecycle_policy: MixedExpiryLifecyclePolicy = (
        MixedExpiryLifecyclePolicy.CLOSE_BEFORE_FIRST_EXPIRY
    )
    mixed_expiry_close_buffer_calendar_days: int = Field(default=1, ge=0)
    breakeven_solver: BreakevenSolverConfiguration = Field(
        default_factory=BreakevenSolverConfiguration
    )
    touch_targets: list[float] = Field(default_factory=list)
    near_expiry_threshold_hours: float = Field(default=48.0, gt=0)
    display_policy: TradeEconomicsDisplayPolicy = Field(default_factory=TradeEconomicsDisplayPolicy)
    advanced_greeks: AdvancedGreekPolicy = Field(default_factory=AdvancedGreekPolicy)
    leverage_denominator_floor: float = Field(default=1.0, gt=0)
    intensity_thresholds: TradeIntensityThresholds = Field(default_factory=TradeIntensityThresholds)

    @model_validator(mode="after")
    def validate_policy_axes(self) -> TradeEconomicsConfiguration:
        for values, label in (
            (self.time_decay_horizons_days, "time-decay horizons"),
            (self.scenario_horizons_days, "scenario horizons"),
        ):
            if values != sorted(set(values)) or any(value <= 0 for value in values):
                raise ValueError(f"{label} must be positive, unique, and sorted")
        required_rate_scenarios = {
            RateScenarioType.BASE_CURVE,
            RateScenarioType.PARALLEL_UP,
            RateScenarioType.PARALLEL_DOWN,
            RateScenarioType.STEEPENING,
            RateScenarioType.FLATTENING,
        }
        if not required_rate_scenarios <= {
            scenario.scenario_type for scenario in self.rate_stresses
        }:
            raise ValueError("rate stresses must include base/up/down/steepening/flattening")
        if self.fx_mode is not FXHandlingMode.UNKNOWN and (
            self.entry_fx_rate_usd_per_base is None or self.scenario_fx_rate_usd_per_base is None
        ):
            raise ValueError("known FX handling modes require entry and scenario FX rates")
        return self


class GreekConfidence(StrictModel):
    greek: str = Field(min_length=1)
    estimate: float
    method: str = Field(min_length=1)
    primary_bump: float
    alternate_bumps: list[float]
    grid_levels: list[int]
    estimate_dispersion: float = Field(ge=0)
    relative_dispersion: float = Field(ge=0)
    benchmark_difference: float | None = Field(default=None, ge=0)
    confidence_level: GreekConfidenceLevel
    warnings: list[str] = Field(default_factory=list)


class GreekMeasure(StrictModel):
    value: float
    raw_value: float
    normalized_value: float
    unit: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    multiplier: float = Field(gt=0)
    position_sign: int = Field(ge=-1, le=1)
    model: str = Field(min_length=1)
    source: str = Field(min_length=1)
    timestamp: datetime
    bump_size: float
    confidence: GreekConfidenceLevel
    calculation_method: str = Field(min_length=1)
    provider_raw_value: float | None = None
    provider_convention: str | None = None
    normalized_internal_value: float


class AdvancedGreeks(StrictModel):
    delta: GreekMeasure
    gamma: GreekMeasure
    theta: GreekMeasure
    vega: GreekMeasure
    rho: GreekMeasure
    vanna: GreekMeasure
    vomma: GreekMeasure
    charm_delta_drift_1_calendar_day: GreekMeasure
    veta_vega_drift_1_calendar_day: GreekMeasure
    speed: GreekMeasure | None = None
    color_gamma_drift_1_calendar_day: GreekMeasure | None = None
    confidence: list[GreekConfidence] = Field(min_length=7)
    conventions: list[str] = Field(default_factory=list)


class LeverageDiagnostics(StrictModel):
    capital_at_risk: float | None = Field(default=None, gt=0)
    capital_status: str = Field(min_length=1)
    lambda_value_elasticity: float | None = None
    delta_notional_leverage: float | None = Field(default=None, ge=0)
    gross_delta_leverage: float | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)


class TimeDecayPoint(StrictModel):
    horizon_days: int = Field(ge=0)
    valuation_time: datetime
    estimated_position_value: float
    flat_spot_carry: float
    carry_as_pct_capital: float | None = None
    carry_as_pct_max_loss: float | None = None
    carry_classification: Literal["PURE_FLAT_SPOT_CARRY", "CROSSES_DIVIDEND_EVENT"]
    ex_div_adjusted_position_value: float | None = None
    warnings: list[str] = Field(default_factory=list)


class TimeDecayExposure(StrictModel):
    current_net_theta: float
    theta_per_capital_per_day: float | None = None
    theta_capital_status: str = Field(min_length=1)
    flat_spot_1d: float | None = None
    flat_spot_7d: float | None = None
    flat_spot_30d: float | None = None
    flat_spot_60d: float | None = None
    flat_spot_90d: float | None = None
    effective_decay_rate_0_7: float | None = None
    effective_decay_rate_0_30: float | None = None
    effective_decay_rate_30_60: float | None = None
    effective_decay_rate_60_90: float | None = None
    decay_acceleration_30_60: float | None = None
    decay_acceleration_60_90: float | None = None
    acceleration_status: Literal["ACCELERATING", "DECELERATING", "SIGN_FLIP", "INSUFFICIENT"]
    time_decay_curve: list[TimeDecayPoint] = Field(min_length=2)
    assumptions: list[str]
    confidence: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class LiquidityDiagnostics(StrictModel):
    contract_symbol: str = Field(min_length=1)
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    mid: float | None = Field(default=None, ge=0)
    spread_abs: float | None = Field(default=None, ge=0)
    spread_pct_mid: float | None = Field(default=None, ge=0)
    bid_size: int | None = Field(default=None, ge=0)
    ask_size: int | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)
    open_interest: int | None = Field(default=None, ge=0)
    quote_age_seconds: float = Field(ge=0)
    source: str = Field(min_length=1)
    timestamp: datetime
    liquidity_score: float = Field(ge=0, le=1)
    liquidity_model_version: str = Field(min_length=1)
    calibration_status: Literal["UNCALIBRATED", "CALIBRATED"] = "UNCALIBRATED"


class EntryCostBreakdown(StrictModel):
    # Deprecated 1.0 aliases. They retain midpoint semantics so historical tickets
    # remain readable; schema 1.1 callers must use the explicit fields below.
    premium_paid: float = Field(ge=0)
    premium_received: float = Field(ge=0)
    net_premium: float
    mid_theoretical_value: float
    bid_ask_cost: float = Field(ge=0)
    expected_slippage: float = Field(ge=0)
    commission: float = Field(ge=0)
    fx_conversion_cost: float | None = Field(default=None, ge=0)
    total_entry_cost: float
    total_capital_required: float | None = Field(default=None, ge=0)
    execution_status: ExecutionEstimateStatus
    combo_execution_status: Literal["INDICATIVE", "OBSERVED_COMBO"] = "INDICATIVE"
    warnings: list[str] = Field(default_factory=list)
    theoretical_mid_premium_paid: float | None = Field(default=None, ge=0)
    theoretical_mid_premium_received: float | None = Field(default=None, ge=0)
    theoretical_mid_net_premium: float | None = None
    executable_premium_paid: float | None = Field(default=None, ge=0)
    executable_premium_received: float | None = Field(default=None, ge=0)
    executable_net_premium: float | None = None
    entry_bid_ask_cost: float | None = Field(default=None, ge=0)
    entry_slippage: float | None = Field(default=None, ge=0)
    entry_commission: float | None = Field(default=None, ge=0)
    entry_fx_cost: float | None = Field(default=None, ge=0)
    total_entry_cash_flow: float | None = None

    @model_validator(mode="after")
    def reconcile_entry_economics(self) -> EntryCostBreakdown:
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
        spread_cost = executable_net - theoretical_net
        if spread_cost < -1e-8:
            raise ValueError("executable premium cannot improve on the declared midpoint")
        entry_bid_ask_cost = self.entry_bid_ask_cost
        if entry_bid_ask_cost is None:
            entry_bid_ask_cost = self.bid_ask_cost
            object.__setattr__(self, "entry_bid_ask_cost", entry_bid_ask_cost)
        if abs(entry_bid_ask_cost - spread_cost) > 1e-8:
            raise ValueError("entry spread cost does not reconcile midpoint and executable premium")
        entry_slippage = (
            self.expected_slippage if self.entry_slippage is None else self.entry_slippage
        )
        entry_commission = (
            self.commission if self.entry_commission is None else self.entry_commission
        )
        object.__setattr__(self, "entry_slippage", entry_slippage)
        object.__setattr__(self, "entry_commission", entry_commission)
        if self.entry_fx_cost is None:
            object.__setattr__(self, "entry_fx_cost", self.fx_conversion_cost)
        known_total = (
            executable_net + entry_slippage + entry_commission + (self.entry_fx_cost or 0.0)
        )
        total_entry_cash_flow = self.total_entry_cash_flow
        if total_entry_cash_flow is None:
            total_entry_cash_flow = self.total_entry_cost
            object.__setattr__(self, "total_entry_cash_flow", total_entry_cash_flow)
        if abs(total_entry_cash_flow - known_total) > 1e-8:
            raise ValueError("entry cash-flow components do not reconcile")
        if abs(self.total_entry_cost - total_entry_cash_flow) > 1e-8:
            raise ValueError("deprecated total_entry_cost must equal total_entry_cash_flow")
        return self


class ExitCostEstimate(StrictModel):
    exit_path: ExitPath = ExitPath.CLOSE_BEFORE_EXPIRY
    estimated_exit_bid_ask_cost: float = Field(ge=0)
    estimated_exit_slippage: float = Field(ge=0)
    closing_commissions: float = Field(ge=0)
    fx_exit_cost: float | None = Field(default=None, ge=0)
    # Legacy 1.0 field. New 1.1 builders do not apply this cost to a close trade.
    assignment_or_exercise_cost_if_relevant: float | None = Field(default=None, ge=0)
    exercise_cost_if_relevant: float | None = Field(default=None, ge=0)
    assignment_cost_if_relevant: float | None = Field(default=None, ge=0)
    settlement_cost_if_relevant: float | None = Field(default=None, ge=0)
    hold_to_expiry_cost_status: str = "NOT_EVALUATED"
    total_exit_cost: float
    status: ExecutionEstimateStatus
    warnings: list[str] = Field(default_factory=list)
    exit_cost_status: str = "ESTIMATED_CONFIGURED_EXECUTION_MODEL"

    @model_validator(mode="after")
    def reconcile_total(self) -> ExitCostEstimate:
        known = (
            self.estimated_exit_bid_ask_cost
            + self.estimated_exit_slippage
            + self.closing_commissions
            + (self.fx_exit_cost or 0.0)
            + (self.assignment_or_exercise_cost_if_relevant or 0.0)
        )
        if abs(known - self.total_exit_cost) > 1e-8:
            raise ValueError("exit cost components do not reconcile")
        return self


class RoundTripCost(StrictModel):
    entry_bid_ask_cost: float = Field(ge=0)
    entry_slippage: float = Field(ge=0)
    entry_commissions: float = Field(ge=0)
    entry_fx_cost: float | None = Field(default=None, ge=0)
    exit: ExitCostEstimate
    total_round_trip_cost: float = Field(ge=0)
    round_trip_cost_as_pct_capital: float | None = None

    @model_validator(mode="after")
    def reconcile_total(self) -> RoundTripCost:
        known = (
            self.entry_bid_ask_cost
            + self.entry_slippage
            + self.entry_commissions
            + (self.entry_fx_cost or 0.0)
            + self.exit.total_exit_cost
        )
        if abs(known - self.total_round_trip_cost) > 1e-8:
            raise ValueError("round-trip cost components do not reconcile")
        return self


class MarginEstimate(StrictModel):
    margin_requirement: float | None = Field(default=None, ge=0)
    buying_power_usage: float | None = Field(default=None, ge=0)
    status: MarginStatus
    source: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def prevent_false_zero(self) -> MarginEstimate:
        if self.status in {MarginStatus.UNKNOWN, MarginStatus.BLOCKED} and (
            self.margin_requirement is not None or self.buying_power_usage is not None
        ):
            raise ValueError("unknown or blocked margin must remain null")
        if self.status in {MarginStatus.KNOWN_BROKER, MarginStatus.ESTIMATED} and (
            self.margin_requirement is None or self.margin_requirement <= 0
        ):
            raise ValueError("known or estimated margin must be positive")
        return self


class FXAttribution(StrictModel):
    mode: FXHandlingMode
    option_pnl_usd: float
    entry_fx_rate_usd_per_base: float | None = Field(default=None, gt=0)
    scenario_fx_rate_usd_per_base: float | None = Field(default=None, gt=0)
    pnl_base_at_scenario_fx: float | None = None
    pnl_base_at_constant_entry_fx: float | None = None
    fx_contribution_base: float | None = None
    fx_conversion_fees_base: float | None = Field(default=None, ge=0)
    status: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class ScenarioCell(StrictModel):
    spot: float = Field(ge=0)
    horizon_days: int = Field(ge=0)
    valuation_time: datetime
    volatility_scenario: str = Field(min_length=1)
    estimated_position_value: float
    gross_pnl: float
    round_trip_cost: float | None = Field(default=None, ge=0)
    net_pnl: float | None = None
    net_return: float | None = None
    scenario_status: str = Field(min_length=1)
    exit_path: ExitPath = ExitPath.CLOSE_BEFORE_EXPIRY
    exit_cost_applied: float | None = Field(default=None, ge=0)
    exit_cost_status: str = Field(default="NOT_EVALUATED", min_length=1)
    requested_horizon_days: int | None = Field(default=None, ge=0)
    effective_horizon_days: float | None = Field(default=None, ge=0)
    event_date: date | None = None
    event_status: EventScenarioStatus = EventScenarioStatus.NOT_APPLICABLE
    event_to_expiry_days: int | None = Field(default=None, ge=0)
    applied_vol_shift: float | None = None
    event_leg_effects: list[EventLegEffect] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ScenarioMatrix(StrictModel):
    scenario_name: str = Field(min_length=1)
    scenario_type: VolatilityScenarioType
    scenario_status: VolatilityScenarioStatus
    spot_axis: list[float] = Field(min_length=1)
    horizon_days_axis: list[int] = Field(min_length=1)
    cells: list[ScenarioCell] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)


class EventLegEffect(StrictModel):
    contract_symbol: str = Field(min_length=1)
    event_date: date | None = None
    event_status: EventScenarioStatus
    event_to_expiry_days: int | None = Field(default=None, ge=0)
    applied_vol_shift: float


class RateStressResult(StrictModel):
    scenario_name: str = Field(min_length=1)
    scenario_type: RateScenarioType
    status: Literal["CONFIGURED_STRESS"]
    leg_rate_shifts_basis_points: dict[str, float]
    estimated_position_value: float
    gross_pnl: float
    round_trip_cost: float = Field(ge=0)
    net_pnl: float
    assumptions: list[str] = Field(default_factory=list)


class ProfitInterval(StrictModel):
    lower: float = Field(ge=0)
    upper: float | None = Field(default=None, ge=0)


class BreakevenResult(StrictModel):
    horizon_days: int = Field(ge=0)
    valuation_time: datetime
    volatility_scenario: str = Field(min_length=1)
    break_even_roots: list[float]
    profit_intervals: list[ProfitInterval]
    status: Literal["SOLVED", "NO_ROOT_IN_DOMAIN", "BLOCKED"]
    search_domain: tuple[float, float]
    exit_path: ExitPath = ExitPath.CLOSE_BEFORE_EXPIRY
    applied_exit_cost: float | None = Field(default=None, ge=0)
    exit_cost_status: str = Field(default="NOT_EVALUATED", min_length=1)
    breakeven_type: Literal[
        "CLOSE_BEFORE_EXPIRY_BREAKEVEN",
        "EXPIRATION_BREAKEVEN",
        "MANAGED_EXIT_BREAKEVEN",
    ] = "CLOSE_BEFORE_EXPIRY_BREAKEVEN"
    warnings: list[str] = Field(default_factory=list)


class BreakevenClock(StrictModel):
    results: list[BreakevenResult] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class TargetArrivalResult(StrictModel):
    target_spot: float = Field(gt=0)
    volatility_scenario: str = Field(min_length=1)
    status: TargetArrivalStatus
    latest_profitable_arrival_date: datetime | None = None
    profitable_horizons_days: list[int] = Field(default_factory=list)
    managed_exit_deadline: datetime | None = None
    warnings: list[str] = Field(default_factory=list)


class TouchProbabilityMetrics(StrictModel):
    target: float = Field(gt=0)
    direction: TouchDirection
    horizon_days: int = Field(gt=0)
    probability_touch: float | None = Field(default=None, ge=0, le=1)
    probability_terminal_above: float | None = Field(default=None, ge=0, le=1)
    probability_terminal_below: float | None = Field(default=None, ge=0, le=1)
    first_touch_count: int | None = Field(default=None, ge=0)
    median_first_touch_time_conditional_on_touch: float | None = Field(default=None, ge=0)
    confidence_interval_touch: tuple[float, float] | None = None
    effective_sample_size: float | None = Field(default=None, gt=0)
    model: str | None = None
    calibration_status: ProbabilityStatus
    reason: str | None = None

    @model_validator(mode="after")
    def enforce_availability(self) -> TouchProbabilityMetrics:
        unavailable = self.calibration_status in {
            ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE,
            ProbabilityStatus.PROBABILITY_MODEL_NOT_PROMOTED,
        }
        values = (
            self.probability_touch,
            self.probability_terminal_above,
            self.probability_terminal_below,
            self.first_touch_count,
            self.median_first_touch_time_conditional_on_touch,
            self.confidence_interval_touch,
            self.effective_sample_size,
        )
        if unavailable and (any(value is not None for value in values) or not self.reason):
            raise ValueError("unavailable probabilities must be null and carry a reason")
        return self


class EconomicPathState(StrictModel):
    spot: float = Field(gt=0)
    valuation_time: datetime
    volatility_by_contract: dict[str, float] = Field(min_length=1)
    rate_shift_basis_points: float = 0.0
    fx_rate_usd_per_base: float | None = Field(default=None, gt=0)
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_volatilities(self) -> EconomicPathState:
        if any(value <= 0 for value in self.volatility_by_contract.values()):
            raise ValueError("economic path volatilities must be positive")
        return self


class DistributionPnLMetrics(StrictModel):
    expected_pnl: float | None = None
    median_pnl: float | None = None
    expected_return: float | None = None
    median_return: float | None = None
    probability_profit: float | None = Field(default=None, ge=0, le=1)
    probability_gain_25: float | None = Field(default=None, ge=0, le=1)
    probability_gain_50: float | None = Field(default=None, ge=0, le=1)
    probability_gain_90: float | None = Field(default=None, ge=0, le=1)
    probability_x2: float | None = Field(default=None, ge=0, le=1)
    probability_x3: float | None = Field(default=None, ge=0, le=1)
    probability_loss_25: float | None = Field(default=None, ge=0, le=1)
    probability_loss_50: float | None = Field(default=None, ge=0, le=1)
    probability_loss_70: float | None = Field(default=None, ge=0, le=1)
    probability_loss_90: float | None = Field(default=None, ge=0, le=1)
    var_95: float | None = Field(default=None, ge=0)
    cvar_95: float | None = Field(default=None, ge=0)
    minimum_pnl: float | None = None
    maximum_pnl: float | None = None
    effective_sample_size: float | None = Field(default=None, gt=0)
    confidence_intervals: dict[str, tuple[float, float]] = Field(default_factory=dict)
    model: str | None = None
    measure: Literal["P"] | None = None
    calibration_status: ProbabilityStatus
    availability_status: DistributionAvailabilityStatus
    missing_reason: str | None = None
    assumptions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_distribution_availability(self) -> DistributionPnLMetrics:
        values = (
            self.expected_pnl,
            self.median_pnl,
            self.expected_return,
            self.median_return,
            self.probability_profit,
            self.probability_gain_25,
            self.probability_gain_50,
            self.probability_gain_90,
            self.probability_x2,
            self.probability_x3,
            self.probability_loss_25,
            self.probability_loss_50,
            self.probability_loss_70,
            self.probability_loss_90,
            self.var_95,
            self.cvar_95,
            self.minimum_pnl,
            self.maximum_pnl,
            self.effective_sample_size,
        )
        if self.availability_status is DistributionAvailabilityStatus.UNAVAILABLE:
            if any(value is not None for value in values) or not self.missing_reason:
                raise ValueError("unavailable PnL distributions must remain null with a reason")
        elif self.expected_pnl is None or self.probability_profit is None:
            raise ValueError("available PnL distributions require expected PnL and P(profit)")
        return self


class ScoreDimensionSnapshot(StrictModel):
    name: Literal["opportunity", "risk", "evidence", "model_agreement", "execution_quality"]
    score_value: float | None = Field(default=None, ge=0, le=100)
    score_coverage: float = Field(ge=0, le=1)
    missing_components: list[str] = Field(default_factory=list)
    confidence: str = Field(min_length=1)
    formula_version: str = Field(min_length=1)
    status: str = Field(min_length=1)


class FiveScoreSnapshot(StrictModel):
    opportunity: ScoreDimensionSnapshot
    risk: ScoreDimensionSnapshot
    evidence: ScoreDimensionSnapshot
    model_agreement: ScoreDimensionSnapshot
    execution_quality: ScoreDimensionSnapshot
    scope: FiveScoreScope
    source: str = Field(min_length=1)
    generated_at: datetime
    candidate_id: str | None = None
    config_hash: str | None = None


class GreekTaylorAttribution(StrictModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    vomma: float
    vanna: float
    rho: float
    execution_costs: float
    greek_approximated_pnl: float
    full_repriced_pnl: float
    residual: float


class FullRepricingAttribution(StrictModel):
    spot: float
    time: float
    volatility: float
    rates: float
    fx: float
    execution_costs: float
    other: float
    residual: float
    full_repriced_pnl: float
    method: Literal["exact_shapley_full_repricing"] = "exact_shapley_full_repricing"


class PnLAttribution(StrictModel):
    scenario_name: str = Field(min_length=1)
    taylor: GreekTaylorAttribution
    full_repricing: FullRepricingAttribution


class TradeIntensityDiagnostics(StrictModel):
    effective_leverage: float | None = None
    capital_at_risk_pct: float | None = None
    theta_per_capital_per_day: float | None = None
    flat_spot_30d_loss_pct: float | None = None
    flat_spot_60d_loss_pct: float | None = None
    probability_loss_over_50: float | None = None
    probability_loss_over_70: float | None = None
    spread_over_entry_capital_pct: float | None = None
    greek_instability: GreekConfidenceLevel
    event_iv_sensitivity: float | None = None
    max_loss_pct: float | None = None
    category: TradeIntensityCategory
    triggered_policies: list[str] = Field(default_factory=list)
    policy_status: Literal["CONFIGURED_POLICY_UNCALIBRATED"] = "CONFIGURED_POLICY_UNCALIBRATED"


class LegEconomics(StrictModel):
    side: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    instrument_type: str = Field(min_length=1)
    option_type: str | None = None
    strike: float | None = Field(default=None, gt=0)
    expiration: datetime | None = None
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    mid: float | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0)
    multiplier: float = Field(gt=0)
    premium_paid: float = Field(ge=0)
    premium_received: float = Field(ge=0)
    mid_premium: float | None = Field(default=None, ge=0)
    theoretical_mid_premium_paid: float | None = Field(default=None, ge=0)
    theoretical_mid_premium_received: float | None = Field(default=None, ge=0)
    executable_premium_paid: float | None = Field(default=None, ge=0)
    executable_premium_received: float | None = Field(default=None, ge=0)
    con_id: int | None = Field(default=None, gt=0)
    local_symbol: str | None = None
    trading_class: str | None = None
    deliverable: str | None = None
    exercise_style: str | None = None
    settlement: str | None = None
    adjusted_contract: bool | None = None
    greeks: AdvancedGreeks | None = None


class TradeEconomicsTicket(StrictModel):
    schema_version: Literal["1.0", "1.1"] = "1.1"
    fixture_status: Literal["LIVE_INPUT", "SYNTHETIC_TEST_FIXTURE", "RESEARCH_FIXTURE"]
    candidate_id: str = Field(min_length=1)
    underlying: str = Field(min_length=1)
    strategy_name: str = Field(min_length=1)
    exact_market_timestamp: datetime
    currency: str = Field(min_length=3, max_length=3)
    data_freshness_status: str = Field(min_length=1)
    expirations: list[datetime]
    dte_exact_days: float = Field(ge=0)
    lifecycle_policy: str = "SAME_EXPIRY_HOLD_TO_EXPIRY"
    first_expiry: datetime | None = None
    managed_exit_deadline: datetime | None = None
    intraday_precision_status: IntradayPrecisionStatus
    intraday_precision_warning: str | None = None
    legs: list[LegEconomics]
    entry_cost: EntryCostBreakdown
    exit_cost_estimate: ExitCostEstimate
    round_trip_cost: RoundTripCost
    margin: MarginEstimate
    maximum_loss: float | None = Field(default=None, ge=0)
    maximum_profit: float | None = Field(default=None, ge=0)
    expiration_breakevens: list[float]
    capital_at_risk: float | None = Field(default=None, gt=0)
    leverage: LeverageDiagnostics
    time_decay: TimeDecayExposure | None = None
    aggregate_greeks: AdvancedGreeks | None = None
    breakeven_clock: BreakevenClock | None = None
    target_arrivals: list[TargetArrivalResult] = Field(default_factory=list)
    scenario_matrices: list[ScenarioMatrix] = Field(default_factory=list)
    rate_stress_results: list[RateStressResult] = Field(default_factory=list)
    touch_probabilities: list[TouchProbabilityMetrics] = Field(default_factory=list)
    distribution_pnl: DistributionPnLMetrics | None = None
    five_scores: FiveScoreSnapshot | None = None
    pnl_attributions: list[PnLAttribution] = Field(default_factory=list)
    fx_attribution: FXAttribution
    liquidity: list[LiquidityDiagnostics] = Field(default_factory=list)
    intensity: TradeIntensityDiagnostics | None = None
    assignment_and_exercise_risks: list[str] = Field(default_factory=list)
    classification: str = Field(min_length=1)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    data_status: str = Field(min_length=1)
    probability_status: ProbabilityStatus
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"
