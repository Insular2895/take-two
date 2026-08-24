# Limitations

## M0 Greeks, carry and trade economics

- M0 full-repricing mechanics, advanced Greeks, carry curves, scenario matrices, breakeven clocks,
  round-trip architecture, FX decomposition and typed tickets are complete offline. This validates
  software behavior on deterministic/synthetic inputs, not a trading edge or market calibration.
- The QuantLib American FD engine is date-based. Exact timestamps and DTE are preserved, but
  American intraday outputs are `APPROXIMATED_DATE_ENGINE` and become
  `INSUFFICIENT_NEAR_EXPIRY` inside the configured threshold.
- Future IV transformations are `CONFIGURED_STRESS`. Without a valid supplied surface they remain
  `LEG_LEVEL_STRESS_ONLY`; they are not forecasts of skew, term structure or event crush.
- Exit spread, exit slippage and closing costs are configured estimates. Real NBBO, simultaneous
  combo execution, fill quality, market depth and prospective slippage remain `PENDING_OPRA` or
  `PENDING_PAPER_VALIDATION`.
- Hold-to-expiry economics never charge an option-closing spread, slippage or commission. Known
  exercise/assignment/settlement fees are applied only when relevant; unknown applicable fees
  block the affected PnL/root. Broker-specific delivery, exercise and assignment outcomes remain
  `PENDING_BROKER`.
- Broker margin remains `PENDING_BROKER` unless an explicit future what-if value is supplied.
  Unknown margin is null, never zero; analytical bounded-risk estimates are visibly labeled.
- `P(touch)` is available only from admissible `P` paths. Distribution PnL additionally requires
  full economic states or an explicit future-IV valuation rule. The main M0.1 golden ticket has no
  promoted real-world probability model, so expected PnL and probabilities remain null rather than
  inheriting `Q` pricing simulations. The separate probability fixture is synthetic only.
- Exact Shapley attribution removes factor ordering, but attribution is still model- and
  state-definition-dependent. Taylor attribution remains a local explanation with a visible
  residual; full repricing is primary.
- Treasury CMT inputs retain their par-yield identity. M0 provides curve metadata/interpolation
  architecture but does not claim a bootstrapped arbitrage-free zero curve.
- Mixed-expiry structures are forced to `CLOSE_BEFORE_FIRST_EXPIRY` at a configured buffer. The
  engine intentionally does not model calendars/diagonals after the first leg expiry, assignment,
  structure transformation, stock delivery or post-expiry cash management.
- A canonical five-score snapshot may be candidate-specific or `RUN_GLOBAL_CONTEXT`. The bridge
  copies scores but does not calibrate them, create a composite or infer candidate ownership from a
  global artifact.
- Dated `EVENT_IV_CRUSH` is a configured sensitivity, not an event forecast. Timing and
  event-to-expiry bucketing are deterministic; the shift sizes remain uncalibrated configuration.

- Le panel options réel contient 25 observations alignées et seulement 10 tests OOS
  non chevauchants, contre 41 observations requises par la politique formelle. Les
  intervalles sont larges et le holdout futur reste `UNOPENED`.
- Les droits de recherche/stockage dépendent du type d'abonnement et des accords du
  compte utilisateur. Le code documente les restrictions, mais ne peut confirmer ces
  faits contractuels à la place du titulaire.
- 130 dates de surface passent les diagnostics, 50 présentent un arbitrage calendrier
  et 21 échouent. Heston n'est pas calibré : l'optimiseur multi-start, l'identifiabilité
  et la stabilité OOS ne passent pas les gates.
- V10 sous-performe cash et buy-and-hold sur le développement complet et le segment OOS.
  `ENGINE_NOT_PROVEN_SUPERIOR` est un constat de développement, pas une preuve que toute
  stratégie future échouera.
- Les quotes MarketData.app sont EOD et par jambe ; elles ne prouvent ni NBBO intraday,
  ni fill simultané d'un combo. La composante d'exécution live reste `pending_opra`.

- Quantitative conventions are now centralized as Actual/365 Fixed for calendar time and 252
  sessions for empirical annualisation. These product conventions are explicit, not universal.
- Active forecast path sets are tagged `P` and pricing path sets are tagged `Q`; historical
  serialized reports were not rewritten, so their documented generation-specific assumptions
  remain authoritative.
- Black–Scholes has an analytic/QuantLib European cross-check and the American finite-difference
  engine has a grid-refinement test. This is numerical evidence, not market calibration evidence.
- The V10 final-holdout protocol is sealed. Private real development data and hashes exist under
  conditional account rights, but no sufficiently large, rights-confirmed final sample has been
  provisioned. Holdout promotion remains blocked and the final holdout stays unopened.
- The diagnosed IV solver and raw-SVI fitter expose failures on real point-in-time development
  surfaces, including failed and calendar-arbitrage snapshots. This diagnostic has not validated
  promoted OOS fit quality; eSSVI remains unimplemented behind explicit data and arbitrage gates.
- EWMA and stationary Gaussian GARCH baselines now have likelihood, residual and chronological
  forecast diagnostics on private real development returns. Heavy tails, leverage, structural
  breaks and TTWO OOS superiority remain unvalidated. Heston calibration remains blocked.
- Experiment manifests, availability-time checks, purge/embargo, order-invariant PBO ties,
  signal-alignment placebo and a one-time hash-chained holdout ledger are implemented. The final
  holdout content is deliberately absent and unopened; permutation exchangeability and primary-paper PBO
  conformance remain limitations.
- Simulated exits now use a serializable chronological state machine, and canonical path
  probabilities have Wilson/ESS/minimum-path sidecars. Daily checkpoints still miss intraday
  crossings; Wilson assumes iid unweighted trials, block-bootstrap coverage depends on
  stationarity and block length, and no rare-event importance sampler is implemented. LSM is
  deferred until a real material gap against finite-difference/checkpoint controls is measured.
- The V11 scenario updater is now explicitly labeled a `configured_heuristic_belief`; its legacy
  Bayesian schema name is retained only for compatibility. Model/parameter ensembles decompose
  predictive and Monte Carlo uncertainty, but current equal weights and illustrative members
  remain diagnostic. No fitted likelihood, real posterior predictive distribution or TTWO
  holdout calibration exists.
- Allocation objectives are now explicit/versioned and a full non-compensatory Pareto frontier
  is computed from the exhaustively enumerated whole-contract feasible set, always including
  cash/NO_TRADE. Frontier membership is conditional on the candidate universe, objective vector
  and uncalibrated regime inputs; pairwise dominance is intentionally limited to small budgets.
- Event evidence now has point-in-time dependency contracts, and probability sets cannot claim
  empirical calibration without dataset/experiment/calibration hashes and an OOS partition.
  Independence, shared-driver discounts, user belief bounds and all event shock distributions are
  still explicit assumptions; no real TTWO catalyst probability, causal effect or latent-state
  transition is calibrated. Bounded belief ranges are sensitivity sets, not confidence regions.
- The final evidence sidecar enforces complete sections, intervals/diagnostics and a monotone
  weakest-link grade. Hashes establish artifact identity, not correctness; grade inputs still need
  independent review, and the current chain remains `software_tested_only` because real OOS,
  fresh holdout and paper evidence are absent. Static reporting is not financial validation.
- The Phase-10 deterministic audit finds no active experiment manifest and no fresh holdout.
  Its `READY_RESEARCH_ONLY` status validates the repository's guarded research workflow only;
  financial promotion remains `BLOCKED_MISSING_REAL_EVIDENCE`, and no predictive-accuracy gain is
  claimed from the larger test suite.
- Phase 11 evaluated Bergomi/rough volatility, Bayesian filtering, advanced rates and other BOOK
  extensions without integrating any model. No candidate passed the authorized-data,
  identifiability, OOS materiality, ranking-sensitivity, numerical-cost and independent-review
  gates. Current-scope `reject` statuses are reversible if their recorded materiality gate passes.
- MarketData.app historical chains are EOD bid/ask, not intraday NBBO or
  simultaneous combo fills.
- Alpaca indicative snapshots do not supply the open-interest/underlying fields
  required by the active liquidity and budget gates.
- V7, V8, and V9 were inspected and are contaminated. The V11.1 split contract
  can lock a fresh holdout, but no authorized historical option dataset has
  populated one yet.
- The accessible option history is too short for robust multi-regime,
  catalyst-specific nested validation.
- Conditional GBM and historical bootstrap are screen-grade distributions, not
  causal GTA VI forecasts.
- Future IV is stressed, but a calibrated detailed IV-surface forecast is P2.
- Rolling is registered but rejected during optimization when future combo
  quotes are unavailable.
- Broker combo margin, live FX, contract IDs, permissions, commissions, and
  fills require a fresh IBKR human preview.
- Structural validity and favorable simulation never substitute for DSR, PBO,
  placebo, external walk-forward, locked holdout, and paper-trading gates.
- V10 thesis mode is a scenario scanner, not a probability model. Expected P&L
  and probability of success are null unless the user supplies a probability
  for every target and the vector sums to one.
- V10 uses a flat configured risk-free rate, continuous dividend yield, and
  per-leg IV stresses. It does not forecast the full future volatility surface.
- A quote with missing open interest, volume, or unconfirmed deliverable can be
  retained only as an explicit watchlist warning; a known threshold breach,
  invalid quote, stale quote, non-standard multiplier, budget breach, or
  unbounded/margin-unknown structure is blocked.
- `LEAPS call` is a maturity label on `long_call`, not a fourth architecture.
  Long calls still have contractually unbounded upside but bounded premium risk.
- V11 is a probabilistic research overlay, not a validated probability engine.
  Its default priors, likelihoods, evidence caps, regime drifts, jump
  parameters, and Heston parameters are explicit experimental assumptions.
- The default V11 run inherits a synthetic V10.1 chain. Its Dupire
  finite-difference surface is therefore `partial`; unstable nodes fall back
  to observed IV and no global static-arbitrage calibration is claimed.
- The V11 path repricer uses conditional Black-Scholes between V10.1 QuantLib
  American control points. Early exercise, discrete dividends, pin risk, and
  assignment still require the V10.1 controls and broker review.
- Without an aligned point-in-time factor file, covariance is limited to the
  available TTWO return series. It cannot infer missing Nasdaq, peer, rate, FX,
  volume, IV, OI, sentiment, news, or catalyst factors.
- Exact integer enumeration solves only the configured finite candidate pool
  and contract cap. Gradient/Hessian diagnostics describe the smooth
  mean-variance surrogate, not CVaR or discrete constraints.
- Existing V7–V9 holdouts remain contaminated. V11.1 implements a point-in-time
  walk-forward interface and explicit baselines, and the private pre-OPRA development
  run remains sample-limited and non-promoting. Promotion still requires a new real sample,
  untouched holdout, and paper run.
- SEC, FRED, Take-Two RSS, Google Trends alpha, and IBKR/OPRA connectors are
  opt-in read-only ports. The exchange-calendar port is also unconfigured by
  default and therefore reported as a missing required series. The default run
  does not contact external providers. Credentials, fair-access limits, data
  entitlements, terms, and production retry policies remain deployment
  responsibilities. IBKR TWS/IB Gateway uses a locally authenticated socket rather than an API
  key; the current configuration stops before entitlement confirmation or connection.
- A leg-level quote is not an executable combo quote. Some IBKR smart combo
  orders do not support a what-if check, so the absence of a broker what-if
  response must block promotion rather than weaken the gate.
- Position monitoring and multi-date fixture replay emit human-readable advice
  only. They cannot submit, modify, cancel, roll, exercise, or partially close
  a position.

See [V10 known limits](known_limits.md) for scanner-specific details.
