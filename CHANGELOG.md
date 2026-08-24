# Changelog

## 0.12.2 — 2026-08-24

### M0.2 flexible budget configurator and capital safety

- Added separate `BudgetPolicyV1Legacy` and `FlexibleBudgetPolicyV2` contracts with asymmetric
  target tolerances, SOFT/HARD/OFF lower policy, explicit/AUTO loss and buying-power caps, and no
  hidden V2 reserve.
- Centralized entry-cash, maximum-loss, buying-power and point-in-time FX gates in
  `evaluate_budget_policy`; credit cash is floored at zero and unknown capital remains null.
- Added per-quantity V2 diagnostics to whole-contract generation without changing the five scores.
- Removed common-expiry terminal payoff from V2 calendar/diagonal authorization and added the
  research-only `LifecycleCapitalRequirement` fail-closed path.
- Versioned the trade-economics ticket to 1.2 while retaining 1.0/1.1 readers, added the Budget
  renderer, prospective Phase M config/CLI, schemas, reports, and regression coverage.
- Preserved historical/OOS artifacts, the unopened holdout, `OPRA=NOT_STARTED`, and the no-order
  boundary.

## 0.12.1 — 2026-08-24

### M0.1 final pre-OPRA trade economics corrections

- Split theoretical midpoint premiums from executable ask-paid/bid-received premiums while
  preserving readable ticket 1.0 compatibility fields and exact signed cost reconciliation.
- Added explicit close, hold-to-expiry, exercise/assignment/settlement and mixed-expiry managed
  exit paths; expiration no longer receives fictitious option-closing costs.
- Expanded the Markdown ticket with complete carry/decay economics, net PnL distribution metrics,
  canonical five-score snapshots, event timing and applied exit costs.
- Enforced real-world path-state requirements for expected PnL, event-date-aware IV crush, and the
  configurable `CLOSE_BEFORE_FIRST_EXPIRY` lifecycle policy.
- Regenerated schema 1.1 golden/probability fixtures without opening the holdout, connecting OPRA,
  or adding any order capability.

## 0.12.0 — 2026-08-24

### M0 Greeks, Carry & Trade Economics hardening

- Added versioned strict models for advanced Greeks, numerical confidence, carry, volatility
  stresses, breakeven clocks, touch probability, costs, margin, FX, attribution, intensity and the
  `TradeEconomicsTicket`.
- Added same-full-pricer Vanna, Vomma, Charm, Veta, Speed and Color with configurable multi-bump and
  grid-refinement diagnostics plus European analytic benchmarks.
- Added full-repriced flat-spot carry, Spot × Time × IV matrices, generic multi-root breakevens,
  target-arrival timing and factor-order-invariant Shapley attribution.
- Split entry, estimated exit and round-trip economics; eliminated false-zero execution and margin
  fallbacks; retained indicative per-leg combo status.
- Added explicit dividend-treatment guards, rate-curve metadata, exact DTE and date-engine
  intraday precision statuses.
- Extended future read-only OPRA contracts with optional contract identity, adjustment and provider
  Greek metadata without connecting a provider.
- Added the versioned configuration section, JSON Schema, renderer, synthetic golden reports,
  numerical/property tests, implementation specification and 2026 source audit.
- Preserved `transmit=false`, `what_if=true`, `order_capability=forbidden`; final holdout untouched.
