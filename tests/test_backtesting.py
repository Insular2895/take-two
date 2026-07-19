from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.backtesting import BacktestCase, BacktestDataset, run_backtest
from take_two_options.domain import ModelReadiness


def _dataset() -> BacktestDataset:
    return BacktestDataset.model_validate_json(
        Path("fixtures/ttwo_v2_backtest_fixture.json").read_text(encoding="utf-8")
    )


def test_backtest_uses_executable_sides_and_separate_splits() -> None:
    report = run_backtest(_dataset())
    first = next(item for item in report.cases if item.case_id == "train-long-call-win")

    assert first.entry_outlay == pytest.approx(1_000.0)
    assert first.exit_value == pytest.approx(1_400.0)
    assert first.net_pnl == pytest.approx(395.70)
    assert report.train_metrics.observations == 2
    assert report.test_metrics.observations == 2
    assert report.model_readiness is ModelReadiness.SCREEN_GRADE
    assert report.execution_price_quality == "historical_nbbo"


def test_backtest_rejects_look_ahead_quote() -> None:
    case = _dataset().cases[0].model_dump()
    case["legs"][0]["entry_quote"]["data_available_at"] = "2026-01-06T15:30:00Z"

    with pytest.raises(ValidationError, match="look-ahead"):
        BacktestCase.model_validate(case)
