from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from take_two_options.american import price_option_quote, validate_dividend_treatment
from take_two_options.budget import (
    BudgetStatus,
    FlexibleBudgetPolicyV2,
    LifecycleCapitalStatus,
)
from take_two_options.candidates import generate_candidates
from take_two_options.data import FixtureDataProvider
from take_two_options.decision.quality_scores import FiveScoreReport
from take_two_options.domain import (
    DividendForecast,
    ExerciseStyle,
    MarketDataBundle,
    PositionSide,
)
from take_two_options.engine import analyze_bundle
from take_two_options.pricing import analyze_risk, estimate_execution
from take_two_options.quantitative.contracts import Measure
from take_two_options.quantitative.trade_economics import (
    _event_leg_effect,
    build_trade_economics_ticket,
    calculate_distribution_pnl_metrics,
    calculate_fx_attribution,
    calculate_leg_advanced_greeks,
    calculate_touch_probability,
    solve_breakeven_regions,
)
from take_two_options.reporting.trade_economics import (
    render_trade_economics_markdown,
)
from take_two_options.trade_economics_models import (
    AnalysisMode,
    BreakevenSolverConfiguration,
    DistributionAvailabilityStatus,
    DividendTreatmentMode,
    EconomicPathState,
    EventScenarioStatus,
    ExitPath,
    FiveScoreScope,
    FXHandlingMode,
    GreekConfidenceLevel,
    IntradayPrecisionStatus,
    MarginEstimate,
    MarginStatus,
    ProbabilityPnLValuationRule,
    ProbabilityStatus,
    RateScenarioType,
    RiskFreeCurve,
    RiskFreeCurveNode,
    TouchDirection,
    TradeEconomicsTicket,
    VolatilityScenario,
    VolatilityScenarioParameters,
    VolatilityScenarioType,
)

ROOT = Path(__file__).resolve().parents[1]


def _fast_bundle() -> MarketDataBundle:
    bundle = FixtureDataProvider(ROOT / "fixtures/ttwo_v1_fixture.json").load_bundle()
    config = bundle.trade_economics
    config.time_decay_horizons_days = [1, 7, 30, 60, 90]
    config.scenario_horizons_days = [7, 30]
    config.spot_grid.values = [0.85, 1.0, 1.15]
    config.volatility_scenarios = config.volatility_scenarios[:3]
    config.greek_bumps.grid_levels = [50, 75]
    config.breakeven_solver.grid_points = 101
    config.exit_cost_model.exercise_cost = 0.0
    config.exit_cost_model.assignment_cost = 0.0
    config.exit_cost_model.settlement_cost = 0.0
    return bundle


@pytest.fixture(scope="module")
def m0_tickets() -> tuple[TradeEconomicsTicket, TradeEconomicsTicket]:
    bundle = _fast_bundle()
    candidates = generate_candidates(bundle)
    long_call = next(item for item in candidates if item.id == "ttwo-long-call")
    bull_spread = next(item for item in candidates if item.id == "ttwo-bull-call-spread")
    analyze_risk(long_call, bundle)
    analyze_risk(bull_spread, bundle)
    return (
        build_trade_economics_ticket(
            long_call,
            bundle,
            fixture_status="SYNTHETIC_TEST_FIXTURE",
        ),
        build_trade_economics_ticket(
            bull_spread,
            bundle,
            fixture_status="SYNTHETIC_TEST_FIXTURE",
        ),
    )


def test_flat_spot_carry_is_full_repricing_and_spread_greeks_aggregate(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    long_ticket, spread_ticket = m0_tickets
    assert long_ticket.time_decay is not None
    assert spread_ticket.time_decay is not None
    assert long_ticket.aggregate_greeks is not None
    assert spread_ticket.aggregate_greeks is not None
    assert long_ticket.time_decay.flat_spot_30d < 0
    naive_30d = long_ticket.time_decay.current_net_theta * 30
    assert long_ticket.time_decay.flat_spot_30d != pytest.approx(naive_30d, rel=1e-3)
    leg_delta = sum(
        (-1 if leg.side == "short" else 1) * leg.quantity * leg.multiplier * leg.greeks.delta.value
        for leg in spread_ticket.legs
        if leg.greeks is not None
    )
    assert spread_ticket.aggregate_greeks.delta.value == pytest.approx(leg_delta)
    horizons = [point.horizon_days for point in long_ticket.time_decay.time_decay_curve]
    assert horizons[0] == 0
    assert max(horizons) <= math.ceil(long_ticket.dte_exact_days)


def test_advanced_greeks_match_european_benchmarks_and_publish_conventions() -> None:
    bundle = _fast_bundle()
    candidate = next(item for item in generate_candidates(bundle) if item.id == "ttwo-long-call")
    quote = candidate.legs[0].option_quote
    assert quote is not None
    quote.contract.exercise_style = ExerciseStyle.EUROPEAN
    advanced = calculate_leg_advanced_greeks(quote, bundle, side=PositionSide.LONG)
    time_years = (quote.contract.expiration - bundle.analysis_timestamp).total_seconds() / (
        365 * 24 * 60 * 60
    )
    spot = bundle.underlying.price
    strike = quote.contract.strike
    sigma = quote.implied_volatility
    assert sigma is not None
    root_time = math.sqrt(time_years)
    d1 = (math.log(spot / strike) + (bundle.risk_free_rate + 0.5 * sigma * sigma) * time_years) / (
        sigma * root_time
    )
    d2 = d1 - sigma * root_time
    density = math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    vega_raw = spot * density * root_time
    expected_vanna = (-density * d2 / sigma) * 0.01
    expected_vomma = (vega_raw * d1 * d2 / sigma) * 0.0001
    assert advanced.vanna.value == pytest.approx(expected_vanna, abs=3e-5)
    assert advanced.vomma.value == pytest.approx(expected_vomma, abs=4e-5)
    assert advanced.charm_delta_drift_1_calendar_day.unit == ("delta_drift_per_calendar_day")
    assert advanced.veta_vega_drift_1_calendar_day.unit == "vega_drift_per_calendar_day"
    assert advanced.speed is not None
    assert advanced.color_gamma_drift_1_calendar_day is not None
    confidence = {item.greek: item.confidence_level for item in advanced.confidence}
    assert confidence["speed"] in {
        GreekConfidenceLevel.LOW,
        GreekConfidenceLevel.UNRELIABLE,
    }
    assert confidence["color"] in {
        GreekConfidenceLevel.LOW,
        GreekConfidenceLevel.UNRELIABLE,
    }


def test_lambda_is_sane_for_single_leg_and_suppressed_for_spread(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    long_ticket, spread_ticket = m0_tickets
    assert long_ticket.leverage.lambda_value_elasticity is not None
    assert long_ticket.leverage.lambda_value_elasticity > 0
    assert spread_ticket.leverage.lambda_value_elasticity is None
    assert any("multi-leg" in warning for warning in spread_ticket.leverage.warnings)


def test_dividend_modes_are_explicit_and_duplicate_economics_are_rejected() -> None:
    bundle = _fast_bundle()
    bundle.dividend_treatment_mode = DividendTreatmentMode.CONTINUOUS_YIELD
    bundle.continuous_dividend_yield = 0.01
    validate_dividend_treatment(bundle)
    bundle.dividend_treatment_mode = DividendTreatmentMode.DISCRETE_CASH
    bundle.continuous_dividend_yield = 0.0
    bundle.dividends = [
        DividendForecast(
            ex_date=(bundle.analysis_timestamp + timedelta(days=20)).date(),
            amount=1.0,
            currency="USD",
            freshness=bundle.underlying.freshness,
            source=bundle.underlying.sources[0],
        )
    ]
    validate_dividend_treatment(bundle)
    bundle.continuous_dividend_yield = 0.01
    with pytest.raises(ValueError, match="BLOCKED_DIVIDEND_TREATMENT_AMBIGUOUS"):
        validate_dividend_treatment(bundle)


def test_breakeven_solver_supports_call_vertical_and_non_monotonic_butterfly() -> None:
    config = BreakevenSolverConfiguration(grid_points=801)
    call_roots, call_profit = solve_breakeven_regions(
        lambda spot: max(spot - 100, 0) - 10,
        minimum_spot=0,
        maximum_spot=200,
        config=config,
    )
    vertical_roots, vertical_profit = solve_breakeven_regions(
        lambda spot: max(spot - 100, 0) - max(spot - 120, 0) - 8,
        minimum_spot=0,
        maximum_spot=200,
        config=config,
    )
    butterfly_roots, butterfly_profit = solve_breakeven_regions(
        lambda spot: max(spot - 90, 0) - 2 * max(spot - 100, 0) + max(spot - 110, 0) - 4,
        minimum_spot=0,
        maximum_spot=200,
        config=config,
    )
    assert call_roots == pytest.approx([110], abs=1e-4)
    assert call_profit[0].lower == pytest.approx(110, abs=1e-4)
    assert vertical_roots == pytest.approx([108], abs=1e-4)
    assert vertical_profit[0].lower == pytest.approx(108, abs=1e-4)
    assert butterfly_roots == pytest.approx([94, 106], abs=1e-4)
    assert len(butterfly_profit) == 1
    assert butterfly_profit[0].upper == pytest.approx(106, abs=1e-4)


@settings(max_examples=25, deadline=None)
@given(
    strike=st.floats(min_value=10, max_value=300, allow_nan=False, allow_infinity=False),
    premium=st.floats(min_value=0.5, max_value=40, allow_nan=False, allow_infinity=False),
)
def test_property_breakeven_roots_reconcile(strike: float, premium: float) -> None:
    config = BreakevenSolverConfiguration(grid_points=201)

    def evaluator(spot: float) -> float:
        return max(spot - strike, 0) - premium

    roots, intervals = solve_breakeven_regions(
        evaluator,
        minimum_spot=0,
        maximum_spot=strike + premium + 50,
        config=config,
    )
    assert len(roots) == 1
    assert abs(evaluator(roots[0])) <= config.pnl_tolerance + config.root_tolerance
    assert intervals[0].lower == pytest.approx(roots[0], abs=1e-4)


def test_costs_reconcile_and_unknown_margin_never_uses_false_zero(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    ticket, _ = m0_tickets
    round_trip = ticket.round_trip_cost
    known = (
        round_trip.entry_bid_ask_cost
        + round_trip.entry_slippage
        + round_trip.entry_commissions
        + (round_trip.entry_fx_cost or 0)
        + round_trip.exit.total_exit_cost
    )
    assert round_trip.total_round_trip_cost == pytest.approx(known)
    unknown = MarginEstimate(
        margin_requirement=None,
        buying_power_usage=None,
        status=MarginStatus.UNKNOWN,
        source="pending_broker_what_if",
    )
    assert unknown.margin_requirement is None
    with pytest.raises(ValidationError, match="unknown or blocked margin must remain null"):
        MarginEstimate(
            margin_requirement=0,
            buying_power_usage=0,
            status=MarginStatus.UNKNOWN,
            source="invalid_false_zero",
        )


def test_fx_attribution_is_zero_at_constant_fx_and_reconciles_when_fx_moves() -> None:
    constant = calculate_fx_attribution(
        option_pnl_usd=120,
        mode=FXHandlingMode.CONVERT_AT_ENTRY_AND_EXIT,
        entry_fx_rate_usd_per_base=1.2,
        scenario_fx_rate_usd_per_base=1.2,
    )
    changed = calculate_fx_attribution(
        option_pnl_usd=120,
        mode=FXHandlingMode.CONVERT_AT_ENTRY_AND_EXIT,
        entry_fx_rate_usd_per_base=1.2,
        scenario_fx_rate_usd_per_base=1.0,
    )
    assert constant.fx_contribution_base == pytest.approx(0)
    assert changed.fx_contribution_base == pytest.approx(
        changed.pnl_base_at_scenario_fx - changed.pnl_base_at_constant_entry_fx
    )


def test_touch_probability_is_pathwise_and_absence_remains_null() -> None:
    paths = [[100, 112, 105], [100, 108, 115], [100, 105, 109], [100, 111, 112]]
    result = calculate_touch_probability(
        paths,
        target=110,
        direction=TouchDirection.UPPER,
        horizon_days=30,
        model="synthetic_p_paths",
        measure=Measure.REAL_WORLD,
        calibration_status=ProbabilityStatus.MODEL_IMPLIED,
        minimum_paths=1,
    )
    assert result.probability_touch == pytest.approx(0.75)
    assert result.probability_terminal_above == pytest.approx(0.5)
    assert result.probability_touch >= result.probability_terminal_above
    assert result.median_first_touch_time_conditional_on_touch == pytest.approx(15)
    unavailable = calculate_touch_probability(
        None,
        target=110,
        direction=TouchDirection.UPPER,
        horizon_days=30,
        model=None,
        measure=None,
        calibration_status=ProbabilityStatus.PROBABILITY_MODEL_NOT_AVAILABLE,
    )
    assert unavailable.probability_touch is None
    assert unavailable.reason


def test_exact_timestamp_is_preserved_but_date_fd_precision_is_disclosed() -> None:
    bundle = _fast_bundle()
    quote = bundle.option_quotes[0]
    result = price_option_quote(quote, bundle)
    assert result.valuation_time == bundle.analysis_timestamp
    assert result.exact_time_to_expiry_years == pytest.approx(
        (quote.contract.expiration - bundle.analysis_timestamp).total_seconds()
        / (365 * 24 * 60 * 60)
    )
    assert result.intraday_precision_status is IntradayPrecisionStatus.APPROXIMATED_DATE_ENGINE
    near_bundle = bundle.model_copy(deep=True)
    near_quote = near_bundle.option_quotes[0]
    near_quote.contract.expiration = near_bundle.analysis_timestamp + timedelta(hours=12)
    near = price_option_quote(near_quote, near_bundle)
    assert near.intraday_precision_status is IntradayPrecisionStatus.INSUFFICIENT_NEAR_EXPIRY


def test_shapley_attribution_reconciles_and_renderer_uses_ticket_values(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    ticket, _ = m0_tickets
    for attribution in ticket.pnl_attributions:
        full = attribution.full_repricing
        components = (
            full.spot
            + full.time
            + full.volatility
            + full.rates
            + full.fx
            + full.execution_costs
            + full.other
            + full.residual
        )
        assert components == pytest.approx(full.full_repriced_pnl, abs=1e-7)
    markdown = render_trade_economics_markdown(ticket)
    assert ticket.fixture_status in markdown
    assert f"{ticket.round_trip_cost.total_round_trip_cost:,.2f}" in markdown
    assert "Full repricing is the primary financial value" in markdown
    assert "order_capability=`forbidden`" in markdown


def test_risk_free_curve_interpolates_declared_quote_type_without_relabeling() -> None:
    bundle = _fast_bundle()
    bundle.risk_free_curve = RiskFreeCurve(
        curve_id="synthetic-par-curve",
        as_of=bundle.analysis_timestamp,
        currency="USD",
        source_instrument="US Treasury CMT",
        quote_type="par_yield",
        compounding="bond_equivalent_semiannual",
        day_count="ACT/365 interpolation axis",
        interpolation_method="linear_in_declared_par_yield",
        nodes=[
            RiskFreeCurveNode(maturity_days=30, annual_rate=0.04),
            RiskFreeCurveNode(maturity_days=90, annual_rate=0.05),
        ],
        source="SYNTHETIC_TEST_FIXTURE",
    )
    assert bundle.risk_free_curve.rate_for(60) == pytest.approx(0.045)
    assert bundle.risk_free_curve.quote_type == "par_yield"
    with pytest.raises(ValidationError, match="bootstrap method"):
        RiskFreeCurve(
            curve_id="invalid-zero-curve",
            as_of=bundle.analysis_timestamp,
            currency="USD",
            source_instrument="par yields",
            quote_type="zero_rate",
            compounding="continuous",
            day_count="ACT/365",
            interpolation_method="linear",
            nodes=[RiskFreeCurveNode(maturity_days=30, annual_rate=0.04)],
            source="SYNTHETIC_TEST_FIXTURE",
        )


def test_required_rate_curve_stresses_are_full_repriced_and_visible(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    ticket, _ = m0_tickets
    by_type = {result.scenario_type: result for result in ticket.rate_stress_results}
    assert set(by_type) == {
        RateScenarioType.BASE_CURVE,
        RateScenarioType.PARALLEL_UP,
        RateScenarioType.PARALLEL_DOWN,
        RateScenarioType.STEEPENING,
        RateScenarioType.FLATTENING,
    }
    assert by_type[RateScenarioType.PARALLEL_UP].estimated_position_value != pytest.approx(
        by_type[RateScenarioType.PARALLEL_DOWN].estimated_position_value
    )
    assert all(result.status == "CONFIGURED_STRESS" for result in by_type.values())
    parallel_attribution = next(
        item for item in ticket.pnl_attributions if "parallel_up" in item.scenario_name
    )
    assert parallel_attribution.full_repricing.rates != pytest.approx(0)


def test_committed_golden_json_and_markdown_represent_the_same_ticket() -> None:
    ticket = TradeEconomicsTicket.model_validate_json(
        (ROOT / "reports/examples/m0_trade_economics_ticket.json").read_text(encoding="utf-8")
    )
    markdown = (ROOT / "reports/examples/m0_trade_economics_ticket.md").read_text(encoding="utf-8")
    assert ticket.fixture_status == "SYNTHETIC_TEST_FIXTURE"
    assert markdown == render_trade_economics_markdown(ticket)


@pytest.mark.parametrize("schema_version", ["1.0", "1.1"])
def test_trade_economics_ticket_remains_backward_readable(schema_version: str) -> None:
    payload = json.loads(
        (ROOT / "reports/examples/m0_trade_economics_ticket.json").read_text(
            encoding="utf-8"
        )
    )
    payload["schema_version"] = schema_version
    payload.pop("budget_diagnostics", None)
    payload.pop("lifecycle_capital_requirement", None)

    ticket = TradeEconomicsTicket.model_validate(payload)

    assert ticket.schema_version == schema_version
    assert ticket.budget_diagnostics is None


def test_engine_deep_mode_attaches_tickets_only_to_configured_top_candidates() -> None:
    bundle = _fast_bundle()
    bundle.trade_economics.analysis_mode = AnalysisMode.DEEP_ANALYSIS
    bundle.trade_economics.deep_analysis_candidate_limit = 2
    bundle.trade_economics.time_decay_horizons_days = [1, 7]
    bundle.trade_economics.scenario_horizons_days = [7]
    bundle.trade_economics.spot_grid.values = [0.85, 1.15]
    bundle.trade_economics.breakeven_solver.grid_points = 51
    report = analyze_bundle(bundle)
    tickets = [
        candidate.trade_economics
        for candidate in report.candidates
        if candidate.trade_economics is not None
    ]
    assert len(tickets) == 2
    assert all(ticket.order_capability == "forbidden" for ticket in tickets)


def test_m0_1_long_and_short_premiums_use_midpoint_and_executable_sides_once() -> None:
    bundle = _fast_bundle()
    long_candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-long-call"
    )
    long_execution = estimate_execution(long_candidate, bundle)
    assert long_execution.theoretical_mid_premium_paid == pytest.approx(2_900)
    assert long_execution.executable_premium_paid == pytest.approx(3_000)
    assert long_execution.bid_ask_cost == pytest.approx(100)
    assert long_execution.total_entry_cash_flow == pytest.approx(3_002.15)
    assert long_execution.total_entry_cash_flow == pytest.approx(
        long_execution.executable_net_premium + long_execution.slippage + long_execution.fees
    )

    short_candidate = long_candidate.model_copy(deep=True)
    short_candidate.legs[0].side = PositionSide.SHORT
    quote = short_candidate.legs[0].option_quote
    assert quote is not None
    quote.bid = 8
    quote.ask = 10
    short_execution = estimate_execution(short_candidate, bundle)
    assert short_execution.theoretical_mid_premium_received == pytest.approx(900)
    assert short_execution.executable_premium_received == pytest.approx(800)
    assert short_execution.bid_ask_cost == pytest.approx(100)
    assert short_execution.executable_net_premium == pytest.approx(-800)
    assert short_execution.total_entry_cash_flow == pytest.approx(-797.85)


def test_expiration_uses_hold_path_without_fictional_close_cost_and_reconciles(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    for ticket in m0_tickets:
        assert ticket.breakeven_clock is not None
        base_results = [
            result
            for result in ticket.breakeven_clock.results
            if result.volatility_scenario == "base_constant_leg_iv"
        ]
        expiry_result = max(base_results, key=lambda result: result.valuation_time)
        assert expiry_result.exit_path is ExitPath.HOLD_TO_EXPIRY
        assert expiry_result.breakeven_type == "EXPIRATION_BREAKEVEN"
        assert expiry_result.applied_exit_cost == pytest.approx(0)
        assert expiry_result.break_even_roots == pytest.approx(
            ticket.expiration_breakevens,
            abs=2e-4,
        )
        close_cell = next(
            cell for cell in ticket.scenario_matrices[0].cells if cell.requested_horizon_days == 7
        )
        expiry_cell = max(
            ticket.scenario_matrices[0].cells,
            key=lambda cell: cell.valuation_time,
        )
        assert close_cell.exit_path is ExitPath.CLOSE_BEFORE_EXPIRY
        assert any(
            result.breakeven_type == "CLOSE_BEFORE_EXPIRY_BREAKEVEN" for result in base_results
        )
        assert close_cell.exit_cost_applied == pytest.approx(
            ticket.exit_cost_estimate.total_exit_cost
        )
        assert expiry_cell.exit_path is ExitPath.HOLD_TO_EXPIRY
        assert expiry_cell.exit_cost_applied == pytest.approx(0)
        assert ticket.exit_cost_estimate.total_exit_cost == pytest.approx(
            ticket.exit_cost_estimate.estimated_exit_bid_ask_cost
            + ticket.exit_cost_estimate.estimated_exit_slippage
            + ticket.exit_cost_estimate.closing_commissions
            + (ticket.exit_cost_estimate.fx_exit_cost or 0)
        )
        assert ticket.exit_cost_estimate.exercise_cost_if_relevant in {None, 0}
        assert ticket.exit_cost_estimate.settlement_cost_if_relevant == 0


def test_bear_put_expiration_breakeven_reconciles_with_contractual_payoff() -> None:
    bundle = _fast_bundle()
    candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-bear-put-spread"
    )
    analyze_risk(candidate, bundle)
    ticket = build_trade_economics_ticket(candidate, bundle)
    assert ticket.breakeven_clock is not None
    expiry = max(
        (
            result
            for result in ticket.breakeven_clock.results
            if result.volatility_scenario == "base_constant_leg_iv"
        ),
        key=lambda result: result.valuation_time,
    )
    assert expiry.break_even_roots == pytest.approx(ticket.expiration_breakevens, abs=2e-4)


def test_ticket_1_2_contains_budget_diagnostics_and_renderer_section(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    ticket, _ = m0_tickets
    assert ticket.schema_version == "1.2"
    assert ticket.budget_diagnostics is not None
    markdown = render_trade_economics_markdown(ticket)
    assert "## Budget" in markdown
    assert "This trade — Budget" in markdown
    assert ticket.budget_diagnostics.budget_status.value in markdown


def test_renderer_exposes_full_theta_statistics_and_score_sections(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    markdown = render_trade_economics_markdown(m0_tickets[0])
    for expected in (
        "Theta / capital / day",
        "Flat Spot 7d %",
        "Flat Spot 30d %",
        "Flat Spot 60d %",
        "Flat Spot 90d %",
        "Decay rate 0-7d",
        "Decay acceleration 30-60",
        "Statistics",
        "Decision scores",
        "Current theta is NOT multiplied by horizon",
    ):
        assert expected in markdown


def test_distribution_pnl_is_null_without_sufficient_promoted_paths(
    m0_tickets: tuple[TradeEconomicsTicket, TradeEconomicsTicket],
) -> None:
    distribution = m0_tickets[0].distribution_pnl
    assert distribution is not None
    assert distribution.availability_status is DistributionAvailabilityStatus.UNAVAILABLE
    assert distribution.expected_pnl is None
    assert distribution.median_pnl is None
    assert distribution.probability_profit is None
    assert distribution.cvar_95 is None
    assert distribution.missing_reason


def test_full_economic_paths_produce_exact_net_pnl_distribution() -> None:
    bundle = _fast_bundle()
    candidate = next(item for item in generate_candidates(bundle) if item.id == "ttwo-long-call")
    analyze_risk(candidate, bundle)
    ticket = build_trade_economics_ticket(candidate, bundle)
    quote = candidate.legs[0].option_quote
    assert quote is not None and quote.implied_volatility is not None
    paths = [
        [
            EconomicPathState(
                spot=spot,
                valuation_time=quote.contract.expiration,
                volatility_by_contract={quote.contract.local_symbol: quote.implied_volatility},
            )
        ]
        for spot in (250.0, 280.0, 320.0, 400.0)
    ]
    metrics = calculate_distribution_pnl_metrics(
        candidate,
        bundle,
        close_exit_cost=ticket.exit_cost_estimate,
        economic_paths=paths,
        model="synthetic_full_economic_paths",
        measure=Measure.REAL_WORLD,
        calibration_status=ProbabilityStatus.MODEL_IMPLIED,
    )
    expected_path_pnls = [-3002.15, -1002.15, 2997.85, 10997.85]
    assert metrics.expected_pnl == pytest.approx(sum(expected_path_pnls) / 4)
    assert metrics.median_pnl == pytest.approx(997.85)
    assert metrics.probability_profit == pytest.approx(0.5)
    assert metrics.probability_loss_25 == pytest.approx(0.5)
    assert metrics.probability_loss_90 == pytest.approx(0.25)
    assert metrics.var_95 == pytest.approx(2702.15)
    assert metrics.cvar_95 == pytest.approx(3002.15)
    assert metrics.effective_sample_size == pytest.approx(4)


def test_spot_paths_require_an_explicit_future_iv_valuation_rule() -> None:
    bundle = _fast_bundle()
    candidate = next(item for item in generate_candidates(bundle) if item.id == "ttwo-long-call")
    analyze_risk(candidate, bundle)
    ticket = build_trade_economics_ticket(candidate, bundle)
    unavailable = calculate_distribution_pnl_metrics(
        candidate,
        bundle,
        close_exit_cost=ticket.exit_cost_estimate,
        spot_paths=[[257.79, 300.0]],
        spot_path_horizon_days=30,
        model="synthetic_spot_paths",
        measure=Measure.REAL_WORLD,
        calibration_status=ProbabilityStatus.MODEL_IMPLIED,
    )
    assert unavailable.expected_pnl is None
    assert unavailable.missing_reason == "INSUFFICIENT_STATE_PATHS_FOR_PNL_DISTRIBUTION"
    available = calculate_distribution_pnl_metrics(
        candidate,
        bundle,
        close_exit_cost=ticket.exit_cost_estimate,
        spot_paths=[[257.79, 300.0]],
        spot_path_horizon_days=30,
        spot_path_valuation_rule=(ProbabilityPnLValuationRule.CONSTANT_LEG_IV_PATH_VALUATION),
        model="synthetic_spot_paths",
        measure=Measure.REAL_WORLD,
        calibration_status=ProbabilityStatus.MODEL_IMPLIED,
    )
    assert available.expected_pnl is not None
    assert "MODEL_IMPLIED_UNDER_DECLARED_IV_RULE" in " ".join(available.assumptions)


def test_engine_bridges_exact_canonical_candidate_scores_into_ranked_deep_ticket() -> None:
    bundle = _fast_bundle()
    screen_bundle = bundle.model_copy(deep=True)
    screen_bundle.trade_economics.analysis_mode = AnalysisMode.SCREEN
    canonical_rank = analyze_bundle(screen_bundle).ranked_candidate_ids
    bundle.trade_economics.analysis_mode = AnalysisMode.DEEP_ANALYSIS
    bundle.trade_economics.deep_analysis_candidate_limit = 1
    report = FiveScoreReport.model_validate_json(
        (ROOT / "reports/pre_opra/five_scores_2026-08-08.json").read_text(encoding="utf-8")
    )
    canonical = {
        candidate_id: report.model_copy(
            update={
                "candidate_id": candidate_id,
                "report_id": f"synthetic-{candidate_id}",
            }
        )
        for candidate_id in canonical_rank
    }
    decision = analyze_bundle(
        bundle,
        canonical_five_score_reports=canonical,
        canonical_ranked_candidate_ids=canonical_rank,
    )
    assert decision.ranked_candidate_ids == canonical_rank
    top_id = decision.ranked_candidate_ids[0]
    top = next(candidate for candidate in decision.candidates if candidate.id == top_id)
    assert top.trade_economics is not None
    scores = top.trade_economics.five_scores
    assert scores is not None
    assert scores.scope is FiveScoreScope.CANDIDATE
    source = canonical[top_id]
    assert scores.opportunity.score_value == source.opportunity.score_value
    assert scores.risk.score_value == source.risk.score_value
    assert scores.evidence.score_value == source.evidence.score_value
    assert scores.model_agreement.score_value == source.model_agreement.score_value
    assert scores.execution_quality.score_value == source.execution_quality.score_value
    assert top.trade_economics.read_only is True
    assert top.trade_economics.transmit is False


def _event_scenario(event_date: date) -> VolatilityScenario:
    return VolatilityScenario(
        name="synthetic_event_crush",
        scenario_type=VolatilityScenarioType.EVENT_IV_CRUSH,
        unit="vol_points",
        parameters=VolatilityScenarioParameters(
            short_end_max_days=90,
            long_end_min_days=365,
            front_expiry_shift_vol_points=-20,
            mid_expiry_shift_vol_points=-10,
            back_expiry_shift_vol_points=-2,
            relative_to_event_date=event_date,
        ),
        source="synthetic_test",
    )


def test_event_iv_crush_uses_event_date_and_event_to_expiry_tenor() -> None:
    bundle = _fast_bundle()
    quote = bundle.option_quotes[0].model_copy(deep=True)
    event_date = bundle.analysis_timestamp.date() + timedelta(days=30)
    scenario = _event_scenario(event_date)
    before = _event_leg_effect(quote, scenario, bundle.analysis_timestamp)
    assert before.event_status is EventScenarioStatus.EVENT_NOT_OCCURRED_YET
    assert before.applied_vol_shift == 0

    event_time = bundle.analysis_timestamp + timedelta(days=30)
    exact = _event_leg_effect(quote, scenario, event_time)
    after = _event_leg_effect(quote, scenario, event_time + timedelta(days=1))
    assert exact.event_status is EventScenarioStatus.EVENT_CRUSH_APPLIED
    assert after.event_status is EventScenarioStatus.EVENT_CRUSH_APPLIED

    expires_before = quote.model_copy(deep=True)
    expires_before.contract.expiration = event_time - timedelta(days=1)
    expired_effect = _event_leg_effect(expires_before, scenario, event_time)
    assert expired_effect.event_status is EventScenarioStatus.OPTION_EXPIRES_BEFORE_EVENT
    assert expired_effect.applied_vol_shift == 0

    front = quote.model_copy(deep=True)
    front.contract.expiration = event_time + timedelta(days=45)
    back = quote.model_copy(deep=True)
    back.contract.expiration = event_time + timedelta(days=400)
    assert _event_leg_effect(front, scenario, event_time).applied_vol_shift == -20
    assert _event_leg_effect(back, scenario, event_time).applied_vol_shift == -2

    generic = scenario.model_copy(deep=True)
    generic.parameters.relative_to_event_date = None
    generic_effect = _event_leg_effect(quote, generic, bundle.analysis_timestamp)
    assert (
        generic_effect.event_status is EventScenarioStatus.CONFIGURED_GENERIC_EVENT_STRESS_NO_DATE
    )
    assert generic_effect.event_date is None


@pytest.mark.parametrize("calendar", [True, False])
def test_mixed_expiry_calendar_and_diagonal_stop_at_managed_deadline(
    calendar: bool,
) -> None:
    bundle = _fast_bundle()
    bundle.trade_economics.scenario_horizons_days = [7, 400]
    bundle.trade_economics.time_decay_horizons_days = [1, 7, 400]
    candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-bull-call-spread"
    ).model_copy(deep=True)
    first_quote = candidate.legs[0].option_quote
    second_quote = candidate.legs[1].option_quote
    assert first_quote is not None and second_quote is not None
    second_quote.contract.expiration = first_quote.contract.expiration + timedelta(days=90)
    if calendar:
        second_quote.contract.strike = first_quote.contract.strike
    analyze_risk(candidate, bundle)
    ticket = build_trade_economics_ticket(candidate, bundle)
    deadline = first_quote.contract.expiration - timedelta(days=1)
    assert ticket.managed_exit_deadline == deadline
    assert ticket.expiration_breakevens == []
    assert ticket.time_decay is not None
    assert max(point.valuation_time for point in ticket.time_decay.time_decay_curve) <= deadline
    clipped = [
        cell
        for matrix in ticket.scenario_matrices
        for cell in matrix.cells
        if cell.requested_horizon_days == 400
    ]
    assert clipped
    assert all(cell.valuation_time == deadline for cell in clipped)
    assert all(cell.exit_path is ExitPath.MIXED_EXPIRY_MANAGED_CLOSE for cell in clipped)
    assert all(cell.scenario_status == "CLIPPED_BY_MIXED_EXPIRY_POLICY" for cell in clipped)
    assert all(
        target.latest_profitable_arrival_date is None
        or target.latest_profitable_arrival_date <= deadline
        for target in ticket.target_arrivals
    )
    assert ticket.breakeven_clock is not None
    assert all(
        result.breakeven_type == "MANAGED_EXIT_BREAKEVEN"
        for result in ticket.breakeven_clock.results
    )
    assert "intentionally not modeled" in render_trade_economics_markdown(ticket)


@pytest.mark.parametrize("calendar", [True, False])
def test_v2_mixed_expiry_ticket_blocks_unproven_capital_without_false_max_loss(
    calendar: bool,
) -> None:
    bundle = _fast_bundle()
    candidate = next(
        item for item in generate_candidates(bundle) if item.id == "ttwo-bull-call-spread"
    ).model_copy(deep=True)
    first_quote = candidate.legs[0].option_quote
    second_quote = candidate.legs[1].option_quote
    assert first_quote is not None and second_quote is not None
    second_quote.contract.expiration = first_quote.contract.expiration + timedelta(days=90)
    if calendar:
        second_quote.contract.strike = first_quote.contract.strike
    analyze_risk(candidate, bundle)
    policy = FlexibleBudgetPolicyV2(
        currency="USD",
        target_budget=5_000,
        under_target_tolerance=5_000,
        max_overspend=0,
        maximum_contracts=4,
    )

    ticket = build_trade_economics_ticket(candidate, bundle, budget_policy=policy)

    assert ticket.maximum_loss is None
    assert ticket.budget_diagnostics is not None
    assert ticket.budget_diagnostics.budget_status is (
        BudgetStatus.BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN
    )
    assert not ticket.budget_diagnostics.paper_eligible
    assert ticket.lifecycle_capital_requirement is not None
    assert ticket.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.UNKNOWN
    )
    assert ticket.capital_at_risk is None
    assert ticket.leverage.capital_at_risk is None
    assert ticket.leverage.capital_status == LifecycleCapitalStatus.UNKNOWN.value
    assert "BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN" in ticket.blockers
