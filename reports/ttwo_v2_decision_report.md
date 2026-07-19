# TTWO options research decision report

> Read-only research. This report is not an investment recommendation and cannot authorize an order.

## Input posture

- Report: `TTWO-RESEARCH-20260718T120000Z`
- Analysis timestamp: `2026-07-18T12:00:00+00:00`
- Model readiness: `screen_grade`
- Underlying: `TTWO` at $257.79
- Market-data source: `offline_tt_nasdaq_fixture`
- Fundamental direction: `bullish`
- Thesis: Illustrative bullish research thesis: release execution could lift bookings and expectations.
- Catalyst: Illustrative GTA VI release window; date requires primary-source refresh.
- Invalidation: Re-underwrite on a material release delay, guidance deterioration, or thesis-source conflict.
- Expectations implied: Not modeled; fixture target prices are explicit analyst assumptions.
- Ranked research alternatives: `ttwo-stock-research`, `ttwo-no-trade`, `ttwo-long-call`, `ttwo-bull-call-spread`, `ttwo-long-put`, `ttwo-bear-put-spread`
- Pareto research set: `ttwo-long-put`, `ttwo-no-trade`, `ttwo-stock-research`

## Warnings

- Research output only: not an investment recommendation or order instruction.
- Fixture market data is illustrative and must be replaced with timestamped live data.
- Scores compare assumptions; they do not authorize execution, sizing, or risk activation.
- American values use QuantLib finite differences; assignment and pin flags still require human review.
- Jump and stochastic-volatility scenarios are model comparisons, not forecasts.

## Model limitations

- Model outputs are screen-grade until calibrated on source-backed TTWO history
- Synthetic fixtures and heuristic thresholds do not constitute out-of-sample evidence
- Assignment and pin levels are deterministic flags, not event probabilities
- Merton jump parameters are not source-backed calibrated
- Heston parameters are not source-backed calibrated

## Volatility surface

- Available: `true`
- Expiries / strikes: 2 / 3
- Interpolated / extrapolated contracts: 6 / 0

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
- Score summary: 0.881
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
  - `skew_term_structure`: 1.000
  - `margin`: 1.000
  - `carry`: 1.000
  - `adverse_robustness`: 1.000
  - `data_confidence`: 0.544
- Assumptions: No position is opened
- Failure modes: Opportunity cost if the thesis resolves before evidence is refreshed
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $0.00 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `bullish_gap`: $0.00 at spot $296.46; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `bearish_gap`: $0.00 at spot $219.12; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `iv_crush`: $0.00 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `iv_expansion`: $0.00 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `gta_delay`: $0.00 at spot $232.01; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `ex_dividend`: $0.00 at spot $255.21; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `liquidity_stress`: $0.00 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_gbm_p05`: $0.00 at spot $185.91; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_gbm_p50`: $0.00 at spot $259.58; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_gbm_p95`: $0.00 at spot $363.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $0.00 at spot $179.14; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $0.00 at spot $253.00; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $0.00 at spot $355.95; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_heston_full_truncation_p05`: $0.00 at spot $179.44; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_heston_full_truncation_p50`: $0.00 at spot $263.57; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00
- `monte_carlo_heston_full_truncation_p95`: $0.00 at spot $332.27; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$0.00/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
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
- Score summary: 0.898
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.514
  - `payoff_quality`: 0.800
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.821
  - `liquidity`: 1.000
  - `cost_quality`: 1.000
  - `complexity`: 1.000
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 1.000
  - `skew_term_structure`: 1.000
  - `margin`: 1.000
  - `carry`: 1.000
  - `adverse_robustness`: 0.695
  - `data_confidence`: 0.544
- Assumptions: Research quantity is not a sizing recommendation
- Failure modes: Full equity downside; Event delay; Multiple compression
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1.29 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `bullish_gap`: $385.40 at spot $296.46; attribution D/G/T/V/R/C/resid $386.69/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `bearish_gap`: $-387.97 at spot $219.12; attribution D/G/T/V/R/C/resid $-386.69/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `iv_crush`: $-1.29 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `iv_expansion`: $-1.29 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `gta_delay`: $-259.08 at spot $232.01; attribution D/G/T/V/R/C/resid $-257.79/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `ex_dividend`: $-27.07 at spot $255.21; attribution D/G/T/V/R/C/resid $-25.78/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `liquidity_stress`: $-1.29 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_gbm_p05`: $-720.10 at spot $185.91; attribution D/G/T/V/R/C/resid $-718.81/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_gbm_p50`: $16.65 at spot $259.58; attribution D/G/T/V/R/C/resid $17.94/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_gbm_p95`: $1,058.71 at spot $363.79; attribution D/G/T/V/R/C/resid $1,060.00/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $-787.75 at spot $179.14; attribution D/G/T/V/R/C/resid $-786.46/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $-49.23 at spot $253.00; attribution D/G/T/V/R/C/resid $-47.94/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $980.35 at spot $355.95; attribution D/G/T/V/R/C/resid $981.64/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_heston_full_truncation_p05`: $-784.84 at spot $179.44; attribution D/G/T/V/R/C/resid $-783.55/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_heston_full_truncation_p50`: $56.51 at spot $263.57; attribution D/G/T/V/R/C/resid $57.80/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00
- `monte_carlo_heston_full_truncation_p95`: $743.55 at spot $332.27; attribution D/G/T/V/R/C/resid $744.84/$0.00/$0.00/$0.00/$0.00/$-1.29/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
- `PASS` `VETO-CORPORATE-ACTIONS` (read_only_gate): Corporate actions are explicitly handled
- `PASS` `VETO-EVENT-RISK` (read_only_gate): Critical market events are explicitly handled
- `PASS` `VETO-COSTS` (read_only_gate): Fees and slippage must be explicit for the instrument
- `PASS` `VETO-MARGIN` (read_only_gate): Broker margin must be known for any structure containing a short option
- `PASS` `VETO-MAX-LOSS` (read_only_gate): Maximum loss must be explicitly calculated
- `PASS` `VETO-UNBOUNDED-RISK` (read_only_gate): Unbounded-risk structures are disabled in V1
- `PASS` `VETO-CATALYST-COVERAGE` (read_only_gate): Option expiration must cover the declared catalyst window
- `PASS` `VETO-SCENARIOS` (read_only_gate): Delay, gap, IV, event, and liquidity scenarios must be visible
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
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
- Net Greeks delta/gamma/theta/vega/rho: 57.201 / 0.607 / -8.509 / 71.310 / 59.555
- Option model diagnostics:
  - `TTWO  270115C00260000`: `quantlib_fd_american` price $27.38, European $27.38, early-exercise premium $0.00
- Exercise-risk diagnostics:
  - `TTWO  270115C00260000` `long`: assignment `low`, pin `low`, extrinsic $27.38
- Score summary: 0.774
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.291
  - `payoff_quality`: 0.800
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.118
  - `liquidity`: 0.848
  - `cost_quality`: 0.999
  - `complexity`: 0.900
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 0.972
  - `skew_term_structure`: 1.000
  - `margin`: 1.000
  - `carry`: 0.915
  - `adverse_robustness`: 0.002
  - `data_confidence`: 0.544
- Assumptions: QuantLib American model values are indicative and not executable quotes
- Failure modes: IV crush; Theta decay; Catalyst delay beyond expiration
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1,517.09 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-1,252.74/$0.00/$0.00/$-264.35/$0.00
- `bullish_gap`: $1,358.87 at spot $296.46; attribution D/G/T/V/R/C/resid $2,211.87/$408.29/$-1,148.20/$151.26/$0.00/$-264.35/$0.00
- `bearish_gap`: $-2,538.46 at spot $219.12; attribution D/G/T/V/R/C/resid $-2,211.87/$480.80/$-779.92/$236.88/$0.00/$-264.35/$0.00
- `iv_crush`: $-2,021.19 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-1,252.74/$-504.11/$0.00/$-264.35/$0.00
- `iv_expansion`: $-1,013.83 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-1,252.74/$503.25/$0.00/$-264.35/$0.00
- `gta_delay`: $-2,263.08 at spot $232.01; attribution D/G/T/V/R/C/resid $-1,474.58/$211.13/$-991.40/$256.11/$0.00/$-264.35/$0.00
- `ex_dividend`: $-672.36 at spot $255.21; attribution D/G/T/V/R/C/resid $-147.46/$2.03/$-262.58/$0.00/$0.00/$-264.35/$0.00
- `liquidity_stress`: $-378.87 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-265.00/$196.02/$0.00/$-309.90/$0.00
- `monte_carlo_gbm_p05`: $-2,988.66 at spot $185.91; attribution D/G/T/V/R/C/resid $-4,111.66/$1,649.57/$-262.22/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_gbm_p50`: $-1,420.90 at spot $259.58; attribution D/G/T/V/R/C/resid $102.63/$0.97/$-1,260.16/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_gbm_p95`: $7,592.55 at spot $363.79; attribution D/G/T/V/R/C/resid $6,063.27/$2,422.18/$-628.55/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $-2,995.94 at spot $179.14; attribution D/G/T/V/R/C/resid $-4,498.61/$1,958.00/$-190.99/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $-1,757.25 at spot $253.00; attribution D/G/T/V/R/C/resid $-274.22/$7.05/$-1,225.74/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $6,815.78 at spot $355.95; attribution D/G/T/V/R/C/resid $5,615.09/$2,137.58/$-672.53/$0.00/$0.00/$-264.35/$0.00
- `monte_carlo_heston_full_truncation_p05`: $-2,980.05 at spot $162.15; attribution D/G/T/V/R/C/resid $-5,470.81/$2,806.68/$-73.09/$21.51/$0.00/$-264.35/$0.00
- `monte_carlo_heston_full_truncation_p50`: $-1,395.60 at spot $267.22; attribution D/G/T/V/R/C/resid $539.37/$26.41/$-1,275.84/$-421.18/$0.00/$-264.35/$0.00
- `monte_carlo_heston_full_truncation_p95`: $4,461.27 at spot $330.73; attribution D/G/T/V/R/C/resid $4,172.48/$1,293.02/$-853.17/$113.28/$0.00/$-264.35/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
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
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
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
- Net Greeks delta/gamma/theta/vega/rho: 12.021 / -0.018 / -0.349 / -0.621 / 11.112
- Option model diagnostics:
  - `TTWO  270115C00260000`: `quantlib_fd_american` price $27.38, European $27.38, early-exercise premium $0.00
  - `TTWO  270115C00280000`: `quantlib_fd_american` price $18.81, European $18.81, early-exercise premium $0.00
- Exercise-risk diagnostics:
  - `TTWO  270115C00260000` `long`: assignment `low`, pin `low`, extrinsic $27.38
  - `TTWO  270115C00280000` `short`: assignment `low`, pin `low`, extrinsic $18.81
- Score summary: 0.739
- Score components:
  - `thesis_fit`: 1.000
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.226
  - `payoff_quality`: 0.406
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.553
  - `liquidity`: 0.833
  - `cost_quality`: 0.995
  - `complexity`: 0.700
  - `assignment_early_exercise`: 0.800
  - `iv_rv_context`: 0.979
  - `skew_term_structure`: 1.000
  - `margin`: 0.800
  - `carry`: 0.991
  - `adverse_robustness`: 0.005
  - `data_confidence`: 0.544
- Assumptions: Both legs execute together at the modeled executable net debit
- Failure modes: Capped upside; Assignment and pin risk; Legging risk
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-345.43 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-97.97/$0.00/$0.00/$-247.46/$0.00
- `bullish_gap`: $313.50 at spot $296.46; attribution D/G/T/V/R/C/resid $464.84/$-35.17/$193.58/$-62.30/$0.00/$-247.46/$0.00
- `bearish_gap`: $-849.69 at spot $219.12; attribution D/G/T/V/R/C/resid $-464.84/$17.37/$-253.08/$98.33/$0.00/$-247.46/$0.00
- `iv_crush`: $-425.10 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-97.97/$-79.67/$0.00/$-247.46/$0.00
- `iv_expansion`: $-313.46 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-97.97/$31.97/$0.00/$-247.46/$0.00
- `gta_delay`: $-716.84 at spot $232.01; attribution D/G/T/V/R/C/resid $-309.89/$3.07/$-245.54/$82.98/$0.00/$-247.46/$0.00
- `ex_dividend`: $-293.60 at spot $255.21; attribution D/G/T/V/R/C/resid $-30.99/$-0.05/$-15.10/$0.00/$0.00/$-247.46/$0.00
- `liquidity_stress`: $-278.27 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-12.21/$-0.14/$0.00/$-265.91/$0.00
- `monte_carlo_gbm_p05`: $-1,093.21 at spot $185.91; attribution D/G/T/V/R/C/resid $-864.10/$146.01/$-127.66/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_gbm_p50`: $-309.15 at spot $259.58; attribution D/G/T/V/R/C/resid $21.57/$-0.03/$-83.22/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_gbm_p95`: $843.61 at spot $363.79; attribution D/G/T/V/R/C/resid $1,274.24/$-388.23/$205.05/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $-1,099.06 at spot $179.14; attribution D/G/T/V/R/C/resid $-945.42/$192.01/$-98.19/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $-440.84 at spot $253.00; attribution D/G/T/V/R/C/resid $-57.63/$-0.14/$-135.60/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $827.24 at spot $355.95; attribution D/G/T/V/R/C/resid $1,180.05/$-327.99/$222.64/$0.00/$0.00/$-247.46/$0.00
- `monte_carlo_heston_full_truncation_p05`: $-1,090.36 at spot $162.15; attribution D/G/T/V/R/C/resid $-1,149.73/$335.61/$-42.19/$13.42/$0.00/$-247.46/$0.00
- `monte_carlo_heston_full_truncation_p50`: $-254.77 at spot $263.57; attribution D/G/T/V/R/C/resid $69.48/$-0.37/$-49.64/$-26.77/$0.00/$-247.46/$0.00
- `monte_carlo_heston_full_truncation_p95`: $877.25 at spot $311.55; attribution D/G/T/V/R/C/resid $646.25/$-79.49/$247.85/$310.10/$0.00/$-247.46/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
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
- `PASS` `GATE-ASSIGNMENT-PIN` (read_only_gate): American assignment and pin risk require human review (TTWO  270115C00280000: assignment=low, pin risk=low)
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
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
- Net Greeks delta/gamma/theta/vega/rho: -43.983 / 0.599 / -6.087 / 71.055 / -52.670
- Option model diagnostics:
  - `TTWO  270115P00260000`: `quantlib_fd_american` price $25.78, European $25.27, early-exercise premium $0.52
- Exercise-risk diagnostics:
  - `TTWO  270115P00260000` `long`: assignment `low`, pin `low`, extrinsic $23.57
- Score summary: 0.737
- Score components:
  - `thesis_fit`: 0.150
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.231
  - `payoff_quality`: 1.000
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.255
  - `liquidity`: 0.831
  - `cost_quality`: 0.999
  - `complexity`: 0.900
  - `assignment_early_exercise`: 1.000
  - `iv_rv_context`: 0.946
  - `skew_term_structure`: 1.000
  - `margin`: 1.000
  - `carry`: 0.932
  - `adverse_robustness`: 0.000
  - `data_confidence`: 0.544
- Assumptions: QuantLib American model values are indicative and not executable quotes
- Failure modes: IV crush; Theta decay; Bullish gap
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-1,092.81 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-969.13/$0.00/$0.00/$-123.68/$0.00
- `bullish_gap`: $-2,117.02 at spot $296.46; attribution D/G/T/V/R/C/resid $-1,700.76/$404.97/$-855.17/$157.62/$0.00/$-123.68/$0.00
- `bearish_gap`: $1,755.87 at spot $219.12; attribution D/G/T/V/R/C/resid $1,700.76/$486.84/$-536.99/$228.94/$0.00/$-123.68/$0.00
- `iv_crush`: $-1,594.87 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-969.13/$-502.05/$0.00/$-123.68/$0.00
- `iv_expansion`: $-590.87 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-969.13/$501.94/$0.00/$-123.68/$0.00
- `gta_delay`: $741.72 at spot $232.01; attribution D/G/T/V/R/C/resid $1,133.84/$212.19/$-733.98/$253.35/$0.00/$-123.68/$0.00
- `ex_dividend`: $-198.81 at spot $255.21; attribution D/G/T/V/R/C/resid $113.38/$2.01/$-190.52/$0.00/$0.00/$-123.68/$0.00
- `liquidity_stress`: $-166.59 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$-192.53/$195.35/$0.00/$-169.41/$0.00
- `monte_carlo_gbm_p05`: $-2,681.28 at spot $364.00; attribution D/G/T/V/R/C/resid $-4,671.24/$2,421.16/$-307.52/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_gbm_p50`: $-1,180.10 at spot $259.65; attribution D/G/T/V/R/C/resid $-81.90/$1.05/$-975.57/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_gbm_p95`: $4,582.49 at spot $187.15; attribution D/G/T/V/R/C/resid $3,106.81/$1,661.54/$-62.17/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $-2,675.54 at spot $359.08; attribution D/G/T/V/R/C/resid $-4,455.22/$2,240.99/$-337.63/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $-872.39 at spot $253.39; attribution D/G/T/V/R/C/resid $193.48/$5.91/$-948.09/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $5,228.19 at spot $180.70; attribution D/G/T/V/R/C/resid $3,390.81/$1,979.40/$-18.34/$0.00/$0.00/$-123.68/$0.00
- `monte_carlo_heston_full_truncation_p05`: $-2,702.11 at spot $308.75; attribution D/G/T/V/R/C/resid $-2,241.17/$675.53/$-750.89/$-261.90/$0.00/$-123.68/$0.00
- `monte_carlo_heston_full_truncation_p50`: $-1,750.82 at spot $258.03; attribution D/G/T/V/R/C/resid $-10.72/$0.02/$-970.06/$-646.38/$0.00/$-123.68/$0.00
- `monte_carlo_heston_full_truncation_p95`: $5,354.33 at spot $179.44; attribution D/G/T/V/R/C/resid $3,446.29/$2,044.52/$-12.79/$-0.02/$0.00/$-123.68/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
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
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
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
- Net Greeks delta/gamma/theta/vega/rho: -5.958 / 0.035 / 0.088 / 2.309 / -5.579
- Option model diagnostics:
  - `TTWO  270115P00260000`: `quantlib_fd_american` price $25.78, European $25.27, early-exercise premium $0.52
  - `TTWO  270115P00250000`: `quantlib_fd_american` price $21.42, European $21.03, early-exercise premium $0.39
- Exercise-risk diagnostics:
  - `TTWO  270115P00260000` `long`: assignment `low`, pin `low`, extrinsic $23.57
  - `TTWO  270115P00250000` `short`: assignment `low`, pin `low`, extrinsic $21.42
- Score summary: 0.672
- Score components:
  - `thesis_fit`: 0.150
  - `catalyst_coverage`: 1.000
  - `expected_payoff`: 0.177
  - `payoff_quality`: 0.210
  - `max_loss_quality`: 1.000
  - `assumption_sensitivity`: 0.645
  - `liquidity`: 0.790
  - `cost_quality`: 0.991
  - `complexity`: 0.700
  - `assignment_early_exercise`: 0.800
  - `iv_rv_context`: 0.940
  - `skew_term_structure`: 1.000
  - `margin`: 0.800
  - `carry`: 1.000
  - `adverse_robustness`: 0.000
  - `data_confidence`: 0.544
- Assumptions: Both legs execute together at the modeled executable net debit
- Failure modes: Capped downside payoff; Assignment and pin risk; Legging risk
- Contradictions: none recorded

Scenario P&L (illustrative):

- `base_time_passage`: $-259.27 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$8.65/$0.00/$0.00/$-267.92/$0.00
- `bullish_gap`: $-524.74 at spot $296.46; attribution D/G/T/V/R/C/resid $-230.39/$36.22/$-94.11/$31.46/$0.00/$-267.92/$0.00
- `bearish_gap`: $70.34 at spot $219.12; attribution D/G/T/V/R/C/resid $230.39/$21.85/$142.80/$-56.78/$0.00/$-267.92/$0.00
- `iv_crush`: $-286.98 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$8.65/$-27.70/$0.00/$-267.92/$0.00
- `iv_expansion`: $-239.89 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$8.65/$19.39/$0.00/$-267.92/$0.00
- `gta_delay`: $-24.44 at spot $232.01; attribution D/G/T/V/R/C/resid $153.59/$11.33/$110.81/$-32.25/$0.00/$-267.92/$0.00
- `ex_dividend`: $-248.40 at spot $255.21; attribution D/G/T/V/R/C/resid $15.36/$0.13/$4.03/$0.00/$0.00/$-267.92/$0.00
- `liquidity_stress`: $-273.60 at spot $257.79; attribution D/G/T/V/R/C/resid $0.00/$0.00/$2.67/$6.41/$0.00/$-282.68/$0.00
- `monte_carlo_gbm_p05`: $-695.42 at spot $364.00; attribution D/G/T/V/R/C/resid $-632.78/$265.35/$-60.07/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_gbm_p50`: $-277.75 at spot $259.65; attribution D/G/T/V/R/C/resid $-11.09/$0.09/$1.18/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_gbm_p95`: $295.70 at spot $183.00; attribution D/G/T/V/R/C/resid $445.62/$36.80/$81.20/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_merton_jump_diffusion_p05`: $-693.08 at spot $359.08; attribution D/G/T/V/R/C/resid $-603.52/$243.25/$-64.89/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_merton_jump_diffusion_p50`: $-214.58 at spot $253.39; attribution D/G/T/V/R/C/resid $26.21/$0.39/$26.74/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_merton_jump_diffusion_p95`: $295.70 at spot $165.97; attribution D/G/T/V/R/C/resid $547.05/$15.64/$0.93/$0.00/$0.00/$-267.92/$0.00
- `monte_carlo_heston_full_truncation_p05`: $-704.26 at spot $308.75; attribution D/G/T/V/R/C/resid $-303.60/$63.59/$-100.79/$-95.54/$0.00/$-267.92/$0.00
- `monte_carlo_heston_full_truncation_p50`: $-318.31 at spot $270.01; attribution D/G/T/V/R/C/resid $-72.82/$3.45/$-36.89/$55.87/$0.00/$-267.92/$0.00
- `monte_carlo_heston_full_truncation_p95`: $295.68 at spot $228.42; attribution D/G/T/V/R/C/resid $174.96/$14.14/$121.82/$252.68/$0.00/$-267.92/$0.00

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
- `PASS` `VETO-DIVIDEND-YIELD-FRESHNESS` (read_only_gate): Dividend-yield input must be current
- `PASS` `VETO-VOL-SURFACE-FRESHNESS` (read_only_gate): Volatility surface must be current
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
- `PASS` `GATE-ASSIGNMENT-PIN` (read_only_gate): American assignment and pin risk require human review (TTWO  270115P00250000: assignment=low, pin risk=low)
- `FAIL` `GATE-MODEL-CALIBRATION` (read_only_gate): Screen-grade uncalibrated models: merton_jump_diffusion, heston_full_truncation
- Evidence `CORPUS-CLEAN-RULESET-2026` (read_only_gate, high): `option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md`
- Evidence `CORPUS-TTWO-OPERATIONAL-2026` (read_only_gate, medium): `option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md`

## Required before any future execution layer

- Refresh spot, complete option chain, IV surface, rates, events, dividends, borrow, fees, and margin.
- Reconcile broker contract semantics and executable combo quotes.
- Independently validate thesis, catalyst dates, invalidation, payoff, assignment, and exit rules.
- Complete paper validation and explicit human approval under a separately reviewed execution policy.
