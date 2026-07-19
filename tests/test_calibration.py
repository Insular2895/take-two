from pathlib import Path

from take_two_options.calibration import CalibrationDataset, calibrate_dataset
from take_two_options.domain import CalibrationStatus, ModelReadiness, SimulationModel


def test_calibration_estimates_supported_parameters_and_refuses_heston() -> None:
    dataset = CalibrationDataset.model_validate_json(
        Path("fixtures/ttwo_v2_calibration_fixture.json").read_text(encoding="utf-8")
    )

    report = calibrate_dataset(dataset)
    gbm = next(item for item in report.results if item.model is SimulationModel.GBM)
    heston = next(
        item for item in report.results if item.model is SimulationModel.HESTON_FULL_TRUNCATION
    )

    assert gbm.status is CalibrationStatus.ILLUSTRATIVE
    assert gbm.parameters["annualized_volatility"] > 0
    assert heston.status is CalibrationStatus.INSUFFICIENT_DATA
    assert report.model_readiness is ModelReadiness.SCREEN_GRADE
    assert report.excluded_points == 2
