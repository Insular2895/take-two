import pytest

from take_two_options.research_statistics import (
    bootstrap_interval,
    conditional_value_at_risk,
    deflated_sharpe_probability,
    empirical_quantile,
    payoff_ratio,
    profit_factor,
    wilson_interval,
)


def test_intervals_and_tail_risk_are_deterministic() -> None:
    values = [-0.4, -0.1, 0.05, 0.2, 0.3]

    first = bootstrap_interval(values, lambda sample: sum(sample) / len(sample), samples=500)
    second = bootstrap_interval(values, lambda sample: sum(sample) / len(sample), samples=500)

    assert first == second
    assert first[0] < first[1]
    assert empirical_quantile(values, 0.5) == pytest.approx(0.05)
    assert conditional_value_at_risk(values) == pytest.approx(0.4)


def test_win_rate_and_multiple_testing_diagnostics_are_bounded() -> None:
    low, high = wilson_interval(6, 10)
    probability = deflated_sharpe_probability(
        [-0.1, 0.02, 0.05, 0.08, 0.12, 0.15, 0.18, 0.2],
        trials=20,
    )

    assert low < 0.6 < high
    assert probability is not None
    assert 0 <= probability <= 1


def test_profit_and_payoff_ratios_use_positive_and_negative_returns() -> None:
    values = [-0.2, -0.1, 0.1, 0.4]

    assert profit_factor(values) == pytest.approx(5 / 3)
    assert payoff_ratio(values) == pytest.approx(5 / 3)
