from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from take_two_options.historical_data.market_context import (
    UnderlyingDailyBar,
    parse_ecb_fx_csv,
    parse_treasury_csv,
)


def test_public_rate_parsers_apply_conservative_next_day_availability() -> None:
    treasury = parse_treasury_csv('Date,"1 Mo","1 Yr"\n07/17/2026,3.73,4.01\n')
    fx = parse_ecb_fx_csv("TIME_PERIOD,OBS_VALUE,OBS_STATUS\n2026-07-17,1.16,A\n")
    assert treasury[0].rates_by_maturity_days[30] == pytest.approx(0.0373)
    assert treasury[0].available_at.date().isoformat() == "2026-07-18"
    assert fx[0].usd_per_eur == pytest.approx(1.16)
    assert fx[0].available_at.date().isoformat() == "2026-07-18"


def test_underlying_bar_rejects_impossible_ohlc_and_lookahead() -> None:
    with pytest.raises(ValidationError):
        UnderlyingDailyBar(
            ticker="TTWO",
            market_time=datetime(2026, 1, 1, tzinfo=UTC),
            available_at=datetime(2026, 1, 1, tzinfo=UTC),
            open=100,
            high=99,
            low=98,
            close=100,
            volume=1,
            feed="iex",
        )
