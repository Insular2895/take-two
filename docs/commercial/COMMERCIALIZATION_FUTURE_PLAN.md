# Future Phase N — commercial productization plan

Status: `DORMANT_PLANNING_ONLY`

Commercial phase: `DORMANT`

Commercial implementation: `FORBIDDEN`

Research validation: `PRIORITY`

Phase M: `MUST_COMPLETE_FIRST`

Created: 2026-08-08

This document preserves a possible commercialization roadmap without opening or implementing
Phase N. It is a planning artifact, not a product decision, legal opinion, market study, pricing
recommendation, architecture approval, or authorization to change the quantitative engine.

## 1. Current state and entry gate

The repository currently reports:

- `PRE_OPRA_RESEARCH_COMPLETE`;
- `NO_POSITION_RECOMMENDED`;
- `ENGINE_NOT_PROVEN_SUPERIOR`;
- final holdout `UNOPENED`;
- Phase M not started;
- IBKR TWS paper socket configured without an API key, but entitlement/licence unconfirmed and not connected;
- `transmit=false`, `what_if=true`, and `order_capability=forbidden`.

`FINAL_PROJECT_VALIDATION.md` does not currently exist. Therefore:

```text
PHASE_N_ENTRY_GATE=CLOSED
COMMERCIAL_PRODUCT_BUILD=FORBIDDEN
```

Phase N may only be considered after all of the following are complete and archived:

1. authorized OPRA market-data access and Phase M;
2. governed shadow mode;
3. prospective paper trading;
4. a sufficient prospective sample across an adequate duration;
5. probability and calibration validation with confidence intervals;
6. validation of the five scores and their coverage;
7. validation of severe-loss estimates and risk calibration;
8. observed slippage, fees, spreads, rejects, and data-quality incidents;
9. prospective V10 comparison against the same baselines;
10. stability and robustness analysis by market regime;
11. an intact, governed final holdout when the protocol permits its one-time use;
12. an independently reviewable `FINAL_PROJECT_VALIDATION.md`.

A single profitable trade, a TTWO call returning a multiple, a successful GTA scenario, or a
small positive sequence cannot open Phase N.

## 2. Facts, hypotheses, constraints, and decisions

| Type | Current statement | Consequence |
| --- | --- | --- |
| Verified repository fact | The current derived verdict is `ENGINE_NOT_PROVEN_SUPERIOR`. | No claim of demonstrated edge is permitted. |
| Verified repository fact | Phase M and prospective paper validation are incomplete. | The entry gate remains closed. |
| Verified repository fact | The final holdout remains `UNOPENED`. | It must not be opened or fabricated for commercial planning. |
| Current governance decision | Commercial implementation is forbidden before the Phase N entry gate and a later commercial GO. | Documentation only in the present phase. |
| Hypothesis to test | A private quantitative backend could support web/API analytics. | Architecture remains conceptual until N5. |
| Hypothesis to test | Retail, professional analytics, or B2B/API may be viable segments. | No segment is selected before current market research. |
| Hypothesis to test | A prospective decision dataset may become a defensible asset. | Data rights, quality, retention, and proof must be validated. |
| External constraint | Regulation, data licenses, IP, security, and economics can independently veto commercialization. | Quantitative success alone is insufficient. |

No item marked as a hypothesis is an approved product requirement.

## 3. Final quantitative verdict routing

When `FINAL_PROJECT_VALIDATION.md` exists, its mechanically derived verdict routes the work as
follows:

| Final verdict | Phase N consequence |
| --- | --- |
| `VALIDATION_FAILED` | Phase N is prohibited. Do not build or market the engine. |
| `ENGINE_NOT_PROVEN_SUPERIOR` | Do not claim edge. At most assess a research/analytics product with no superiority claim, subject to every non-quantitative gate. |
| `PROMISING_BUT_NOT_PROVEN` | Continue validation. Do not present the engine as validated and do not begin product development. |
| `ENGINE_ADDS_VALUE` | Phase N may be studied only if prospective evidence is sufficient and legal, data, IP, security, market, and economic gates also pass. |

This routing does not automatically issue a commercial `GO`. That decision belongs in the future
`COMMERCIAL_GO_NO_GO.md` and requires explicit approval.

## 4. Commercial hypotheses to evaluate

The primary product hypothesis is:

```text
PROPRIETARY QUANT RESEARCH CORE
            +
PRIVATE SERVER-SIDE BACKEND
            +
WEB AND/OR ANALYTICS API
            +
RECURRING SUBSCRIPTION
```

The customer could buy access to analyses, scores, simulations, risk diagnostics, comparisons,
dashboards, alerts, or structured API outputs. The customer would not automatically receive the
source code, models, parameters, internal datasets, provider secrets, or infrastructure.

At least three business models must be compared with updated evidence:

### A. Retail research SaaS

Potential scope: scanner, scenarios, five scores, severe-loss ladder, comparisons, alerts, and
dashboards for informed individual users.

### B. Professional analytics

Potential scope: richer history, IV surfaces, advanced simulations, exports, batch screening,
API access, and controlled customization for sophisticated users.

### C. B2B, API, or white label

Potential customers: fintechs, portfolio tools, broker analytics, research platforms,
educational platforms, wealth-tech, and specialist institutions.

No model or segment is selected by this document.

## 5. TTWO laboratory and multi-underlying gate

TTWO remains the research laboratory. The intended sequence is:

```text
TTWO
  ↓
prospective evidence
  ↓
5–10 justified liquid underlyings
  ↓
multi-underlying validation
  ↓
commercial product assessment
```

AAPL, NVDA, MSFT, AMZN, META, TSLA, SPY, and QQQ are examples for later screening, not approved
instruments. Each future inclusion requires documented option liquidity, historical coverage,
OPRA coverage, spreads, open interest, model compatibility, data quality, and regime coverage.

Before any public SaaS, the research core must accept ticker, budget, currency, objective, risk
profile, and horizon without Python code changes. TTWO-, GTA-, Take-Two-, and Rockstar-specific
events or rules must remain outside the generic core. This is a future validation criterion, not
an authorization to refactor the engine now.

## 6. Product and UX principles

The future product must not collapse its output to `BUY`, `SELL`, or a magic score. A candidate
view should preserve, when licensed and validated:

- ticker, strategy, expiration, legs, and capital required;
- Opportunity, Risk, Evidence, Model Agreement, and Execution Quality;
- raw expected return, P(Profit), P(Target), CVaR, maximum loss, and breakeven;
- P(loss >25%), P(loss >50%), P(loss >70%), and P(loss >90%);
- classification, principal risks, invalidation conditions, freshness, and provenance.

Scores remain summaries. Raw metrics, uncertainty, coverage, missing components, and severe-loss
behavior remain visible. Alerts may cover opportunity, risk, IV, liquidity, events, and
invalidations, but must stay analytically separate from execution.

A future commercial API may return candidate structures, scores, raw metrics, evidence,
classification, and timestamps. It must not redistribute raw market data without explicit rights.

## 7. Pricing, tiers, and unit-economics hypotheses

The following ranges are hypotheses to test, not approved or recommended prices:

| Segment | Hypothesis |
| --- | ---: |
| Retail | EUR 49–199/month |
| Professional | EUR 300–1,500/month |
| B2B/API | EUR 15,000–100,000+/year |

Possible future tiers—also unapproved—are Free, Investor, Pro, Quant/API, and Enterprise. No tier,
billing code, subscription, or Stripe integration is to be created now.

Future pricing research must use current competitor prices, customer interviews,
willingness-to-pay, validated capabilities, launch geography, regulatory scope, provider fees,
support burden, acquisition cost, and margin sensitivity.

Revenue scenarios are arithmetic, not forecasts:

```text
MRR = paid_users × average_revenue_per_user
ARR = 12 × MRR

cost_per_user = data_cost
              + compute
              + storage
              + support
              + billing
              + monitoring
              + allocated_legal_and_compliance_cost
```

Conservative, base, and high-growth scenarios must be labeled as scenarios. Future unit economics
must include gross margin, contribution margin, CAC, LTV, churn, retention, conversion, and
customer concentration.

## 8. Prospective data moat hypothesis

Standard methods such as Heston, GARCH, SVI, and Monte Carlo are not a sufficient moat. A possible
defensible asset is a governed prospective decision dataset:

```text
market snapshot
  → candidate universe
  → frozen V10 prediction and five scores
  → decision
  → future outcome
  → observed costs and slippage
  → error attribution and postmortem
```

Each record should preserve provenance, timestamp, snapshot and decision hashes, model version,
score versions, market regime, quotes, candidate set, ranking, predictions, decision, realized
outcome, realized P&L, spread, slippage, and model error. Decision records and subsequent
realizations remain separate and immutable.

Future public surfaces must not expose proprietary source code, sensitive parameters, full
decision history, internal calibration, licensed datasets, provider secrets, or architecture
detail that unnecessarily enables replication. Whether the public research repository and a
future commercial system should be separated is a decision for N3.

## 9. Product architecture hypothesis

No infrastructure provider or topology is selected. The conceptual boundary is:

```text
DATA PROVIDERS
      ↓
PRIVATE DATA LAYER
      ↓
PRIVATE QUANT RESEARCH CORE
      ↓
VERSIONED RESEARCH API
      ↓
┌─────────┼──────────┐
↓         ↓          ↓
WEB     FUTURE MOBILE   COMMERCIAL API
↓         ↓          ↓
AUTHORIZED USERS AND ORGANIZATIONS
```

The quantitative core remains server-side and inaccessible directly. Billing must be isolated:

```text
BILLING → ENTITLEMENT → PRODUCT ACCESS
```

Billing must never change quantitative logic. Research `model_version`, commercial `api_version`,
and `product_version` remain independent.

Only in N5 or later may the team assess API backend, workers, queues, caches, relational and
time-series storage, object storage, observability, secrets, backup, and disaster recovery. The
minimum architecture should match measured demand rather than assumed scale.

## 10. Data licensing gate

Before any public or paid product, obtain current written analysis of OPRA and exchange data,
broker data, historical options, FRED, SEC, news/events, third-party feeds, derived datasets, and
prospective decision records.

For every source, distinguish:

| Right | Question |
| --- | --- |
| Use | May the company ingest the data for the declared purpose? |
| Display | May values be shown to the intended customer category? |
| Redistribution | May raw or transformed values leave the licensed system? |
| Derived data | What transformations qualify, and what restrictions survive? |
| Non-display use | Are modeling, ranking, alerting, and automated processing licensed? |
| Storage | What may be retained, for how long, and with which controls? |
| Commercial use | Which entity, geography, subscriber class, and product are covered? |

The ability to use data internally never implies the right to display or redistribute it.

During N2, create `docs/commercial/OPRA_COMMERCIAL_DATA_RIGHTS.md` using then-current official
provider and exchange rules. It must cover subscriber category, professional/non-professional
classification, display, non-display, derived data, redistribution, user reporting, audits, and
exchange fees. Do not create or treat that document as validated now.

## 11. Regulatory, legal, privacy, and claims gate

Professional legal review is mandatory in the actual launch jurisdiction and at the actual launch
date. Research, analytics, investment recommendations, personalized investment advice, and
execution are not interchangeable categories.

The product boundary must be reassessed if it collects wealth, income, capital, age, horizon,
financial situation, objectives, or risk tolerance and then recommends a specific option. A
disclaimer such as "not financial advice" does not override the product's actual behavior.

During Phase N, prepare these review documents without presenting them as legal opinions:

```text
docs/commercial/regulatory/PRODUCT_CLASSIFICATION.md
docs/commercial/regulatory/JURISDICTION_MATRIX.md
docs/commercial/regulatory/DATA_RIGHTS.md
docs/commercial/regulatory/RISK_DISCLOSURES.md
docs/commercial/regulatory/USER_SUITABILITY_BOUNDARY.md
docs/commercial/regulatory/MARKETING_CLAIMS_POLICY.md
docs/commercial/regulatory/RECORD_RETENTION.md
```

Marketing claims such as guaranteed returns, beats the market, AI predicts the market, 90%
profitable, best option, or risk free are prohibited without appropriate and reviewable evidence.
Every permitted quantitative claim must identify period, sample, methodology, fees, limitations,
and whether evidence is backtest, walk-forward, holdout, paper, or live. Those evidence classes
must never be merged.

A possible public transparency page should disclose methodology, start date, frozen versions,
sample size, paper/live distinction, baselines, costs, drawdown, CVaR, and failures without
cherry-picking. Privacy planning must cover email, billing, IP addresses, usage, risk preferences,
portfolios, and financial information. Data minimization is the default.

## 12. Security, reliability, and model governance gate

Before a SaaS or API launch, complete and independently review:

- threat modeling, dependency and supply-chain audits;
- secret management, authentication, authorization, organizations, and roles;
- tenant isolation, API keys, quotas, rate limits, and abuse controls;
- encryption, access logs, backups, tested restoration, and incident response;
- privacy controls and vulnerability disclosure;
- market-data, model, API, score-drift, and calibration-drift monitoring;
- fail-closed behavior when inputs are missing, stale, crossed, or unlicensed.

If current data are unavailable, the product must show `DATA_UNAVAILABLE` or another explicit
blocked state, not a stale recommendation.

Every material model change after launch must follow:

```text
research → validation → shadow → paper → approval → deployment
```

During Phase N, create `MODEL_CHANGE_LOG.md`. Each entry must record reason, source, expected
effect, tests, validation, approval, and deployment date. Monitor at least Brier score, ECE, return
distribution, risk calibration, score monotonicity, model disagreement, and execution slippage.
Material drift must reduce Evidence or suspend the affected output.

## 13. Performance, scalability, and operations gate

Before architecture selection and pricing, benchmark candidate generation, pricing, simulation,
memory, concurrent use, ingestion, OPRA throughput, and dashboard generation. Report P50, P95,
and P99 where appropriate.

Operational readiness eventually includes health checks, logs, metrics, traces, alerts, cost
controls, support workflows, FAQ, billing support, data-issue reporting, incident policy,
recovery, and clear retail/pro documentation. No target or infrastructure is approved now.

## 14. Commercial roadmap N0–N15

All steps are `NOT_STARTED`. Each phase requires its own evidence, review, and explicit approval.

| Phase | Purpose | Minimum output or gate | Current status |
| --- | --- | --- | --- |
| N0 | Commercial readiness audit | Reconcile final quantitative evidence, blockers, date, ownership, and scope | `NOT_STARTED_BLOCKED_BY_ENTRY_GATE` |
| N1 | Legal/regulatory classification | Current professional analysis for intended product, users, and jurisdictions | `NOT_STARTED` |
| N2 | Market-data licensing review | Written rights matrix for every provider and output | `NOT_STARTED` |
| N3 | IP/security separation | IP inventory, repository boundary, threat model, secrets and data-flow review | `NOT_STARTED` |
| N4 | Multi-underlying validation | Justified liquid universe and prospective validation comparable to TTWO | `NOT_STARTED` |
| N5 | SaaS product architecture | Minimum architecture proposal supported by benchmarks and commercial GO | `NOT_STARTED` |
| N6 | Authentication/organizations | Identity, tenant, role, API-key, quota, privacy, and audit design | `NOT_STARTED` |
| N7 | Subscription/billing | Billing isolated from entitlement and quant logic; tested unit economics | `NOT_STARTED` |
| N8 | Web product | Risk-first web experience with raw metrics and fail-closed states | `NOT_STARTED` |
| N9 | API product | Versioned, licensed, rate-limited analytical API | `NOT_STARTED` |
| N10 | Internal admin/monitoring | Data/model/API health, drift, incidents, support, and audit controls | `NOT_STARTED` |
| N11 | Private alpha | Selected users; UX, bugs, comprehension, quality, latency, risk communication | `NOT_STARTED` |
| N12 | Closed beta | Willingness-to-pay, retention, usage, feature value, alerts, support load | `NOT_STARTED` |
| N13 | Paid beta | Real pricing, conversion, churn, support, unit economics, and reliability | `NOT_STARTED` |
| N14 | General availability | All launch, legal, licensing, security, support, and monitoring gates signed | `NOT_STARTED` |
| N15 | Enterprise/B2B | Segment-specific licensing, compliance, SLAs, integrations, and concentration risk | `NOT_STARTED` |

Private alpha, closed beta, paid beta, and general availability are distinct stages. Passing one
does not automatically approve the next.

## 15. Commercial GO/NO-GO before N5

Before any product-development phase, create `COMMERCIAL_GO_NO_GO.md` and assess quantitative
edge and permitted claim level, data rights, regulatory classification, security/privacy, current
market evidence, unit economics, differentiation, and IP ownership/separation.

| Outcome | Meaning |
| --- | --- |
| `GO` | All critical gates pass with named evidence and approvers; implementation may be separately authorized. |
| `CONDITIONAL_GO` | Only explicitly bounded preparatory work may proceed; blockers, owners, and deadlines are recorded. |
| `NO_GO` | Do not build the SaaS. Preserve research or reassess a narrower non-edge analytics concept only if permitted. |

`GO` is not produced automatically by the quantitative engine or by this plan. It requires an
explicit human decision after the relevant professional reviews.

## 16. Future research, pricing, and product metrics

At the actual Phase N date, refresh competitor and pricing research. Compare current options
analytics, volatility tools, scanners, research platforms, and institutional analytics by price,
features, data, API, users, strengths, and weaknesses.

Create `docs/commercial/PRICING_RESEARCH.md` with competitor prices, interviews, cost floor,
willingness-to-pay, proposed tiers, margins, and sensitivity. Validate or reject the current price
hypotheses.

Track, when applicable:

- MRR, ARR, ARPU, CAC, LTV, gross margin, logo/revenue churn, activation, retention, conversion;
- API requests, active keys, usage, latency, error rate, and cost per request;
- analyses used, score comprehension, confusing screens, and alert value.

Analytics collection must remain proportionate and minimized.

## 17. Commercial value, IP, and strategic alternatives

Commercial differentiation must describe the customer outcome, not the presence of standard
models. A candidate proposition to test is: compare option structures using return, severe risk,
quality of evidence, model agreement, and execution conditions.

Branding and product naming wait for commercial GO, legal review, and positioning. The technical
repository need not become the product name.

Future alternatives—license technology, sell code/IP, sell the company, sell API access, or operate
a recurring SaaS—must remain distinct. Valuation, if relevant, should use ARR/MRR, growth, churn,
margins, retention, concentration, IP, data rights, track record, regulatory position, brand, and
market size, not lines of code or mathematical complexity.

## 18. Definition of commercially complete

Commercialization cannot be considered complete unless all applicable items are satisfied:

- sufficient quantitative and multi-underlying validation;
- commercial-ready data licenses;
- current legal and regulatory review;
- security and privacy review;
- pricing and willingness-to-pay tested;
- viable unit economics;
- stable product, support, monitoring, and recovery;
- defensible marketing claims;
- no unauthorized data redistribution.

## 19. Dormant-phase prohibitions

Until the entry gate and later commercial GO are explicitly passed, do not:

- create the SaaS, public application, users, organizations, auth, subscriptions, or billing;
- add Stripe or another payment provider;
- implement commercial tiers or hard-code prices;
- refactor the quantitative core solely for commercial reasons;
- expose OPRA, broker, licensed, proprietary, or user data;
- add order submission, modification, cancellation, exercise, or roll capability;
- weaken validation, holdout, score, risk, or evidence rules;
- claim edge, guaranteed performance, or regulatory safety;
- start N0–N15 merely because this roadmap exists.

## 20. Resumption procedure

When Phase M, shadow mode, paper validation, prospective evidence, and final project validation
are genuinely complete:

1. read `FINAL_PROJECT_VALIDATION.md`;
2. read this plan;
3. read `COMMERCIALIZATION_RESUME_PROMPT.md`;
4. verify the date and provenance of all final evidence;
5. refresh regulation, data licenses, competitors, pricing, and provider terms;
6. run N0–N4 as audits, not implementation;
7. produce `COMMERCIAL_GO_NO_GO.md`;
8. begin N5 only after a documented `GO` and explicit user approval.

If any prerequisite is missing, contradictory, stale, or insufficient, stop with the exact blocker.

## 21. Provenance and validation status

Source of this plan: user-supplied Phase N specification dated 2026-08-08, current repository
reports, and local vault governance/checklists. No external legal, market, licensing, competitor,
or pricing research was performed for this dormant planning document.

All regulatory, licensing, pricing, architecture, segment, moat, and valuation statements are
future hypotheses or review requirements. None is a validated execution decision.
