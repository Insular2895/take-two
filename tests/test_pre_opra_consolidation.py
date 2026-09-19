from __future__ import annotations

import math
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.candidate_generation.search_space import StrategySearchSpace
from take_two_options.decision.request import load_trade_request
from take_two_options.domain import (
    ExerciseStyle,
    MarketDataBundle,
    OptionType,
    PositionSide,
    SimulationModel,
)
from take_two_options.forecasting.contracts import HistoricalReturnSeries
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import (
    Architecture,
    CandidateLeg,
    CandidateRisk,
    CompiledStrategyCandidate,
    ExitPolicy,
    MaintenancePolicy,
    ModelMetrics,
    ParameterOrigin,
    QuoteSnapshot,
)
from take_two_options.optimization.fine_search import fine_search
from take_two_options.optimization.trial_registry import TrialRegistry
from take_two_options.quantitative.contracts import (
    DEFAULT_QUANT_CONVENTIONS,
    EvidenceLevel,
    Measure,
    ModelEligibility,
    VolatilityPolicy,
)
from take_two_options.quantitative.costs import EconomicComponent, reconcile_pnl
from take_two_options.quantitative.pricing import (
    CanonicalMarketState,
    PricingInputError,
    VolatilityBatchState,
    VolatilityState,
    price_option,
    price_option_batch,
    require_contract_economics,
)
from take_two_options.simulation.conditional_monte_carlo import (
    ConditionalPathSet,
    _next_empirical_gbm_spot,
    simulate_conditional_paths,
)
from take_two_options.simulation.evaluation import evaluate_path_set
from take_two_options.simulation.legacy_models import simulate_terminal_spots
from take_two_options.simulation.model_ensemble import summarize_models
from take_two_options.simulation.path_execution import execute_path

ROOT = Path(__file__).resolve().parents[1]
START = date(2026, 8, 27)


def _quote(
    *,
    symbol: str = "TTWO261127C00100000",
    expiration: date = date(2026, 11, 27),
    option_type: OptionType = OptionType.CALL,
    exercise_style: ExerciseStyle | None = ExerciseStyle.AMERICAN,
    multiplier: int | None = 100,
    multiplier_status: EvidenceLevel = EvidenceLevel.KNOWN,
) -> QuoteSnapshot:
    return QuoteSnapshot(
        symbol=symbol,
        expiration=expiration,
        option_type=option_type,
        strike=100.0,
        exercise_style=exercise_style,
        bid=5.0,
        ask=6.0,
        bid_size=10,
        ask_size=12,
        volume=100,
        open_interest=500,
        implied_volatility=0.30,
        quote_timestamp=datetime(2026, 8, 27, 20, tzinfo=UTC),
        multiplier=multiplier,
        multiplier_status=multiplier_status,
        contract_adjustment_status=EvidenceLevel.KNOWN,
        deliverable_description="standard listed deliverable",
        price_quality="eod_bid_ask",
        source_id="unit-option-chain",
    )


def _candidate(
    *,
    symbol: str = "TTWO261127C00100000",
    maximum_loss: float | None = 603.0,
) -> CompiledStrategyCandidate:
    quote = _quote(symbol=symbol)
    maximum_loss_status = (
        EvidenceLevel.KNOWN if maximum_loss is not None else EvidenceLevel.UNKNOWN
    )
    return CompiledStrategyCandidate(
        candidate_id=f"candidate-{symbol}",
        architecture=Architecture.LONG_CALL,
        recipe_id="long-call-base",
        legs=[
            CandidateLeg(
                side=PositionSide.LONG,
                quantity=1,
                quote=quote,
                entry_price=6.0,
            )
        ],
        exit_policy=ExitPolicy(
            policy_id="unit-exit",
            profit_target=0.50,
            stop_loss=0.50,
            maximum_holding_days=1,
            origin=ParameterOrigin.EXPERIMENTAL,
        ),
        maintenance_policy=MaintenancePolicy(
            rolling_rule="none",
            capital_recovery_rule="none",
            review_frequency_days=1,
            partial_recovery_feasible=False,
        ),
        risk=CandidateRisk(
            theoretical_mid_entry=550.0,
            entry_bid_ask_cost=50.0,
            entry_debit=600.0,
            fees=0.65,
            slippage=0.05,
            total_cost=600.70,
            maximum_loss=maximum_loss,
            maximum_loss_status=maximum_loss_status,
            maximum_gain=None,
            break_even_points=[106.007],
            budget_remaining=(399.30 if maximum_loss is not None else None),
            bounded=True,
            executable_sides_used=True,
        ),
        horizon_compatible=True,
        thesis_compatible=True,
        liquidity_compatible=True,
        broker_constructible=True,
        source_ids=["unit-option-chain"],
    )


def _market_state(
    *,
    rate: float = 0.04,
    dividend_yield: float | None = 0.01,
) -> CanonicalMarketState:
    return CanonicalMarketState(
        risk_free_rate=rate,
        risk_free_rate_status=EvidenceLevel.KNOWN,
        continuous_dividend_yield=dividend_yield,
        dividend_status=(
            EvidenceLevel.KNOWN
            if dividend_yield is not None
            else EvidenceLevel.NOT_APPLICABLE
        ),
        source_ids=("unit-rate", "unit-dividends"),
    )


def _volatility() -> VolatilityState:
    return VolatilityState(
        annual_volatility=0.30,
        policy=VolatilityPolicy.FROZEN_SURFACE,
        evidence=EvidenceLevel.UNVALIDATED,
        source_id="unit-option-chain",
        assumptions=("Fixed IV is an explicit PRE-OPRA assumption",),
    )


def _metrics(
    model_id: str,
    expected_pnl: float,
    *,
    eligibility: ModelEligibility,
    measure: Measure = Measure.REAL_WORLD,
) -> ModelMetrics:
    return ModelMetrics(
        model_id=model_id,
        measure=measure,
        eligibility=eligibility,
        paths=2,
        seed=7,
        probability_profit=0.5,
        probability_gain_50=0.5,
        probability_gain_80=0.5,
        probability_gain_100=0.0,
        probability_loss_50=0.0,
        probability_loss_70=0.0,
        probability_near_total_loss=0.0,
        expected_pnl=expected_pnl,
        median_pnl=expected_pnl,
        quantiles={"p05": expected_pnl, "p95": expected_pnl},
        var_95=max(-expected_pnl, 0.0),
        cvar_95=max(-expected_pnl, 0.0),
        simulated_drawdown=max(-expected_pnl, 0.0),
        mean_exit_days=1.0,
        take_profit_frequency=0.0,
        stop_frequency=0.0,
        exit_reasons={"time_exit": 2},
    )


def _historical_series() -> HistoricalReturnSeries:
    timestamps = [
        datetime(2026, 7, 1, 20, tzinfo=UTC) + timedelta(days=index)
        for index in range(26)
    ]
    closes = [100.0]
    for index in range(1, len(timestamps)):
        closes.append(closes[-1] * math.exp(0.001 + (index % 3 - 1) * 0.002))
    return HistoricalReturnSeries(
        ticker="TTWO",
        as_of=timestamps[-1],
        timestamps=timestamps,
        closes=closes,
        source_id="unit-history",
    )


def test_empirical_gbm_uses_mean_log_return_without_second_variance_correction() -> None:
    spot = 100.0
    assert _next_empirical_gbm_spot(
        spot,
        mean_log_return=0.001,
        daily_log_return_volatility=0.0,
        gaussian_draw=9.0,
    ) == pytest.approx(spot * math.exp(0.001), rel=0, abs=1e-12)

    actual = _next_empirical_gbm_spot(
        spot,
        mean_log_return=0.001,
        daily_log_return_volatility=0.20,
        gaussian_draw=0.40,
    )
    assert actual == pytest.approx(spot * math.exp(0.001 + 0.20 * 0.40))
    assert actual != pytest.approx(
        spot * math.exp(0.001 - 0.5 * 0.20**2 + 0.20 * 0.40)
    )


def test_risk_neutral_gbm_retains_q_drift_variance_correction(
    bundle: MarketDataBundle,
) -> None:
    result = simulate_terminal_spots(bundle, SimulationModel.GBM)
    horizon = (
        bundle.monte_carlo_horizon_days
        / DEFAULT_QUANT_CONVENTIONS.calendar_day_basis
    )
    draw = random.Random(bundle.monte_carlo_seed).gauss(0.0, 1.0)
    expected = bundle.underlying.price * math.exp(
        (
            bundle.risk_free_rate
            - bundle.continuous_dividend_yield
            - 0.5 * bundle.annualized_volatility**2
        )
        * horizon
        + bundle.annualized_volatility * math.sqrt(horizon) * draw
    )
    assert result.measure is Measure.RISK_NEUTRAL
    assert result.terminal_spots[0] == pytest.approx(expected)


def test_seeded_real_world_paths_are_deterministic_and_explicitly_unvalidated() -> None:
    first = simulate_conditional_paths(
        _historical_series(),
        spot=100.0,
        horizon_days=5,
        paths=8,
        seed=123,
    )
    second = simulate_conditional_paths(
        _historical_series(),
        spot=100.0,
        horizon_days=5,
        paths=8,
        seed=123,
    )
    assert first == second
    assert all(item.measure is Measure.REAL_WORLD for item in first)
    assert {item.eligibility for item in first} == {
        ModelEligibility.UNVALIDATED,
        ModelEligibility.DIAGNOSTIC_ONLY,
    }


def test_q_paths_cannot_be_used_as_real_world_probabilities() -> None:
    request = load_trade_request(ROOT / "configs/trades/ttwo_gta6_1000eur.yaml")
    q_paths = ConditionalPathSet(
        model_id="q-pricing-paths",
        seed=1,
        paths=[[100.0, 101.0]],
        calibration_observations=100,
        assumptions=("unit",),
        measure=Measure.RISK_NEUTRAL,
        eligibility=ModelEligibility.DIAGNOSTIC_ONLY,
    )
    with pytest.raises(ValueError, match="requires measure P, received Q"):
        evaluate_path_set(
            _candidate(),
            q_paths,
            request=request,
            start_date=START,
            market_state=_market_state(),
        )


def test_canonical_pricing_uses_rate_dividend_and_american_style() -> None:
    contract = _quote()
    valuation_time = datetime(2026, 8, 27, 12, tzinfo=UTC)
    low_rate = price_option(
        contract,
        _market_state(rate=0.0, dividend_yield=0.01),
        spot=100.0,
        valuation_time=valuation_time,
        volatility_state=_volatility(),
    )
    high_rate = price_option(
        contract,
        _market_state(rate=0.08, dividend_yield=0.01),
        spot=100.0,
        valuation_time=valuation_time,
        volatility_state=_volatility(),
    )
    high_dividend = price_option(
        contract,
        _market_state(rate=0.0, dividend_yield=0.08),
        spot=100.0,
        valuation_time=valuation_time,
        volatility_state=_volatility(),
    )
    assert low_rate.model_id == "quantlib_fd_american"
    assert low_rate.measure is Measure.RISK_NEUTRAL
    assert high_rate.price_per_share != pytest.approx(low_rate.price_per_share)
    assert high_dividend.price_per_share != pytest.approx(low_rate.price_per_share)


def test_fast_pricing_is_parity_checked_inside_its_supported_domain() -> None:
    valuation_time = datetime(2026, 8, 27, 12, tzinfo=UTC)
    contract = _quote(exercise_style=ExerciseStyle.EUROPEAN)
    authoritative = price_option(
        contract,
        _market_state(rate=0.04, dividend_yield=0.0),
        spot=100.0,
        valuation_time=valuation_time,
        volatility_state=_volatility(),
    )
    fast = price_option(
        contract,
        _market_state(rate=0.04, dividend_yield=0.0),
        spot=100.0,
        valuation_time=valuation_time,
        volatility_state=_volatility(),
        pricing_mode="fast_if_supported",
    )
    assert fast.model_id == "analytic_bsm_fast_supported"
    assert fast.price_per_share == pytest.approx(
        authoritative.price_per_share,
        rel=2e-3,
        abs=2e-3,
    )
    batch = price_option_batch(
        contract,
        _market_state(rate=0.04, dividend_yield=0.0),
        spots=(90.0, 100.0, 110.0),
        valuation_time=valuation_time,
        volatility_state=VolatilityBatchState(
            annual_volatilities=(0.25, 0.30, 0.35),
            policy=VolatilityPolicy.CONFIGURED_STRESS,
            evidence=EvidenceLevel.UNVALIDATED,
            source_id="batch-parity-test",
            assumptions=("Batch parity test",),
        ),
    )
    references = [
        price_option(
            contract,
            _market_state(rate=0.04, dividend_yield=0.0),
            spot=spot,
            valuation_time=valuation_time,
            volatility_state=VolatilityState(
                annual_volatility=volatility,
                policy=VolatilityPolicy.CONFIGURED_STRESS,
                evidence=EvidenceLevel.UNVALIDATED,
                source_id="batch-parity-test",
                assumptions=("Batch parity test",),
            ),
        ).price_per_share
        for spot, volatility in zip(
            (90.0, 100.0, 110.0),
            (0.25, 0.30, 0.35),
            strict=True,
        )
    ]
    assert batch.prices_per_share == pytest.approx(references, rel=2e-3, abs=2e-3)


def test_fast_pricing_grid_matches_authoritative_supported_domains() -> None:
    valuation_time = datetime(2026, 8, 27, 12, tzinfo=UTC)
    cases = (
        (ExerciseStyle.EUROPEAN, OptionType.CALL, 80.0, 0.15, 30, -0.01, 0.00),
        (ExerciseStyle.EUROPEAN, OptionType.CALL, 100.0, 0.30, 90, 0.00, 0.03),
        (ExerciseStyle.EUROPEAN, OptionType.CALL, 125.0, 0.60, 365, 0.08, 0.01),
        (ExerciseStyle.EUROPEAN, OptionType.PUT, 80.0, 0.60, 365, 0.08, 0.03),
        (ExerciseStyle.EUROPEAN, OptionType.PUT, 100.0, 0.30, 90, 0.04, 0.00),
        (ExerciseStyle.EUROPEAN, OptionType.PUT, 125.0, 0.15, 30, -0.01, 0.01),
        (ExerciseStyle.AMERICAN, OptionType.CALL, 90.0, 0.25, 180, 0.04, 0.00),
        (ExerciseStyle.AMERICAN, OptionType.CALL, 115.0, 0.45, 540, 0.08, 0.00),
    )
    for style, option_type, spot, volatility, days, rate, dividend_yield in cases:
        contract = _quote(
            expiration=valuation_time.date() + timedelta(days=days),
            option_type=option_type,
            exercise_style=style,
        )
        volatility_state = VolatilityState(
            annual_volatility=volatility,
            policy=VolatilityPolicy.CONFIGURED_STRESS,
            evidence=EvidenceLevel.UNVALIDATED,
            source_id="fast-reference-grid",
            assumptions=("Deterministic supported-domain parity grid",),
        )
        authoritative = price_option(
            contract,
            _market_state(rate=rate, dividend_yield=dividend_yield),
            spot=spot,
            valuation_time=valuation_time,
            volatility_state=volatility_state,
        )
        fast = price_option(
            contract,
            _market_state(rate=rate, dividend_yield=dividend_yield),
            spot=spot,
            valuation_time=valuation_time,
            volatility_state=volatility_state,
            pricing_mode="fast_if_supported",
        )
        assert fast.model_id == "analytic_bsm_fast_supported"
        assert fast.price_per_share == pytest.approx(
            authoritative.price_per_share,
            rel=2e-3,
            abs=2e-3,
        )


def test_fast_pricing_falls_back_for_unsupported_american_domain() -> None:
    contract = _quote(
        option_type=OptionType.PUT,
        exercise_style=ExerciseStyle.AMERICAN,
    )
    result = price_option(
        contract,
        _market_state(rate=0.04, dividend_yield=0.02),
        spot=100.0,
        valuation_time=datetime(2026, 8, 27, 12, tzinfo=UTC),
        volatility_state=_volatility(),
        pricing_mode="fast_if_supported",
    )
    assert result.model_id == "quantlib_fd_american"


def test_path_execution_consumes_canonical_rate_and_dividend_inputs() -> None:
    candidate = _candidate()
    no_carry = execute_path(
        candidate,
        [100.0, 101.0],
        start_date=START,
        market_state=_market_state(rate=0.0, dividend_yield=0.0),
        commission_per_contract_side=0.65,
        slippage_per_contract_side=0.05,
    )
    with_carry = execute_path(
        candidate,
        [100.0, 101.0],
        start_date=START,
        market_state=_market_state(rate=0.08, dividend_yield=0.04),
        commission_per_contract_side=0.65,
        slippage_per_contract_side=0.05,
    )
    assert no_carry.pnl != pytest.approx(with_carry.pnl)


def test_unsupported_contract_metadata_fails_closed_without_fast_approximation() -> None:
    missing_style = _quote(exercise_style=None)
    with pytest.raises(PricingInputError, match="EXERCISE_STYLE_UNKNOWN"):
        price_option(
            missing_style,
            _market_state(),
            spot=100.0,
            valuation_time=datetime(2026, 8, 27, tzinfo=UTC),
            volatility_state=_volatility(),
        )

    path_source = (
        ROOT / "src/take_two_options/simulation/path_execution.py"
    ).read_text(encoding="utf-8")
    assert "def _option_value" not in path_source
    assert "price_option(" in path_source


def test_unknown_multiplier_blocks_whole_contract_economics() -> None:
    unknown = _quote(multiplier=None, multiplier_status=EvidenceLevel.UNKNOWN)
    with pytest.raises(PricingInputError, match="MULTIPLIER_UNKNOWN"):
        require_contract_economics(unknown)


def test_only_decision_eligible_p_models_control_the_ensemble() -> None:
    diagnostic = _metrics(
        "diagnostic-low",
        -10_000.0,
        eligibility=ModelEligibility.DIAGNOSTIC_ONLY,
    )
    eligible = _metrics(
        "eligible",
        125.0,
        eligibility=ModelEligibility.DECISION_ELIGIBLE,
    )
    summary = summarize_models([diagnostic, eligible])
    assert summary.decision_status is ModelEligibility.DECISION_ELIGIBLE
    assert summary.conservative_expected_pnl == 125.0
    assert {item.model_id for item in summary.model_metrics} == {
        "diagnostic-low",
        "eligible",
    }

    blocked = summarize_models([diagnostic])
    assert blocked.decision_status is ModelEligibility.BLOCKED
    assert blocked.conservative_expected_pnl is None
    assert blocked.decision_reasons == ["NO_DECISION_ELIGIBLE_REAL_WORLD_MODEL"]


def test_q_model_metrics_cannot_be_marked_decision_eligible() -> None:
    with pytest.raises(ValidationError, match="require measure P"):
        _metrics(
            "invalid-q-decision",
            1.0,
            eligibility=ModelEligibility.DECISION_ELIGIBLE,
            measure=Measure.RISK_NEUTRAL,
        )


def test_unknown_capital_keeps_return_on_risk_null() -> None:
    result = execute_path(
        _candidate(maximum_loss=None),
        [100.0, 101.0],
        start_date=START,
        market_state=_market_state(),
        commission_per_contract_side=0.65,
        slippage_per_contract_side=0.05,
    )
    assert result.return_on_risk is None


def test_costs_reconcile_exactly_once_and_unknown_costs_remain_unknown() -> None:
    def component(value: float | None, evidence: EvidenceLevel) -> EconomicComponent:
        return EconomicComponent(value=value, evidence=evidence, source="unit-cost")

    known = reconcile_pnl(
        gross_pnl=100.0,
        entry_bid_ask_cost=component(10.0, EvidenceLevel.KNOWN),
        exit_bid_ask_cost=component(8.0, EvidenceLevel.HEURISTIC),
        entry_slippage=component(2.0, EvidenceLevel.UNVALIDATED),
        exit_slippage=component(3.0, EvidenceLevel.UNVALIDATED),
        commissions=component(4.0, EvidenceLevel.ESTIMATED),
        exercise_assignment_settlement_costs=component(
            0.0,
            EvidenceLevel.NOT_APPLICABLE,
        ),
        fx_costs=component(1.0, EvidenceLevel.ESTIMATED),
    )
    assert known.net_pnl == 72.0
    assert known.status is EvidenceLevel.ESTIMATED

    unknown = reconcile_pnl(
        gross_pnl=100.0,
        entry_bid_ask_cost=component(10.0, EvidenceLevel.KNOWN),
        exit_bid_ask_cost=component(8.0, EvidenceLevel.HEURISTIC),
        entry_slippage=component(2.0, EvidenceLevel.UNVALIDATED),
        exit_slippage=component(None, EvidenceLevel.UNKNOWN),
        commissions=component(4.0, EvidenceLevel.ESTIMATED),
        exercise_assignment_settlement_costs=component(
            0.0,
            EvidenceLevel.NOT_APPLICABLE,
        ),
        fx_costs=component(1.0, EvidenceLevel.ESTIMATED),
    )
    assert unknown.net_pnl is None
    assert unknown.status is EvidenceLevel.BLOCKED


def test_nan_and_infinity_are_rejected_at_model_metric_boundary() -> None:
    with pytest.raises(ValidationError):
        _metrics(
            "nan",
            math.nan,
            eligibility=ModelEligibility.DECISION_ELIGIBLE,
        )
    with pytest.raises(ValidationError):
        _metrics(
            "infinity",
            math.inf,
            eligibility=ModelEligibility.DECISION_ELIGIBLE,
        )


def test_one_candidate_numerical_failure_does_not_abort_fine_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = load_trade_request(ROOT / "configs/trades/ttwo_gta6_1000eur.yaml")
    catalog = compile_knowledge(load_knowledge(ROOT / "research/knowledge_items"))
    recipe = next(item for item in catalog.recipes if item.architecture is Architecture.LONG_CALL)
    search_space = StrategySearchSpace(
        recipe_id=recipe.recipe_id,
        architecture=recipe.architecture,
        minimum_dte=1,
        maximum_dte=365,
        minimum_moneyness=0.5,
        maximum_moneyness=2.0,
        profit_targets=[0.5],
        stops=[0.5],
        holding_days=[1],
        rolling_rules=["none"],
        capital_recovery_rules=["none"],
    )
    failing = _candidate(symbol="FAIL")
    passing = _candidate(symbol="PASS")
    failing.recipe_id = recipe.recipe_id
    passing.recipe_id = recipe.recipe_id

    def fake_evaluation(
        candidate: CompiledStrategyCandidate,
        *_args: object,
        **_kwargs: object,
    ) -> ModelMetrics:
        if candidate.legs[0].quote.symbol == "FAIL":
            raise ArithmeticError("synthetic numerical failure")
        return _metrics(
            "eligible",
            10.0,
            eligibility=ModelEligibility.DECISION_ELIGIBLE,
        )

    monkeypatch.setattr(
        "take_two_options.optimization.fine_search.evaluate_path_set",
        fake_evaluation,
    )
    results = fine_search(
        [failing, passing],
        recipes={recipe.recipe_id: recipe},
        search_spaces={recipe.recipe_id: search_space},
        path_sets=[
            ConditionalPathSet(
                model_id="eligible",
                seed=7,
                paths=[[100.0, 101.0]],
                calibration_observations=100,
                assumptions=("unit",),
                eligibility=ModelEligibility.DECISION_ELIGIBLE,
            )
        ],
        request=request,
        market_state=_market_state(),
        registry=TrialRegistry(run_id="unit-run", seed=7, config_hash="a" * 64),
    )
    assert len(results) == 2
    statuses = {item.legs[0].quote.symbol: item.evaluation.decision_status for item in results}
    assert statuses == {
        "FAIL": ModelEligibility.BLOCKED,
        "PASS": ModelEligibility.DECISION_ELIGIBLE,
    }
