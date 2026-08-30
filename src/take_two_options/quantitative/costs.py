"""Single reconciliation contract for simulated path transaction economics."""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from take_two_options.domain import StrictModel
from take_two_options.quantitative.contracts import EvidenceLevel


class EconomicComponent(StrictModel):
    value: float | None = Field(default=None, ge=0)
    evidence: EvidenceLevel
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def preserve_missingness(self) -> EconomicComponent:
        unavailable = {
            EvidenceLevel.UNKNOWN,
            EvidenceLevel.INSUFFICIENT_DATA,
            EvidenceLevel.BLOCKED,
        }
        if self.evidence in unavailable and self.value is not None:
            raise ValueError("unavailable economic components must remain null")
        if self.evidence not in unavailable and self.value is None:
            raise ValueError("available economic components require a value")
        if self.evidence is EvidenceLevel.NOT_APPLICABLE and self.value != 0:
            raise ValueError("not-applicable economic components must be explicit zero")
        return self


class PnLReconciliation(StrictModel):
    """Gross PnL less each named friction exactly once equals net PnL."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
    )

    gross_pnl: float
    entry_bid_ask_cost: EconomicComponent
    exit_bid_ask_cost: EconomicComponent
    entry_slippage: EconomicComponent
    exit_slippage: EconomicComponent
    commissions: EconomicComponent
    exercise_assignment_settlement_costs: EconomicComponent
    fx_costs: EconomicComponent
    net_pnl: float | None = None
    status: EvidenceLevel

    @model_validator(mode="after")
    def reconcile(self) -> PnLReconciliation:
        components = (
            self.entry_bid_ask_cost,
            self.exit_bid_ask_cost,
            self.entry_slippage,
            self.exit_slippage,
            self.commissions,
            self.exercise_assignment_settlement_costs,
            self.fx_costs,
        )
        if any(component.value is None for component in components):
            if self.net_pnl is not None or self.status is not EvidenceLevel.BLOCKED:
                raise ValueError("unknown cost components require blocked null net PnL")
            return self
        expected = self.gross_pnl - sum(
            component.value for component in components if component.value is not None
        )
        if self.net_pnl is None or abs(self.net_pnl - expected) > 1e-8:
            raise ValueError("PnL cost components do not reconcile exactly once")
        if self.status is EvidenceLevel.BLOCKED:
            raise ValueError("fully known reconciliation cannot be blocked")
        return self


def reconcile_pnl(
    *,
    gross_pnl: float,
    entry_bid_ask_cost: EconomicComponent,
    exit_bid_ask_cost: EconomicComponent,
    entry_slippage: EconomicComponent,
    exit_slippage: EconomicComponent,
    commissions: EconomicComponent,
    exercise_assignment_settlement_costs: EconomicComponent,
    fx_costs: EconomicComponent,
) -> PnLReconciliation:
    components = (
        entry_bid_ask_cost,
        exit_bid_ask_cost,
        entry_slippage,
        exit_slippage,
        commissions,
        exercise_assignment_settlement_costs,
        fx_costs,
    )
    if any(component.value is None for component in components):
        return PnLReconciliation(
            gross_pnl=gross_pnl,
            entry_bid_ask_cost=entry_bid_ask_cost,
            exit_bid_ask_cost=exit_bid_ask_cost,
            entry_slippage=entry_slippage,
            exit_slippage=exit_slippage,
            commissions=commissions,
            exercise_assignment_settlement_costs=exercise_assignment_settlement_costs,
            fx_costs=fx_costs,
            net_pnl=None,
            status=EvidenceLevel.BLOCKED,
        )
    net = gross_pnl - sum(
        component.value for component in components if component.value is not None
    )
    evidence = (
        EvidenceLevel.ESTIMATED
        if any(
            component.evidence
            in {EvidenceLevel.ESTIMATED, EvidenceLevel.HEURISTIC, EvidenceLevel.UNVALIDATED}
            for component in components
        )
        else EvidenceLevel.KNOWN
    )
    return PnLReconciliation(
        gross_pnl=gross_pnl,
        entry_bid_ask_cost=entry_bid_ask_cost,
        exit_bid_ask_cost=exit_bid_ask_cost,
        entry_slippage=entry_slippage,
        exit_slippage=exit_slippage,
        commissions=commissions,
        exercise_assignment_settlement_costs=exercise_assignment_settlement_costs,
        fx_costs=fx_costs,
        net_pnl=net,
        status=evidence,
    )
