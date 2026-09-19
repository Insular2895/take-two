# Execution revalidation before entry or reprice

## Purpose

An old selected opportunity is evidence about time T0, not authority to chase it at T1. Every
initial executable price and every one-shot reprice must create a new immutable
`ExecutionRevalidationTicket` from the same structure and fresh inputs.

## Ticket contents

The schema binds:

- analysis, candidate, selection and PLANNED dossier IDs;
- original market snapshot and original economics, plus their hashes;
- current market hash, git/config versions and previous ticket;
- exact legs, quantity, structure type/hash and whole-BAG mode;
- spot; each leg bid/ask, timestamp, IV and provider Greeks; BAG and synthetic quotes;
- data type and component freshness; FX, rates, dividends, OI, volume and sizes;
- trading/liquid hours and timezone;
- original economics, proposed execution economics and explicit deltas;
- material-drift result, verdict, blockers and optional reanalysis request.

Its JSON Schema is `schemas/execution_revalidation_ticket.schema.json`.

## Canonical recalculation

The revalidation service does not calculate `old_limit + tick`. It calls the injected canonical
economics engine for the unchanged structure and proposed whole-BAG limit. The returned snapshot
contains cash flow, commission, slippage, FX cost, capital, buying power when known, max loss/gain,
breakevens, expected PnL/return, probabilities, VaR/CVaR, return ratios, theta/capital, flat-spot
diagnostics, scenario hashes, event/volatility evidence, touch probabilities, liquidity and the
five existing scores. No sixth score is introduced.

## Greeks semantics

Case A — only the desired limit changes and the market snapshot hash is identical:

- raw contract Greeks must remain identical;
- entry-dependent max loss, max gain, breakeven, expected return, distribution-relative metrics
  and theta/capital are recalculated.

Case B — spot, time, IV, quotes, rates or dividends changed:

- all available Greeks and all economics are recalculated from the fresh market.

A test fails the ticket if a canonical engine changes Greeks under an identical market hash.
Golden tests cover identical market, spot, IV, time, tick, hard ceiling, BAG, underlying, leg and
FX freshness.

## Verdicts

| Verdict | Meaning |
|---|---|
| `EXECUTABLE` | Initial price passed configured gates; still needs preview and human confirmation. |
| `EXECUTABLE_REPRICE_PROPOSAL` | One reprice passed an approved drift policy; never automatic. |
| `REVIEW_REQUIRED` | Evidence/policy does not justify automatic acceptance. |
| `REANALYSIS_REQUIRED` | Material drift means the candidate universe must run again. |
| `BLOCKED` | A hard precondition failed. |

Delayed/frozen data, stale components, absent BAG, invalid tick, unknown commission/capital/max
loss, budget excess, unverified signed convention and cross-currency FX gaps block.

## MaterialExecutionDriftPolicy

The versioned policy can bound deterioration in expected PnL/return/probability, CVaR, max loss,
capital, reward/risk, spread, spot, maximum leg-IV change, five-score/execution-quality change and
analysis age. Thresholds are nullable and no investment threshold is invented in code. With no
approved thresholds:

```text
material_drift_status = REQUIRES_POLICY
reprice verdict       = REVIEW_REQUIRED
automatic repricing   = false
```

The D1 policy table is immutable; this patch inserts no approved policy.

## Reanalysis

Material drift creates an immutable `ReanalysisRequest`. The candidate-universe runner must
preserve the original decision, rerun the current canonical universe, store the new decision and
rank/candidate changes, and refuse any implementation that rewrites original artifacts. A newly
dominant candidate does not mutate the old order; it requires a new selection and confirmation.
