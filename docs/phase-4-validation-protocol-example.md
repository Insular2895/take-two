# Phase 4 example — sealed experiment and holdout access

```python
manifest = create_experiment_manifest(
    code_commit=commit,
    config_hash=config_hash,
    dataset_hash=dataset_hash,
    split_policy_hash=split_hash,
    trial_registry_hash=trial_hash,
    seed=seed,
    # other required identity fields omitted here
)
assert verify_experiment_manifest(manifest)

split = build_point_in_time_split(observations, open_final_holdout=False, ...)
assert split.final_holdout_ids == ()
```

The data custodian must first append `seal`, then at most one `evaluate`, then optional `report`
entries to `HoldoutAccessLedger`. Any `tune` after evaluation raises. The real TTWO holdout is not
provisioned, so this example demonstrates the protocol only.
