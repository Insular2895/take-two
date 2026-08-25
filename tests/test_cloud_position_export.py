from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.budget import FXExecutionCostStatus
from take_two_options.cloud.contracts import (
    CloudCloseAction,
    CloudPositionDossier,
    CloudPositionState,
)
from take_two_options.cloud.export_position import build_cloud_position_dossier
from take_two_options.trade_economics_models import TradeEconomicsTicket

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_TICKET = REPOSITORY_ROOT / "reports/examples/m0_trade_economics_ticket.json"


def _ticket() -> tuple[TradeEconomicsTicket, bytes]:
    payload = GOLDEN_TICKET.read_bytes()
    ticket = TradeEconomicsTicket.model_validate_json(payload)
    return ticket.model_copy(update={"underlying_spot": 215.0}), payload


def test_canonical_ticket_exports_without_repricing() -> None:
    ticket, payload = _ticket()
    dossier = build_cloud_position_dossier(
        ticket,
        ticket_bytes=payload,
        repository_root=REPOSITORY_ROOT,
        initial_state=CloudPositionState.PAPER_OPEN,
    )

    assert dossier.trade_economics_ticket_hash == hashlib.sha256(payload).hexdigest()
    assert dossier.schema_version == "1.1"
    assert dossier.entry_cash_flow_policy == pytest.approx(
        -ticket.entry_cost.total_entry_cash_flow
    )
    assert dossier.capital_required_policy == pytest.approx(
        ticket.budget_diagnostics.effective_capital_requirement
    )
    assert dossier.initial_spot == 215.0
    assert dossier.initial_position_state is CloudPositionState.PAPER_OPEN
    assert dossier.fixture_status == "SYNTHETIC_DEMO"
    assert dossier.flat_spot_diagnostics is not None
    assert dossier.flat_spot_diagnostics.flat_spot_30d == ticket.time_decay.flat_spot_30d
    assert dossier.transmit is False
    assert dossier.order_capability == "forbidden"
    assert all(
        leg.close_action
        is (
            CloudCloseAction.SELL_TO_CLOSE
            if leg.side.value == "LONG"
            else CloudCloseAction.BUY_TO_CLOSE
        )
        for leg in dossier.legs
    )


def test_missing_spot_fails_closed() -> None:
    ticket, payload = _ticket()
    with pytest.raises(ValueError, match="underlying_spot"):
        build_cloud_position_dossier(
            ticket.model_copy(update={"underlying_spot": None}),
            ticket_bytes=payload,
            repository_root=REPOSITORY_ROOT,
        )


def test_safety_flags_cannot_be_weakened() -> None:
    ticket, payload = _ticket()
    dossier = build_cloud_position_dossier(
        ticket,
        ticket_bytes=payload,
        repository_root=REPOSITORY_ROOT,
    )
    with pytest.raises(ValidationError):
        CloudPositionDossier.model_validate({**dossier.model_dump(mode="json"), "transmit": True})


def test_credit_entry_exports_signed_cash_flow_separately_from_capital() -> None:
    ticket, payload = _ticket()
    entry = ticket.entry_cost.model_copy(
        update={
            "premium_paid": 0.0,
            "premium_received": 305.0,
            "net_premium": -305.0,
            "mid_theoretical_value": -305.0,
            "bid_ask_cost": 0.0,
            "expected_slippage": 2.0,
            "commission": 3.0,
            "total_entry_cost": -300.0,
            "theoretical_mid_premium_paid": 0.0,
            "theoretical_mid_premium_received": 305.0,
            "theoretical_mid_net_premium": -305.0,
            "executable_premium_paid": 0.0,
            "executable_premium_received": 305.0,
            "executable_net_premium": -305.0,
            "entry_bid_ask_cost": 0.0,
            "entry_slippage": 2.0,
            "entry_commission": 3.0,
            "total_entry_cash_flow": -300.0,
        }
    )
    diagnostics = ticket.budget_diagnostics.model_copy(
        update={
            "native_entry_cash": -300.0,
            "converted_entry_cash_before_fx_cost": 0.0,
            "required_entry_cash_after_fx": 0.0,
            "required_entry_cash": 0.0,
            "effective_capital_requirement": 700.0,
        }
    )
    credit = ticket.model_copy(update={"entry_cost": entry, "budget_diagnostics": diagnostics})

    dossier = build_cloud_position_dossier(
        credit,
        ticket_bytes=payload,
        repository_root=REPOSITORY_ROOT,
    )

    assert dossier.entry_cash_flow_policy == pytest.approx(300.0)
    assert dossier.capital_required_policy == pytest.approx(700.0)


def test_export_fails_when_entry_sign_is_not_canonical() -> None:
    ticket, payload = _ticket()
    entry = ticket.entry_cost.model_copy(update={"total_entry_cash_flow": None})
    with pytest.raises(ValueError, match="ENTRY_CASH_FLOW_SIGN_UNPROVEN"):
        build_cloud_position_dossier(
            ticket.model_copy(update={"entry_cost": entry}),
            ticket_bytes=payload,
            repository_root=REPOSITORY_ROOT,
        )


def test_policy_currency_cash_flow_converts_signed_native_economics_once() -> None:
    ticket, payload = _ticket()
    diagnostics = ticket.budget_diagnostics.model_copy(
        update={
            "currency": "EUR",
            "native_currency": "USD",
            "native_entry_cash": ticket.entry_cost.total_entry_cash_flow,
            "converted_entry_cash_before_fx_cost": 2701.935,
            "entry_fx_cost": 3.0,
            "entry_fx_cost_status": FXExecutionCostStatus.KNOWN,
            "required_entry_cash_after_fx": 2704.935,
            "required_entry_cash": 2704.935,
            "effective_capital_requirement": 2704.935,
            "fx_rate_to_policy_currency": 0.9,
            "fx_rate": 0.9,
            "fx_timestamp": ticket.exact_market_timestamp,
            "fx_rate_source": "SYNTHETIC_TEST",
            "fx_cost_source": "SYNTHETIC_TEST",
        }
    )
    converted = ticket.model_copy(update={"budget_diagnostics": diagnostics})

    dossier = build_cloud_position_dossier(
        converted,
        ticket_bytes=payload,
        repository_root=REPOSITORY_ROOT,
    )

    assert dossier.entry_cash_flow_policy == pytest.approx(-2704.935)
    assert dossier.capital_required_policy == pytest.approx(2704.935)
