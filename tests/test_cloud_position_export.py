from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

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
    assert dossier.actual_entry_cash == ticket.budget_diagnostics.required_entry_cash_after_fx
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
