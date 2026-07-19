from datetime import timedelta

import pytest

from take_two_options.american import assess_exercise_risk, price_option_quote
from take_two_options.domain import (
    DividendForecast,
    MarketDataBundle,
    PositionSide,
    RiskLevel,
)


def test_american_put_is_not_below_european(bundle: MarketDataBundle) -> None:
    quote = next(item for item in bundle.option_quotes if item.contract.option_type.value == "put")
    result = price_option_quote(quote, bundle)

    assert result.price >= result.european_benchmark - 0.01


def test_non_dividend_american_call_converges_to_european(
    bundle: MarketDataBundle,
) -> None:
    quote = next(item for item in bundle.option_quotes if item.contract.option_type.value == "call")
    result = price_option_quote(quote, bundle)

    assert result.early_exercise_premium == pytest.approx(0.0, abs=0.01)


def test_dividend_and_low_extrinsic_short_call_is_high_assignment_risk(
    bundle: MarketDataBundle,
) -> None:
    quote = next(item for item in bundle.option_quotes if item.contract.option_type.value == "call")
    quote.contract.strike = 200.0
    quote.contract.expiration = bundle.analysis_timestamp + timedelta(days=25)
    quote.implied_volatility = 0.20
    bundle.dividends = [
        DividendForecast(
            ex_date=(bundle.analysis_timestamp + timedelta(days=10)).date(),
            payment_date=(bundle.analysis_timestamp + timedelta(days=15)).date(),
            amount=6.0,
            currency="USD",
            freshness=bundle.underlying.freshness,
            source=bundle.underlying.sources[0],
        )
    ]

    result = price_option_quote(quote, bundle)
    risk = assess_exercise_risk(quote, bundle, PositionSide.SHORT, result)

    assert result.price >= result.european_benchmark - 0.01
    assert risk.assignment_risk is RiskLevel.HIGH
    assert risk.next_ex_dividend_date == bundle.dividends[0].ex_date
    assert any("dividend" in reason.lower() for reason in risk.reasons)


def test_near_strike_short_option_near_expiry_has_high_pin_risk(
    bundle: MarketDataBundle,
) -> None:
    quote = bundle.option_quotes[0]
    quote.contract.strike = bundle.underlying.price
    quote.contract.expiration = bundle.analysis_timestamp + timedelta(days=5)
    result = price_option_quote(quote, bundle)

    risk = assess_exercise_risk(quote, bundle, PositionSide.SHORT, result)

    assert risk.pin_risk is RiskLevel.HIGH
    assert risk.human_review_required
