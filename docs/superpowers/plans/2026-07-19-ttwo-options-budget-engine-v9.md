# TTWO Options Budget Engine V9

Status: implemented, source-backed, no-trade retained.

## Scope

1. Add a dated EUR/USD conversion and a hard EUR risk cap to panel specifications.
2. Apply the cap to historical cases and the current-chain scan.
3. Compare one EUR 1,000 long-dated trade with EUR 310/245/445 short/medium/long pockets.
4. Preserve liquidity, statistical, holdout and bounded-risk gates.
5. Put the budget comparison first in the portable dashboard.
6. Validate models, tests, canonical artifact and desktop/mobile HTML delivery.

## Acceptance

- No historical case above its EUR pocket contributes to metrics.
- No current structure above its EUR pocket can become eligible.
- Empty pockets remain explicit and do not trigger relaxed liquidity filters.
- Dashboard rows expose readable legs, indicative debit, modeled risk in USD/EUR, scenario and
  blockers.
- Report remains read-only and cannot submit orders.
