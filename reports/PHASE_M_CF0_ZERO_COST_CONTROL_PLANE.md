# Phase M-CF0 — Zero-cost Cloudflare control plane

Date: 2026-08-24

Branch: `codex/v10-quantitative-validation-and-robust-decision-engine`

Deployment: **active** at `https://take-two-control.lpertusa2895.workers.dev`, with D1 and a
Worker-level Cloudflare Access **All traffic** account-member policy.

## Outcome

CF0 now provides a private, responsive, single-user control plane using one TypeScript Worker
behind Cloudflare Access, one D1 database, one SQLite-backed `TTWOPositionMonitor` Durable Object,
and UI resources bundled as Worker text modules.
It needs no VPS, production Docker, PostgreSQL, Redis, reverse proxy, paid Cloudflare component, or
always-on Mac.

The Python engine remains canonical. `CloudPositionDossier` is a strict Pydantic contract with an
export CLI and generated JSON Schema. The exporter maps the existing ticket without repricing.
The Worker validates and imports the dossier, reconstructs all durable state from D1, and computes
only lightweight entry-to-current monitoring projections.

## Components and data flow

```text
Python canonical ticket -> CloudPositionDossier -> authenticated Worker -> D1
                                                        |
                                                        v
                                              Durable Object alarm
                                                        |
                                                        v
                                              HTTPS provider adapter
```

D1 tables: `system_state`, `positions`, `position_legs`, `fills`, `pnl_snapshots`,
`model_snapshots`, `close_previews`, `monitoring_events`, `audit_events`, `daily_usage`, and
`action_password_attempts` are active. The legacy `sessions` and `login_attempts` tables remain
unused for non-destructive schema compatibility. Audit events are append-only by trigger;
close-preview economics cannot be mutated after creation.

## User interface

The single `/dashboard` page has SYSTEM, POSITION / PNL, MARKET / THETA, RISK, ENGINE, PNL HISTORY,
CLOSE STRUCTURE, CONTROLS, and RECENT EVENTS panels. It prioritizes mobile PnL/status/close content,
labels synthetic/stale/not-configured data, shows `ORDER CAPABILITY FORBIDDEN`, polls cached state
only while visible, and slows under conservation mode.

The three economic values remain separate:

- mark-to-market PnL from signed leg midpoints;
- estimated liquidation PnL from long bid / short ask, explicit combo-vs-legwise mode, and known
  exit costs;
- expected remaining PnL only from the timestamped canonical model snapshot.

Unknown required FX execution cost makes net liquidation `N/A`; it is never treated as zero.
Partial close views retain realized, unrealized, and total PnL. Fully reconciled positions remain in
D1 and render as `TTWO — CLOSED`.

## Whole-structure close and realized PnL

There is one primary `CLOSE STRUCTURE` button. Its preview reverses every exact identity, expiry,
strike, right, ratio, multiplier, and quantity as one BAG-shaped structure. Missing completeness
returns `COMBO_CLOSE_PREVIEW_UNAVAILABLE`; no individual-leg fallback exists.

Acknowledgement is protected by CSRF, requires a Cloudflare Access authentication timestamp no
older than five minutes, and requires the separate action password. It stores only
`CLOSE_PREVIEW_READY` and tells the human to close the complete combo manually in IBKR. It cannot
send, cancel, modify, exercise, retry, or mark a trade closed.

Manual fill reconciliation captures timestamp, combo price, quantity, commission, FX cost/rate,
and optional broker reference. The original estimate stays immutable. The acceptance fixture
persists €1,023 entry cash, €1,455 estimated proceeds / €432 estimated PnL, €1,440 actual proceeds /
€417 actual realized PnL, and −€15 estimate error. One of two structures yields `PARTIAL_CLOSE`; zero
remaining yields `CLOSED`.

## Authentication and controls

- Cloudflare Access is the only production login and authorizes Cloudflare account members on all
  Worker traffic.
- The Worker requires a direct `ctx.access` identity with an email and returns `403` otherwise.
- Private UI resources are bundled into the Worker so Access context reaches application code.
- Sensitive control-plane mutations require a second, reusable action password after Access. Its
  keyed HMAC verifier is held only as an encrypted Worker secret; the password and verifier never
  enter D1, browser storage, logs, assets, or Git.
- Action-password failures are reserved atomically in D1 per verified Access identity and limited
  to five attempts per rolling 15 minutes. Missing verifier configuration fails closed.
- A random 256-bit `__Host-ttwo_csrf` cookie is `HttpOnly; Secure; SameSite=Strict; Path=/` and must
  match the mutation header.
- Cloudflare Access logout and session revocation replace application password/session endpoints.
- SAFE MODE and monitoring pause persist independently. SAFE MODE preserves existing monitoring
  but blocks imports; pause never implies a financial close.
- Same-origin CSP, `no-store`, frame denial, no-referrer, and no browser delivery of secrets.

## Scheduler and failure behavior

The Durable Object serializes one monitor, uses an expiring persisted lock, and relies on
at-least-once-safe alarm logic. Each wake reads D1, fetches provider state if configured, rejects
bad/stale data, projects current economics, persists at most once per minute or on a transition,
and reschedules. No active position or persisted pause removes the alarm. Provider errors retain
the last snapshot and record `DATA_PROVIDER_ERROR`; stale data becomes `DATA_STALE` before exit-rule
evaluation.

Cloudflare documents that alarms are at-least-once and can retry, which is why material events have
dedupe keys: [Durable Object alarms](https://developers.cloudflare.com/durable-objects/api/alarms/).

## Free-tier estimate

Default `APPLICATION_ESTIMATE_ONLY` daily estimate for one user and one open position:

| Item | Estimate |
|---|---:|
| Alarm executions | 990 |
| Browser API reads (8 visible hours) | 2,880 |
| Worker/DO invocations plus allowance | 3,970 |
| External provider subrequests | 4,950 |
| PnL history rows | 600 |
| Approximate D1 row writes | 7,150 |

This is below the internal 60,000 soft warning, 80,000 degradation trigger, and 90,000 unsafe
ceiling. It is also below the current Workers Free 100,000 request/day and D1 Free 100,000
row-write/day quotas; it does not promise future limits or provider costs. Official sources checked:
[Workers limits](https://developers.cloudflare.com/workers/platform/limits/),
[D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/),
[D1 limits](https://developers.cloudflare.com/d1/platform/limits/), and
[Durable Objects pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/).

## Verification

- Cloudflare: `npm run check` — TypeScript, safety scan, and 33 Vitest tests.
- Cross-language: shared `monitoring_parity.json` covers PnL, HOLD, WATCH, profit, stop, time, IV,
  theta, trailing drawdown, stale data, thesis invalidation, and insufficient data.
- Python exporter: strict schema/safety/hash/identity tests and CLI smoke export.
- D1/Worker integration: missing/invalid Access identity denial, bundled private assets, removed
  password endpoints, CSRF, Access freshness, action-password absence/success/failure/atomic rate
  limiting, import, runtime-independent reads, alarms, provider absence, duplicate/concurrent
  alarms, SAFE MODE, pause/resume, immutable preview, actual reconciliation, identity-aware audits,
  and partial close.
- Repository cloud safety scan rejects broker-order capability tokens and `transmit: true`.

Final local gate: 346 Python tests passed; Ruff and strict mypy passed; 29 generated schemas and the
offline artifact validator passed. The 33 Worker tests, safety scan, TypeScript compiler, Wrangler
production dry-run, remote D1 migration, Worker secret presence check, deployment, and unauthenticated
Access redirect passed. GitHub CI remains a publication-time check and runs both the Python and
Cloudflare gates.

## Recovery and domain

`EXPORT DATA` creates an authenticated secret-free JSON backup. D1 is primary persistence; its Free
plan currently exposes seven days of Time Travel. Standard Wrangler migrations are non-destructive.
See `docs/cloudflare/RECOVERY.md`.

The real deployment uses the workers.dev hostname. A future registrar domain can be added to
Cloudflare and attached as `trade.example.com` without changing application architecture, but the
Access **All traffic** coverage must be verified before use. See `docs/cloudflare/CUSTOM_DOMAIN.md`.

## Limitations and status

- Cloudflare Access policy is external account state and must remain enabled for **All traffic**.
- `LIVE_MARKET_DATA=NOT_CONFIGURED`; demo/last-imported data remain labelled.
- `BROKER_LIVE_SYNC=NOT_CONFIGURED`; actual fills require manual IBKR reconciliation.
- The UTC expected-session cadence is not a substitute for an exchange calendar.
- OPRA/provider/broker/FX/domain costs are outside the €0 Cloudflare-hosting claim.
- The final holdout remains unopened. No V10 retuning or Phase M market validation occurred.

```text
CF0_CONTROL_PLANE=READY
CF0_WEB_UI=READY
CF0_AUTH=READY
CF0_ACTION_PASSWORD=READY
CF0_PERSISTENCE=READY
CF0_MONITOR_SCHEDULER=READY
CF0_STRUCTURE_CLOSE_PREVIEW=READY
CF0_REALIZED_PNL_RECONCILIATION=READY
CF0_FREE_TIER_DESIGN=READY
LIVE_MARKET_DATA=NOT_CONFIGURED
BROKER_LIVE_SYNC=NOT_CONFIGURED
ORDER_TRANSMISSION=FORBIDDEN
PHASE_M_VALIDATION=NOT_STARTED
```
