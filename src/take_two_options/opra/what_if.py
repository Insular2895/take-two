"""Sanitize already-captured IBKR what-if observations without requesting one.

IBKR exposes margin preview through an order-shaped API operation.  This module
deliberately contains no broker transport and imports no order class: a human-run,
separately governed process may provide a redacted observation later, and this
offline boundary only validates and normalizes that observation.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, field_validator

from take_two_options.domain import StrictModel
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.opra.contracts import BrokerWhatIfEvidence

_SENTINEL_ABSOLUTE_VALUE = 1e50


class BrokerWhatIfObservation(StrictModel):
    """Redacted transcription of broker output; never a request or an order."""

    schema_version: Literal["1.0"] = "1.0"
    candidate_id: str = Field(min_length=1)
    observed_at: datetime
    source_id: str = Field(min_length=1)
    currency: str = Field(min_length=3, max_length=3)
    commission_currency: str | None = Field(default=None, min_length=3, max_length=3)
    commission: str | None = None
    minimum_commission: str | None = None
    maximum_commission: str | None = None
    initial_margin_before: str | None = None
    initial_margin_change: str | None = None
    initial_margin_after: str | None = None
    maintenance_margin_before: str | None = None
    maintenance_margin_change: str | None = None
    maintenance_margin_after: str | None = None
    equity_with_loan_before: str | None = None
    equity_with_loan_change: str | None = None
    equity_with_loan_after: str | None = None
    broker_status: str | None = None
    warning_text: str | None = None
    account_scope_redacted: Literal[True] = True
    example_only: bool = True
    read_only: Literal[True] = True
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("observed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("what-if observation timestamp must be timezone-aware")
        return value.astimezone(UTC)

    @field_validator("currency", "commission_currency")
    @classmethod
    def require_currency_shape(cls, value: str | None) -> str | None:
        if value is not None and (not value.isalpha() or not value.isupper()):
            raise ValueError("what-if currencies must be three uppercase letters")
        return value


class BrokerWhatIfNormalizationReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    input_hash: str = Field(min_length=64, max_length=64)
    status: Literal["NORMALIZED_COMPLETE", "NORMALIZED_INCOMPLETE"]
    evidence: BrokerWhatIfEvidence
    checks: tuple[str, ...] = Field(min_length=1)
    strategy_promotion_eligible: Literal[False] = False
    connection_attempted: Literal[False] = False
    transmit: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"
    maximum_claim: Literal["sanitized_offline_broker_observation"] = (
        "sanitized_offline_broker_observation"
    )


def normalize_broker_what_if(
    observation: BrokerWhatIfObservation,
) -> BrokerWhatIfNormalizationReport:
    """Normalize a real, redacted observation and preserve every unknown as unknown."""

    if observation.example_only:
        raise ValueError("IBKR_WHAT_IF_OBSERVATION_MARKED_EXAMPLE_ONLY")

    warnings: list[str] = []
    values: dict[str, float | None] = {}
    nonnegative = {"commission", "minimum_commission", "maximum_commission"}
    numeric_fields = (
        "commission",
        "minimum_commission",
        "maximum_commission",
        "initial_margin_before",
        "initial_margin_change",
        "initial_margin_after",
        "maintenance_margin_before",
        "maintenance_margin_change",
        "maintenance_margin_after",
        "equity_with_loan_before",
        "equity_with_loan_change",
        "equity_with_loan_after",
    )
    for field_name in numeric_fields:
        values[field_name] = _parse_broker_number(
            getattr(observation, field_name),
            field_name=field_name,
            nonnegative=field_name in nonnegative,
            warnings=warnings,
        )

    currency_matches = observation.commission_currency == observation.currency
    if observation.commission_currency is None:
        warnings.append("WHAT_IF_COMMISSION_CURRENCY_MISSING")
    elif not currency_matches:
        warnings.append("WHAT_IF_COMMISSION_CURRENCY_MISMATCH")
    if observation.warning_text and observation.warning_text.strip():
        warnings.append("WHAT_IF_BROKER_WARNING_PRESENT_REDACTED")

    bounds_valid = _commission_bounds_are_valid(values, warnings)
    complete = (
        all(
            values[name] is not None
            for name in (
                "commission",
                "initial_margin_change",
                "maintenance_margin_change",
            )
        )
        and currency_matches
        and bounds_valid
    )
    evidence = BrokerWhatIfEvidence(
        candidate_id=observation.candidate_id,
        observed_at=observation.observed_at,
        currency=observation.currency,
        estimated_commission=values["commission"],
        minimum_commission=values["minimum_commission"],
        maximum_commission=values["maximum_commission"],
        initial_margin_before=values["initial_margin_before"],
        initial_margin_change=values["initial_margin_change"],
        initial_margin_after=values["initial_margin_after"],
        maintenance_margin_before=values["maintenance_margin_before"],
        maintenance_margin_change=values["maintenance_margin_change"],
        maintenance_margin_after=values["maintenance_margin_after"],
        equity_with_loan_before=values["equity_with_loan_before"],
        equity_with_loan_change=values["equity_with_loan_change"],
        equity_with_loan_after=values["equity_with_loan_after"],
        buying_power_change=None,
        broker_status=observation.broker_status,
        source_id=observation.source_id,
        complete=complete,
        warnings=warnings,
    )
    checks = [
        "WHAT_IF_INPUT_REDACTED",
        "WHAT_IF_NO_CONNECTION_ATTEMPTED",
        "WHAT_IF_ORDER_CAPABILITY_FORBIDDEN",
        "WHAT_IF_REQUIRED_FIELDS_COMPLETE" if complete else "WHAT_IF_REQUIRED_FIELDS_INCOMPLETE",
    ]
    return BrokerWhatIfNormalizationReport(
        input_hash=stable_hash(observation.model_dump(mode="json")),
        status="NORMALIZED_COMPLETE" if complete else "NORMALIZED_INCOMPLETE",
        evidence=evidence,
        checks=tuple(checks),
    )


def _parse_broker_number(
    raw: str | None,
    *,
    field_name: str,
    nonnegative: bool,
    warnings: list[str],
) -> float | None:
    detail = field_name.upper()
    if raw is None or not raw.strip():
        warnings.append(f"WHAT_IF_{detail}_MISSING")
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        warnings.append(f"WHAT_IF_{detail}_INVALID")
        return None
    if not math.isfinite(value):
        warnings.append(f"WHAT_IF_{detail}_NON_FINITE")
        return None
    if abs(value) >= _SENTINEL_ABSOLUTE_VALUE:
        warnings.append(f"WHAT_IF_{detail}_SENTINEL")
        return None
    if nonnegative and value < 0:
        warnings.append(f"WHAT_IF_{detail}_NEGATIVE")
        return None
    return value


def _commission_bounds_are_valid(values: dict[str, float | None], warnings: list[str]) -> bool:
    commission = values["commission"]
    minimum = values["minimum_commission"]
    maximum = values["maximum_commission"]
    valid = True
    if minimum is not None and maximum is not None and minimum > maximum:
        warnings.append("WHAT_IF_COMMISSION_BOUNDS_REVERSED")
        valid = False
    if commission is not None and minimum is not None and commission < minimum:
        warnings.append("WHAT_IF_COMMISSION_BELOW_MINIMUM")
        valid = False
    if commission is not None and maximum is not None and commission > maximum:
        warnings.append("WHAT_IF_COMMISSION_ABOVE_MAXIMUM")
        valid = False
    if not valid:
        values["minimum_commission"] = None
        values["maximum_commission"] = None
    return valid
