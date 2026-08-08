from __future__ import annotations

from datetime import date

import pytest

from take_two_options.american import european_scenario_value
from take_two_options.domain import OptionType
from take_two_options.pricing import black_scholes_price_greeks
from take_two_options.quantitative.implied_volatility import (
    ImpliedVolStatus,
    solve_implied_volatility,
)
from take_two_options.quantitative.svi import (
    SVIFitStatus,
    SVIObservation,
    SVIParameters,
    calendar_arbitrage_report,
    evaluate_essvi_gate,
    fit_svi_slice,
    raw_svi_total_variance,
    svi_arbitrage_report,
)


def test_diagnosed_iv_solver_recovers_black_scholes_volatility() -> None:
    target = black_scholes_price_greeks(
        spot=100,
        strike=110,
        time_years=0.75,
        rate=0.03,
        volatility=0.32,
        option_type=OptionType.CALL,
        dividend_yield=0.01,
    ).price

    result = solve_implied_volatility(
        lambda volatility: (
            black_scholes_price_greeks(
                spot=100,
                strike=110,
                time_years=0.75,
                rate=0.03,
                volatility=volatility,
                option_type=OptionType.CALL,
                dividend_yield=0.01,
            ).price
        ),
        target_price=target,
    )

    assert result.status is ImpliedVolStatus.CONVERGED
    assert result.volatility == pytest.approx(0.32, abs=1e-6)
    assert result.residual == pytest.approx(0.0, abs=1e-6)
    assert result.iterations > 0


def test_iv_solver_reports_bracket_failures_instead_of_returning_a_number() -> None:
    below = solve_implied_volatility(lambda volatility: 1.0 + volatility, target_price=0.5)
    above = solve_implied_volatility(lambda volatility: 1.0 + volatility, target_price=10.0)
    non_monotone = solve_implied_volatility(lambda volatility: -volatility, target_price=0.0)
    flat = solve_implied_volatility(lambda volatility: 1.0, target_price=1.0)

    assert below.status is ImpliedVolStatus.BELOW_BRACKET
    assert below.volatility is None
    assert above.status is ImpliedVolStatus.ABOVE_BRACKET
    assert above.volatility is None
    assert non_monotone.status is ImpliedVolStatus.NO_BRACKET
    assert flat.status is ImpliedVolStatus.NO_BRACKET
    assert "insensitive" in flat.warnings[0]


def test_diagnosed_iv_solver_handles_quantlib_european_short_maturity() -> None:
    valuation = date(2026, 1, 5)
    expiration = date(2026, 1, 19)
    price = european_scenario_value(
        spot=100,
        strike=125,
        valuation_date=valuation,
        expiration_date=expiration,
        option_type=OptionType.CALL,
        volatility=0.55,
        rate=0.03,
        time_grid=180,
        price_grid=180,
    )
    result = solve_implied_volatility(
        lambda volatility: european_scenario_value(
            spot=100,
            strike=125,
            valuation_date=valuation,
            expiration_date=expiration,
            option_type=OptionType.CALL,
            volatility=volatility,
            rate=0.03,
            time_grid=180,
            price_grid=180,
        ),
        target_price=price,
        price_tolerance=1e-7,
    )
    assert result.status is ImpliedVolStatus.CONVERGED
    assert result.volatility == pytest.approx(0.55, abs=2e-4)


def test_svi_synthetic_slice_is_reconstructed_and_arbitrage_checked() -> None:
    parameters = SVIParameters(a=0.04, b=0.08, rho=-0.30, m=0.0, sigma=0.20)
    observations = [
        SVIObservation(
            log_forward_moneyness=k,
            total_variance=raw_svi_total_variance(k, parameters),
        )
        for k in (-0.60, -0.45, -0.30, -0.15, 0.0, 0.15, 0.30, 0.45, 0.60)
    ]

    report = fit_svi_slice(observations)

    assert report.status is SVIFitStatus.FITTED
    assert report.parameters is not None
    assert report.weighted_rmse == pytest.approx(0.0, abs=1e-10)
    assert report.maximum_absolute_error == pytest.approx(0.0, abs=1e-10)
    assert report.arbitrage is not None and report.arbitrage.butterfly_arbitrage_free


def test_svi_detects_known_butterfly_violation_and_calendar_crossing() -> None:
    violating = SVIParameters(a=-0.0410, b=0.1331, rho=0.3060, m=0.3586, sigma=0.4153)
    assert not svi_arbitrage_report(violating).butterfly_arbitrage_free

    front = SVIParameters(a=0.05, b=0.08, rho=-0.2, m=0.0, sigma=0.2)
    back = SVIParameters(a=0.03, b=0.08, rho=-0.2, m=0.0, sigma=0.2)
    calendar = calendar_arbitrage_report([(0.25, front), (0.50, back)])
    assert not calendar.calendar_arbitrage_free
    assert calendar.violations > 0


def test_essvi_stays_behind_data_and_arbitrage_gates() -> None:
    blocked = evaluate_essvi_gate(
        expiration_count=2,
        minimum_quotes_per_expiration=3,
        point_in_time_quotes=False,
        svi_slices_arbitrage_checked=False,
    )
    eligible = evaluate_essvi_gate(
        expiration_count=4,
        minimum_quotes_per_expiration=5,
        point_in_time_quotes=True,
        svi_slices_arbitrage_checked=True,
    )
    assert not blocked.eligible
    assert len(blocked.reasons) == 4
    assert eligible.eligible
