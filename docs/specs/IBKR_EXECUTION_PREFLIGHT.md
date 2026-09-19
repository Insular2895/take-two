# IBKR execution preflight

Status: implemented as deterministic offline contracts; broker facts remain
`NOT_PROVEN_OFFLINE` until the operator-authorized Paper window.

## Required sequence

The gateway evaluates the following evidence immediately before the order primitive. The first
failure blocks; nothing is silently rounded, substituted or downgraded.

1. **Runtime boundary** — isolated adapter explicitly armed, default runtime still disabled.
2. **Network/session** — loopback; Paper port `4002` (Gateway) or `7497` (TWS); stable positive
   client ID; gateway, IB server and market-data farm separately connected; `nextValidId`
   established; git/config versions identical to the execution ticket.
3. **Account** — exactly one account, prefix `DU`; TTWO US-options and short-option permissions
   proven when relevant.
4. **Settings** — Read-Only explicitly and temporarily disabled by the operator for this Paper
   window; maintain/resubmit after reconnect off; precautions and percentage constraints not
   bypassed; API message log enabled at Detail; no competing login attested.
5. **Lineage** — current PLANNED dossier, approved candidate, fresh ticket, immutable preview,
   confirmation hashes and current kill-switch version all agree.
6. **Contract qualification** — each leg matches conId, localSymbol, tradingClass, expiry, strike,
   right, multiplier, currency and exchange; one unique match; validExchanges/orderTypes checked;
   adjusted/non-standard contracts blocked for review.
7. **BAG** — all legs belong to the governed structure; integer ratios; compatible currency;
   whole BAG; fresh bid/ask; signed price convention verified; guaranteed mode proven.
8. **Market rules** — `marketRuleIds` and `reqMarketRule` PriceIncrement band determine the tick at
   the proposed price; minSize, sizeIncrement and suggestedSizeIncrement are recorded.
9. **Hours/data** — `tradingHours`, `liquidHours` and `timeZoneId` are broker evidence; live TTWO,
   every leg and BAG input is fresh; delayed/frozen/degraded data blocks.
10. **Pacing** — outgoing-message count, active ticker lines, broker limit, pacing warning and
    retry-not-before are captured. An active warning, exceeded ticker capacity or backoff window
    blocks instead of retrying in a tight loop.
11. **Economics/account** — capital and max loss are each at most EUR 1,500 and the analysis
    ceiling; available funds are known and sufficient; commissions are known; broker what-if is
    confirmed, or a separately confirmed conservative Paper-only fallback exists.

## Contract and market-rule algorithm

`ContractDetails.minTick` is recorded but is not treated as the universal increment. The relevant
PriceIncrement band is the greatest `lowEdge <= proposed_price`. Price must be an exact multiple
of that increment and quantity must satisfy the applicable size rule. Invalid price/size returns
the normalized equivalents of IBKR 110/355. No customer-disadvantageous rounding is automatic.
A future rounding proposal must show the original value, allowed increment, proposed rounded
value and economic delta, then create a new revalidation ticket.

Official references:

- [Defining contracts in the TWS API](https://ibkrcampus.com/campus/trading-lessons/defining-contracts-in-the-tws-api/)
- [Contract rules endpoint](https://ibkrcampus.com/docs/web-api/api-reference/trading/trading-contracts/get-contract-rules)

## Session and order IDs

The execution transport is persistent. `nextValidId` seeds a locked monotonic allocator; no
historic ID is reused. `orderRef` is the durable application identity; `orderId`, `permId` and
`execId` are broker identities. A reprice requires the same username hash, client ID, order ID,
candidate, BAG and remaining quantity. Failure to prove ownership yields
`REPRICE_BLOCKED_SESSION_MISMATCH`.

On restart, the journal reconciles open orders, completed orders and recent executions by those
identities. Missing ACK never authorizes a resend. Uncertain truth is `AMBIGUOUS` plus
`RECONCILIATION_REQUIRED`.

Official reference: [IBKR Campus — placing orders](https://ibkrcampus.com/campus/trading-lessons/python-placing-orders/).

## What-if

Statuses are explicit:

- `BROKER_WHAT_IF_CONFIRMED`;
- `BROKER_WHAT_IF_UNSUPPORTED`;
- `BROKER_WHAT_IF_INCOMPLETE`;
- `BROKER_WHAT_IF_FAILED`.

Unsupported is not zero margin or zero commission. A Paper-only fallback needs analytical
max-loss, available Paper funds, explicit confirmation and a named versioned fallback policy; it
grants no future Live permission. A confirmed broker margin above available Paper funds blocks.

## Operator attestations still required

All of the following are `NOT_PROVEN_OFFLINE`: actual OPRA entitlement, US-options permission,
current BAG tick, signed BAG convention, Paper what-if behavior, commissions, margin, precaution
behavior, session competition and reconnect behavior.
