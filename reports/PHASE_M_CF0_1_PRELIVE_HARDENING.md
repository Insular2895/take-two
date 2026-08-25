# Phase M-CF0.1 — pre-live economics and data-freshness hardening

Date: 2026-08-24

## Result

`COMPLETE_PRE_LIVE_READ_ONLY`

The Worker now evaluates freshness from the oldest required market input and supports both debit
and bounded-risk credit structures with signed opening and closing cash flows. Capital requirement
is separate from PnL accounting.

## Initial problems

- freshness was derived from the underlying timestamp alone;
- required option, FX, and combo timestamps could not conservatively control monitoring status;
- `actual_entry_cash > 0` conflated cash flow, capital requirement, return denominator, and PnL;
- combo quotes and manual fills implicitly assumed cash received;
- UI wording assumed every close generated proceeds.

## Implemented behavior

- `CloudPositionDossier` schema 1.1 carries `entry_cash_flow_policy` and
  `capital_required_policy` plus unchanged Phase M context ID/hash provenance;
- receipt-positive / payment-negative account cash-flow convention;
- final entry cash flow derives from canonical ticket execution economics, including policy FX
  conversion and FX execution cost exactly once;
- MTM, estimated liquidation, realized, loss, and partial-close formulas use signed flows;
- returns use governed capital, while capital never enters a PnL formula;
- combo quotes and manual fills require explicit `CREDIT` or `DEBIT` type;
- required-data freshness persists the oldest timestamp, component provenance, age, status, and
  reasons;
- stale data precedes every economic exit rule; missing/invalid/future input fails closed;
- dashboard wording is neutral and shows oldest required input age.

## Files changed

- Python contract/export: `src/take_two_options/cloud/contracts.py`,
  `src/take_two_options/cloud/export_position.py`;
- Worker domain/persistence/routes/provider/monitor/types/demo: `cloudflare/src/`;
- dashboard wording and reconciliation form: `cloudflare/public/app.txt`,
  `cloudflare/public/dashboard.txt`;
- additive D1 migrations: `cloudflare/migrations/0003_*`, `cloudflare/migrations/0004_*`;
- tests: `tests/test_cloud_position_export.py`, `cloudflare/test/domain.test.ts`,
  `cloudflare/test/integration.test.ts`;
- generated contract: `schemas/cloud_position_dossier.schema.json`;
- specifications, audit, and this Markdown/JSON report under `docs/` and `reports/`.

## Schema and D1 migration

- generated `schemas/cloud_position_dossier.schema.json` now describes dossier 1.1;
- migration `0003_prelive_freshness_signed_cash.sql` adds signed entry/capital, signed fill, signed
  close-preview, and freshness provenance columns without dropping data;
- migration `0004_close_preview_signed_economics_immutable.sql` extends the immutable preview
  trigger;
- only the proven synthetic schema 1.0 debit path is backfilled; unknown legacy signs become
  `RECONCILIATION_REQUIRED`.

## Acceptance cases

| Case | Expected | Result |
|---|---:|---|
| Debit MTM | `1487 - 1023 = +464` | `PASS` |
| Debit liquidation | `1455 - 1023 = +432` | `PASS` |
| Credit MTM | `-120 + 300 = +180` | `PASS` |
| Credit liquidation | `-105 + 300 = +195` | `PASS` |
| Losing credit close | `-660 + 300 = -360` | `PASS` |
| Manual debit close of credit entry | `-102 + 300 = +198` | `PASS` |
| Partial credit close | `-115 + 300 = +185` | `PASS` |
| Fresh underlying / stale option | `DATA_STALE` | `PASS` |
| Stale required FX | `DATA_STALE` | `PASS` |
| Stale used combo | `DATA_STALE` | `PASS` |
| Stale unused combo | no effect | `PASS` |
| Future timestamp | fail closed | `PASS` |
| Missing option timestamp | fail closed | `PASS` |

## Validation and freeze

- Python full suite, Ruff, mypy, 30 schemas, offline artifact validation, research registry, Phase 10
  release audit, security gate, Cloudflare check/Vitest, D1 migrations, and Wrangler dry-run pass;
- M0/M0.1/M0.2/M0.2.1 and golden ticket hashes are unchanged;
- Phase M governed context remains intact;
- Cloudflare Access, CSRF, and action-password confirmation are unchanged;
- whole-BAG preview only; no leg-by-leg fallback;
- `read_only=true`, `transmit=false`, `what_if=true`, `order_capability=forbidden`;
- `HOLDOUT=UNOPENED`.

## Remaining live dependencies

Live read-only provider/OPRA rights, verified timestamp and quote semantics, broker read-only sync,
observed execution evidence, shadow validation, and separately authorized paper validation remain
not configured.

## Final status

```text
CF0_REQUIRED_DATA_FRESHNESS = HARDENED
CF0_SIGNED_CASH_FLOW_ACCOUNTING = HARDENED
DEBIT_STRUCTURES = SUPPORTED
CREDIT_STRUCTURES = SUPPORTED
PARTIAL_CLOSE_ACCOUNTING = SUPPORTED
PHASE_M_CONTEXT_PROPAGATION = COMPLETE
CF0_CONTROL_PLANE = READY_FOR_LIVE_READ_ONLY_INTEGRATION
CLOUDFLARE_ACCESS = UNCHANGED
ORDER_TRANSMISSION = FORBIDDEN
HOLDOUT = UNOPENED
```
