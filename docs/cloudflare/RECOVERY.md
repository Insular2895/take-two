# Persistence, export, and recovery

D1 is the source of truth for system state, positions and legs, fills, PnL and model snapshots,
immutable close previews, monitoring events, append-only audit events, and daily usage. Cloudflare
Access owns authentication sessions. Durable Object memory is never authoritative.

The authenticated `EXPORT DATA` action downloads JSON containing positions, legs, fills, PnL/model
snapshots, close previews, monitoring events, and audit events. It excludes legacy auth tables,
Access identities/tokens, credentials, secrets, and API keys. Store exports in an encrypted location.

On runtime/isolate disappearance, the next request reconstructs the dashboard from D1. The alarm
reconstructs its work from `system_state` and the active position. SAFE MODE, monitoring pause,
partial close, reconciled fills, closed history, and previews therefore survive browser, VS Code,
Mac, or Worker-isolate shutdown.

Migrations use standard non-destructive Wrangler D1 migrations:

```bash
npx wrangler d1 migrations apply take-two-control --local
npx wrangler d1 migrations apply take-two-control --remote
```

Never auto-recreate or drop production D1. Before recovery, take a manual export and verify the
target account/database. Cloudflare D1 Free currently retains Time Travel history for seven days;
use the current documented bookmark/timestamp procedure rather than guessing a restore command:
[D1 Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/). Restoring changes
cloud state and requires explicit operator confirmation.

Retention is compact by design: no raw quote tape, one-minute PnL history by default, and raw quote
detail only in decision/state events or immutable previews.
