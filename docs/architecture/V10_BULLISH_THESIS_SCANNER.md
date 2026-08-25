# V10.1 Bullish Thesis Scanner

## Purpose

`ttwo-options thesis-scan` converts a user-supplied bullish thesis into an
auditable option-structure comparison. It does not decide that the thesis is
true and does not authorize a trade.

The path is separate from the generic V9-compatible decision pipeline, so all
existing commands and report contracts remain available.

## Contracts and data flow

```text
CLI
 └─ ThesisScanRequest
     ├─ dated budget, maximum loss, catalyst and targets
     ├─ optional user probabilities
     └─ chain path / optional explicit spot
          |
          v
 ThesisChain normalizer
 ├─ native thesis_chain_v1
 ├─ MarketSnapshot
 └─ AlpacaOptionChainExport + look-ahead-safe spot or --spot
          |
          v
 Explicit hard filters
 ├─ quote timestamps and maximum age
 ├─ bid/ask validity and relative spread
 ├─ catalyst + expiration buffer
 ├─ strike moneyness window
 ├─ known OI/volume threshold breaches
 ├─ multiplier / standard-contract checks
 └─ dated FX / bounded maximum loss / EUR budget / debit-only margin rule
          |
          v
 Exhaustive configured construction
 ├─ long_call (standard or LEAPS maturity class)
 ├─ bull_call_spread
 └─ symmetric call_butterfly
          |
          v
 Shared QuantLib finite-difference American engine
 ├─ net Greeks
 ├─ today, +30, +60, +90, catalyst, expiry
 ├─ automatic spot grid + user targets
 ├─ IV down / stable / up
 ├─ terminal payoff
 └─ underlying / time / IV / execution attribution
          |
          v
 Three independent deterministic rankings
 ├─ prudent
 ├─ balanced
 └─ aggressive
          |
          v
 V10.1 decision metrics computed in Python
 ├─ contractual vs modeled gain kept separate
 ├─ exact terminal ×2 / ×3 / ×5 value thresholds
 ├─ target P&L table in USD and EUR
 ├─ measurable execution and structure risks
 └─ no user probability means expected values remain null
          |
          v
 JSON + Markdown + accessible standalone HTML + IBKR preview-only tickets
```

## Enumeration boundary

“All reasonable combinations” is finite and versioned by
`configs/thesis_scanner/default.yaml`: moneyness range, maximum vertical width,
maximum symmetric butterfly wing, whole-contract limit, quote spread, OI,
volume, costs, FX, and catalyst buffer. The scanner records counts for every
generated architecture and every hard rejection. It never relaxes a threshold
to force a result.

Missing OI/volume or unconfirmed deliverable is preserved as a warning when the
value is genuinely unavailable. A known failure is blocked. Credit structures
or combinations whose margin cannot be bounded from the listed payoff are
blocked by the debit/margin rule.

## Pricing and risk

Long entries use ask; short entries use bid. The report also shows the
diagnostic synthetic midpoint. Fees and configured slippage are added to total
cost and maximum loss. USD values are converted with the dated USD-per-EUR
rate in policy.

Pre-expiry values call the same cached QuantLib American finite-difference
engine used elsewhere in the repository. Expiry uses exact terminal payoff.
Every scenario contains a reconciliation:

```text
P&L = underlying effect + time effect + IV effect + execution effect + residual
```

Residual is a numerical check, not a new source of P&L.

## Ranking

The three weight vectors are visible in policy. Each criterion is normalized to
`[0, 1]`; every output includes the complete criterion map, score, top reasons,
and invalidation conditions. Ties are broken by score, lower maximum loss, then
stable candidate ID. Rankings do not share an optimized score.

V9 evidence is deliberately represented as `historical_confidence: 0.35`.
That penalty participates in each score but does not become an automatic
thesis-mode blocker.

`request.top` is applied after each independent deterministic sort. The report
therefore contains at most N scores per profile and the HTML renders those
arrays directly; it does not hard-code three cards. A candidate may occur in
more than one profile without duplicating candidate calculations.

## V10.1 dashboard contract

The primary navigation is three accessible accordion columns. Opening one row
closes the other open row in that profile, selects the candidate, and refreshes
the existing legs, ticket, costs, Greeks, liquidity, payoff, date curves,
heatmap, IV, P&L, and risk views. Native buttons expose `aria-expanded`,
`aria-controls`, labelled regions, keyboard activation, and visible focus.

Every accordion panel uses `StructureDecisionMetrics`, calculated before report
serialization. This keeps JavaScript presentation-only. Contractual gain and
best modeled gain are distinct. Terminal ×2/×3/×5 thresholds solve for gross
position value using the configured initial total cost:

```text
×2 value = 2 × initial total cost
net profit at ×2 = 1 × initial total cost
```

No unconfigured exit fee is added. A capped structure reports an unattainable
multiple explicitly. Butterflies can return two terminal spot solutions around
their center strike.

## Security boundary

The V10.1 package imports no broker trading client. Preview objects can only be
`transmit=false`, `what_if=true`, and `order_capability=forbidden`. The HTML is
self-contained, performs no network request, uses text-only DOM insertion for
report data, and exposes no order button.

## Validation

`tests/test_thesis_scanner.py` covers the required universe, EUR budget, exact
terminal and modeled pre-expiry P&L, IV cases, risk and break-even, deterministic
rankings, stale/invalid quote rejection, absent probabilities, preview-only
security, and full fixture-to-dashboard generation.
