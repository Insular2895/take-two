# Legacy V9

Fixed budget-plan experiment retained for reproduction only. `single_long`,
`staged_three`, fixed budget buckets, fixed profiles, DTEs, targets, stops, and
holding periods are not inputs to the active optimizer.

```bash
ttwo-options legacy marketdata-accuracy \
  --spec data/marketdata/ttwo_v9_budget_spec.json \
  --json-out experiments/legacy/v9/reports/reproduced.json
```
