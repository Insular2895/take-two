# Product contract

## Input

One strict `TradeRequest` describes ticker, dated budget/FX, maximum loss,
thesis and invalidation, economic horizon, catalysts, allowed bounded-risk
structures, liquidity/execution policies, maintenance preferences, and locked
holdout policy. It never preselects a winning strike, expiration, target, stop,
or architecture.

## Decision

The engine must:

1. load and validate structured knowledge and modern-validation records;
2. compile only non-conflicted, provenance-aware recipes;
3. enumerate multiple whole-contract structures from actually listed quotes;
4. use ask for long entry, bid for short entry, and explicit costs;
5. veto unknown/unbounded risk, budget, horizon, liquidity, data, and broker
   failures before simulation or scoring;
6. keep simulation models separate and expose dispersion;
7. preserve every configured observation minimum;
8. use hard vetoes, then Pareto, then a visible secondary score;
9. return an explicit wait/no-trade/blocked verdict when evidence is lacking.

## Output

`reports/latest/` contains canonical JSON, Markdown, standalone HTML, SVG
figures, a trial registry, configuration/data audit, and either an admissible
preview ticket or a blocked-ticket status. No file is an order instruction.

## Safety boundary

There is no broker trading client in the active pipeline. Preview artifacts set
`transmit=false`, require human confirmation, leave IBKR `con_id` unresolved,
and cannot be generated for blocked candidates.
