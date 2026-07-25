from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import Architecture
from take_two_options.thesis_scanner.data import load_thesis_chain
from take_two_options.thesis_scanner.engine import (
    load_thesis_policy,
    run_thesis_scan,
)
from take_two_options.thesis_scanner.enumeration import enumerate_bullish_candidates
from take_two_options.thesis_scanner.ranking import rank_candidates
from take_two_options.thesis_scanner.schemas import (
    IVCase,
    ThesisScanReport,
    ThesisScanRequest,
)

ROOT = Path(__file__).resolve().parents[1]
CHAIN = ROOT / "fixtures" / "thesis_scanner" / "ttwo_synthetic_chain.json"
POLICY = ROOT / "configs" / "thesis_scanner" / "default.yaml"
KNOWLEDGE = ROOT / "research" / "knowledge_items"
SCAN_TIME = datetime(2026, 7, 25, 12, tzinfo=UTC)


def _request(*, probabilities: bool = True) -> ThesisScanRequest:
    return ThesisScanRequest(
        ticker="TTWO",
        direction="bullish",
        budget_eur=1_000,
        max_loss_eur=1_000,
        catalyst_date="2026-11-19",
        expiration_buffer_days=45,
        target_prices=[220, 250, 280, 300, 330, 360],
        scenario_probabilities=([0.10, 0.15, 0.20, 0.20, 0.20, 0.15] if probabilities else None),
        top=3,
        current_chain=str(CHAIN),
    )


@pytest.fixture(scope="session")
def full_report(tmp_path_factory: pytest.TempPathFactory) -> ThesisScanReport:
    output = tmp_path_factory.mktemp("thesis-scan")
    return run_thesis_scan(
        request=_request(),
        json_out=output / "report.json",
        markdown_out=output / "report.md",
        html_out=output / "dashboard.html",
        policy_path=POLICY,
        knowledge_dir=KNOWLEDGE,
        created_at=SCAN_TIME,
    )


def test_enumerates_required_bullish_universe(full_report: ThesisScanReport) -> None:
    assert set(full_report.generated_by_architecture) == {
        Architecture.LONG_CALL.value,
        Architecture.BULL_CALL_SPREAD.value,
        Architecture.CALL_BUTTERFLY.value,
    }
    assert full_report.generated_candidates > full_report.technically_admissible_candidates
    assert any(candidate.maturity_class == "leaps" for candidate in full_report.candidates)


def test_eur_budget_and_maximum_loss_are_hard_limits(
    full_report: ThesisScanReport,
) -> None:
    for candidate in full_report.candidates:
        assert candidate.execution.total_cost_eur <= full_report.request.budget_eur
        assert candidate.maximum_loss_eur <= full_report.request.max_loss_eur
        assert candidate.base_candidate.risk.bounded is True
        assert not candidate.blockers
    assert full_report.blocked_reasons["BUDGET_EXCEEDED"] > 0
    assert full_report.blocked_reasons["MAXIMUM_LOSS_EXCEEDED"] > 0


def test_terminal_and_pre_expiry_pnl_are_internally_consistent(
    full_report: ThesisScanReport,
) -> None:
    candidate = full_report.candidates[0]
    dates = {point.valuation_date for point in candidate.scenario_points}
    start = full_report.chain.as_of.date()
    assert {
        start,
        start + timedelta(days=30),
        start + timedelta(days=60),
        start + timedelta(days=90),
        full_report.request.catalyst_date,
        candidate.expiration,
    } <= dates
    terminal = next(
        point
        for point in candidate.scenario_points
        if point.terminal and point.iv_case is IVCase.STABLE
    )
    expected = (
        terminal_payoff(candidate.base_candidate.legs, terminal.spot)
        - candidate.base_candidate.risk.total_cost
    )
    assert terminal.pnl_usd == pytest.approx(expected, abs=1e-4)
    pre_expiry = next(point for point in candidate.scenario_points if not point.terminal)
    assert pre_expiry.pnl_usd == pytest.approx(
        pre_expiry.estimated_value_usd - candidate.execution.total_cost_usd,
        abs=1e-4,
    )
    assert pre_expiry.residual_usd == pytest.approx(0, abs=1e-4)


def test_iv_scenarios_are_evaluated_with_american_engine(
    full_report: ThesisScanReport,
) -> None:
    candidate = next(
        item for item in full_report.candidates if item.architecture is Architecture.LONG_CALL
    )
    points = {
        point.iv_case: point.pnl_usd
        for point in candidate.scenario_points
        if point.valuation_date == full_report.request.catalyst_date and point.spot == 300
    }
    assert points[IVCase.UP] > points[IVCase.STABLE] > points[IVCase.DOWN]
    assert candidate.net_greeks.model == "quantlib_fd_american"


def test_long_call_risk_and_break_even_include_costs(
    full_report: ThesisScanReport,
) -> None:
    candidate = next(
        item for item in full_report.candidates if item.architecture is Architecture.LONG_CALL
    )
    leg = candidate.base_candidate.legs[0]
    expected_break_even = leg.quote.strike + candidate.execution.total_cost_usd / (
        leg.quantity * leg.quote.multiplier
    )
    assert candidate.base_candidate.risk.break_even_points == [
        pytest.approx(expected_break_even, abs=1e-4)
    ]
    assert candidate.base_candidate.risk.maximum_gain is None


def test_rankings_are_independent_and_deterministic(
    full_report: ThesisScanReport,
) -> None:
    first = rank_candidates(
        [candidate.model_copy(deep=True) for candidate in full_report.candidates],
        request=full_report.request,
        policy=full_report.policy,
        spot=full_report.chain.spot,
    )
    second = rank_candidates(
        [candidate.model_copy(deep=True) for candidate in full_report.candidates],
        request=full_report.request,
        policy=full_report.policy,
        spot=full_report.chain.spot,
    )
    assert first == second
    assert {ranking.profile.value for ranking in first} == {
        "prudent",
        "balanced",
        "aggressive",
    }
    assert len({ranking.scores[0].candidate_id for ranking in first}) >= 2


def test_stale_and_invalid_quotes_are_rejected_explicitly() -> None:
    chain = load_thesis_chain(CHAIN, ticker="TTWO")
    stale = chain.quotes[0].model_copy(
        update={"quote_timestamp": datetime(2026, 7, 1, 20, tzinfo=UTC)}
    )
    invalid = chain.quotes[1].model_copy(update={"bid": 0.0, "ask": 0.0})
    reduced = chain.model_copy(update={"quotes": [stale, invalid]})
    result = enumerate_bullish_candidates(
        request=_request(),
        policy=load_thesis_policy(POLICY),
        chain=reduced,
        catalog=compile_knowledge(load_knowledge(KNOWLEDGE)),
        scan_time=SCAN_TIME,
    )
    assert result.quote_rejections.usable_calls == 0
    assert result.quote_rejections.reasons["QUOTE_STALE"] == 1
    assert result.quote_rejections.reasons["BID_ASK_NON_POSITIVE"] == 1


def test_probabilities_are_never_invented(
    tmp_path: Path,
) -> None:
    report = run_thesis_scan(
        request=_request(probabilities=False),
        json_out=tmp_path / "report.json",
        markdown_out=tmp_path / "report.md",
        html_out=tmp_path / "dashboard.html",
        policy_path=POLICY,
        knowledge_dir=KNOWLEDGE,
        created_at=SCAN_TIME,
    )
    assert report.probability_status == "not_provided"
    assert all(candidate.expected_pnl_usd is None for candidate in report.candidates)
    assert all(candidate.probability_success is None for candidate in report.candidates)
    assert "Aucun P&L espéré" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_preview_cannot_transmit_and_fixture_builds_standalone_dashboard(
    full_report: ThesisScanReport,
) -> None:
    assert full_report.order_capability == "forbidden"
    assert full_report.ibkr_previews
    assert all(ticket.transmit is False for ticket in full_report.ibkr_previews)
    assert all(ticket.what_if is True for ticket in full_report.ibkr_previews)
    html = Path(full_report.output_files[2]).read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "Payoff terminal" in html
    assert "Heatmap spot × date" in html
    assert "Previews IBKR — aucune transmission" in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "placeOrder" not in html
