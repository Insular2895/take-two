# Broker execution provider — isolated PAPER foundation only

Status: the Phase M paper control/journal foundation exists, but the IBKR adapter is disabled and no
broker submission is currently possible. Live execution does not exist.

## Research-engine boundary

The Python research engine and its reports retain the strict read-only boundary. The new code is an
isolated service and D1 control plane; it does not weaken `src/take_two_options` or make research
scores executable.

The Research UI may create a `PLANNED` dossier from a paper-eligible candidate. The conceptual
`EXÉCUTER` control reports `IBKR EXECUTION NOT CONFIGURED`. There is no API route that can preview,
stage, place, modify, cancel, or transmit an opening order. There is also no manual opening fallback.

## First provider — IBKR paper, NOT YET WIRED

IBKR paper is the approved first personal broker architecture. The persistence, HMAC, replay,
idempotency, claim, kill-switch, and restart-journal layers are implemented. A later activation
slice must still implement and validate:

- authentication and minimum credential scopes;
- combo/BAG contract identity and whole-structure semantics;
- broker preview/what-if evidence and buying power;
- idempotency, replay defense, timeout ambiguity, and reconciliation;
- separation of estimate, preview, submitted order, acknowledged order, and actual fills;
- kill switches, rate limits, audit logs, incident response, and credential rotation;
- paper/shadow validation before any real-money consideration.

See [`M_IBKR_PAPER_CONTROL_PLANE.md`](M_IBKR_PAPER_CONTROL_PLANE.md). The approval covers building
the paper architecture, not deploying it or enabling live execution.

## Commercial per-user configuration — NOT YET ENABLED

A future commercial product might let each customer authorize their own broker. That would require
tenant isolation, consent, revocation, scoped secret storage, regional/legal review, support and
recovery processes, and per-user audit ownership. None is implemented by CF0.2, and no shared broker
credential should be inferred from this type marker.
