# Phase M governed context propagation

Date: 2026-08-24

Status: `IMPLEMENTED_PRE_OPRA_READ_ONLY`

## Scope

This integration layer does not change V10 formulas, five-score formulas, ranking, historical
budget policy V1, or the approved V2 budget semantics. It provides one prospective context that
binds the already-existing static policy and optional runtime evidence to one auditable identity.

It starts no OPRA connection, paper run, holdout evaluation, or broker execution path.

## Static policy and runtime evidence

`ProspectiveBudgetConfig` is the static, governed policy loaded from
`configs/phase_m/v2/ttwo_prospective_budget.yaml`. It owns:

- `FlexibleBudgetPolicyV2`;
- `MixedExpiryLifecycleConfiguration`;
- `holdout_status=UNOPENED`;
- `opra_status=NOT_STARTED`;
- `read_only=true`, `transmit=false`, and `order_capability=forbidden`.

`FXRate`, `FXExecutionCost`, and `BrokerCapitalContext` are point-in-time runtime evidence. They do
not enter the YAML and cannot mutate it. User authorization in the static budget remains distinct
from broker account reality.

## Canonical contract

`PhaseMDecisionContext` contains:

- the prospective config, its source path, and its stable hash;
- optional FX rate, FX execution cost, and broker capital evidence;
- a timezone-aware creation timestamp;
- canonical source IDs;
- a deterministic `context_id` and `context_hash`.

The hash includes the complete static config, lifecycle config, every supplied runtime evidence
object, and provenance. It excludes `created_at`, so identical governed inputs produce the same
identity. The model has no API-key, password, token, or free-form secret field.

`build_phase_m_decision_context(...)` validates typed inputs and hashes them.
`load_phase_m_decision_context(...)` calls the existing `load_prospective_budget_config(...)` once,
then delegates to the builder. No second YAML parser exists.

## Validation

The builder and candidate-cutoff validation enforce:

- required explicit mixed-expiry lifecycle;
- timezone-aware context and runtime timestamps;
- FX policy currency equal to the budget policy currency;
- FX source currency equal to candidate currency when conversion is required;
- FX, FX-cost, and validated broker timestamps at or before the candidate cutoff;
- fixed FX cost expressed in policy currency;
- broker currency directly in policy currency or convertible through the supplied governed FX pair;
- deterministic, internally consistent config and context hashes.

Absent FX cost during a required conversion remains `UNKNOWN` in `BudgetDiagnostics`; it never
becomes zero. Same-currency evaluation needs no artificial FX object and resolves the execution
cost as `NOT_APPLICABLE`. Unknown required broker buying power remains null.

## Propagation graph

```text
ProspectiveBudgetConfig
        |
        +---- budget_policy
        |
        +---- mixed_expiry_lifecycle
        |
        v
PhaseMDecisionContext
        |
        +---- FXRate
        |
        +---- FXExecutionCost
        |
        +---- BrokerCapitalContext
        |
        v
analyze_trade
        |
        v
enumerate_candidates
        |
        v
build_candidate
        |
        +---- evaluate_budget_policy
        |
        +---- LifecycleCapitalRequirement
        |
        v
TradeEconomicsTicket builder / prospective decision record
        |
        v
optional CloudPositionDossier context ID/hash
```

The generic compiled-candidate pipeline and the quantitative ticket builder are existing distinct
typed domains. They now accept the same canonical context interface; no lossy conversion between
their candidate models was introduced.

## Phase M behavior

When `phase_m_context` is supplied:

- loose policy/evidence arguments cannot be mixed with it;
- `analyze_trade` passes the exact context-owned policy, lifecycle, FX, FX-cost, and broker objects;
- enumeration and factory require context ID/hash as a pair and reject a missing lifecycle;
- the factory does not reconstruct FX from legacy `TradeRequest` fields;
- the ticket builder does not reconstruct FX cost from execution estimates or broker capital from
  unrelated margin estimates;
- ticket scenario, breakeven, target-arrival, and lifecycle-capital deadlines all use the context's
  configured lifecycle;
- candidate, report, ticket, and cloud dossier may carry the same context ID/hash.

When no Phase M context is supplied, existing historical/research behavior remains unchanged.

## Budget and lifecycle invariants

- target: €1,000;
- preferred lower bound: €800, SOFT;
- hard authorized ceiling: €1,500;
- AUTO loss and buying-power caps use the effective hard ceiling;
- no pressure exists to spend toward the target;
- mixed-expiry capital precedence remains broker buying power, then validated analytical lifecycle
  bound, then `UNKNOWN`;
- common-expiry payoff remains diagnostic-only for calendars and diagonals;
- lifecycle mismatch remains `MIXED_EXPIRY_LIFECYCLE_CONFIG_MISMATCH`.

## CLI and serialization

```bash
ttwo-options trade phase-m-context \
  --config configs/phase_m/v2/ttwo_prospective_budget.yaml \
  --json-out phase_m_context.json
```

With no runtime evidence, the CLI truthfully reports it as not provided and performs no provider
connection. `schemas/phase_m_decision_context.schema.json` is the stable strict serialization
contract.

## Safety boundary

Every affected prospective artifact remains read-only and preview-only:

```text
read_only=true
transmit=false
what_if=true
order_capability=forbidden
HOLDOUT=UNOPENED
OPRA=NOT_STARTED
```
