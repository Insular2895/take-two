"""Canonical governed context for prospective Phase M decisions."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_serializer, model_validator

from take_two_options.budget import (
    BrokerCapitalContext,
    FXExecutionCost,
    FXRate,
)
from take_two_options.config.contracts import ProspectiveBudgetConfig
from take_two_options.config.loader import load_prospective_budget_config
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.models import StrictModel


def _required_source_ids(
    *,
    config_source: str,
    fx_rate: FXRate | None,
    fx_execution_cost: FXExecutionCost | None,
    broker_capital_context: BrokerCapitalContext | None,
) -> set[str]:
    sources = {config_source}
    if fx_rate is not None:
        sources.add(fx_rate.source)
    if fx_execution_cost is not None and fx_execution_cost.source is not None:
        sources.add(fx_execution_cost.source)
    if broker_capital_context is not None and broker_capital_context.source is not None:
        sources.add(broker_capital_context.source)
    return sources


def _context_hash_payload(
    *,
    prospective_config: ProspectiveBudgetConfig,
    prospective_config_source: str,
    prospective_config_hash: str,
    fx_rate: FXRate | None,
    fx_execution_cost: FXExecutionCost | None,
    broker_capital_context: BrokerCapitalContext | None,
    source_ids: list[str],
) -> dict[str, object]:
    return {
        "prospective_config": prospective_config.model_dump(
            mode="json",
            exclude_computed_fields=True,
        ),
        "prospective_config_source": prospective_config_source,
        "prospective_config_hash": prospective_config_hash,
        "fx_rate": fx_rate.model_dump(mode="json") if fx_rate is not None else None,
        "fx_execution_cost": (
            fx_execution_cost.model_dump(mode="json")
            if fx_execution_cost is not None
            else None
        ),
        "broker_capital_context": (
            broker_capital_context.model_dump(mode="json")
            if broker_capital_context is not None
            else None
        ),
        "source_ids": source_ids,
    }


class PhaseMDecisionContext(StrictModel):
    """Immutable identity around static policy and point-in-time runtime evidence."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    prospective_config: ProspectiveBudgetConfig
    prospective_config_source: str = Field(min_length=1)
    prospective_config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    fx_rate: FXRate | None = None
    fx_execution_cost: FXExecutionCost | None = None
    broker_capital_context: BrokerCapitalContext | None = None
    created_at: datetime
    source_ids: list[str] = Field(default_factory=list)
    context_id: str = Field(pattern=r"^phase-m-context-[a-f0-9]{16}$")
    context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_serializer("prospective_config")
    def serialize_prospective_config(
        self,
        value: ProspectiveBudgetConfig,
    ) -> dict[str, object]:
        return value.model_dump(mode="json", exclude_computed_fields=True)

    def assert_integrity(self) -> None:
        if self.created_at.utcoffset() is None:
            raise ValueError("PHASE_M_CONTEXT_TIMESTAMP_NAIVE")
        if getattr(self.prospective_config, "mixed_expiry_lifecycle", None) is None:
            raise ValueError("PHASE_M_LIFECYCLE_CONTEXT_MISSING")
        expected_config_hash = stable_hash(
            self.prospective_config.model_dump(
                mode="json",
                exclude_computed_fields=True,
            )
        )
        if self.prospective_config_hash != expected_config_hash:
            raise ValueError("PHASE_M_CONFIG_HASH_MISMATCH")
        if self.source_ids != sorted(set(self.source_ids)):
            raise ValueError("PHASE_M_CONTEXT_SOURCES_NOT_CANONICAL")
        required_sources = _required_source_ids(
            config_source=self.prospective_config_source,
            fx_rate=self.fx_rate,
            fx_execution_cost=self.fx_execution_cost,
            broker_capital_context=self.broker_capital_context,
        )
        if not required_sources.issubset(self.source_ids):
            raise ValueError("PHASE_M_CONTEXT_PROVENANCE_MISSING")
        policy_currency = self.prospective_config.budget_policy.currency
        if self.fx_rate is not None:
            if self.fx_rate.policy_currency != policy_currency:
                raise ValueError("PHASE_M_FX_POLICY_CURRENCY_MISMATCH")
            if self.fx_rate.timestamp > self.created_at:
                raise ValueError("PHASE_M_FX_CONTEXT_FROM_FUTURE")
        if self.fx_execution_cost is not None:
            if (
                self.fx_execution_cost.cost_amount is not None
                and self.fx_execution_cost.currency != policy_currency
            ):
                raise ValueError("PHASE_M_FX_COST_CURRENCY_MISMATCH")
            if (
                self.fx_execution_cost.timestamp is not None
                and self.fx_execution_cost.timestamp > self.created_at
            ):
                raise ValueError("PHASE_M_FX_COST_CONTEXT_FROM_FUTURE")
        broker = self.broker_capital_context
        if broker is not None and broker.validated and broker.buying_power_requirement is not None:
            if broker.timestamp is not None and broker.timestamp > self.created_at:
                raise ValueError("PHASE_M_BROKER_CONTEXT_FROM_FUTURE")
            allowed_broker_currencies = {policy_currency}
            if self.fx_rate is not None:
                allowed_broker_currencies.add(self.fx_rate.source_currency)
            if broker.currency not in allowed_broker_currencies:
                raise ValueError("PHASE_M_BROKER_CURRENCY_UNCONVERTIBLE")
        expected_context_hash = stable_hash(
            _context_hash_payload(
                prospective_config=self.prospective_config,
                prospective_config_source=self.prospective_config_source,
                prospective_config_hash=self.prospective_config_hash,
                fx_rate=self.fx_rate,
                fx_execution_cost=self.fx_execution_cost,
                broker_capital_context=self.broker_capital_context,
                source_ids=self.source_ids,
            )
        )
        if self.context_hash != expected_context_hash:
            raise ValueError("PHASE_M_CONTEXT_HASH_MISMATCH")
        if self.context_id != f"phase-m-context-{expected_context_hash[:16]}":
            raise ValueError("PHASE_M_CONTEXT_ID_MISMATCH")

    @model_validator(mode="after")
    def validate_integrity_and_provenance(self) -> PhaseMDecisionContext:
        self.assert_integrity()
        return self

    def validate_for_candidate(self, *, candidate_currency: str, cutoff: datetime) -> None:
        """Validate runtime evidence against one candidate cutoff without calculating economics."""

        if cutoff.utcoffset() is None:
            raise ValueError("PHASE_M_CANDIDATE_CUTOFF_NAIVE")
        self.assert_integrity()
        source_currency = candidate_currency.upper()
        policy_currency = self.prospective_config.budget_policy.currency
        if source_currency != policy_currency:
            if self.fx_rate is None:
                raise ValueError("PHASE_M_FX_CONTEXT_MISSING")
            if (
                self.fx_rate.source_currency != source_currency
                or self.fx_rate.policy_currency != policy_currency
            ):
                raise ValueError("PHASE_M_FX_CONTEXT_CURRENCY_MISMATCH")
            if self.fx_rate.timestamp > cutoff:
                raise ValueError("PHASE_M_FX_CONTEXT_AFTER_CUTOFF")
        if (
            self.fx_execution_cost is not None
            and self.fx_execution_cost.timestamp is not None
            and self.fx_execution_cost.timestamp > cutoff
        ):
            raise ValueError("PHASE_M_FX_COST_CONTEXT_AFTER_CUTOFF")
        broker = self.broker_capital_context
        if (
            broker is not None
            and broker.validated
            and broker.timestamp is not None
            and broker.timestamp > cutoff
        ):
            raise ValueError("PHASE_M_BROKER_CONTEXT_AFTER_CUTOFF")


def build_phase_m_decision_context(
    prospective_config: ProspectiveBudgetConfig,
    *,
    prospective_config_source: str,
    fx_rate: FXRate | None = None,
    fx_execution_cost: FXExecutionCost | None = None,
    broker_capital_context: BrokerCapitalContext | None = None,
    created_at: datetime | None = None,
    source_ids: Iterable[str] = (),
) -> PhaseMDecisionContext:
    """Validate and hash one static policy plus optional point-in-time evidence."""

    if getattr(prospective_config, "mixed_expiry_lifecycle", None) is None:
        raise ValueError("PHASE_M_LIFECYCLE_CONTEXT_MISSING")
    timestamp = created_at or datetime.now(UTC)
    config_hash = stable_hash(
        prospective_config.model_dump(mode="json", exclude_computed_fields=True)
    )
    canonical_sources = sorted(
        set(source_ids)
        | _required_source_ids(
            config_source=prospective_config_source,
            fx_rate=fx_rate,
            fx_execution_cost=fx_execution_cost,
            broker_capital_context=broker_capital_context,
        )
    )
    hash_payload = _context_hash_payload(
        prospective_config=prospective_config,
        prospective_config_source=prospective_config_source,
        prospective_config_hash=config_hash,
        fx_rate=fx_rate,
        fx_execution_cost=fx_execution_cost,
        broker_capital_context=broker_capital_context,
        source_ids=canonical_sources,
    )
    context_hash = stable_hash(hash_payload)
    return PhaseMDecisionContext(
        prospective_config=prospective_config,
        prospective_config_source=prospective_config_source,
        prospective_config_hash=config_hash,
        fx_rate=fx_rate,
        fx_execution_cost=fx_execution_cost,
        broker_capital_context=broker_capital_context,
        created_at=timestamp,
        source_ids=canonical_sources,
        context_id=f"phase-m-context-{context_hash[:16]}",
        context_hash=context_hash,
    )


def load_phase_m_decision_context(
    prospective_config_path: Path,
    *,
    fx_rate: FXRate | None = None,
    fx_execution_cost: FXExecutionCost | None = None,
    broker_capital_context: BrokerCapitalContext | None = None,
    created_at: datetime | None = None,
    source_ids: Iterable[str] = (),
) -> PhaseMDecisionContext:
    """Load the canonical YAML once, then build one governed Phase M context."""

    config = load_prospective_budget_config(prospective_config_path)
    return build_phase_m_decision_context(
        config,
        prospective_config_source=prospective_config_path.as_posix(),
        fx_rate=fx_rate,
        fx_execution_cost=fx_execution_cost,
        broker_capital_context=broker_capital_context,
        created_at=created_at,
        source_ids=source_ids,
    )
