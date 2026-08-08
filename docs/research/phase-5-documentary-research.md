# Phase 5 documentary research — path exits and Monte Carlo uncertainty

Date: 2026-08-08
Status: `sourced_and_implemented_no_empirical_promotion`

## Conclusions

- An exit policy is a stopping rule on the information available at each checkpoint. The engine
  now records the complete state after each observation and rejects non-chronological or
  post-terminal transitions. This prevents the implementation from consulting a future path
  value, but daily checkpoints can still miss an intraday threshold crossing.
- Glasserman chapter 4 defines a control-variate observation as
  `Y - b * (X - E[X])`; the variance-minimising coefficient is
  `Cov(X,Y) / Var(X)` (printed pp. 186–187). Estimating that coefficient from the same sample is
  asymptotically valid, with explicit small-sample caveats (printed pp. 195–201).
- Antithetic outputs must be averaged by pair and the number of independent replications is the
  number of pairs, not the number of paths. Variance improves only when the paired outputs are
  negatively correlated (Glasserman, printed pp. 205–207).
- A zero observed rare-event count is not a zero-risk proof. Every unweighted canonical path
  probability now has a Wilson interval, effective sample size and explicit minimum-path flag.
  Weighted paths expose ESS but deliberately receive no binomial Wilson interval because they
  are not iid Bernoulli trials.
- Ordinary iid bootstrap is unsuitable when time-series dependence matters. The implemented
  circular moving-block bootstrap resamples contiguous blocks and records block size, sample
  count and seed. Block-length choice remains a sensitivity parameter, not a fitted truth.

## Sources inspected

- Paul Glasserman, *Monte Carlo Methods in Financial Engineering*, Springer, 2004, chapter 4,
  especially sections 4.1–4.2, printed pp. 186–207; chapter 8 table-of-contents and optimal
  stopping boundary also inspected. The two local files are treated as copies of one work.
- Leif B.G. Andersen and Vladimir V. Piterbarg, *Interest Rate Modeling*, Volume I, chapter 3,
  especially the already-inspected discretisation material around printed p. 106.
- Hans R. Künsch, “The Jackknife and the Bootstrap for General Stationary Observations,”
  *The Annals of Statistics* 17(3), 1989, pp. 1217–1241, DOI
  `10.1214/aos/1176347265`; primary bibliographic metadata and abstract inspected.
- Emmanuelle Clément, Damien Lamberton and Philip Protter, “An analysis of the
  Longstaff-Schwartz algorithm for American option pricing,” Cornell ORIE Technical Report
  1296, 2001 / *Finance and Stochastics* 6, 2002. The local PDF exists but is not text
  extractable; Cornell primary metadata was inspected.

The local PDFs remained read-only. External access was used only for bibliographic metadata
where the local Longstaff-Schwartz file could not be reliably extracted.

## Implementation and validation

- `ExitMachineState` is immutable and JSON-serializable. Profit target, stop loss and final-time
  priority exactly preserve the previous path engine; fees and slippage are still charged once
  at entry and once at exit.
- Control-variate and antithetic reports retain baseline/adjusted replication variance,
  standard error, independent-replication count and measured reduction factor. Synthetic tests
  demonstrate reduction; the API does not claim that every control or antithetic pairing helps.
- Probability sidecars cover all seven canonical P&L probabilities plus take-profit and stop
  frequencies. They do not alter the historical `ModelMetrics` serialization.
- The block bootstrap is seeded and deterministic. The discretisation comparator reports exit
  reason/day mismatches and P&L gaps between aligned coarse and fine checkpoint runs.
- LSM is deferred. The repository already has an American finite-difference engine and no
  measured, material FD/checkpoint discrepancy on a real point-in-time TTWO panel. Implementing
  a regression stopping model before that evidence would add basis-selection and path-reuse
  risk without satisfying the phase gate.

## Limits

- Daily exit observations cannot establish intraday execution or threshold order.
- Wilson coverage assumes unweighted iid Bernoulli trials; serial or common-random-number
  dependence needs a design-specific interval.
- ESS is a concentration diagnostic, not a proof of independence or tail coverage.
- Percentile block-bootstrap intervals depend on stationarity, block length and sample size.
- No rare-event importance-sampling scheme is implemented; insufficient tail paths stay
  explicitly insufficient.
- Synthetic variance reduction and state-machine tests are numerical checks, not real TTWO
  empirical validation.
