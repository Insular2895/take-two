# Phase M — isolated IBKR paper control plane

Status: **read-only IBKR adapter implemented locally; execution adapter disabled**
Decision owner: project owner
Decision date: 2026-08-25

## Validated objective

The user approved an Oracle Cloud Ampere A1 VM running IB Gateway and an isolated bridge so a
local Mac/VS Code session is not required. The target outcome is:

- observe the paper position and its net liquidation P&L after estimated or actual fees;
- warn before a configured capital floor;
- queue a whole-combo exit automatically at the configured floor;
- allow a manual close from a fresh preview followed by one sensitive confirmation;
- install a broker-native protective order automatically after a paper entry;
- recover order and fill state after a process, VM, network, or personal-computer interruption.

This approval applies to **paper trading only**. It is not approval for a live account, opening
orders, commercial/multi-tenant execution, or bypassing IBKR warnings.

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

Migration `0007_ibkr_paper_control.sql` creates:

- fail-closed system state: `broker_mode=DISABLED`, kill switch engaged, bridge health unknown;
- a per-position warning floor, automatic-exit floor, slippage ceiling, and quote-age ceiling;
- idempotent paper intents with immutable command economics;
- append-only broker events, heartbeat history, and anti-replay nonces;
- a claim lease. An expired claim becomes `AMBIGUOUS`; it is never automatically redispatched.

The Worker implements:

- `GET /api/broker/status`;
- `POST /api/broker/control` and `POST /api/broker/exit-policy`, protected by Cloudflare Access,
  CSRF, recent authentication, and the existing action password;
- a two-step manual flow: create preview, then confirm; confirmation queues an idempotent paper
  intent only when the paper bridge is healthy and every gate passes;
- automatic floor evaluation by the Durable Object monitor;
- signed internal heartbeat, claim, and event routes with a 60-second clock window and nonce
  replay defense;
- SAFE MODE engaging the broker kill switch and blocking every unclaimed ready intent.

The isolated service under `services/ibkr-paper-bridge` implements:

- strict paper-only command validation, including `DU` account guard and close-only combo legs;
- an outbound Cloudflare client using both an Access service token and application HMAC;
- a local SQLite WAL journal, durable outbox, immutable-command hash, and restart recovery hook;
- a non-root, read-only Docker service with no published ports;
- a separate official-API telemetry adapter restricted to loopback, paper port `4002`, one `DU`
  account and symbol `TTWO`; it returns redacted positions, per-contract quotes and broker-reported
  P&L while preserving missing values as missing;
- a deliberately disabled gateway adapter.

The telemetry adapter is not imported by the bridge runtime and exposes no place, modify, cancel,
exercise, or global-cancel operation. Its live P&L payload is explicitly marked as not yet
reconciled with final execution commissions and fees.

## Not implemented yet

The following remain blocked pending project-adapter validation on the logged-in Oracle paper VM:

1. run the project-owned read-only adapter on the VM and publish its redacted telemetry through a
   signed, schema-validated Cloudflare route;
2. group IBKR option legs into the governed Take Two position without guessing from symbols alone;
3. combo quote refresh and tick-size validation immediately before dispatch;
4. bounded BAG limit construction and paper submission;
5. `openOrder`, `orderStatus`, `execDetails`, error, and commission callback normalization;
6. recovery using `orderRef`, `permId`, `execId`, open orders, and recent executions;
7. actual-fill/commission reconciliation into the user-visible net P&L;
8. broker-native protective-order creation after a verified paper entry;
9. fault-injection, disconnect, partial-fill, and weekly reauthentication tests.

Until those items pass paper tests, `DisabledGateway` reports unhealthy, the Worker kill switch
stays engaged, and no bridge command can be claimed.

## State and idempotency rules

```text
READY -> CLAIMED -> BROKER_ACKNOWLEDGED -> PARTIAL_FILL -> FILLED
                  \-> REJECTED | CANCELLED | EXPIRED | AMBIGUOUS
```

- An intent identity and command JSON never change.
- A manual preview has one `manual-close:<preview_id>` idempotency key.
- An automatic floor policy produces at most one intent per policy revision.
- `AMBIGUOUS` means reconcile with IBKR by `orderRef`/`permId`; never guess and never resend.
- Every partial execution uses its IBKR `execId`; commission/fees attach to that execution.
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
