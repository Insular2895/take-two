# TTWO Options Opportunity Engine V8

## Objective

Turn the V7 single-expiry option panel into a read-only opportunity workbench that:

- compares a broader set of explicitly defined option architectures;
- supports path-dependent profit targets and stop losses using historical EOD bid/ask;
- keeps portfolio-dependent and unbounded-risk structures visible but blocked;
- separates current opportunities, historical winners, and the full audit trail in HTML;
- preserves purged chronological splits, multiple-testing diagnostics, and no-trade.

## Safety boundary

- No broker order, position, account, sizing, or exercise endpoint.
- Only bounded-risk, self-contained option structures may enter the historical panel.
- Covered/protective structures remain catalog-only until a real portfolio state is supplied.
- Naked short gamma and structures with potentially unbounded loss remain risk-disabled.
- A reused holdout is exploratory and cannot produce an `eligible` status.

## Architecture catalog

Backtest-capable in V8:

- long call and long put;
- bull call and bear put verticals;
- long straddle and long strangle;
- call and put butterflies;
- iron condor;
- long call calendar and call diagonal;
- LEAPS call and LEAPS put recipes.

Catalog-only:

- protective put, covered call, collar/fence, gamma scalping.

Risk-disabled:

- short straddle, short strangle, ratio spread, naked ratio backspread.

## Implementation sequence

1. Add a typed architecture registry with documentary readiness and data requirements.
2. Extend panel legs with quantities and add multi-leg/multi-expiry selection.
3. Add moneyness selection, wing width, front-expiry target, and path exit policies.
4. Normalize returns by bounded risk capital, including credit structures.
5. Add market regime descriptors and reused-holdout governance.
6. Rebuild the canonical dashboard around current opportunities, historical winners,
   architecture coverage, risk/return diagnostics, and detailed legs.
7. Add focused unit tests, run the full quality suite, then run a source-backed V8 panel.

## V8 reference recipes

- `leaps_put_110_tp80`: buy a put near 110% of spot, target about 365 DTE, exit at the
  first EOD executable net return of +80%, at the configured stop, or at the time limit.
- `call_butterfly_atm`: buy one lower call, sell two center calls, buy one upper call,
  with one expiry and approximately symmetric wings.
- `iron_condor_delta`: buy outer put/call wings and sell inner OTM put/call options,
  with bounded terminal risk and return normalized by maximum loss.
- `long_call_calendar`: buy a back-month call and sell a same-strike front-month call;
  the planned exit must precede the short option expiry.

## Validation evidence

- Selection tests assert exact side, option type, strike ordering, expiry ordering, and quantity.
- Exit tests assert that the first historical EOD threshold crossing is used.
- Credit-risk tests assert that maximum bounded loss, not net credit, is the denominator.
- Governance tests assert that reused holdout data cannot authorize an eligible candidate.
- Dashboard tests assert dedicated opportunity, winner, and architecture datasets.
- Desktop and mobile portable HTML are visually checked after artifact generation.

## Known interpretation limits

- EOD threshold crossing does not prove an intraday fill at the threshold.
- Multi-leg exits are synthetic simultaneous executable-side marks, not broker combo quotes.
- One year of free option history is not enough to establish durable predictive accuracy.
- The architecture catalog is broader than the validated strategy set by design.
