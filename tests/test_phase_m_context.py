from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from take_two_options.budget import (
    BrokerCapitalContext,
    BudgetGuaranteeStatus,
    BudgetStatus,
    FXAccountMode,
    FXExecutionCost,
    FXExecutionCostStatus,
    FXRate,
    LifecycleCapitalStatus,
)
from take_two_options.candidate_generation import enumerator as enumerator_module
from take_two_options.candidate_generation.enumerator import EnumerationResult
from take_two_options.candidate_generation.factory import build_candidate
from take_two_options.candidates import generate_candidates
from take_two_options.config.contracts import ProspectiveBudgetConfig
from take_two_options.config.loader import load_prospective_budget_config
from take_two_options.data import FixtureDataProvider
from take_two_options.decision import pipeline
from take_two_options.decision.request import load_trade_request
from take_two_options.domain import (
    ExerciseStyle,
    MarketDataBundle,
    OptionType,
    PositionSide,
)
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import Architecture, MarketSnapshot, QuoteSnapshot
from take_two_options.phase_m_context import (
    PhaseMDecisionContext,
    build_phase_m_decision_context,
    load_phase_m_decision_context,
)
from take_two_options.pricing import analyze_risk
from take_two_options.quantitative.contracts import EvidenceLevel
from take_two_options.quantitative.trade_economics import build_trade_economics_ticket
from take_two_options.trade_economics_models import ExitPath

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/phase_m/v2/ttwo_prospective_budget.yaml"
REQUEST_PATH = ROOT / "configs/trades/ttwo_gta6_1000eur.yaml"
KNOWLEDGE_DIR = ROOT / "research/knowledge_items"
EVIDENCE_TIME = datetime(2026, 7, 23, 19, tzinfo=UTC)
CONTEXT_TIME = datetime(2026, 8, 24, 20, tzinfo=UTC)


def _prospective_config(
    *,
    buffer_days: int = 3,
    currency: str = "EUR",
) -> ProspectiveBudgetConfig:
    config = load_prospective_budget_config(CONFIG_PATH)
    lifecycle = config.mixed_expiry_lifecycle.model_copy(
        update={
            "close_buffer_calendar_days": buffer_days,
            "source": "test-phase-m-lifecycle",
            "version": "test-v1",
        }
    )
    policy = config.budget_policy.model_copy(update={"currency": currency})
    return config.model_copy(
        deep=True,
        update={"budget_policy": policy, "mixed_expiry_lifecycle": lifecycle},
    )


def _fx_rate(*, rate: float = 1.0, timestamp: datetime = EVIDENCE_TIME) -> FXRate:
    return FXRate(
        source_currency="USD",
        policy_currency="EUR",
        rate_to_policy_currency=rate,
        timestamp=timestamp,
        source="test-fx-rate",
    )


def _fx_cost(
    *,
    amount: float | None = 6.0,
    status: FXExecutionCostStatus = FXExecutionCostStatus.KNOWN,
) -> FXExecutionCost:
    return FXExecutionCost(
        mode=FXAccountMode.CONVERT_AT_ENTRY_AND_EXIT,
        status=status,
        cost_amount=amount,
        currency="EUR" if amount is not None else None,
        source="test-fx-cost",
        timestamp=EVIDENCE_TIME,
    )


def _broker(*, buying_power: float = 900.0) -> BrokerCapitalContext:
    return BrokerCapitalContext(
        buying_power_requirement=buying_power,
        currency="EUR",
        source="test-broker-capital",
        timestamp=EVIDENCE_TIME,
        validated=True,
    )


def _context(
    *,
    config: ProspectiveBudgetConfig | None = None,
    fx_rate: FXRate | None = None,
    fx_cost: FXExecutionCost | None = None,
    broker: BrokerCapitalContext | None = None,
    created_at: datetime = CONTEXT_TIME,
) -> PhaseMDecisionContext:
    return build_phase_m_decision_context(
        config or _prospective_config(),
        prospective_config_source=CONFIG_PATH.as_posix(),
        fx_rate=fx_rate,
        fx_execution_cost=fx_cost,
        broker_capital_context=broker,
        created_at=created_at,
    )


def _request():
    return load_trade_request(REQUEST_PATH).model_copy(
        update={
            "currency": "USD",
            "budget": 1_000.0,
            "maximum_loss": 1_000.0,
            "fx_rate_to_usd": None,
            "fx_rate_as_of": None,
        }
    )


def _quote(
    *,
    symbol: str,
    expiration: date,
    strike: float,
    bid: float,
    ask: float,
) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=symbol,
        expiration=expiration,
        option_type=OptionType.CALL,
        exercise_style=ExerciseStyle.AMERICAN,
        strike=strike,
        bid=bid,
        ask=ask,
        volume=100,
        open_interest=500,
        implied_volatility=0.30,
        quote_timestamp=EVIDENCE_TIME,
        multiplier=100,
        multiplier_status=EvidenceLevel.KNOWN,
        contract_adjustment_status=EvidenceLevel.KNOWN,
        deliverable_description="standard listed deliverable",
        price_quality="eod_bid_ask",
        source_id="test-chain",
    )


def _market_snapshot(*, quotes: list[QuoteSnapshot] | None = None) -> MarketSnapshot:
    selected_quotes = quotes or [
        _quote(
            symbol="TTWO280121C00230000",
            expiration=date(2028, 1, 21),
            strike=230,
            bid=14.90,
            ask=14.963,
        )
    ]
    return MarketSnapshot(
        snapshot_id="phase-m-test-snapshot",
        ticker="TTWO",
        as_of=EVIDENCE_TIME,
        spot=230.0,
        spot_timestamp=EVIDENCE_TIME,
        quote_quality="eod_bid_ask",
        source_ids=["test-chain"],
        quotes=selected_quotes,
        available_expirations=sorted(
            {quote.expiration for quote in selected_quotes}
        ),
        data_warnings=["Synthetic Phase M test fixture"],
    )


def _install_pipeline_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    snapshot: MarketSnapshot | None = None,
) -> MarketSnapshot:
    selected_snapshot = snapshot or _market_snapshot()
    history_path = tmp_path / "phase_m_history.json"
    history_path.write_text(
        json.dumps(
            {
                "source": {"id": "phase-m-test-history"},
                "points": [
                    {
                        "timestamp": (
                            datetime(2026, 7, 1, 19, tzinfo=UTC)
                            + timedelta(days=index)
                        ).isoformat(),
                        "close": 225.0 + index * 0.25 + index % 3,
                    }
                    for index in range(23)
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pipeline,
        "load_latest_market_snapshot",
        lambda **_: selected_snapshot,
    )
    monkeypatch.setattr(pipeline, "_historical_path", lambda _: history_path)
    return selected_snapshot


def _recipe(architecture: Architecture):
    catalog = compile_knowledge(load_knowledge(KNOWLEDGE_DIR))
    return next(item for item in catalog.recipes if item.architecture is architecture)


def _fast_bundle() -> MarketDataBundle:
    bundle = FixtureDataProvider(ROOT / "fixtures/ttwo_v1_fixture.json").load_bundle()
    config = bundle.trade_economics
    config.time_decay_horizons_days = [1, 7, 400]
    config.scenario_horizons_days = [7, 400]
    config.spot_grid.values = [0.85, 1.0, 1.15]
    config.volatility_scenarios = config.volatility_scenarios[:3]
    config.greek_bumps.grid_levels = [50, 75]
    config.breakeven_solver.grid_points = 101
    config.exit_cost_model.exercise_cost = 0.0
    config.exit_cost_model.assignment_cost = 0.0
    config.exit_cost_model.settlement_cost = 0.0
    return bundle


def test_canonical_context_loads_once_serializes_provenance_and_excludes_secret_fields() -> None:
    context = load_phase_m_decision_context(CONFIG_PATH, created_at=CONTEXT_TIME)
    restored = PhaseMDecisionContext.model_validate_json(context.model_dump_json())

    assert restored.context_hash == context.context_hash
    assert restored.context_id == context.context_id
    assert restored.prospective_config_hash
    assert CONFIG_PATH.as_posix() in restored.source_ids
    assert restored.prospective_config.holdout_status == "UNOPENED"
    assert restored.prospective_config.opra_status == "NOT_STARTED"
    serialized = restored.model_dump_json().lower()
    for forbidden in ("api_key", "password", "session_token", "cloudflare_secret"):
        assert forbidden not in serialized


def test_context_hash_is_stable_but_changes_with_each_governed_input() -> None:
    base = _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(), broker=_broker())
    same = _context(
        fx_rate=_fx_rate(),
        fx_cost=_fx_cost(),
        broker=_broker(),
        created_at=CONTEXT_TIME + timedelta(minutes=5),
    )
    variants = [
        _context(fx_rate=_fx_rate(rate=0.99), fx_cost=_fx_cost(), broker=_broker()),
        _context(
            fx_rate=_fx_rate(timestamp=EVIDENCE_TIME - timedelta(minutes=1)),
            fx_cost=_fx_cost(),
            broker=_broker(),
        ),
        _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(amount=7), broker=_broker()),
        _context(
            config=_prospective_config(buffer_days=2),
            fx_rate=_fx_rate(),
            fx_cost=_fx_cost(),
            broker=_broker(),
        ),
        _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(), broker=_broker(buying_power=901)),
    ]

    assert same.context_hash == base.context_hash
    assert same.context_id == base.context_id
    assert all(item.context_hash != base.context_hash for item in variants)


def test_phase_m_requires_explicit_lifecycle_and_never_uses_enumerator_default() -> None:
    payload = load_prospective_budget_config(CONFIG_PATH).model_dump(mode="json")
    payload.pop("mixed_expiry_lifecycle")
    with pytest.raises(ValidationError):
        ProspectiveBudgetConfig.model_validate(payload)

    from take_two_options.candidate_generation.enumerator import enumerate_candidates

    with pytest.raises(ValueError, match="PHASE_M_LIFECYCLE_CONTEXT_MISSING"):
        enumerate_candidates(
            compile_knowledge(load_knowledge(KNOWLEDGE_DIR)),
            _request(),
            _market_snapshot(),
            budget_policy=_prospective_config().budget_policy,
            phase_m_context_id="phase-m-context-" + "a" * 16,
            phase_m_context_hash="a" * 64,
        )


def test_analyze_trade_propagates_exact_context_objects_without_mutating_static_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(), broker=_broker())
    static_before = context.prospective_config.model_dump(mode="json")
    captured: dict[str, Any] = {}
    _install_pipeline_data(monkeypatch, tmp_path)

    def capture_enumeration(*args: Any, **kwargs: Any) -> EnumerationResult:
        captured.update(kwargs)
        return EnumerationResult(search_spaces=[], candidates=[])

    monkeypatch.setattr(pipeline, "enumerate_candidates", capture_enumeration)
    report = pipeline.analyze_trade(
        request_path=REQUEST_PATH,
        report_dir=tmp_path,
        knowledge_dir=KNOWLEDGE_DIR,
        phase_m_context=context,
    )

    assert captured["budget_policy"] is context.prospective_config.budget_policy
    assert captured["fx"] is context.fx_rate
    assert captured["fx_cost"] is context.fx_execution_cost
    assert captured["broker_context"] is context.broker_capital_context
    assert (
        captured["mixed_expiry_lifecycle"]
        is context.prospective_config.mixed_expiry_lifecycle
    )
    assert captured["phase_m_context_id"] == context.context_id
    assert captured["phase_m_context_hash"] == context.context_hash
    assert report.phase_m_context_id == context.context_id
    assert report.phase_m_context_hash == context.context_hash
    assert context.prospective_config.model_dump(mode="json") == static_before


def test_fx_cost_known_blocks_1497_plus_6_and_unknown_cost_fails_closed() -> None:
    context = _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(), broker=None)
    quote = _quote(
        symbol="TTWO270820C00100000",
        expiration=date(2027, 8, 20),
        strike=100,
        bid=14.90,
        ask=14.963,
    )
    known = build_candidate(
        architecture=Architecture.LONG_CALL,
        recipe=_recipe(Architecture.LONG_CALL),
        leg_specs=[(PositionSide.LONG, 1, quote)],
        quantity=1,
        request=_request(),
        horizon_compatible=True,
        budget_policy=context.prospective_config.budget_policy,
        fx=context.fx_rate,
        fx_cost=context.fx_execution_cost,
        broker_context=context.broker_capital_context,
        mixed_expiry_lifecycle=context.prospective_config.mixed_expiry_lifecycle,
        phase_m_context_id=context.context_id,
        phase_m_context_hash=context.context_hash,
    )
    assert known.budget_diagnostics is not None
    assert known.budget_diagnostics.converted_entry_cash_before_fx_cost == pytest.approx(1497)
    assert known.budget_diagnostics.entry_fx_cost == 6
    assert known.budget_diagnostics.required_entry_cash_after_fx == pytest.approx(1503)
    assert known.budget_diagnostics.budget_status is BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING

    unknown_cost = _fx_cost(amount=None, status=FXExecutionCostStatus.UNKNOWN)
    unknown_context = _context(fx_rate=_fx_rate(), fx_cost=unknown_cost, broker=None)
    unknown = build_candidate(
        architecture=Architecture.LONG_CALL,
        recipe=_recipe(Architecture.LONG_CALL),
        leg_specs=[(PositionSide.LONG, 1, quote)],
        quantity=1,
        request=_request(),
        horizon_compatible=True,
        budget_policy=unknown_context.prospective_config.budget_policy,
        fx=unknown_context.fx_rate,
        fx_cost=unknown_context.fx_execution_cost,
        broker_context=None,
        mixed_expiry_lifecycle=(
            unknown_context.prospective_config.mixed_expiry_lifecycle
        ),
        phase_m_context_id=unknown_context.context_id,
        phase_m_context_hash=unknown_context.context_hash,
    )
    assert unknown.budget_diagnostics is not None
    assert unknown.budget_diagnostics.research_eligible
    assert not unknown.budget_diagnostics.paper_eligible
    assert unknown.budget_diagnostics.budget_guarantee_status is BudgetGuaranteeStatus.UNPROVEN
    assert "FX_EXECUTION_COST_UNKNOWN" in unknown.budget_diagnostics.reason_codes
    assert unknown.budget_diagnostics.entry_fx_cost is None


def test_fx_cost_cases_run_through_analyze_enumerator_and_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    snapshot = _market_snapshot(
        quotes=[
            _quote(
                symbol="TTWO280121C00230000",
                expiration=date(2028, 1, 21),
                strike=230,
                bid=14.90,
                ask=14.963,
            )
        ]
    )
    _install_pipeline_data(monkeypatch, tmp_path, snapshot=snapshot)
    captured: list[dict[str, Any]] = []
    real_build_candidate = build_candidate

    def capture_build_candidate(*args: Any, **kwargs: Any):
        captured.append(kwargs)
        return real_build_candidate(*args, **kwargs)

    monkeypatch.setattr(
        enumerator_module,
        "build_candidate",
        capture_build_candidate,
    )

    known_context = _context(
        fx_rate=_fx_rate(),
        fx_cost=_fx_cost(),
        broker=_broker(),
    )
    known_report = pipeline.analyze_trade(
        request_path=REQUEST_PATH,
        report_dir=tmp_path / "known",
        knowledge_dir=KNOWLEDGE_DIR,
        phase_m_context=known_context,
    )
    known_diagnostics = known_report.candidate_comparison[0]["budget_diagnostics"]

    assert captured
    assert captured[0]["budget_policy"] is known_context.prospective_config.budget_policy
    assert captured[0]["fx"] is known_context.fx_rate
    assert captured[0]["fx_cost"] is known_context.fx_execution_cost
    assert captured[0]["broker_context"] is known_context.broker_capital_context
    assert (
        captured[0]["mixed_expiry_lifecycle"]
        is known_context.prospective_config.mixed_expiry_lifecycle
    )
    assert known_diagnostics["converted_entry_cash_before_fx_cost"] == pytest.approx(1497)
    assert known_diagnostics["entry_fx_cost"] == 6
    assert known_diagnostics["required_entry_cash_after_fx"] == pytest.approx(1503)
    assert known_diagnostics["budget_status"] == "EXCEEDS_HARD_BUDGET_CEILING"

    known_calls = len(captured)
    unknown_context = _context(
        fx_rate=_fx_rate(),
        fx_cost=_fx_cost(amount=None, status=FXExecutionCostStatus.UNKNOWN),
    )
    unknown_report = pipeline.analyze_trade(
        request_path=REQUEST_PATH,
        report_dir=tmp_path / "unknown",
        knowledge_dir=KNOWLEDGE_DIR,
        phase_m_context=unknown_context,
    )
    unknown_diagnostics = unknown_report.candidate_comparison[0]["budget_diagnostics"]

    assert len(captured) > known_calls
    assert captured[known_calls]["fx_cost"] is unknown_context.fx_execution_cost
    assert unknown_diagnostics["research_eligible"] is True
    assert unknown_diagnostics["paper_eligible"] is False
    assert unknown_diagnostics["budget_guarantee_status"] == "UNPROVEN"
    assert "FX_EXECUTION_COST_UNKNOWN" in unknown_diagnostics["reason_codes"]
    assert unknown_diagnostics["entry_fx_cost"] is None


def test_same_currency_needs_no_fake_fx_evidence() -> None:
    config = _prospective_config(currency="USD")
    context = _context(config=config)
    quote = _quote(
        symbol="TTWO270820C00100000",
        expiration=date(2027, 8, 20),
        strike=100,
        bid=5.0,
        ask=5.2,
    )
    candidate = build_candidate(
        architecture=Architecture.LONG_CALL,
        recipe=_recipe(Architecture.LONG_CALL),
        leg_specs=[(PositionSide.LONG, 1, quote)],
        quantity=1,
        request=_request(),
        horizon_compatible=True,
        budget_policy=config.budget_policy,
        mixed_expiry_lifecycle=config.mixed_expiry_lifecycle,
        phase_m_context_id=context.context_id,
        phase_m_context_hash=context.context_hash,
    )
    assert candidate.budget_diagnostics is not None
    assert candidate.budget_diagnostics.entry_fx_cost_status is (
        FXExecutionCostStatus.NOT_APPLICABLE
    )


def test_phase_m_factory_does_not_reconstruct_fx_from_legacy_request_fields() -> None:
    context = _context()
    quote = _quote(
        symbol="TTWO270820C00100000",
        expiration=date(2027, 8, 20),
        strike=100,
        bid=5.0,
        ask=5.2,
    )
    legacy_request_with_fx = load_trade_request(REQUEST_PATH)
    candidate = build_candidate(
        architecture=Architecture.LONG_CALL,
        recipe=_recipe(Architecture.LONG_CALL),
        leg_specs=[(PositionSide.LONG, 1, quote)],
        quantity=1,
        request=legacy_request_with_fx,
        horizon_compatible=True,
        budget_policy=context.prospective_config.budget_policy,
        mixed_expiry_lifecycle=context.prospective_config.mixed_expiry_lifecycle,
        phase_m_context_id=context.context_id,
        phase_m_context_hash=context.context_hash,
    )
    assert candidate.budget_diagnostics is not None
    assert candidate.budget_diagnostics.budget_status is BudgetStatus.FX_REQUIRED
    assert candidate.budget_diagnostics.fx_rate is None


def test_broker_capital_and_buffer_three_propagate_through_factory() -> None:
    context = _context(fx_rate=_fx_rate(), fx_cost=_fx_cost(amount=0), broker=_broker())
    front = _quote(
        symbol="TTWO270820C00100000",
        expiration=date(2027, 8, 20),
        strike=100,
        bid=2.0,
        ask=2.2,
    )
    back = _quote(
        symbol="TTWO280121C00100000",
        expiration=date(2028, 1, 21),
        strike=100,
        bid=10.0,
        ask=10.2,
    )
    common = {
        "architecture": Architecture.CALL_CALENDAR,
        "recipe": _recipe(Architecture.CALL_CALENDAR),
        "leg_specs": [
            (PositionSide.LONG, 1, back),
            (PositionSide.SHORT, 1, front),
        ],
        "quantity": 1,
        "request": _request(),
        "horizon_compatible": True,
        "budget_policy": context.prospective_config.budget_policy,
        "fx": context.fx_rate,
        "fx_cost": context.fx_execution_cost,
        "mixed_expiry_lifecycle": context.prospective_config.mixed_expiry_lifecycle,
        "phase_m_context_id": context.context_id,
        "phase_m_context_hash": context.context_hash,
    }
    with_broker = build_candidate(**common, broker_context=context.broker_capital_context)
    without_broker = build_candidate(**common, broker_context=None)

    assert with_broker.lifecycle_capital_requirement is not None
    assert with_broker.lifecycle_capital_requirement.managed_exit_deadline == date(2027, 8, 17)
    assert with_broker.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.BROKER_BUYING_POWER
    )
    assert with_broker.lifecycle_capital_requirement.broker_buying_power == 900
    assert with_broker.budget_diagnostics is not None
    assert with_broker.budget_diagnostics.buying_power_requirement == 900
    assert without_broker.lifecycle_capital_requirement is not None
    assert without_broker.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.UNKNOWN
    )
    assert without_broker.budget_diagnostics is not None
    assert not without_broker.budget_diagnostics.paper_eligible


def test_trade_economics_uses_context_lifecycle_for_every_deadline_consumer() -> None:
    bundle = _fast_bundle()
    candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-bull-call-spread"
    ).model_copy(deep=True)
    first_quote = candidate.legs[0].option_quote
    second_quote = candidate.legs[1].option_quote
    assert first_quote is not None and second_quote is not None
    second_quote.contract.expiration = first_quote.contract.expiration + timedelta(days=90)
    second_quote.contract.strike = first_quote.contract.strike
    analyze_risk(candidate, bundle)
    evidence_time = bundle.analysis_timestamp - timedelta(minutes=1)
    context = build_phase_m_decision_context(
        _prospective_config(buffer_days=3),
        prospective_config_source=CONFIG_PATH.as_posix(),
        fx_rate=_fx_rate(timestamp=evidence_time),
        fx_execution_cost=FXExecutionCost(
            mode=FXAccountMode.CONVERT_AT_ENTRY_AND_EXIT,
            status=FXExecutionCostStatus.KNOWN,
            cost_amount=0,
            currency="EUR",
            source="test-fx-cost",
            timestamp=evidence_time,
        ),
        broker_capital_context=BrokerCapitalContext(
            buying_power_requirement=900,
            currency="EUR",
            source="test-broker-capital",
            timestamp=evidence_time,
            validated=True,
        ),
        created_at=bundle.analysis_timestamp,
    )

    original_bundle = bundle.model_dump(mode="json")
    ticket = build_trade_economics_ticket(candidate, bundle, phase_m_context=context)
    deadline = first_quote.contract.expiration - timedelta(days=3)

    assert ticket.phase_m_context_id == context.context_id
    assert ticket.phase_m_context_hash == context.context_hash
    assert ticket.managed_exit_deadline == deadline
    assert ticket.mixed_expiry_close_buffer_calendar_days == 3
    assert ticket.lifecycle_config_source == "test-phase-m-lifecycle"
    assert ticket.lifecycle_capital_requirement is not None
    assert ticket.lifecycle_capital_requirement.managed_exit_deadline == deadline
    assert ticket.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.BROKER_BUYING_POWER
    )
    assert ticket.breakeven_clock is not None
    assert all(result.valuation_time <= deadline for result in ticket.breakeven_clock.results)
    assert all(
        cell.valuation_time <= deadline
        for matrix in ticket.scenario_matrices
        for cell in matrix.cells
    )
    assert all(
        target.managed_exit_deadline == deadline
        and (
            target.latest_profitable_arrival_date is None
            or target.latest_profitable_arrival_date <= deadline
        )
        for target in ticket.target_arrivals
    )
    assert any(
        cell.requested_horizon_days == 400
        and cell.exit_path is ExitPath.MIXED_EXPIRY_MANAGED_CLOSE
        for matrix in ticket.scenario_matrices
        for cell in matrix.cells
    )
    assert bundle.model_dump(mode="json") == original_bundle


def test_context_rejects_future_and_currency_mismatched_runtime_evidence() -> None:
    with pytest.raises(ValidationError, match="PHASE_M_FX_POLICY_CURRENCY_MISMATCH"):
        build_phase_m_decision_context(
            _prospective_config(),
            prospective_config_source=CONFIG_PATH.as_posix(),
            fx_rate=FXRate(
                source_currency="USD",
                policy_currency="GBP",
                rate_to_policy_currency=1,
                timestamp=EVIDENCE_TIME,
                source="wrong-policy-currency",
            ),
            created_at=CONTEXT_TIME,
        )

    context = _context(
        fx_rate=_fx_rate(timestamp=EVIDENCE_TIME + timedelta(hours=2)),
        created_at=CONTEXT_TIME,
    )
    with pytest.raises(ValueError, match="PHASE_M_FX_CONTEXT_AFTER_CUTOFF"):
        context.validate_for_candidate(
            candidate_currency="USD",
            cutoff=EVIDENCE_TIME + timedelta(hours=1),
        )
