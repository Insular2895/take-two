# CF0 candidate filter, sort, and heatmap semantics

Status: implemented locally on 2026-08-25.

## Complete universe

The Python enumerator returns every combination admitted by the compiled `StrategyCatalog`, the
`TradeRequest`, the listed snapshot, and whole-contract sizing. Hard-vetoed candidates remain
persisted with reasons. D1 stores one compact summary and one structured detail document per
candidate. Every returned summary therefore has a detail route.

Views are projections, not storage caps:

- `BEST OVERALL`: immutable engine ranks 1–25;
- `BY ARCHITECTURE`: lowest engine rank per architecture;
- `TOP`: immutable engine ranks 1–100;
- `ALL`: every summary;
- `PAPER ELIGIBLE`: `paper_eligible=true`;
- `RESEARCH ONLY`: research eligible but not paper eligible.

## Two independent ranks

`engine_rank` is written by Python and never recomputed by the browser. Its current pre-evaluation
method is `HARD_VETO_PARETO_BUDGET_DISTANCE_V1`: hard-veto status, paper eligibility, canonical
Pareto rank, absolute distance from target budget, maximum loss, then candidate ID. This is not a
sixth score. Missing simulation metrics are not converted into fake zeros.

The user-selected sort is ephemeral UI state. It can reorder cards but cannot update D1 or alter
`engine_rank`.

## Metric catalogue

| Metric | Direction |
|---|---|
| engine rank | lower is better |
| capital required | neutral; user direction controls |
| maximum loss | lower is better |
| maximum gain | higher is better |
| probability profit | higher is better |
| expected PnL | higher is better |
| CVaR 95 | lower is better |
| net delta, gamma, vega, DTE, IV | neutral; user direction controls |
| maximum relative spread | lower is better |

## Dynamic heatmap

The algorithm is deterministic:

1. apply active view, architecture, and budget-status filters to the full summary array;
2. sort that visible array using the active user metric, with null/non-finite values last;
3. compute tied percentiles from finite values in that visible post-filter array;
4. invert percentiles for lower-is-better metrics;
5. for neutral-direction metrics, use the user-selected ascending/descending direction;
6. map percentiles to six deterministic bands: strongest green, green, light green, yellow,
   orange, red;
7. keep `N/A` visually neutral;
8. paginate only after filtering, sorting, and percentile calculation.

Color is not the only signal: every highlighted cell names the metric and prints `HIGHER`, `LOWER`,
or `NEUTRAL`; the numeric or `N/A` value remains visible.

## Comparison

The compare set is client-side, limited to four candidate IDs, and displays raw metrics only. It
does not calculate a composite score, mutate rank, or select a candidate.
