# M0.1 Final Pre-OPRA Correction Report

Generated: 2026-08-24

Branch: `codex/v10-quantitative-validation-and-robust-decision-engine`

Base inspected: `9b8842e`

## Outcome

```text
M0_1_STATUS = COMPLETE
PRE_OPRA_LOGIC_STATUS = COMPLETE
NEXT_PHASE = M — OPRA READ-ONLY LIVE DATA + SHADOW/PAPER VALIDATION
```

This status covers offline trade-economics logic only. The final holdout remains `UNOPENED`, OPRA
remains `NOT_STARTED`, and no provider session, shadow mode, paper campaign or order capability was
started.

## State before correction

The M0 implementation already contained full repricing, advanced Greeks, carry, scenario matrices,
breakeven solving and attribution. The pre-patch audit found misleading midpoint premium labels,
closing costs at expiration, incomplete human theta output, no distribution-PnL contract, no
five-score ticket bridge, DTE-only event crush and an implicit/incomplete mixed-expiry lifecycle.
The detailed evidence is in `docs/audits/M0_1_FINAL_CORRECTION_AUDIT.md`.

## Seven corrections

| # | Correction | Final status | Implemented result |
| ---: | --- | --- | --- |
| 1 | Midpoint versus executable premium | `COMPLETE` | Per-leg and aggregate midpoint paid/received/net are distinct from ask-paid/bid-received/net. Signed reconciliation proves spread is counted once. |
| 2 | Expiration versus closing costs | `COMPLETE` | Scenario/breakeven rows expose exit path and applied cost. Common expiration uses intrinsic plus known expiry fees and excludes option-closing spread/slippage/commission. |
| 3 | Human theta/carry output | `COMPLETE` | Renderer exposes theta/capital/day, 1/7/30/60/90-day carry in currency and percentages, decay rates, acceleration and the full-repricing warning. |
| 4 | Distribution PnL metrics | `COMPLETE` | Typed expected/median net PnL/return, gain/loss probabilities, positive-loss VaR/CVaR, ESS, intervals and model metadata require full economic paths or an explicit IV valuation rule. |
| 5 | Canonical five-score bridge | `COMPLETE` | The exact five dimensions are copied without a new formula. Candidate versus run-global scope is explicit, and an optional canonical ranked order controls deep-ticket selection. |
| 6 | Event-date-aware IV crush | `COMPLETE` | Event timing, option-expiry eligibility and event-to-expiry buckets control the shock; generic no-date stress is explicitly labeled. |
| 7 | Mixed-expiry lifecycle | `COMPLETE` | Sole policy is configurable `CLOSE_BEFORE_FIRST_EXPIRY`; scenarios clip, terminal roots are managed-exit roots, targets cannot pass the deadline and the post-expiry omission is explicit. |

## Schema and artifacts

- `TradeEconomicsTicket` is now schema `1.1`; legacy `1.0` fields remain readable.
- Tickets enforce `read_only=true`, `transmit=false`, `what_if=true` and
  `order_capability=forbidden`.
- `schemas/trade_economics_ticket.schema.json` and `schemas/pre_opra_config.schema.json` were
  regenerated from the typed contracts.
- The main synthetic JSON/Markdown golden shows midpoint/executable entry economics, both close and
  hold-to-expiry paths, full theta/carry output, statistics availability and all five scores.
- `reports/examples/m0_1_probability_distribution_fixture.json` separately demonstrates a
  synthetic equal-weight `P` distribution under the declared constant-leg-IV rule.

## Verification

| Check | Result |
| --- | --- |
| `pytest -q` | `287 passed`, one third-party `websockets.legacy` deprecation warning |
| `ruff check .` | passed |
| `mypy src scripts` | passed, 186 source files |
| schema export/check | 27 schemas exported and verified |
| offline artifact validation | passed; calibration/walk-forward remain fixture-only; order capability forbidden |
| golden regeneration | deterministic; all three artifact SHA-256 hashes unchanged on immediate regeneration |
| focused M0.1 tests | 26 passed |

## Remaining limitations

- `PENDING_OPRA`: live NBBO, quote freshness, sizes/depth, provider Greeks and contract discovery.
- `PENDING_BROKER`: simultaneous combo quote, broker margin and account commission preview.
- `PENDING_PAPER`: realized fills, real exit spread/slippage, prospective PnL, score calibration,
  touch/distribution calibration and proof of V10 strategy superiority.
- Exercise, assignment, settlement, FX or margin inputs that are economically applicable but
  unknown remain null/blocked.
- The mixed-expiry engine intentionally stops before the first expiry and does not model later
  assignment, stock delivery, structure transformation or cash management.
- Expected PnL is model-implied under declared assumptions, never a revenue promise.

## Safety stop

No order submit/modify/cancel, automatic exercise/assignment, roll, hedge or trading automation was
added. M0.1 stops here; Phase M is not started by this report.
