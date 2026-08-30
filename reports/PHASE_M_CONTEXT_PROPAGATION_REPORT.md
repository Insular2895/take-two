# Phase M context propagation report

> Historical file note (2026-08-30): the file list below describes the Phase M implementation at
> that date. The former `src/take_two_options/engine.py` was later migrated into
> `src/take_two_options/decision/pipeline.py` and deleted during PRE-OPRA consolidation.

Date: 2026-08-24

## Initial finding

`CONFIRMED/PARTIAL`: candidate enumeration and factory already accepted the required objects, but
`analyze_trade` supplied only a loose budget policy plus reconstructed FX. The ticket builder used a
separate lifecycle source and could reconstruct missing runtime evidence. There was no canonical
context ID/hash spanning prospective decisions and cloud export.

## Exact integration changes

- Added immutable, strict `PhaseMDecisionContext`, deterministic config/context hashes, explicit
  source provenance, one builder, one loader helper, and a generated JSON Schema.
- Made `ProspectiveBudgetConfig.mixed_expiry_lifecycle` required.
- Added `phase_m_context` to `analyze_trade`, the deep ticket path, and `analyze_bundle` while
  preserving every context-free caller.
- Explicitly propagated policy, lifecycle, FX, FX execution cost, and broker capital through
  enumeration and candidate factory.
- Disabled Phase M reconstruction from legacy request FX, configured execution FX costs, and
  unrelated margin estimates.
- Added context ID/hash to prospective candidate/report/ticket records and optional cloud dossiers.
- Added the provider-free `trade phase-m-context` dry-run CLI.

## Propagation graph

```text
ProspectiveBudgetConfig
        +-- budget_policy
        +-- mixed_expiry_lifecycle
        v
PhaseMDecisionContext
        +-- FXRate
        +-- FXExecutionCost
        +-- BrokerCapitalContext
        v
analyze_trade
        v
enumerate_candidates
        v
build_candidate
        +-- evaluate_budget_policy
        +-- LifecycleCapitalRequirement
        v
TradeEconomicsTicket / prospective record
        v
optional CloudPositionDossier context ID/hash
```

There is no hidden lifecycle or evidence fallback in Phase M mode.

## Static/runtime separation

The YAML remains the sole source for budget policy, lifecycle and safety state. FX quotes, FX costs,
and broker buying power remain optional point-in-time runtime evidence and never mutate the YAML.
The context contains no credential fields.

## Lifecycle, FX, and capital results

- Buffer 3 gives 2027-08-17 for a 2027-08-20 first expiry across candidate, lifecycle capital,
  ticket, scenarios, breakeven clock, and target arrival.
- €1,497 converted entry plus €6 known FX cost gives €1,503 and blocks against the €1,500 ceiling.
- Unknown required FX cost remains null, research-visible, guarantee-unproven, and paper-ineligible.
- Same-currency evaluation requires no fake FX evidence and reports cost `NOT_APPLICABLE`.
- Validated €900 broker buying power becomes the mixed-expiry lifecycle source; absence returns
  `UNKNOWN` without inventing zero or combo margin.

## Files changed

Core and interfaces:

- `src/take_two_options/phase_m_context.py`
- `src/take_two_options/config/contracts.py`
- `src/take_two_options/decision/pipeline.py`
- `src/take_two_options/candidate_generation/enumerator.py`
- `src/take_two_options/candidate_generation/factory.py`
- `src/take_two_options/quantitative/trade_economics.py`
- `src/take_two_options/trade_economics_models.py`
- `src/take_two_options/knowledge/schemas.py`
- `src/take_two_options/engine.py`
- `src/take_two_options/cli.py`
- `src/take_two_options/cloud/contracts.py`
- `src/take_two_options/cloud/export_position.py`
- `cloudflare/src/types.ts`
- `cloudflare/src/domain.ts`

Schemas, tests, and documentation:

- `schemas/phase_m_decision_context.schema.json`
- `schemas/prospective_budget_config.schema.json`
- `schemas/trade_economics_ticket.schema.json`
- `schemas/cloud_position_dossier.schema.json`
- `scripts/export_offline_schemas.py`
- `tests/test_phase_m_context.py`
- `tests/test_offline_artifacts_v11.py`
- `docs/audits/PHASE_M_CONTEXT_PROPAGATION_PRE_PATCH.md`
- `docs/audits/PHASE_M_CONTEXT_PROPAGATION_POST_PATCH.md`
- `docs/specs/PHASE_M_GOVERNED_CONTEXT_PROPAGATION.md`
- `README.md`
- `CHANGELOG.md`
- this Markdown report and its JSON counterpart.

## Tests and compatibility

- Python: 357 passed, including full `analyze_trade -> enumerate_candidates -> build_candidate`
  coverage for known and unknown FX-cost cases.
- Ruff: passed.
- strict mypy: passed across 191 source files.
- schemas: 30 verified.
- offline artifacts, research registry, Phase 10 audit, and Phase 11 gate: passed.
- Cloudflare: 33 tests, TypeScript, safety scan, and Wrangler dry-run passed.
- Legacy calls without context remain valid.
- Historical artifacts and five-score hashes are unchanged.

## Historical hashes

| Artifact | SHA-256 status |
|---|---|
| M0 Greeks/carry report | unchanged |
| M0.1 correction report | unchanged |
| M0.2 budget report | unchanged |
| M0.2.1 semantics report | unchanged |
| pre-OPRA five scores | unchanged |
| M0 ticket golden fixture | unchanged |

## Safety and remaining dependencies

`read_only=true`, `transmit=false`, `what_if=true`, `order_capability=forbidden`,
`HOLDOUT=UNOPENED`, and `OPRA=NOT_STARTED` remain true. No paper run or provider connection was
started.

Remaining Phase M work is live **read-only** data integration followed by separately authorized
shadow/paper prospective validation. Real FX/FX-cost and broker-capital snapshots remain required
runtime evidence; they are not fabricated by this patch.

```text
PHASE_M_CONTEXT_PROPAGATION = COMPLETE
STATIC_POLICY_WIRING = COMPLETE
RUNTIME_EVIDENCE_WIRING = COMPLETE
MIXED_EXPIRY_CONTEXT = SINGLE_SOURCE_OF_TRUTH
FX_CONTEXT = EXPLICIT
BROKER_CAPITAL_CONTEXT = EXPLICIT
PRE_OPRA_LOGIC = FROZEN
HOLDOUT = UNOPENED
ORDER_TRANSMISSION = FORBIDDEN
```

Next: `PHASE M LIVE READ-ONLY DATA INTEGRATION + SHADOW/PAPER PROSPECTIVE VALIDATION`.
