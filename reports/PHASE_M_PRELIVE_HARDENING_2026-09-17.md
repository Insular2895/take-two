# Phase M — pre-live hardening

Date: 2026-09-17
Starting commit: `ae2e4204e26d608460202b5f0c556e8a47a630c7`
Scope: offline code, tests, schemas, local D1 migrations and documentation only

## Status

```text
PRELIVE_HARDENING = COMPLETE
RESEARCH_WORKBENCH = READY
IBKR_PROVIDER_IMPLEMENTATION = READY_FOR_LIVE_READONLY_VALIDATION
IBKR_LIVE_DATA_VALIDATION = NOT_RUN
OPRA_ENTITLEMENT = UNCONFIRMED
SHADOW_CAMPAIGN = NOT_STARTED
PAPER_EXECUTION = DISABLED
LIVE_EXECUTION = FORBIDDEN
HOLDOUT = UNOPENED
```

`COMPLETE` means the four requested software-hardening issues pass offline validation. It does not
mean that IBKR, OPRA, a paper order or a live account was validated.

## Economic stop correction

The old control compared signed `estimated_close_cash_flow_policy` with positive fields named net
liquidation value. That was unsafe for credit positions: paying cash to close is normal and the
negative close cash flow does not by itself imply a loss.

The V2 policy now stores:

- `trigger_metric = LIQUIDATION_PNL_POLICY`;
- `warning_liquidation_pnl_policy <= 0`;
- `automatic_exit_liquidation_pnl_policy <= 0`;
- `warning >= automatic_exit`.

The only economic trigger is `projection.liquidation_pnl`. The close cash flow remains in the
execution command as an estimate but cannot drive the stop. Unknown PnL, fees, slippage or FX,
stale/incomplete data, synthetic providers, missing conIds, unhealthy bridge, SAFE MODE, kill
switch or non-PAPER mode block evaluation before an intent can be created.

Migration `0009_fix_paper_exit_pnl_semantics.sql` creates `position_exit_policies_v2`. Legacy
positive-threshold rows are copied with null PnL thresholds, `automatic_exit_enabled=0`,
`legacy_policy_detected=1` and `REQUIRES_EXPLICIT_RECONFIGURATION`. Migrations 0001–0008 were not
modified.

## Timestamp and freshness model

Timestamp provenance, freshness evidence, market-data type and promotion eligibility are stored
separately.

- `SOURCE_TIMESTAMP`: a genuine exchange/provider timestamp is present, not future and within the
  configured maximum age.
- `BOUNDED_CAPTURE_WINDOW`: no source timestamp was supplied, but a direct live snapshot completed
  normally inside the request window with complete, valid two-sided components.
- `UNVERIFIED`: the evidence cannot establish freshness.

The outcome distinguishes `LIVE_SOURCE_TIMESTAMP_FRESH`, `LIVE_CAPTURE_WINDOW_FRESH`, `STALE`,
`DELAYED`, `FROZEN`, `INCOMPLETE` and `INVALID`. Client receipt time is never represented as an
exchange/provider timestamp. The canonical conversion leaves both source timestamp fields null
when client receipt is the only evidence.

Freshness is evaluated for the underlying and every option leg; BAG freshness is evaluated on its
own request. The chain aggregate uses the weakest required component. Cloud monitoring separately
requires FX only for cross-currency positions and combo freshness only when a combo quote is used.
Expired cache refresh failures return an explicit error; `stale_fallbacks` remains zero.

## Execution security boundaries

The security report now proves five domains independently:

```text
research_engine_order_capability = forbidden
read_only_market_provider_order_capability = forbidden
read_only_telemetry_order_capability = forbidden
paper_execution_adapter = disabled
live_execution_capability = forbidden
```

AST tests reject order imports/calls, `transmit=True`, read-only telemetry mutations and any bridge
runtime replacement of `DisabledGateway`. The existing `PaperGateway.execute_bounded_combo`
protocol method remains allowed because no enabled runtime implementation exists. Loopback,
paper-port and `DU` account guards remain enforced.

## npm audit qualification

Before remediation, `npm audit --json` reported four high findings, all on the dev/build/test path:

| Finding | Path | Advisory/range | Remediation |
|---|---|---|---|
| `sharp` | Wrangler/plugin → Miniflare → Sharp | `GHSA-rgj7-g3m4-5g8c`, npm source `1193725`, `<0.35.4` | Sharp `0.35.4` transitively |
| `miniflare` | Wrangler/plugin → Miniflare | affected through Sharp | `5.20260917.0-alpha` |
| `wrangler` | direct dev dependency → Miniflare | `4.16.0–4.130.0` | `4.134.0` |
| `@cloudflare/vitest-plugin` | direct dev dependency → Wrangler/Miniflare | `1.0.0–1.1.6` | `1.1.12` |

Workers types were compatibly aligned to `5.20260917.1`. After `npm ci`, both the full audit and
`npm audit --omit=dev --json` report zero vulnerabilities. The dry-run bundle contains none of
Wrangler, Miniflare, Sharp or Vitest. CI now fails on high/critical runtime advisories through
`npm audit --omit=dev --audit-level=high`.

## Validation evidence

- Root Python: `450 passed`; one third-party `websockets.legacy` deprecation warning.
- Cloudflare/Vitest: `67 passed` across 8 files.
- IBKR paper bridge: `14 passed`.
- Ruff: pass; mypy strict: pass across 200 source files.
- Generated schemas: 44 verified.
- Offline artefacts, research registry, Phase 10 and Phase 11 deterministic gates: pass.
- Security gate: pass; 178 research files, 2 provider files and 5 telemetry files scanned.
- `pip check`: pass.
- `npm ci`, full audit, runtime audit and runtime audit CI command: pass, zero vulnerabilities.
- Wrangler dry-run: pass; 251.70 KiB upload, 59.96 KiB gzip.
- D1: clean migration, 0001–0008 upgrade and legacy-row upgrade all pass locally. Defaults remain
  `DISABLED`, kill switch engaged, bridge `NOT_CONFIGURED`, zero claimable intent.

## Remaining external gates

Before the first real IBKR/OPRA read-only validation:

1. human proof of the account's OPRA entitlement and permitted data use/storage;
2. operator-confirmed IB Gateway/TWS paper session, loopback socket and Read-Only API setting;
3. explicit authorization for the first connection command;
4. live observation of underlying, complete option chain, Greeks/OI/volume and BAG snapshot;
5. comparison with the TWS display and capture of redacted evidence.

Shadow and paper campaigns remain later gates. A real `PaperGateway`, order callbacks, commissions,
margin what-if and broker-native protection remain intentionally unimplemented/disabled.

## Non-actions confirmed

- no remote deployment;
- no remote D1 migration;
- no Cloudflare secret or Access change;
- no IBKR or OPRA connection;
- no broker order;
- no ranking/model/Research Workbench change;
- no historical/OOS rewrite;
- holdout unopened;
- order transmission forbidden.
