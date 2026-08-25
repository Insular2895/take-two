# Phase 8 documentary research — event scenarios and sequential decisions

Date: 2026-08-08  
Status: `sourced_and_implemented_diagnostic_only`

## Questions studied

- Under which assumptions is a sequential probability update coherent with a joint update?
- How must repeated, derived, shared-driver and contradictory reports be handled?
- Which claims are conditional associations, and which would require a causal model?
- Can a latent-state filter be justified with the current TTWO event history?
- How can user beliefs, historical estimates, market-implied quantities and calibrated
  probabilities remain semantically distinct?

## Books and PDF passages inspected

- Joseph K. Blitzstein and Jessica Hwang, *Introduction to Probability*, Second Edition,
  CRC Press, 2019, chapter 2, printed pp. 45–79 (PDF pp. 56–90). Sections 2.1, 2.3–2.6 and
  2.9 were inspected. Retained concepts: conditioning on declared background information,
  odds-form Bayes, law of total probability, conditional independence and coherent sequential
  updates. The sequential/simultaneous equivalence in section 2.6 explicitly assumes the needed
  conditional structure; it does not authorize multiplying dependent evidence as if independent.
- Richard McElreath, *Statistical Rethinking*, Second Edition, 2019 compilation, chapters 5–6,
  especially printed pp. 132–134 and 181–193 (PDF pp. 148–150 and 197–209). Retained concepts:
  association is not intervention, DAGs are explicit causal assumptions, shared causes create
  confounding, and conditioning on a collider can create an association.
- Simo Särkkä, *Bayesian Filtering and Smoothing*, Second Edition, was inventoried but not used
  as an implementation source. A state-space filter needs an identified transition/observation
  model and sequential data that the current sparse TTWO catalyst corpus does not provide.

The original PDFs remained read-only. Summarizer was invoked on a temporary qpdf-bounded copy of
Blitzstein/Hwang chapter 2. Its `smart` OCR route stalled during MinerU initialization and was
stopped; the `text` route produced the local Markdown transcription but its downstream evidence
packet step also stalled. Direct text extraction from the same bounded pages was therefore used
for inspection. No generated summary was treated as evidence.

## Concepts and formulas retained

- `FORM-SCENARIO-MIXTURE-001`: a configured scenario expectation is the law-of-total-
  probability mixture of already-priced conditional outcomes.
- `FORM-BELIEF-SWITCH-001`: with one scenario belief varied and all residual beliefs kept in
  their declared central proportions, candidate indifference is a one-dimensional linear root.
- Sequential coherence is a validation condition, not a new fitted formula. Same-fact and derived
  reports receive zero additional novelty. A shared-driver discount must be explicitly declared.
- Probability boxes are propagated by exact bounded-simplex extrema. These ranges are sensitivity
  bounds unless the probability set carries complete out-of-sample calibration lineage.

Measure: scenario outcome beliefs and historical estimates are under `P`; a market-implied
scenario must remain tagged `Q`. The module never converts one measure to the other.

## Assumptions, alternatives and contradictions

Assumptions:

- every event has an availability timestamp no later than the decision cutoff;
- every dependency parent was available no later than its child;
- declared independence and dependence multipliers are configuration assumptions;
- conditional scenario P&Ls are produced upstream with explicit quote/execution assumptions;
- probability intervals admit at least one normalized vector.

Alternatives considered:

- automatic source-correlation estimation: rejected because the event sample is too small and
  source syndication is not a stable stochastic process;
- hidden Markov/Bayesian filtering: deferred until a real point-in-time sequence and observation
  likelihood demonstrate material predictive gain;
- naive Bayes multiplication: rejected because independence is not implied by multiple URLs or
  by unconditional independence;
- causal GTA VI effect estimation: rejected because the data cannot identify interventions or
  close plausible backdoor paths.

Contradictions found:

- the legacy class names say `Bayesian*`, while the active implementation is a configured
  fractional likelihood heuristic. Compatibility names remain, but the new sidecar origin is
  `configured_heuristic`, never `empirically_calibrated`;
- coherent sequential Bayes is theoretically order-invariant under a valid joint model, while the
  current heuristic uses cumulative family caps. Therefore input order is normalized by
  availability time and the result must not be presented as a statistical posterior.

## Choice, expected impact and validation

The chosen design adds lateral typed contracts instead of changing historical schemas:

1. a point-in-time acyclic evidence graph with explicit relation and discount;
2. probability sets whose origin determines mandatory lineage;
3. configured event shocks with `P/Q`, status, source, duration and recovery;
4. bounded belief sensitivity for expected P&L, target probability and large-loss probability;
5. explicit advisory rules that can return `NO_TRADE` and always carry
   `order_capability=forbidden`.

Expected impact: less duplicate-news amplification, auditable narrative assumptions, conservative
probability presentation and measurable revaluation conditions. It does not improve empirical
TTWO forecasting by itself.

Validation method: deterministic synthetic sequences, acyclic/chronological rejection tests,
derived-event neutralization, probability-origin misuse tests, bounded-simplex oracle examples,
analytic belief switch and stale-rule fail-closed tests.

Implementation files:

- `src/take_two_options/intelligence/sequential_decision.py`
- `src/take_two_options/intelligence/event_scenarios.py`

Tests: `tests/test_sequential_event_decision.py`.

## Limitations

- No real TTWO scenario probability, shock distribution or dependency discount is calibrated.
- Marginal probability intervals are not simultaneous confidence regions.
- Shock definitions are contracts; upstream repricing must still validate surface, liquidity and
  execution behavior.
- The belief switch holds conditional P&Ls fixed and varies only one belief.
- Advisory rule success is not permission to trade and cannot schedule an action.
