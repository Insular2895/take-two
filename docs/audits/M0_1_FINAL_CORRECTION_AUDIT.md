# M0.1 Final Pre-OPRA Correction Audit

Audit date: 2026-08-24

Repository: `Insular2895/take-two`

Branch: `codex/v10-quantitative-validation-and-robust-decision-engine`
State inspected: commit `9b8842e`

This audit was completed before the M0.1 business-code patch. It evaluates only the offline,
read-only trade-economics layer. The final holdout remains `UNOPENED`, Phase M OPRA remains
`NOT_STARTED`, and no order, exercise, assignment, roll, hedge, or broker-session capability is in
scope.

## Findings

| # | Required correction | Status before M0.1 | Evidence |
|---:|---|---|---|
| 1 | Theoretical midpoint premium versus executable bid/ask premium | `CONFIRMED` | `estimate_execution()` correctly uses ask/bid in aggregate cash cost, but `ExecutionEstimate.premium_paid`, `premium_received`, `LegEconomics.premium_paid`, and `premium_received` are midpoint amounts. The renderer therefore labels the long-call midpoint premium as paid. |
| 2 | Exit costs and expiration breakeven | `CONFIRMED` | Scenario cells, target arrival, and `build_breakeven_clock()` subtract the configured close-out spread, slippage, and commission at every horizon, including expiration. The golden expiration root therefore does not reconcile to the contractual payoff breakeven. No exit-path field exists. |
| 3 | Full theta/time-decay visibility | `PARTIAL` | `TimeDecayExposure` already contains theta/capital, carry percentages, decay rates, acceleration values, and status. The Markdown renderer exposes only current theta, absolute carry values, and the acceleration status. |
| 4 | Distribution PnL metrics | `CONFIRMED` | The ticket exposes pathwise touch metrics only. It has no typed expected/median net PnL, return, gain/loss thresholds, VaR/CVaR, ESS, assumptions, or strict state-path availability contract. |
| 5 | Canonical five-score bridge | `CONFIRMED` | Canonical `FiveScoreReport`/`QualityScore` contracts and the committed pre-OPRA five-score artifact exist, but `TradeEconomicsTicket` has no score snapshot. The existing committed artifact is scoped to `engine_candidate`, not silently attributable to every generated strategy candidate. |
| 6 | Event-date-aware `EVENT_IV_CRUSH` | `CONFIRMED` | `relative_to_event_date` exists in configuration, but `_scenario_volatility()` buckets event crush from valuation-time DTE only and does not expose event date/status/tenor/shift in cells. |
| 7 | Mixed-expiry calendar/diagonal lifecycle | `PARTIAL` | Carry and scenario horizons are clipped to the earliest expiration, with one warning, but there is no explicit lifecycle policy, configurable close buffer, managed-exit deadline, clipped-horizon status, managed-exit breakeven label, or target-arrival guard. |

## Corrective constraints

- Preserve all ticket 1.0 fields as readable compatibility aliases while publishing ticket schema
  `1.1` for newly built artifacts.
- Do not double count midpoint-to-executable spread economics.
- Apply close-out costs only to an explicit `CLOSE_BEFORE_EXPIRY` or managed-close path.
- Keep unknown exercise/assignment/settlement and FX costs null; never coerce them to zero.
- Compute probabilistic PnL only from full economic paths or spot paths with an explicit future-IV
  valuation rule. A spot path alone does not authorize expected PnL.
- Copy canonical score outputs; do not define a new score formula in the trade-economics module.
- Use `CLOSE_BEFORE_FIRST_EXPIRY` as the sole M0.1 mixed-expiry policy and do not model post-expiry
  lifecycle transformations.
- Keep `transmit=false`, `what_if=true`, and `order_capability=forbidden`.

## Pre-patch conclusion

`M0_1_INITIAL_STATUS = CORRECTIONS_REQUIRED`

The seven audit findings are actionable without opening the holdout, connecting OPRA, changing
historical OOS artifacts, or introducing execution capability. Implementation proceeds
automatically under the constraints above.
