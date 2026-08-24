"""Immutable export contract consumed by the Cloudflare monitoring projection."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.models import StrictModel


class CloudPositionState(StrEnum):
    PLANNED = "PLANNED"
    PAPER_OPEN = "PAPER_OPEN"
    LIVE_ASSISTED_OPEN = "LIVE_ASSISTED_OPEN"


class CloudLegSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class CloudCloseAction(StrEnum):
    SELL_TO_CLOSE = "SELL_TO_CLOSE"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"


class CloudFXCostStatus(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    KNOWN = "KNOWN"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class CloudPositionLeg(StrictModel):
    leg_id: str = Field(min_length=1)
    contract_identity: str = Field(min_length=1)
    con_id: int | None = Field(default=None, gt=0)
    local_symbol: str | None = None
    underlying: str = Field(min_length=1)
    instrument_type: Literal["option"] = "option"
    side: CloudLegSide
    close_action: CloudCloseAction
    ratio: int = Field(gt=0)
    quantity: int = Field(gt=0)
    multiplier: float = Field(gt=0)
    option_right: Literal["CALL", "PUT"]
    strike: float = Field(gt=0)
    expiration: datetime
    entry_bid: float = Field(ge=0)
    entry_ask: float = Field(ge=0)
    entry_mid: float = Field(ge=0)
    entry_executable_price: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_identity_and_close_direction(self) -> CloudPositionLeg:
        if self.con_id is None and not self.local_symbol:
            raise ValueError("every cloud position leg requires con_id or local_symbol")
        expected = (
            CloudCloseAction.SELL_TO_CLOSE
            if self.side is CloudLegSide.LONG
            else CloudCloseAction.BUY_TO_CLOSE
        )
        if self.close_action is not expected:
            raise ValueError("close action must be the exact inverse of the open leg")
        if self.entry_bid > self.entry_ask:
            raise ValueError("entry bid cannot exceed entry ask")
        return self


class CloudFXContext(StrictModel):
    rate_to_policy_currency: float | None = Field(default=None, gt=0)
    rate_source: str | None = None
    rate_timestamp: datetime | None = None
    transaction_cost: float | None = Field(default=None, ge=0)
    transaction_cost_status: CloudFXCostStatus
    transaction_cost_source: str | None = None

    @model_validator(mode="after")
    def prevent_unknown_zero(self) -> CloudFXContext:
        if (
            self.transaction_cost_status is CloudFXCostStatus.UNKNOWN
            and self.transaction_cost is not None
        ):
            raise ValueError("unknown FX transaction cost must remain null")
        if (
            self.transaction_cost_status is CloudFXCostStatus.NOT_APPLICABLE
            and self.transaction_cost != 0
        ):
            raise ValueError("not-applicable FX transaction cost must be explicit zero")
        return self


class CloudScoreValue(StrictModel):
    score_value: float
    coverage: float = Field(ge=0, le=1)
    confidence: str = Field(min_length=1)
    formula_version: str = Field(min_length=1)


class CloudFiveScoreSnapshot(StrictModel):
    opportunity: CloudScoreValue
    risk: CloudScoreValue
    evidence: CloudScoreValue
    model_agreement: CloudScoreValue
    execution_quality: CloudScoreValue
    source: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    timestamp: datetime


class CloudModelSnapshot(StrictModel):
    timestamp: datetime
    source: str = Field(min_length=1)
    status: str = Field(min_length=1)
    expected_remaining_pnl: float | None = None
    probability_profit: float | None = Field(default=None, ge=0, le=1)
    loss_probabilities: dict[str, float] = Field(default_factory=dict)
    var_95: float | None = Field(default=None, ge=0)
    cvar_95: float | None = Field(default=None, ge=0)
    assumptions: list[str] = Field(default_factory=list)

    @field_validator("loss_probabilities")
    @classmethod
    def validate_probabilities(cls, value: dict[str, float]) -> dict[str, float]:
        if any(probability < 0 or probability > 1 for probability in value.values()):
            raise ValueError("model probabilities must be in [0, 1]")
        return value


class CloudFlatSpotDiagnostics(StrictModel):
    timestamp: datetime
    source: str = Field(min_length=1)
    flat_spot_7d: float | None = None
    flat_spot_30d: float | None = None
    flat_spot_60d: float | None = None
    flat_spot_90d: float | None = None


class CloudExitRule(StrictModel):
    rule_id: str = Field(min_length=1)
    threshold: float | int | str | bool
    suggested_action: Literal[
        "HOLD",
        "WATCH",
        "REDUCE",
        "EXIT_REVIEW",
        "THESIS_INVALIDATED",
        "DATA_STALE",
        "BLOCKED_INSUFFICIENT_DATA",
    ]


class CloudExitPlan(StrictModel):
    status: Literal["CONFIGURED", "NOT_CONFIGURED"]
    profit_target: float | None = Field(default=None, gt=0)
    partial_profit_target: float | None = Field(default=None, gt=0)
    operational_stop_loss: float | None = Field(default=None, gt=0, le=1)
    exit_days_before_expiration: int | None = Field(default=None, ge=0)
    iv_crush_threshold: float | None = Field(default=None, gt=0, le=1)
    trailing_drawdown: float | None = Field(default=None, gt=0, le=1)
    rules: list[CloudExitRule] = Field(default_factory=list)
    human_review_required: Literal[True] = True


class CloudQuote(StrictModel):
    contract_identity: str = Field(min_length=1)
    bid: float = Field(ge=0)
    ask: float = Field(ge=0)
    timestamp: datetime
    provider: str = Field(min_length=1)
    source: str = Field(min_length=1)
    quality: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_quote(self) -> CloudQuote:
        if self.bid > self.ask:
            raise ValueError("quote bid cannot exceed ask")
        return self


class CloudImportedMonitoringSnapshot(StrictModel):
    timestamp: datetime
    underlying_timestamp: datetime
    provider: str = Field(min_length=1)
    source: str = Field(min_length=1)
    quality: str = Field(min_length=1)
    synthetic: bool = False
    spot: float = Field(gt=0)
    option_quotes: list[CloudQuote] = Field(min_length=1)
    fx_rate_to_policy_currency: float | None = Field(default=None, gt=0)
    fx_source: str | None = None
    fx_timestamp: datetime | None = None
    estimated_exit_commission: float | None = Field(default=None, ge=0)
    estimated_exit_slippage: float | None = Field(default=None, ge=0)
    estimated_exit_fx: float | None = Field(default=None, ge=0)
    estimated_exit_fx_status: CloudFXCostStatus = CloudFXCostStatus.UNKNOWN
    current_iv: float | None = Field(default=None, gt=0)
    current_greeks: dict[str, float] = Field(default_factory=dict)
    thesis_invalidated: bool = False
    data_sufficient: bool = True


class CloudPositionDossier(StrictModel):
    schema_version: Literal["1.1"] = "1.1"
    fixture_status: Literal[
        "CANONICAL_EXPORT",
        "SYNTHETIC_DEMO",
    ] = "CANONICAL_EXPORT"
    dossier_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    created_at: datetime
    opened_at: datetime
    initial_position_state: CloudPositionState
    ticker: str = Field(min_length=1)
    structure_name: str = Field(min_length=1)
    structure_type: str = Field(min_length=1)
    legs: list[CloudPositionLeg] = Field(min_length=1)
    quantity: int = Field(gt=0)
    multiplier: float = Field(gt=0)
    entry_native_currency: str = Field(min_length=3, max_length=3)
    policy_currency: str = Field(min_length=3, max_length=3)
    entry_cash_flow_policy: float = Field(
        description=(
            "Signed opening account cash flow in policy currency: positive cash received, "
            "negative cash paid; all known entry costs are included exactly once."
        )
    )
    capital_required_policy: float = Field(
        ge=0,
        description=(
            "Governed non-negative capital requirement in policy currency; never a PnL basis."
        ),
    )
    actual_entry_fx: CloudFXContext
    actual_entry_commissions: float = Field(ge=0)
    actual_entry_slippage: float = Field(ge=0)
    initial_spot: float = Field(gt=0)
    initial_iv: dict[str, float] = Field(min_length=1)
    initial_greeks: dict[str, float] = Field(min_length=1)
    expirations: list[datetime] = Field(min_length=1)
    managed_exit_deadline: datetime | None = None
    initial_scenario_probabilities: dict[str, float] | None = None
    latest_promoted_model_snapshot: CloudModelSnapshot | None = None
    flat_spot_diagnostics: CloudFlatSpotDiagnostics | None = None
    five_scores: CloudFiveScoreSnapshot | None = None
    budget_diagnostics: dict[str, Any]
    exit_plan: CloudExitPlan
    last_imported_snapshot: CloudImportedMonitoringSnapshot | None = None
    trade_economics_ticket_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    trade_economics_schema_version: str = Field(min_length=1)
    phase_m_context_id: str | None = Field(
        default=None,
        pattern=r"^phase-m-context-[a-f0-9]{16}$",
    )
    phase_m_context_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    git_commit: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    config_hash_source: str = Field(min_length=1)
    market_snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    market_snapshot_hash_source: str = Field(min_length=1)
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    human_confirmation_required: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("entry_native_currency", "policy_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("initial_scenario_probabilities")
    @classmethod
    def validate_scenario_probabilities(
        cls, value: dict[str, float] | None
    ) -> dict[str, float] | None:
        if value is None:
            return None
        if any(probability < 0 or probability > 1 for probability in value.values()):
            raise ValueError("scenario probabilities must be in [0, 1]")
        if abs(sum(value.values()) - 1.0) > 1e-8:
            raise ValueError("scenario probabilities must sum to one")
        return value

    @model_validator(mode="after")
    def validate_structure_integrity(self) -> CloudPositionDossier:
        identities = [leg.contract_identity for leg in self.legs]
        if len(set(identities)) != len(identities):
            raise ValueError("cloud dossier leg identities must be unique")
        if any(leg.quantity != leg.ratio * self.quantity for leg in self.legs):
            raise ValueError("leg quantity must equal exact ratio times structure quantity")
        if any(leg.multiplier != self.multiplier for leg in self.legs):
            raise ValueError("all dossier legs must use the declared structure multiplier")
        leg_expirations = sorted({leg.expiration for leg in self.legs})
        if sorted(set(self.expirations)) != leg_expirations:
            raise ValueError("dossier expirations must exactly match leg expirations")
        if not self.read_only or self.transmit or not self.what_if:
            raise ValueError("cloud dossier violates the read-only safety boundary")
        return self
