from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from take_two_options.validation.comparable_panel import implied_volatility_and_delta


def test_call_iv_inversion_recovers_plausible_delta() -> None:
    result = implied_volatility_and_delta(
        spot=100,
        strike=100,
        maturity_days=30,
        rate=0.04,
        price=4.75,
    )
    assert result is not None
    implied_volatility, delta = result
    assert implied_volatility == pytest.approx(0.40, abs=0.06)
    assert 0.50 < delta < 0.60


def test_call_iv_inversion_rejects_price_below_no_arbitrage_bound() -> None:
    assert (
        implied_volatility_and_delta(
            spot=100,
            strike=50,
            maturity_days=30,
            rate=0.04,
            price=1,
        )
        is None
    )


def test_timezone_fixture_is_explicit() -> None:
    assert datetime.combine(date(2026, 8, 8), datetime.min.time(), UTC).tzinfo is UTC
