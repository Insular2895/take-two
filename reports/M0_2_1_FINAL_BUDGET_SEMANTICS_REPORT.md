# M0.2.1 Final Budget Semantics Report

Generated: 2026-08-24

Scope: minimal offline pre-OPRA cleanup only

## Three initial issues

1. `account_liquidity_reserve` was configured but did not reduce deployable
   capital (`CONFIRMED`).
2. The mixed-expiry trade-economics buffer existed, but the candidate factory
   independently hardcoded one calendar day (`CONFIRMED`).
3. FX rate conversion existed, but budget authorization lacked a distinct,
   evidenced FX execution-cost context (`PARTIAL`).

## Final semantics

- A positive reserve requires known `account_available_capital`.
- Deployable capital is `max(0, available - reserve)`.
- The effective hard ceiling is the lower of the configured ceiling and known
  deployable capital. V2 hard gates and AUTO loss/buying-power caps honor it.
- A typed `MixedExpiryLifecycleConfiguration` is injected into candidate
  generation and propagated through the ticket, scenarios, breakeven clock,
  and target arrival. Any stored mismatch fails closed.
- `FXRate` converts economics; `FXExecutionCost` adds a fixed or bps entry cost
  after conversion. Unknown required cost remains null, adds
  `FX_EXECUTION_COST_UNKNOWN`, sets the guarantee to `UNPROVEN`, and blocks
  paper. Explicit demonstrated no-conversion evidence permits zero as
  `NOT_APPLICABLE`.

## Compatibility and historical preservation

`FlexibleBudgetPolicyV2` remains version 2.0 and `TradeEconomicsTicket` remains
schema 1.2 because new serialized fields are optional. V1 is unchanged.
Historical validation was not regenerated. The committed M0.2 report remains:

- JSON SHA-256: `04fdce78ccc07717632c2d7d192ece4a69783f9626ac7bd50db94c8be16be977`;
- Markdown SHA-256: `15304095bc67d474c0f691698e615325956231b92913fd97f4c1a9abedec6065`.

## Validation

| Check | Result |
| --- | --- |
| pytest | 332 passed |
| Ruff | passed |
| mypy | 187 source files, no issues |
| JSON Schema | 28 verified |
| Historical hash regression | passed |
| Offline artifacts | passed |
| Research lineage | passed |
| Phase 10 release audit | passed |
| Phase 11 extension gate | passed |
| Security boundary | 166 Python files; zero forbidden order paths |
| Dependency consistency | passed |
| Deterministic fixture generation | passed |

Coverage includes reserve zero/active/invalid/above-account, account-limited
AUTO caps, no-position at zero deployable capital, calendar/diagonal buffers 0
and 3, factory literal removal, FX fixed/bps costs, threshold crossing, unknown
cost, same-currency, and validated maintained USD cash.

## Safety invariants

- `HOLDOUT = UNOPENED`
- `OPRA = NOT_STARTED`
- `read_only = true`
- `transmit = false`
- `what_if = true`
- `order_capability = forbidden`

No OPRA connection, shadow/paper activity, order path, retuning, score change,
or historical/OOS recalculation occurred.

## Remaining Phase M dependencies

Actual IBKR FX fee and conversion route, validated account USD cash, actual
buying power, combo margin, live commissions, authorized OPRA/NBBO and combo
quotes, and prospective shadow/paper fills remain unknown pending Phase M.

`M0_2_1_STATUS = COMPLETE`

`BUDGET_SEMANTICS = FINALIZED`

`PRE_OPRA_LOGIC_STATUS = COMPLETE_AND_FROZEN`

`NEXT_PHASE = M — OPRA READ-ONLY + SHADOW/PAPER VALIDATION`
