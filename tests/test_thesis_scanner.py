from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from take_two_options.candidate_generation.factory import build_candidate, terminal_payoff
from take_two_options.domain import OptionType, PositionSide
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import (
    Architecture,
    CompiledStrategyCandidate,
    QuoteSnapshot,
)
from take_two_options.thesis_scanner.data import load_thesis_chain
from take_two_options.thesis_scanner.engine import (
    load_thesis_policy,
    run_thesis_scan,
)
from take_two_options.thesis_scanner.enumeration import (
    _trade_request,
    enumerate_bullish_candidates,
)
from take_two_options.thesis_scanner.pricing import terminal_value_thresholds
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


def _request(*, probabilities: bool = True, top: int = 3) -> ThesisScanRequest:
    return ThesisScanRequest(
        ticker="TTWO",
        direction="bullish",
        budget_eur=1_000,
        max_loss_eur=1_000,
        catalyst_date="2026-11-19",
        expiration_buffer_days=45,
        target_prices=[220, 250, 280, 300, 330, 360],
        scenario_probabilities=([0.10, 0.15, 0.20, 0.20, 0.20, 0.15] if probabilities else None),
        top=top,
        current_chain=str(CHAIN),
    )


def _quote(strike: float, *, bid: float, ask: float) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=f"TTWO270319C{int(strike * 1000):08d}",
        expiration=date(2027, 3, 19),
        option_type=OptionType.CALL,
        strike=strike,
        bid=bid,
        ask=ask,
        volume=100,
        open_interest=500,
        implied_volatility=0.35,
        quote_timestamp=datetime(2026, 7, 24, 20, tzinfo=UTC),
        multiplier=100,
        price_quality="modeled",
        source_id="unit-test",
    )


def _build_structure(
    architecture: Architecture,
    leg_specs: list[tuple[PositionSide, int, QuoteSnapshot]],
) -> CompiledStrategyCandidate:
    policy = load_thesis_policy(POLICY)
    chain = load_thesis_chain(CHAIN, ticker="TTWO")
    catalog = compile_knowledge(load_knowledge(KNOWLEDGE))
    recipe = next(item for item in catalog.recipes if item.architecture is architecture)
    trade_request = _trade_request(
        _request(),
        policy,
        chain,
        maximum_dte=600,
    )
    return build_candidate(
        architecture=architecture,
        recipe=recipe,
        leg_specs=leg_specs,
        quantity=1,
        request=trade_request,
        horizon_compatible=True,
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
    assert candidate.decision_metrics.contractual_gain_unbounded is True
    assert candidate.decision_metrics.contractual_gain_loss_ratio is None


def test_long_call_terminal_multiples_use_total_cost() -> None:
    candidate = _build_structure(
        Architecture.LONG_CALL,
        [(PositionSide.LONG, 1, _quote(100, bid=4.8, ask=5.0))],
    )
    thresholds = terminal_value_thresholds(
        candidate.legs,
        total_cost_usd=candidate.risk.total_cost,
    )
    assert candidate.risk.maximum_loss == pytest.approx(candidate.risk.total_cost)
    assert candidate.risk.maximum_gain is None
    assert candidate.risk.break_even_points == [
        pytest.approx(100 + candidate.risk.total_cost / 100, abs=1e-4)
    ]
    assert thresholds[0].spot_prices == [
        pytest.approx(100 + 2 * candidate.risk.total_cost / 100, abs=1e-4)
    ]
    assert all(threshold.attainable for threshold in thresholds)


def test_bull_call_spread_contractual_math_and_capped_multiples() -> None:
    candidate = _build_structure(
        Architecture.BULL_CALL_SPREAD,
        [
            (PositionSide.LONG, 1, _quote(100, bid=4.8, ask=5.0)),
            (PositionSide.SHORT, 1, _quote(110, bid=2.0, ask=2.2)),
        ],
    )
    width_value = (110 - 100) * 100
    expected_gain = width_value - candidate.risk.total_cost
    thresholds = terminal_value_thresholds(
        candidate.legs,
        total_cost_usd=candidate.risk.total_cost,
    )
    assert candidate.risk.maximum_loss == pytest.approx(candidate.risk.total_cost)
    assert candidate.risk.maximum_gain == pytest.approx(expected_gain)
    assert candidate.risk.break_even_points == [
        pytest.approx(100 + candidate.risk.total_cost / 100, abs=1e-4)
    ]
    assert thresholds[0].attainable is True
    assert thresholds[1].attainable is True
    assert thresholds[2].attainable is False
    assert thresholds[2].message == "Impossible — gain plafonné par la structure."


def test_call_butterfly_contractual_math_break_evens_and_two_sided_multiples() -> None:
    candidate = _build_structure(
        Architecture.CALL_BUTTERFLY,
        [
            (PositionSide.LONG, 1, _quote(100, bid=3.8, ask=4.0)),
            (PositionSide.SHORT, 2, _quote(110, bid=2.5, ask=2.7)),
            (PositionSide.LONG, 1, _quote(120, bid=1.3, ask=1.5)),
        ],
    )
    expected_gain = (110 - 100) * 100 - candidate.risk.total_cost
    thresholds = terminal_value_thresholds(
        candidate.legs,
        total_cost_usd=candidate.risk.total_cost,
    )
    assert candidate.risk.maximum_loss == pytest.approx(candidate.risk.total_cost)
    assert candidate.risk.maximum_gain == pytest.approx(expected_gain)
    assert candidate.risk.break_even_points == [
        pytest.approx(100 + candidate.risk.total_cost / 100, abs=1e-4),
        pytest.approx(120 - candidate.risk.total_cost / 100, abs=1e-4),
    ]
    assert all(threshold.attainable for threshold in thresholds)
    assert all(len(threshold.spot_prices) == 2 for threshold in thresholds)


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
    assert all(
        candidate.decision_metrics.expected_pnl_eur is None
        for candidate in report.candidates
    )
    assert "Aucun P&L espéré" in (tmp_path / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("top", [3, 5, 10])
def test_top_parameter_controls_each_profile(
    top: int,
    tmp_path: Path,
) -> None:
    output = tmp_path / f"top-{top}"
    report = run_thesis_scan(
        request=_request(top=top),
        json_out=output / "report.json",
        markdown_out=output / "report.md",
        html_out=output / "dashboard.html",
        policy_path=POLICY,
        knowledge_dir=KNOWLEDGE,
        created_at=SCAN_TIME,
    )
    assert all(len(ranking.scores) == top for ranking in report.rankings)
    assert all(
        len({score.candidate_id for score in ranking.scores}) == top
        for ranking in report.rankings
    )


def test_preview_cannot_transmit_and_fixture_builds_standalone_dashboard(
    full_report: ThesisScanReport,
) -> None:
    assert full_report.order_capability == "forbidden"
    assert len(full_report.ibkr_previews) == len(full_report.candidates)
    assert all(ticket.transmit is False for ticket in full_report.ibkr_previews)
    assert all(ticket.what_if is True for ticket in full_report.ibkr_previews)
    assert full_report.historical_evidence.status == "weak_contaminated"
    assert full_report.historical_evidence.eligibility_effect == "warning_only"
    html = Path(full_report.output_files[2]).read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert full_report.schema_version == "10.1"
    assert "Contexte de marché et hypothèses utilisateur" in html
    assert "Meilleures stratégies — <span id=\"topCount\">" in html
    assert "R.request.top" in html
    assert "Top 3 par profil" not in html
    assert "accordion-trigger" in html
    assert 'setAttribute("aria-expanded","false")' in html
    assert 'setAttribute("aria-controls",panelId)' in html
    assert 'panel.setAttribute("aria-labelledby",triggerId)' in html
    assert ":focus-visible" in html
    assert "@media(max-width:900px)" in html
    assert "score.score.toFixed(2)" in html
    assert '"#"+(index+1)' in html
    assert "Fiche décisionnelle active" in html
    assert "Gain maximal contractuel" in html
    assert "Meilleur gain parmi les scénarios modélisés" in html
    assert "Impossible — gain plafonné par la structure." in html
    assert "Tableau de P&amp;L aux objectifs" in html
    assert "Coût, perte maximale et gain potentiel" in html
    assert "Payoff terminal" in html
    assert "Courbes de P&amp;L à plusieurs dates" in html
    assert "Heatmap spot × date" in html
    assert "Sensibilité IV au catalyseur" in html
    assert "3–4. Ticket IBKR et coûts" in html
    assert "9. Risques de la structure" in html
    assert "10. Historique de backtest — séparé de la simulation actuelle" in html
    assert "Débit maximal" in html
    assert "meilleur trade garanti" not in html.lower()
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "placeOrder" not in html


def test_readme_ends_with_v11_read_only_ibkr_opra_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Données live IBKR/OPRA — frontière V11" in readme
    assert "OPRA est le flux de données temps réel des options américaines" in readme
    assert "OPRA\n  n’exécute aucun ordre" in readme
    assert "adaptateur TWS/IB Gateway injecté" in readme
    assert "session IBKR/OPRA autorisée" in readme
    assert "transmit=false" in readme
    assert "what_if=true" in readme
    assert readme.rstrip().endswith(
        "valider fraîcheur, droits, contrats, quotes combo, commissions et marges."
    )
