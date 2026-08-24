# M0 official-source validity audit — 2026

Audit date: 2026-08-24
Scope: conventions and API/data boundaries needed by M0
Outcome: no external source changes the read-only or pre-OPRA classification

## Findings

| Topic | Primary-source check | M0 consequence |
| --- | --- | --- |
| QuantLib version | QuantLib 1.43 was released on 2026-07-14 and the project pins `>=1.43,<1.44`. | Dependency range is current as of the audit date. |
| American FD time | Official QuantLib sources represent settlement/exercise with `Date`; the FD vanilla engine accepts a cash-dividend schedule and finite grids. | Preserve exact input datetimes but label American intraday precision approximate; apply the near-expiry insufficiency status. |
| Contract semantics | OCC product specifications describe standard equity-option contracts and adjusted-contract exceptions; the ODD remains the controlling risk disclosure. | Read multiplier, deliverable, exercise style and adjusted status from contract data; never assume 100 when metadata exists. |
| Provider Greeks | IBKR exposes option computations across distinct market-data ticks and documents model calculations plus contract/combo identifiers. | Preserve provider stream and convention; recompute normalized internal Greeks; never call a per-leg sum an observed combo quote. |
| Broker margin | IBKR documents order what-if fields for estimated commission, margin and equity effects. | Pre-OPRA analytical margin is not broker margin. Unknown values remain null and real values stay `PENDING_BROKER`. |
| Treasury rates | Treasury states that CMT rates are daily par yields quoted on a bond-equivalent basis. | Preserve `par_yield`; do not relabel interpolation as a zero curve. A zero curve requires explicit bootstrap metadata. |
| Advanced Greek language | OIC educational material describes Vanna as Delta sensitivity to IV and Vomma as Vega sensitivity to IV. | M0 publishes explicit mathematical derivatives and units instead of relying on vendor names alone. |

## Sources

- [QuantLib 1.43 release](https://github.com/lballabio/QuantLib/releases)
- [QuantLib FD Black–Scholes vanilla engine header](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/vanilla/fdblackscholesvanillaengine.hpp)
- [QuantLib FD Black–Scholes vanilla engine implementation](https://github.com/lballabio/QuantLib/blob/master/ql/pricingengines/vanilla/fdblackscholesvanillaengine.cpp)
- [QuantLib American-option tests](https://github.com/lballabio/QuantLib/blob/master/test-suite/americanoption.cpp)
- [QuantLib Python package 1.43](https://pypi.org/project/QuantLib/)
- [OCC equity options product specifications](https://www.theocc.com/clearance-and-settlement/clearing/equity-options-product-specifications)
- [OCC Options Disclosure Document](https://www.theocc.com/company-information/documents-and-archives/options-disclosure-document)
- [IBKR option computations](https://interactivebrokers.github.io/tws-api/option_computations.html)
- [IBKR spread contracts](https://interactivebrokers.github.io/tws-api/spread_contracts.html)
- [IBKR margin considerations](https://interactivebrokers.github.io/tws-api/margin.html)
- [IBKR order/what-if fields](https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html)
- [IBKR current API documentation landing page](https://ibkrcampus.com/campus/ibkr-api-page/webapi-doc/)
- [U.S. Treasury interest-rate statistics FAQ](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rates-frequently-asked-questions)
- [OIC advanced-Greek FAQ](https://www.optionseducation.org/news/may-office-hours-faqs)

## Limits and uncertainty

- Official documentation establishes interface and convention facts, not numerical correctness of
  this repository; tests and analytic benchmarks cover the latter only for declared fixtures.
- OCC standard specifications do not eliminate adjusted contracts; future live ingestion must
  still inspect each contract.
- IBKR legacy TWS pages are retained because they directly document the fields used by the future
  adapter. Current IBKR Campus documentation must be rechecked before connection work.
- Treasury par-yield interpolation is an explicit approximation. M0 does not claim a bootstrapped
  arbitrage-free discount curve.
- OIC terminology is educational. The formulas and normalizations in the M0 convention document
  are authoritative for this codebase.

## Classification

`VALIDITY_STATUS = CURRENT_FOR_M0_PRE_OPRA_AS_OF_2026-08-24`

Re-audit is required before Phase M if QuantLib, OCC contract rules, broker APIs, settlement rules,
margin interfaces or market-data terms change.
