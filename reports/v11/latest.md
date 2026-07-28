# V11 — Probabilistic Strategy Intelligence & Execution Monitor

- Posture : `watchlist`
- Base V10.1 : `v10.1-9f966d01f3e8f085bbb5`
- Données : `v11-data-18013ce5ae90fe11df31`
- Exécution : `forbidden` ; `transmit=false` ; `what_if=true` ; validation humaine

## Données et connecteurs

- Séries requises manquantes : US.market_calendar
- `v10_normalized_seed` : `ready` ; 136 observations
- `sec_edgar` : `not_configured` ; 0 observations
- `fred` : `not_configured` ; 0 observations
- `take_two_rss` : `not_configured` ; 0 observations
- `google_trends_alpha` : `not_configured` ; 0 observations
- `market_calendar` : `not_configured` ; 0 observations
- `ibkr_opra_read_only` : `not_configured` ; 0 observations

## Distribution bayésienne

| Scénario | Probabilité |
| --- | ---: |
| delay_or_guidance_down | 20.00% |
| gta_success | 35.00% |
| market_base | 35.00% |
| rupture | 10.00% |

Chaque mise à jour conserve le prior, la vraisemblance, le poids effectif, le posterior, la famille et les contradictions. Les faits dupliqués ne sont comptés qu'une fois.

## Covariance dynamique

- Local vol : `partial` (22 nœuds, 0 fallbacks)
- Statut : `partial`
- Facteurs : TTWO_return
- Shrinkage : 0.25
- Valeur propre minimale : 0.000453403
- Limite : Comparable-event covariance was not available.
- Limite : Current-regime subset was not available.

## Comparaison multi-modèles

| Candidat | Modèle | Régime | P(profit) | P(perte totale) | P(x2) | P(x3) | P(x5) | P&L moyen USD | CVaR 95 USD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| cand-75984ebc6c766510 | black_scholes_gbm | neutral | 46.3% | 0.0% | 15.8% | 0.0% | 0.0% | 6.37 | 698.60 |
| cand-75984ebc6c766510 | local_volatility | neutral | 42.2% | 0.0% | 13.7% | 0.0% | 0.0% | -64.86 | 701.73 |
| cand-75984ebc6c766510 | heston | neutral | 53.8% | 0.0% | 9.3% | 0.0% | 0.0% | 48.72 | 684.54 |
| cand-75984ebc6c766510 | heston_jump | neutral | 53.9% | 0.0% | 11.6% | 0.0% | 0.0% | 65.20 | 687.54 |
| cand-75984ebc6c766510 | black_scholes_gbm | thesis | 52.0% | 0.0% | 17.2% | 0.0% | 0.0% | 74.37 | 700.00 |
| cand-75984ebc6c766510 | local_volatility | thesis | 56.3% | 0.0% | 18.5% | 0.0% | 0.0% | 121.88 | 697.75 |
| cand-75984ebc6c766510 | heston | thesis | 59.6% | 0.0% | 14.2% | 0.0% | 0.0% | 153.34 | 680.49 |
| cand-75984ebc6c766510 | heston_jump | thesis | 58.0% | 0.0% | 14.6% | 0.0% | 0.0% | 141.80 | 688.29 |
| cand-75984ebc6c766510 | black_scholes_gbm | adverse | 32.9% | 0.0% | 6.8% | 0.0% | 0.0% | -211.31 | 702.02 |
| cand-75984ebc6c766510 | local_volatility | adverse | 28.5% | 0.0% | 4.6% | 0.0% | 0.0% | -282.43 | 710.34 |
| cand-75984ebc6c766510 | heston | adverse | 32.7% | 0.0% | 4.4% | 0.0% | 0.0% | -212.73 | 690.15 |
| cand-75984ebc6c766510 | heston_jump | adverse | 38.2% | 0.3% | 6.3% | 0.0% | 0.0% | -145.24 | 759.87 |
| cand-75984ebc6c766510 | black_scholes_gbm | rupture | 39.1% | 0.0% | 11.4% | 0.0% | 0.0% | -102.61 | 699.16 |
| cand-75984ebc6c766510 | local_volatility | rupture | 36.2% | 0.0% | 5.1% | 0.0% | 0.0% | -186.44 | 699.89 |
| cand-75984ebc6c766510 | heston | rupture | 37.6% | 0.0% | 6.7% | 0.0% | 0.0% | -141.03 | 694.03 |
| cand-75984ebc6c766510 | heston_jump | rupture | 38.7% | 0.7% | 7.3% | 0.0% | 0.0% | -138.63 | 781.77 |
| cand-5159edae09c7d168 | black_scholes_gbm | neutral | 86.5% | 0.0% | 34.1% | 3.4% | 0.0% | 534.93 | 525.93 |
| cand-5159edae09c7d168 | local_volatility | neutral | 69.9% | 0.0% | 15.3% | 1.5% | 0.0% | 222.48 | 552.14 |
| cand-5159edae09c7d168 | heston | neutral | 81.9% | 0.0% | 27.9% | 1.6% | 0.0% | 444.82 | 530.00 |
| cand-5159edae09c7d168 | heston_jump | neutral | 83.6% | 0.0% | 29.4% | 2.0% | 0.0% | 470.21 | 525.75 |
| cand-5159edae09c7d168 | black_scholes_gbm | thesis | 88.7% | 0.0% | 38.7% | 4.7% | 0.0% | 595.07 | 525.52 |
| cand-5159edae09c7d168 | local_volatility | thesis | 79.6% | 0.0% | 19.0% | 1.8% | 0.0% | 339.58 | 541.15 |
| cand-5159edae09c7d168 | heston | thesis | 89.2% | 0.0% | 34.2% | 3.1% | 0.0% | 556.97 | 514.37 |
| cand-5159edae09c7d168 | heston_jump | thesis | 89.6% | 0.1% | 31.7% | 3.9% | 0.3% | 564.61 | 514.80 |
| cand-5159edae09c7d168 | black_scholes_gbm | adverse | 93.3% | 0.0% | 47.5% | 6.3% | 0.0% | 711.10 | 507.26 |
| cand-5159edae09c7d168 | local_volatility | adverse | 84.6% | 0.0% | 29.3% | 2.9% | 0.0% | 486.46 | 530.70 |
| cand-5159edae09c7d168 | heston | adverse | 87.4% | 0.0% | 32.0% | 2.9% | 0.0% | 528.35 | 528.93 |
| cand-5159edae09c7d168 | heston_jump | adverse | 87.4% | 0.3% | 35.5% | 2.5% | 0.0% | 554.16 | 555.72 |
| cand-5159edae09c7d168 | black_scholes_gbm | rupture | 99.6% | 0.0% | 79.3% | 15.2% | 0.0% | 1042.51 | 0.00 |
| cand-5159edae09c7d168 | local_volatility | rupture | 97.0% | 0.0% | 60.9% | 8.8% | 0.0% | 854.02 | 248.91 |
| cand-5159edae09c7d168 | heston | rupture | 99.0% | 0.0% | 61.0% | 5.4% | 0.0% | 860.53 | 0.00 |
| cand-5159edae09c7d168 | heston_jump | rupture | 98.1% | 0.4% | 61.8% | 6.4% | 0.9% | 914.66 | 78.48 |
| cand-4dfb14afde235e50 | black_scholes_gbm | neutral | 94.6% | 0.0% | 50.4% | 6.1% | 0.0% | 850.28 | 578.68 |
| cand-4dfb14afde235e50 | local_volatility | neutral | 82.0% | 0.0% | 19.2% | 1.5% | 0.0% | 411.16 | 618.57 |
| cand-4dfb14afde235e50 | heston | neutral | 95.3% | 0.0% | 42.8% | 3.0% | 0.0% | 780.86 | 502.40 |
| cand-4dfb14afde235e50 | heston_jump | neutral | 95.7% | 0.0% | 48.5% | 4.8% | 0.0% | 831.24 | 447.08 |
| cand-4dfb14afde235e50 | black_scholes_gbm | thesis | 96.4% | 0.0% | 55.1% | 10.6% | 0.0% | 930.87 | 362.16 |
| cand-4dfb14afde235e50 | local_volatility | thesis | 87.6% | 0.0% | 26.0% | 1.5% | 0.0% | 532.76 | 607.27 |
| cand-4dfb14afde235e50 | heston | thesis | 96.1% | 0.0% | 51.2% | 4.4% | 0.0% | 858.26 | 364.06 |
| cand-4dfb14afde235e50 | heston_jump | thesis | 96.7% | 0.0% | 49.6% | 4.1% | 0.2% | 865.40 | 315.18 |
| cand-4dfb14afde235e50 | black_scholes_gbm | adverse | 98.7% | 0.0% | 67.1% | 11.1% | 0.0% | 1058.75 | 0.00 |
| cand-4dfb14afde235e50 | local_volatility | adverse | 92.6% | 0.0% | 46.1% | 6.0% | 0.0% | 782.14 | 575.78 |
| cand-4dfb14afde235e50 | heston | adverse | 97.9% | 0.0% | 52.5% | 4.8% | 0.0% | 890.42 | 123.09 |
| cand-4dfb14afde235e50 | heston_jump | adverse | 96.5% | 0.1% | 52.7% | 5.2% | 0.0% | 884.51 | 344.13 |
| cand-4dfb14afde235e50 | black_scholes_gbm | rupture | 100.0% | 0.0% | 92.4% | 26.7% | 0.0% | 1378.14 | 0.00 |
| cand-4dfb14afde235e50 | local_volatility | rupture | 99.3% | 0.0% | 75.6% | 16.3% | 0.0% | 1170.74 | 0.00 |
| cand-4dfb14afde235e50 | heston | rupture | 99.9% | 0.0% | 80.9% | 11.4% | 0.0% | 1185.50 | 0.00 |
| cand-4dfb14afde235e50 | heston_jump | rupture | 99.2% | 0.2% | 80.3% | 11.5% | 0.6% | 1233.38 | 0.00 |
| cand-119e6d7d30c47119 | black_scholes_gbm | neutral | 44.5% | 0.0% | 13.9% | 0.0% | 0.0% | 0.38 | 621.42 |
| cand-119e6d7d30c47119 | local_volatility | neutral | 39.8% | 0.0% | 11.2% | 0.0% | 0.0% | -79.91 | 623.68 |
| cand-119e6d7d30c47119 | heston | neutral | 49.4% | 0.0% | 9.9% | 0.0% | 0.0% | 11.76 | 611.90 |
| cand-119e6d7d30c47119 | heston_jump | neutral | 51.2% | 0.0% | 11.0% | 0.0% | 0.0% | 35.65 | 608.03 |
| cand-119e6d7d30c47119 | black_scholes_gbm | thesis | 50.5% | 0.0% | 15.2% | 0.0% | 0.0% | 60.89 | 628.54 |
| cand-119e6d7d30c47119 | local_volatility | thesis | 53.0% | 0.0% | 15.2% | 0.0% | 0.0% | 83.01 | 621.37 |
| cand-119e6d7d30c47119 | heston | thesis | 57.5% | 0.0% | 13.3% | 0.0% | 0.0% | 122.05 | 604.06 |
| cand-119e6d7d30c47119 | heston_jump | thesis | 56.7% | 0.0% | 15.4% | 0.0% | 0.0% | 121.22 | 610.99 |
| cand-119e6d7d30c47119 | black_scholes_gbm | adverse | 32.0% | 0.0% | 6.9% | 0.0% | 0.0% | -188.30 | 624.12 |
| cand-119e6d7d30c47119 | local_volatility | adverse | 26.9% | 0.0% | 4.4% | 0.0% | 0.0% | -257.85 | 633.49 |
| cand-119e6d7d30c47119 | heston | adverse | 32.1% | 0.0% | 4.5% | 0.0% | 0.0% | -190.02 | 616.03 |
| cand-119e6d7d30c47119 | heston_jump | adverse | 38.8% | 0.4% | 6.9% | 0.0% | 0.0% | -118.32 | 678.62 |
| cand-119e6d7d30c47119 | black_scholes_gbm | rupture | 40.0% | 0.0% | 10.1% | 0.0% | 0.0% | -70.37 | 623.76 |
| cand-119e6d7d30c47119 | local_volatility | rupture | 36.6% | 0.0% | 6.6% | 0.0% | 0.0% | -152.20 | 628.87 |
| cand-119e6d7d30c47119 | heston | rupture | 41.3% | 0.0% | 7.0% | 0.0% | 0.0% | -76.89 | 618.35 |
| cand-119e6d7d30c47119 | heston_jump | rupture | 41.1% | 0.9% | 8.4% | 0.0% | 0.0% | -82.20 | 699.85 |
| cand-a31726b9f88bb946 | black_scholes_gbm | neutral | 77.3% | 0.0% | 26.0% | 1.8% | 0.0% | 647.47 | 888.07 |
| cand-a31726b9f88bb946 | local_volatility | neutral | 58.9% | 0.0% | 19.8% | 2.1% | 0.0% | 281.40 | 924.56 |
| cand-a31726b9f88bb946 | heston | neutral | 69.3% | 0.0% | 21.5% | 0.5% | 0.0% | 479.81 | 892.79 |
| cand-a31726b9f88bb946 | heston_jump | neutral | 72.8% | 0.0% | 24.0% | 1.0% | 0.0% | 546.25 | 886.31 |
| cand-a31726b9f88bb946 | black_scholes_gbm | thesis | 79.8% | 0.0% | 34.3% | 2.5% | 0.0% | 786.82 | 895.55 |
| cand-a31726b9f88bb946 | local_volatility | thesis | 69.7% | 0.0% | 21.6% | 2.1% | 0.0% | 471.39 | 910.59 |
| cand-a31726b9f88bb946 | heston | thesis | 79.7% | 0.0% | 27.3% | 1.5% | 0.0% | 702.41 | 884.69 |
| cand-a31726b9f88bb946 | heston_jump | thesis | 78.9% | 0.0% | 28.4% | 2.7% | 0.1% | 730.48 | 883.21 |
| cand-a31726b9f88bb946 | black_scholes_gbm | adverse | 84.4% | 0.0% | 34.3% | 2.6% | 0.0% | 877.23 | 882.99 |
| cand-a31726b9f88bb946 | local_volatility | adverse | 74.4% | 0.0% | 22.6% | 1.6% | 0.0% | 556.15 | 894.48 |
| cand-a31726b9f88bb946 | heston | adverse | 74.8% | 0.0% | 27.4% | 1.1% | 0.0% | 608.08 | 897.28 |
| cand-a31726b9f88bb946 | heston_jump | adverse | 76.2% | 0.5% | 28.3% | 1.2% | 0.0% | 651.96 | 957.18 |
| cand-a31726b9f88bb946 | black_scholes_gbm | rupture | 97.6% | 0.0% | 62.4% | 8.9% | 0.0% | 1472.30 | 248.00 |
| cand-a31726b9f88bb946 | local_volatility | rupture | 93.0% | 0.0% | 50.6% | 4.7% | 0.0% | 1222.29 | 857.49 |
| cand-a31726b9f88bb946 | heston | rupture | 95.1% | 0.0% | 50.4% | 3.8% | 0.0% | 1233.32 | 822.08 |
| cand-a31726b9f88bb946 | heston_jump | rupture | 93.2% | 0.5% | 48.4% | 4.8% | 0.9% | 1273.83 | 923.30 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | neutral | 46.8% | 0.0% | 0.0% | 0.0% | 0.0% | -53.59 | 735.80 |
| cand-b9aa8a0e0964eb88 | local_volatility | neutral | 44.6% | 0.0% | 0.0% | 0.0% | 0.0% | -91.38 | 735.91 |
| cand-b9aa8a0e0964eb88 | heston | neutral | 54.3% | 0.0% | 0.0% | 0.0% | 0.0% | 17.76 | 730.03 |
| cand-b9aa8a0e0964eb88 | heston_jump | neutral | 53.8% | 0.0% | 0.0% | 0.0% | 0.0% | 18.66 | 729.28 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | thesis | 49.8% | 0.0% | 0.0% | 0.0% | 0.0% | -9.52 | 731.13 |
| cand-b9aa8a0e0964eb88 | local_volatility | thesis | 58.2% | 0.0% | 0.0% | 0.0% | 0.0% | 24.01 | 728.97 |
| cand-b9aa8a0e0964eb88 | heston | thesis | 58.8% | 0.0% | 0.0% | 0.0% | 0.0% | 84.38 | 729.31 |
| cand-b9aa8a0e0964eb88 | heston_jump | thesis | 55.6% | 0.0% | 0.0% | 0.0% | 0.0% | 56.68 | 730.16 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | adverse | 25.7% | 0.0% | 0.0% | 0.0% | 0.0% | -284.59 | 743.62 |
| cand-b9aa8a0e0964eb88 | local_volatility | adverse | 26.3% | 0.0% | 0.0% | 0.0% | 0.0% | -307.13 | 746.43 |
| cand-b9aa8a0e0964eb88 | heston | adverse | 25.4% | 0.0% | 0.0% | 0.0% | 0.0% | -276.84 | 742.88 |
| cand-b9aa8a0e0964eb88 | heston_jump | adverse | 30.0% | 0.0% | 0.0% | 0.0% | 0.0% | -243.30 | 786.23 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | rupture | 27.4% | 0.0% | 0.0% | 0.0% | 0.0% | -257.60 | 743.01 |
| cand-b9aa8a0e0964eb88 | local_volatility | rupture | 24.8% | 0.0% | 0.0% | 0.0% | 0.0% | -297.47 | 746.68 |
| cand-b9aa8a0e0964eb88 | heston | rupture | 21.4% | 0.0% | 0.0% | 0.0% | 0.0% | -317.87 | 740.28 |
| cand-b9aa8a0e0964eb88 | heston_jump | rupture | 22.5% | 0.0% | 0.0% | 0.0% | 0.0% | -325.86 | 791.88 |

## Allocations sous contraintes

### prudent — rang 1

- Allocation : cash / aucune stratégie
- Réserve : 1000.00 EUR
- P&L espéré : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Dispersion modèles : 0.00 EUR
- Objectif normalisé : 0.000000

### prudent — rang 2

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Dispersion modèles : 845.63 EUR
- Objectif normalisé : -0.837789

### prudent — rang 3

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Dispersion modèles : 717.12 EUR
- Objectif normalisé : -0.928774

### prudent — rang 4

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Dispersion modèles : 332.23 EUR
- Objectif normalisé : -1.258892

### prudent — rang 5

- Allocation : 1× cand-b9aa8a0e0964eb88
- Réserve : 124.27 EUR
- P&L espéré : -71.23 EUR
- CVaR 95 : 692.51 EUR
- Dispersion modèles : 358.76 EUR
- Objectif normalisé : -1.268514

### balanced — rang 1

- Allocation : cash / aucune stratégie
- Réserve : 1000.00 EUR
- P&L espéré : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Dispersion modèles : 0.00 EUR
- Objectif normalisé : 0.000000

### balanced — rang 2

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Dispersion modèles : 845.63 EUR
- Objectif normalisé : -0.231483

### balanced — rang 3

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Dispersion modèles : 717.12 EUR
- Objectif normalisé : -0.391202

### balanced — rang 4

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Dispersion modèles : 332.23 EUR
- Objectif normalisé : -0.777672

### balanced — rang 5

- Allocation : 1× cand-b9aa8a0e0964eb88
- Réserve : 124.27 EUR
- P&L espéré : -71.23 EUR
- CVaR 95 : 692.51 EUR
- Dispersion modèles : 358.76 EUR
- Objectif normalisé : -0.819139

### aggressive — rang 1

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Dispersion modèles : 845.63 EUR
- Objectif normalisé : 0.279327

### aggressive — rang 2

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Dispersion modèles : 717.12 EUR
- Objectif normalisé : 0.065969

### aggressive — rang 3

- Allocation : cash / aucune stratégie
- Réserve : 1000.00 EUR
- P&L espéré : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Dispersion modèles : 0.00 EUR
- Objectif normalisé : 0.000000

### aggressive — rang 4

- Allocation : 1× cand-a31726b9f88bb946
- Réserve : 2.45 EUR
- P&L espéré : 587.01 EUR
- CVaR 95 : 837.06 EUR
- Dispersion modèles : 1041.45 EUR
- Objectif normalisé : -0.137070

### aggressive — rang 5

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Dispersion modèles : 332.23 EUR
- Objectif normalisé : -0.361414

## Validation walk-forward / stress / paper

- `cand-75984ebc6c766510` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`failed` ; paper=`not_run` ; promotion=false
- `cand-5159edae09c7d168` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`failed` ; paper=`not_run` ; promotion=false
- `cand-4dfb14afde235e50` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`passed` ; paper=`not_run` ; promotion=false
- `cand-119e6d7d30c47119` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`failed` ; paper=`not_run` ; promotion=false
- `cand-a31726b9f88bb946` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`failed` ; paper=`not_run` ; promotion=false
- `cand-b9aa8a0e0964eb88` : walk-forward=`contaminated` ; holdout=`contaminated` ; stress=`failed` ; paper=`not_run` ; promotion=false

## Plans de sortie

### cand-75984ebc6c766510

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

### cand-5159edae09c7d168

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

### cand-4dfb14afde235e50

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

### cand-119e6d7d30c47119

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

### cand-a31726b9f88bb946

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

### cand-b9aa8a0e0964eb88

- Profit : +150%
- Prise partielle : +80%
- Stop opérationnel : -70%
- Sortie temps : 60 jours avant échéance
- IV crush : 35%
- Trailing : 30%

## Tickets IBKR

- `cand-75984ebc6c766510` : limite indicative 8.8010 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5
- `cand-5159edae09c7d168` : limite indicative 6.8005 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5
- `cand-4dfb14afde235e50` : limite indicative 3.8505 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5
- `cand-119e6d7d30c47119` : limite indicative 7.8010 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5
- `cand-a31726b9f88bb946` : limite indicative 11.4005 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5
- `cand-b9aa8a0e0964eb88` : limite indicative 10.0010 USD/action ; `transmit=false` ; `what_if=true` ; blockers=5

## Limites et validations

- Surface quality is synthetic; live OPRA calibration is required.
- Finite differences do not enforce calendar/butterfly arbitrage globally; the extracted surface remains a research input.
- Comparable-event covariance was not available.
- Current-regime subset was not available.
- A single TTWO return series cannot estimate the requested cross-factor covariance; supply an aligned factor-history file for Nasdaq, gaming peers, rates, FX, volume, IV, OI, sentiment, news intensity, and catalyst proximity.
- Leg quotes do not prove a simultaneous combo fill.
- IBKR notes that account market-data entitlements are required and some smart combo orders do not support what-if commission/margin checks.
- Google Trends API access remains limited alpha and must not be replaced by an undocumented scraper in a production workflow.

### Validations requises

- Freeze a live IBKR/OPRA chain with contract conIds, deliverables, combo quotes, commissions, and account-specific margin.
- Calibrate the local-volatility surface and Heston/jump parameters without look-ahead.
- Run nested walk-forward, event-window backtests, crisis stresses, and a new untouched holdout.
- Complete paper trading with human-reviewed entries, partial exits, rolls, and invalidations.
- Obtain explicit user approval before any future change to the forbidden execution boundary.
