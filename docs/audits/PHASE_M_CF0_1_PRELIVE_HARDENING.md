# Phase M-CF0.1 pre-live hardening audit

Date: 2026-08-24

## Initial audit

Two correctness gaps were confirmed:

1. the Worker classified freshness from `ProviderSnapshot.timestamp`, populated from the TTWO
   underlying timestamp, even when a required option, FX, or used combo input was older;
2. `actual_entry_cash` was required positive and reused as entry cash flow, risk capital, return
   denominator, and PnL subtraction basis. Combo and manual fills were also assumed to produce
   proceeds.

No quantitative model, five-score formula, budget policy, Phase M context, Access policy, or order
capability required modification.

## Corrections

| Area | Result | Evidence |
|---|---|---|
| Required-data freshness | `PASS` | Oldest required underlying/option/FX/used-combo timestamp controls status. |
| Future timestamps | `PASS` | More than five seconds ahead yields `INVALID` and `MARKET_TIMESTAMP_FROM_FUTURE`. |
| Rule order | `PASS` | Invalid/insufficient and stale data return before economic rules. |
| Signed entry economics | `PASS` | Dossier 1.1 receipt-positive `entry_cash_flow_policy`. |
| Capital separation | `PASS` | `capital_required_policy` comes from governed diagnostics and never enters PnL sums. |
| Signed close economics | `PASS` | Combo and manual fills require `CREDIT`/`DEBIT`; costs reduce both directions. |
| Partial close | `PASS` | Entry cash flow allocated pro rata for debit and credit structures. |
| Legacy behavior | `PASS` | Proven synthetic 1.0 debit adapter preserves the €432 CF0 estimate; unknown 1.0 sign fails closed. |
| D1 | `PASS` | Additive migrations, safe synthetic debit backfill, unknown legacy reconciliation, immutable previews. |
| UI | `PASS` | Neutral close-cash-flow wording and oldest-required-input age; no redesign. |

## Acceptance economics

- Debit fixture: entry flow `-1023`, capital `1023`, mark `+1487`, MTM PnL `+464`, estimated close
  cash flow `+1455`, liquidation PnL `+432`.
- Credit fixture: entry flow `+300`, capital `700`, mark `-120`, MTM PnL `+180`, estimated gross
  close `-100`, costs `5`, net close cash flow `-105`, liquidation PnL `+195`.
- Losing credit close: `+300 - 650 - 10 = -360`.
- Manual credit reconciliation: `+300 - 100 - 2 = +198`.
- Two-lot partial credit close: allocated entry `+300`, signed close `-115`, realized `+185`, one
  lot retains `+300` of opening cash flow.

## Validation

The final report records the actual full-suite counts. Ruff, mypy, deterministic schema validation,
offline artifacts, research registry, Phase 10 release audit, Cloudflare TypeScript/Vitest/safety
scan, local D1 migrations, and Wrangler dry-run all pass.

The recorded M0, M0.1, M0.2, M0.2.1, and golden ticket hashes are unchanged. Holdout status remains
`UNOPENED`.

## Remaining dependencies

- live read-only market-data provider and verified quote semantics;
- point-in-time option, FX, and combo timestamp provenance;
- OPRA entitlement and legal data-use confirmation;
- broker read-only sync and observed fills;
- later, separately authorized shadow and paper validation.

No remaining dependency is represented as complete.
