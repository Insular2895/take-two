# M0.2 Budget and Capital Audit

Status: `COMPLETE`

Scope: prospective budget configuration, capital gates, whole-contract sizing,
mixed-expiry lifecycle capital, ticket diagnostics, and V1 compatibility. This
audit does not open the holdout, connect to OPRA, retune V10, or enable orders.

## Initial state

The repository has two active research paths with different capital semantics:

- the historical/pre-OPRA path uses `TradeRequest.budget`,
  `TradeRequest.maximum_loss`, `maximum_contracts`, and a fixed
  `safety_reserve_fraction`;
- the trade-economics path uses `PortfolioState.max_loss_budget` and exposes
  entry cash, maximum loss, and margin in schema 1.1, but has no versioned
  budget contract or centralized eligibility result.

Both paths are read-only. Neither currently implements the requested flexible
target range or an explicit inclusive hard ceiling.

## Findings

### BUDGET-01 — No versioned V1/V2 policy boundary

`TradeRequest` and `CapitalConstraintsConfig` encode a single fixed budget and
maximum loss. They cannot express a preferred lower bound, soft versus hard
minimum spend, an independent overspend tolerance, AUTO capital caps, or an
account liquidity reserve.

Risk: changing those fields in place would rewrite the meaning and hashes of
historical V1 runs.

Correction boundary: preserve V1 inputs and behavior; introduce a separate,
opt-in `FlexibleBudgetPolicyV2` for prospective Phase M research.

### BUDGET-02 — Capital checks are distributed

Budget and maximum-loss checks occur in candidate construction and legacy veto
logic, while trade-economics separately derives entry cash and margin. No
single typed evaluator produces a canonical status, headroom, utilization, and
warnings.

Risk: the same candidate can receive inconsistent capital treatment across
generation, pruning, reporting, and ticketing.

Correction boundary: one `evaluate_budget_policy(candidate, policy, fx,
broker_context)` function will be the V2 source of truth.

### BUDGET-03 — Entry cash, loss, and buying power are not parallel gates

The existing code exposes these values but does not evaluate all three against
independent policy caps. Credit structures can have negative entry cash while
their actual limiting capital is maximum loss or buying power.

Risk: treating a credit as negative budget, or summing entry cash, loss, and
buying power, understates or overstates the requirement.

Correction boundary: evaluate each known dimension independently and define
effective capital as the maximum relevant known requirement, never their sum.
Unknown margin/buying power remains null.

### BUDGET-04 — Mixed-expiry maximum loss is unsafe in the V11 factory

`candidate_generation/factory.py::_risk` sends calendar and diagonal legs with
different expirations through one common-expiry intrinsic payoff grid. The
result is stored as `CandidateRisk.maximum_loss` and used by budget vetoes.

Risk: that terminal value is not a lifecycle capital bound. Front-leg expiry,
assignment/exercise, residual back-leg value, and the managed-exit policy are
not represented. A scenario-grid worst observation would not fix this because
it is not a guaranteed bound.

Correction boundary: V2 mixed-expiry candidates receive a typed
`LifecycleCapitalRequirement`. Priority is broker buying power, then a
validated architecture-specific analytical bound, otherwise `UNKNOWN`.
Unknown remains research-visible and paper-blocked with
`BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN`. The old number may remain only as an
explicit `LEGACY_COMMON_EXPIRY_PROXY` for V1 compatibility.

### BUDGET-05 — Whole-contract generation is present but not V2 budget-aware

The V11 enumerator already emits every integer scale from one through the
contract-count limit. However, the limit is derived only from
`TradeRequest.maximum_contracts`, and each emitted candidate is filtered using
legacy budget semantics.

Risk: the engine cannot show that each quantity is a distinct V2 candidate,
nor stop enumeration using the flexible hard ceiling and capital caps.

Correction boundary: keep integer enumeration, make V2 evaluation explicit on
every quantity, and reject only after computing that quantity's own economics.

### BUDGET-06 — Ticket schema cannot carry the decision contract

`TradeEconomicsTicket` accepts schema 1.0/1.1 and reports raw costs, risk, and
margin, but it does not contain `BudgetDiagnostics` or mixed-expiry lifecycle
capital.

Risk: a renderer or downstream consumer must reconstruct policy decisions from
unversioned fields.

Correction boundary: add schema 1.2 with typed diagnostics while continuing to
parse 1.0 and 1.1 payloads.

### BUDGET-07 — CLI/config naming is not the requested prospective contract

The current thesis scanner exposes `--budget-eur` and `--max-loss-eur`. The
pre-OPRA YAML stores the historical V1 amount and reserve. Neither is an
appropriate place to silently switch semantics.

Correction boundary: add explicit currency-neutral V2 flags/configuration for
a prospective budget diagnostic command/path. Keep historical config files
unchanged.

## Required invariants

- Canonical policy `1000 / -200 / +500` derives `800 / 1000 / 1500`.
- The hard ceiling is inclusive: `1500.00` passes; `1500.01` fails. Only a
  machine-scale floating-point tolerance is permitted.
- `SOFT` minimum spend warns but does not block; `HARD` blocks; `OFF` ignores.
- Entry cash includes executable premiums, fees, slippage, and FX cost.
- Maximum loss and buying power are separate gates; unknown values stay null.
- Credit entry cash is floored at zero for budget consumption.
- No-position candidates remain eligible with zero capital.
- V2 budget diagnostics do not change the five scores or inject a hidden score.
- Mixed-expiry scenario grids are diagnostics, not guaranteed capital bounds.
- Historical V1 configurations and pre-OPRA evidence artifacts are not
  regenerated or reinterpreted.

## Implementation decision to validate in code

M0.2 will add a dedicated `budget` module with versioned policies, FX evidence,
broker context, lifecycle capital, diagnostics, and the central evaluator. The
V11 compiled candidate will carry optional diagnostics/lifecycle fields; the
trade-economics ticket will carry schema 1.2 diagnostics. A separate prospective
Phase M configuration will opt into V2.

This is an implementation boundary for M0.2, not authorization to start Phase M
or to trade.

## Closure evidence

All findings `BUDGET-01` through `BUDGET-07` are closed in the M0.2 code path.
The full repository validation passed with 320 tests, Ruff, mypy, 28 schemas,
offline artifact checks, research lineage, Phase 10/11 audits, the security
boundary, dependency consistency, and deterministic fixture generation.

Historical pre-OPRA/OOS artifacts and the unopened holdout ledger retain their
pre-M0.2 hashes. OPRA remains `NOT_STARTED`; the holdout remains `UNOPENED`;
no order capability was added.
