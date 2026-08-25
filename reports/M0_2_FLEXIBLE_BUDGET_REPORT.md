# M0.2 Flexible Budget Report

Generated: 2026-08-24

Scope: offline budget/capital hardening only

## Initial state

- Historical V10/pre-OPRA used one legacy budget, maximum loss, contract cap,
  and safety reserve.
- No typed asymmetric target range or central cross-architecture capital gate
  existed.
- The V11 candidate factory still exposed a common-expiry terminal payoff as
  maximum loss for calendars/diagonals.
- Trade-economics ticket 1.1 exposed cash/loss/margin but no policy diagnostic.

## Budget policies

`BudgetPolicyV1Legacy` preserves historical `budget`, `maximum_loss`, and
`safety_reserve_fraction` semantics. Historical reports are not regenerated.

`FlexibleBudgetPolicyV2` provides:

- target budget;
- asymmetric under/over tolerances;
- `SOFT`, `HARD`, or `OFF` minimum spend;
- `AUTO` or explicit maximum-loss and buying-power caps;
- whole-contract cap;
- explicit zero-default account liquidity reserve;
- policy version and derived values.

The single `evaluate_budget_policy(candidate, policy, fx, broker_context)`
function evaluates entry cash, maximum loss, and buying power in parallel. It
uses point-in-time FX evidence and never adds the three capital constraints.
Unknown loss/margin remains null.

## Canonical 1000 / -200 / +500 example

| Value | EUR |
| --- | ---: |
| Preferred lower bound | 800 |
| Target budget | 1,000 |
| Hard authorized ceiling | 1,500 |
| AUTO maximum-loss cap | 1,500 |
| AUTO buying-power cap | 1,500 |

1500 is accepted at the inclusive hard ceiling. 1500.01 emits
`EXCEEDS_HARD_BUDGET_CEILING`. A 700 candidate is eligible and warned under
`SOFT`; it is blocked with reason `BELOW_HARD_MINIMUM_SPEND` under `HARD`.

At 540 per unit, quantities 1 and 2 are eligible at 540 and 1080; quantity 3
is a distinct candidate and is blocked at 1620. No fractional quantity is
constructed.

## Capital safeguards

- Debit entry cash uses executable premiums, slippage, commissions, and entry
  FX cost.
- Credit entry cash is zero for budget consumption, not negative; loss and
  buying power still gate independently.
- Custom risk caps can block a candidate even when entry cash is below target.
- Missing FX emits `FX_REQUIRED`.
- Missing required capital emits `CAPITAL_REQUIREMENT_UNKNOWN` and blocks paper.
- `NO_POSITION_RECOMMENDED` does not increase budget, reduce fees, or assume a
  better fill.
- Budget diagnostics are outside the five scores and do not alter ranking
  economics.

## Mixed-expiry correction

For call/put calendars and diagonals, BudgetPolicyV2 excludes the factory's
common-expiry payoff proxy. `LifecycleCapitalRequirement` enforces
`CLOSE_BEFORE_FIRST_EXPIRY` and uses, in order:

1. validated broker buying power;
2. validated architecture-specific analytical bound;
3. `UNKNOWN`.

A scenario-grid worst observation is never treated as proof. With no valid
bound, maximum loss remains null, the candidate stays visible for research,
paper eligibility is false, and status is
`BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN`. Legacy V1 may retain the old number
only with label `LEGACY_COMMON_EXPIRY_PROXY`.

## Ticket, configuration, and CLI

- `TradeEconomicsTicket` is now 1.2 with `budget_diagnostics` and lifecycle
  capital; 1.0 and 1.1 payloads remain readable.
- The renderer prints policy, trade capital, delta, utilization, headroom,
  status, and eligibility.
- `configs/phase_m/v2/ttwo_prospective_budget.yaml` prepares V2 without starting
  Phase M.
- `ttwo-options trade budget` and optional `trade analyze` flags expose
  `--budget`, `--budget-currency`, `--allow-under`, `--allow-over`, and advanced
  caps.

## Validation

| Check | Result |
| --- | --- |
| pytest | 320 passed |
| Ruff | passed |
| mypy | 187 source files, no issues |
| JSON Schema | 28 verified |
| Offline artifacts | passed |
| Research lineage | passed |
| Phase 10 release audit | passed |
| Phase 11 extension gate | passed |
| Security boundary | 166 Python files; zero forbidden order paths |
| Dependency consistency | passed |
| Deterministic fixture generation | passed |

Regression tests lock hashes for the final pre-OPRA report, baseline,
five-score artifact, M0.1 report, and unopened holdout ledger. No OOS or
historical validation artifact changed.

## Remaining Phase M dependencies

Still required externally: authorized OPRA/NBBO and combo quotes, validated
broker what-if buying power/margin and commissions, account permissions,
fresh point-in-time FX, paper fills/slippage, and shadow/paper sample evidence.
None was requested or connected in M0.2.

## Safety and final status

- `HOLDOUT = UNOPENED`
- `OPRA = NOT_STARTED`
- `read_only = true`
- `transmit = false`
- `what_if = true`
- `order_capability = forbidden`

`M0_2_STATUS = COMPLETE`

`FLEXIBLE_BUDGET_POLICY = READY`

`PRE_OPRA_LOGIC_STATUS = COMPLETE`

`NEXT_PHASE = M — OPRA READ-ONLY + SHADOW/PAPER VALIDATION`
