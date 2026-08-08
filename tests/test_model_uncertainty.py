import pytest

from take_two_options.quantitative.model_uncertainty import (
    EnsembleMemberEstimate,
    EnsembleWeightBasis,
    summarize_model_ensemble,
)
from take_two_options.quantitative.probability_calibration import (
    evaluate_binary_calibration,
)


def _member(
    member_id: str,
    *,
    mean: float,
    weight: float,
    calibration_status: str = "illustrative",
) -> EnsembleMemberEstimate:
    return EnsembleMemberEstimate(
        member_id=member_id,
        model_id=f"model-{member_id}",
        parameter_set_id=f"parameters-{member_id}",
        weight=weight,
        expected_value=mean,
        outcome_variance=4.0,
        mean_standard_error=1.0,
        probability_profit=0.4 if mean == 0 else 0.7,
        observations=1_000,
        calibration_status=calibration_status,
    )


def test_model_ensemble_separates_within_between_and_monte_carlo_uncertainty() -> None:
    report = summarize_model_ensemble(
        [_member("a", mean=0.0, weight=0.5), _member("b", mean=10.0, weight=0.5)],
        weight_basis=EnsembleWeightBasis.EQUAL_SENSITIVITY,
    )

    assert report.weighted_expected_value == 5.0
    assert report.within_model_predictive_variance == 4.0
    assert report.between_model_predictive_variance == 25.0
    assert report.total_predictive_variance == 29.0
    assert report.monte_carlo_standard_error == pytest.approx(2**-0.5)
    assert report.expected_value_range == (0.0, 10.0)
    assert report.claim_status == "diagnostic_only"


def test_oos_ensemble_evidence_requires_hash_weights_and_calibrated_members() -> None:
    report = summarize_model_ensemble(
        [
            _member("a", mean=0.0, weight=0.5, calibration_status="calibrated"),
            _member("b", mean=10.0, weight=0.5, calibration_status="calibrated"),
        ],
        weight_basis=EnsembleWeightBasis.VALIDATED_OOS,
        validation_dataset_hash="sha256:authorized-validation-dataset",
    )

    assert report.claim_status == "oos_evidence_declared"
    assert report.blockers == ()
    with pytest.raises(ValueError, match="sum to one"):
        summarize_model_ensemble(
            [_member("a", mean=0.0, weight=0.4), _member("b", mean=1.0, weight=0.4)],
            weight_basis=EnsembleWeightBasis.USER_ASSUMPTION,
        )


def test_calibration_curve_and_scores_distinguish_calibrated_synthetic_forecasts() -> None:
    outcomes = [True] * 10 + [False] * 90 + [True] * 90 + [False] * 10
    calibrated = evaluate_binary_calibration(
        [0.1] * 100 + [0.9] * 100,
        outcomes,
        bins=10,
        minimum_observations=100,
        dataset_role="validation",
        dataset_hash="sha256:synthetic-validation",
    )
    reversed_forecasts = evaluate_binary_calibration(
        [0.9] * 100 + [0.1] * 100,
        outcomes,
        bins=10,
        minimum_observations=100,
    )

    assert calibrated.status == "diagnostic_ready"
    assert calibrated.expected_calibration_error == pytest.approx(0.0)
    assert len(calibrated.bins) == 2
    assert calibrated.brier_score < reversed_forecasts.brier_score
    assert calibrated.log_loss < reversed_forecasts.log_loss


def test_calibration_stays_insufficient_and_holdout_identity_is_mandatory() -> None:
    report = evaluate_binary_calibration(
        [0.5, 0.5],
        [True, False],
        minimum_observations=100,
    )
    assert report.status == "insufficient_data"
    with pytest.raises(ValueError, match="dataset hash"):
        evaluate_binary_calibration(
            [0.5, 0.5],
            [True, False],
            dataset_role="final_holdout",
        )
