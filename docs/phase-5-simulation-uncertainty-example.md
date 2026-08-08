# Phase 5 example — exit state and uncertainty sidecars

```python
state = initial_exit_state(-2.0)
state = advance_exit_state(
    state,
    day=1,
    pnl=4.0,
    return_on_risk=0.40,
    is_final_checkpoint=False,
    profit_target=0.50,
    stop_loss=0.40,
)
assert state.state == "open"

probabilities = estimate_path_probabilities(
    path_results,
    maximum_loss=500.0,
    minimum_paths=10_000,
)
profit = probabilities.probabilities["probability_profit"]
assert profit.interval_method == "wilson_binomial_iid"
```

`profit.estimate` is never interpreted alone: `lower`, `upper`,
`effective_sample_size` and `sufficient_paths` travel with it. Weighted paths deliberately omit
the Wilson bounds rather than presenting an iid binomial interval with false precision.

Before enabling a more complex American-exercise simulation, compare aligned coarse and fine
checkpoint results with `compare_exit_discretizations`. A material gap is evidence to
investigate; it is not automatic authorization to select LSM.
