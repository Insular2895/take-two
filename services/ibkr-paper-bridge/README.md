# Take Two IBKR paper bridge

This service is the outbound-only VM half of the isolated paper control plane. It validates
close-only paper commands, journals them before broker work, posts idempotent events, and exposes no
HTTP or IBKR port.

Current execution status: `DisabledGateway` only. Building/running this container cannot submit an
order, and the bridge runtime cannot claim one through the new reader. A separate read-only adapter
now collects the locally connected paper account's TTWO positions, per-contract quotes and
broker-reported P&L. It rejects non-loopback hosts, ports other than the paper Gateway port `4002`,
multiple accounts, non-`DU` accounts and symbols other than `TTWO`.

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
redacted and contains no account identifier. It is not yet posted to Cloudflare and does not prove
execution-fee reconciliation or an executable combo quote.

## Local checks

```bash
PYTHONPATH=src ../../.venv/bin/python -m ruff check src tests
PYTHONPATH=src ../../.venv/bin/python -m pytest -q
docker compose build
```

Copy `.env.example` to an untracked `.env` only on the target VM. Never commit real values. The two
Cloudflare Access service-token headers pass the outer Access policy; the separate shared secret
signs every request, and D1 rejects a repeated nonce.

See [`../../docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md`](../../docs/specs/M_IBKR_PAPER_CONTROL_PLANE.md)
and [`../../docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md`](../../docs/deployment/ORACLE_A1_IBKR_PAPER_BRIDGE.md).
