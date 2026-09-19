# Phase M — final Paper execution readiness

Date: 2026-09-19  
Branch: `codex/m-ibkr-paper-control-readonly`  
Starting and current commit: `f2bb94da2758d11256c02c18f53bde701041fffb`  
Scope: offline implementation, tests, local migrations and documentation only

## Outcome

```text
EXECUTION_REVALIDATION       = READY_OFFLINE
PAPER_ENTRY_CONTROL_PLANE    = READY_OFFLINE_LOCKED
PAPER_ADAPTER_CODE           = READY_OFFLINE_DISARMED
PAPER_RUNTIME_DEFAULT        = DISABLED
PAPER_REAL_ORDER_TEST        = NOT_RUN
LIVE_EXECUTION               = FORBIDDEN
HOLDOUT                      = UNOPENED
```

`READY_OFFLINE` is a software result. It does not prove an entitlement, permission, broker
setting, quote, tick, margin, commission, submission, callback, simulated fill or Live
executability. No IBKR connection, remote deployment, remote D1 migration, Paper order, order
modification, cancellation, Live account access or holdout opening occurred.

The new entry path is deliberately unable to dispatch in the current composition:
`main.py` constructs `DisabledGateway()`, the isolated Paper adapter defaults disarmed, and every
confirmed entry is stored with `dispatch_authorized=0`.

## Independent audit table

| Requirement | Current code after patch | Current official documentation / constraint | Contradiction found? | Fix / disposition | Evidence |
|---|---|---|---|---|---|
| Default runtime | Exactly one `DisabledGateway()` composition | Execution must remain separately authorized | No | Retained and statically verified | `main.py`, security gate |
| Opening boundary | Typed `PAPER_ENTRY` exists beside legacy close intents | Orders are explicit broker objects | Yes: bridge was close-only | Added strict entry authorization and separate D1 entry ledger | `contracts.py`, migration 0011 |
| Browser authority | Browser sends only persisted dossier/ticket IDs | Application must control the final order object | No | Worker re-reads immutable server-side evidence | `paper-entry.ts` |
| Application vs wire sides | `BUY_TO_OPEN`/`SELL_TO_OPEN` stay metadata; wire legs are `BUY`/`SELL` | IBKR combo legs use `BUY`/`SELL`; blindly setting `openClose` is inappropriate here | Yes in the original gap | Separated and cross-validated both meanings | `contracts.py`, `paper_gateway.py` |
| Immutable structure | Legs, expiries, ratios, quantity and structure hash cannot be repriced | Modification must retain order identity; a structural change is a new decision | No | Only whole-BAG limit may change | revalidation schema and bounded-reprice spec |
| Fresh market | Spot, all leg maps, IV, optional Greeks, BAG/synthetic quotes, times, liquidity, FX/rates/dividends captured | Market data type and subscription state can be degraded or unavailable | Yes: exact all-leg coverage was not initially enforced | Exact selected-conId coverage now fails closed | `execution_revalidation.py` |
| Full economics | Canonical engine is called for every initial/reprice ticket | Broker preview does not replace analytical economics | No | Economics are immutable ticket evidence | `ExecutionEconomicsSnapshot` |
| Greeks semantics | Same market forbids changed raw Greeks; market/time/IV change recomputes | User limit is not an input to raw contract Greeks | No | Golden tests cover both cases | `test_execution_revalidation.py` |
| Drift policy | Versioned nullable thresholds; no default investment threshold | No IBKR source can define project investment thresholds | No | Missing policy yields `REQUIRES_POLICY`; reprice needs review | `MaterialExecutionDriftPolicy` |
| IV/five-score drift | IV, all five scores and execution quality are explicit possible drift inputs | Project policy, not broker policy | Yes: absent from first draft | Added configurable fields without setting values | revalidation code/schema |
| Reanalysis | Material drift emits immutable rerun request and preserves original artifacts | A broker reprice cannot decide candidate dominance | No | Universe rerunner rejects history rewrite | revalidation service/tests |
| Hard blockers vs drift | Stale/incomplete evidence returns `BLOCKED` | No executable proposal may be based on stale data | Yes: material drift could previously mask a hard blocker | Hard blockers now take precedence | revalidation regression test |
| Paper provenance | Environment is `IBKR_PAPER_SIMULATOR`; fills are `PAPER_SIMULATED_FILL` | IBKR documents important Paper limitations | No | Exchange-validation wording prohibited | lifecycle model/migrations/UI |
| Contract qualification | Full identity, uniqueness, exchanges, order types and adjusted-contract flag | `ContractDetails` carries these fields; conId alone is insufficient | No | Every leg must match qualification evidence exactly | `paper_gateway.py` |
| Price increments | PriceIncrement bands, min size and size increments validated exactly | `minTick` may not describe every price band | No | No automatic rounding | `MarketRuleEvidence` |
| BAG submission | Exactly one BAG order; no leg-by-leg fallback | IBKR supports combo/BAG orders | No | Architecture matrix covers 12 structures | bridge tests |
| Whole BAG vs guarantee | Submission mode and broker guarantee mode are distinct | Smart-routed combo legs may execute separately depending on routing | Yes in common terminology risk | Unknown/non-guaranteed mode blocks | adapter/spec |
| Hours/timezone | Trading hours, liquid hours and time-zone evidence required | Contract details expose broker hours/timezone | No | First test limited to governed liquid window | preflight model/runbook |
| Market data permission | Live/fresh evidence required; delayed/frozen blocks | Subscription and competing sessions affect API data | No | Codes 354, 10089–10091, 10186, 10197 normalized | lifecycle classifier |
| Account permission | One `DU` account, TTWO, US-options and short-leg permission checks | Paper permissions reflect relevant account configuration | No | Non-DU/multiple-account/permission uncertainty blocks | adapter/tests |
| Read-Only API | Must be false only for an explicit Paper execution window | Read-Only API prevents order placement | No | Code never changes the broker setting | gateway/runbook |
| Reconnect setting | Maintain/resubmit must remain off | Broker setting can change resubmission behavior | No | Configuration drift blocks | gateway/runbook |
| Persistent session identity | Stable username hash/client ID and monotonic `nextValidId` required | Modification/recovery depends on same API ownership and IDs | No | Missing/mismatched identity blocks | gateway/journal |
| Preflight age/version | Bounded age plus exact git/config/kill-switch versions | Stale application evidence cannot authorize current placement | Yes: version matching was initially only recorded | Added execution-time comparisons | gateway/tests |
| Pacing | Counts, ticker capacity, warnings and retry deadline are evidence | IBKR enforces message/ticker limits | Yes: first draft only normalized errors | Active pacing/backoff state now blocks | preflight adapter/tests |
| What-if | Separate `whatIf=true`, `transmit=false` order shape | Some smart combos may not support what-if | Yes: initial validation created a circular dependency | Request skips only the not-yet-existing result; actual execution still requires it | adapter/tests |
| What-if fallback | Unsupported is never zero; fallback needs explicit authorization and version | Unsupported preview is not proof of zero margin/commission | No | Versioned Paper-only fallback field; default false | contracts/preflight spec |
| Funds/margin | Analytical capital/max loss and available funds required; confirmed broker margin must fit | Broker what-if is account specific | Yes: first draft did not compare returned margin with funds | Added fail-closed comparison | adapter/tests |
| TIF/precautions | First entry is `DAY`; IOC/FOK/GTC and reused close slippage fail; no precaution bypass | Order/TIF compatibility and broker precautions can reject | No | Flags fixed false; errors 109/111/163/164/201 retained | contracts/gateway/classifier |
| Lifecycle truth | Submission attempt, pending, working, partial, terminal and reconciliation states separate | Callbacks can repeat and do not imply acceptance merely from `placeOrder` | Yes: Cloudflare enum lacked transitions for new states | Transition table completed | `broker-lifecycle-store.ts` |
| Callback evidence | Open/order status/errors/executions/commissions/completed boundaries modeled | IBKR exposes distinct callbacks and broker identities | No | Raw status/hash plus canonical projection | `order_lifecycle.py`, migration 0010 |
| Error normalization | Required documented codes plus unknown category retained | Error text/codes must be interpreted from actual evidence | No | Original code/message evidence preserved and redacted | classifier/tests |
| Working no fill | `WORKING_NO_FILL_YET`, never automatic liquidity failure | Paper fill simulation differs from an exchange | No | Marketability remains a separate evidence-based diagnostic | no-fill spec/tests |
| Repricing | One fresh ticket and one human proposal; no modify/chasing loop | Modification ownership is constrained; Paper behavior is not Live proof | No | Broker modify primitive remains absent from runtime | bounded-reprice spec |
| Partial fill/recovery | execId idempotency, remaining quantity and unresolved recovery identity | Callback duplication and missing ACK are possible | No | Unknown truth blocks new claims/resend | journal/tests |
| Signed ticket ingestion | HMAC body hash, lineage and safety flags validated | Internal evidence still needs application integrity | Yes: duplicate ticket ID could previously be silently ignored | Conflicting ticket identity now rejects; exact duplicate is idempotent | `paper-entry.ts` |
| UI language | Locked, revalidation, working/no-fill, Paper fill and reconciliation labels exist | Paper is a simulator | No | Reason/evidence shown separately from fill | dashboard/app assets |
| Live/holdout | No Live path; holdout unopened | Separate future decisions | No | Security gate and docs retain prohibition | security gate/Phase 10 audit |

## Architecture delivered

```text
selected candidate + PLANNED dossier
  -> fresh market + canonical economics
  -> immutable ExecutionRevalidationTicket
  -> signed internal ingestion
  -> server-built immutable entry preview
  -> fresh human confirmation
  -> paper_entry_intent(dispatch_authorized=0)
  -> STOP in this patch

future operator-only window
  -> broker/session/contract/market-rule/data/account/what-if preflight
  -> disarmed isolated IbkrPaperExecutionGateway
  -> one whole BAG LMT DAY order
  -> callback normalization + append-only reconciliation
```

The research engine and read-only providers retain zero order capability. The Paper gateway is a
separate dependency-injected boundary and is not imported by the composition root. Its transport
contract is persistent, but wiring it to the locally installed official `ibapi` session remains an
explicit activation task; it is not silently simulated in production code.

## ExecutionRevalidationTicket

The immutable ticket contains:

- full analysis/candidate/selection/dossier lineage and previous ticket;
- original market and economics, current market and proposed execution economics;
- exact structure hash, legs, quantity and application/wire directions;
- spot, per-leg quotes/timestamps/IV/Greeks, BAG/synthetic prices, market-data type and freshness;
- FX, rates, dividends, OI, volume, sizes, trading/liquid hours and timezone;
- commission, slippage, FX cost, capital, buying power when available, max loss/profit,
  breakevens, expected PnL/return, probabilities, VaR/CVaR and return ratios;
- all requested Greeks, time projections, scenario hashes, liquidity diagnostics and exactly five
  scores;
- explicit deltas, configurable material-drift result, verdict, blockers and optional reanalysis.

The valid verdicts are `EXECUTABLE`, `EXECUTABLE_REPRICE_PROPOSAL`, `REVIEW_REQUIRED`,
`REANALYSIS_REQUIRED` and `BLOCKED`. Human confirmation is mandatory; automatic repricing and
Live execution are schema-level false invariants.

## Entry adapter and preflight

The adapter rejects an unarmed configuration, non-loopback host, Live port, non-`DU` account,
multiple accounts, non-TTWO command, stale ticket/preflight, version mismatch, changed contract,
unqualified/adjusted leg, invalid exchange/order type, invalid price or size band, non-live data,
stale BAG, unverified signed convention, market outside policy, missing permission, active pacing
warning/backoff, insufficient funds, budget/max-loss above EUR 1,500, incomplete what-if and
non-guaranteed/unknown combo mode.

It creates one parent BAG action (`BUY` debit, `SELL` credit), preserves each leg ratio and
`BUY`/`SELL` wire action, keeps precautions enabled and returns only
`BROKER_SUBMISSION_ATTEMPTED`. Broker acceptance requires later callback evidence.

## Lifecycle, errors and recovery

Canonical states include the complete requested sequence from `CREATED` through
`RECONCILIATION_REQUIRED`. Raw broker status always remains available. `orderId`, `permId` and
`execId` are distinct; `orderRef` remains the durable application identity. Duplicate callbacks
are idempotent, each execution is keyed by `execId`, and commission attaches to that execution.

The rejection classifier deterministically covers 100, 101, 103, 106, 107, 109, 110, 111, 116,
133, 134, 154, 160, 163, 164, 200–203, 312–315, 354, 355, 360, 10002, 10015,
10089–10091, 10186 and 10197. Code 201 uses message evidence when a narrower category is supported;
otherwise `UNKNOWN_BROKER_REJECTION` remains valid.

On restart, an unresolved attempted dispatch is reconciled before another claim. Missing ACK does
not authorize retransmission. A state that cannot be proved becomes `AMBIGUOUS` /
`RECONCILIATION_REQUIRED`.

## Additive migrations

Migrations 0001–0009 were not edited.

- `0010_order_lifecycle_readiness.sql` adds canonical/latest state, lifecycle events, errors,
  executions, commissions, immutable market snapshots and reprice proposals.
- `0011_final_paper_entry_readiness.sql` adds immutable drift policies, revalidation tickets,
  previews, confirmations, operator attestations, locked entry intents, what-if evidence,
  lifecycle events, Paper-simulated executions and commissions.

Clean apply and upgrade from 0001–0009 both report `integrity_check=ok`, zero foreign-key
violations and eight `paper_entry_*` tables.

## Contradictions and defects found during final audit

All active contradictions found were fixed:

1. the what-if request required an already confirmed what-if result;
2. revalidation could accept maps that did not cover exactly every selected leg;
3. material drift could take precedence over stale/incomplete hard blockers;
4. IV regime/five-score drift was described but absent from the policy model;
5. the ticket held only the original market hash, not the original market snapshot;
6. Cloudflare declared new lifecycle states without defining their projection transitions;
7. a repeated signed ticket ID with different bytes could be silently ignored;
8. git/config equality, preflight age and pacing/backoff were recorded but not enforced at the
   final adapter boundary;
9. a confirmed broker what-if margin was not compared with available Paper funds;
10. active documentation blurred the legacy close flow with the new locked entry flow.

Frozen historical evidence was not rewritten.

## Historical approximately EUR 50 test

Repository code, reports, specs, committed audit material and test artifacts contain no attributable
IBKR `openOrder`, `orderStatus`, error, API message log, transmit evidence, rejection, cancellation
or fill for that attempt.

```text
HISTORICAL_50_EUR_TEST_ROOT_CAUSE = UNRESOLVED_NO_BROKER_EVIDENCE
```

Unranked hypotheses only: order never transmitted, Read-Only API, order precaution, invalid
contract/BAG, invalid tick, Paper-simulator limitation, missing market-data or trading permission,
competing session, price too far from market, or a valid working order that did not fill.

## Validation evidence

- Root Ruff: pass.
- Root mypy: pass, 201 source files.
- Root pytest: **460 passed**, one third-party `websockets.legacy` deprecation warning.
- Bridge Ruff: pass.
- Bridge pytest: **107 passed**.
- Cloudflare clean `npm ci`: 86 packages audited, zero vulnerabilities.
- Cloudflare check: typecheck pass, safety scan pass, **74 passed across 8 test files**.
- Runtime npm audit: zero vulnerabilities.
- Wrangler deploy dry-run: pass; 322.68 KiB upload / 74.93 KiB gzip; no deployment.
- Offline schemas: **45 verified**.
- Offline artifact validation, research registry, Phase 10 audit, Phase 11 gate: pass.
- Security gate: pass; 179 research files, 2 market-provider files and 5 telemetry files scanned;
  default gateway disabled, isolated Paper adapter offline-ready/disarmed, Live forbidden.
- Python dependency check: pass.
- D1 clean and upgrade migration paths: pass, integrity OK, zero FK violations.
- Git whitespace check: pass.

## NOT_PROVEN_OFFLINE / remaining execution blockers

These facts require the later controlled IBKR Paper observation and remain blockers:

1. actual OPRA entitlement, contractual usage/storage rights and real-time market-data type;
2. actual US-options and short-option permissions for the selected `DU` account;
3. actual contract identities, deliverables and adjusted-contract status at test time;
4. actual BAG bid/ask, signed price convention and `reqMarketRule` increment/size behavior;
5. actual Paper combo guarantee/routing behavior and simulator fill behavior;
6. actual smart-combo what-if support, margin, buying power, commissions and precautions;
7. actual API callback order/duplication, session competition, pacing and reconnect behavior;
8. recovery against actual open/completed orders and recent executions;
9. concrete official persistent `ibapi` transport wiring and operator-only composition;
10. an approved versioned material-drift policy; without it repricing remains review-only;
11. the separate operator attestation/one-intent dispatch authorization step;
12. any shadow/Paper campaign, untouched holdout or Live executability evidence.

## Files changed

Cloudflare and D1:

- `cloudflare/migrations/0010_order_lifecycle_readiness.sql`
- `cloudflare/migrations/0011_final_paper_entry_readiness.sql`
- `cloudflare/src/broker-control.ts`
- `cloudflare/src/broker-lifecycle-store.ts`
- `cloudflare/src/broker-lifecycle.ts`
- `cloudflare/src/index.ts`
- `cloudflare/src/paper-entry.ts`
- `cloudflare/public/app.txt`
- `cloudflare/public/dashboard.txt`
- `cloudflare/public/styles.txt`
- `cloudflare/scripts/safety-scan.mjs`
- `cloudflare/test/broker-control.test.ts`

Research/revalidation and schemas:

- `src/take_two_options/execution_revalidation.py`
- `src/take_two_options/intelligence/execution.py`
- `scripts/export_offline_schemas.py`
- `schemas/execution_revalidation_ticket.schema.json`
- `tests/test_execution_revalidation.py`
- `tests/test_offline_artifacts_v11.py`
- `tests/test_security_boundaries.py`

Bridge:

- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/contracts.py`
- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/gateway.py`
- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/journal.py`
- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/order_lifecycle.py`
- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/paper_gateway.py`
- `services/ibkr-paper-bridge/src/ttwo_ibkr_bridge/runtime.py`
- `services/ibkr-paper-bridge/tests/test_bridge.py`
- `services/ibkr-paper-bridge/tests/test_order_lifecycle.py`
- `services/ibkr-paper-bridge/tests/test_paper_gateway.py`
- `services/ibkr-paper-bridge/README.md`

Documentation and reports:

- `docs/IBKR_OPRA_ROADMAP.md`
- `docs/PAPER_TRADING_PLAN.md`
- `docs/SECURITY.md`
- `docs/cloudflare/ARCHITECTURE.md`
- `docs/cloudflare/SECURITY.md`
- `docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md`
- `docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md`
- `docs/specs/IBKR_BOUNDED_REPRICING.md`
- `docs/specs/IBKR_EXECUTION_PREFLIGHT.md`
- `docs/specs/IBKR_EXECUTION_REVALIDATION.md`
- `docs/specs/IBKR_NO_FILL_DIAGNOSTICS.md`
- `docs/specs/IBKR_ORDER_LIFECYCLE.md`
- `docs/specs/IBKR_PAPER_ENTRY_EXECUTION.md`
- `docs/specs/IBKR_PAPER_SIMULATOR_LIMITATIONS.md`
- `reports/PHASE_M_ORDER_LIFECYCLE_READINESS.md`
- `reports/PHASE_M_ORDER_LIFECYCLE_READINESS.json`
- `reports/PHASE_M_FINAL_PAPER_EXECUTION_READINESS.md`
- `reports/PHASE_M_FINAL_PAPER_EXECUTION_READINESS.json`

## Primary official sources

- [IBKR Paper Trading Account limitations](https://ibkrcampus.com/campus/glossary-terms/paper-trading-account/)
- [Installing and configuring TWS for the API](https://ibkrcampus.com/campus/trading-lessons/installing-configuring-tws-for-the-api/)
- [TWS API connection parameters](https://ibkrcampus.com/docs/excel/rtd/connection-parameters)
- [API settings configuration](https://ibkrcampus.com/docs/tws-api/protobuf/api-settings-config)
- [Python complex/BAG orders](https://ibkrcampus.com/campus/trading-lessons/python-complex-orders/)
- [Python placing orders and callbacks](https://ibkrcampus.com/campus/trading-lessons/python-placing-orders/)
- [Defining contracts](https://ibkrcampus.com/campus/trading-lessons/defining-contracts-in-the-tws-api/)
- [Trading contract rules](https://ibkrcampus.com/docs/web-api/api-reference/trading/trading-contracts/get-contract-rules)
- [Market-data subscriptions introduction](https://ibkrcampus.com/docs/general/market-data-subscriptions/introduction)
- [Market-data availability](https://ibkrcampus.com/docs/web-api/v1/endpoints/market-data/market-data-availability)
- [Order-status reference](https://ibkrcampus.com/docs/tws-api/protobuf/order-status)
- [Modify-order reference](https://ibkrcampus.com/docs/web-api/v1/endpoints/orders/modify-order)
- [TWS API introduction](https://ibkrcampus.com/docs/tws-api/doc/introduction)
- [Official TWS API message codes (legacy reference)](https://interactivebrokers.github.io/tws-api/message_codes.html)

