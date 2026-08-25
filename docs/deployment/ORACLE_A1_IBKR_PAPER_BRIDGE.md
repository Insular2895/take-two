# Oracle A1 + IB Gateway paper bridge runbook

Status: **VM/API read-only path validated; signed telemetry implemented; dispatch remains disabled**

## Provisioning checkpoint — 2026-08-25

User-confirmed state from the OCI console and the first SSH session:

- `take-two-ibkr-paper` is running in `eu-paris-1` on `VM.Standard.A1.Flex` with 2 OCPUs and
  12 GB RAM;
- the image is Ubuntu 24.04 Minimal ARM64 and instance-metadata access is v2-only;
- the VM has an ephemeral public IP for administration;
- OCI SSH ingress was changed from `0.0.0.0/0` to the owner's current public IPv4 `/32`;
- UFW is active with default-deny ingress, default-allow egress, and SSH limited to the source IP
  observed for the authenticated session;
- base packages were updated and `fail2ban` plus unattended upgrades were enabled.
- Docker Engine and the Compose plugin were installed from Docker's official Ubuntu repository;
  the user-confirmed `hello-world` run pulled and executed the `arm64v8` image successfully.
- XFCE and TigerVNC were installed; the user confirmed display `:1` is listening on the loopback
  interface only. VNC port `5901` remains closed in OCI and UFW and is intended to be reached solely
  through an SSH local-forward tunnel.
- the owner successfully reached the XFCE desktop from macOS through an SSH local forward
  (`127.0.0.1:15901` to VM loopback `127.0.0.1:5901`); the first failed attempt was traced to a
  missing local tunnel, not a VM/VNC failure.
- IB Gateway Stable ARM64 was downloaded from IBKR and installed as the unprivileged `ubuntu`
  user. Its first GUI launch required Ubuntu package `libxtst6`; after installation, the owner
  logged into the IB API paper path and the API server plus market-data farms reported connected.
- Gateway API settings were user-confirmed with Read-Only enabled, paper socket port `4002`,
  localhost-only clients, trusted IP `127.0.0.1`, and automatic order maintenance/resubmission
  after reconnect disabled. The Gateway process nevertheless listens on `*:4002`; OCI has no
  ingress rule for that port and UFW now carries explicit IPv4/IPv6 deny rules. A local TCP probe
  to `127.0.0.1:4002` succeeded after those rules were applied.
- the official TWS API `10.49.02` Mac/Unix archive was transferred directly to the VM, verified by
  SHA-256, extracted outside the repository, and its Python client was installed in a dedicated
  virtual environment with its pinned Protobuf dependency. No IBKR source or binary was committed;
- the owner confirmed a local Python read-only probe completed the API handshake on `127.0.0.1:4002`,
  received the managed-account, server-time, and position-end callbacks, and rejected any account
  not prefixed `DU`. The probe did not contain any place, modify, or cancel-order call and did not
  print the account identifier.

The exact OCI rule value and public IP were deliberately not copied into the repository. This
checkpoint validates the standalone official Python client and paper-account guard. It does not
yet validate the project bridge image or project-owned adapter against that VM, combo quotes,
recovery, or any paper order path.

## Project read-only adapter checkpoint

The repository now contains a project-owned read-only telemetry adapter and redacted CLI. Local
validation covers:

- loopback-only host and paper Gateway port `4002`;
- exactly one `DU` account, with the identifier removed from output;
- TTWO-only non-zero positions and per-contract market-data requests;
- broker-reported per-position market value, daily, unrealized, and realized P&L;
- real-time, frozen, delayed, and delayed-frozen quote labels;
- null-preserving aggregation: one missing leg value makes the corresponding total unavailable;
- an explicit warning that live P&L is not final fee-reconciled P&L;
- a source-boundary test proving the read-only module contains no order-transmission call and remains
  absent from the bridge runtime, which still instantiates `DisabledGateway`.

The adapter imports successfully against official `ibapi 10.49.2` and pinned `protobuf 5.29.5` in
an isolated local installation.

On 2026-08-25, commit `c84e47964acf63f5c9617126dcc899cf0a0fdff7` was cloned to
`~/apps/take-two` on the Oracle VM and the project package was installed into the dedicated official
API environment at `~/.venvs/ibkr-api`. The project CLI completed a redacted `PAPER_READ_ONLY`
snapshot against loopback port `4002`: server time was present, the account identifier remained
absent, and the symbol scope remained `TTWO`. The paper account contained zero open TTWO positions,
so this checkpoint does not yet validate per-leg quotes, position P&L, fee reconciliation, or combo
grouping. The first snapshot was not posted to Cloudflare. The repository now includes a persistent,
read-only systemd publisher and a dedicated schema-validated Cloudflare route. No executable combo
adapter has been enabled.

## What the user will provide later

IBKR's TWS socket API does not use an API key/secret. At the activation step the owner will:

1. log into **Paper Trading** inside IB Gateway on the Oracle VM;
2. verify the paper account identifier begins with `DU` locally;
3. enable the socket client on paper port `4002` and keep it restricted to localhost;
4. initially keep IB Gateway's API Read-Only setting enabled while connectivity and market-data
   callbacks are tested;
5. disable Read-Only only for the controlled paper execution test window.

Never paste the IBKR username, password, 2FA response, account identifier, Cloudflare service-token
secret, or bridge HMAC secret into chat, GitHub, an image, or a committed environment file.

## VM target

- Provider/shape: OCI `VM.Standard.A1.Flex`, Always Free eligible in the tenancy's home region.
- Initial size: 2 OCPUs, 12 GB RAM, 50 GB boot volume, Ubuntu ARM64.
- Cost target: €0 only while the Console marks every resource **Always Free eligible** and the
  tenancy remains within its displayed limits.
- Availability limitation: A1 capacity can be unavailable. Oracle may reclaim a VM it classifies as
  idle; this free VM is therefore suitable for paper proving, not a guaranteed live safety system.
- Network: no public ingress to `4002`, the bridge, or its journal. Use OCI Bastion/SSH for admin.

Oracle's current documentation is not perfectly consistent across locale/account pages about the
maximum A1 allowance. Use the limits shown inside the actual tenancy; do not provision from a blog
or assume 4 OCPUs/24 GB are free.

## Secret map

| Location | Name | Purpose |
|---|---|---|
| Cloudflare Worker secret | `BROKER_BRIDGE_SHARED_SECRET` | verifies application HMAC |
| Cloudflare Worker variable | `BROKER_BRIDGE_ID` | pins the one expected VM identity |
| VM `.env` only | `TTWO_BRIDGE_SHARED_SECRET` | same HMAC value |
| VM `.env` only | `CF_ACCESS_CLIENT_ID` | Access service-token ID |
| VM `.env` only | `CF_ACCESS_CLIENT_SECRET` | Access service-token secret |
| VM `.env` only | `TTWO_CONTROL_URL` | protected Worker URL |

Read-only telemetry uses a separate credential boundary:

| Location | Name | Purpose |
|---|---|---|
| Cloudflare Worker secret | `BROKER_TELEMETRY_SHARED_SECRET` | verifies telemetry-only HMAC |
| Cloudflare Worker variable | `BROKER_TELEMETRY_ID` | pins the telemetry publisher identity |
| VM root-owned env | `TTWO_TELEMETRY_SHARED_SECRET` | same telemetry-only HMAC value |
| VM root-owned env | `CF_ACCESS_CLIENT_ID` | dedicated VM Access service-token ID |
| VM root-owned env | `CF_ACCESS_CLIENT_SECRET` | dedicated VM Access service-token secret |
| VM root-owned env | `TTWO_CONTROL_URL` | protected Worker base URL |

The Access policy must keep the existing human account-member rule and add a dedicated VM Service
Auth policy selecting only the VM service token. Do not reuse the GitHub Actions token. Rotate the
service token and telemetry HMAC independently after an incident.

Cloudflare shows the service-token secret only once. Enter it directly in the protected VM setup
session; never paste it into chat. The daemon sends both Access headers and the telemetry HMAC.

## Current safe verification

The bridge image can be built now, but it intentionally uses `DisabledGateway`. Its heartbeat is
`DEGRADED`, so Cloudflare cannot disable the kill switch and cannot dispatch an intent. The separate
read-only VM probe proves local IBKR connectivity and the `DU` guard. The new project reader remains
outside that runtime and grants no broker authority to the project bridge.

Migrations `0007` and `0008` are additive and fail closed: broker mode defaults to `DISABLED`, the
kill switch defaults engaged, and telemetry has no order capability. Back up remote D1 before
applying them. A deployment of these migrations does not authorize paper dispatch.

## Persistent telemetry service

After the branch is installed on the VM and the dedicated Access service token exists:

```bash
cd ~/apps/take-two
git pull --ff-only
~/.venvs/ibkr-api/bin/python -m pip install --no-deps -e services/ibkr-paper-bridge
sudo install -d -m 0700 /etc/take-two
sudo install -m 0600 \
  services/ibkr-paper-bridge/deploy/systemd/ibkr-telemetry.env.example \
  /etc/take-two/ibkr-telemetry.env
sudo install -m 0644 \
  services/ibkr-paper-bridge/deploy/systemd/take-two-ibkr-telemetry.service \
  /etc/systemd/system/take-two-ibkr-telemetry.service
sudo systemctl daemon-reload
```

Replace every placeholder in `/etc/take-two/ibkr-telemetry.env` through a private SSH session, then
validate and start:

```bash
sudo systemd-analyze verify /etc/systemd/system/take-two-ibkr-telemetry.service
sudo systemctl enable --now take-two-ibkr-telemetry.service
sudo systemctl status --no-pager take-two-ibkr-telemetry.service
sudo journalctl -u take-two-ibkr-telemetry.service -n 30 --no-pager
```

The log intentionally contains only a success position count or an exception class. It must never
contain an account identifier, payload, request header, URL, or secret. Once enabled, no Mac
terminal, VNC tunnel, or VS Code window is required for telemetry. IB Gateway itself must remain
logged in on the VM and may still require periodic IBKR reauthentication.

## Later activation order

1. Create and harden OCI A1.
2. Install official IB Gateway ARM64 and log into Paper Trading.
3. Install the official TWS API locally on the VM.
4. Add and test the real adapter with Read-Only still enabled.
5. Verify positions, combo quotes, `DU` account guard, callbacks, and recovery.
6. Exercise simulated failures and partial fills.
7. Enable a short paper execution window and submit the smallest representative combo.
8. Reconcile execution price plus commissions/fees before showing final net P&L.
9. Prove native protective orders and automatic-floor behavior in paper.
10. Only then consider keeping paper dispatch continuously enabled.
