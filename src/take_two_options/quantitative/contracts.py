"""Central conventions, observation provenance, and probability-measure contracts."""

from __future__ import annotations

import math
from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from take_two_options.domain import StrictModel

CALENDAR_DAYS_PER_YEAR = 365.0
TRADING_SESSIONS_PER_YEAR = 252.0


class Measure(StrEnum):
    """Probability measure attached to a model input or output."""

    REAL_WORLD = "P"
    RISK_NEUTRAL = "Q"
    NOT_APPLICABLE = "not_applicable"


class DataStatus(StrEnum):
    OBSERVED = "observed"
    DERIVED = "derived"
    IMPUTED = "imputed"
    MISSING = "missing"


class DayCountConvention(StrEnum):
    ACTUAL_365_FIXED = "actual_365_fixed"
    TRADING_252 = "trading_252"


class CompoundingConvention(StrEnum):
    CONTINUOUS = "continuous"
    SIMPLE = "simple"


class QuantConventionSet(StrictModel):
    """Immutable conventions used by all new quantitative code."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)

    calendar_day_basis: float = Field(default=CALENDAR_DAYS_PER_YEAR, gt=0)
    trading_session_basis: float = Field(default=TRADING_SESSIONS_PER_YEAR, gt=0)
    day_count: DayCountConvention = DayCountConvention.ACTUAL_365_FIXED
    compounding: CompoundingConvention = CompoundingConvention.CONTINUOUS
    theta_unit: Literal["per_calendar_day"] = "per_calendar_day"
    volatility_unit: Literal["annual_decimal"] = "annual_decimal"

    def calendar_year_fraction(self, start: date | datetime, end: date | datetime) -> float:
        """Return an Actual/365 Fixed year fraction, preserving intraday precision."""
        if isinstance(start, datetime) != isinstance(end, datetime):
            raise TypeError("start and end must both be dates or both be datetimes")
        if isinstance(start, datetime):
            assert isinstance(end, datetime)
            elapsed = end - start
        else:
            assert isinstance(end, date) and not isinstance(end, datetime)
            elapsed = end - start
        seconds = elapsed.total_seconds()
        if seconds < 0:
            raise ValueError("end must not precede start")
        return seconds / (self.calendar_day_basis * 24.0 * 60.0 * 60.0)

    def trading_year_fraction(self, sessions: int) -> float:
        if sessions < 0:
            raise ValueError("sessions cannot be negative")
        return sessions / self.trading_session_basis

    def annualize_mean_return(self, mean_session_return: float) -> float:
        return mean_session_return * self.trading_session_basis

    def annualize_volatility(self, session_volatility: float) -> float:
        if session_volatility < 0:
            raise ValueError("volatility cannot be negative")
        return session_volatility * math.sqrt(self.trading_session_basis)

    def deannualize_volatility(self, annual_volatility: float) -> float:
        if annual_volatility < 0:
            raise ValueError("volatility cannot be negative")
        return annual_volatility / math.sqrt(self.trading_session_basis)

    def discount_factor(self, annual_rate: float, time_years: float) -> float:
        if time_years < 0:
            raise ValueError("time cannot be negative")
        if self.compounding is CompoundingConvention.CONTINUOUS:
            return math.exp(-annual_rate * time_years)
        denominator = 1.0 + annual_rate * time_years
        if denominator <= 0:
            raise ValueError("simple-compounding denominator must be positive")
        return 1.0 / denominator


DEFAULT_QUANT_CONVENTIONS = QuantConventionSet()


class ObservedValue(StrictModel):
    """A scalar value whose origin, status, unit, and measure cannot be implicit."""

    value: float | int | str | bool | date | datetime | None
    status: DataStatus
    source_id: str = Field(min_length=1)
    as_of: date | datetime | None = None
    unit: str = Field(min_length=1)
    measure: Measure = Measure.NOT_APPLICABLE

    @model_validator(mode="after")
    def validate_missingness(self) -> ObservedValue:
        if self.status is DataStatus.MISSING and self.value is not None:
            raise ValueError("missing observations cannot carry a value")
        if self.status is not DataStatus.MISSING and self.value is None:
            raise ValueError("non-missing observations require a value")
        return self


class MeasureTaggedSeries(StrictModel):
    """Numeric observations with an explicit modelling purpose and measure."""

    values: tuple[float, ...] = Field(min_length=1)
    measure: Measure
    purpose: Literal["forecast", "pricing", "descriptive"]
    frequency: str = Field(min_length=1)
    source_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_measure_for_purpose(self) -> MeasureTaggedSeries:
        if self.purpose == "forecast" and self.measure is not Measure.REAL_WORLD:
            raise ValueError("forecast distributions require the real-world measure P")
        if self.purpose == "pricing" and self.measure is not Measure.RISK_NEUTRAL:
            raise ValueError("pricing distributions require the risk-neutral measure Q")
        return self


class MeasureTransition(StrictModel):
    """Explicit, sourced transition between real-world and risk-neutral measures."""

    from_measure: Measure
    to_measure: Measure
    method: str = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)
    assumptions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_transition(self) -> MeasureTransition:
        valid = {self.from_measure, self.to_measure} == {
            Measure.REAL_WORLD,
            Measure.RISK_NEUTRAL,
        }
        if not valid:
            raise ValueError("a measure transition must explicitly connect P and Q")
        return self


def require_measure(actual: Measure, expected: Measure, *, context: str) -> None:
    """Reject an accidental P/Q crossing at a quantitative boundary."""
    if actual is not expected:
        raise ValueError(
            f"{context} requires measure {expected.value}, received {actual.value}; "
            "provide an explicit MeasureTransition"
        )
