# Phase 7 example — versioned objective and exact Pareto frontier

```python
objective = OptimizationObjectiveContract(
    objective_id="prudent-worst-case-v1",
    version="1.0",
    kind=AllocationObjectiveKind.WORST_CASE_MEAN_RISK,
    risk_aversion=1.2,
    cvar_aversion=1.0,
    execution_penalty=0.8,
    model_risk_penalty=0.8,
    regime_weight_semantics="configured_heuristic_sensitivity",
)

report = optimize_allocations_with_frontier(
    ...,
    objective_contract=objective,
)
assert any(point.no_trade for point in report.pareto_frontier)
```

`selected_allocations` preserves the familiar scalar ranking. `pareto_frontier` is computed
separately from every feasible whole-contract vector and is the correct view for return/risk/cost
trade-offs. Neither output is permission to trade.
