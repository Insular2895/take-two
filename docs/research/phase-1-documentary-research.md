# Phase 1 documentary research — conventions, measures, numerical audit

Date: 2026-08-08
Status: `sourced_and_implemented`

## Immediate conclusions

1. The code must distinguish empirical dynamics under `P` from arbitrage pricing under `Q`.
   Björk defines an equivalent martingale measure in chapter 10.2 (printed p. 141) and gives
   the discounted risk-neutral valuation formula and Black–Scholes `Q` dynamics in chapter
   12.2 (printed pp. 175–176). Andersen–Piterbarg maps the same boundary in sections 1.3 and
   4.2.1 (printed pp. 8 and 170).
2. Calendar time and return sampling are different conventions. The engine therefore uses
   Actual/365 Fixed for option time and 252 sessions only for empirical annualisation. The
   rate-model source explicitly separates measure and day-count material (Andersen–Piterbarg,
   Vol. I, sections 4.2.1 and 5.A, printed pp. 170 and 221–223).
3. A numerical claim needs both absolute and scale-aware relative error. Süli–Mayers treats
   robust bracketing in section 1.6 (printed p. 28), global behaviour in 1.7 (p. 29), and
   absolute/relative conditioning in 2.7 (pp. 58–71). A finite-difference output also needs a
   refinement sequence; one grid value is not convergence evidence.

## Local sources inspected

- Tomas Björk, *Arbitrage Theory in Continuous Time* (local PDF), chapters 10.2 and 12.2,
  printed pp. 141 and 175–176.
- Leif B.G. Andersen and Vladimir V. Piterbarg, *Interest Rate Modeling*, Vol. I (local
  fragments), table of contents and sections 1.3, 2.3, 3.2.2, 4.2.1 and 5.A, printed pp. 8,
  52, 106, 170 and 221–223.
- Endre Süli and David F. Mayers, *An Introduction to Numerical Analysis*, Cambridge
  University Press, 2003 (local PDF), title/copyright pages and sections 1.6, 1.7 and 2.7,
  printed pp. 28–29 and 58–71.

Extraction used local `pdftotext` output only; the source PDFs were not modified. Formula
locations and code/test mappings are in `formula_registry.yaml`.

## Alternatives and rejected shortcuts

- A single annual basis for everything was rejected because option maturity and observed
  trading-session variance are different quantities.
- A free string such as “risk-neutral drift” was rejected as the only P/Q protection; runtime
  contracts now reject incompatible purposes.
- Exact float equality across pricers was rejected; the harness records absolute error,
  relative error, both tolerances, and status.
- One high-resolution QuantLib value was not called “converged”; a separate grid-refinement
  report is required.

## Limits

- The new tags cover the shared and active path objects but do not rewrite every legacy
  serialized schema. Compatibility reports remain unchanged.
- The property test cross-checks European Black–Scholes against QuantLib finite differences;
  it does not prove every American configuration.
- Actual/365 Fixed is the current product convention, not a universal market convention.
- No predictive or holdout claim is created by this phase.
