# Data usage rights — pre-OPRA research

Reviewed on 2026-08-08. This is an engineering control, not legal advice. Account-specific
agreements can be stricter than public terms and must be confirmed by the subscriber.

| Provider / data | Local private research | Retention | Derived internal analysis | Raw redistribution | Public aggregates | Raw GitHub |
|---|---:|---:|---:|---:|---:|---:|
| Market Data historical option EOD | conditional | conditional | conditional | forbidden | conditional | forbidden |
| Alpaca IEX equity data | conditional | conditional | conditional | forbidden | conditional | forbidden |
| U.S. Treasury par yields | allowed | allowed | allowed | conditional | allowed | conditional |
| ECB EUR/USD reference rates | allowed | allowed | allowed | allowed with attribution | allowed | allowed with attribution |
| SEC EDGAR filings/facts | allowed | allowed | allowed | conditional | allowed | conditional |

## Enforced interpretation

- Market Data self-service plans are personal-use licences. Raw records, bulk exports, API
  mirrors, and reconstructible datasets are never committed. The terms also require deletion of
  downloaded subscription data when the subscription ends, subject to the applicable agreement.
- Market Data's public-use terms allow qualifying educational work to show limited excerpts and
  non-reconstructible aggregates with attribution. This repository publishes only aggregate
  counts, diagnostics, hashes, and analytical results; no licensed row is exposed.
- Alpaca's customer agreement prohibits reproducing, distributing, selling, or commercially
  exploiting market data without written consent. Its raw extracts therefore remain local.
- ECB information may be reused with attribution and disclosure of modifications. Treasury and
  SEC public data are used with source attribution and their access/disclaimer policies intact.
- SEC automation declares a user agent and stays below the official ten-request-per-second
  ceiling. Third-party exhibits are not presumed reusable.

## Human confirmations still required

1. Confirm the Market Data subscriber classification, current subscription, applicable exchange
   agreements, and deletion obligations.
2. Confirm the Alpaca account's subscriber/display agreements and whether public derived
   aggregates require consent.
3. Obtain written commercial/redistribution rights before exposing any raw or reconstructible
   licensed data to another person, service, API, file, dashboard, or repository.

## Official sources

- [Market Data terms](https://www.marketdata.app/terms/)
- [Market Data redistribution policy](https://www.marketdata.app/docs/account/data-policies/data-redistribution/)
- [Market Data historical public-use terms](https://www.marketdata.app/terms/public-use/)
- [Alpaca customer agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf)
- [U.S. Treasury interest-rate files](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files)
- [ECB disclaimer and copyright](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html)
- [SEC developer resources](https://www.sec.gov/about/developer-resources)
- [SEC EDGAR access policy](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
