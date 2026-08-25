# M0.2.1 Final Budget Semantics Audit

Date: 2026-08-24

Scope: minimal offline cleanup of M0.2 budget semantics. This audit was written
before the business-logic patch.

## Safety boundary observed

- Branch: `codex/v10-quantitative-validation-and-robust-decision-engine`.
- Baseline commit: `f000e58` (`feat: harden flexible budget and capital policy`).
- Worktree: clean at audit start.
- Holdout remains `UNOPENED`; OPRA remains `NOT_STARTED`.
- No order, broker connection, credential, shadow, paper, score-retuning, or
  historical recalculation is in scope.

## Finding 1 — account liquidity reserve

Status: `CONFIRMED`

Evidence:

- `FlexibleBudgetPolicyV2.account_liquidity_reserve` exists and defaults to
  zero.
- `evaluate_budget_policy` only emits a warning when the reserve is positive.
- There is no `account_available_capital`, deployable-account calculation, or
  account-constrained hard ceiling.

Risk: a configured non-zero reserve appears economically active while it does
not reduce deployable capital.

Required patch: add optional account capital, validate non-zero reserve against
known capital, derive deployable capital and use the minimum of configured and
account ceilings for all V2 hard gates and AUTO caps.

## Finding 2 — mixed-expiry close buffer

Status: `CONFIRMED`

Evidence:

- `TradeEconomicsConfiguration` already owns
  `mixed_expiry_close_buffer_calendar_days` with `int >= 0` and default `1`.
- scenario clipping, time decay, breakeven, and target-arrival logic derive
  their deadline through `_lifecycle` from that configuration.
- `candidate_generation/factory.py` independently hardcodes
  `timedelta(days=1)` when constructing `LifecycleCapitalRequirement`.

Risk: candidate budget diagnostics and the later economics ticket can disagree
when the configured buffer is not one day.

Required patch: inject one typed lifecycle configuration into candidate
generation, persist its provenance on the ticket, and fail closed on any
deadline mismatch.

## Finding 3 — FX execution cost

Status: `PARTIAL`

Evidence:

- `FXRate` correctly converts native candidate economics to policy currency.
- execution contracts already expose optional `fx_conversion_cost` /
  `entry_fx_cost`, and their reconciliation includes it when supplied.
- `BudgetCandidate` and `evaluate_budget_policy` do not model FX transaction
  cost as a distinct evidenced context or status.
- candidate generation passes native entry economics and a rate only; unknown
  conversion cost can therefore be treated as zero by omission.

Risk: a converted debit just below the ceiling can be incorrectly authorized
when a real entry conversion fee would push required cash above the ceiling.

Required patch: separate rate from execution cost, support fixed and bps costs,
record source/timestamp/status, add known costs after currency conversion, and
mark a required-but-unknown cost `UNPROVEN` / paper-ineligible.

## Backward-compatibility baseline

- Keep `BudgetPolicyV1Legacy` unchanged.
- Keep optional-field-compatible `FlexibleBudgetPolicyV2.version = 2.0` and
  `TradeEconomicsTicket.schema_version = 1.2` if old V2 payloads remain valid.
- Preserve the committed M0.2 report hashes:
  - JSON: `04fdce78ccc07717632c2d7d192ece4a69783f9626ac7bd50db94c8be16be977`;
  - Markdown: `15304095bc67d474c0f691698e615325956231b92913fd97f4c1a9abedec6065`.

## Initial conclusion

All three requested issues are present. The patch is necessary, bounded, and
can continue without any external market or broker data. Actual broker FX fees,
conversion routes, USD cash availability, buying power, combo margin, and live
commissions remain future Phase M dependencies and must not be invented.

## Closure

- Finding 1 corrected: account reserve now reduces known deployable capital;
  positive reserve without account capital fails validation; all V2 hard gates
  and AUTO caps use the effective ceiling.
- Finding 2 corrected: candidate generation receives the typed lifecycle
  configuration; buffer 0/3 coverage proves shared deadlines across candidate,
  ticket, scenario, breakeven, and target-arrival outputs.
- Finding 3 corrected: `FXExecutionCost` is separate from `FXRate`; fixed/bps
  cost is added after conversion, unknown cost is never zero and paper fails
  closed, while explicit no-conversion evidence permits `NOT_APPLICABLE = 0`.
- Compatibility: V2 remains 2.0 and ticket schema remains 1.2; historical M0.2
  JSON and Markdown hashes match the recorded baseline.
- Validation: 332 tests, Ruff, mypy (187 source files), and 28 schema checks
  pass. Holdout and OPRA state remain unchanged and no order path was added.
