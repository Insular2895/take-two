from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from ttwo_ibkr_bridge.contracts import GatewayEvent, PaperCommand
from ttwo_ibkr_bridge.journal import BridgeJournal
from ttwo_ibkr_bridge.order_lifecycle import (
    BrokerErrorEvidence,
    CancellationCause,
    CanonicalExecutionStatus,
    CashFlowType,
    CommissionEvidence,
    ExecutionCondition,
    ExecutionDiagnosticSnapshot,
    ExecutionEvidence,
    IBKRBrokerExecutionNormalizer,
    MarketabilityDiagnostic,
    MarketabilityInput,
    OpenOrderEvidence,
    OrderStatusEvidence,
    RejectionCategory,
    RepriceRequest,
    RepriceStatus,
    classify_marketability,
    propose_reprice,
)

NOW = datetime(2026, 9, 18, 12, 0, tzinfo=UTC)
NORMALIZER = IBKRBrokerExecutionNormalizer()


def order_status(
    status: str,
    *,
    filled: str = "0",
    remaining: str = "1",
    transmitted: bool = True,
    why_held: str | None = None,
    cancellation_cause: CancellationCause | None = None,
) -> OrderStatusEvidence:
    return OrderStatusEvidence(
        order_id=42,
        status=status,
        filled=Decimal(filled),
        remaining=Decimal(remaining),
        avg_fill_price=Decimal("5.25") if Decimal(filled) else None,
        perm_id=84,
        parent_id=0,
        last_fill_price=Decimal("5.25") if Decimal(filled) else None,
        client_id=7,
        why_held=why_held,
        market_cap_price=None,
        received_at=NOW,
        transmitted_to_broker=transmitted,
        time_in_force="DAY",
        cancellation_cause=cancellation_cause,
    )


@pytest.mark.parametrize(
    ("raw", "canonical"),
    [
        ("PendingSubmit", CanonicalExecutionStatus.PENDING_SUBMIT),
        ("PreSubmitted", CanonicalExecutionStatus.PRE_SUBMITTED),
        ("Submitted", CanonicalExecutionStatus.WORKING),
        ("PendingCancel", CanonicalExecutionStatus.PENDING_CANCEL),
        ("ApiCancelled", CanonicalExecutionStatus.API_CANCELLED),
        ("Filled", CanonicalExecutionStatus.FILLED),
        ("Inactive", CanonicalExecutionStatus.INACTIVE),
        ("FutureUnknown", CanonicalExecutionStatus.AMBIGUOUS),
    ],
)
def test_ibkr_status_mapping_is_deterministic(
    raw: str, canonical: CanonicalExecutionStatus
) -> None:
    event = NORMALIZER.order_status(
        order_status(raw, filled="1", remaining="0") if raw == "Filled" else order_status(raw)
    )
    assert event.detail is not None
    assert event.detail["raw_broker_status"] == raw
    assert event.detail["canonical_execution_status"] == canonical.value


def test_transmit_false_is_local_not_transmitted() -> None:
    event = NORMALIZER.open_order(
        OpenOrderEvidence(
            order_id=42,
            perm_id=84,
            client_id=7,
            order_ref="TTWO-P-123",
            raw_status="Inactive",
            total_quantity=Decimal("1"),
            limit_price=Decimal("5.25"),
            time_in_force="DAY",
            transmit=False,
            received_at=NOW,
        )
    )
    assert event.detail is not None
    assert event.detail["canonical_execution_status"] == "LOCAL_NOT_TRANSMITTED"
    assert event.detail["transmitted_to_broker"] is False


def test_open_order_status_is_mapped_without_treating_pending_as_broker_acceptance() -> None:
    submitted = NORMALIZER.open_order(
        OpenOrderEvidence(
            order_id=42,
            perm_id=84,
            client_id=7,
            order_ref="TTWO-P-123",
            raw_status="Submitted",
            total_quantity=Decimal("1"),
            limit_price=Decimal("5.25"),
            time_in_force="DAY",
            transmit=True,
            received_at=NOW,
        )
    )
    pending = NORMALIZER.open_order(
        OpenOrderEvidence(
            order_id=43,
            perm_id=None,
            client_id=7,
            order_ref="TTWO-P-124",
            raw_status="PendingSubmit",
            total_quantity=Decimal("1"),
            limit_price=Decimal("5.25"),
            time_in_force="DAY",
            transmit=True,
            received_at=NOW,
        )
    )
    assert submitted.detail is not None and pending.detail is not None
    assert submitted.detail["canonical_execution_status"] == "WORKING"
    assert submitted.detail["transmitted_to_broker"] is True
    assert pending.detail["canonical_execution_status"] == "PENDING_SUBMIT"
    assert pending.detail["transmitted_to_broker"] is None


def test_working_zero_fill_is_not_a_terminal_failure() -> None:
    event = NORMALIZER.order_status(order_status("Submitted"))
    assert event.detail is not None
    assert event.detail["canonical_execution_status"] == "WORKING"
    assert event.detail["execution_condition"] == "WORKING_NO_FILL_YET"
    assert "NO_LIQUIDITY" not in event.detail.values()


def test_partial_and_complete_fills_use_quantities_not_labels_only() -> None:
    partial = NORMALIZER.order_status(order_status("Submitted", filled="2", remaining="2"))
    complete = NORMALIZER.order_status(order_status("Submitted", filled="4", remaining="0"))
    assert partial.detail is not None and complete.detail is not None
    assert partial.detail["canonical_execution_status"] == "PARTIALLY_FILLED"
    assert partial.detail["execution_condition"] == "PARTIAL_FILL_ACTIVE"
    assert complete.detail["canonical_execution_status"] == "FILLED"


def test_broker_hold_and_tif_cancellation_remain_precise() -> None:
    held = NORMALIZER.order_status(order_status("Submitted", why_held="locate pending"))
    tif = NORMALIZER.order_status(
        order_status("Cancelled", cancellation_cause=CancellationCause.TIF_EXPIRED)
    )
    assert held.detail is not None and tif.detail is not None
    assert held.detail["execution_condition"] == ExecutionCondition.BROKER_HELD.value
    assert tif.detail["execution_condition"] == "TIF_CONDITION_NOT_SATISFIED"
    assert tif.detail["cancellation_cause"] == "TIF_EXPIRED"


def test_explicit_api_cancellation_cause_is_not_a_liquidity_guess() -> None:
    event = NORMALIZER.order_status(
        order_status("Cancelled", cancellation_cause=CancellationCause.API_REQUESTED)
    )
    assert event.detail is not None
    assert event.detail["canonical_execution_status"] == "CANCELLED"
    assert event.detail["cancellation_cause"] == "API_REQUESTED"
    assert "LIQUIDITY" not in str(event.detail)


def test_rejection_preserves_code_redacts_account_and_classifies_precaution() -> None:
    event = NORMALIZER.error(
        BrokerErrorEvidence(
            request_or_order_id=42,
            error_code=109,
            message="Price outside Percentage setting for account DU123456",
            advanced_rejection_json='{"account":"DU123456","reason":"precaution"}',
            received_at=NOW,
            order_rejected=False,
            transmitted_to_broker=False,
        )
    )
    assert event.detail is not None
    assert event.detail["broker_error_code"] == 109
    assert event.detail["normalized_category"] == RejectionCategory.ORDER_PRECAUTION.value
    assert event.detail["canonical_execution_status"] == "LOCAL_NOT_TRANSMITTED"
    assert "DU123456" not in str(event.detail)
    assert "NO_LIQUIDITY" not in str(event.detail)


def test_price_protection_and_unknown_rejections_do_not_lose_raw_code() -> None:
    protected = NORMALIZER.error(
        BrokerErrorEvidence(
            request_or_order_id=42,
            error_code=201,
            message="Order rejected: limit price outside allowed price protection range",
            advanced_rejection_json=None,
            received_at=NOW,
            order_rejected=True,
            transmitted_to_broker=True,
        )
    )
    unknown = NORMALIZER.error(
        BrokerErrorEvidence(
            request_or_order_id=43,
            error_code=9999,
            message="Unmapped broker rejection",
            advanced_rejection_json=None,
            received_at=NOW,
            order_rejected=True,
            transmitted_to_broker=True,
        )
    )
    assert protected.detail is not None and unknown.detail is not None
    assert protected.detail["normalized_category"] == "LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE"
    assert protected.detail["broker_error_code"] == 201
    assert unknown.detail["normalized_category"] == "UNKNOWN_BROKER_REJECTION"


@pytest.mark.parametrize(
    ("code", "category"),
    [
        (100, "MESSAGE_RATE"),
        (101, "TICKER_LIMIT"),
        (103, "DUPLICATE_ORDER"),
        (106, "INVALID_ORDER"),
        (107, "INVALID_ORDER"),
        (109, "ORDER_PRECAUTION"),
        (110, "INVALID_TICK"),
        (111, "INCOMPATIBLE_TIF"),
        (116, "EXCHANGE_RESTRICTION"),
        (133, "SUBMISSION_FAILED"),
        (134, "MODIFICATION_FAILED"),
        (154, "HALTED_SECURITY"),
        (160, "INVALID_SIZE"),
        (163, "ORDER_PRECAUTION"),
        (164, "ORDER_PRECAUTION"),
        (200, "INVALID_CONTRACT"),
        (202, "CANCELLATION"),
        (203, "ACCOUNT_PERMISSION"),
        (312, "INVALID_COMBO"),
        (313, "INVALID_COMBO"),
        (314, "INVALID_COMBO"),
        (315, "EXCHANGE_RESTRICTION"),
        (354, "MARKET_DATA_PERMISSION"),
        (355, "INVALID_SIZE"),
        (360, "WHAT_IF_UNSUPPORTED"),
        (10002, "COMBO_GUARANTEE"),
        (10015, "API_TRADING_NOT_ALLOWED"),
        (10089, "MARKET_DATA_PERMISSION"),
        (10090, "MARKET_DATA_PERMISSION"),
        (10091, "MARKET_DATA_PERMISSION"),
        (10186, "MARKET_DATA_PERMISSION"),
        (10197, "SESSION_STATE"),
    ],
)
def test_documented_error_matrix_is_deterministic(code: int, category: str) -> None:
    event = NORMALIZER.error(
        BrokerErrorEvidence(
            request_or_order_id=42,
            error_code=code,
            message="deterministic offline fixture",
            advanced_rejection_json=None,
            received_at=NOW,
            order_rejected=True,
            transmitted_to_broker=True,
        )
    )
    assert event.detail is not None
    assert event.detail["broker_error_code"] == code
    assert event.detail["normalized_category"] == category


def test_session_loss_for_an_order_requires_reconciliation() -> None:
    event = NORMALIZER.error(
        BrokerErrorEvidence(
            request_or_order_id=42,
            error_code=504,
            message="Not connected",
            advanced_rejection_json=None,
            received_at=NOW,
            order_rejected=False,
            transmitted_to_broker=None,
        )
    )
    assert event.detail is not None
    assert event.detail["canonical_execution_status"] == "RECONCILIATION_REQUIRED"
    assert event.detail["execution_condition"] == "STATE_UNKNOWN"


def marketability(
    cash_flow_type: CashFlowType,
    limit: str,
    *,
    live: bool = True,
    fresh: bool = True,
    convention: bool = True,
    quote: bool = True,
) -> MarketabilityDiagnostic:
    return classify_marketability(
        MarketabilityInput(
            cash_flow_type=cash_flow_type,
            requested_limit=Decimal(limit),
            combo_bid=Decimal("5.10") if quote else None,
            combo_ask=Decimal("5.40") if quote else None,
            market_data_type="live" if live else "delayed",
            combo_freshness="FRESH" if fresh else "STALE",
            option_freshness="FRESH",
            underlying_freshness="FRESH",
            fx_freshness=None,
            fx_required=False,
            price_convention_verified=convention,
        )
    )


def test_debit_and_credit_marketability_use_inverse_economics() -> None:
    assert (
        marketability(CashFlowType.DEBIT, "5.20") is MarketabilityDiagnostic.WORKING_INSIDE_SPREAD
    )
    assert marketability(CashFlowType.DEBIT, "5.25") is MarketabilityDiagnostic.WORKING_NEAR_ASK
    assert (
        marketability(CashFlowType.DEBIT, "5.40")
        is MarketabilityDiagnostic.IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE
    )
    assert marketability(CashFlowType.CREDIT, "5.40") is MarketabilityDiagnostic.WORKING_AT_ASK_SIDE
    assert marketability(CashFlowType.CREDIT, "5.25") is MarketabilityDiagnostic.WORKING_NEAR_BID
    assert (
        marketability(CashFlowType.CREDIT, "5.10")
        is MarketabilityDiagnostic.IMMEDIATELY_MARKETABLE_AT_OBSERVED_QUOTE
    )


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"fresh": False}, MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_DATA_STALE),
        ({"live": False}, MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_DATA_NOT_LIVE),
        (
            {"convention": False},
            MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_PRICE_CONVENTION_UNVERIFIED,
        ),
        ({"quote": False}, MarketabilityDiagnostic.MARKETABILITY_UNKNOWN_NO_COMBO_QUOTE),
    ],
)
def test_marketability_fails_closed(
    kwargs: dict[str, bool], expected: MarketabilityDiagnostic
) -> None:
    assert marketability(CashFlowType.DEBIT, "5.25", **kwargs) is expected


def reprice(**updates: object) -> RepriceRequest:
    values: dict[str, object] = {
        "cash_flow_type": CashFlowType.DEBIT,
        "current_limit": Decimal("5.25"),
        "proposed_limit": Decimal("5.30"),
        "combo_bid": Decimal("5.10"),
        "combo_ask": Decimal("5.40"),
        "quantity": 1,
        "multiplier": Decimal("100"),
        "maximum_debit_policy": Decimal("5.40"),
        "minimum_credit_policy": None,
        "remaining_hard_budget_headroom": Decimal("20"),
        "remaining_max_loss_headroom": Decimal("20"),
        "current_estimated_pnl": Decimal("25"),
        "original_order_shape_hash": "a" * 64,
        "proposed_order_shape_hash": "a" * 64,
        "market_data_type": "live",
        "combo_freshness": "FRESH",
        "option_freshness": "FRESH",
        "underlying_freshness": "FRESH",
        "fx_freshness": None,
        "fx_required": False,
        "price_convention_verified": True,
    }
    values.update(updates)
    return RepriceRequest(**values)  # type: ignore[arg-type]


def test_debit_reprice_is_preview_only_and_budget_bounded() -> None:
    proposal = propose_reprice(reprice())
    assert proposal.status is RepriceStatus.READY_FOR_HUMAN_PREVIEW
    assert proposal.incremental_capital_impact == Decimal("5.00")
    assert proposal.new_estimated_pnl_economics == Decimal("20.00")
    assert proposal.automatic_action_allowed is False

    over_price = propose_reprice(reprice(proposed_limit=Decimal("5.41")))
    over_budget = propose_reprice(reprice(remaining_hard_budget_headroom=Decimal("4.99")))
    assert over_price.status is RepriceStatus.BLOCKED_AUTHORIZED_BOUND
    assert over_budget.status is RepriceStatus.BLOCKED_HARD_BUDGET


def test_credit_reprice_moves_down_only_within_minimum_credit() -> None:
    valid = propose_reprice(
        reprice(
            cash_flow_type=CashFlowType.CREDIT,
            current_limit=Decimal("5.25"),
            proposed_limit=Decimal("5.20"),
            maximum_debit_policy=None,
            minimum_credit_policy=Decimal("5.10"),
        )
    )
    wrong_direction = propose_reprice(
        reprice(
            cash_flow_type=CashFlowType.CREDIT,
            proposed_limit=Decimal("5.30"),
            maximum_debit_policy=None,
            minimum_credit_policy=Decimal("5.10"),
        )
    )
    assert valid.status is RepriceStatus.READY_FOR_HUMAN_PREVIEW
    assert valid.incremental_capital_impact == Decimal("5.00")
    assert wrong_direction.status is RepriceStatus.BLOCKED_DIRECTION


def test_reprice_blocks_stale_data_and_order_shape_changes() -> None:
    stale = propose_reprice(reprice(combo_freshness="STALE"))
    no_quote = propose_reprice(reprice(combo_bid=None, combo_ask=None))
    changed = propose_reprice(reprice(proposed_order_shape_hash="b" * 64))
    assert stale.status is RepriceStatus.REPRICE_UNAVAILABLE_DATA_STALE
    assert no_quote.status is RepriceStatus.REPRICE_UNAVAILABLE_DATA_STALE
    assert changed.status is RepriceStatus.BLOCKED_ORDER_SHAPE_CHANGED


def test_submission_snapshot_and_reprice_event_are_typed_preview_evidence() -> None:
    snapshot = ExecutionDiagnosticSnapshot(
        ticker="TTWO",
        candidate_id="candidate-1",
        strategy="BULL_CALL_SPREAD",
        quantity=1,
        legs=(
            {"con_id": 101, "ratio": 1, "action": "BUY"},
            {"con_id": 102, "ratio": 1, "action": "SELL"},
        ),
        market_data_type="LIVE",
        snapshot_timestamp=NOW,
        data_freshness="FRESH",
        combo_bid=Decimal("5.10"),
        combo_ask=Decimal("5.40"),
        combo_midpoint=Decimal("5.25"),
        synthetic_combo_bid=Decimal("5.05"),
        synthetic_combo_ask=Decimal("5.45"),
        signed_price_convention_verified=True,
        requested_limit=Decimal("5.25"),
        cash_flow_type=CashFlowType.DEBIT,
        expected_commission=Decimal("1.25"),
        capital_required=Decimal("525"),
        maximum_loss=Decimal("525"),
        spread_absolute=Decimal("0.30"),
        spread_percent=Decimal("5.71"),
        quote_age_seconds=Decimal("0.5"),
    )
    submission = NORMALIZER.submission_attempted(snapshot, NOW, order_id=42)
    proposal = NORMALIZER.reprice_proposal(
        propose_reprice(reprice()),
        "broker-reprice_preview-1",
        NOW,
    )
    assert submission.event_type == "SUBMISSION_ATTEMPTED"
    assert submission.detail is not None
    assert submission.detail["canonical_execution_status"] is None
    assert submission.detail["transmitted_to_broker"] is None
    assert submission.detail["market_snapshot"]["requested_limit"] == 5.25
    assert proposal.event_type == "REPRICE_PROPOSAL"
    assert proposal.detail is not None
    assert proposal.detail["automatic_action_allowed"] is False
    assert proposal.detail["proposal_id"] == "broker-reprice_preview-1"


def test_execution_commission_callbacks_and_recovery_identity_are_idempotent(
    tmp_path: Path,
) -> None:
    journal = BridgeJournal(tmp_path / "bridge.sqlite3")
    raw_command = {
        "intent_id": "broker-intent_123",
        "intent_type": "MANUAL_CLOSE",
        "mode": "PAPER",
        "account_guard": {"required_prefix": "DU", "live_accounts_forbidden": True},
        "position_id": "position-1",
        "preview_id": "preview-1",
        "order_ref": "TTWO-P-123",
        "ticker": "TTWO",
        "native_currency": "USD",
        "requested_quantity": 2,
        "legs": [{"con_id": 900001, "ratio": 1, "action": "SELL_TO_CLOSE"}],
        "maximum_exit_slippage_policy": 25,
        "pricing_policy": "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
        "time_in_force": "DAY",
        "transmit": False,
    }
    journal.remember_claim(PaperCommand.from_mapping(raw_command), raw_command)
    journal.mark_dispatch_started("broker-intent_123")
    execution = NORMALIZER.execution(
        ExecutionEvidence(
            exec_id="0001.01",
            order_id=42,
            perm_id=84,
            shares=Decimal("1"),
            cumulative_quantity=Decimal("1"),
            remaining_quantity=Decimal("1"),
            price=Decimal("5.25"),
            side="SLD",
            exchange="SMART",
            execution_time=NOW,
            received_at=NOW,
            combo_bid_near_fill=Decimal("5.20"),
            combo_ask_near_fill=Decimal("5.30"),
            execution_delay_seconds=Decimal("12.5"),
            slippage_vs_decision_midpoint=Decimal("0.10"),
            slippage_vs_executable_quote=Decimal("0.05"),
            partial_fill_sequence=1,
        )
    )
    journal.remember_event("broker-intent_123", execution)
    journal.remember_event("broker-intent_123", execution)
    assert execution.detail is not None
    assert execution.detail["combo_bid_near_fill"] == 5.2
    assert execution.detail["execution_delay_seconds"] == 12.5
    assert execution.detail["partial_fill_sequence"] == 1
    commission = NORMALIZER.commission(
        CommissionEvidence(
            exec_id="0001.01",
            commission=Decimal("1.25"),
            currency="USD",
            received_at=NOW,
        )
    )
    journal.remember_event("broker-intent_123", commission)
    identity = journal.unresolved_orders()[0]
    assert identity.broker_order_id == 42
    assert identity.broker_perm_id == 84
    assert identity.broker_exec_ids == ("0001.01",)
    assert len(journal.unposted_events()) == 2
    journal.close()


def test_callback_boundaries_are_preserved() -> None:
    events = [
        NORMALIZER.callback_boundary("openOrderEnd", NOW),
        NORMALIZER.callback_boundary("execDetailsEnd", NOW, 12),
        NORMALIZER.callback_boundary("completedOrdersEnd", NOW),
    ]
    assert [event.event_type for event in events] == [
        "OPEN_ORDER_END",
        "EXECUTION_END",
        "COMPLETED_ORDERS_END",
    ]


def test_gateway_event_still_rejects_unknown_callbacks() -> None:
    event = GatewayEvent(
        broker_event_key="unknown-event-123",
        event_type="NOT_A_CALLBACK",
        occurred_at=NOW,
    )
    with pytest.raises(ValueError, match="unsupported gateway event"):
        event.as_payload()
