# Formula lineage matrix

Generated from the canonical registries on 2026-08-08. The validation script checks exact Formula
ID coverage and every referenced file/symbol.

| Formula ID | Source IDs | Implementation | Tests | Status |
| --- | --- | --- | --- | --- |
| `FORM-MEASURE-CHANGE-001` | book-bjork-arbitrage-theory, book-andersen-piterbarg-interest-rate-modeling | src/take_two_options/quantitative/contracts.py<br>src/take_two_options/intelligence/stochastic.py<br>src/take_two_options/simulation/legacy_models.py | tests/test_quantitative_foundations.py | `tested` |
| `FORM-DISCOUNT-FACTOR-001` | book-bjork-arbitrage-theory, book-andersen-piterbarg-interest-rate-modeling | src/take_two_options/quantitative/contracts.py | tests/test_quantitative_foundations.py | `tested` |
| `FORM-BS-PRICE-001` | book-bjork-arbitrage-theory | src/take_two_options/pricing.py<br>src/take_two_options/american.py | tests/test_quantitative_foundations.py | `numerically_validated` |
| `FORM-FD-CONVERGENCE-001` | book-suli-mayers-numerical-analysis, book-andersen-piterbarg-interest-rate-modeling | src/take_two_options/quantitative/numerical_validation.py | tests/test_quantitative_foundations.py | `tested` |
| `FORM-IV-ROOT-001` | book-suli-mayers-numerical-analysis | src/take_two_options/quantitative/implied_volatility.py<br>src/take_two_options/american.py | tests/test_implied_volatility_svi.py | `numerically_validated` |
| `FORM-SVI-RAW-001` | paper-gatheral-jacquier-svi | src/take_two_options/quantitative/svi.py | tests/test_implied_volatility_svi.py | `tested` |
| `FORM-SVI-ARBITRAGE-001` | paper-gatheral-jacquier-svi | src/take_two_options/quantitative/svi.py | tests/test_implied_volatility_svi.py | `tested` |
| `FORM-EWMA-001` | book-tsay-analysis-financial-time-series | src/take_two_options/quantitative/calibration.py | tests/test_quantitative_calibration.py | `tested` |
| `FORM-GARCH-001` | book-tsay-analysis-financial-time-series | src/take_two_options/quantitative/calibration.py | tests/test_quantitative_calibration.py | `tested` |
| `FORM-WILSON-001` | paper-wilson-binomial-interval | src/take_two_options/research_statistics.py<br>src/take_two_options/simulation/uncertainty.py | tests/test_simulation_uncertainty.py | `tested` |
| `FORM-MC-SE-001` | book-glasserman-monte-carlo | src/take_two_options/intelligence/valuation.py<br>src/take_two_options/simulation/uncertainty.py | tests/test_intelligence_v11.py<br>tests/test_simulation_uncertainty.py | `tested` |
| `FORM-MC-CI-001` | book-glasserman-monte-carlo | src/take_two_options/intelligence/valuation.py | tests/test_intelligence_v11.py | `tested` |
| `FORM-BOOTSTRAP-001` | book-wasserman-all-statistics | src/take_two_options/research_statistics.py | tests/test_research_statistics.py | `tested` |
| `FORM-CONTROL-VARIATE-001` | book-glasserman-monte-carlo | src/take_two_options/simulation/uncertainty.py | tests/test_simulation_uncertainty.py | `tested` |
| `FORM-ANTITHETIC-001` | book-glasserman-monte-carlo | src/take_two_options/simulation/uncertainty.py | tests/test_simulation_uncertainty.py | `tested` |
| `FORM-BLOCK-BOOTSTRAP-001` | paper-kunsch-block-bootstrap | src/take_two_options/simulation/uncertainty.py | tests/test_simulation_uncertainty.py | `tested` |
| `FORM-PREDICTIVE-MIXTURE-001` | book-mcelreath-statistical-rethinking | src/take_two_options/quantitative/model_uncertainty.py<br>src/take_two_options/intelligence/valuation.py | tests/test_model_uncertainty.py<br>tests/test_intelligence_v11.py | `tested` |
| `FORM-PROBABILITY-CALIBRATION-001` | paper-brier-probability-forecast-verification, book-mcelreath-statistical-rethinking | src/take_two_options/quantitative/probability_calibration.py<br>src/take_two_options/intelligence/backtesting.py | tests/test_model_uncertainty.py | `tested` |
| `FORM-SCENARIO-MIXTURE-001` | book-blitzstein-hwang-introduction-probability | src/take_two_options/intelligence/event_scenarios.py | tests/test_sequential_event_decision.py | `tested` |
| `FORM-BELIEF-SWITCH-001` | book-blitzstein-hwang-introduction-probability | src/take_two_options/intelligence/event_scenarios.py | tests/test_sequential_event_decision.py | `tested` |
| `FORM-PARETO-DOMINANCE-001` | book-boyd-vandenberghe-convex-optimization | src/take_two_options/optimization/allocation_pareto.py | tests/test_allocation_pareto.py | `tested` |
| `FORM-ROBUST-ALLOCATION-OBJECTIVE-001` | book-boyd-vandenberghe-convex-optimization | src/take_two_options/optimization/allocation_pareto.py<br>src/take_two_options/intelligence/optimizer.py | tests/test_allocation_pareto.py | `tested` |
| `FORM-PBO-001` | paper-bailey-borwein-lopez-zhu-pbo | src/take_two_options/validation/pbo.py | tests/test_validation_protocol_v10.py | `tested` |
| `FORM-PLACEBO-001` | book-wasserman-all-statistics | src/take_two_options/validation/placebo.py | tests/test_validation_protocol_v10.py | `tested` |
| `FORM-DSR-001` | paper-bailey-lopez-deflated-sharpe | src/take_two_options/research_statistics.py | tests/test_research_statistics.py | `tested` |
