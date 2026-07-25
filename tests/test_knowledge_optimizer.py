from __future__ import annotations

import inspect
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from take_two_options.candidate_generation.enumerator import enumerate_candidates
from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.candidate_generation.pruning import prune_candidate
from take_two_options.decision.request import load_trade_request
from take_two_options.domain import OptionType, PositionSide
from take_two_options.forecasting.contracts import HistoricalReturnSeries
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.conflicts import detect_conflicts
from take_two_options.knowledge.loader import KnowledgeCorpus, load_knowledge
from take_two_options.knowledge.schemas import (
    Architecture,
    DecisionReport,
    MarketSnapshot,
    ParameterDefinition,
    ParameterOrigin,
    QuoteSnapshot,
    ReportAnalysis,
    ResearchRun,
    Verdict,
)
from take_two_options.knowledge.validator import validate_knowledge
from take_two_options.maintenance.capital_recovery import recovery_action
from take_two_options.maintenance.exits import exit_reason
from take_two_options.maintenance.rolling import roll_review_required
from take_two_options.maintenance.state_machine import PositionState, transition
from take_two_options.optimization.parameter_stability import local_stability
from take_two_options.optimization.trial_registry import TrialRegistry
from take_two_options.reporting import ibkr_ticket
from take_two_options.reporting.decision_report import write_decision_report
from take_two_options.reporting.ibkr_ticket import (
    TicketBlockedError,
    build_ibkr_preview,
    write_blocked_ticket_status,
)
from take_two_options.simulation.conditional_monte_carlo import (
    simulate_conditional_paths,
)
from take_two_options.validation.gates import (
    evaluate_validation_gates,
    sample_gate,
)
from take_two_options.validation.holdout import (
    contaminated_holdout_ids,
    holdout_status,
)
from take_two_options.validation.nested_walk_forward import (
    nested_purged_walk_forward,
)
from take_two_options.validation.pbo import probability_of_backtest_overfitting
from take_two_options.validation.placebo import placebo_diagnostics
from take_two_options.validation.purging import (
    LabeledObservation,
    dynamic_embargo_days,
)
from take_two_options.validation.stress import stress_candidate, stress_passed

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "research" / "knowledge_items"
REQUEST_PATH = ROOT / "configs" / "trades" / "ttwo_gta6_1000eur.yaml"
CONTAMINATED_MANIFEST = (
    ROOT / "validation" / "contaminated_holdouts" / "v7_v8_v9" / "manifest.json"
)


def _quote(
    *,
    expiration: date,
    strike: float,
    bid: float,
    ask: float,
) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=f"TTWO{expiration:%y%m%d}C{int(strike * 1000):08d}",
        expiration=expiration,
        option_type=OptionType.CALL,
        strike=strike,
        bid=bid,
        ask=ask,
        volume=50,
        open_interest=250,
        implied_volatility=0.30,
        delta=None,
        quote_timestamp=datetime(2026, 7, 24, 20, tzinfo=UTC),
        price_quality="eod_bid_ask",
        source_id="test-chain",
    )


def _snapshot() -> MarketSnapshot:
    expirations = [date(2027, 8, 20), date(2028, 1, 21)]
    prices = [(90.0, 14.0, 14.2), (100.0, 8.0, 8.2), (110.0, 4.0, 4.2)]
    quotes = [
        _quote(expiration=expiration, strike=strike, bid=bid, ask=ask)
        for expiration in expirations
        for strike, bid, ask in prices
    ]
    return MarketSnapshot(
        snapshot_id="test-snapshot",
        ticker="TTWO",
        as_of=datetime(2026, 7, 24, 20, tzinfo=UTC),
        spot=100,
        spot_timestamp=datetime(2026, 7, 24, 20, tzinfo=UTC),
        quote_quality="eod_bid_ask",
        source_ids=["test-chain"],
        quotes=quotes,
        available_expirations=expirations,
    )


def _catalog_and_request():
    catalog = compile_knowledge(load_knowledge(KNOWLEDGE_DIR))
    selected_recipes = [
        recipe
        for recipe in catalog.recipes
        if recipe.architecture in {Architecture.LONG_CALL, Architecture.BULL_CALL_SPREAD}
    ]
    catalog = catalog.model_copy(update={"recipes": selected_recipes})
    request = load_trade_request(REQUEST_PATH).model_copy(
        update={
            "currency": "USD",
            "budget": 1_000.0,
            "maximum_loss": 1_000.0,
            "fx_rate_to_usd": None,
            "fx_rate_as_of": None,
            "maximum_contracts": 4,
            "allowed_structures": [
                Architecture.LONG_CALL,
                Architecture.BULL_CALL_SPREAD,
            ],
        }
    )
    return catalog, request


def _empty_report() -> DecisionReport:
    catalog, request = _catalog_and_request()
    now = datetime(2026, 7, 25, 10, tzinfo=UTC)
    run = ResearchRun(
        run_id="test-run",
        started_at=now,
        completed_at=now,
        seed=7,
        config_hash="a" * 64,
        code_version="test",
        request_id=request.request_id,
        knowledge_hash=catalog.knowledge_hash,
        status="completed",
    )
    return DecisionReport(
        report_id="test-report",
        created_at=now,
        analysis=ReportAnalysis(
            ticker=request.ticker,
            budget=request.budget,
            currency=request.currency,
            thesis=request.thesis_summary,
            horizon_days=(request.horizon_min_days, request.horizon_max_days),
            data_date=None,
            data_quality="test",
            holdout_status="NOT_REACHED_AFTER_HARD_VETOES",
            total_trials=0,
        ),
        verdict=Verdict.NO_TRADE,
        request=request,
        research_run=run,
        no_trade_reasons=["test hard veto"],
        order_capability="forbidden",
    )


def test_knowledge_corpus_validates_and_compiles_all_bounded_recipes() -> None:
    corpus = load_knowledge(KNOWLEDGE_DIR)
    validation = validate_knowledge(corpus)
    catalog = compile_knowledge(corpus)

    assert validation.valid
    assert validation.item_count == 3
    assert validation.recipe_count == 15
    assert validation.modern_validation_count == 1
    assert len(catalog.rules) == 3
    assert len(catalog.recipes) == 15
    assert not catalog.blocked_items
    assert "leaps" not in {architecture.value for architecture in Architecture}
    assert all(recipe.bounded_risk_required for recipe in catalog.recipes)


def test_conflicting_structured_rules_are_exposed_not_silently_resolved() -> None:
    corpus = load_knowledge(KNOWLEDGE_DIR)
    first = corpus.items[0].model_copy(
        update={
            "parameters_provided": [
                ParameterDefinition(
                    name="test_threshold",
                    value=1,
                    origin=ParameterOrigin.EXPERIMENTAL,
                )
            ]
        }
    )
    conflicting_parameter = first.parameters_provided[0].model_copy(
        update={"value": 999}
    )
    duplicate = first.model_copy(
        update={
            "knowledge_id": f"{first.knowledge_id}-conflict",
            "parameters_provided": [conflicting_parameter],
        }
    )
    synthetic = KnowledgeCorpus(
        items=[first, duplicate],
        recipes=[],
        modern_validations=[],
    )

    conflicts = detect_conflicts(synthetic)

    assert len(conflicts) == 1
    assert first.parameters_provided[0].name in conflicts[0]


def test_candidate_enumerator_uses_listed_expirations_whole_quantities_and_sides() -> None:
    catalog, request = _catalog_and_request()

    result = enumerate_candidates(catalog, request, _snapshot())

    assert len(result.candidates) > 6
    assert set(result.combinations_by_architecture) == {
        "long_call",
        "bull_call_spread",
    }
    assert {leg.quote.expiration for item in result.candidates for leg in item.legs} == {
        date(2027, 8, 20),
        date(2028, 1, 21),
    }
    assert all(leg.quantity == int(leg.quantity) for item in result.candidates for leg in item.legs)
    assert all(item.risk.bounded for item in result.candidates)
    assert all(
        leg.entry_price == (leg.quote.ask if leg.side is PositionSide.LONG else leg.quote.bid)
        for item in result.candidates
        for leg in item.legs
    )
    assert any(not item.hard_vetoes for item in result.candidates)


def test_current_candidate_payoff_budget_bounded_risk_and_pruning() -> None:
    catalog, request = _catalog_and_request()
    candidates = enumerate_candidates(catalog, request, _snapshot()).candidates
    feasible = next(item for item in candidates if not item.hard_vetoes)

    assert terminal_payoff(feasible.legs, 200) >= terminal_payoff(feasible.legs, 0)
    assert feasible.risk.maximum_loss <= request.budget
    assert feasible.risk.maximum_loss <= request.maximum_loss
    assert feasible.risk.bounded
    assert prune_candidate(feasible) == []
    assert any("BUDGET_EXCEEDED" in item.hard_vetoes for item in candidates)


def test_combo_round_trip_spread_is_a_hard_liquidity_veto() -> None:
    catalog, request = _catalog_and_request()
    snapshot = _snapshot()
    widened = snapshot.model_copy(
        update={
            "quotes": [
                quote.model_copy(update={"bid": 0.1, "ask": quote.ask})
                for quote in snapshot.quotes
            ]
        }
    )

    candidates = enumerate_candidates(catalog, request, widened).candidates
    spreads = [
        item
        for item in candidates
        if item.architecture is Architecture.BULL_CALL_SPREAD
    ]

    assert spreads
    assert all("LIQUIDITY_FAILED" in item.hard_vetoes for item in spreads)
    assert any("COMBO_SPREAD_FAILED" in item.hard_vetoes for item in spreads)


def test_sample_gates_preserve_minimums_and_contaminated_holdouts_win() -> None:
    gate = sample_gate(configured_minimum=20, available_observations=3)
    contaminated = contaminated_holdout_ids(CONTAMINATED_MANIFEST)
    status, reasons = holdout_status(
        requested_holdout_id="v9",
        contaminated_ids=contaminated,
        observations=500,
        configured_minimum=4,
    )

    assert gate.configured_minimum == 20
    assert gate.available_observations == 3
    assert gate.status == "INSUFFICIENT_DATA"
    assert contaminated == {"v7", "v8", "v9"}
    assert status == "CONTAMINATED"
    assert "previously inspected" in reasons[0]
    clean_status, clean_reasons = holdout_status(
        requested_holdout_id="fresh-locked-holdout",
        contaminated_ids=contaminated,
        observations=4,
        configured_minimum=4,
    )
    assert clean_status == "PASSED"
    assert clean_reasons == []


def test_nested_purging_dynamic_embargo_pbo_and_validation_gates() -> None:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    observations = [
        LabeledObservation(
            observation_id=f"obs-{index}",
            feature_start=start + timedelta(days=index),
            entry=start + timedelta(days=index),
            exit=start + timedelta(days=index),
        )
        for index in range(16)
    ]
    windows = nested_purged_walk_forward(
        observations,
        minimum_train=4,
        minimum_validation=2,
        minimum_test=2,
        embargo_days=0,
    )
    pbo = probability_of_backtest_overfitting(
        [
            [0.1, 0.2, -0.1, 0.3],
            [-0.2, 0.4, 0.2, -0.1],
            [0.0, 0.1, 0.0, 0.1],
        ]
    )
    _, request = _catalog_and_request()
    metrics = evaluate_validation_gates(
        policy=request.final_holdout_policy.model_copy(
            update={"locked_holdout_id": "v9"}
        ),
        train_returns=[0.01] * 20,
        validation_returns=[0.01] * 8,
        test_returns=[0.01] * 8,
        holdout_returns=[0.01] * 4,
        contaminated_ids={"v7", "v8", "v9"},
        performance_matrix=[[0.1, 0.2, -0.1, 0.3], [0.0, -0.1, 0.1, 0.2]],
        nested_windows=len(windows),
        purged_observations=0,
        embargo_days=dynamic_embargo_days(
            observations, feature_lookback_days=5
        ),
        stability=0.8,
        stress_ok=True,
        placebo_ok=True,
        real_trial_count=100,
    )

    assert windows
    assert dynamic_embargo_days(observations, feature_lookback_days=5) == 5
    assert pbo is not None and 0 <= pbo <= 1
    assert metrics.status == "CONTAMINATED"
    assert metrics.holdout.configured_minimum == 4


def test_placebo_refuses_to_invent_a_result_when_history_is_short() -> None:
    results, passed = placebo_diagnostics([0.1, -0.1, 0.2], seed=7)

    assert results == {"available_observations": 3.0}
    assert passed is None


def test_exit_roll_stability_and_stress_behaviors_are_deterministic() -> None:
    catalog, request = _catalog_and_request()
    candidates = enumerate_candidates(catalog, request, _snapshot()).candidates
    center = next(item for item in candidates if not item.hard_vetoes)
    neighbors = [
        center.model_copy(deep=True),
        center.model_copy(deep=True),
        center.model_copy(deep=True),
    ]
    for index, candidate in enumerate(neighbors):
        candidate.candidate_id = f"neighbor-{index}"
        candidate.evaluation.conservative_expected_pnl = 100.0 + index
    center.evaluation.conservative_expected_pnl = 101.0
    center.candidate_id = "center"
    stability = local_stability(center, neighbors)
    stress = stress_candidate(center)

    assert exit_reason(
        return_on_risk=0.6,
        days_held=3,
        profit_target=0.5,
        stop_loss=0.4,
        maximum_holding_days=20,
    ) == "profit_target"
    assert exit_reason(
        return_on_risk=-0.5,
        days_held=3,
        profit_target=0.5,
        stop_loss=0.4,
        maximum_holding_days=20,
    ) == "stop_loss"
    assert exit_reason(
        return_on_risk=0,
        days_held=20,
        profit_target=0.5,
        stop_loss=0.4,
        maximum_holding_days=20,
    ) == "time_exit"
    assert roll_review_required(
        as_of=date(2027, 7, 25),
        expiration=date(2027, 8, 20),
        threshold_days=30,
    )
    assert stability is not None and 0 <= stability <= 1
    assert stress["spread_x1_5_expected_pnl"] < stress["baseline_expected_pnl"]
    assert stress_passed(stress)
    center.evaluation.conservative_expected_pnl = 1.0
    assert stress_passed(stress_candidate(center)) is False


def test_conditional_models_are_separate_and_reproducible_by_seed() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    closes = [100.0]
    for index in range(40):
        closes.append(closes[-1] * (1.002 if index % 3 else 0.997))
    series = HistoricalReturnSeries(
        ticker="TTWO",
        as_of=start + timedelta(days=40),
        timestamps=[start + timedelta(days=index) for index in range(len(closes))],
        closes=closes,
        source_id="test-history",
    )

    first = simulate_conditional_paths(
        series, spot=100, horizon_days=10, paths=16, seed=42
    )
    second = simulate_conditional_paths(
        series, spot=100, horizon_days=10, paths=16, seed=42
    )

    assert [item.model_id for item in first] == [
        "gbm_historical",
        "conditional_historical_bootstrap",
    ]
    assert [item.paths for item in first] == [item.paths for item in second]
    assert first[0].paths != first[1].paths


def test_trial_registry_is_exhaustive_deterministic_and_append_only(tmp_path: Path) -> None:
    registry = TrialRegistry(run_id="run", seed=7, config_hash="b" * 64)
    first = registry.register(stage="generation", outcome="generated")
    second = registry.register(stage="pruning", outcome="pruned", reason="budget")
    output = tmp_path / "trials.jsonl"
    registry.write_jsonl(output)
    rows = [json.loads(line) for line in output.read_text().splitlines()]

    assert first.trial_id == "run-trial-00000001"
    assert second.trial_id == "run-trial-00000002"
    assert registry.counts() == {"generation": 1, "pruning": 1}
    assert len(rows) == len(registry.records) == 2
    assert rows[1]["reason"] == "budget"


def test_reports_and_broker_artifacts_remain_read_only(tmp_path: Path) -> None:
    report = _empty_report()
    written = write_decision_report(report, tmp_path)
    blocked_path = write_blocked_ticket_status(
        written, tmp_path / "ibkr_ticket_status.json"
    )

    assert (tmp_path / "decision_report.json").is_file()
    assert (tmp_path / "decision_report.md").is_file()
    assert (tmp_path / "decision_report.html").is_file()
    assert len(written.visualization_files) == 16
    assert json.loads(blocked_path.read_text())["ticket_created"] is False
    with pytest.raises(TicketBlockedError):
        build_ibkr_preview(report, "missing")
    source = inspect.getsource(ibkr_ticket)
    assert "placeOrder" not in source
    assert '"transmit": False' in source
    assert '"order_capability": "forbidden"' in source


def test_maintenance_requires_human_for_live_and_uses_whole_contract_recovery() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        transition(
            PositionState.PLANNED,
            PositionState.LIVE_ASSISTED_OPEN,
            reason="skip preview",
            timestamp=datetime.now(UTC),
        )
    assert recovery_action(long_contracts=1, target_contracts_to_sell=1) == (
        "close_entire_position"
    )
    assert recovery_action(long_contracts=3, target_contracts_to_sell=1) == (
        "sell_1_whole_contracts"
    )
