"""Official U.S. Treasury par-yield curve cache and maturity interpolation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TREASURY_CSV_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&"
    "field_tdr_date_value={year}&page&_format=csv"
)

_TENORS = {
    "1 Mo": 30,
    "1.5 Month": 45,
    "2 Mo": 60,
    "3 Mo": 91,
    "4 Mo": 121,
    "6 Mo": 182,
    "1 Yr": 365,
    "2 Yr": 730,
    "3 Yr": 1_095,
    "5 Yr": 1_825,
    "7 Yr": 2_555,
    "10 Yr": 3_650,
    "20 Yr": 7_300,
    "30 Yr": 10_950,
}


class TreasuryDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class TreasuryCurveObservation:
    observation_date: date
    rates: dict[int, float]


class TreasuryYieldCurve:
    def __init__(self, observations: list[TreasuryCurveObservation]) -> None:
        if not observations:
            raise ValueError("Treasury curve requires observations")
        self._observations = sorted(observations, key=lambda item: item.observation_date)

    @classmethod
    def from_csv_text(cls, text: str) -> TreasuryYieldCurve:
        rows = csv.DictReader(StringIO(text))
        observations: list[TreasuryCurveObservation] = []
        for row in rows:
            raw_date = row.get("Date")
            if not raw_date:
                continue
            month, day, year = (int(part) for part in raw_date.split("/"))
            rates: dict[int, float] = {}
            for label, days in _TENORS.items():
                value = row.get(label)
                if value is not None and value not in {"", "N/A"}:
                    rates[days] = float(value) / 100
            if rates:
                observations.append(
                    TreasuryCurveObservation(date(year, month, day), rates)
                )
        if not observations:
            raise TreasuryDataError("Treasury CSV contained no usable yield rows")
        return cls(observations)

    @classmethod
    def from_files(cls, paths: list[Path]) -> TreasuryYieldCurve:
        observations: list[TreasuryCurveObservation] = []
        for path in paths:
            observations.extend(cls.from_csv_text(path.read_text(encoding="utf-8"))._observations)
        deduplicated = {item.observation_date: item for item in observations}
        return cls(list(deduplicated.values()))

    def rate_for(self, observation_date: date, maturity_days: int) -> float:
        if maturity_days <= 0:
            raise ValueError("maturity_days must be positive")
        eligible = [
            item for item in self._observations if item.observation_date <= observation_date
        ]
        if not eligible:
            raise TreasuryDataError(
                f"No Treasury curve available on or before {observation_date.isoformat()}"
            )
        curve = eligible[-1].rates
        tenors = sorted(curve)
        if maturity_days <= tenors[0]:
            return curve[tenors[0]]
        if maturity_days >= tenors[-1]:
            return curve[tenors[-1]]
        upper_index = next(index for index, days in enumerate(tenors) if days >= maturity_days)
        lower_days = tenors[upper_index - 1]
        upper_days = tenors[upper_index]
        weight = (maturity_days - lower_days) / (upper_days - lower_days)
        return curve[lower_days] * (1 - weight) + curve[upper_days] * weight

    @property
    def start_date(self) -> date:
        return self._observations[0].observation_date

    @property
    def end_date(self) -> date:
        return self._observations[-1].observation_date


def fetch_treasury_year(
    year: int,
    *,
    cache_dir: Path = Path("data/treasury"),
    force_refresh: bool = False,
    timeout: float = 20.0,
) -> Path:
    cache_path = cache_dir / f"daily_treasury_yield_curve_{year}.csv"
    if cache_path.exists() and not force_refresh:
        return cache_path
    url = TREASURY_CSV_URL.format(year=year)
    request = Request(url, headers={"User-Agent": "take-two-options/0.7 read-only research"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            text = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as error:
        raise TreasuryDataError(f"Treasury CSV request failed for {year}: {error}") from error
    TreasuryYieldCurve.from_csv_text(text)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")
    return cache_path
