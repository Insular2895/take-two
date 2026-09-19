# IBKR Paper entry execution

Status: `READY_OFFLINE_DISARMED` — 19 September 2026.

This specification explains the only permitted future opening path. It is a software readiness
result, not permission to trade. No IBKR connection or Paper order was used to validate it.

## Boundary

An opening command is created only from this immutable chain:

```text
completed analysis
  -> selected candidate
  -> immutable PLANNED dossier
  -> fresh ExecutionRevalidationTicket
  -> immutable Paper-entry preview
  -> fresh human confirmation
  -> operator/broker preflight (future controlled step)
  -> isolated IbkrPaperExecutionGateway
```

The browser supplies only persisted `dossier_id` and `ticket_id`. It cannot submit strikes,
expirations, conIds, ratios, sides, quantity, limit, or a replacement structure. Cloudflare
re-reads the selected candidate, dossier and ticket before creating a preview and again before
confirmation.

`paper_entry_intents` is deliberately separate from the legacy close-intent table: an unopened
`PLANNED` dossier is not a `position`, and pretending otherwise would corrupt the lifecycle.

## Application intent versus IBKR wire values

| Meaning | Application metadata | IBKR combo-leg wire action |
|---|---|---|
| Open a long option leg | `BUY_TO_OPEN` | `BUY` |
| Open a short option leg | `SELL_TO_OPEN` | `SELL` |

Open/close intent is never encoded by blindly setting `Order.openClose`. The application retains
that meaning and the isolated adapter sends only the documented `BUY`/`SELL` combo-leg action.
The parent BAG action is `BUY` for a debit and `SELL` for a credit.

## Immutable order shape

For one execution attempt these fields cannot change: ticker, candidate, dossier, conIds,
localSymbols, tradingClass, rights, strikes, expirations, multipliers, currencies, exchanges,
ratios, overall quantity and structure type. The only repriceable field is the whole-BAG LMT
price. A structural change requires reconciliation/cancellation, a new analysis, a new selection,
a new ticket and a new confirmation.

Supported shape tests cover long call, long put, bull call spread, bear put spread, call/put
butterflies, broken-wing butterfly, straddle, strangle, iron condor, calendar and diagonal. This
proves deterministic BAG construction, not identical margin treatment across structures.

## Whole BAG is not a guarantee claim

`combo_submission_mode=WHOLE_BAG` means the application sends one BAG order and never falls back
to independent option orders. It does not mean every IBKR route guarantees atomic leg execution.
`broker_combo_guarantee_mode` is therefore separate. The first controlled test accepts only
`GUARANTEED`; `UNKNOWN` and `NON_GUARANTEED` fail with
`BLOCKED_NON_GUARANTEED_COMBO`. The adapter never silently sets `NonGuaranteed=1`.

Official reference: [IBKR Campus — Python complex orders](https://ibkrcampus.com/campus/trading-lessons/python-complex-orders/).

## Activation layers

There are four independent facts:

1. the source adapter exists;
2. the adapter configuration is `armed_for_governed_paper_entry`;
3. the control-plane intent has an operator attestation and dispatch authorization;
4. the composition root actually uses that adapter.

At this checkpoint only item 1 is true. `main.py` still constructs exactly
`DisabledGateway()`. Confirmed entries are persisted with `dispatch_authorized=0`; they cannot be
claimed by the existing close-intent claimant. There is no generic `ALLOW_LIVE`,
`DISABLE_SAFETY` or `SKIP_PREFLIGHT` switch.

## Wire order

The adapter constructs exactly one `WireBagContract` with `security_type=BAG` and one
`WireLimitOrder` with:

- `order_type=LMT`, `time_in_force=DAY`;
- TTWO only, one `DU` account, loopback and Paper port only;
- `outside_regular_trading_hours=false`;
- `non_guaranteed=false`;
- `bypass_order_precautions=false`;
- `override_percentage_constraints=false`;
- stable client ID and durable `orderRef`;
- exact git/config match, bounded preflight age and clear pacing/backoff evidence;
- `transmit=true` only after every entry and broker preflight gate succeeds.

What-if uses a distinct order-shaped object with `what_if=true` and `transmit=false`. It is never
reused as a routed order.

## Truth labels

- environment: `IBKR_PAPER_SIMULATOR`;
- a Paper execution callback: `PAPER_SIMULATED_FILL`;
- never: `EXCHANGE_VALIDATED_FILL`;
- `SUBMISSION_ATTEMPTED` does not mean accepted or working;
- `transmit=false` means `LOCAL_NOT_TRANSMITTED`, never submitted.

## Current result

```text
PAPER_ADAPTER_CODE       = READY_OFFLINE
PAPER_RUNTIME_DEFAULT    = DISABLED
PAPER_REAL_ORDER_TEST    = NOT_RUN
LIVE_EXECUTION           = FORBIDDEN
HOLDOUT                  = UNOPENED
```
