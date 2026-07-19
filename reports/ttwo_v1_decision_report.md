# TTWO options research decision report

> Read-only research. This report is not an investment recommendation and cannot authorize an order.

## Input posture

- Report: `TTWO-RESEARCH-20260718T120000Z`
- Analysis timestamp: `2026-07-18T12:00:00+00:00`
- Underlying: `TTWO` at $257.79
- Market-data source: `offline_tt_nasdaq_fixture`
- Fundamental direction: `bullish`
- Thesis: Illustrative bullish research thesis: release execution could lift bookings and expectations.
- Catalyst: Illustrative GTA VI release window; date requires primary-source refresh.
- Invalidation: Re-underwrite on a material release delay, guidance deterioration, or thesis-source conflict.
- Expectations implied: Not modeled; fixture target prices are explicit analyst assumptions.
- Ranked research alternatives: `ttwo-stock-research`, `ttwo-no-trade`, `ttwo-long-call`, `ttwo-long-put`, `ttwo-bull-call-spread`, `ttwo-bear-put-spread`
- Pareto research set: `ttwo-long-put`, `ttwo-no-trade`, `ttwo-stock-research`

## Warnings

- Research output only: not an investment recommendation or order instruction.
- Fixture market data is illustrative and must be replaced with timestamped live data.
- Scores compare assumptions; they do not authorize execution, sizing, or risk activation.
- American exercise, assignment, dividends, jumps, skew, and broker margin require human review.

## Candidates

### No trade / wait for proof

- ID: `ttwo-no-trade`
- Status: `no_trade`
- Description: Reference alternative that preserves capital and waits for refreshed evidence
- Legs: none
- Executable debit: $0.00
- Executable credit: $0.00
- Fees / slippage: $0.00 / $0.00
- Liquidity heuristic: 1.000
- Margin estimate: $0.00
- Maximum gain: $0.00
- Maximum loss: $0.00
- Break-even: none
- Net Greeks delta/gamma/theta/vega/rho: 0.000 / 0.000 / 0.000 / 0.000 / 0.000
- Score summary: 0.868
- Score components:
  - `thesis_fit`: 0.650
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.500
  - `payoff_quality`: 0.700
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 1.000
  - `liquidity`: 1.000
  - `cost_quality`: 1.000
  - `complexity`: 1.000
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 0.700
  - `skew_term_structure`: 0.750
  - `margin`: 1.000
  - `carry`: 1.000
  - `adverse_robustness`: 1.000
  - `data_confidence`: 0.586
- Assumptions: No position is opened
- Failure modes: Opportunity cost if the thesis resolves before evidence is refreshed
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $0.00 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `bullish_gap`: $0.00 at spot $296.46; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `bearish_gap`: $0.00 at spot $219.12; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `iv_crush`: $0.00 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `iv_expansion`: $0.00 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `gta_delay`: $0.00 at spot $232.01; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `ex_dividend`: $0.00 at spot $255.21; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `liquidity_stress`: $0.00 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_p05`: $0.00 at spot $185.91; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_p50`: $0.00 at spot $259.58; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_p95`: $0.00 at spot $363.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$0.00/$0.00

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

### TTWO stock research proxy

- ID: `ttwo-stock-research`
- Status: `human_review_required`
- Description: Illustrative long-stock comparison using a non-executable research quantity
- Leg 1: `long` 10 `TTWO` at $257.79
- Executable debit: $2,579.19
- Executable credit: $0.00
- Fees / slippage: $0.00 / $1.29
- Liquidity heuristic: 1.000
- Margin estimate: $0.00
- Maximum gain: unbounded/unknown
- Maximum loss: $2,579.19
- Break-even: $257.92
- Net Greeks delta/gamma/theta/vega/rho: 10.000 / 0.000 / 0.000 / 0.000 / 0.000
- Score summary: 0.903
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.514
  - `payoff_quality`: 0.800
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.828
  - `liquidity`: 1.000
  - `cost_quality`: 1.000
  - `complexity`: 1.000
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 1.000
  - `skew_term_structure`: 1.000
  - `margin`: 1.000
  - `carry`: 1.000
  - `adverse_robustness`: 0.721
  - `data_confidence`: 0.586
- Assumptions: Research quantity is not a sizing recommendation
- Failure modes: Full equity downside; Event delay; Multiple compression
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1.29 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `bullish_gap`: $385.40 at spot $296.46; attribution D/G/T/V/C/R $386.69/$0.00/$0.00/$0.00/$-1.29/$0.00
- `bearish_gap`: $-387.97 at spot $219.12; attribution D/G/T/V/C/R $-386.69/$0.00/$0.00/$0.00/$-1.29/$0.00
- `iv_crush`: $-1.29 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `iv_expansion`: $-1.29 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `gta_delay`: $-259.08 at spot $232.01; attribution D/G/T/V/C/R $-257.79/$0.00/$0.00/$0.00/$-1.29/$0.00
- `ex_dividend`: $-27.07 at spot $255.21; attribution D/G/T/V/C/R $-25.78/$0.00/$0.00/$0.00/$-1.29/$0.00
- `liquidity_stress`: $-1.29 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_p05`: $-720.10 at spot $185.91; attribution D/G/T/V/C/R $-718.81/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_p50`: $16.65 at spot $259.58; attribution D/G/T/V/C/R $17.94/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_p95`: $1,058.71 at spot $363.79; attribution D/G/T/V/C/R $1,060.00/$0.00/$0.00/$0.00/$-1.29/$0.00

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

### Long call

- ID: `ttwo-long-call`
- Status: `human_review_required`
- Description: Defined-premium bullish exposure across the catalyst window
- Leg 1: `long` 1 `TTWO  270115C00260000`; call 260, expiry `2027-01-15T21:00:00+00:00`, bid/ask $28.00/$30.00, multiplier 100, deliverable `100 TTWO common shares`
- Executable debit: $3,002.15
- Executable credit: $0.00
- Fees / slippage: $0.65 / $1.50
- Liquidity heuristic: 0.848
- Margin estimate: $0.00
- Maximum gain: unbounded/unknown
- Maximum loss: $3,002.15
- Break-even: $290.02
- Net Greeks delta/gamma/theta/vega/rho: 57.196 / 0.600 / -8.554 / 71.314 / 59.524
- Score summary: 0.737
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.291
  - `payoff_quality`: 0.800
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.119
  - `liquidity`: 0.848
  - `cost_quality`: 0.999
  - `complexity`: 0.900
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 0.972
  - `skew_term_structure`: 0.350
  - `margin`: 1.000
  - `carry`: 0.915
  - `adverse_robustness`: 0.005
  - `data_confidence`: 0.586
- Assumptions: Black-Scholes is indicative for an American equity option
- Failure modes: IV crush; Theta decay; Catalyst delay beyond expiration
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1,497.07 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-1,026.50/$0.00/$-102.15/$-368.41
- `bullish_gap`: $1,372.83 at spot $296.46; attribution D/G/T/V/C/R $2,211.68/$448.48/$-1,026.50/$356.57/$-102.15/$-515.25
- `bearish_gap`: $-2,524.83 at spot $219.12; attribution D/G/T/V/C/R $-2,211.68/$448.48/$-1,026.50/$713.14/$-102.15/$-346.12
- `iv_crush`: $-2,002.39 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-1,026.50/$-855.77/$-102.15/$-17.97
- `iv_expansion`: $-992.65 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-1,026.50/$855.77/$-102.15/$-719.77
- `gta_delay`: $-2,246.15 at spot $232.01; attribution D/G/T/V/C/R $-1,474.45/$199.32/$-1,026.50/$570.51/$-102.15/$-412.88
- `ex_dividend`: $-646.10 at spot $255.21; attribution D/G/T/V/C/R $-147.45/$1.99/$-256.63/$0.00/$-102.15/$-141.87
- `liquidity_stress`: $-352.53 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-256.63/$213.94/$-102.15/$-207.70
- `monte_carlo_p05`: $-2,987.30 at spot $185.91; attribution D/G/T/V/C/R $-4,111.30/$1,549.73/$-1,026.50/$0.00/$-102.15/$702.93
- `monte_carlo_p50`: $-1,400.87 at spot $259.58; attribution D/G/T/V/C/R $102.62/$0.97/$-1,026.50/$0.00/$-102.15/$-375.80
- `monte_carlo_p95`: $7,588.08 at spot $363.79; attribution D/G/T/V/C/R $6,062.74/$3,370.04/$-1,026.50/$0.00/$-102.15/$-716.05

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-LEG-1-FRESHNESS` (read_only_gate): TTWO  270115C00260000 quote must be current
- `PASS` `VETO-LEG-1-BID-ASK` (read_only_gate): TTWO  270115C00260000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-1-CONTRACT` (read_only_gate): TTWO  270115C00260000 contract semantics must be complete
- `PASS` `VETO-LEG-1-ADJUSTMENT` (read_only_gate): TTWO  270115C00260000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-1-SOURCE` (read_only_gate): TTWO  270115C00260000 quote source must authorize research use
- `PASS` `VETO-LEG-1-LIQUIDITY` (read_only_gate): TTWO  270115C00260000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

### Bull call spread

- ID: `ttwo-bull-call-spread`
- Status: `human_review_required`
- Description: Bounded-risk bullish vertical with capped upside
- Leg 1: `long` 1 `TTWO  270115C00260000`; call 260, expiry `2027-01-15T21:00:00+00:00`, bid/ask $28.00/$30.00, multiplier 100, deliverable `100 TTWO common shares`
- Leg 2: `short` 1 `TTWO  270115C00280000`; call 280, expiry `2027-01-15T21:00:00+00:00`, bid/ask $19.00/$20.50, multiplier 100, deliverable `100 TTWO common shares`
- Executable debit: $1,104.30
- Executable credit: $0.00
- Fees / slippage: $1.30 / $3.00
- Liquidity heuristic: 0.833
- Margin estimate: $0.00
- Maximum gain: $895.70
- Maximum loss: $1,104.30
- Break-even: $271.04
- Net Greeks delta/gamma/theta/vega/rho: 11.804 / -0.014 / -0.301 / -0.698 / 10.927
- Score summary: 0.690
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.226
  - `payoff_quality`: 0.406
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.563
  - `liquidity`: 0.833
  - `cost_quality`: 0.995
  - `complexity`: 0.700
  - `assignment_early_exercise`: 0.600
  - `iv_rv_context`: 0.979
  - `skew_term_structure`: 0.350
  - `margin`: 0.800
  - `carry`: 0.992
  - `adverse_robustness`: 0.011
  - `data_confidence`: 0.586
- Assumptions: Both legs execute together at the modeled executable net debit
- Failure modes: Capped upside; Assignment and pin risk; Legging risk
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-350.10 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-36.13/$0.00/$-179.30/$-134.68
- `bullish_gap`: $299.78 at spot $296.46; attribution D/G/T/V/C/R $456.45/$-10.77/$-36.13/$-3.49/$-179.30/$73.02
- `bearish_gap`: $-848.05 at spot $219.12; attribution D/G/T/V/C/R $-456.45/$-10.77/$-36.13/$-6.98/$-179.30/$-158.42
- `iv_crush`: $-425.95 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-36.13/$8.38/$-179.30/$-218.90
- `iv_expansion`: $-319.73 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-36.13/$-8.38/$-179.30/$-95.92
- `gta_delay`: $-716.50 at spot $232.01; attribution D/G/T/V/C/R $-304.30/$-4.79/$-36.13/$-5.59/$-179.30/$-186.40
- `ex_dividend`: $-304.29 at spot $255.21; attribution D/G/T/V/C/R $-30.43/$-0.05/$-9.03/$0.00/$-179.30/$-85.48
- `liquidity_stress`: $-289.83 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-9.03/$-2.10/$-179.30/$-99.40
- `monte_carlo_p05`: $-1,092.31 at spot $185.91; attribution D/G/T/V/C/R $-848.49/$-37.22/$-36.13/$0.00/$-179.30/$8.83
- `monte_carlo_p50`: $-314.47 at spot $259.58; attribution D/G/T/V/C/R $21.18/$-0.02/$-36.13/$0.00/$-179.30/$-120.20
- `monte_carlo_p95`: $837.87 at spot $363.79; attribution D/G/T/V/C/R $1,251.23/$-80.93/$-36.13/$0.00/$-179.30/$-117.01

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-LEG-1-FRESHNESS` (read_only_gate): TTWO  270115C00260000 quote must be current
- `PASS` `VETO-LEG-1-BID-ASK` (read_only_gate): TTWO  270115C00260000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-1-CONTRACT` (read_only_gate): TTWO  270115C00260000 contract semantics must be complete
- `PASS` `VETO-LEG-1-ADJUSTMENT` (read_only_gate): TTWO  270115C00260000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-1-SOURCE` (read_only_gate): TTWO  270115C00260000 quote source must authorize research use
- `PASS` `VETO-LEG-1-LIQUIDITY` (read_only_gate): TTWO  270115C00260000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-LEG-2-FRESHNESS` (read_only_gate): TTWO  270115C00280000 quote must be current
- `PASS` `VETO-LEG-2-BID-ASK` (read_only_gate): TTWO  270115C00280000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-2-CONTRACT` (read_only_gate): TTWO  270115C00280000 contract semantics must be complete
- `PASS` `VETO-LEG-2-ADJUSTMENT` (read_only_gate): TTWO  270115C00280000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-2-SOURCE` (read_only_gate): TTWO  270115C00280000 quote source must authorize research use
- `PASS` `VETO-LEG-2-LIQUIDITY` (read_only_gate): TTWO  270115C00280000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- `PASS` `GATE-ASSIGNMENT-PIN` (read_only_gate): American early assignment and expiration pin risk require human review
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

### Long put

- ID: `ttwo-long-put`
- Status: `human_review_required`
- Description: Defined-premium bearish or downside-event research exposure
- Leg 1: `long` 1 `TTWO  270115P00260000`; put 260, expiry `2027-01-15T21:00:00+00:00`, bid/ask $25.00/$27.00, multiplier 100, deliverable `100 TTWO common shares`
- Executable debit: $2,702.15
- Executable credit: $0.00
- Fees / slippage: $0.65 / $1.50
- Liquidity heuristic: 0.831
- Margin estimate: $0.00
- Maximum gain: $23,297.85
- Maximum loss: $2,702.15
- Break-even: $232.98
- Net Greeks delta/gamma/theta/vega/rho: -42.724 / 0.583 / -5.607 / 71.287 / -67.068
- Score summary: 0.705
- Score components:
  - `thesis_fit`: 0.150
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.231
  - `payoff_quality`: 1.000
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.344
  - `liquidity`: 0.831
  - `cost_quality`: 0.999
  - `complexity`: 0.900
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 0.946
  - `skew_term_structure`: 0.350
  - `margin`: 1.000
  - `carry`: 0.938
  - `adverse_robustness`: 0.007
  - `data_confidence`: 0.586
- Assumptions: Black-Scholes is indicative for an American equity option
- Failure modes: IV crush; Theta decay; Bullish gap
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1,129.99 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-672.87/$0.00/$-102.15/$-354.97
- `bullish_gap`: $-2,136.69 at spot $296.46; attribution D/G/T/V/C/R $-1,652.06/$436.19/$-672.87/$356.44/$-102.15/$-502.25
- `bearish_gap`: $1,693.84 at spot $219.12; attribution D/G/T/V/C/R $1,652.06/$436.19/$-672.87/$712.87/$-102.15/$-332.27
- `iv_crush`: $-1,635.25 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-672.87/$-855.45/$-102.15/$-4.78
- `iv_expansion`: $-625.66 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-672.87/$855.45/$-102.15/$-706.09
- `gta_delay`: $690.39 at spot $232.01; attribution D/G/T/V/C/R $1,101.37/$193.86/$-672.87/$570.30/$-102.15/$-400.13
- `ex_dividend`: $-282.92 at spot $255.21; attribution D/G/T/V/C/R $110.14/$1.94/$-168.22/$0.00/$-102.15/$-124.63
- `liquidity_stress`: $-247.13 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$-168.22/$213.86/$-102.15/$-190.62
- `monte_carlo_p05`: $-2,683.47 at spot $364.00; attribution D/G/T/V/C/R $-4,537.47/$3,290.46/$-672.87/$0.00/$-102.15/$-661.45
- `monte_carlo_p50`: $-1,216.17 at spot $259.65; attribution D/G/T/V/C/R $-79.55/$1.01/$-672.87/$0.00/$-102.15/$-362.62
- `monte_carlo_p95`: $4,407.03 at spot $187.15; attribution D/G/T/V/C/R $3,017.84/$1,455.53/$-672.87/$0.00/$-102.15/$708.67

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-LEG-1-FRESHNESS` (read_only_gate): TTWO  270115P00260000 quote must be current
- `PASS` `VETO-LEG-1-BID-ASK` (read_only_gate): TTWO  270115P00260000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-1-CONTRACT` (read_only_gate): TTWO  270115P00260000 contract semantics must be complete
- `PASS` `VETO-LEG-1-ADJUSTMENT` (read_only_gate): TTWO  270115P00260000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-1-SOURCE` (read_only_gate): TTWO  270115P00260000 quote source must authorize research use
- `PASS` `VETO-LEG-1-LIQUIDITY` (read_only_gate): TTWO  270115P00260000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

### Bear put spread

- ID: `ttwo-bear-put-spread`
- Status: `human_review_required`
- Description: Bounded-risk bearish vertical with capped payoff
- Leg 1: `long` 1 `TTWO  270115P00260000`; put 260, expiry `2027-01-15T21:00:00+00:00`, bid/ask $25.00/$27.00, multiplier 100, deliverable `100 TTWO common shares`
- Leg 2: `short` 1 `TTWO  270115P00250000`; put 250, expiry `2027-01-15T21:00:00+00:00`, bid/ask $20.00/$22.00, multiplier 100, deliverable `100 TTWO common shares`
- Executable debit: $704.30
- Executable credit: $0.00
- Fees / slippage: $1.30 / $3.00
- Liquidity heuristic: 0.790
- Margin estimate: $0.00
- Maximum gain: $295.70
- Maximum loss: $704.30
- Break-even: $252.96
- Net Greeks delta/gamma/theta/vega/rho: -5.761 / 0.030 / 0.059 / 2.697 / -9.644
- Score summary: 0.623
- Score components:
  - `thesis_fit`: 0.150
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.177
  - `payoff_quality`: 0.210
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.659
  - `liquidity`: 0.790
  - `cost_quality`: 0.991
  - `complexity`: 0.700
  - `assignment_early_exercise`: 0.600
  - `iv_rv_context`: 0.940
  - `skew_term_structure`: 0.350
  - `margin`: 0.800
  - `carry`: 1.000
  - `adverse_robustness`: 0.013
  - `data_confidence`: 0.586
- Assumptions: Both legs execute together at the modeled executable net debit
- Failure modes: Capped downside payoff; Assignment and pin risk; Legging risk
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-246.28 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$7.04/$0.00/$-204.30/$-49.02
- `bullish_gap`: $-515.90 at spot $296.46; attribution D/G/T/V/C/R $-222.76/$22.10/$7.04/$13.49/$-204.30/$-131.47
- `bearish_gap`: $74.35 at spot $219.12; attribution D/G/T/V/C/R $222.76/$22.10/$7.04/$26.97/$-204.30/$-0.23
- `iv_crush`: $-278.12 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$7.04/$-32.37/$-204.30/$-48.50
- `iv_expansion`: $-224.99 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$7.04/$32.37/$-204.30/$-60.10
- `gta_delay`: $-15.08 at spot $232.01; attribution D/G/T/V/C/R $148.51/$9.82/$7.04/$21.58/$-204.30/$2.26
- `ex_dividend`: $-230.54 at spot $255.21; attribution D/G/T/V/C/R $14.85/$0.10/$1.76/$0.00/$-204.30/$-42.95
- `liquidity_stress`: $-254.34 at spot $257.79; attribution D/G/T/V/C/R $0.00/$0.00/$1.76/$8.09/$-204.30/$-59.90
- `monte_carlo_p05`: $-695.09 at spot $364.00; attribution D/G/T/V/C/R $-611.83/$166.71/$7.04/$0.00/$-204.30/$-52.71
- `monte_carlo_p50`: $-264.77 at spot $259.65; attribution D/G/T/V/C/R $-10.73/$0.05/$7.04/$0.00/$-204.30/$-56.84
- `monte_carlo_p95`: $265.35 at spot $187.15; attribution D/G/T/V/C/R $406.92/$73.74/$7.04/$0.00/$-204.30/$-18.07

Rules and evidence:

- `PASS` `R-DECISION-001` (read_only_gate): Compare no-trade, stock, directional option, and bounded spread alternatives
- `PASS` `R-GREEKS-001` (read_only_gate): Aggregate Greeks using each contract multiplier
- `PASS` `R-OPTIONS-001` (read_only_gate): Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit
- `PASS` `VETO-PROVENANCE` (read_only_gate): Decision inputs must have explicit provenance
- `PASS` `VETO-EVIDENCE-STATUS` (read_only_gate): All decision evidence is validated for research
- `PASS` `VETO-RULE-STATUS` (read_only_gate): Candidate rules are usable as read-only gates
- `PASS` `VETO-UNDERLYING-FRESHNESS` (read_only_gate): Underlying snapshot must be current for its declared fixture window
- `PASS` `VETO-FUNDAMENTALS-FRESHNESS` (read_only_gate): fundamentals input must be current within its declared maximum age
- `PASS` `VETO-PORTFOLIO-FRESHNESS` (read_only_gate): portfolio input must be current within its declared maximum age
- `PASS` `VETO-RISK-FREE-RATE-FRESHNESS` (read_only_gate): risk-free-rate input must be current within its declared maximum age
- `PASS` `VETO-VOLATILITY-FRESHNESS` (read_only_gate): volatility input must be current within its declared maximum age
- `PASS` `VETO-LEG-1-FRESHNESS` (read_only_gate): TTWO  270115P00260000 quote must be current
- `PASS` `VETO-LEG-1-BID-ASK` (read_only_gate): TTWO  270115P00260000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-1-CONTRACT` (read_only_gate): TTWO  270115P00260000 contract semantics must be complete
- `PASS` `VETO-LEG-1-ADJUSTMENT` (read_only_gate): TTWO  270115P00260000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-1-SOURCE` (read_only_gate): TTWO  270115P00260000 quote source must authorize research use
- `PASS` `VETO-LEG-1-LIQUIDITY` (read_only_gate): TTWO  270115P00260000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-LEG-2-FRESHNESS` (read_only_gate): TTWO  270115P00250000 quote must be current
- `PASS` `VETO-LEG-2-BID-ASK` (read_only_gate): TTWO  270115P00250000 requires a positive, ordered bid/ask
- `PASS` `VETO-LEG-2-CONTRACT` (read_only_gate): TTWO  270115P00250000 contract semantics must be complete
- `PASS` `VETO-LEG-2-ADJUSTMENT` (read_only_gate): TTWO  270115P00250000 adjusted deliverable must be understood
- `PASS` `VETO-LEG-2-SOURCE` (read_only_gate): TTWO  270115P00250000 quote source must authorize research use
- `PASS` `VETO-LEG-2-LIQUIDITY` (read_only_gate): TTWO  270115P00250000 requires non-zero volume/OI and <=35% relative spread
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- `PASS` `GATE-ASSIGNMENT-PIN` (read_only_gate): American early assignment and expiration pin risk require human review
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

## Required before any future execution layer

- Refresh spot, complete option chain, IV surface, rates, events, dividends, borrow, fees, and margin.
- Reconcile broker contract semantics and executable combo quotes.
- Independently validate thesis, catalyst dates, invalidation, payoff, assignment, and exit rules.
- Complete paper validation and explicit human approval under a separately reviewed execution policy.
