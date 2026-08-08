# Phase 11 documentary research — advanced extension materiality

Date: 2026-08-08
Status: `documentary_gate_complete_no_model_integrated`

## Immediate result

No examined extension demonstrates incremental TTWO decision value. The resulting statuses are
eight `defer`, three current-scope `reject`, zero `prototype` and zero
`candidate_for_implementation`. These are evidence classifications, not permanent theoretical
judgments. Each can be reopened only by its recorded measurable gate.

## Sources and passages inspected

- Lorenzo Bergomi, *Stochastic Volatility Modeling*: every available local fragment, chapters
  3–12 and the epilogue/reference fragment. Chapter 6 frames native Heston as a single-maturity
  instantaneous-variance model; chapter 7 models the forward-variance curve and notes the need to
  simulate its state or find a finite-dimensional representation; chapters 8–9 connect model
  covariance choices to static and dynamic smile behavior; chapter 12 adds calibration and state
  variables for local-stochastic volatility. The epilogue warns that model parameters should be
  connected to observable hedge/P&L targets, not fitted for their own sake.
- Leif B.G. Andersen and Vladimir V. Piterbarg, *Interest Rate Modeling*: Volume-I chapter 6 and
  Volume-II chapters 10–15. The image-only fragments were sampled with read-only, bounded OCR:
  Volume-I-part-2 PDF pp. 1–46 for curve construction; Volume-II PDF pp. 1, 41, 76, 136, 186,
  201, 226 and 251 for one-/multi-factor short-rate, quasi-Gaussian, LMM, calibration and
  interpolation passages. These sections address multi-tenor rate-derivative dynamics, not a
  proven TTWO option-ranking sensitivity.
- Simo Särkkä and Lennart Svensson, *Bayesian Filtering and Smoothing*, second edition: contents,
  chapter 1 (printed pp. 1–16), state-space modeling chapters 5–8, particle filtering chapter 11
  and parameter estimation chapter 16 (printed pp. 319–348). A filter needs an explicit state
  transition, measurement likelihood and sequential observations; none is identified for TTWO
  events.
- Gatheral, Jaisson and Rosenbaum, [“Volatility is rough”](https://arxiv.org/abs/1410.3394),
  primary arXiv metadata and abstract. Its roughness evidence depends on high-frequency
  volatility estimation.
- Bayer, Friz and Gatheral,
  [“Pricing under rough volatility”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2554754),
  primary SSRN preprint metadata and publisher DOI. Its rBergomi evidence concerns SPX and
  integrated-volatility claims.
- Livieri, Mouti, Pallavicini and Rosenbaum,
  [“Rough volatility: evidence from option prices”](https://arxiv.org/abs/1702.02777), primary
  arXiv metadata and abstract. It uses short-maturity at-the-money SPX options and explicitly
  observes maturity-smoothing differences in the estimated Hurst parameter.
- Existing inspected Glasserman, Tsay, McElreath, Nocedal–Wright, SVI/eSSVI and
  Longstaff–Schwartz records were reused for the other candidate extensions.

All local PDFs remained read-only. Ghostscript text extraction was used for Bergomi and Särkkä;
the Andersen–Piterbarg image-only samples required low-resolution rendering plus Tesseract OCR.
No extracted formula or OCR value was promoted. The earlier full Summarizer route had already
proved unreliable for this corpus, so this phase used bounded passage extraction and records that
limitation rather than treating summaries as evidence.

## Evaluation

| Extension | Status | Dominant blocker | Gate before reconsideration |
| --- | --- | --- | --- |
| Bergomi forward variance | `defer` | no validated Heston/TTWO smile-dynamics baseline | stable OOS price and rank gain vs Heston/SVI |
| Rough Bergomi | `defer` | index evidence, no dense/high-frequency TTWO inputs | stable TTWO roughness and OOS gain |
| Bayesian filtering | `defer` | no identified transition/measurement likelihood | preregister model and improve OOS calibration |
| Stochastic rates/HJM/LMM | `reject` current scope | no material multi-tenor rate exposure | material price/rank change vs deterministic curve |
| eSSVI | `defer` | raw SVI has not failed on real TTWO data | real-surface OOS stability gain |
| Learned regimes | `defer` | no stable regime labels/transitions | chronological OOS gain vs transparent rules |
| Hierarchical event Bayes | `defer` | too few independent comparable events | justified population and calibrated prediction |
| Longstaff–Schwartz | `defer` | no material FD/checkpoint discrepancy | measured gap plus basis/path-reuse validation |
| Higher-order Greeks/AAD | `reject` current scope | no read-only decision need | stable sensitivity tied to a validated rule |
| Sobol/QMC/distributed MC | `defer` | no profiled error/runtime bottleneck | reproducible unbiased error/cost gain |
| Neural volatility surface | `reject` current scope | insufficient data, transparency and arbitrage control | OOS win with enforceable arbitrage constraints |

## Facts, assumptions, inferences and decision

Facts:

- the repository has no active real-data manifest or fresh final holdout;
- Heston is gated but not fitted on a real TTWO surface;
- Bergomi chapters 1–2, Andersen–Piterbarg Volume III and the Gatheral book are absent locally;
- current rough-volatility empirical sources study broad equity/index data, especially SPX.

Assumptions:

- a complex model is useful here only if it changes calibrated prices, uncertainty or final
  rankings enough to survive costs and model risk;
- the current deterministic Treasury curve is the correct rates baseline until sensitivity says
  otherwise.

Inference:

- adding state variables or non-Markovian dynamics now would increase non-identifiability faster
  than evidence quality. This follows from the missing data/baselines; it is not claimed as a
  universal result about these models.

Decision for this phase:

- integrate no advanced model;
- keep every implementation gate fail-closed and `order_capability=forbidden`;
- require a separate reviewed implementation phase even if a future assessment reaches
  `candidate_for_implementation`.

The machine-checkable implementation is
`src/take_two_options/validation/extension_evaluation.py`; it contains no pricing, filtering,
rates, volatility or order-execution model.
