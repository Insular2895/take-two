# M0.2.1 Final Budget Semantics Cleanup

Status: `COMPLETE_OFFLINE_AND_FROZEN`

This minimal patch closes the three remaining pre-OPRA budget-semantics gaps.
It does not change V10, the five scores, historical/OOS results, the holdout, or
any execution capability.

## Account reserve semantics

`FlexibleBudgetPolicyV2` now distinguishes the user-authorized trade budget
from available account capital:

```text
account_deployable_capital =
  max(0, account_available_capital - account_liquidity_reserve)

effective_hard_budget_ceiling =
  min(hard_authorized_ceiling, account_deployable_capital)
```

When account capital is unknown, the effective ceiling remains the configured
hard ceiling. A positive reserve requires known account capital at policy
validation time. V2 AUTO maximum-loss and buying-power caps use the effective
ceiling; explicit caps remain declared risk caps, while the effective account
ceiling still dominates every authorization. V1 keeps its historical 5%
reserve behavior unchanged; V2 never applies a hidden fractional reserve.

Diagnostics expose available capital, reserve, deployable capital, configured
ceiling, effective ceiling, and account headroom. The CLI accepts
`--account-capital` and `--liquidity-reserve` on the prospective budget paths.

## One mixed-expiry lifecycle configuration

`MixedExpiryLifecycleConfiguration` is the typed source of the
`CLOSE_BEFORE_FIRST_EXPIRY` policy, calendar-day buffer, source, and version.
It is resolved upstream and injected into candidate generation. The factory no
longer owns a one-day business literal.

For mixed expiries:

```text
first_expiry = min(leg expirations)
managed_exit_deadline = first_expiry - close_buffer_calendar_days
```

The same deadline is persisted in candidate capital, the ticket, clipped
scenarios, managed-exit breakevens, and target-arrival results. Ticket
validation fails closed with `MIXED_EXPIRY_LIFECYCLE_CONFIG_MISMATCH` if any
stored deadline or provenance disagrees. Buffers 0 and 3 are covered for
calendars and diagonals. No post-first-expiry lifecycle was added.

## FX rate and FX execution cost

`FXRate` remains the point-in-time economic conversion. The separate
`FXExecutionCost` records account mode, status, fixed policy-currency amount or
basis points, source, timestamp, and assumptions. Entry cash is calculated as:

```text
converted_required_entry_cash = max(convert(native_required_entry_cash), 0)
required_entry_cash_after_fx =
  converted_required_entry_cash + entry_fx_transaction_cost
```

Executable bid/ask already contains spread economics, so spread is not added a
second time. Credit entry cash remains floored at zero, but a real FX fee can
still consume cash. A required unknown FX cost remains null, makes the budget
guarantee `UNPROVEN`, adds `FX_EXECUTION_COST_UNKNOWN`, and blocks paper while
preserving research analysis. Zero is accepted only as explicit
`NOT_APPLICABLE` evidence, including validated maintained underlying-currency
cash.

## Compatibility and safety

The additions are optional for existing serialized V2 and ticket payloads, so
`FlexibleBudgetPolicyV2.version = 2.0` and
`TradeEconomicsTicket.schema_version = 1.2` remain stable. Historical M0.2
reports are hash-protected and were not regenerated.

- `HOLDOUT = UNOPENED`
- `OPRA = NOT_STARTED`
- `read_only = true`
- `transmit = false`
- `what_if = true`
- `order_capability = forbidden`

Actual broker FX fees/routes, validated USD cash, buying power, combo margin,
commissions, NBBO/combination quotes, and paper fills remain Phase M evidence.
