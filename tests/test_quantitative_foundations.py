from __future__ import annotations

import math
from datetime import date, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from take_two_options.american import american_scenario_value, european_scenario_value
from take_two_options.domain import OptionType
from take_two_options.pricing import black_scholes_price_greeks
from take_two_options.quantitative.contracts import (
    DataStatus,
    Measure,
    MeasureTaggedSeries,
    MeasureTransition,
    ObservedValue,
    QuantConventionSet,
    require_measure,
)
from take_two_options.quantitative.numerical_validation import (
    FiniteDifferencePoint,
    NumericalStatus,
    assess_fd_convergence,
    compare_values,
)


def test_conventions_separate_calendar_days_and_trading_sessions() -> None:
    conventions = QuantConventionSet()
    assert conventions.calendar_year_fraction(date(2025, 1, 1), date(2026, 1, 1)) == 1.0
    assert conventions.calendar_year_fraction(
        datetime(2025, 1, 1), datetime(2025, 7, 2, 12)
    ) == pytest.approx(0.5)
    assert conventions.trading_year_fraction(126) == 0.5
    assert conventions.annualize_volatility(conventions.deannualize_volatility(0.32)) == 0.32


def test_observed_value_and_measure_boundaries_are_fail_closed() -> None:
    with pytest.raises(ValidationError, match="missing observations"):
        ObservedValue(
            value=1.0,
            status=DataStatus.MISSING,
            source_id="test",
            unit="usd",
        )
    with pytest.raises(ValidationError, match="forecast distributions require"):
        MeasureTaggedSeries(
            values=(0.01,),
            measure=Measure.RISK_NEUTRAL,
            purpose="forecast",
            frequency="daily",
            source_id="test",
        )
    with pytest.raises(ValueError, match="requires measure Q"):
        require_measure(Measure.REAL_WORLD, Measure.RISK_NEUTRAL, context="option pricer")
    transition = MeasureTransition(
        from_measure=Measure.REAL_WORLD,
        to_measure=Measure.RISK_NEUTRAL,
        method="specified market price of risk",
        source_ids=("FORM-MEASURE-CHANGE-001",),
        assumptions=("equivalent measures",),
    )
    assert transition.to_measure is Measure.RISK_NEUTRAL
    with pytest.raises(ValueError, match="Black-Scholes pricing requires measure Q"):
        black_scholes_price_greeks(
            spot=100,
            strike=100,
            time_years=1,
            rate=0.03,
            volatility=0.25,
            option_type=OptionType.CALL,
            measure=Measure.REAL_WORLD,
        )


@given(
    spot=st.floats(min_value=20, max_value=300, allow_nan=False, allow_infinity=False),
    strike=st.floats(min_value=20, max_value=300, allow_nan=False, allow_infinity=False),
    volatility=st.floats(min_value=0.08, max_value=1.2, allow_nan=False, allow_infinity=False),
    days=st.integers(min_value=7, max_value=730),
    rate=st.floats(min_value=-0.01, max_value=0.15, allow_nan=False, allow_infinity=False),
)
def test_black_scholes_matches_quantlib_european(
    spot: float, strike: float, volatility: float, days: int, rate: float
) -> None:
    valuation = date(2026, 1, 5)
    expiry = valuation + timedelta(days=days)
    analytic = black_scholes_price_greeks(
        spot=spot,
        strike=strike,
        time_years=days / 365.0,
        rate=rate,
        volatility=volatility,
        option_type=OptionType.CALL,
    ).price
    finite_difference = european_scenario_value(
        spot=spot,
        strike=strike,
        valuation_date=valuation,
        expiration_date=expiry,
        option_type=OptionType.CALL,
        volatility=volatility,
        rate=rate,
        time_grid=220,
        price_grid=220,
    )
    comparison = compare_values(
        reference_name="black_scholes_analytic",
        candidate_name="quantlib_fd_european",
        reference_value=analytic,
        candidate_value=finite_difference,
        absolute_tolerance=0.035,
        relative_tolerance=0.002,
    )
    assert comparison.status is NumericalStatus.PASSED


def test_put_call_parity_and_finite_difference_convergence_report() -> None:
    call = black_scholes_price_greeks(
        spot=100,
        strike=105,
        time_years=0.75,
        rate=0.03,
        volatility=0.27,
        option_type=OptionType.CALL,
        dividend_yield=0.01,
    ).price
    put = black_scholes_price_greeks(
        spot=100,
        strike=105,
        time_years=0.75,
        rate=0.03,
        volatility=0.27,
        option_type=OptionType.PUT,
        dividend_yield=0.01,
    ).price
    parity = 100 * math.exp(-0.01 * 0.75) - 105 * math.exp(-0.03 * 0.75)
    assert call - put == pytest.approx(parity, abs=1e-10)

    report = assess_fd_convergence(
        (
            FiniteDifferencePoint(time_steps=50, price_steps=50, value=9.40),
            FiniteDifferencePoint(time_steps=100, price_steps=100, value=9.32),
            FiniteDifferencePoint(time_steps=200, price_steps=200, value=9.30),
        ),
        tolerance=0.025,
    )
    assert report.status is NumericalStatus.PASSED


def test_american_finite_difference_grid_converges() -> None:
    values = tuple(
        american_scenario_value(
            spot=100,
            strike=105,
            valuation_date=date(2026, 1, 5),
            expiration_date=date(2026, 10, 5),
            option_type=OptionType.PUT,
            volatility=0.30,
            rate=0.035,
            dividend_yield=0.01,
            time_grid=grid,
            price_grid=grid,
        )
        for grid in (50, 100, 200)
    )
    report = assess_fd_convergence(
        tuple(
            FiniteDifferencePoint(time_steps=grid, price_steps=grid, value=value)
            for grid, value in zip((50, 100, 200), values, strict=True)
        ),
        tolerance=0.02,
    )
    assert report.status is NumericalStatus.PASSED
