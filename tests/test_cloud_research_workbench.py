from __future__ import annotations

import math
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.budget import BudgetCandidate, evaluate_budget_policy
from take_two_options.cloud.research_contracts import AnalysisBudgetRequest
from take_two_options.cloud.research_workbench import run_research_analysis
from take_two_options.config.loader import load_prospective_budget_config


@pytest.fixture(scope="module")
def result():  # type: ignore[no-untyped-def]
    return run_research_analysis(
        analysis_request_id="analysis-aaaaaaaaaaaaaaaaaaaaaaaa",
        budget_request=AnalysisBudgetRequest(),
    )


def test_budget_request_maps_exactly_to_v2() -> None:
    base = load_prospective_budget_config(
        Path("configs/phase_m/v2/ttwo_prospective_budget.yaml")
    ).budget_policy
    request = AnalysisBudgetRequest(
        preferred_budget=800,
        target_budget=1000,
        maximum_budget=1500,
        minimum_spend_policy="HARD",
    )
    policy = request.apply_to(base)
    assert policy.target_budget == 1000
    assert policy.under_target_tolerance == 200
    assert policy.max_overspend == 500
    assert policy.preferred_lower_bound == 800
    assert policy.hard_authorized_ceiling == 1500
    assert policy.minimum_spend_policy.value == "HARD"


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_budget_request_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValidationError):
        AnalysisBudgetRequest(preferred_budget=value)


def test_budget_request_rejects_unknown_fields_and_invalid_order() -> None:
    with pytest.raises(ValidationError):
        AnalysisBudgetRequest.model_validate(
            {
                "preferred_budget": 800,
                "target_budget": 1000,
                "maximum_budget": 1500,
                "minimum_spend_policy": "SOFT",
                "market_data_mode": "SYNTHETIC_DEMO",
                "currency": "EUR",
                "repository": "attacker/repo",
            }
        )
    with pytest.raises(ValidationError):
        AnalysisBudgetRequest(preferred_budget=1200, target_budget=1000)


def test_hard_ceiling_has_no_economic_epsilon() -> None:
    base = load_prospective_budget_config(
        Path("configs/phase_m/v2/ttwo_prospective_budget.yaml")
    ).budget_policy
    policy = AnalysisBudgetRequest().apply_to(base)
    exact = evaluate_budget_policy(
        BudgetCandidate(
            candidate_id="exact",
            architecture="fixture",
            currency="EUR",
            required_entry_cash=1500,
            maximum_loss=1500,
        ),
        policy,
        None,
        None,
    )
    above = evaluate_budget_policy(
        BudgetCandidate(
            candidate_id="above",
            architecture="fixture",
            currency="EUR",
            required_entry_cash=1500.01,
            maximum_loss=1500.01,
        ),
        policy,
        None,
        None,
    )
    assert exact.diagnostics.eligible is True
    assert exact.diagnostics.budget_status.value == "AT_HARD_CEILING"
    assert above.diagnostics.eligible is False
    assert above.diagnostics.budget_status.value == "EXCEEDS_HARD_BUDGET_CEILING"


def test_complete_generated_universe_is_retained(result) -> None:  # type: ignore[no-untyped-def]
    assert result.market_data_mode.value == "SYNTHETIC_DEMO"
    assert result.total_generated == sum(result.combinations_by_architecture.values())
    assert len(result.summaries) == result.total_generated
    assert len(result.details) == result.total_generated
    assert {item.candidate_id for item in result.summaries} == {
        item.candidate_id for item in result.details
    }
    assert [item.engine_rank for item in result.summaries] == list(
        range(1, result.total_generated + 1)
    )


def test_top_views_do_not_delete_or_cap_candidates(result) -> None:  # type: ignore[no-untyped-def]
    assert len(result.best_overall_ids) == 25
    assert result.total_generated > len(result.best_overall_ids)
    assert all(item.trade_economics_ticket_hash for item in result.summaries)
    assert result.safety == {
        "read_only": True,
        "transmit": False,
        "order_capability": "forbidden",
    }


def test_missing_metrics_are_null_not_invented_zero(result) -> None:  # type: ignore[no-untyped-def]
    assert all(item.expected_pnl is None for item in result.summaries)
    assert all(item.probability_profit is None for item in result.summaries)
    assert all(item.net_theta is None for item in result.summaries)
    assert all(item.score_probability is None for item in result.summaries)


def test_no_trade_is_a_first_class_terminal_result() -> None:
    result = run_research_analysis(
        analysis_request_id="analysis-bbbbbbbbbbbbbbbbbbbbbbbb",
        budget_request=AnalysisBudgetRequest(
            preferred_budget=1,
            target_budget=1,
            maximum_budget=1,
            minimum_spend_policy="HARD",
        ),
    )
    assert result.status == "NO_TRADE"
    assert result.verdict == "NO_TRADE"
    assert result.total_generated > 0
    assert result.total_paper_eligible == 0
    assert result.no_trade_reasons == ["NO_CANDIDATE_PASSED_PAPER_ELIGIBILITY_GATES"]
