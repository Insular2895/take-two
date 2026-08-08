# Phase 8 example — configured event beliefs and advisory rules

```python
beliefs = ScenarioProbabilitySet(
    set_id="user-sensitivity-v1",
    probabilities={"launch": 0.40, "delay": 0.60},
    intervals={"launch": (0.20, 0.70), "delay": (0.30, 0.80)},
    origin=ProbabilityOrigin.USER_ASSUMPTION,
    as_of=cutoff,
    source_ids=["research-form"],
    uncertainty_diagnostic="User sensitivity bounds; not confidence intervals.",
    submitted_by="researcher",
)

report = evaluate_event_scenarios(
    scenario_set,
    priced_outcomes,
    objective="maximize_expected_pnl",
    target_return_fraction=0.90,
    large_loss_fraction=0.70,
)
assert any(item.candidate_id == "NO_TRADE" for item in report.candidates)
assert report.order_capability == "forbidden"
```

Every scenario separately declares spot, volatility-level, skew, curvature and liquidity shock
distributions, recovery dynamics, `P/Q`, source and evidence status. The evaluator aggregates only
outcomes priced upstream; it does not invent an option price.

An evidence update uses one `EventEvidenceContract` per normalized event. Reports derived from the
same fact have `dependence_multiplier=0`; a shared driver requires a declared multiplier below one.
`update_sequential_scenario_beliefs` sorts by `observed_at`, verifies an acyclic point-in-time graph,
and returns the existing configured heuristic plus an origin-safe probability sidecar.

Research conditions use timestamped `MetricObservation` objects. Missing, future, stale or
unit-incompatible inputs fail the rule and can preserve `NO_TRADE`. An action such as
`research_eligible_now`, `revalue_after_event` or `exit_review_profit` is human-readable advice;
there is no scheduling or order capability.
