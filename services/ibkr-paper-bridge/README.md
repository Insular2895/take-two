# Take Two IBKR paper bridge

This service is the outbound-only VM half of the isolated paper control plane. It validates legacy
close commands and governed opening commands, journals them before broker work, posts idempotent
events, and exposes no HTTP or IBKR port.

Current runtime status: `DisabledGateway` only. Building/running this container cannot submit an
order. Legacy close commands still require `transmit=false`; the runtime journals
`LOCAL_NOT_TRANSMITTED` and never calls the gateway. `paper_gateway.py` contains a dependency-
injectable, Paper-only entry adapter, but it defaults disarmed and is not imported by `main.py`.
A separate read-only adapter
now collects the locally connected paper account's TTWO positions, per-contract quotes and
broker-reported P&L. It rejects non-loopback hosts, ports other than the paper Gateway port `4002`,
multiple accounts, non-`DU` accounts and symbols other than `TTWO`.

## Offline order-lifecycle readiness

`order_lifecycle.py` prepares deterministic, side-effect-free normalization for future IBKR
callbacks: `openOrder`, `orderStatus`, `error`, `execDetails`, `commissionReport` and callback
boundaries. It preserves the raw status, hashes raw evidence, redacts broker messages, and emits a
separate canonical state. A submitted order with zero fills becomes `WORKING` plus
`WORKING_NO_FILL_YET`, never a guessed rejection or liquidity failure.

The same pure module computes marketability and bounded-reprice diagnostics for debit and credit
combos. Repricing remains a preview: stale/delayed/missing data, an unverified BAG convention,
changed order shape, budget/max-loss breach or authorized-price breach fail closed. There is no
broker modify operation.

The SQLite recovery journal persists `orderRef`, `orderId`, `permId` and `execId`. After restart,
unresolved work blocks a new claim until its state is proved; an unknown state requires
reconciliation and never authorizes duplicate submission.

## Governed Paper entry readiness

`PAPER_ENTRY` separates application actions (`BUY_TO_OPEN`/`SELL_TO_OPEN`) from IBKR combo-leg
wire actions (`BUY`/`SELL`). It requires the immutable analysis/selection/dossier lineage, a fresh
revalidation ticket, an immutable preview and confirmation, complete contract identity, valid
market-rule tick, whole-BAG mode and a guaranteed-combo attestation. The adapter rejects non-DU,
non-loopback, non-Paper ports, stale/degraded data, git/config drift, pacing/backoff conflicts and
an unarmed gateway. The first governed entry is `DAY` only; IOC/FOK/GTC and reused exit-slippage
allowances fail before the order primitive.

This is `READY_OFFLINE_DISARMED`, not a Paper execution result. The official API transport must be
injected in a future operator-authorized composition root; no Live mode exists.

The read-only payload never contains the account identifier. Missing P&L values remain null rather
than becoming false zero totals, and live P&L is explicitly marked as not yet reconciled with final
execution commissions and fees.

## Official IBKR dependency

The official `ibapi` source is not vendored or fetched from an unofficial package index. Install the
user-accepted official TWS API Python client into the same VM virtual environment, then install this
service without replacing it. The VM runbook records the currently validated official version.

With IB Gateway still in Paper Trading and **Read-Only API** enabled:

```bash
ttwo-ibkr-readonly-snapshot
```

This command only invokes account, position, P&L and market-data requests. The console output is
redacted and contains no account identifier. The persistent `ttwo-ibkr-telemetry` entry point runs
the same snapshot every 30 seconds and publishes it only to the dedicated signed Cloudflare
telemetry route. It has no claim, event, preview, or execution method.

The Cloudflare card reports broker market value plus broker-reported daily, unrealized and realized
P&L. Those values remain explicitly **not final fee-reconciled P&L** and do not prove an executable
combo quote.

## Local checks

```bash
PYTHONPATH=src ../../.venv/bin/python -m ruff check src tests
PYTHONPATH=src ../../.venv/bin/python -m pytest -q
docker compose build
```

Copy `.env.example` to an untracked `.env` only on the target VM. Never commit real values. The two
Cloudflare Access service-token headers pass the outer Access policy; the separate shared secret
signs every request, and D1 rejects a repeated nonce.

The production telemetry daemon uses
[`deploy/systemd/take-two-ibkr-telemetry.service`](deploy/systemd/take-two-ibkr-telemetry.service)
and a root-owned `0600` environment file at `/etc/take-two/ibkr-telemetry.env`. Keep the telemetry
HMAC distinct from `BROKER_BRIDGE_SHARED_SECRET`: the Worker rejects either credential at the
other route. The root-only
[`configure-telemetry-access.sh`](deploy/systemd/configure-telemetry-access.sh) helper accepts the
dedicated Access ID/secret without echoing the secret, replaces only those two placeholders, and
starts the daemon after validation.

See [`../../docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md`](../../docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md)
and [`../../docs/specs/IBKR_ORDER_LIFECYCLE.md`](../../docs/specs/IBKR_ORDER_LIFECYCLE.md),
[`../../docs/specs/IBKR_NO_FILL_DIAGNOSTICS.md`](../../docs/specs/IBKR_NO_FILL_DIAGNOSTICS.md),
[`../../docs/specs/IBKR_BOUNDED_REPRICING.md`](../../docs/specs/IBKR_BOUNDED_REPRICING.md)
and [`../../docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md`](../../docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md).
