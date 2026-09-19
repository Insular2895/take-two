"""Canonical PRE-OPRA option-pricing boundary.

Prices are per share, volatility and rates are annual decimals, and valuation is
risk-neutral (Q). Whole-contract economics are applied by callers only after an
explicit multiplier and adjustment check.
"""

from __future__ import annotations

import importlib
import math
from datetime import date, datetime
from typing import Any, Literal, TypeAlias

from pydantic import ConfigDict, Field, model_validator

from take_two_options.american import american_scenario_value, european_scenario_value
from take_two_options.domain import ExerciseStyle, OptionType, StrictModel
from take_two_options.knowledge.schemas import MarketSnapshot, QuoteSnapshot
from take_two_options.pricing import black_scholes_price_greeks
from take_two_options.quantitative.contracts import (
    DEFAULT_QUANT_CONVENTIONS,
    EvidenceLevel,
    Measure,
    ModelEligibility,
    VolatilityPolicy,
)

np: Any = importlib.import_module("numpy")
NDArray: TypeAlias = Any


class PricingInputError(ValueError):
    """Raised when required economic evidence is absent or unsupported."""


class DividendCashFlow(StrictModel):
    ex_date: date
    amount: float = Field(gt=0)


class CanonicalMarketState(StrictModel):
    """Provider-independent economic state consumed by all option repricing."""

    risk_free_rate: float | None = None
    risk_free_rate_status: EvidenceLevel
    continuous_dividend_yield: float | None = Field(default=None, ge=0)
    discrete_dividends: tuple[DividendCashFlow, ...] = ()
    dividend_status: EvidenceLevel
    source_ids: tuple[str, ...] = Field(min_length=1)

    @classmethod
    def from_snapshot(cls, snapshot: MarketSnapshot) -> CanonicalMarketState:
        return cls(
            risk_free_rate=snapshot.risk_free_rate,
            risk_free_rate_status=snapshot.risk_free_rate_status,
            continuous_dividend_yield=snapshot.continuous_dividend_yield,
            discrete_dividends=tuple(
                DividendCashFlow(ex_date=item.ex_date, amount=item.amount)
                for item in snapshot.discrete_dividends
            ),
            dividend_status=snapshot.dividend_status,
            source_ids=tuple(snapshot.source_ids),
        )

    def require_pricing_inputs(self) -> tuple[float, float, tuple[tuple[date, float], ...]]:
        if self.risk_free_rate_status not in {
            EvidenceLevel.KNOWN,
            EvidenceLevel.ESTIMATED,
        } or self.risk_free_rate is None:
            raise PricingInputError("BLOCKED_RISK_FREE_RATE_UNKNOWN")
        if self.dividend_status not in {
            EvidenceLevel.KNOWN,
            EvidenceLevel.ESTIMATED,
            EvidenceLevel.NOT_APPLICABLE,
        }:
            raise PricingInputError("BLOCKED_DIVIDEND_INPUT_UNKNOWN")
        dividend_yield = self.continuous_dividend_yield
        if self.dividend_status is EvidenceLevel.NOT_APPLICABLE:
            if dividend_yield is not None or self.discrete_dividends:
                raise PricingInputError("BLOCKED_DIVIDEND_STATUS_CONTRADICTION")
            dividend_yield = 0.0
        elif dividend_yield is None and self.discrete_dividends:
            dividend_yield = 0.0
        elif dividend_yield is None:
            raise PricingInputError("BLOCKED_DIVIDEND_INPUT_UNKNOWN")
        dividends = tuple((item.ex_date, item.amount) for item in self.discrete_dividends)
        return self.risk_free_rate, dividend_yield, dividends


class VolatilityState(StrictModel):
    annual_volatility: float = Field(gt=0, le=5)
    policy: VolatilityPolicy
    evidence: EvidenceLevel
    source_id: str = Field(min_length=1)
    assumptions: tuple[str, ...] = Field(min_length=1)


class PricingResult(StrictModel):
    price_per_share: float = Field(ge=0)
    model_id: str = Field(min_length=1)
    measure: Measure = Measure.RISK_NEUTRAL
    eligibility: ModelEligibility = ModelEligibility.AUTHORITATIVE
    volatility_policy: VolatilityPolicy
    input_evidence: EvidenceLevel
    assumptions: tuple[str, ...]

    @model_validator(mode="after")
    def require_q_measure(self) -> PricingResult:
        if self.measure is not Measure.RISK_NEUTRAL:
            raise ValueError("option pricing must remain under measure Q")
        return self


class VolatilityBatchState(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    annual_volatilities: tuple[float, ...] = Field(min_length=1)
    policy: VolatilityPolicy
    evidence: EvidenceLevel
    source_id: str = Field(min_length=1)
    assumptions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_volatilities(self) -> VolatilityBatchState:
        if any(value <= 0 or not math.isfinite(value) for value in self.annual_volatilities):
            raise ValueError("batch volatilities must be finite and positive")
        return self


class PricingBatchResult(StrictModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    prices_per_share: tuple[float, ...] = Field(min_length=1)
    model_id: str = Field(min_length=1)
    measure: Measure = Measure.RISK_NEUTRAL
    eligibility: ModelEligibility = ModelEligibility.AUTHORITATIVE
    volatility_policy: VolatilityPolicy
    input_evidence: EvidenceLevel
    assumptions: tuple[str, ...]

    @model_validator(mode="after")
    def validate_prices(self) -> PricingBatchResult:
        if self.measure is not Measure.RISK_NEUTRAL:
            raise ValueError("option pricing must remain under measure Q")
        if any(value < 0 or not math.isfinite(value) for value in self.prices_per_share):
            raise ValueError("batch option prices must be finite and non-negative")
        return self


def require_contract_economics(contract: QuoteSnapshot) -> int:
    """Return the multiplier only when contract economics are demonstrably usable."""

    if contract.multiplier_status is not EvidenceLevel.KNOWN or contract.multiplier is None:
        raise PricingInputError("BLOCKED_CONTRACT_MULTIPLIER_UNKNOWN")
    if contract.contract_adjustment_status is not EvidenceLevel.KNOWN:
        raise PricingInputError("BLOCKED_CONTRACT_ADJUSTMENT_UNKNOWN")
    if contract.deliverable_description != "standard listed deliverable":
        raise PricingInputError("BLOCKED_ADJUSTED_CONTRACT_UNSUPPORTED")
    return contract.multiplier


def _fast_domain_supported(
    contract: QuoteSnapshot,
    *,
    rate: float,
    dividend_yield: float,
    dividends: tuple[tuple[date, float], ...],
) -> bool:
    return (
        contract.exercise_style is ExerciseStyle.EUROPEAN and not dividends
    ) or (
        contract.exercise_style is ExerciseStyle.AMERICAN
        and contract.option_type is OptionType.CALL
        and dividend_yield == 0
        and not dividends
        and rate >= 0
    )


def _normal_cdf_batch(values: NDArray) -> NDArray:
    absolute = np.abs(values)
    t = 1.0 / (1.0 + 0.2316419 * absolute)
    density = np.exp(-0.5 * absolute**2) / math.sqrt(2 * math.pi)
    polynomial = t * (
        0.319381530
        + t
        * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429)))
    )
    positive = 1.0 - density * polynomial
    return np.where(values >= 0, positive, 1.0 - positive)


def _fast_bsm_batch(
    *,
    spots: NDArray,
    strike: float,
    time_years: float,
    volatilities: NDArray,
    rate: float,
    dividend_yield: float,
    option_type: OptionType,
) -> NDArray:
    if time_years <= 0:
        intrinsic = (
            np.maximum(spots - strike, 0.0)
            if option_type is OptionType.CALL
            else np.maximum(strike - spots, 0.0)
        )
        return intrinsic
    root_time = math.sqrt(time_years)
    d1 = (
        np.log(spots / strike)
        + (rate - dividend_yield + 0.5 * volatilities**2) * time_years
    ) / (volatilities * root_time)
    d2 = d1 - volatilities * root_time
    discount_r = math.exp(-rate * time_years)
    discount_q = math.exp(-dividend_yield * time_years)
    if option_type is OptionType.CALL:
        prices = spots * discount_q * _normal_cdf_batch(d1) - strike * discount_r * (
            _normal_cdf_batch(d2)
        )
    else:
        prices = strike * discount_r * _normal_cdf_batch(-d2) - spots * discount_q * (
            _normal_cdf_batch(-d1)
        )
    return np.maximum(prices, 0.0)


def price_option_batch(
    contract: QuoteSnapshot,
    market_state: CanonicalMarketState,
    *,
    spots: tuple[float, ...],
    valuation_time: datetime,
    volatility_state: VolatilityBatchState,
) -> PricingBatchResult:
    """Price a batch under the canonical contract; unsupported domains use reference pricing."""
    if contract.exercise_style is None:
        raise PricingInputError("BLOCKED_EXERCISE_STYLE_UNKNOWN")
    require_contract_economics(contract)
    if len(spots) != len(volatility_state.annual_volatilities) or not spots:
        raise PricingInputError("BLOCKED_PRICING_BATCH_SHAPE")
    if any(value <= 0 or not math.isfinite(value) for value in spots):
        raise PricingInputError("BLOCKED_INVALID_SPOT")
    rate, dividend_yield, dividends = market_state.require_pricing_inputs()
    valuation_date = valuation_time.date()
    if _fast_domain_supported(
        contract,
        rate=rate,
        dividend_yield=dividend_yield,
        dividends=dividends,
    ):
        time_years = (
            0.0
            if valuation_date >= contract.expiration
            else DEFAULT_QUANT_CONVENTIONS.calendar_year_fraction(
                valuation_date,
                contract.expiration,
            )
        )
        prices = _fast_bsm_batch(
            spots=np.asarray(spots, dtype=float),
            strike=contract.strike,
            time_years=time_years,
            volatilities=np.asarray(volatility_state.annual_volatilities, dtype=float),
            rate=rate,
            dividend_yield=dividend_yield,
            option_type=contract.option_type,
        )
        equivalence = (
            "Vectorized European BSM in its supported domain"
            if contract.exercise_style is ExerciseStyle.EUROPEAN
            else "Non-dividend American call is equivalent to its European value"
        )
        return PricingBatchResult(
            prices_per_share=tuple(float(value) for value in prices),
            model_id="analytic_bsm_fast_supported",
            volatility_policy=volatility_state.policy,
            input_evidence=volatility_state.evidence,
            assumptions=(*volatility_state.assumptions, equivalence),
        )
    prices = tuple(
        price_option(
            contract,
            market_state,
            spot=spot,
            valuation_time=valuation_time,
            volatility_state=VolatilityState(
                annual_volatility=volatility,
                policy=volatility_state.policy,
                evidence=volatility_state.evidence,
                source_id=volatility_state.source_id,
                assumptions=volatility_state.assumptions,
            ),
        ).price_per_share
        for spot, volatility in zip(
            spots,
            volatility_state.annual_volatilities,
            strict=True,
        )
    )
    return PricingBatchResult(
        prices_per_share=prices,
        model_id="authoritative_batch_fallback",
        volatility_policy=volatility_state.policy,
        input_evidence=volatility_state.evidence,
        assumptions=(
            *volatility_state.assumptions,
            "Unsupported fast domain fell back to authoritative pricing",
        ),
    )


def price_option(
    contract: QuoteSnapshot,
    market_state: CanonicalMarketState,
    *,
    spot: float,
    valuation_time: datetime,
    volatility_state: VolatilityState,
    pricing_mode: Literal["authoritative", "fast_if_supported"] = "authoritative",
) -> PricingResult:
    """Price one vanilla option through the authoritative QuantLib implementation."""

    if spot <= 0:
        raise PricingInputError("BLOCKED_INVALID_SPOT")
    if contract.exercise_style is None:
        raise PricingInputError("BLOCKED_EXERCISE_STYLE_UNKNOWN")
    require_contract_economics(contract)
    rate, dividend_yield, dividends = market_state.require_pricing_inputs()
    valuation_date = valuation_time.date()
    if valuation_date >= contract.expiration:
        intrinsic = (
            max(spot - contract.strike, 0.0)
            if contract.option_type is OptionType.CALL
            else max(contract.strike - spot, 0.0)
        )
        return PricingResult(
            price_per_share=intrinsic,
            model_id="intrinsic_at_expiry",
            volatility_policy=volatility_state.policy,
            input_evidence=volatility_state.evidence,
            assumptions=volatility_state.assumptions,
        )
    if pricing_mode == "fast_if_supported":
        fast_domain = _fast_domain_supported(
            contract,
            rate=rate,
            dividend_yield=dividend_yield,
            dividends=dividends,
        )
        if fast_domain:
            time_years = DEFAULT_QUANT_CONVENTIONS.calendar_year_fraction(
                valuation_date,
                contract.expiration,
            )
            value = black_scholes_price_greeks(
                spot=spot,
                strike=contract.strike,
                time_years=time_years,
                rate=rate,
                volatility=volatility_state.annual_volatility,
                option_type=contract.option_type,
                dividend_yield=dividend_yield,
                measure=Measure.RISK_NEUTRAL,
            ).price
            equivalence = (
                "Analytic European BSM in its supported domain"
                if contract.exercise_style is ExerciseStyle.EUROPEAN
                else "Non-dividend American call is equivalent to its European value"
            )
            return PricingResult(
                price_per_share=max(value, 0.0),
                model_id="analytic_bsm_fast_supported",
                volatility_policy=volatility_state.policy,
                input_evidence=volatility_state.evidence,
                assumptions=(*volatility_state.assumptions, equivalence),
            )
    elif pricing_mode != "authoritative":
        raise PricingInputError("BLOCKED_PRICING_MODE_UNSUPPORTED")
    if contract.exercise_style is ExerciseStyle.AMERICAN:
        value = american_scenario_value(
            spot=spot,
            strike=contract.strike,
            valuation_date=valuation_date,
            expiration_date=contract.expiration,
            option_type=contract.option_type,
            volatility=volatility_state.annual_volatility,
            rate=rate,
            dividend_yield=dividend_yield,
            dividends=dividends,
        )
        model_id = "quantlib_fd_american"
    elif contract.exercise_style is ExerciseStyle.EUROPEAN:
        value = european_scenario_value(
            spot=spot,
            strike=contract.strike,
            valuation_date=valuation_date,
            expiration_date=contract.expiration,
            option_type=contract.option_type,
            volatility=volatility_state.annual_volatility,
            rate=rate,
            dividend_yield=dividend_yield,
            dividends=dividends,
        )
        model_id = "quantlib_fd_european"
    else:  # pragma: no cover - exhaustive enum guard
        raise PricingInputError("BLOCKED_EXERCISE_STYLE_UNSUPPORTED")
    return PricingResult(
        price_per_share=value,
        model_id=model_id,
        volatility_policy=volatility_state.policy,
        input_evidence=volatility_state.evidence,
        assumptions=volatility_state.assumptions,
    )
