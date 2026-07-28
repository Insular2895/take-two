# V11 — Probabilistic Strategy Intelligence & Execution Monitor

## Status and boundary

V11 is an auditable research layer over a completed V10.1 structure report.
It does not construct new option architectures and it does not replace the
QuantLib American pricing controls. It adds conditional evidence, model,
allocation, and monitoring views while preserving `NO_TRADE`.

Its execution boundary is absolute:

- market data may be read through narrow adapters;
- no module can submit, modify, cancel, exercise, roll, or close an order;
- previews set `transmit=false`, `what_if=true`,
  `human_confirmation_required=true`, and `order_capability=forbidden`;
- an injected order-capable adapter is rejected;
- a missing executable combo quote or unsupported what-if is a blocker.

## Inputs and outputs

Required inputs:

- a strict V10.1 `ThesisScanReport`;
- a dated V11 YAML policy;
- optionally, normalized evidence events;
- optionally, aligned point-in-time factor history;
- optionally, explicitly configured read-only data connectors.

Outputs:

- one strict JSON report;
- one Markdown review report;
- one responsive standalone HTML report;
- advisory position-monitor reports when a stored dossier and a current
  snapshot are supplied.

The default fixture run is reproducible and offline:

```bash
ttwo-options intelligence-run \
  --base-report reports/examples/v10_thesis_scan.json \
  --policy configs/intelligence/v11.yaml \
  --events fixtures/v11/events_empty.json \
  --json-out reports/v11/latest.json \
  --markdown-out reports/v11/latest.md \
  --html-out reports/v11/latest.html
```

## Module map

| Module | Responsibility | Explicit non-responsibility |
| --- | --- | --- |
| `schemas` | Strict versioned contracts | Data inference |
| `data_hub` | Provenance, normalization, deduplication, connector status | Orders |
| `bayesian` | Scenario posterior and complete update audit | Calibrating priors |
| `covariance` | Rolling/event/regime covariance, shrinkage, PSD repair | Inventing missing factors |
| `volatility_calibration` | Point-in-time Dupire finite-difference nodes | Global arbitrage-free calibration |
| `stochastic` | Seeded regime/model path ensembles | Claiming causal forecasts |
| `valuation` | Conditional option repricing, exits, path metrics | Replacing V10.1 American controls |
| `validation` | Cost, crisis, CVaR, holdout, and paper gates | Laundering old holdouts |
| `optimizer` | Exact finite integer allocation | Continuous relaxation as final answer |
| `execution` | Read-only combo quote envelope and blocked preview | Broker mutation |
| `monitoring` | Explainable advisory actions and Greek attribution | Automatic exits |
| `reporting` | JSON, Markdown, standalone HTML | Recomputing risk in JavaScript |
| `pipeline` | Deterministic orchestration | Weakening downstream gates |

## Data hub and connectors

Every observation names its series, timestamp, unit, domain, source, and
quality. Every source records provider, retrieval time, URI when available,
terms note, and content hash when available. Required series are checked rather
than silently filled.

Implemented connector boundaries:

- SEC EDGAR submissions and company facts;
- FRED series with `FRED_API_KEY`;
- official Take-Two RSS;
- Google Trends official API through an injected limited-alpha port;
- official or licensed US exchange sessions through an injected calendar port;
- IBKR/OPRA option and combo market-data snapshots through an injected
  market-data-only port;
- local normalized JSON for reproducible fixtures.

The default pipeline seeds spot, FX, rate, dividend, and option-chain
observations from V10.1. It does not open network connections. Unconfigured
connectors appear as `not_configured`, not as successful sources.

## Evidence and Bayesian scenarios

Events are normalized to a finite ontology. A stable `canonical_fact_id`
deduplicates several reports of the same underlying fact. Evidence families
have cumulative weight caps so several correlated articles cannot manufacture
confidence. A contradictory event reverses the configured likelihood signal.

For every accepted or deduplicated event, the report retains:

- prior distribution;
- scenario likelihoods;
- requested and effective evidence weights;
- confidence and evidence family;
- contradiction source identifiers;
- posterior distribution;
- whether deduplication or a family cap applied.

The default priors and likelihood tables are hypotheses in
`configs/intelligence/v11.yaml`. They are not observed frequencies and cannot
be promoted without calibration and out-of-sample review.

## Stochastic ensemble

The pipeline crosses four regimes—neutral, thesis, adverse, rupture—with four
models:

1. geometric Brownian motion;
2. local volatility from a Dupire total-variance finite-difference surface;
3. Heston stochastic volatility with full truncation;
4. Heston with compensated compound-lognormal jumps.

All paths are seeded and reproducible. Regime IV transitions are gradual from
the current observed IV rather than instant time-zero gains. Each
candidate/model/regime group reports expected and median P&L, profit and total
loss probabilities, ×2/×3/×5 probabilities, VaR/CVaR, drawdown, percentiles,
time-to-profit, and early-exit rates.

The path repricer is a conditional Black-Scholes control. The V10.1 QuantLib
American results remain authoritative for current/checkpoint pricing,
early-exercise diagnostics, and contractual edge cases.

## Local volatility and covariance

Dupire calibration operates on the point-in-time V10.1 chain. It differentiates
total variance across maturity and log-moneyness, then replaces unstable nodes
with the corresponding observed IV. A synthetic or sparse chain therefore
returns `partial` and warnings. It does not claim a globally arbitrage-free
surface.

Covariance accepts aligned factor returns and computes:

- trailing 20, 60, and 252 observation windows;
- optional event and current-regime windows;
- a weighted blend;
- diagonal shrinkage;
- symmetric positive-semidefinite eigenvalue clipping;
- correlation and condition-number diagnostics.

If only TTWO history is supplied, the report remains a partial one-factor
estimate and lists the missing factors. No Nasdaq, gaming peer, rate, FX,
volume, IV, OI, sentiment, news, or catalyst series is fabricated.

## Exact constrained allocation

The optimizer enumerates every feasible integer vector in the configured
candidate pool. It enforces:

- whole option contracts;
- EUR budget and maximum loss;
- total contract cap;
- bounded-debit margin;
- V10.1 liquidity/admissibility state.

Its objective combines posterior-weighted mean P&L, variance, adverse/rupture
CVaR, execution risk, and cross-model dispersion. Prudent, balanced, and
aggressive profiles alter only declared coefficients. Cash reserve and the
all-zero `NO_TRADE` vector are always legitimate; capital deployment is never
forced.

Gradient, Hessian, and eigenvalue diagnostics describe only the smooth
mean-variance surrogate. CVaR, execution penalties, and integer feasibility
are evaluated by exact enumeration.

## Promotion gates

A candidate is not promoted merely because a simulation or allocation score
is favorable. The report evaluates:

- spread ×1.5, slippage ×2, and commissions ×2;
- adverse and rupture regimes;
- stress CVaR;
- walk-forward and holdout status;
- paper-monitoring status.

V7–V9 inspected holdouts remain contaminated and are preserved as such.
Promotion stays false until a fresh nested walk-forward sample, untouched
holdout, and paper-trading campaign exist.

## Position dossier

The dossier freezes the initial thesis, invalidation rules, entry economics,
planned partial/full exits, and reference Greeks. A current snapshot produces
one advisory action:

- `conserver`;
- `surveiller`;
- `reduire`;
- `sortir`;
- `these_invalidee`.

The report explains P&L, probability changes, regime change, thesis/market
divergence, and delta/gamma/theta/vega/rho attribution. It never mutates the
broker position.

## Required validation before operational use

1. Freeze a real point-in-time IBKR/OPRA chain with entitlements, `conId`,
   deliverables, simultaneous combo quotes, commissions, margin, and supported
   what-if responses.
2. Calibrate scenario priors/likelihoods and local-vol/Heston/jump parameters
   without look-ahead.
3. Supply aligned factor histories with publication timestamps.
4. Run nested walk-forward, event windows, crisis tests, a new locked holdout,
   and paper trading.
5. Obtain explicit approval for any change to the forbidden execution
   boundary. That change is not part of V11.

## Primary integration references

- [IBKR TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR TWS API reference](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-ref/)
- [IBKR market-data subscriptions](https://ibkrcampus.com/campus/ibkr-api-page/market-data-subscriptions/)
- [OPRA plan](https://www.opraplan.com/)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC fair-access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/overview.html)
- [Google Trends API alpha](https://developers.google.com/search/apis/trends)
- [Take-Two Investor Relations RSS](https://ir.take2games.com/rss-feeds/)
- [QuantLib](https://github.com/lballabio/QuantLib)
- Bruno Dupire, “Pricing with a Smile,” *Risk*, 1994.
