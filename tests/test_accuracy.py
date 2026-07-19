from datetime import date, timedelta

from take_two_options.accuracy import (
    AccuracyDeltaProfile,
    AccuracyExperimentTemplate,
    AccuracyGeneratorSpec,
    generate_accuracy_suite_spec,
)
from take_two_options.treasury_data import TreasuryCurveObservation, TreasuryYieldCurve


def _sessions() -> list[date]:
    current = date(2025, 7, 21)
    sessions = []
    while len(sessions) < 260:
        if current.weekday() < 5:
            sessions.append(current)
        current += timedelta(days=1)
    return sessions


def test_accuracy_generator_builds_rolling_purged_holdout_panels() -> None:
    sessions = _sessions()
    curve = TreasuryYieldCurve(
        [TreasuryCurveObservation(sessions[0], {91: 0.04, 182: 0.041, 365: 0.042})]
    )
    config = AccuracyGeneratorSpec(
        ticker="TTWO",
        start_date=sessions[0],
        end_date=sessions[-1],
        profiles=[
            AccuracyDeltaProfile(
                profile_id="balanced", long_delta_target=0.55, short_delta_target=0.30
            )
        ],
        experiments=[
            AccuracyExperimentTemplate(
                experiment_id="primary",
                holding_sessions=5,
                target_dte=150,
                profile_ids=["balanced"],
                minimum_train_observations=10,
                minimum_test_observations=4,
                minimum_holdout_observations=2,
            )
        ],
        current_quote_date=sessions[-1],
    )

    suite = generate_accuracy_suite_spec(config, sessions, curve)
    panel = suite.panels[0]

    assert len(panel.observations) >= 40
    assert {item.split for item in panel.observations} == {"train", "test", "holdout"}
    assert all(item.expiration is None for item in panel.observations)
    assert panel.target_dte == 150
    assert all(item.risk_free_rate is not None for item in panel.observations)
    train_exit = max(item.exit_quote_date for item in panel.observations if item.split == "train")
    test_signal = min(
        item.signal_quote_date for item in panel.observations if item.split == "test"
    )
    assert test_signal > train_exit + timedelta(days=1)
    assert panel.multiple_testing_trials == 4
    assert suite.current_scan.expirations
