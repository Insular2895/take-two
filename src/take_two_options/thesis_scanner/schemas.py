"""Strict contracts for the V10 Bullish Thesis Scanner."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import OptionType, PositionSide, StrictModel
from take_two_options.knowledge.schemas import (
    Architecture,
    CompiledStrategyCandidate,
)


class ThesisCandidateStatus(StrEnum):
    ELIGIBLE = "eligible_thesis_candidate"
    WATCHLIST = "watchlist"
    BLOCKED = "blocked"
    NO_TRADE = "no_trade"


class ThesisProfile(StrEnum):
    PRUDENT = "prudent"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class IVCase(StrEnum):
    DOWN = "iv_down"
    STABLE = "iv_stable"
    UP = "iv_up"


class ThesisScanRequest(StrictModel):
    ticker: str = Field(min_length=1)
    direction: Literal["bullish"]
    budget_eur: float = Field(gt=0)
    max_loss_eur: float = Field(gt=0)
    catalyst_date: date
    expiration_buffer_days: int = Field(ge=0)
    target_prices: list[float] = Field(min_length=1)
    scenario_probabilities: list[float] | None = None
    top: int = Field(default=3, ge=1, le=20)
    current_chain: str
    spot_override: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_request(self) -> ThesisScanRequest:
        if self.max_loss_eur > self.budget_eur:
            raise ValueError("maximum loss cannot exceed the EUR budget")
        if any(price <= 0 for price in self.target_prices):
            raise ValueError("target prices must be positive")
        if self.scenario_probabilities is not None:
            if len(self.scenario_probabilities) != len(self.target_prices):
                raise ValueError("scenario probabilities must match the number of target prices")
            if any(value < 0 or value > 1 for value in self.scenario_probabilities):
                raise ValueError("scenario probabilities must be between zero and one")
            if abs(sum(self.scenario_probabilities) - 1.0) > 1e-6:
                raise ValueError("scenario probabilities must sum to one")
        return self


class ThesisScanPolicy(StrictModel):
    policy_id: str
    eur_usd_rate: float = Field(gt=0)
    fx_rate_date: date
    fx_rate_source: str
    maximum_fx_age_days: int = Field(ge=0)
    risk_free_rate: float
    risk_free_rate_date: date
    risk_free_rate_source: str
    continuous_dividend_yield: float = Field(ge=0, lt=1)
    dividend_source: str
    maximum_quote_age_days: int = Field(ge=0)
    minimum_open_interest: int = Field(ge=0)
    minimum_volume: int = Field(ge=0)
    maximum_relative_spread: float = Field(gt=0)
    commission_per_contract_side: float = Field(ge=0)
    slippage_per_contract_side: float = Field(ge=0)
    maximum_contracts: int = Field(gt=0)
    minimum_moneyness: float = Field(gt=0)
    maximum_moneyness: float = Field(gt=0)
    maximum_vertical_width: float = Field(gt=0)
    maximum_butterfly_wing_width: float = Field(gt=0)
    leaps_minimum_dte: int = Field(gt=0)
    iv_case_multipliers: dict[IVCase, float]
    spot_grid_multipliers: list[float] = Field(min_length=3)
    historical_confidence: float = Field(ge=0, le=1)
    profile_weights: dict[ThesisProfile, dict[str, float]]
    source_status: Literal[
        "product_constraint",
        "calibration_required",
        "experimental",
    ] = "calibration_required"

    @model_validator(mode="after")
    def validate_policy(self) -> ThesisScanPolicy:
        if self.maximum_moneyness < self.minimum_moneyness:
            raise ValueError("maximum moneyness must follow minimum moneyness")
        if set(self.iv_case_multipliers) != set(IVCase):
            raise ValueError("all three IV cases must be configured")
        if any(value <= 0 for value in self.iv_case_multipliers.values()):
            raise ValueError("IV multipliers must be positive")
        if set(self.profile_weights) != set(ThesisProfile):
            raise ValueError("all three ranking profiles must be configured")
        for profile, weights in self.profile_weights.items():
            if not weights or any(value < 0 for value in weights.values()):
                raise ValueError(f"{profile.value} weights must be non-negative")
            if sum(weights.values()) <= 0:
                raise ValueError(f"{profile.value} weights must have positive mass")
        return self


class ThesisQuote(StrictModel):
    symbol: str = Field(min_length=1)
    expiration: date
    option_type: OptionType
    strike: float = Field(gt=0)
    bid: float | None = Field(default=None, ge=0)
    ask: float | None = Field(default=None, ge=0)
    bid_size: int | None = Field(default=None, ge=0)
    ask_size: int | None = Field(default=None, ge=0)
    volume: int | None = Field(default=None, ge=0)
    open_interest: int | None = Field(default=None, ge=0)
    implied_volatility: float | None = Field(default=None, gt=0, lt=5)
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None
    quote_timestamp: datetime | None = None
    multiplier: int | None = Field(default=None, gt=0)
    multiplier_status: Literal["confirmed", "assumed", "unknown"] = "unknown"
    standard_contract: bool | None = None
    price_quality: Literal[
        "opra",
        "indicative",
        "eod_bid_ask",
        "synthetic",
        "unknown",
    ]
    source_id: str

    @property
    def midpoint(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2


class ThesisChain(StrictModel):
    format_version: Literal["thesis_chain_v1"] = "thesis_chain_v1"
    ticker: str
    as_of: datetime
    retrieved_at: datetime
    spot: float = Field(gt=0)
    spot_timestamp: datetime
    spot_source_id: str
    price_quality: Literal[
        "opra",
        "indicative",
        "eod_bid_ask",
        "synthetic",
        "unknown",
    ]
    source_id: str
    quotes: list[ThesisQuote] = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)
    source_path: str | None = None


class QuoteRejectionSummary(StrictModel):
    total_quotes: int = Field(ge=0)
    usable_calls: int = Field(ge=0)
    reasons: dict[str, int] = Field(default_factory=dict)


class ThesisExecution(StrictModel):
    theoretical_mid_debit_usd: float
    theoretical_mid_debit_eur: float
    conservative_debit_usd: float
    conservative_debit_eur: float
    slippage_usd: float = Field(ge=0)
    slippage_eur: float = Field(ge=0)
    commissions_usd: float = Field(ge=0)
    commissions_eur: float = Field(ge=0)
    total_cost_usd: float
    total_cost_eur: float
    indicative_limit_price_per_share: float
    fx_rate: float = Field(gt=0)
    fx_rate_date: date
    fx_rate_source: str
    quote_date: datetime
    notes: list[str] = Field(default_factory=list)


class NetGreeks(StrictModel):
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    model: Literal["quantlib_fd_american"] = "quantlib_fd_american"
    units: dict[str, str] = Field(
        default_factory=lambda: {
            "delta": "USD_position_value_per_USD_spot",
            "gamma": "USD_position_delta_per_USD_spot",
            "theta": "USD_position_value_per_calendar_day",
            "vega": "USD_position_value_per_IV_percentage_point",
            "rho": "USD_position_value_per_rate_percentage_point",
        }
    )


class ThesisScenarioPoint(StrictModel):
    scenario_id: str
    spot: float = Field(gt=0)
    valuation_date: date
    days_forward: int = Field(ge=0)
    iv_case: IVCase
    iv_multiplier: float = Field(gt=0)
    terminal: bool
    estimated_value_usd: float
    pnl_usd: float
    pnl_eur: float
    underlying_effect_usd: float
    theta_effect_usd: float
    iv_effect_usd: float
    execution_cost_effect_usd: float
    residual_usd: float


class ThesisCandidate(StrictModel):
    candidate_id: str
    architecture: Architecture
    maturity_class: Literal["standard", "leaps"]
    display_name: str
    base_candidate: CompiledStrategyCandidate
    status: ThesisCandidateStatus
    dte: int = Field(ge=0)
    expiration: date
    execution: ThesisExecution
    net_greeks: NetGreeks
    scenario_points: list[ThesisScenarioPoint]
    target_pnl_stable_at_catalyst_usd: dict[str, float]
    maximum_loss_eur: float = Field(ge=0)
    maximum_gain_eur: float | None = Field(default=None, ge=0)
    expected_pnl_usd: float | None = None
    probability_success: float | None = Field(default=None, ge=0, le=1)
    maximum_return_on_risk: float | None = Field(default=None, ge=0)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    selection_reasons: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    historical_confidence: float = Field(ge=0, le=1)


class ProfileScore(StrictModel):
    candidate_id: str
    profile: ThesisProfile
    score: float = Field(ge=0, le=100)
    criteria: dict[str, float]
    reasons: list[str]
    invalidation_conditions: list[str]


class ProfileRanking(StrictModel):
    profile: ThesisProfile
    scores: list[ProfileScore]


class IBKRPreviewLeg(StrictModel):
    action: Literal["ACHETER", "VENDRE"]
    quantity: int = Field(gt=0)
    option_type: Literal["CALL"]
    occ_symbol: str
    strike: float
    expiration: date
    exchange: Literal["SMART"] = "SMART"
    con_id: None = None
    con_id_status: Literal["resolve_in_tws"] = "resolve_in_tws"


class IBKRPreviewTicket(StrictModel):
    candidate_id: str
    mode: Literal["preview"] = "preview"
    broker: Literal["IBKR"] = "IBKR"
    security_type: Literal["OPT", "BAG"]
    order_type: Literal["LMT"] = "LMT"
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"
    debit_max_per_share_usd: float
    indicative_cost_per_lot_usd: float
    indicative_cost_eur: float
    quote_date: datetime
    legs: list[IBKRPreviewLeg]
    message: str = "vérifier la cotation combo live dans IBKR avant validation"


class ThesisScanReport(StrictModel):
    schema_version: Literal["10.0"] = "10.0"
    report_id: str
    created_at: datetime
    request: ThesisScanRequest
    policy: ThesisScanPolicy
    chain: ThesisChain
    quote_rejections: QuoteRejectionSummary
    generated_by_architecture: dict[str, int]
    generated_candidates: int = Field(ge=0)
    technically_admissible_candidates: int = Field(ge=0)
    overall_status: ThesisCandidateStatus
    candidates: list[ThesisCandidate]
    rankings: list[ProfileRanking]
    ibkr_previews: list[IBKRPreviewTicket]
    blocked_reasons: dict[str, int]
    historical_warning: str
    probability_status: Literal["user_supplied", "not_provided"]
    assumptions: list[str]
    limitations: list[str]
    data_sources: list[str]
    output_files: list[str] = Field(default_factory=list)
    order_capability: Literal["forbidden"] = "forbidden"


def side_label(side: PositionSide) -> Literal["ACHETER", "VENDRE"]:
    return "ACHETER" if side is PositionSide.LONG else "VENDRE"
