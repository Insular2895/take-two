"""Prospective Paper-entry revalidation contracts.

This module has no broker/order capability.  It binds an immutable selected
candidate to fresh market evidence and to the output of the canonical economics
engine.  The broker bridge consumes only a confirmed ticket produced after this
boundary; it never invents research inputs or arbitrary legs.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import ConfigDict, Field, field_validator, model_validator

from take_two_options.models import StrictModel

GLOBAL_PAPER_HARD_CEILING_EUR = 1_500.0


class RevalidationVerdict(StrEnum):
    EXECUTABLE = "EXECUTABLE"
    EXECUTABLE_REPRICE_PROPOSAL = "EXECUTABLE_REPRICE_PROPOSAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REANALYSIS_REQUIRED = "REANALYSIS_REQUIRED"
    BLOCKED = "BLOCKED"


class MaterialDriftStatus(StrEnum):
    WITHIN_POLICY = "WITHIN_POLICY"
    MATERIAL_DRIFT = "MATERIAL_DRIFT"
    REQUIRES_POLICY = "REQUIRES_POLICY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ExecutionEnvironment(StrEnum):
    IBKR_PAPER_SIMULATOR = "IBKR_PAPER_SIMULATOR"


class MarketDataType(StrEnum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    FROZEN = "FROZEN"
    DELAYED_FROZEN = "DELAYED_FROZEN"
    NOT_SUBSCRIBED = "NOT_SUBSCRIBED"
    UNKNOWN = "UNKNOWN"


class ComboGuaranteeMode(StrEnum):
    GUARANTEED = "GUARANTEED"
    NON_GUARANTEED = "NON_GUARANTEED"
    UNKNOWN = "UNKNOWN"


class ImmutableModel(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=True,
        populate_by_name=True,
    )


def canonical_hash(value: Any) -> str:
    if isinstance(value, StrictModel):
        value = value.model_dump(mode="json")
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


class ExecutionLegIdentity(ImmutableModel):
    con_id: int = Field(gt=0)
    local_symbol: str = Field(min_length=1)
    trading_class: str = Field(min_length=1)
    expiration: str = Field(pattern=r"^\d{8}$")
    strike: float = Field(gt=0)
    right: str = Field(pattern=r"^[CP]$")
    multiplier: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    exchange: str = Field(min_length=1)
    ratio: int = Field(gt=0)
    application_action: str = Field(pattern=r"^(BUY_TO_OPEN|SELL_TO_OPEN)$")
    wire_action: str = Field(pattern=r"^(BUY|SELL)$")

    @model_validator(mode="after")
    def application_and_wire_directions_agree(self) -> ExecutionLegIdentity:
        expected = "BUY" if self.application_action == "BUY_TO_OPEN" else "SELL"
        if self.wire_action != expected:
            raise ValueError("application open intent and IBKR wire action disagree")
        return self


class FiveScoreSnapshot(ImmutableModel):
    opportunity: float | None = Field(default=None, ge=0, le=100)
    risk: float | None = Field(default=None, ge=0, le=100)
    evidence: float | None = Field(default=None, ge=0, le=100)
    model_agreement: float | None = Field(default=None, ge=0, le=100)
    execution_quality: float | None = Field(default=None, ge=0, le=100)
    formula_version: str = Field(min_length=1)


class GreekVector(ImmutableModel):
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None
    rho: float | None = None
    vanna: float | None = None
    vomma: float | None = None
    charm: float | None = None
    veta: float | None = None
    speed: float | None = None
    color: float | None = None
    lambda_value: float | None = Field(default=None, alias="lambda")

    @field_validator("*", mode="before")
    @classmethod
    def finite_optional(cls, value: object) -> object:
        if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError("Greek values must be finite or null")
        return value


class ExecutionMarketSnapshot(ImmutableModel):
    snapshot_id: str = Field(min_length=1)
    captured_at: datetime
    ticker: str = Field(pattern=r"^TTWO$")
    spot: float = Field(gt=0)
    market_data_type: MarketDataType
    underlying_timestamp: datetime
    leg_timestamps: dict[int, datetime]
    leg_bid_ask: dict[int, tuple[float, float]]
    leg_implied_volatility: dict[int, float]
    provider_leg_greeks: dict[int, GreekVector | None]
    combo_bid: float | None = Field(default=None, ge=0)
    combo_ask: float | None = Field(default=None, ge=0)
    combo_timestamp: datetime | None = None
    synthetic_combo_bid: float | None = Field(default=None, ge=0)
    synthetic_combo_ask: float | None = Field(default=None, ge=0)
    signed_price_convention_verified: bool = False
    fx_rate_to_eur: float | None = Field(default=None, gt=0)
    fx_timestamp: datetime | None = None
    rate_curve_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    dividend_input_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    open_interest: dict[int, int | None]
    volume: dict[int, int | None]
    bid_size: dict[int, int | None]
    ask_size: dict[int, int | None]
    trading_hours: str = Field(min_length=1)
    liquid_hours: str = Field(min_length=1)
    time_zone_id: str = Field(min_length=1)
    quote_age_seconds: float = Field(ge=0)
    underlying_fresh: bool
    option_leg_freshness: dict[int, bool]
    bag_fresh: bool
    fx_fresh: bool | None = None
    rate_inputs_fresh: bool
    dividend_inputs_fresh: bool
    required_inputs_fresh: bool

    @field_validator("captured_at", "underlying_timestamp", "combo_timestamp", "fx_timestamp")
    @classmethod
    def timezone_required(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("market timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_market_components(self) -> ExecutionMarketSnapshot:
        if self.combo_bid is not None and self.combo_ask is not None:
            if self.combo_bid > self.combo_ask:
                raise ValueError("combo bid cannot exceed combo ask")
            if self.combo_timestamp is None:
                raise ValueError("combo timestamp is required with a BAG quote")
        for con_id, (bid, ask) in self.leg_bid_ask.items():
            if con_id <= 0 or bid < 0 or ask < bid:
                raise ValueError("invalid option-leg quote")
        required = set(self.leg_bid_ask)
        if not required or not required.issubset(self.leg_timestamps):
            raise ValueError("every quoted leg requires its provider timestamp")
        if not required.issubset(self.leg_implied_volatility):
            raise ValueError("every quoted leg requires current IV")
        if not required.issubset(self.option_leg_freshness):
            raise ValueError("every quoted leg requires explicit freshness evidence")
        return self

    @property
    def evidence_hash(self) -> str:
        return canonical_hash(self)

    @property
    def liquidity_spread(self) -> float | None:
        if self.combo_bid is None or self.combo_ask is None:
            return None
        return self.combo_ask - self.combo_bid


class ExecutionEconomicsSnapshot(ImmutableModel):
    source_engine_version: str = Field(min_length=1)
    proposed_combo_limit: float = Field(ge=0)
    cash_flow_type: str = Field(pattern=r"^(DEBIT|CREDIT)$")
    signed_entry_cash_flow: float
    expected_commissions: float | None = Field(default=None, ge=0)
    slippage_estimate: float | None = Field(default=None, ge=0)
    fx_transaction_cost: float | None = Field(default=None, ge=0)
    capital_required: float | None = Field(default=None, ge=0)
    broker_buying_power_requirement: float | None = Field(default=None, ge=0)
    max_loss: float | None = Field(default=None, ge=0)
    max_profit: float | None = Field(default=None, ge=0)
    breakevens: tuple[float, ...] = ()
    expected_pnl: float | None = None
    expected_return: float | None = None
    probability_profit: float | None = Field(default=None, ge=0, le=1)
    probability_loss: float | None = Field(default=None, ge=0, le=1)
    var_95: float | None = Field(default=None, ge=0)
    cvar_95: float | None = Field(default=None, ge=0)
    return_on_capital: float | None = None
    return_on_risk: float | None = None
    theta_per_capital_day: float | None = None
    greeks: GreekVector
    flat_spot_pnl: dict[str, float | None]
    spot_time_iv_matrix_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    volatility_shock_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    event_crush_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    touch_probabilities: dict[str, float | None]
    liquidity_diagnostics: dict[str, float | int | str | None]
    five_scores: FiveScoreSnapshot

    @field_validator(
        "signed_entry_cash_flow",
        "expected_pnl",
        "expected_return",
        "return_on_capital",
        "return_on_risk",
        "theta_per_capital_day",
    )
    @classmethod
    def finite_optional_metrics(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("economics values must be finite or null")
        return value


class SelectedExecutionContext(ImmutableModel):
    original_analysis_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    selection_id: str = Field(min_length=1)
    dossier_id: str = Field(min_length=1)
    original_trade_economics_ticket_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_market_snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    structure_type: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    policy_currency: str = Field(default="EUR", min_length=3, max_length=3)
    legs: tuple[ExecutionLegIdentity, ...]
    structure_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_market: ExecutionMarketSnapshot
    original_economics: ExecutionEconomicsSnapshot
    analysis_hard_ceiling_eur: float = Field(gt=0, le=GLOBAL_PAPER_HARD_CEILING_EUR)

    @model_validator(mode="after")
    def verify_structure_hash(self) -> SelectedExecutionContext:
        identity = {
            "structure_type": self.structure_type,
            "quantity": self.quantity,
            "legs": [leg.model_dump(mode="json") for leg in self.legs],
        }
        if canonical_hash(identity) != self.structure_hash:
            raise ValueError("structure hash does not match immutable candidate shape")
        if self.original_market.evidence_hash != self.original_market_snapshot_hash:
            raise ValueError("original market snapshot hash mismatch")
        required_con_ids = {leg.con_id for leg in self.legs}
        market_maps = (
            self.original_market.leg_timestamps,
            self.original_market.leg_bid_ask,
            self.original_market.leg_implied_volatility,
            self.original_market.provider_leg_greeks,
            self.original_market.open_interest,
            self.original_market.volume,
            self.original_market.bid_size,
            self.original_market.ask_size,
            self.original_market.option_leg_freshness,
        )
        if not required_con_ids or any(set(values) != required_con_ids for values in market_maps):
            raise ValueError("original market must cover exactly every selected option leg")
        return self


class MaterialExecutionDriftPolicy(ImmutableModel):
    policy_version: str = Field(min_length=1)
    max_expected_pnl_deterioration: float | None = Field(default=None, ge=0)
    max_expected_return_deterioration: float | None = Field(default=None, ge=0)
    max_probability_profit_deterioration: float | None = Field(default=None, ge=0, le=1)
    max_cvar_increase: float | None = Field(default=None, ge=0)
    max_loss_increase: float | None = Field(default=None, ge=0)
    max_capital_increase: float | None = Field(default=None, ge=0)
    max_reward_risk_deterioration: float | None = Field(default=None, ge=0)
    max_spread_increase: float | None = Field(default=None, ge=0)
    max_spot_move_fraction: float | None = Field(default=None, ge=0)
    max_leg_iv_absolute_change: float | None = Field(default=None, ge=0)
    max_five_score_deterioration: float | None = Field(default=None, ge=0)
    max_execution_quality_deterioration: float | None = Field(default=None, ge=0)
    max_analysis_age_seconds: int | None = Field(default=None, gt=0)

    @property
    def configured(self) -> bool:
        return any(
            value is not None
            for name, value in self.model_dump().items()
            if name != "policy_version"
        )


class DriftEvaluation(ImmutableModel):
    status: MaterialDriftStatus
    policy_version: str
    breached_metrics: tuple[str, ...] = ()
    observed_deltas: dict[str, float | None]


class ReanalysisRequest(ImmutableModel):
    original_analysis_id: str
    original_candidate_id: str
    original_rank: int | None = Field(default=None, gt=0)
    current_market_snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reason_codes: tuple[str, ...]
    preserve_original_artifacts: bool = True


class ExecutionRevalidationTicket(ImmutableModel):
    schema_version: str = "execution-revalidation/1.0"
    ticket_id: str = Field(pattern=r"^execution-revalidation-[a-f0-9]{16}$")
    created_at: datetime
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.IBKR_PAPER_SIMULATOR
    original_analysis_id: str
    candidate_id: str
    selection_id: str
    dossier_id: str
    original_trade_economics_ticket_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    original_market_snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_market_snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    current_git_commit: str = Field(pattern=r"^[a-f0-9]{7,40}$")
    current_config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    previous_execution_ticket_id: str | None = None
    structure_type: str = Field(min_length=1)
    structure_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    quantity: int = Field(gt=0)
    legs: tuple[ExecutionLegIdentity, ...]
    proposed_limit: float = Field(gt=0)
    valid_tick: float | None = Field(default=None, gt=0)
    rounded_from_limit: float | None = Field(default=None, ge=0)
    combo_submission_mode: str = Field(pattern=r"^WHOLE_BAG$")
    broker_combo_guarantee_mode: ComboGuaranteeMode
    original_market: ExecutionMarketSnapshot
    original_economics: ExecutionEconomicsSnapshot
    current_market: ExecutionMarketSnapshot
    proposed_execution_economics: ExecutionEconomicsSnapshot
    deltas: dict[str, float | None]
    material_drift: DriftEvaluation
    verdict: RevalidationVerdict
    blockers: tuple[str, ...]
    reanalysis_request: ReanalysisRequest | None = None
    human_confirmation_required: bool = True
    automatic_repricing_allowed: bool = False
    live_execution_allowed: bool = False

    @field_validator("created_at")
    @classmethod
    def created_at_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("ticket timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def enforce_fail_closed_flags(self) -> ExecutionRevalidationTicket:
        if not self.human_confirmation_required:
            raise ValueError("human confirmation is mandatory")
        if self.automatic_repricing_allowed or self.live_execution_allowed:
            raise ValueError("automatic repricing and live execution remain forbidden")
        if (
            self.verdict is RevalidationVerdict.REANALYSIS_REQUIRED
            and self.reanalysis_request is None
        ):
            raise ValueError("reanalysis verdict requires an immutable request")
        return self

    @property
    def ticket_hash(self) -> str:
        return canonical_hash(self)


class CanonicalEconomicsRecalculator(Protocol):
    def reprice_same_structure(
        self,
        context: SelectedExecutionContext,
        market: ExecutionMarketSnapshot,
        proposed_limit: float,
    ) -> ExecutionEconomicsSnapshot: ...


class FreshMarketProvider(Protocol):
    def refresh(self, context: SelectedExecutionContext) -> ExecutionMarketSnapshot: ...


class CandidateUniverseRerunner(Protocol):
    def rerun(
        self,
        request: ReanalysisRequest,
        market: ExecutionMarketSnapshot,
    ) -> dict[str, Any]: ...


def _worse_decrease(original: float | None, current: float | None) -> float | None:
    return None if original is None or current is None else max(original - current, 0.0)


def _worse_increase(original: float | None, current: float | None) -> float | None:
    return None if original is None or current is None else max(current - original, 0.0)


def evaluate_material_drift(
    context: SelectedExecutionContext,
    market: ExecutionMarketSnapshot,
    economics: ExecutionEconomicsSnapshot,
    policy: MaterialExecutionDriftPolicy,
    now: datetime,
) -> DriftEvaluation:
    original = context.original_economics
    original_spread = context.original_market.liquidity_spread
    current_spread = market.liquidity_spread
    shared_iv_legs = set(context.original_market.leg_implied_volatility).intersection(
        market.leg_implied_volatility
    )
    maximum_iv_change = (
        max(
            abs(
                market.leg_implied_volatility[con_id]
                - context.original_market.leg_implied_volatility[con_id]
            )
            for con_id in shared_iv_legs
        )
        if shared_iv_legs
        else None
    )
    score_names = (
        "opportunity",
        "risk",
        "evidence",
        "model_agreement",
        "execution_quality",
    )
    score_deteriorations = [
        deterioration
        for name in score_names
        if (
            deterioration := _worse_decrease(
                getattr(original.five_scores, name),
                getattr(economics.five_scores, name),
            )
        )
        is not None
    ]
    deltas: dict[str, float | None] = {
        "expected_pnl_deterioration": _worse_decrease(
            original.expected_pnl, economics.expected_pnl
        ),
        "expected_return_deterioration": _worse_decrease(
            original.expected_return, economics.expected_return
        ),
        "probability_profit_deterioration": _worse_decrease(
            original.probability_profit, economics.probability_profit
        ),
        "cvar_increase": _worse_increase(original.cvar_95, economics.cvar_95),
        "max_loss_increase": _worse_increase(original.max_loss, economics.max_loss),
        "capital_increase": _worse_increase(original.capital_required, economics.capital_required),
        "reward_risk_deterioration": _worse_decrease(
            original.return_on_risk, economics.return_on_risk
        ),
        "spread_increase": _worse_increase(original_spread, current_spread),
        "spot_move_fraction": abs(market.spot / context.original_market.spot - 1.0),
        "maximum_leg_iv_absolute_change": maximum_iv_change,
        "maximum_five_score_deterioration": (
            max(score_deteriorations) if score_deteriorations else None
        ),
        "execution_quality_deterioration": _worse_decrease(
            original.five_scores.execution_quality,
            economics.five_scores.execution_quality,
        ),
        "analysis_age_seconds": max(
            (
                now.astimezone(UTC) - context.original_market.captured_at.astimezone(UTC)
            ).total_seconds(),
            0.0,
        ),
    }
    if not policy.configured:
        return DriftEvaluation(
            status=MaterialDriftStatus.REQUIRES_POLICY,
            policy_version=policy.policy_version,
            observed_deltas=deltas,
        )
    thresholds = {
        "expected_pnl_deterioration": policy.max_expected_pnl_deterioration,
        "expected_return_deterioration": policy.max_expected_return_deterioration,
        "probability_profit_deterioration": policy.max_probability_profit_deterioration,
        "cvar_increase": policy.max_cvar_increase,
        "max_loss_increase": policy.max_loss_increase,
        "capital_increase": policy.max_capital_increase,
        "reward_risk_deterioration": policy.max_reward_risk_deterioration,
        "spread_increase": policy.max_spread_increase,
        "spot_move_fraction": policy.max_spot_move_fraction,
        "maximum_leg_iv_absolute_change": policy.max_leg_iv_absolute_change,
        "maximum_five_score_deterioration": policy.max_five_score_deterioration,
        "execution_quality_deterioration": policy.max_execution_quality_deterioration,
        "analysis_age_seconds": (
            float(policy.max_analysis_age_seconds)
            if policy.max_analysis_age_seconds is not None
            else None
        ),
    }
    missing = [
        name
        for name, limit in thresholds.items()
        if limit is not None and deltas[name] is None
    ]
    if missing:
        return DriftEvaluation(
            status=MaterialDriftStatus.INSUFFICIENT_EVIDENCE,
            policy_version=policy.policy_version,
            breached_metrics=tuple(missing),
            observed_deltas=deltas,
        )
    breached_items: list[str] = []
    for name, limit in thresholds.items():
        observed = deltas[name]
        if limit is not None and observed is not None and observed > limit:
            breached_items.append(name)
    breached = tuple(breached_items)
    return DriftEvaluation(
        status=(
            MaterialDriftStatus.MATERIAL_DRIFT
            if breached
            else MaterialDriftStatus.WITHIN_POLICY
        ),
        policy_version=policy.policy_version,
        breached_metrics=breached,
        observed_deltas=deltas,
    )


def _metric_deltas(
    original: ExecutionEconomicsSnapshot,
    current: ExecutionEconomicsSnapshot,
) -> dict[str, float | None]:
    names = (
        "expected_pnl",
        "expected_return",
        "probability_profit",
        "max_loss",
        "capital_required",
        "cvar_95",
        "return_on_risk",
        "theta_per_capital_day",
    )
    deltas = {
        name: (
            None
            if getattr(original, name) is None or getattr(current, name) is None
            else float(getattr(current, name)) - float(getattr(original, name))
        )
        for name in names
    }
    original_breakeven = original.breakevens[0] if original.breakevens else None
    current_breakeven = current.breakevens[0] if current.breakevens else None
    deltas["primary_breakeven"] = (
        None
        if original_breakeven is None or current_breakeven is None
        else current_breakeven - original_breakeven
    )
    for name in (
        "opportunity",
        "risk",
        "evidence",
        "model_agreement",
        "execution_quality",
    ):
        original_score = getattr(original.five_scores, name)
        current_score = getattr(current.five_scores, name)
        deltas[f"five_score_{name}"] = (
            None
            if original_score is None or current_score is None
            else current_score - original_score
        )
    return deltas


class ExecutionRevalidationService:
    """Refresh market data and invoke the existing canonical engine for every proposal."""

    def __init__(
        self,
        market_provider: FreshMarketProvider,
        economics_engine: CanonicalEconomicsRecalculator,
    ) -> None:
        self._market_provider = market_provider
        self._economics_engine = economics_engine

    def build_ticket(
        self,
        context: SelectedExecutionContext,
        *,
        proposed_limit: float,
        valid_tick: float | None,
        drift_policy: MaterialExecutionDriftPolicy,
        now: datetime,
        is_reprice: bool,
        previous_ticket_id: str | None = None,
        broker_combo_guarantee_mode: ComboGuaranteeMode = ComboGuaranteeMode.UNKNOWN,
        rounded_from_limit: float | None = None,
    ) -> ExecutionRevalidationTicket:
        if now.tzinfo is None:
            raise ValueError("revalidation time must include a timezone")
        market = self._market_provider.refresh(context)
        economics = self._economics_engine.reprice_same_structure(
            context,
            market,
            proposed_limit,
        )
        blockers: list[str] = []
        required_con_ids = {leg.con_id for leg in context.legs}
        market_maps = (
            market.leg_timestamps,
            market.leg_bid_ask,
            market.leg_implied_volatility,
            market.provider_leg_greeks,
            market.open_interest,
            market.volume,
            market.bid_size,
            market.ask_size,
            market.option_leg_freshness,
        )
        if any(set(values) != required_con_ids for values in market_maps):
            blockers.append("OPTION_LEG_MARKET_COVERAGE_MISMATCH")
        if market.market_data_type is not MarketDataType.LIVE:
            blockers.append("MARKET_DATA_NOT_LIVE")
        if not market.required_inputs_fresh:
            blockers.append("REPRICE_UNAVAILABLE_DATA_STALE")
        if not market.underlying_fresh:
            blockers.append("UNDERLYING_QUOTE_STALE")
        if not all(market.option_leg_freshness.values()):
            blockers.append("OPTION_LEG_QUOTE_STALE")
        if not market.bag_fresh:
            blockers.append("BAG_QUOTE_STALE")
        if not market.rate_inputs_fresh:
            blockers.append("RATE_INPUTS_STALE")
        if not market.dividend_inputs_fresh:
            blockers.append("DIVIDEND_INPUTS_STALE")
        fx_required = any(
            leg.currency.upper() != context.policy_currency.upper() for leg in context.legs
        )
        if fx_required and (
            market.fx_rate_to_eur is None
            or market.fx_timestamp is None
            or market.fx_fresh is not True
        ):
            blockers.append("FX_EVIDENCE_REQUIRED")
        if market.combo_bid is None or market.combo_ask is None or market.combo_timestamp is None:
            blockers.append("MISSING_BAG_QUOTE")
        if not market.signed_price_convention_verified:
            blockers.append("UNVERIFIED_SIGNED_PRICE_CONVENTION")
        if valid_tick is None or valid_tick <= 0:
            blockers.append("MARKET_RULE_TICK_UNAVAILABLE")
        elif not math.isclose(
            proposed_limit / valid_tick,
            round(proposed_limit / valid_tick),
            abs_tol=1e-8,
        ):
            blockers.append("INVALID_MARKET_RULE_TICK")
        capital = economics.capital_required
        effective_ceiling = min(context.analysis_hard_ceiling_eur, GLOBAL_PAPER_HARD_CEILING_EUR)
        if capital is None:
            blockers.append("CAPITAL_REQUIREMENT_UNKNOWN")
        elif capital > effective_ceiling + 1e-9:
            blockers.append("HARD_BUDGET_EXCEEDED")
        if economics.max_loss is None:
            blockers.append("MAX_LOSS_UNKNOWN")
        if economics.expected_commissions is None:
            blockers.append("COMMISSION_UNKNOWN")
        if market.evidence_hash == context.original_market_snapshot_hash:
            if economics.greeks != context.original_economics.greeks:
                blockers.append("GREEKS_CHANGED_WITHOUT_MARKET_CHANGE")
        drift = evaluate_material_drift(context, market, economics, drift_policy, now)
        reanalysis: ReanalysisRequest | None = None
        if blockers:
            verdict = RevalidationVerdict.BLOCKED
        elif drift.status is MaterialDriftStatus.MATERIAL_DRIFT:
            verdict = RevalidationVerdict.REANALYSIS_REQUIRED
            reanalysis = ReanalysisRequest(
                original_analysis_id=context.original_analysis_id,
                original_candidate_id=context.candidate_id,
                current_market_snapshot_hash=market.evidence_hash,
                reason_codes=drift.breached_metrics,
            )
        elif is_reprice and drift.status in {
            MaterialDriftStatus.REQUIRES_POLICY,
            MaterialDriftStatus.INSUFFICIENT_EVIDENCE,
        }:
            verdict = RevalidationVerdict.REVIEW_REQUIRED
        else:
            verdict = (
                RevalidationVerdict.EXECUTABLE_REPRICE_PROPOSAL
                if is_reprice
                else RevalidationVerdict.EXECUTABLE
            )
        seed = {
            "context": context.structure_hash,
            "market": market.evidence_hash,
            "limit": proposed_limit,
            "previous": previous_ticket_id,
            "created_at": now.astimezone(UTC).isoformat(),
        }
        metric_deltas = _metric_deltas(context.original_economics, economics)
        metric_deltas["bag_spread"] = (
            None
            if context.original_market.liquidity_spread is None
            or market.liquidity_spread is None
            else market.liquidity_spread - context.original_market.liquidity_spread
        )
        return ExecutionRevalidationTicket(
            ticket_id=f"execution-revalidation-{canonical_hash(seed)[:16]}",
            created_at=now,
            original_analysis_id=context.original_analysis_id,
            candidate_id=context.candidate_id,
            selection_id=context.selection_id,
            dossier_id=context.dossier_id,
            original_trade_economics_ticket_hash=context.original_trade_economics_ticket_hash,
            original_market_snapshot_hash=context.original_market_snapshot_hash,
            current_market_snapshot_hash=market.evidence_hash,
            current_git_commit=context.git_commit,
            current_config_hash=context.config_hash,
            previous_execution_ticket_id=previous_ticket_id,
            structure_type=context.structure_type,
            structure_hash=context.structure_hash,
            quantity=context.quantity,
            legs=context.legs,
            proposed_limit=proposed_limit,
            valid_tick=valid_tick,
            rounded_from_limit=rounded_from_limit,
            combo_submission_mode="WHOLE_BAG",
            broker_combo_guarantee_mode=broker_combo_guarantee_mode,
            original_market=context.original_market,
            original_economics=context.original_economics,
            current_market=market,
            proposed_execution_economics=economics,
            deltas=metric_deltas,
            material_drift=drift,
            verdict=verdict,
            blockers=tuple(blockers),
            reanalysis_request=reanalysis,
        )

    @staticmethod
    def rerun_universe_if_required(
        ticket: ExecutionRevalidationTicket,
        rerunner: CandidateUniverseRerunner,
    ) -> dict[str, Any]:
        if ticket.verdict is not RevalidationVerdict.REANALYSIS_REQUIRED:
            raise ValueError("candidate universe rerun requires REANALYSIS_REQUIRED")
        assert ticket.reanalysis_request is not None
        result = rerunner.rerun(ticket.reanalysis_request, ticket.current_market)
        if result.get("original_artifacts_preserved") is not True:
            raise ValueError("reanalysis must preserve original decision artifacts")
        return result
