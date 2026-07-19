from datetime import timedelta

import pytest
from pydantic import ValidationError

from take_two_options.candidates import generate_candidates
from take_two_options.data import ReadOnlyBrokerGateway
from take_two_options.domain import (
    CandidateStatus,
    EvidenceStatus,
    FreshnessStatus,
    MarketDataBundle,
    PositionSide,
    UnderlyingSnapshot,
)
from take_two_options.exceptions import ForbiddenOperation
from take_two_options.pricing import analyze_risk
from take_two_options.scenarios import deterministic_scenarios
from take_two_options.validation import apply_vetoes


def _prepared(bundle: MarketDataBundle, candidate_id: str):  # type: ignore[no-untyped-def]
    candidate = next(item for item in generate_candidates(bundle) if item.id == candidate_id)
    analyze_risk(candidate, bundle)
    deterministic_scenarios(candidate, bundle)
    return candidate


def test_stale_underlying_blocks_actionable_candidate(bundle: MarketDataBundle) -> None:
    bundle.underlying.freshness.status = FreshnessStatus.STALE
    bundle.underlying.freshness.is_stale = True
    candidate = _prepared(bundle, "ttwo-long-call")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-UNDERLYING-FRESHNESS" in reason for reason in candidate.veto_reasons)


def test_declared_current_but_over_age_fundamentals_are_vetoed(
    bundle: MarketDataBundle,
) -> None:
    bundle.fundamental.freshness.as_of = bundle.analysis_timestamp - timedelta(days=2)
    bundle.fundamental.freshness.max_age_seconds = 3600
    candidate = _prepared(bundle, "ttwo-long-call")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-FUNDAMENTALS-FRESHNESS" in reason for reason in candidate.veto_reasons)


def test_missing_bid_ask_blocks_candidate(bundle: MarketDataBundle) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    assert candidate.legs[0].option_quote is not None
    candidate.legs[0].option_quote.bid = None

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("BID-ASK" in reason for reason in candidate.veto_reasons)


def test_contract_rejects_unknown_multiplier_and_deliverable(bundle: MarketDataBundle) -> None:
    contract = bundle.option_quotes[0].contract.model_dump()
    contract["multiplier"] = 0
    contract["deliverable"] = ""

    with pytest.raises(ValidationError):
        bundle.option_quotes[0].contract.__class__.model_validate(contract)


def test_underlying_contract_rejects_missing_provenance(bundle: MarketDataBundle) -> None:
    snapshot = bundle.underlying.model_dump()
    snapshot["sources"] = []

    with pytest.raises(ValidationError):
        UnderlyingSnapshot.model_validate(snapshot)


def test_adjusted_contract_without_understood_deliverable_is_vetoed(
    bundle: MarketDataBundle,
) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    assert candidate.legs[0].option_quote is not None
    candidate.legs[0].option_quote.contract.adjusted_contract = True
    candidate.legs[0].option_quote.contract.adjustment_understood = False

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("ADJUSTMENT" in reason for reason in candidate.veto_reasons)


def test_unknown_margin_blocks_vertical(bundle: MarketDataBundle) -> None:
    bundle.portfolio.margin_known = False
    candidate = _prepared(bundle, "ttwo-bull-call-spread")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-MARGIN" in reason for reason in candidate.veto_reasons)


def test_short_american_leg_adds_assignment_and_pin_review_gate(
    bundle: MarketDataBundle,
) -> None:
    candidate = _prepared(bundle, "ttwo-bull-call-spread")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.HUMAN_REVIEW_REQUIRED
    gate = next(
        rule for rule in candidate.rule_evaluations if rule.rule_id == "GATE-ASSIGNMENT-PIN"
    )
    assert gate.passed
    assert "assignment" in gate.message
    assert "pin risk" in gate.message


def test_unhandled_earnings_event_blocks_candidate(bundle: MarketDataBundle) -> None:
    bundle.underlying.events[0].event_type = "earnings"
    bundle.underlying.events[0].name = "Illustrative earnings event"
    bundle.underlying.events[0].handled = False
    candidate = _prepared(bundle, "ttwo-stock-research")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-EVENT-RISK" in reason for reason in candidate.veto_reasons)


def test_expiration_before_catalyst_blocks_candidate(bundle: MarketDataBundle) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    assert candidate.legs[0].option_quote is not None
    candidate.legs[0].option_quote.contract.expiration = (
        bundle.fundamental.catalyst_window_start - timedelta(days=1)
    )

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-CATALYST-COVERAGE" in reason for reason in candidate.veto_reasons)


def test_unvalidated_evidence_blocks_candidate(bundle: MarketDataBundle) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    candidate.evidence[0].status = EvidenceStatus.DRAFT_TO_VALIDATE

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-EVIDENCE-STATUS" in reason for reason in candidate.veto_reasons)


def test_unvalidated_rule_blocks_candidate(bundle: MarketDataBundle) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    candidate.rule_evaluations[0].status = EvidenceStatus.DRAFT_TO_VALIDATE

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-RULE-STATUS" in reason for reason in candidate.veto_reasons)


def test_unbounded_short_call_is_disabled(bundle: MarketDataBundle) -> None:
    candidate = _prepared(bundle, "ttwo-long-call")
    candidate.id = "test-naked-short-call"
    candidate.legs[0].side = PositionSide.SHORT
    analyze_risk(candidate, bundle)
    deterministic_scenarios(candidate, bundle)

    assert apply_vetoes(candidate, bundle) is CandidateStatus.BLOCKED
    assert any("VETO-UNBOUNDED-RISK" in reason for reason in candidate.veto_reasons)


def test_no_trade_survives_data_veto_as_reference_alternative(bundle: MarketDataBundle) -> None:
    bundle.underlying.freshness.status = FreshnessStatus.STALE
    candidate = _prepared(bundle, "ttwo-no-trade")

    assert apply_vetoes(candidate, bundle) is CandidateStatus.NO_TRADE
    assert not candidate.veto_reasons
    assert any(
        rule.rule_id == "VETO-UNDERLYING-FRESHNESS" and not rule.passed
        for rule in candidate.rule_evaluations
    )


def test_broker_gateway_cannot_send_modify_or_cancel_orders() -> None:
    gateway = ReadOnlyBrokerGateway()

    with pytest.raises(ForbiddenOperation):
        gateway.submit_order({"symbol": "TTWO"})
    with pytest.raises(ForbiddenOperation):
        gateway.modify_order("1", {"limit": 1})
    with pytest.raises(ForbiddenOperation):
        gateway.cancel_order("1")
