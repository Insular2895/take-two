# M0.2 Flexible Budget Policy

Status: `COMPLETE_OFFLINE`

Policy: `FlexibleBudgetPolicyV2`
Historical compatibility: `BudgetPolicyV1Legacy`

## Scope and safety boundary

M0.2 adds a prospective capital policy and diagnostics. It does not retune V10,
recalculate historical OOS results, open the final holdout, connect OPRA, start
shadow/paper activity, or add order submission. All produced tickets remain
`read_only=true`, `transmit=false`, `what_if=true`, and
`order_capability=forbidden`.

## User contract

The simple configurator has three primary values:

- `target_budget`: desired deployment;
- `under_target_tolerance`: acceptable under-use;
- `max_overspend`: maximum authorized overspend.

Derived values are:

```text
preferred_lower_bound = max(0, target_budget - under_target_tolerance)
hard_authorized_ceiling = target_budget + max_overspend
```

For `1000 / 200 / 500`, the values are exactly `800 / 1000 / 1500`.
The lower bound is `SOFT` by default, may be `HARD`, or may be disabled with
`OFF`. The upper bound is always hard and inclusive: 1500 passes; 1500.01 does
not. Equality uses only a machine-scale `ulp` tolerance, never an economic
allowance.

`maximum_loss_cap` and `buying_power_cap` accept `AUTO` or an explicit positive
amount. Since M0.2.1, `AUTO` resolves to the lower of the configured hard
ceiling and known account-deployable capital. The V2
`account_liquidity_reserve` is explicit and defaults to zero; when positive it
requires `account_available_capital` and is subtracted from that capital. The
historical five-percent reserve is never silently layered onto V2.

## Configuration

The prospective, non-started Phase M input is
`configs/phase_m/v2/ttwo_prospective_budget.yaml`:

```yaml
budget_policy:
  version: "2.0"
  currency: EUR
  target_budget: 1000
  under_target_tolerance: 200
  max_overspend: 500
  minimum_spend_policy: SOFT
  maximum_loss_cap: {mode: AUTO, value: null}
  buying_power_cap: {mode: AUTO, value: null}
  maximum_contracts: 4
  account_available_capital: null
  account_liquidity_reserve: 0
```

The historical `configs/pre_opra/v1/ttwo_research.yaml` is unchanged and keeps
V1 `budget`, `maximum_loss`, and `safety_reserve_fraction` semantics.

The CLI exposes the same simple inputs:

```bash
ttwo-options trade budget \
  --budget 1000 \
  --budget-currency EUR \
  --allow-under 200 \
  --allow-over 500 \
  --account-capital 2000 \
  --liquidity-reserve 500
```

The same flags are optional on `trade analyze`; without `--budget`, the legacy
request path is unchanged.

## Single evaluation function

Every V2 compiled architecture is passed to:

```python
evaluate_budget_policy(candidate, policy, fx, broker_context, fx_cost)
```

The evaluator compares three parallel constraints in policy currency:

1. required entry cash;
2. maximum economic loss;
3. broker/validated analytical buying power.

They are never added. `effective_capital_requirement` is the maximum relevant
known requirement and is used only as a transparent summary. Entry cash floors
a credit at zero and includes executable ask/bid premiums, entry slippage,
commissions, and entry FX costs. Unknown maximum loss or buying power remains
null, never zero.

FX conversion requires a point-in-time source, timestamp, currency pair, and
rate. A missing conversion emits `FX_REQUIRED` and blocks paper eligibility.
The FX execution cost is separate evidence: a known fixed amount or basis-point
cost is added after conversion; a required unknown cost emits
`FX_EXECUTION_COST_UNKNOWN`, leaves the guarantee unproven, and blocks paper.
An explicit `NOT_APPLICABLE` zero requires a demonstrated no-entry-conversion
account mode.

## Statuses and eligibility

The typed status set is:

- `BELOW_PREFERRED_RANGE`;
- `WITHIN_PREFERRED_RANGE`;
- `ABOVE_TARGET_WITHIN_TOLERANCE`;
- `AT_HARD_CEILING`;
- `EXCEEDS_HARD_BUDGET_CEILING`;
- `MAXIMUM_LOSS_EXCEEDED`;
- `BUYING_POWER_EXCEEDED`;
- `CAPITAL_REQUIREMENT_UNKNOWN`;
- `FX_REQUIRED`;
- `BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN`.

A hard lower-bound failure keeps status `BELOW_PREFERRED_RANGE` and adds the
reason code `BELOW_HARD_MINIMUM_SPEND`. A no-position candidate remains valid
at zero capital and the pipeline emits `NO_POSITION_RECOMMENDED` rather than
altering the configured budget.

`BudgetDiagnostics` records all three requirements, effective capital, delta
to target, headroom, both utilization ratios, eligibility, policy version, FX
provenance, reason codes, and warnings. It is a gate/diagnostic only. It does
not modify Opportunity, Risk, Evidence, Model Agreement, or Execution Quality
and is not a sixth score.

## Whole-contract enumeration

Each integer scale is built as a distinct candidate with its own ID, economics,
risk, diagnostic, and later scores. No post-ranking fractional scaling exists.
Enumeration stops at the policy contract-count limit. Known hard failures can
be pruned cheaply; unknown capital is retained for research and cannot be
assumed affordable.

For a 540-per-unit requirement and a 1500 ceiling:

| Quantity | Capital | Result |
| ---: | ---: | --- |
| 1 | 540 | eligible |
| 2 | 1080 | eligible |
| 3 | 1620 | hard blocked |

## Mixed-expiry correction

For call/put calendars and diagonals, V2 never treats all legs as expiring at a
single terminal spot. The older factory result may remain in memory only as
`LEGACY_COMMON_EXPIRY_PROXY` for V1 reproducibility.

`LifecycleCapitalRequirement` follows `CLOSE_BEFORE_FIRST_EXPIRY` and records:

- managed exit deadline;
- current entry cash;
- validated analytical loss bound, if any;
- validated broker buying power, if any;
- effective requirement;
- calculation status and warnings.

The candidate factory receives the same typed
`MixedExpiryLifecycleConfiguration` used by trade economics. Its configured
calendar-day buffer controls candidate capital, ticket, scenario clipping,
breakeven, and target-arrival deadlines; inconsistent tickets fail closed.

Proof priority is validated broker buying power, then a mathematically
validated architecture-specific bound, otherwise `UNKNOWN`. A scenario-grid
worst observation is never promoted to a guaranteed bound. With no proof, the
candidate remains visible as research-only and receives
`BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN`; paper eligibility is false.

## Ticket 1.2 and compatibility

Newly built `TradeEconomicsTicket` objects use schema 1.2 and include
`budget_diagnostics` plus optional `lifecycle_capital_requirement`. The reader
continues to accept schemas 1.0 and 1.1 with those fields absent. The Markdown
renderer prints policy limits and this trade's cash, loss, buying power,
effective capital, target delta, headroom, status, and eligibility.

Committed pre-OPRA, five-score, M0.1, M0.2, and final-holdout-ledger hashes are
locked by regression tests. No historical validation report is regenerated by
M0.2.1. The V2 policy remains version 2.0 and the ticket remains 1.2 because
the new fields are optional and old payloads remain readable.

See [M0.2.1 Final Budget Semantics Cleanup](M0_2_1_BUDGET_SEMANTICS_CLEANUP.md)
for the frozen final semantics.
