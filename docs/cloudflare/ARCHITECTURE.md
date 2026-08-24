# Phase M-CF0 architecture

## Decision

CF0 is one TypeScript Worker deployment with static assets, an authenticated API, one D1
database, and one SQLite-backed Durable Object class named `TTWOPositionMonitor`. The existing
Python engine remains canonical and exports an immutable `CloudPositionDossier`; CF0 performs only
lightweight post-entry projection.

```text
browser (Mac / iPhone / iPad)
             |
             v
 Cloudflare Worker + assets
       |             |
       v             v
      D1     TTWOPositionMonitor
                       |
                       v
              HTTPS market-data API
```

There is no VPS, production Docker, PostgreSQL, Redis, reverse proxy, daemon, Queue, KV, R2,
Workflow, Vercel, Telegram, or always-on user device. D1 is the durable source of truth. Durable
Object storage contains only the scheduler lock and alarm; losing an isolate cannot lose a
position, SAFE MODE, PnL history, preview, fill, or audit event.

## Boundaries

- Python owns pricing, calibration, distributions, promoted model snapshots, five scores,
  historical research, and validation.
- The Worker owns authentication, dossier validation/import, cached reads, PnL display,
  conservative liquidation projection, advisory exit checks, manual-close reconciliation, and
  export.
- The Durable Object owns one alarm loop and concurrency serialization. Every wake reads D1,
  performs bounded work, persists when due or on a transition, schedules the next alarm, and exits.
- The browser polls persisted state every 10 seconds only while visible; it never causes an external
  quote fetch.

## Canonical flow

```bash
python -m take_two_options.cloud.export_position \
  --ticket reports/examples/m0_trade_economics_ticket.json \
  --output cloud_position.json
```

The exporter maps canonical typed fields without repricing. The generated schema is
`schemas/cloud_position_dossier.schema.json`. Import validation fails closed on the schema version,
SHA-256 formats, git commit, timestamps, currencies, unique contract identities, exact ratios,
inverse close direction, and immutable safety flags.

The default exported state is deliberately `PLANNED`; use `--state PAPER_OPEN` or
`--state LIVE_ASSISTED_OPEN` only when that state is true. Non-live Python fixtures export as
`SYNTHETIC_DEMO` even though their serialization is canonical, so the dashboard cannot present
fixture economics as live.

## Monitoring and storage cadence

- Expected US session: 30-second alarm target.
- Outside expected session: 5 minutes.
- No active position: alarm is removed.
- PnL history: at most one full snapshot per 60 seconds, plus material state transitions.
- Conservation mode: monitor 60 seconds, browser 30 seconds, snapshots 120 seconds.

The current session window is a lightweight UTC expectation, not an exchange-calendar oracle. A
future provider adapter should expose authoritative session state when one is selected.

## Truthful status

The application has no provider configured and no broker synchronization. `SYNTHETIC_DEMO` and
`LAST_IMPORTED_SNAPSHOT` remain visibly labelled. `read_only=true`, `transmit=false`,
`what_if=true`, `human_confirmation_required=true`, and `order_capability=forbidden` are both
contract and runtime boundaries.
