# Phase M — order lifecycle, no-fill diagnostics and bounded repricing readiness

Date: 2026-09-18  
Branch: `codex/m-ibkr-paper-control-readonly`  
Starting commit: `f2bb94da2758d11256c02c18f53bde701041fffb`  
Scope: offline code, tests, local D1 migrations and documentation only

## Result

```text
ORDER_LIFECYCLE_MODEL = READY_OFFLINE
NO_FILL_DIAGNOSTICS = READY_OFFLINE
REPRICE_PROPOSAL = READY_OFFLINE
ACTUAL_PAPER_GATEWAY = DISABLED
PAPER_ORDER_TRANSMISSION = DISABLED
LIVE_EXECUTION = FORBIDDEN
HOLDOUT = UNOPENED
```

`READY_OFFLINE` means that deterministic models, storage, UI projection and tests exist. It does
not mean that a real IBKR callback, BAG quote, OPRA entitlement, Paper order or fill was observed.

## Delivered software

### Broker-specific evidence normalization

The bridge now has typed evidence for `openOrder`, `orderStatus`, `error`, `execDetails`,
`commissionReport` and callback boundaries. It preserves raw IBKR status and produces a separate
canonical state. Raw evidence is hashed; account identifiers and credential-like material are
redacted from structured evidence.

The deterministic lifecycle includes `LOCAL_NOT_TRANSMITTED`, `PENDING_SUBMIT`, `PRE_SUBMITTED`,
`WORKING`, `PARTIALLY_FILLED`, `FILLED`, cancellation states, `REJECTED`, `INACTIVE`, `AMBIGUOUS`
and `RECONCILIATION_REQUIRED`. `WORKING` with zero fill and a positive remainder derives
`WORKING_NO_FILL_YET`, a non-terminal condition.

### Additive D1 evidence model

Migration `0010_order_lifecycle_readiness.sql` adds:

- `broker_order_state_latest`;
- `broker_order_lifecycle_events`;
- `broker_order_errors`;
- `broker_executions`;
- `broker_commissions`;
- `broker_market_snapshots`;
- `broker_reprice_proposals`.

Lifecycle, error, execution and commission rows are append-only. Market snapshots and reprice
proposals are immutable. `broker_event_key`, `permId` and `execId` enforce identity/idempotency.
Migrations 0001–0009 were not edited.

Each future fill is joined to its immutable submission snapshot through `intent_id`. Execution
rows also accept optional near-fill combo bid/ask, execution delay, slippage versus the decision
midpoint, slippage versus the executable quote and partial-fill sequence. Missing real evidence
remains null, and none of these observations feeds historical frozen scores automatically.

### Worker and interface

The signed bridge event endpoint validates and persists canonical evidence, while retaining the
existing coarse intent status for compatibility. The authenticated broker status response exposes
the latest exact state, timeline, errors, fills, commissions, submission snapshot and reprice
previews. Full evidence JSON and advanced rejection JSON are not browser-visible.

The POSITION / EXECUTION panel now displays precise status, raw broker status, transmission,
filled/remaining quantities, TIF, age, limit, combo snapshot, cancellation/rejection, evidence
timeline and preview-only repricing. Working orders are not rendered as generic red failures.

### Recovery

The local SQLite/WAL journal persists `orderRef`, `orderId`, `permId` and `execId`. A restart first
replays its outbox and asks the future gateway to reconcile unresolved identities. It does not
claim a new command while prior work remains unresolved. Unknown session state becomes
`RECONCILIATION_REQUIRED`, not a duplicate submission.

## Rejection and cancellation taxonomy

Rejections preserve the broker code and a redacted message. Categories are account permission,
buying power, market-data permission, order precaution, limit outside allowed range, invalid
contract/combo, unsupported type, exchange restriction, account/session state, duplicate order and
unknown rejection.

Cancellation cause is separate: user, API, TWS, broker, exchange, TIF expiry, precaution, invalid
order, price protection, session loss or unknown. A specific cause is assigned only when supported
by evidence.

No IBKR precaution is bypassed. Code 109/precaution evidence is retained as an order precaution;
it is never renamed `NO_LIQUIDITY`.

## No-fill design

The system first asks whether the order was transmitted, accepted, rejected, cancelled, held,
partially filled or unresolved. Marketability is calculated only with a verified BAG convention,
live and fresh combo/leg/underlying data, and fresh FX when required.

Debit and credit use inverse economics: a higher maximum debit is more aggressive, while a lower
minimum credit is more aggressive. Even a limit marketable at the observed quote does not guarantee
a fill. Stale/delayed/missing data or an unverified convention returns an explicit unknown result.

## Bounded reprice design

`RepriceProposal` may change only the combo limit. It verifies the immutable order-shape hash,
direction, maximum debit/minimum credit, budget headroom, max-loss headroom, quote availability,
freshness and price convention. Outcomes are either human-preview-ready or a precise blocked/
unavailable status.

Every persisted proposal has `automatic_action_allowed=0`. No `modifyOrder`, chasing loop, TIF
change, market-order conversion or leg-by-leg fallback exists.

## Historical approximately €50 test

Repository, reports and documented traces were searched for broker evidence. No attributable
`orderStatus`, `openOrder`, IBKR error, TWS/API log, transmit state, warning or broker
cancellation/rejection was found.

```text
historical_test = ~50 EUR demo test
root_cause = UNRESOLVED_NO_BROKER_EVIDENCE
```

Possible explanations remain hypotheses only: `TRANSMIT_FALSE`, `API/TWS_PRECAUTION`,
`MISSING_MARKET_DATA`, `PRICE_PRECAUTION`, `INVALID/UNVERIFIED_ORDER_STATE`.

## Validation evidence

- Root Python: `450 passed`; one third-party `websockets.legacy` deprecation warning.
- Ruff: pass; mypy strict: pass across 200 source files.
- Offline schemas: 44 verified.
- Offline artefacts, research registry and deterministic Phase 10/11 audits: pass.
- Security gate: pass; research order capability forbidden, provider/telemetry read-only,
  `DisabledGateway` still active, live execution forbidden.
- Python dependency check: pass.
- IBKR bridge: Ruff pass; `44 passed`.
- Cloudflare: clean `npm ci`, `72 passed` across 8 files, typecheck and safety scan pass.
- npm full install audit and runtime audit: zero vulnerabilities.
- Wrangler dry-run: pass; 299.18 KiB upload, 70.07 KiB gzip; no deployment performed.
- D1: all migrations through 0010 pass on a clean local database.
- D1: a local database migrated through 0009 upgrades independently with 0010.

## Safety-gate result

`DisabledGateway()` remains the runtime gateway. Commands require `transmit=false`; the runtime
records `LOCAL_NOT_TRANSMITTED` and does not call the gateway. No broker connection, Paper order,
modify, cancel, live account, remote migration, remote deployment or holdout access occurred.

The research five-score formulas, ranking, candidate generation, filters/sorting, heatmap,
historical OOS, Phase M budget semantics, debit/credit signed accounting and freshness semantics
were not changed.

## Remaining gates before actual Paper execution

1. confirm OPRA entitlement and the permitted use/storage policy;
2. explicitly authorize and complete real IBKR read-only validation;
3. observe the BAG signed-price convention and fresh combo behavior in TWS/IB Gateway;
4. reconcile contract `conId`s, ratios, action, multiplier, tick size and debit/credit convention;
5. implement the project-owned `IBKRPaperGateway` without changing the default disabled runtime;
6. validate order precautions and callback ordering against a `DU*` paper account;
7. test reject, cancellation, IOC/FOK, partial fill, commission, disconnect and restart cases;
8. prove recovery with open orders/recent executions and no duplicate submission;
9. complete a security review and receive explicit human approval for first Paper transmission.

## Primary references

- [IBKR order submission and statuses](https://interactivebrokers.github.io/tws-api/order_submission.html)
- [IBKR executions and commissions](https://interactivebrokers.github.io/tws-api/executions_commissions.html)
- [IBKR open orders](https://interactivebrokers.github.io/tws-api/open_orders.html)
- [IBKR error handling](https://interactivebrokers.github.io/tws-api/error_handling.html)
- [IBKR message codes](https://interactivebrokers.github.io/tws-api/message_codes.html)
- [IBKR automated considerations and precautions](https://interactivebrokers.github.io/tws-api/automated_considerations.html)
- [IBKR Campus order status values](https://ibkrcampus.com/docs/web-api/v1/endpoints/order-monitoring/order-status-value)
