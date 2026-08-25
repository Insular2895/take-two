# Cloud required-data freshness

Date: 2026-08-24

Status: `IMPLEMENTED_PRE_LIVE_READ_ONLY`

## Canonical rule

A projection is fresh only when every market input actually used by that projection is fresh.
`ProviderSnapshot.timestamp` remains a legacy ordering field and cannot establish freshness.

`calculateRequiredDataFreshness(...)` evaluates:

- the explicit underlying timestamp;
- the timestamp of every option quote matched by `contract_identity`;
- the FX timestamp when native and policy currencies differ;
- the combo timestamp only when `COMBO_QUOTE` is the selected liquidation mode.

The effective timestamp is the oldest required valid timestamp. Timestamps are never averaged and
missing timestamps are never replaced with request time, Worker time, an underlying timestamp, or
another quote.

## Statuses and configuration

The single source constants are:

- `MARKET_DATA_STALE_SECONDS = 120`;
- `MARKET_TIMESTAMP_FUTURE_TOLERANCE_SECONDS = 5`.

The helper accepts explicit overrides for controlled tests or future governed configuration. Its
statuses are:

- `FRESH`: every required input is present, valid, not future, and at most 120 seconds old;
- `STALE`: the required set is complete but at least one timestamp is too old;
- `INVALID`: the required set is complete but a timestamp exceeds the future tolerance;
- `INSUFFICIENT_DATA`: a required quote, price, rate, or timestamp is absent or invalid.

`MARKET_TIMESTAMP_FROM_FUTURE` is recorded without clamping. Same-currency projections leave FX
timestamp null and treat FX freshness as not applicable. An unused stale combo quote cannot affect
a legwise projection.

## Monitoring order

Freshness is evaluated before thesis, stop, profit, expiry, IV, theta, and trailing-drawdown rules:

1. `INSUFFICIENT_DATA` or `INVALID` -> `BLOCKED_INSUFFICIENT_DATA`;
2. `STALE` -> `DATA_STALE`;
3. only `FRESH` data may reach economic exit rules.

The D1 PnL snapshot persists the effective timestamp, component timestamps, age, status, and reason
codes. The dashboard displays the age of the oldest required input rather than the legacy last
underlying quote.

## Safety boundary

This contract adds no provider, entitlement, OPRA connection, broker sync, or order capability.
Live quote semantics and timestamp provenance remain dependencies of the next separately governed
phase.
