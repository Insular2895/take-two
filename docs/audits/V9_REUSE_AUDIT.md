# V9 reuse audit for the V10 Bullish Thesis Scanner

Audit date: 2026-07-25

Post-consolidation note (2026-08-30): this document records the V9-to-V10 decision made at the
time. The former active `scoring.py` implementation has now been migrated and deleted. Current
decisions use structural vetoes, explicit eligibility, Pareto filtering and only then an
explanatory ranking from `decision/ranking.py`; archived V9 artifacts remain historical only.

## Scope inspected

- V9 generator fixture, architecture note, known limits, testing strategy,
  Markdown report, dashboard artifact, and SQL source under
  `experiments/legacy/v9/` and `docs/archive/v9/`.
- Active and legacy implementation in `pricing.py`, `american.py`,
  `scenarios.py`, `scoring.py`, `accuracy.py`, `marketdata_panel.py`,
  `strategy_architectures.py`, and `accuracy_dashboard.py`.
- Current knowledge-driven candidate generator, hard vetoes, read-only CLI,
  report contracts, and contaminated-holdout manifest.

## V9 behaviors that remain legacy-only

- `single_long`, `staged_three`, fixed EUR 310/245/445 buckets;
- fixed delta/moneyness profiles, DTEs, profit targets, stops, and holding
  periods;
- `LEAPS_CALL` as a separate architecture;
- reused V7-V9 holdouts as an eligibility gate;
- a single ranking intended to decide whether a strategy was historically
  validated.

The V10 scanner does not import those assumptions. Historical V9 outcomes are
shown as confidence warnings only.

## Reusable implementation

| Module | Reused capability | V10 decision |
| --- | --- | --- |
| `pricing.py` | executable ask/bid sides, midpoint, fees, slippage, terminal payoff, break-even, bounded max gain/loss, net Greeks | Reuse the mechanics; do not fork a payoff engine. |
| `american.py` | QuantLib finite-difference American valuation and Greeks | Add one explicit primitive-input facade, backed by the existing cached QuantLib engine, for price/date/IV scenario grids. |
| `scenarios.py` | pre-expiry repricing and sequential spot/theta/IV/rate/cost attribution | Reuse the attribution method and model semantics in the V10 report contracts. |
| `scoring.py` (historical; deleted 2026-08-30) | deterministic decomposed score and Pareto-first discipline | Preserve only the Pareto-first principle; active explanatory ranking lives in `decision/ranking.py` and cannot become a second authoritative score. |
| `accuracy.py` | historical warning summaries and current-chain orchestration patterns | Read historical results as warnings; never let weak reused holdouts become fresh evidence. |
| `marketdata_panel.py` | quote screening, OCC leg construction, executable side selection, risk and cost calculations | Reuse normalized quote and risk conventions; exhaustive enumeration replaces profile selection. |
| `strategy_architectures.py` | human-readable structure mechanics, limitations, entry and exit descriptions | Reuse descriptions. Treat “LEAPS call” as a long-call maturity label, not a duplicate architecture. |
| `accuracy_dashboard.py` | compact IBKR-readable legs, explicit blockers, source-backed dashboard rows | Reuse the presentation principles, not the long concatenated cells. |

## Preserved compatibility

- The active `knowledge`, `data`, `trade`, and `position` commands remain
  unchanged.
- The hidden `legacy` command group remains available for V1-V9 reproduction.
- Existing reports and archived V9 artifacts are not overwritten.
- The V10 command writes only to paths explicitly supplied by the user.

## Data boundaries carried into V10

- Alpaca `indicative` is not OPRA and does not contain open interest or
  contract deliverables.
- OPRA labels are accepted only when they are present in source metadata.
- MarketData.app historical chains are EOD leg markets, not simultaneous combo
  quotes or intraday NBBO replay.
- A midpoint is theoretical; conservative entry uses long ask and short bid.
- A leg-by-leg combo debit is not a guaranteed broker fill.
- Unknown multiplier, adjusted deliverable, stale FX, incoherent quotes, or
  unknown risk remains visible as a hard blocker or explicit watchlist reason.

## V10 architecture boundary

The scanner accepts the bullish direction as user input. It compares how
bounded-risk call structures express that assumption across user-supplied
prices, dates, and IV states. It does not forecast TTWO, invent scenario
probabilities, authorize an order, or convert a weak backtest into a hard
directional veto.
