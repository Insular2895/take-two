import pytest
from pydantic import ValidationError

from take_two_options.optimization.allocation_pareto import (
    AllocationObjectiveKind,
    AllocationParetoPoint,
    OptimizationObjectiveContract,
    allocation_pareto_frontier,
    dominates_allocation,
    evaluate_scalar_objective,
)


def _point(
    allocation_id: str,
    *,
    counts: tuple[int, ...],
    expected: float,
    worst: float,
    risk: float,
    cost: float,
) -> AllocationParetoPoint:
    return AllocationParetoPoint(
        allocation_id=allocation_id,
        counts=counts,
        expected_return_fraction=expected,
        worst_case_return_fraction=worst,
        volatility_fraction=risk,
        cvar_fraction=risk,
        cost_fraction=cost,
        maximum_loss_fraction=cost,
        execution_risk_fraction=risk / 10,
        model_dispersion_fraction=risk / 5,
        scalar_objective=expected - risk,
        no_trade=not any(counts),
    )


def test_exact_pareto_frontier_removes_dominated_points_and_preserves_cash() -> None:
    cash = _point("cash", counts=(0, 0), expected=0.0, worst=0.0, risk=0.0, cost=0.0)
    dominated = _point("dominated", counts=(1, 0), expected=-0.01, worst=-0.02, risk=0.1, cost=0.2)
    prudent = _point("prudent", counts=(0, 1), expected=0.04, worst=0.02, risk=0.03, cost=0.2)
    aggressive = _point(
        "aggressive", counts=(1, 1), expected=0.12, worst=-0.01, risk=0.12, cost=0.4
    )

    frontier = allocation_pareto_frontier([cash, dominated, prudent, aggressive])

    assert {point.allocation_id for point in frontier} == {
        "cash",
        "prudent",
        "aggressive",
    }
    assert dominates_allocation(cash, dominated)
    assert not dominates_allocation(prudent, aggressive)


def test_versioned_objectives_select_weighted_or_worst_case_expectation() -> None:
    weighted = OptimizationObjectiveContract(
        objective_id="weighted-v1",
        kind=AllocationObjectiveKind.WEIGHTED_MEAN_RISK,
        risk_aversion=0,
        cvar_aversion=0,
        execution_penalty=0,
        model_risk_penalty=0,
        regime_weight_semantics="configured_heuristic_sensitivity",
    )
    worst_case = weighted.model_copy(
        update={
            "objective_id": "worst-v1",
            "kind": AllocationObjectiveKind.WORST_CASE_MEAN_RISK,
        }
    )
    inputs = {
        "weighted_expected_usd": 100.0,
        "worst_case_expected_usd": -50.0,
        "variance_usd2": 10_000.0,
        "cvar_usd": 30.0,
        "execution_risk_usd": 5.0,
        "model_dispersion_usd": 150.0,
        "budget_usd": 1_000.0,
    }

    assert evaluate_scalar_objective(weighted, **inputs) == pytest.approx(0.1)
    assert evaluate_scalar_objective(worst_case, **inputs) == pytest.approx(-0.05)
    with pytest.raises(ValidationError, match="evidence hash"):
        OptimizationObjectiveContract(
            objective_id="unsupported-validated-claim",
            kind=AllocationObjectiveKind.WEIGHTED_MEAN_RISK,
            risk_aversion=0,
            cvar_aversion=0,
            execution_penalty=0,
            model_risk_penalty=0,
            regime_weight_semantics="validated_oos",
        )


def test_frontier_rejects_fractional_counts_and_missing_no_trade() -> None:
    with pytest.raises(ValidationError):
        _point(
            "fractional",
            counts=(0.5,),  # type: ignore[arg-type]
            expected=0.1,
            worst=0.0,
            risk=0.1,
            cost=0.1,
        )
    risky = _point("risky", counts=(1,), expected=0.1, worst=0.0, risk=0.1, cost=0.1)
    with pytest.raises(ValueError, match="NO_TRADE"):
        allocation_pareto_frontier([risky])
