# Phase 9 documentary research — reporting uncertainty, evidence and option risks

Date: 2026-08-08  
Status: `sourced_and_implemented_reporting_only`

## Questions studied

- How can point estimates, intervals and their coverage assumptions be communicated without
  implying certainty?
- How can a software grade remain monotone and distinct from a trade recommendation?
- Which option-risk facts and terminology must remain visible in a decision report?
- How can formula/source/code/test lineage fail closed in CI?

## Sources inspected

- Larry Wasserman, *All of Statistics*, 2004, chapter 8, printed pp. 107–114. Sections 8.1–8.3
  distinguish the point statistic, estimated standard error and several approximate bootstrap
  confidence intervals. The text explicitly notes approximation limits and cautions that methods
  based on very small samples may be unreliable.
- Paul Glasserman, *Monte Carlo Methods in Financial Engineering*, 2004, chapter 1, printed
  pp. 1–10. The sample mean, estimated standard error and asymptotic normal interval are distinct;
  the interval describes simulation error under independent finite-variance replications.
- Options Clearing Corporation, *Characteristics and Risks of Standardized Options*, June 2024,
  official current ODD page and PDF checked on 2026-08-08. Chapter II explains premium and
  contract terminology; chapter X (printed pp. 61–90) details holder/writer, market, liquidity,
  exercise and disruption risks. OCC's official page states that the June 2024 ODD superseded the
  prior version and warns that future updated versions may be issued.

The local books remained read-only. OCC was consulted from its official website because document
currentness is time-sensitive.

## Concepts, formulas and measure

- A point estimate is never shown without a finite interval or an explicit unavailable diagnostic.
- Probability intervals always state their origin; heuristic/user sensitivity is not confidence
  coverage.
- `FORM-MC-SE-001`, `FORM-MC-CI-001` and `FORM-BOOTSTRAP-001` are now fully registered.
- The grade is a prerequisite chain, not a statistical formula: proposed → implemented → tested →
  numerically validated → empirically validated → holdout validated → paper validated.
- The overall grade is the minimum across required components; optional evidence cannot compensate.
- Each estimate carries `P`, `Q` or `not_applicable`; reporting never performs a measure change.

## Assumptions, alternatives, contradictions and limitations

Assumptions:

- empirical validation needs a real dataset hash and explicit OOS role;
- holdout validation needs the final-holdout role plus the sealed ledger hash;
- paper validation needs a paper manifest and all prior grades;
- every reported probability has an interval and diagnostic;
- OCC wording is a risk-disclosure source, not quantitative validation.

Alternatives rejected:

- one blended confidence score: it hides the weakest dependency;
- `production_ready` from unit tests: software correctness is not financial validation;
- dynamic external dashboard assets: they break offline auditability and widen the attack surface;
- silent formula-registry drift: replaced by a CI validator.

Contradictions:

- legacy readiness may call deterministic offline reporting `production_ready_offline`; the new
  decision grade deliberately caps claims at research-only and never emits `production_ready`;
- a 95% Monte Carlo interval can be precise while the model is wrong. The report therefore keeps
  simulation error, model risk and data limits in separate sections;
- a bounded-loss option can still lose the entire premium, be illiquid or face exercise/market
  disruption. A favorable scenario rank cannot erase those risks.

Limits:

- grade inputs still require truthful external evidence manifests; hashes prove identity, not data
  quality;
- interval coverage is method-specific and may fail under dependence, small samples or model error;
- the static dashboard is an evidence view, not personalized financial advice;
- the current OCC edition must be rechecked before any distribution outside research.

## Choice, impact and validation

The implementation adds a typed final evidence sidecar with every mandatory section, a monotone
grade calculator, static Markdown/HTML renderers, a formula lineage matrix, an errata registry and
a CI validator. Historical V11 report contracts remain unchanged.

Expected impact: fewer overclaims, no orphan formula, explicit `NO_TRADE` reasons and a stable
machine-readable distinction between software tests and real-world validation.

Validation: monotonicity/weakest-link tests, probability-without-interval rejection, golden section
assertions, network-free HTML checks, registry ID/file/symbol integrity and the existing security
gate.

Implementation: `src/take_two_options/reporting/evidence_grade.py` and
`scripts/validate_research_registry.py`. Tests: `tests/test_evidence_grade_reporting.py` plus the
full offline gate.
