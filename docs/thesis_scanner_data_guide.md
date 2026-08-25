# V10.1 thesis scanner data guide

## Accepted chain inputs

`--current-chain` accepts three read-only formats:

1. `thesis_chain_v1`, the strict native V10.1 fixture/adapter contract;
2. the active `MarketSnapshot` JSON cache;
3. an `AlpacaOptionChainExport`.

Native input should provide spot and quote timestamps, expiration, call/put,
strike, bid, ask, volume, open interest, IV when available, multiplier,
multiplier confirmation, standard-contract status, price quality, and source ID.

## Alpaca boundary

The Alpaca export does not contain underlying spot, open interest, or contract
deliverable. V10.1 therefore:

- requires `--spot` or finds the newest look-ahead-safe close from the sibling
  calibration dataset;
- marks OI/volume unavailable instead of substituting zero;
- marks multiplier 100 as assumed;
- marks deliverable status unknown;
- identifies `indicative` as non-executable.

Those warnings make candidates watchlist items. A broker-confirmed chain is
required before any human trade decision.

## MarketSnapshot boundary

MarketData.app EOD bid/ask is not a simultaneous combo market. Contract
multiplier is carried through but remains assumed unless a broker/OCC contract
detail confirms it. Missing IV is inverted from the American midpoint when
mathematically possible; failure to recover IV blocks candidates using that leg.

## Freshness and invalid data

The scanner compares each quote timestamp with scan time and the chain
timestamp. It rejects missing/future/stale timestamps, missing or non-positive
bid/ask, crossed quotes, spreads over policy, expirations before
`catalyst + buffer`, known OI/volume failures, non-standard multipliers,
non-standard contracts, and strikes outside configured moneyness.

Policy inputs are explicitly dated:

- `eur_usd_rate`, date, source, and maximum age;
- risk-free rate, date, and source;
- dividend yield and source;
- commission and slippage per contract side.

They are configuration inputs, not silently refreshed market facts.

## Données nécessaires pour un calcul fiable

Une chaîne fournie manuellement doit contenir, sans substitution silencieuse :

- ticker, spot du sous-jacent et timestamp du spot ;
- symbole OCC ;
- expiration ;
- strike ;
- bid et ask ;
- tailles bid/ask lorsqu’elles sont disponibles ;
- volume ;
- open interest ;
- volatilité implicite ;
- multiplicateur et deliverable contractuel ;
- source et qualité de la donnée ;
- taux EUR/USD, date et source ;
- taux sans risque, date et source ;
- commissions ;
- slippage ;
- budget ;
- perte maximale autorisée ;
- date du catalyseur ;
- objectifs de cours ;
- probabilités facultatives, uniquement lorsqu’elles viennent de l’utilisateur.

La saisie manuelle d’une chaîne complète est possible avec le contrat
`thesis_chain_v1`, mais elle est déconseillée : elle prend du temps et augmente
le risque d’erreur sur les symboles OCC, timestamps, strikes, multiplicateurs,
deliverables et cotations. Toute valeur manquante doit produire un
avertissement ou un blocage explicite.

Les cotations synthétiques, retardées, indicatives, EOD ou reconstruites jambe
par jambe sont affichées avec l’avertissement :

> Estimation de recherche — ce prix n’est pas une cotation combo exécutable.

## Synthetic example

```bash
ttwo-options thesis-scan \
  --ticker TTWO --direction bullish --budget-eur 1000 \
  --catalyst-date 2026-11-19 --expiration-buffer-days 45 \
  --target-prices 220,250,280,300,330,360 \
  --scenario-probabilities 0.10,0.15,0.20,0.20,0.20,0.15 \
  --max-loss-eur 1000 --top 3 \
  --current-chain fixtures/thesis_scanner/ttwo_synthetic_chain.json \
  --json-out reports/examples/v10_thesis_scan.json \
  --markdown-out reports/examples/v10_thesis_scan.md \
  --html-out reports/examples/v10_thesis_scan.html
```

Remove `--scenario-probabilities` to verify the probability-free contract:
`expected_pnl_usd` and `probability_success` remain null.

The fixture and outputs are synthetic documentation artifacts, not market data
and not recommendations.
