# Future broker execution provider — NOT YET ENABLED

Status: architecture marker only. No provider implementation or execution method exists.

## Current boundary

`cloudflare/src/future-broker-types.ts` defines only inert descriptors for a future provider and a
planned intent. Every capability is `NOT_CONFIGURED`, `NOT_IMPLEMENTED`, or `forbidden`; the planned
intent has `provider=null`, actual entry fields null, and `transmitted=false`.

The Research UI may create a `PLANNED` dossier from a paper-eligible candidate. The conceptual
`EXÉCUTER` control reports `IBKR EXECUTION NOT CONFIGURED`. There is no API route that can preview,
stage, place, modify, cancel, or transmit an opening order. There is also no manual opening fallback.

## First intended provider — NOT YET ENABLED

IBKR is the intended first personal broker implementation. A later phase must separately decide and
validate:

- authentication and minimum credential scopes;
- combo/BAG contract identity and whole-structure semantics;
- broker preview/what-if evidence and buying power;
- idempotency, replay defense, timeout ambiguity, and reconciliation;
- separation of estimate, preview, submitted order, acknowledged order, and actual fills;
- kill switches, rate limits, audit logs, incident response, and credential rotation;
- paper/shadow validation before any real-money consideration.

These are requirements to review, not an authorization to build or activate execution.

## Commercial per-user configuration — NOT YET ENABLED

A future commercial product might let each customer authorize their own broker. That would require
tenant isolation, consent, revocation, scoped secret storage, regional/legal review, support and
recovery processes, and per-user audit ownership. None is implemented by CF0.2, and no shared broker
credential should be inferred from this type marker.
