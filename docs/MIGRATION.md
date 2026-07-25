# Migration

## Removed from the active path

- V8 fixed architecture selection and V9 fixed budget plans;
- `single_long`, `staged_three`, `budget_plan_id`, and `budget_bucket`;
- fixed `delta55_30`, strike offsets, DTE targets, profit targets, stops, and
  holding periods as active assumptions;
- LEAPS as a separate architecture;
- reused V7/V8/V9 holdouts as final validation;
- silent `min(configured_minimum, available_observations)` behavior.

## Preserved

- read-only Alpaca and MarketData.app adapters and verified cache;
- American-option, IV/Greeks, bid/ask, costs, payoff, calibration, bootstrap,
  Wilson, DSR, VaR/CVaR, and no-trade utilities;
- historical fixtures, reports, SQL, and documentation under versioned legacy
  directories;
- all existing non-regression tests.

## New active contracts

`KnowledgeItem`, `StrategyRecipe`, `ModernValidationRecord`, `CompiledRule`,
`TradeRequest`, `ResearchRun`, `TrialRecord`, `CompiledStrategyCandidate`, and
`DecisionReport` are strict Pydantic objects. Every run records seed,
configuration/knowledge/data hashes, real trial counts, and blocking reasons.
