# V11.1 — Offline Reliability & Probabilistic Strategy Intelligence

- Posture : `watchlist`
- Readiness du résultat : `fixture_only`
- Base V10.1 : `v10.1-9f966d01f3e8f085bbb5`
- Run : `run-48e6a37ef7599b6042ff`
- Cutoff : `2026-07-24T20:00:00+00:00`
- Configuration : `5e7ea3160d65c43bae402437463c74da3f8ce343fbd01b3821c6bf161c946f4d`
- Données : `8f27b82909bea87f44f716d62ed23dc926f903f554b97b909dc4adb01a8e3be8`
- Exécution : `forbidden` ; `transmit=false` ; `what_if=true` ; confirmation humaine

## 1. État des données

- Séries requises manquantes : US.market_calendar
- `v10_normalized_seed` : `ready` ; 136 observations
- `sec_edgar` : `not_configured` ; 0 observations
- `fred` : `not_configured` ; 0 observations
- `take_two_rss` : `not_configured` ; 0 observations
- `google_trends_alpha` : `not_configured` ; 0 observations
- `market_calendar` : `not_configured` ; 0 observations
- `ibkr_opra_read_only` : `not_configured` ; 0 observations

## 2. Statut de calibration et de backtest

- Calibration historique : `BLOCKED_MISSING_CALIBRATION_DATA`
- Walk-forward : `BLOCKED_MISSING_CALIBRATION_DATA`
- Aucun dataset manquant n'est remplacé par une fixture.

## 3. Probabilités initiales, postérieures et sensibilité

| Scénario | Posterior | Minimum sensibilité | Maximum sensibilité |
| --- | ---: | ---: | ---: |
| delay_or_guidance_down | 20.00% | 20.00% | 20.00% |
| gta_success | 35.00% | 35.00% | 35.00% |
| market_base | 35.00% | 35.00% | 35.00% |
| rupture | 10.00% | 10.00% | 10.00% |

- Confiance : `low`
- Classement stable sous sensibilité : `True`

## 4. Provenance des événements

| Événement | Type | Famille | Règle | Revue | Sources |
| --- | --- | --- | --- | --- | --- |
| — | aucun événement | — | — | — | — |

## 5. Contradictions

- Aucune contradiction normalisée dans ce run.

## 6–11. Comparaison des modèles et distribution du P&L

| Candidat | Modèle | Régime | Validité | Convergence | IC 95 % P&L | P(profit) | P(perte totale) | x2/x3/x5 | VaR/CVaR |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |
| cand-75984ebc6c766510 | black_scholes_gbm | neutral | illustrative | converged | [-35.28, 48.02] | 46.3% | 0.0% | 15.8%/0.0%/0.0% | 679.31/698.60 |
| cand-75984ebc6c766510 | local_volatility | neutral | partial | converged | [-105.52, -24.20] | 42.2% | 0.0% | 13.7%/0.0%/0.0% | 683.64/701.73 |
| cand-75984ebc6c766510 | heston | neutral | illustrative | converged | [11.21, 86.23] | 53.8% | 0.0% | 9.3%/0.0%/0.0% | 666.20/684.54 |
| cand-75984ebc6c766510 | heston_jump | neutral | illustrative | converged | [26.42, 103.97] | 53.9% | 0.0% | 11.6%/0.0%/0.0% | 667.57/687.54 |
| cand-75984ebc6c766510 | black_scholes_gbm | thesis | illustrative | converged | [32.64, 116.09] | 52.0% | 0.0% | 17.2%/0.0%/0.0% | 675.48/700.00 |
| cand-75984ebc6c766510 | local_volatility | thesis | partial | converged | [80.87, 162.90] | 56.3% | 0.0% | 18.5%/0.0%/0.0% | 676.01/697.75 |
| cand-75984ebc6c766510 | heston | thesis | illustrative | converged | [114.27, 192.41] | 59.6% | 0.0% | 14.2%/0.0%/0.0% | 663.22/680.49 |
| cand-75984ebc6c766510 | heston_jump | thesis | illustrative | converged | [102.43, 181.17] | 58.0% | 0.0% | 14.6%/0.0%/0.0% | 665.42/688.29 |
| cand-75984ebc6c766510 | black_scholes_gbm | adverse | illustrative | converged | [-247.88, -174.74] | 32.9% | 0.0% | 6.8%/0.0%/0.0% | 684.45/702.02 |
| cand-75984ebc6c766510 | local_volatility | adverse | partial | converged | [-316.33, -248.53] | 28.5% | 0.0% | 4.6%/0.0%/0.0% | 689.25/710.34 |
| cand-75984ebc6c766510 | heston | adverse | illustrative | converged | [-247.81, -177.66] | 32.7% | 0.0% | 4.4%/0.0%/0.0% | 676.72/690.15 |
| cand-75984ebc6c766510 | heston_jump | adverse | illustrative | converged | [-182.60, -107.88] | 38.2% | 0.3% | 6.3%/0.0%/0.0% | 704.29/759.87 |
| cand-75984ebc6c766510 | black_scholes_gbm | rupture | illustrative | converged | [-142.36, -62.86] | 39.1% | 0.0% | 11.4%/0.0%/0.0% | 683.98/699.16 |
| cand-75984ebc6c766510 | local_volatility | rupture | partial | converged | [-222.00, -150.88] | 36.2% | 0.0% | 5.1%/0.0%/0.0% | 684.30/699.89 |
| cand-75984ebc6c766510 | heston | rupture | illustrative | converged | [-177.70, -104.36] | 37.6% | 0.0% | 6.7%/0.0%/0.0% | 675.48/694.03 |
| cand-75984ebc6c766510 | heston_jump | rupture | illustrative | converged | [-176.69, -100.57] | 38.7% | 0.7% | 7.3%/0.0%/0.0% | 713.72/781.77 |
| cand-5159edae09c7d168 | black_scholes_gbm | neutral | illustrative | converged | [501.13, 568.72] | 86.5% | 0.0% | 34.1%/3.4%/0.0% | 510.65/525.93 |
| cand-5159edae09c7d168 | local_volatility | neutral | partial | converged | [187.87, 257.10] | 69.9% | 0.0% | 15.3%/1.5%/0.0% | 532.97/552.14 |
| cand-5159edae09c7d168 | heston | neutral | illustrative | converged | [411.34, 478.29] | 81.9% | 0.0% | 27.9%/1.6%/0.0% | 508.60/530.00 |
| cand-5159edae09c7d168 | heston_jump | neutral | illustrative | converged | [437.35, 503.06] | 83.6% | 0.0% | 29.4%/2.0%/0.0% | 506.42/525.75 |
| cand-5159edae09c7d168 | black_scholes_gbm | thesis | illustrative | converged | [561.42, 628.71] | 88.7% | 0.0% | 38.7%/4.7%/0.0% | 503.86/525.52 |
| cand-5159edae09c7d168 | local_volatility | thesis | partial | converged | [306.97, 372.19] | 79.6% | 0.0% | 19.0%/1.8%/0.0% | 518.92/541.15 |
| cand-5159edae09c7d168 | heston | thesis | illustrative | converged | [526.00, 587.95] | 89.2% | 0.0% | 34.2%/3.1%/0.0% | 496.14/514.37 |
| cand-5159edae09c7d168 | heston_jump | thesis | illustrative | converged | [531.37, 597.85] | 89.6% | 0.1% | 31.7%/3.9%/0.3% | 490.71/514.80 |
| cand-5159edae09c7d168 | black_scholes_gbm | adverse | illustrative | converged | [679.60, 742.59] | 93.3% | 0.0% | 47.5%/6.3%/0.0% | 486.93/507.26 |
| cand-5159edae09c7d168 | local_volatility | adverse | partial | converged | [452.67, 520.25] | 84.6% | 0.0% | 29.3%/2.9%/0.0% | 512.48/530.70 |
| cand-5159edae09c7d168 | heston | adverse | illustrative | converged | [496.10, 560.60] | 87.4% | 0.0% | 32.0%/2.9%/0.0% | 504.28/528.93 |
| cand-5159edae09c7d168 | heston_jump | adverse | illustrative | converged | [521.15, 587.17] | 87.4% | 0.3% | 35.5%/2.5%/0.0% | 508.52/555.72 |
| cand-5159edae09c7d168 | black_scholes_gbm | rupture | illustrative | converged | [1019.58, 1065.45] | 99.6% | 0.0% | 79.3%/15.2%/0.0% | 0.00/0.00 |
| cand-5159edae09c7d168 | local_volatility | rupture | partial | converged | [825.74, 882.30] | 97.0% | 0.0% | 60.9%/8.8%/0.0% | 0.00/248.91 |
| cand-5159edae09c7d168 | heston | rupture | illustrative | converged | [836.30, 884.76] | 99.0% | 0.0% | 61.0%/5.4%/0.0% | 0.00/0.00 |
| cand-5159edae09c7d168 | heston_jump | rupture | illustrative | converged | [862.40, 966.92] | 98.1% | 0.4% | 61.8%/6.4%/0.9% | 0.00/78.48 |
| cand-4dfb14afde235e50 | black_scholes_gbm | neutral | illustrative | converged | [815.49, 885.08] | 94.6% | 0.0% | 50.4%/6.1%/0.0% | 544.59/578.68 |
| cand-4dfb14afde235e50 | local_volatility | neutral | partial | converged | [375.07, 447.25] | 82.0% | 0.0% | 19.2%/1.5%/0.0% | 593.94/618.57 |
| cand-4dfb14afde235e50 | heston | neutral | illustrative | converged | [749.14, 812.58] | 95.3% | 0.0% | 42.8%/3.0%/0.0% | 0.00/502.40 |
| cand-4dfb14afde235e50 | heston_jump | neutral | illustrative | converged | [799.37, 863.12] | 95.7% | 0.0% | 48.5%/4.8%/0.0% | 0.00/447.08 |
| cand-4dfb14afde235e50 | black_scholes_gbm | thesis | illustrative | converged | [896.72, 965.02] | 96.4% | 0.0% | 55.1%/10.6%/0.0% | 0.00/362.16 |
| cand-4dfb14afde235e50 | local_volatility | thesis | partial | converged | [497.68, 567.83] | 87.6% | 0.0% | 26.0%/1.5%/0.0% | 582.47/607.27 |
| cand-4dfb14afde235e50 | heston | thesis | illustrative | converged | [826.97, 889.55] | 96.1% | 0.0% | 51.2%/4.4%/0.0% | 0.00/364.06 |
| cand-4dfb14afde235e50 | heston_jump | thesis | illustrative | converged | [833.48, 897.32] | 96.7% | 0.0% | 49.6%/4.1%/0.2% | 0.00/315.18 |
| cand-4dfb14afde235e50 | black_scholes_gbm | adverse | illustrative | converged | [1028.62, 1088.89] | 98.7% | 0.0% | 67.1%/11.1%/0.0% | 0.00/0.00 |
| cand-4dfb14afde235e50 | local_volatility | adverse | partial | converged | [746.36, 817.92] | 92.6% | 0.0% | 46.1%/6.0%/0.0% | 553.97/575.78 |
| cand-4dfb14afde235e50 | heston | adverse | illustrative | converged | [860.98, 919.85] | 97.9% | 0.0% | 52.5%/4.8%/0.0% | 0.00/123.09 |
| cand-4dfb14afde235e50 | heston_jump | adverse | illustrative | converged | [852.94, 916.08] | 96.5% | 0.1% | 52.7%/5.2%/0.0% | 0.00/344.13 |
| cand-4dfb14afde235e50 | black_scholes_gbm | rupture | illustrative | converged | [1356.81, 1399.47] | 100.0% | 0.0% | 92.4%/26.7%/0.0% | 0.00/0.00 |
| cand-4dfb14afde235e50 | local_volatility | rupture | partial | converged | [1142.10, 1199.38] | 99.3% | 0.0% | 75.6%/16.3%/0.0% | 0.00/0.00 |
| cand-4dfb14afde235e50 | heston | rupture | illustrative | converged | [1163.10, 1207.89] | 99.9% | 0.0% | 80.9%/11.4%/0.0% | 0.00/0.00 |
| cand-4dfb14afde235e50 | heston_jump | rupture | illustrative | converged | [1167.07, 1299.69] | 99.2% | 0.2% | 80.3%/11.5%/0.6% | 0.00/0.00 |
| cand-119e6d7d30c47119 | black_scholes_gbm | neutral | illustrative | converged | [-38.79, 39.55] | 44.5% | 0.0% | 13.9%/0.0%/0.0% | 603.99/621.42 |
| cand-119e6d7d30c47119 | local_volatility | neutral | partial | converged | [-117.17, -42.66] | 39.8% | 0.0% | 11.2%/0.0%/0.0% | 605.72/623.68 |
| cand-119e6d7d30c47119 | heston | neutral | illustrative | converged | [-22.88, 46.41] | 49.4% | 0.0% | 9.9%/0.0%/0.0% | 596.33/611.90 |
| cand-119e6d7d30c47119 | heston_jump | neutral | illustrative | converged | [-0.18, 71.47] | 51.2% | 0.0% | 11.0%/0.0%/0.0% | 589.51/608.03 |
| cand-119e6d7d30c47119 | black_scholes_gbm | thesis | illustrative | converged | [21.68, 100.09] | 50.5% | 0.0% | 15.2%/0.0%/0.0% | 610.38/628.54 |
| cand-119e6d7d30c47119 | local_volatility | thesis | partial | converged | [44.64, 121.39] | 53.0% | 0.0% | 15.2%/0.0%/0.0% | 597.91/621.37 |
| cand-119e6d7d30c47119 | heston | thesis | illustrative | converged | [85.46, 158.64] | 57.5% | 0.0% | 13.3%/0.0%/0.0% | 591.25/604.06 |
| cand-119e6d7d30c47119 | heston_jump | thesis | illustrative | converged | [83.89, 158.55] | 56.7% | 0.0% | 15.4%/0.0%/0.0% | 595.48/610.99 |
| cand-119e6d7d30c47119 | black_scholes_gbm | adverse | illustrative | converged | [-222.26, -154.33] | 32.0% | 0.0% | 6.9%/0.0%/0.0% | 608.91/624.12 |
| cand-119e6d7d30c47119 | local_volatility | adverse | partial | converged | [-288.96, -226.74] | 26.9% | 0.0% | 4.4%/0.0%/0.0% | 612.38/633.49 |
| cand-119e6d7d30c47119 | heston | adverse | illustrative | converged | [-222.39, -157.66] | 32.1% | 0.0% | 4.5%/0.0%/0.0% | 599.38/616.03 |
| cand-119e6d7d30c47119 | heston_jump | adverse | illustrative | converged | [-153.11, -83.53] | 38.8% | 0.4% | 6.9%/0.0%/0.0% | 629.41/678.62 |
| cand-119e6d7d30c47119 | black_scholes_gbm | rupture | illustrative | converged | [-107.76, -32.98] | 40.0% | 0.0% | 10.1%/0.0%/0.0% | 608.28/623.76 |
| cand-119e6d7d30c47119 | local_volatility | rupture | partial | converged | [-185.92, -118.48] | 36.6% | 0.0% | 6.6%/0.0%/0.0% | 610.60/628.87 |
| cand-119e6d7d30c47119 | heston | rupture | illustrative | converged | [-111.83, -41.96] | 41.3% | 0.0% | 7.0%/0.0%/0.0% | 601.87/618.35 |
| cand-119e6d7d30c47119 | heston_jump | rupture | illustrative | converged | [-118.56, -45.84] | 41.1% | 0.9% | 8.4%/0.0%/0.0% | 635.09/699.85 |
| cand-a31726b9f88bb946 | black_scholes_gbm | neutral | illustrative | converged | [587.57, 707.38] | 77.3% | 0.0% | 26.0%/1.8%/0.0% | 860.00/888.07 |
| cand-a31726b9f88bb946 | local_volatility | neutral | partial | converged | [215.48, 347.33] | 58.9% | 0.0% | 19.8%/2.1%/0.0% | 901.42/924.56 |
| cand-a31726b9f88bb946 | heston | neutral | illustrative | converged | [421.17, 538.45] | 69.3% | 0.0% | 21.5%/0.5%/0.0% | 864.59/892.79 |
| cand-a31726b9f88bb946 | heston_jump | neutral | illustrative | converged | [486.36, 606.13] | 72.8% | 0.0% | 24.0%/1.0%/0.0% | 863.67/886.31 |
| cand-a31726b9f88bb946 | black_scholes_gbm | thesis | illustrative | converged | [724.92, 848.72] | 79.8% | 0.0% | 34.3%/2.5%/0.0% | 866.53/895.55 |
| cand-a31726b9f88bb946 | local_volatility | thesis | partial | converged | [408.62, 534.16] | 69.7% | 0.0% | 21.6%/2.1%/0.0% | 885.49/910.59 |
| cand-a31726b9f88bb946 | heston | thesis | illustrative | converged | [645.46, 759.36] | 79.7% | 0.0% | 27.3%/1.5%/0.0% | 857.91/884.69 |
| cand-a31726b9f88bb946 | heston_jump | thesis | illustrative | converged | [669.12, 791.84] | 78.9% | 0.0% | 28.4%/2.7%/0.1% | 849.29/883.21 |
| cand-a31726b9f88bb946 | black_scholes_gbm | adverse | illustrative | converged | [819.05, 935.40] | 84.4% | 0.0% | 34.3%/2.6%/0.0% | 852.75/882.99 |
| cand-a31726b9f88bb946 | local_volatility | adverse | partial | converged | [496.28, 616.02] | 74.4% | 0.0% | 22.6%/1.6%/0.0% | 868.69/894.48 |
| cand-a31726b9f88bb946 | heston | adverse | illustrative | converged | [546.67, 669.49] | 74.8% | 0.0% | 27.4%/1.1%/0.0% | 872.39/897.28 |
| cand-a31726b9f88bb946 | heston_jump | adverse | illustrative | converged | [591.02, 712.90] | 76.2% | 0.5% | 28.3%/1.2%/0.0% | 883.80/957.18 |
| cand-a31726b9f88bb946 | black_scholes_gbm | rupture | illustrative | converged | [1425.32, 1519.27] | 97.6% | 0.0% | 62.4%/8.9%/0.0% | 0.00/248.00 |
| cand-a31726b9f88bb946 | local_volatility | rupture | partial | converged | [1169.70, 1274.89] | 93.0% | 0.0% | 50.6%/4.7%/0.0% | 816.81/857.49 |
| cand-a31726b9f88bb946 | heston | rupture | illustrative | converged | [1185.54, 1281.09] | 95.1% | 0.0% | 50.4%/3.8%/0.0% | 0.00/822.08 |
| cand-a31726b9f88bb946 | heston_jump | rupture | illustrative | converged | [1197.64, 1350.01] | 93.2% | 0.5% | 48.4%/4.8%/0.9% | 830.41/923.30 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | neutral | illustrative | converged | [-82.19, -24.99] | 46.8% | 0.0% | 0.0%/0.0%/0.0% | 718.30/735.80 |
| cand-b9aa8a0e0964eb88 | local_volatility | neutral | partial | converged | [-118.20, -64.56] | 44.6% | 0.0% | 0.0%/0.0%/0.0% | 721.34/735.91 |
| cand-b9aa8a0e0964eb88 | heston | neutral | illustrative | converged | [-10.60, 46.11] | 54.3% | 0.0% | 0.0%/0.0%/0.0% | 716.98/730.03 |
| cand-b9aa8a0e0964eb88 | heston_jump | neutral | illustrative | converged | [-10.95, 48.28] | 53.8% | 0.0% | 0.0%/0.0%/0.0% | 716.85/729.28 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | thesis | illustrative | converged | [-37.46, 18.42] | 49.8% | 0.0% | 0.0%/0.0%/0.0% | 714.37/731.13 |
| cand-b9aa8a0e0964eb88 | local_volatility | thesis | partial | converged | [-1.44, 49.46] | 58.2% | 0.0% | 0.0%/0.0%/0.0% | 716.49/728.97 |
| cand-b9aa8a0e0964eb88 | heston | thesis | illustrative | converged | [55.35, 113.41] | 58.8% | 0.0% | 0.0%/0.0%/0.0% | 714.47/729.31 |
| cand-b9aa8a0e0964eb88 | heston_jump | thesis | illustrative | converged | [27.22, 86.14] | 55.6% | 0.0% | 0.0%/0.0%/0.0% | 715.40/730.16 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | adverse | illustrative | converged | [-310.24, -258.93] | 25.7% | 0.0% | 0.0%/0.0%/0.0% | 729.76/743.62 |
| cand-b9aa8a0e0964eb88 | local_volatility | adverse | partial | converged | [-330.70, -283.56] | 26.3% | 0.0% | 0.0%/0.0%/0.0% | 732.55/746.43 |
| cand-b9aa8a0e0964eb88 | heston | adverse | illustrative | converged | [-302.19, -251.49] | 25.4% | 0.0% | 0.0%/0.0%/0.0% | 729.27/742.88 |
| cand-b9aa8a0e0964eb88 | heston_jump | adverse | illustrative | converged | [-270.79, -215.82] | 30.0% | 0.0% | 0.0%/0.0%/0.0% | 738.00/786.23 |
| cand-b9aa8a0e0964eb88 | black_scholes_gbm | rupture | illustrative | converged | [-283.79, -231.41] | 27.4% | 0.0% | 0.0%/0.0%/0.0% | 731.06/743.01 |
| cand-b9aa8a0e0964eb88 | local_volatility | rupture | partial | converged | [-318.94, -276.00] | 24.8% | 0.0% | 0.0%/0.0%/0.0% | 734.43/746.68 |
| cand-b9aa8a0e0964eb88 | heston | rupture | illustrative | converged | [-341.87, -293.86] | 21.4% | 0.0% | 0.0%/0.0%/0.0% | 728.32/740.28 |
| cand-b9aa8a0e0964eb88 | heston_jump | rupture | illustrative | converged | [-351.21, -300.51] | 22.5% | 0.0% | 0.0%/0.0%/0.0% | 745.82/791.88 |

## 12. Robustesse et désaccord des modèles

| Candidat | Verdict | Score | Dispersion P(profit) | Dispersion P&L | Dispersion CVaR | Modèles invalides |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| cand-75984ebc6c766510 | data_insufficient | 47.2 | 31.1% | 435.77 | 101.28 | 0 |
| cand-5159edae09c7d168 | data_insufficient | 78.6 | 29.7% | 820.03 | 555.72 | 0 |
| cand-4dfb14afde235e50 | data_insufficient | 77.4 | 18.0% | 966.98 | 618.57 | 0 |
| cand-119e6d7d30c47119 | data_insufficient | 47.0 | 30.6% | 379.90 | 95.79 | 0 |
| cand-a31726b9f88bb946 | data_insufficient | 81.0 | 38.7% | 1190.89 | 709.18 | 0 |
| cand-b9aa8a0e0964eb88 | data_insufficient | 41.3 | 37.4% | 410.24 | 62.91 | 0 |

## 13. Stress tests

| Candidat | Stress | Statut | P&L stressé | Méthode |
| --- | --- | --- | ---: | --- |
| cand-75984ebc6c766510 | catalyst_delay | failed | -867.51 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-75984ebc6c766510 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-75984ebc6c766510 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-75984ebc6c766510 | rates_shock | data_insufficient | n/a | not_computed |
| cand-75984ebc6c766510 | eurusd_adverse | data_insufficient | -64.86 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-75984ebc6c766510 | bid_ask_x2 | failed | -224.86 | exact_additional_leg_spread_cost |
| cand-75984ebc6c766510 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-75984ebc6c766510 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-75984ebc6c766510 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-75984ebc6c766510 | midpoint_unavailable | failed | -64.86 | already_prudent_ask_bid_entry |
| cand-75984ebc6c766510 | prudent_bid_ask_exit | failed | -224.86 | additional_full_spread_liquidation_proxy |
| cand-75984ebc6c766510 | slippage_x2 | failed | -64.96 | exact_configured_incremental_slippage |
| cand-75984ebc6c766510 | fees_x2 | failed | -66.16 | exact_configured_incremental_fees |
| cand-75984ebc6c766510 | early_exit | failed | -867.51 | worst_v10_1_pre_expiry_liquidation_proxy |
| cand-5159edae09c7d168 | catalyst_delay | failed | -680.19 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-5159edae09c7d168 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-5159edae09c7d168 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-5159edae09c7d168 | rates_shock | data_insufficient | n/a | not_computed |
| cand-5159edae09c7d168 | eurusd_adverse | data_insufficient | 222.48 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-5159edae09c7d168 | bid_ask_x2 | passed | 162.48 | exact_additional_leg_spread_cost |
| cand-5159edae09c7d168 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-5159edae09c7d168 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-5159edae09c7d168 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-5159edae09c7d168 | midpoint_unavailable | passed | 222.48 | already_prudent_ask_bid_entry |
| cand-5159edae09c7d168 | prudent_bid_ask_exit | passed | 162.48 | additional_full_spread_liquidation_proxy |
| cand-5159edae09c7d168 | slippage_x2 | passed | 222.43 | exact_configured_incremental_slippage |
| cand-5159edae09c7d168 | fees_x2 | passed | 221.83 | exact_configured_incremental_fees |
| cand-5159edae09c7d168 | early_exit | failed | -680.19 | worst_v10_1_pre_expiry_liquidation_proxy |
| cand-4dfb14afde235e50 | catalyst_delay | failed | -771.19 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-4dfb14afde235e50 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-4dfb14afde235e50 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-4dfb14afde235e50 | rates_shock | data_insufficient | n/a | not_computed |
| cand-4dfb14afde235e50 | eurusd_adverse | data_insufficient | 411.16 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-4dfb14afde235e50 | bid_ask_x2 | passed | 311.16 | exact_additional_leg_spread_cost |
| cand-4dfb14afde235e50 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-4dfb14afde235e50 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-4dfb14afde235e50 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-4dfb14afde235e50 | midpoint_unavailable | passed | 411.16 | already_prudent_ask_bid_entry |
| cand-4dfb14afde235e50 | prudent_bid_ask_exit | passed | 311.16 | additional_full_spread_liquidation_proxy |
| cand-4dfb14afde235e50 | slippage_x2 | passed | 411.06 | exact_configured_incremental_slippage |
| cand-4dfb14afde235e50 | fees_x2 | passed | 409.86 | exact_configured_incremental_fees |
| cand-4dfb14afde235e50 | early_exit | failed | -771.19 | worst_v10_1_pre_expiry_liquidation_proxy |
| cand-119e6d7d30c47119 | catalyst_delay | failed | -774.73 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-119e6d7d30c47119 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-119e6d7d30c47119 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-119e6d7d30c47119 | rates_shock | data_insufficient | n/a | not_computed |
| cand-119e6d7d30c47119 | eurusd_adverse | data_insufficient | -79.91 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-119e6d7d30c47119 | bid_ask_x2 | failed | -239.91 | exact_additional_leg_spread_cost |
| cand-119e6d7d30c47119 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-119e6d7d30c47119 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-119e6d7d30c47119 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-119e6d7d30c47119 | midpoint_unavailable | failed | -79.91 | already_prudent_ask_bid_entry |
| cand-119e6d7d30c47119 | prudent_bid_ask_exit | failed | -239.91 | additional_full_spread_liquidation_proxy |
| cand-119e6d7d30c47119 | slippage_x2 | failed | -80.01 | exact_configured_incremental_slippage |
| cand-119e6d7d30c47119 | fees_x2 | failed | -81.21 | exact_configured_incremental_fees |
| cand-119e6d7d30c47119 | early_exit | failed | -774.73 | worst_v10_1_pre_expiry_liquidation_proxy |
| cand-a31726b9f88bb946 | catalyst_delay | failed | -1138.92 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-a31726b9f88bb946 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-a31726b9f88bb946 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-a31726b9f88bb946 | rates_shock | data_insufficient | n/a | not_computed |
| cand-a31726b9f88bb946 | eurusd_adverse | data_insufficient | 281.40 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-a31726b9f88bb946 | bid_ask_x2 | passed | 201.40 | exact_additional_leg_spread_cost |
| cand-a31726b9f88bb946 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-a31726b9f88bb946 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-a31726b9f88bb946 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-a31726b9f88bb946 | midpoint_unavailable | passed | 281.40 | already_prudent_ask_bid_entry |
| cand-a31726b9f88bb946 | prudent_bid_ask_exit | passed | 201.40 | additional_full_spread_liquidation_proxy |
| cand-a31726b9f88bb946 | slippage_x2 | passed | 281.35 | exact_configured_incremental_slippage |
| cand-a31726b9f88bb946 | fees_x2 | passed | 280.75 | exact_configured_incremental_fees |
| cand-a31726b9f88bb946 | early_exit | failed | -1138.92 | worst_v10_1_pre_expiry_liquidation_proxy |
| cand-b9aa8a0e0964eb88 | catalyst_delay | failed | -807.67 | worst_existing_pre_expiry_checkpoint_proxy |
| cand-b9aa8a0e0964eb88 | iv_crush | data_insufficient | n/a | v10_1_iv_down_scenario |
| cand-b9aa8a0e0964eb88 | market_sell_off | data_insufficient | n/a | worst_v10_1_stable_iv_spot_scenario |
| cand-b9aa8a0e0964eb88 | rates_shock | data_insufficient | n/a | not_computed |
| cand-b9aa8a0e0964eb88 | eurusd_adverse | data_insufficient | -91.38 | usd_pnl_unchanged_fx_budget_diagnostic |
| cand-b9aa8a0e0964eb88 | bid_ask_x2 | failed | -291.38 | exact_additional_leg_spread_cost |
| cand-b9aa8a0e0964eb88 | open_interest_volume_degraded | data_insufficient | n/a | liquidity_gate |
| cand-b9aa8a0e0964eb88 | negative_gap | data_insufficient | n/a | worst_configured_terminal_or_checkpoint_spot |
| cand-b9aa8a0e0964eb88 | positive_gap | data_insufficient | n/a | best_configured_terminal_or_checkpoint_spot |
| cand-b9aa8a0e0964eb88 | midpoint_unavailable | failed | -91.38 | already_prudent_ask_bid_entry |
| cand-b9aa8a0e0964eb88 | prudent_bid_ask_exit | failed | -291.38 | additional_full_spread_liquidation_proxy |
| cand-b9aa8a0e0964eb88 | slippage_x2 | failed | -91.48 | exact_configured_incremental_slippage |
| cand-b9aa8a0e0964eb88 | fees_x2 | failed | -92.68 | exact_configured_incremental_fees |
| cand-b9aa8a0e0964eb88 | early_exit | failed | -807.67 | worst_v10_1_pre_expiry_liquidation_proxy |

## 14–15. Allocation et cash non utilisé

### prudent — rang 1

- Allocation : cash / NO_TRADE
- Réserve : 1000.00 EUR
- P&L espéré expérimental : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Contraintes actives : aucune proche de la borne
- Motif du cash : Cash/NO_TRADE has objective zero and dominates feasible risky allocations.

### prudent — rang 2

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré expérimental : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### prudent — rang 3

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré expérimental : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### prudent — rang 4

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré expérimental : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### prudent — rang 5

- Allocation : 1× cand-b9aa8a0e0964eb88
- Réserve : 124.27 EUR
- P&L espéré expérimental : -71.23 EUR
- CVaR 95 : 692.51 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### balanced — rang 1

- Allocation : cash / NO_TRADE
- Réserve : 1000.00 EUR
- P&L espéré expérimental : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Contraintes actives : aucune proche de la borne
- Motif du cash : Cash/NO_TRADE has objective zero and dominates feasible risky allocations.

### balanced — rang 2

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré expérimental : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### balanced — rang 3

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré expérimental : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### balanced — rang 4

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré expérimental : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### balanced — rang 5

- Allocation : 1× cand-b9aa8a0e0964eb88
- Réserve : 124.27 EUR
- P&L espéré expérimental : -71.23 EUR
- CVaR 95 : 692.51 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### aggressive — rang 1

- Allocation : 1× cand-4dfb14afde235e50
- Réserve : 325.40 EUR
- P&L espéré expérimental : 730.48 EUR
- CVaR 95 : 503.53 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### aggressive — rang 2

- Allocation : 1× cand-5159edae09c7d168
- Réserve : 404.72 EUR
- P&L espéré expérimental : 465.29 EUR
- CVaR 95 : 485.99 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### aggressive — rang 3

- Allocation : cash / NO_TRADE
- Réserve : 1000.00 EUR
- P&L espéré expérimental : 0.00 EUR
- CVaR 95 : 0.00 EUR
- Contraintes actives : aucune proche de la borne
- Motif du cash : Cash/NO_TRADE has objective zero and dominates feasible risky allocations.

### aggressive — rang 4

- Allocation : 1× cand-a31726b9f88bb946
- Réserve : 2.45 EUR
- P&L espéré expérimental : 587.01 EUR
- CVaR 95 : 837.06 EUR
- Contraintes actives : budget, maximum_loss, maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

### aggressive — rang 5

- Allocation : 1× cand-119e6d7d30c47119
- Réserve : 316.66 EUR
- P&L espéré expérimental : -14.17 EUR
- CVaR 95 : 612.02 EUR
- Contraintes actives : maximum_concentration
- Motif du cash : Unused cash is retained because whole contracts and hard constraints make the residual budget non-deployable without weakening policy.

## 16. Risques d'exécution

- `cand-75984ebc6c766510` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5
- `cand-5159edae09c7d168` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5
- `cand-4dfb14afde235e50` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5
- `cand-119e6d7d30c47119` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5
- `cand-a31726b9f88bb946` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5
- `cand-b9aa8a0e0964eb88` : `transmit=false` ; `what_if=true` ; `order_capability=forbidden` ; blockers=5

## 17. Règles de sortie

### cand-75984ebc6c766510

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

### cand-5159edae09c7d168

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

### cand-4dfb14afde235e50

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

### cand-119e6d7d30c47119

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

### cand-a31726b9f88bb946

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

### cand-b9aa8a0e0964eb88

- `profit_target` → `EXIT_REVIEW` ; seuil=`1.5` ; données=prudent_liquidation_value, actual_cost
- `partial_profit_target` → `REDUCE` ; seuil=`0.8` ; données=prudent_liquidation_value, actual_cost
- `operational_stop_loss` → `EXIT_REVIEW` ; seuil=`0.7` ; données=prudent_liquidation_value, actual_cost
- `fundamental_invalidation` → `THESIS_INVALIDATED` ; seuil=`True` ; données=thesis_review
- `time_exit` → `EXIT_REVIEW` ; seuil=`60` ; données=days_to_expiration
- `iv_crush` → `REDUCE` ; seuil=`0.35` ; données=entry_iv, current_iv
- `liquidity_deterioration` → `EXIT_REVIEW` ; seuil=`0.05` ; données=liquidity_score, bid_ask
- `expected_value_negative` → `EXIT_REVIEW` ; seuil=`0.0` ; données=expected_remaining_pnl
- `cvar_limit` → `EXIT_REVIEW` ; seuil=`0.8` ; données=remaining_cvar_95, actual_cost
- `data_insufficient` → `BLOCKED_INSUFFICIENT_DATA` ; seuil=`True` ; données=quotes, greeks, probabilities, liquidity
- `data_stale` → `DATA_STALE` ; seuil=`False` ; données=snapshot_timestamp
- `trailing_drawdown` → `EXIT_REVIEW` ; seuil=`0.3` ; données=peak_prudent_liquidation_value, prudent_liquidation_value, actual_cost
- `temporal_invalidation` → `EXIT_REVIEW` ; seuil=`dossier_horizon_days` ; données=opened_at, horizon_days
- `theta_limit` → `REDUCE` ; seuil=`200.0` ; données=current_greeks.theta
- `exit_before_catalyst` → `EXIT_REVIEW` ; seuil=`5` ; données=catalyst_date, snapshot_timestamp
- `exit_after_catalyst` → `EXIT_REVIEW` ; seuil=`3` ; données=catalyst_date, snapshot_timestamp

## 18. Conditions d'invalidation

- `cand-75984ebc6c766510` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR
- `cand-5159edae09c7d168` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR
- `cand-4dfb14afde235e50` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR
- `cand-119e6d7d30c47119` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR
- `cand-a31726b9f88bb946` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR
- `cand-b9aa8a0e0964eb88` : Bullish thesis or catalyst timing changes materially; Live maximum debit exceeds the displayed preview; Contract deliverable, multiplier, or quote provenance differs in IBKR

## 19. Readiness status

| Fonction | Statut | Implémentée | Blockers |
| --- | --- | --- | --- |
| v10_1_contractual_engine | production_ready_offline | true | — |
| unified_data_provenance | production_ready_offline | true | US.market_calendar |
| deterministic_event_normalization | experimental_offline | true | Likelihood impact still requires calibrated rules and reviewed events. |
| bayesian_scenario_engine | experimental_offline | true | Priors and likelihoods are not historically calibrated. |
| multi_model_simulation | fixture_only | true | Parameters require historical calibration and convergence review. |
| historical_calibration | requires_historical_calibration | true | BLOCKED_MISSING_CALIBRATION_DATA |
| walk_forward_backtest | requires_historical_calibration | true | BLOCKED_MISSING_CALIBRATION_DATA |
| exact_integer_allocation | experimental_offline | true | Objective inputs remain experimental until model validation. |
| position_monitoring | experimental_offline | true | Live/paper trajectory evidence has not been completed. |
| standalone_reporting | production_ready_offline | true | — |
| ibkr_opra_read_only_adapter | adapter_ready_not_connected | true | not_configured |
| live_market_data | requires_live_market_data | false | OPRA entitlements, TWS/IB Gateway session, and combo quotes are absent. |
| paper_trading_validation | requires_paper_trading | false | No minimum-duration paper campaign has been completed. |
| order_execution | blocked_for_execution | false | Execution is outside this product version by explicit policy. |

## 20. Raisons de NO_TRADE ou blocage

- US.market_calendar
- BLOCKED_MISSING_CALIBRATION_DATA
- BLOCKED_MISSING_CALIBRATION_DATA
- paper_trading_not_run
- execution_forbidden

## Exports et reproductibilité

- Exports : JSON strict, Markdown et HTML autonome.
- Schéma : `11.1`
- Seed : `20260728`
- Profil : `fast_fixture`
- Versions : `{'take_two_options': '0.11.1', 'schema': '11.1', 'python': '3.14.4', 'numpy': '2.5.1'}`
- Durées : `{'load_inputs': 0.203628, 'data_hub': 0.002328, 'events_and_bayes': 0.000356, 'offline_calibration_and_backtest': 1.9e-05, 'calibration_and_covariance': 0.001464, 'simulation': 0.047038, 'valuation_and_validation': 2.836969, 'allocation_and_previews': 0.023966}`

## Limites et validations requises

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
