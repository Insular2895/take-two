# Cloud signed cash-flow accounting

Date: 2026-08-24

Status: `IMPLEMENTED_PRE_LIVE_READ_ONLY`

## Sign convention

All canonical cloud cash flows use the account perspective:

- positive = cash received by the account;
- negative = cash paid by the account.

`CloudPositionDossier` schema 1.1 contains two independent values:

- `entry_cash_flow_policy`: signed opening account cash flow after canonical conversion and all
  known entry costs exactly once;
- `capital_required_policy`: governed non-negative capital consumption from
  `BudgetDiagnostics.effective_capital_requirement`.

Capital requirement is never a PnL basis. The exporter takes the sign from the canonical
`TradeEconomicsTicket.entry_cost.total_entry_cash_flow` cost convention and reverses it into the
account convention. It does not use the floored budget cash requirement to infer debit or credit.
Unprovable sign or capital fails with `ENTRY_CASH_FLOW_SIGN_UNPROVEN` or
`CAPITAL_REQUIREMENT_UNPROVEN`.

## Projection formulas

For remaining quantity `R` out of original quantity `Q`:

```text
entry_cash_flow_remaining = entry_cash_flow_policy * R / Q
capital_required_remaining = capital_required_policy * R / Q

MTM_PNL = signed_current_structure_mark + entry_cash_flow_remaining
ESTIMATED_LIQUIDATION_PNL = estimated_close_cash_flow_policy
                            + entry_cash_flow_remaining
```

Returns and governed exit thresholds use `capital_required_remaining` as denominator. It does not
enter either PnL sum.

Closing costs always reduce the close cash flow:

```text
net_close_cash_flow = signed_gross_close_cash_flow
                      - commission
                      - slippage
                      - FX transaction cost
```

This makes a receipt smaller and a required payment more negative.

## Combo and manual reconciliation

A combo quote contains a positive absolute `price` plus an explicit `cash_flow_type`:

- `CREDIT`: closing receives cash;
- `DEBIT`: closing requires cash.

Legwise fallback remains naturally signed: sell-to-close long legs are positive and buy-to-close
short legs are negative. No result is floored at zero.

Manual IBKR reconciliation also requires a positive absolute fill price and explicit
`close_cash_flow_type`. Realized PnL is:

```text
allocated_entry_cash_flow + signed_close_cash_flow_policy
```

Partial closes allocate entry cash flow by `quantity_closed / original_quantity`. The first partial
fill cannot realize the full opening cash flow.

## Compatibility and persistence

Migrations `0003` and `0004` are additive. Legacy D1 columns remain export-compatible but are not
canonical. Only a schema 1.0 `SYNTHETIC_DEMO` whose executable legs prove a net debit may be adapted
to 1.1. Other legacy rows are marked `RECONCILIATION_REQUIRED`; strategy names are never used to
guess cash-flow direction.

Close-preview economics, including the new signed close cash flow, remain immutable. Whole-BAG
preview behavior, Cloudflare Access, CSRF, action-password confirmation, and the forbidden order
boundary are unchanged.
