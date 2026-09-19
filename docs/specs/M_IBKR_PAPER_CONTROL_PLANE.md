# Phase M — isolated IBKR paper control plane

Status: **Paper entry adapter ready offline and disarmed; default runtime disabled**
Decision owner: project owner
Decision date: 2026-08-25

## Validated objective

The user approved an Oracle Cloud Ampere A1 VM running IB Gateway and an isolated bridge so a
local Mac/VS Code session is not required. The target outcome is:

- observe the paper position and its net liquidation P&L after estimated or actual fees;
- warn before a configured signed liquidation-PnL threshold;
- queue a whole-combo exit automatically at the configured liquidation-PnL threshold;
- allow a manual close from a fresh preview followed by one sensitive confirmation;
- install a broker-native protective order automatically after a paper entry;
- recover order and fill state after a process, VM, network, or personal-computer interruption.

This approval applies to **paper trading preparation only**. The current patch models opening
orders but does not authorize or run one. It is not approval for a live account,
commercial/multi-tenant execution, or bypassing IBKR warnings.

## Architecture

```text
Browser + Cloudflare Access
          |
          v
Cloudflare Worker ---- D1 immutable control/audit ledger
          ^
          | outbound HTTPS poll, Access service token + signed message
          |
Oracle A1 VM: bridge journal (SQLite/WAL) ---- IB Gateway paper socket on localhost:4002
                                                    |
                                                    v
                                              IBKR paper account (DU…)
```

There is no inbound broker port. The bridge polls Cloudflare; Cloudflare never opens a connection
to IB Gateway. The browser never receives a broker credential. The research engine under
`src/take_two_options` remains read-only and retains its package-wide execution prohibition.

## Implemented foundation

Migrations `0007_ibkr_paper_control.sql`, `0009_fix_paper_exit_pnl_semantics.sql`,
`0010_order_lifecycle_readiness.sql` and `0011_final_paper_entry_readiness.sql` create:

- fail-closed system state: `broker_mode=DISABLED`, kill switch engaged, bridge health unknown;
- signed liquidation-PnL warning/exit thresholds, a slippage ceiling, and a quote-age ceiling;
- idempotent paper intents with immutable command economics;
- append-only broker events, heartbeat history, and anti-replay nonces;
- a claim lease. An expired claim becomes `AMBIGUOUS`; it is never automatically redispatched.
- a typed broker lifecycle projection plus append-only raw/canonical evidence, errors, executions,
  commissions, immutable submission snapshots and preview-only reprice proposals.
- immutable revalidation tickets, entry previews/confirmations, operator attestations, Paper-entry
  intents, what-if evidence, lifecycle events, simulated executions and commissions.

The Worker implements:

- `GET /api/broker/status`;
- `POST /api/broker/control` and `POST /api/broker/exit-policy`, protected by Cloudflare Access,
  CSRF, recent authentication, and the existing action password;
- the legacy two-step close flow: create preview, then confirm; confirmation queues an idempotent
  close intent only when the paper bridge is healthy and every close gate passes;
- a separate selected-candidate Paper-entry preview/confirmation flow that always persists the
  entry with `dispatch_authorized=0`; browser confirmation is not dispatch authority;
- automatic signed liquidation-PnL evaluation by the Durable Object monitor;
- signed internal heartbeat, claim, and event routes with a 60-second clock window and nonce
  replay defense;
- SAFE MODE engaging the broker kill switch and blocking every unclaimed ready intent;
- a separate `POST /internal/broker/telemetry` machine route with its own identity, HMAC secret,
  60-second timestamp window, nonce replay defense, strict exact-key schema and derived-total
  verification;
- an authenticated `GET /api/broker/telemetry` route and an always-visible read-only dashboard
  card whose state is `FRESH`, `STALE`, `OFFLINE`, or `NOT_CONFIGURED`;
- a latest-only D1 telemetry projection containing no broker account identifier and always reporting
  `execution_enabled=false`.

The isolated service under `services/ibkr-paper-bridge` implements:

- strict paper-only command validation, including `DU` account guard, legacy close legs and
  governed `PAPER_ENTRY` open legs;
- an outbound Cloudflare client using both an Access service token and application HMAC;
- a local SQLite WAL journal, durable outbox, immutable-command hash, and restart recovery hook;
- a non-root, read-only Docker service with no published ports;
- a separate official-API telemetry adapter restricted to loopback, paper port `4002`, one `DU`
  account and symbol `TTWO`; it returns redacted positions, per-contract quotes and broker-reported
  P&L while preserving missing values as missing;
- a default `DisabledGateway` and a separate `IbkrPaperExecutionGateway` that is disarmed unless
  injected by a future operator-only composition root;
- pure offline normalizers for future `openOrder`, `orderStatus`, `error`, `execDetails`,
  `commissionReport` and callback-boundary evidence, without any broker mutation method;
- explicit `transmit=false` handling that records `LOCAL_NOT_TRANSMITTED` without invoking the
  gateway, and restart identities based on `orderRef`, `orderId`, `permId` and `execId`;
- debit/credit marketability diagnostics and bounded-reprice previews that fail closed on stale,
  delayed, absent or sign-unverified combo data;
- a separate persistent telemetry runtime and hardened systemd unit that can only publish snapshots.

The telemetry adapter is not imported by the bridge runtime and exposes no place, modify, cancel,
exercise, or global-cancel operation. Its live P&L payload is explicitly marked as not yet
reconciled with final execution commissions and fees.

## Not implemented yet

The project-owned adapter was installed from commit `c84e47964acf63f5c9617126dcc899cf0a0fdff7`
on the logged-in Oracle paper VM and completed a redacted `PAPER_READ_ONLY` snapshot on 2026-08-25.
The snapshot proved the handshake, server time, single-paper-account guard, TTWO symbol restriction,
and redaction boundary. The account had zero open TTWO positions, so per-leg quotes and position P&L
remain unvalidated against a real paper position.

Signed read-only publication is implemented and tested. Production activation still requires a
dedicated Cloudflare Access service token entered privately on the VM. The following remain blocked:

1. group IBKR option legs into the governed Take Two position without guessing from symbols alone;
2. wiring real broker collection into the implemented combo-quote, contract, pacing and
   market-rule validation immediately before dispatch;
3. observing BAG limit/tick behavior and the first Paper submission against real broker evidence;
4. wiring the existing offline Paper gateway to the official persistent API transport;
5. proving recovery against real open orders and recent executions;
6. actual-fill/commission reconciliation into the user-visible net P&L;
7. broker-native protective-order creation after a verified paper entry;
8. fault-injection, disconnect, partial-fill, and weekly reauthentication tests.

Until those items pass paper tests, `DisabledGateway` reports unhealthy and the Worker kill switch
stays engaged. In particular, no new `paper_entry_intents` row is dispatch-authorized or claimable;
the older close-intent control path remains a separate, disabled runtime.

The complete offline model and its evidence rules are documented in
[`IBKR_ORDER_LIFECYCLE.md`](IBKR_ORDER_LIFECYCLE.md),
[`IBKR_NO_FILL_DIAGNOSTICS.md`](IBKR_NO_FILL_DIAGNOSTICS.md) and
[`IBKR_BOUNDED_REPRICING.md`](IBKR_BOUNDED_REPRICING.md).

## State and idempotency rules

```text
CREATED -> READY -> CLAIMED -> PENDING_SUBMIT -> PRE_SUBMITTED -> WORKING
                                                            \-> PARTIALLY_FILLED -> FILLED
                                                            \-> CANCELLED | REJECTED
                                                            \-> RECONCILIATION_REQUIRED
```

- An intent identity and command JSON never change.
- A manual preview has one `manual-close:<preview_id>` idempotency key.
- An automatic liquidation-PnL policy produces at most one intent per policy revision.
- Credit and debit positions use the same trigger metric: entry cash flow plus signed estimated
  close cash flow after required exit costs. A negative close cash flow alone never triggers an
  exit.
- Migration `0009` leaves legacy positive-threshold rows disabled with null V2 thresholds until
  an operator explicitly configures signed PnL values.
- `AMBIGUOUS` means reconcile with IBKR by `orderRef`/`permId`; never guess and never resend.
- Every partial execution uses its IBKR `execId`; commission/fees attach to that execution.
- `WORKING_NO_FILL_YET` is non-terminal and never becomes `NO_LIQUIDITY` without separate,
  explicitly defined market evidence.
- `transmit=true` is not alone proof of broker acceptance; raw status and callback evidence remain
  visible alongside the canonical projection.
- D1 is the application control ledger. IBKR is the final truth for orders, executions, and fees.

## Mandatory activation gates

Paper dispatch may only be enabled after all are true:

- Oracle A1 VM is stable and backed up;
- IB Gateway ARM64 is installed from IBKR, logged into paper, and bound to localhost only;
- the connected account begins with `DU` and the live socket ports are explicitly rejected;
- contract `conId`s, combo direction, quantity, multiplier, minimum tick, and signed credit/debit
  price are reconciled against IBKR;
- bounded limit behavior is tested for debit and credit closures;
- partial fills, rejection, network loss before/after submission, restart, and duplicate callback
  tests pass;
- displayed net P&L waits for executions **and** commissions/fees;
- broker-native protection is proven to survive bridge, VM, and network loss;
- SAFE MODE and both kill switches are exercised in paper.

## Primary sources checked

- [IB Gateway Linux ARM64 download](https://portal.interactivebrokers.com/en/trading/ibgateway-latest.php)
- [IBKR API configuration and paper ports](https://www.interactivebrokers.com/campus/trading-lessons/installing-configuring-tws-for-the-api/)
- [IBKR complex/BAG order example](https://www.interactivebrokers.com/campus/trading-lessons/python-complex-orders/)
- [IBKR order-placement callbacks and precautions](https://www.interactivebrokers.com/docs/tws-api/doc/orders/place-order/order-placement-considerations)
- [IBKR execution identity](https://www.interactivebrokers.com/docs/tws-api/ref/execution)
- [IBKR commission and fees reports](https://www.interactivebrokers.com/docs/tws-api/ref/commission-and-fees-report)
- [OCI Always Free resources and reclamation risk](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
