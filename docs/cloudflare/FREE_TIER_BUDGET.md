# Cloudflare Free budget

## Current official limits checked for CF0

As of 2026-08-24, Workers Free documents 100,000 requests/day and 10 ms CPU per HTTP request;
D1 Free documents 5 million rows read/day, 100,000 rows written/day, and 5 GB total storage;
Durable Objects Free supports SQLite-backed namespaces with 100,000 requests/day and 13,000
GB-s/day. Check the official pages before production because platform limits can change:

- [Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/)
- [D1 limits](https://developers.cloudflare.com/d1/platform/limits/)
- [Durable Objects pricing](https://developers.cloudflare.com/durable-objects/platform/pricing/)

## Default one-user estimate

Assumptions: one open position, 30-second market-session alarms for 6.5 hours, 5-minute off-hours
alarms, dashboard visible for 8 hours at 10-second polling, 60-second market-session history, and a
generic provider adapter making status + underlying + options + FX + optional combo calls.

| Estimate | Per day |
|---|---:|
| Monitor alarm executions | 990 |
| Browser API reads | 2,880 |
| Worker/DO invocations plus control allowance | 3,970 |
| External provider HTTP subrequests | 4,950 |
| Full PnL snapshot rows | 600 |
| Approximate total D1 row writes including counters/state | 7,150 |

These are conservative application estimates, labelled `APPLICATION_ESTIMATE_ONLY`; they are not
Cloudflare billing counters. The default is below the internal 60,000 invocation soft warning and
well below the 90,000 unsafe ceiling.

## Guardrails

- `<60,000`: normal.
- `60,000–79,999`: soft warning.
- `80,000–89,999`: `FREE_TIER_CONSERVATION_MODE`.
- `>=90,000`: configuration is unsafe and the estimator test fails.

At conservation, alarm cadence changes 30→60 seconds, visible browser polling should change
10→30 seconds, and snapshot cadence changes 60→120 seconds. Safety events remain active. Daily D1
counters cover API reads, alarms, external requests, and snapshot writes. They intentionally do not
claim equality with account-level Cloudflare analytics.

The Vitest guard fails when a default configuration would cross the internal budget. External
provider requests may have their own paid quota and must be checked separately.
