# M0.1 Exit Path and Expiry Economics

Status: `PRE_OPRA_LOGIC_COMPLETE`

Scope: deterministic read-only research mechanics

Ticket schema: `1.1`

## Economic paths

Every scenario cell and breakeven result declares one path:

| Path | Meaning | Costs applied |
| --- | --- | --- |
| `CLOSE_BEFORE_EXPIRY` | Position is closed before the common expiry. | Estimated future bid/ask, slippage, closing commissions and known FX exit cost. |
| `HOLD_TO_EXPIRY` | Same-expiry position reaches settlement. | No option-closing spread/slippage/commission; only known applicable exercise, assignment and settlement fees. |
| `EXERCISE_ASSIGN_SETTLE` | Explicit contract vocabulary for exercise/assignment/settlement analysis. | Known contract/broker fees only; no automatic action is implemented. |
| `MIXED_EXPIRY_MANAGED_CLOSE` | Calendar/diagonal is closed at its managed deadline. | Same estimated costs as a close before expiry. |

An unknown applicable expiry fee makes applied cost and net PnL null and the result `BLOCKED`.
Unknown never means zero. Explicit configured zero is allowed in a synthetic test fixture.

## Entry reconciliation

For each option leg, midpoint premium uses the midpoint and executable premium uses ask for a long
or bid for a short. Quantities and contract multipliers are applied exactly once.

```text
theoretical_mid_net = theoretical_mid_paid - theoretical_mid_received
executable_net = executable_paid_at_ask - executable_received_at_bid
entry_bid_ask_cost = executable_net - theoretical_mid_net
total_entry_cash_flow = executable_net + slippage + commission + known FX cost
```

The spread field explains the difference between the two premium bases; it is not added a second
time to executable premium.

## Same-expiry expiration

At the common expiration, each option value becomes signed intrinsic/settlement payoff. The
breakeven solver evaluates:

```text
expiration_net_pnl(S) = intrinsic_position_value(S)
                        - total_entry_cash_flow
                        - known_exercise_assignment_settlement_cost(S)
```

It never subtracts a future option-closing spread, slippage or commission. With configured zero
expiry fees, roots must reconcile within numerical tolerance to the contractual breakevens already
computed by the payoff engine.

## Mixed-expiry policy

M0.1 supports one conservative policy only:

```text
policy = CLOSE_BEFORE_FIRST_EXPIRY
managed_exit_deadline = first_expiry - configured_calendar_day_buffer
```

Scenario, carry, target-arrival and breakeven calculations cannot continue past that deadline.
Later requested horizons are clipped and labeled `CLIPPED_BY_MIXED_EXPIRY_POLICY`; the terminal
root is a `MANAGED_EXIT_BREAKEVEN`. Calendar/diagonal lifecycle after the first leg expiry is
intentionally not modeled. M0.1 assumes managed closure before first expiry.

## Safety and outstanding validation

This contract cannot submit, modify, cancel, exercise, assign, roll or hedge. Tickets enforce
`read_only=true`, `transmit=false`, `what_if=true` and `order_capability=forbidden`.

Still pending are live NBBO/freshness/depth/provider Greeks and contract discovery (`PENDING_OPRA`),
combo quotes/margin/commission previews (`PENDING_BROKER`), and realized fills, spreads, slippage,
prospective PnL plus probability/score calibration (`PENDING_PAPER`). The final holdout remains
`UNOPENED`; Phase M OPRA remains `NOT_STARTED`.
