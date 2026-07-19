from pathlib import Path

import pytest

from take_two_options.data import FixtureDataProvider
from take_two_options.domain import MarketDataBundle


@pytest.fixture
def bundle() -> MarketDataBundle:
    return FixtureDataProvider(Path("fixtures/ttwo_v1_fixture.json")).load_bundle()


@pytest.fixture
def v2_bundle() -> MarketDataBundle:
    return FixtureDataProvider(Path("fixtures/ttwo_v2_fixture.json")).load_bundle()
