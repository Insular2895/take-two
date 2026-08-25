"""Strict contracts for the Phase M Cloud Research workbench.

These objects are deliberately compact: GitHub Actions computes the exhaustive
research universe, while D1 stores only browsable summaries and structured
details.  Nothing in this module can describe or transmit a broker order.
"""

from __future__ import annotations

import math
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from take_two_options.budget import FlexibleBudgetPolicyV2, MinimumSpendPolicy
from take_two_options.models import StrictModel


class MarketDataMode(StrEnum):
    LAST_GOVERNED_SNAPSHOT = "LAST_GOVERNED_SNAPSHOT"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"


class AnalysisStatus(StrEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    NO_TRADE = "NO_TRADE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisBudgetRequest(StrictModel):
    """The exact, immutable browser-to-Worker research request."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)

    preferred_budget: float = Field(default=800.0, gt=0)
    target_budget: float = Field(default=1000.0, gt=0)
    maximum_budget: float = Field(default=1500.0, gt=0)
    minimum_spend_policy: Literal["SOFT", "HARD"] = "SOFT"
    market_data_mode: MarketDataMode = MarketDataMode.SYNTHETIC_DEMO
    currency: Literal["EUR"] = "EUR"

    @field_validator("preferred_budget", "target_budget", "maximum_budget")
    @classmethod
    def require_finite_money(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("budget values must be finite")
        return value

    @model_validator(mode="after")
    def validate_budget_order(self) -> AnalysisBudgetRequest:
        if not self.preferred_budget <= self.target_budget <= self.maximum_budget:
            raise ValueError("preferred_budget <= target_budget <= maximum_budget is required")
        return self

    def apply_to(self, policy: FlexibleBudgetPolicyV2) -> FlexibleBudgetPolicyV2:
        """Map the UI semantics exactly onto BudgetPolicyV2."""

        return policy.model_copy(
            update={
                "currency": self.currency,
                "target_budget": self.target_budget,
                "under_target_tolerance": self.target_budget - self.preferred_budget,
                "max_overspend": self.maximum_budget - self.target_budget,
                "minimum_spend_policy": MinimumSpendPolicy(self.minimum_spend_policy),
            }
        )


class AnalysisJobRequest(StrictModel):
    """Immutable request returned only to the signed GitHub runner."""

    analysis_request_id: str = Field(pattern=r"^analysis-[a-f0-9]{24}$")
    request_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    budget: AnalysisBudgetRequest
    created_at: datetime


class CandidateSummary(StrictModel):
    candidate_id: str
    architecture: str
    recipe_id: str
    strategy_name: str
    leg_summary: str
    engine_rank: int = Field(gt=0)
    pareto_rank: int | None = Field(default=None, gt=0)
    quantity: int = Field(gt=0)
    leg_count: int = Field(gt=0)
    expiration: str
    common_expiry: bool
    dte: int = Field(ge=0)
    signed_entry_cash_flow: float
    entry_cash_flow_type: Literal["DEBIT", "CREDIT", "FLAT"]
    capital_required: float | None = Field(default=None, ge=0)
    maximum_loss: float | None = Field(default=None, ge=0)
    maximum_gain: float | None = Field(default=None, ge=0)
    break_even_points: list[float] = Field(default_factory=list)
    net_delta: float | None = None
    net_theta: float | None = None
    average_implied_volatility: float | None = Field(default=None, gt=0)
    maximum_relative_spread: float | None = Field(default=None, ge=0)
    minimum_open_interest: int | None = Field(default=None, ge=0)
    expected_pnl: float | None = None
    expected_return: float | None = None
    return_on_capital: float | None = None
    return_on_risk: float | None = None
    probability_profit: float | None = Field(default=None, ge=0, le=1)
    probability_loss_25: float | None = Field(default=None, ge=0, le=1)
    probability_loss_50: float | None = Field(default=None, ge=0, le=1)
    probability_loss_70: float | None = Field(default=None, ge=0, le=1)
    var_95: float | None = Field(default=None, ge=0)
    cvar_95: float | None = Field(default=None, ge=0)
    risk_on_capital: float | None = Field(default=None, ge=0)
    distance_to_target_budget: float | None = None
    headroom_to_hard_maximum: float | None = None
    theta_per_capital_day: float | None = None
    flat_spot_7d: float | None = None
    flat_spot_30d: float | None = None
    flat_spot_60d: float | None = None
    flat_spot_90d: float | None = None
    net_gamma: float | None = None
    net_vega: float | None = None
    data_freshness: Literal["FRESH", "STALE", "UNKNOWN"]
    budget_status: str
    eligible: bool
    research_eligible: bool
    paper_eligible: bool
    pruned: bool
    reason_codes: list[str] = Field(default_factory=list)
    score_probability: float | None = Field(default=None, ge=0, le=100)
    score_payoff: float | None = Field(default=None, ge=0, le=100)
    score_risk: float | None = Field(default=None, ge=0, le=100)
    score_robustness: float | None = Field(default=None, ge=0, le=100)
    score_executability: float | None = Field(default=None, ge=0, le=100)
    score_opportunity: float | None = Field(default=None, ge=0, le=100)
    score_evidence: float | None = Field(default=None, ge=0, le=100)
    score_model_agreement: float | None = Field(default=None, ge=0, le=100)
    score_execution_quality: float | None = Field(default=None, ge=0, le=100)
    trade_economics_ticket_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class CandidateDetail(StrictModel):
    candidate_id: str
    engine_rank_method: Literal["HARD_VETO_PARETO_BUDGET_DISTANCE_V1"]
    legs: list[dict[str, Any]]
    economics: dict[str, Any]
    payoff: dict[str, Any]
    time_decay: dict[str, Any]
    scenario_matrix: dict[str, Any]
    volatility: dict[str, Any]
    distribution: dict[str, Any]
    scores: dict[str, Any]
    budget_diagnostics: dict[str, Any] | None
    lifecycle_capital_requirement: dict[str, Any] | None
    assumptions: list[str]
    uncertainties: list[str]
    limitations: list[str]
    explanation: list[str]
    phase_m_context_id: str = Field(pattern=r"^phase-m-context-[a-f0-9]{16}$")
    phase_m_context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    trade_economics_ticket: dict[str, Any]


class ResearchAnalysisResult(StrictModel):
    analysis_request_id: str
    status: Literal["COMPLETE", "NO_TRADE"]
    verdict: Literal["RESEARCH_CANDIDATES_AVAILABLE", "NO_TRADE"]
    generated_at: datetime
    market_data_mode: MarketDataMode
    snapshot_id: str
    snapshot_as_of: datetime
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    catalog_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase_m_context_id: str = Field(pattern=r"^phase-m-context-[a-f0-9]{16}$")
    phase_m_context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    total_generated: int = Field(ge=0)
    total_pruned: int = Field(ge=0)
    total_research_eligible: int = Field(ge=0)
    total_paper_eligible: int = Field(ge=0)
    combinations_by_architecture: dict[str, int]
    best_overall_ids: list[str]
    best_by_architecture: dict[str, str]
    no_trade_reasons: list[str]
    warnings: list[str]
    summaries: list[CandidateSummary]
    details: list[CandidateDetail]
    safety: dict[str, bool | str]
