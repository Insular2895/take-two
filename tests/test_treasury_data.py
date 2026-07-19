from datetime import date

import pytest

from take_two_options.treasury_data import TreasuryYieldCurve

CSV = """Date,"1 Mo","3 Mo","6 Mo","1 Yr"
07/18/2025,4.30,4.20,4.10,4.00
07/21/2025,4.20,4.10,4.00,3.90
"""


def test_treasury_curve_uses_latest_prior_date_and_interpolates_maturity() -> None:
    curve = TreasuryYieldCurve.from_csv_text(CSV)

    rate = curve.rate_for(date(2025, 7, 20), 136)

    expected = 0.042 + (0.041 - 0.042) * ((136 - 91) / (182 - 91))
    assert rate == pytest.approx(expected)
    assert curve.start_date == date(2025, 7, 18)
    assert curve.end_date == date(2025, 7, 21)

