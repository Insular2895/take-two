# TTWO — Long call

- Ticket schema: `1.0`
- Fixture status: `SYNTHETIC_TEST_FIXTURE`
- Classification: `research_candidate`
- Market timestamp: `2026-07-18T12:00:00+00:00`
- Currency: `USD`
- Data freshness: `current`
- Expirations: `2027-01-15T21:00:00+00:00`
- Exact DTE: `181.37500000` days
- Intraday precision: `APPROXIMATED_DATE_ENGINE`
- Intraday warning: American FD engine uses date-level exercise grid; intraday exposure is approximate.

## Legs

| Side | Qty | Type | Strike | Expiration | Bid | Ask | Mid | IV | Multiplier | Premium paid | Premium received |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| long | 1 | call | 260.00 | 2027-01-15T21:00:00+00:00 | 28.0000 | 30.0000 | 29.0000 | 0.360000 | 100 | 2,900.00 USD | 0.00 USD |

Greeks `TTWO  270115C00260000`:

- Delta: `0.572291 currency_per_1_spot_unit (HIGH)`
- Gamma: `0.006010 delta_per_1_spot_unit (HIGH)`
- Theta: `-0.085794 currency_per_calendar_day (HIGH)`
- Vega: `0.713012 currency_per_1_vol_point (HIGH)`
- Rho: `0.594610 currency_per_1_percentage_point_rate (HIGH)`
- Vanna: `0.000794 currency_per_spot_unit_per_vol_point (HIGH)`
- Vomma: `-0.000252 currency_per_vol_point_squared (MEDIUM)`
- Charm / delta drift: `-0.000271 delta_drift_per_calendar_day (HIGH)`
- Veta / vega drift: `-0.001885 vega_drift_per_calendar_day (HIGH)`
- Speed: `-0.000038 gamma_per_spot_unit (LOW)`
- Color / gamma drift: `0.000017 gamma_drift_per_calendar_day (MEDIUM)`

## Cost and capital

- Premium paid / received: 2,900.00 USD / 0.00 USD
- Net premium: 2,900.00 USD
- Mid theoretical value: 2,900.00 USD
- Entry bid/ask / slippage / commission: 100.00 USD / 1.50 USD / 0.65 USD
- Total entry cost: 3,002.15 USD
- Exit bid/ask / slippage / commission: 100.00 USD / 1.50 USD / 0.65 USD
- Total exit cost: 102.15 USD (`ESTIMATED_CONFIGURED_EXECUTION_MODEL`)
- Total round-trip cost: 204.30 USD
- Margin / buying power: UNKNOWN / UNKNOWN (`NOT_REQUIRED`)
- Capital at risk: 3,002.15 USD
- Maximum loss / profit: 3,002.15 USD / UNKNOWN
- Expiration breakevens: `[290.0215]`
- Lambda / delta-notional / gross-delta leverage: `5.337029` / `4.914173` / `4.914173`

## Flat-spot carry

- Current local theta: -8.58 USD per day
- Carry 1/7/30/60/90d: `-8.579419` / `-60.499389` / `-267.203716` / `-558.932735` / `-884.852360`
- Decay acceleration status: `ACCELERATING`

| Horizon | Valuation time | Full-repriced value | Flat-spot carry | Class |
| ---: | --- | ---: | ---: | --- |
| 0d | 2026-07-18T12:00:00+00:00 | 2764.2876 | 0.0000 | PURE_FLAT_SPOT_CARRY |
| 1d | 2026-07-19T12:00:00+00:00 | 2755.7082 | -8.5794 | PURE_FLAT_SPOT_CARRY |
| 7d | 2026-07-25T12:00:00+00:00 | 2703.7883 | -60.4994 | PURE_FLAT_SPOT_CARRY |
| 30d | 2026-08-17T12:00:00+00:00 | 2497.0839 | -267.2037 | PURE_FLAT_SPOT_CARRY |
| 60d | 2026-09-16T12:00:00+00:00 | 2205.3549 | -558.9327 | PURE_FLAT_SPOT_CARRY |
| 90d | 2026-10-16T12:00:00+00:00 | 1879.4353 | -884.8524 | PURE_FLAT_SPOT_CARRY |
| 181d | 2027-01-15T21:00:00+00:00 | 0.0000 | -2764.2876 | PURE_FLAT_SPOT_CARRY |

## Spot × time × volatility scenarios

**base_constant_leg_iv** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Horizon | Position value | Gross PnL | Round-trip cost | Net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 180.4530 | 7d | 201.7212 | -2698.2788 | 204.3000 | -2902.5788 |
| 210.0000 | 7d | 721.2577 | -2178.7423 | 204.3000 | -2383.0423 |
| 219.1215 | 7d | 983.2961 | -1916.7039 | 204.3000 | -2121.0039 |
| 257.7900 | 7d | 2703.7883 | -196.2117 | 204.3000 | -400.5117 |
| 260.0000 | 7d | 2831.3352 | -68.6648 | 204.3000 | -272.9648 |
| 296.4585 | 7d | 5321.8021 | 2421.8021 | 204.3000 | 2217.5021 |
| 330.0000 | 7d | 8105.0981 | 5205.0981 | 204.3000 | 5000.7981 |
| 335.1270 | 7d | 8559.2631 | 5659.2631 | 204.3000 | 5454.9631 |
| 180.4530 | 30d | 146.0469 | -2753.9531 | 204.3000 | -2958.2531 |
| 210.0000 | 30d | 595.8361 | -2304.1639 | 204.3000 | -2508.4639 |
| 219.1215 | 30d | 836.2370 | -2063.7630 | 204.3000 | -2268.0630 |
| 257.7900 | 30d | 2497.0839 | -402.9161 | 204.3000 | -607.2161 |
| 260.0000 | 30d | 2623.2693 | -276.7307 | 204.3000 | -481.0307 |
| 296.4585 | 30d | 5119.5458 | 2219.5458 | 204.3000 | 2015.2458 |
| 330.0000 | 30d | 7935.4373 | 5035.4373 | 204.3000 | 4831.1373 |
| 335.1270 | 30d | 8395.1935 | 5495.1935 | 204.3000 | 5290.8935 |
| 180.4530 | 60d | 83.2513 | -2816.7487 | 204.3000 | -3021.0487 |
| 210.0000 | 60d | 431.9223 | -2468.0777 | 204.3000 | -2672.3777 |
| 219.1215 | 60d | 638.6857 | -2261.3143 | 204.3000 | -2465.6143 |
| 257.7900 | 60d | 2205.3549 | -694.6451 | 204.3000 | -898.9451 |
| 260.0000 | 60d | 2329.5597 | -570.4403 | 204.3000 | -774.7403 |
| 296.4585 | 60d | 4840.7414 | 1940.7414 | 204.3000 | 1736.4414 |
| 330.0000 | 60d | 7712.3396 | 4812.3396 | 204.3000 | 4608.0396 |
| 335.1270 | 60d | 8181.0860 | 5281.0860 | 204.3000 | 5076.7860 |
| 180.4530 | 90d | 35.6444 | -2864.3556 | 204.3000 | -3068.6556 |
| 210.0000 | 90d | 271.6607 | -2628.3393 | 204.3000 | -2832.6393 |
| 219.1215 | 90d | 436.0762 | -2463.9238 | 204.3000 | -2668.2238 |
| 257.7900 | 90d | 1879.4353 | -1020.5647 | 204.3000 | -1224.8647 |
| 260.0000 | 90d | 2001.3247 | -898.6753 | 204.3000 | -1102.9753 |
| 296.4585 | 90d | 4541.9584 | 1641.9584 | 204.3000 | 1437.6584 |
| 330.0000 | 90d | 7491.5313 | 4591.5313 | 204.3000 | 4387.2313 |
| 335.1270 | 90d | 7971.7336 | 5071.7336 | 204.3000 | 4867.4336 |
| 180.4530 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 210.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 219.1215 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 257.7900 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 260.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 296.4585 | 182d | 3645.8500 | 745.8500 | 204.3000 | 541.5500 |
| 330.0000 | 182d | 7000.0000 | 4100.0000 | 204.3000 | 3895.7000 |
| 335.1270 | 182d | 7512.7000 | 4612.7000 | 204.3000 | 4408.4000 |

**configured_iv_crush** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Horizon | Position value | Gross PnL | Round-trip cost | Net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 180.4530 | 7d | 40.8894 | -2859.1106 | 204.3000 | -3063.4106 |
| 210.0000 | 7d | 301.2676 | -2598.7324 | 204.3000 | -2803.0324 |
| 219.1215 | 7d | 479.3017 | -2420.6983 | 204.3000 | -2624.9983 |
| 257.7900 | 7d | 2003.1358 | -896.8642 | 204.3000 | -1101.1642 |
| 260.0000 | 7d | 2129.9847 | -770.0153 | 204.3000 | -974.3153 |
| 296.4585 | 7d | 4741.1979 | 1841.1979 | 204.3000 | 1636.8979 |
| 330.0000 | 7d | 7728.3448 | 4828.3448 | 204.3000 | 4624.0448 |
| 335.1270 | 7d | 8212.1651 | 5312.1651 | 204.3000 | 5107.8651 |
| 180.4530 | 30d | 25.0648 | -2874.9352 | 204.3000 | -3079.2352 |
| 210.0000 | 30d | 232.4311 | -2667.5689 | 204.3000 | -2871.8689 |
| 219.1215 | 30d | 388.1304 | -2511.8696 | 204.3000 | -2716.1696 |
| 257.7900 | 30d | 1842.6095 | -1057.3905 | 204.3000 | -1261.6905 |
| 260.0000 | 30d | 1968.0615 | -931.9385 | 204.3000 | -1136.2385 |
| 296.4585 | 30d | 4592.7061 | 1692.7061 | 204.3000 | 1488.4061 |
| 330.0000 | 30d | 7615.1262 | 4715.1262 | 204.3000 | 4510.8262 |
| 335.1270 | 30d | 8103.6747 | 5203.6747 | 204.3000 | 4999.3747 |
| 180.4530 | 60d | 10.5283 | -2889.4717 | 204.3000 | -3093.7717 |
| 210.0000 | 60d | 148.9886 | -2751.0114 | 204.3000 | -2955.3114 |
| 219.1215 | 60d | 271.6729 | -2628.3271 | 204.3000 | -2832.6271 |
| 257.7900 | 60d | 1617.4605 | -1282.5395 | 204.3000 | -1486.8395 |
| 260.0000 | 60d | 1740.8694 | -1159.1306 | 204.3000 | -1363.4306 |
| 296.4585 | 60d | 4392.5066 | 1492.5066 | 204.3000 | 1288.2066 |
| 330.0000 | 60d | 7470.9666 | 4570.9666 | 204.3000 | 4366.6666 |
| 335.1270 | 60d | 7966.3191 | 5066.3191 | 204.3000 | 4862.0191 |
| 180.4530 | 90d | 2.7542 | -2897.2458 | 204.3000 | -3101.5458 |
| 210.0000 | 90d | 77.1754 | -2822.8246 | 204.3000 | -3027.1246 |
| 219.1215 | 90d | 161.9285 | -2738.0715 | 204.3000 | -2942.3715 |
| 257.7900 | 90d | 1367.9160 | -1532.0840 | 204.3000 | -1736.3840 |
| 260.0000 | 90d | 1488.9150 | -1411.0850 | 204.3000 | -1615.3850 |
| 296.4585 | 90d | 4185.4705 | 1285.4705 | 204.3000 | 1081.1705 |
| 330.0000 | 90d | 7334.2055 | 4434.2055 | 204.3000 | 4229.9055 |
| 335.1270 | 90d | 7836.8011 | 4936.8011 | 204.3000 | 4732.5011 |
| 180.4530 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 210.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 219.1215 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 257.7900 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 260.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 296.4585 | 182d | 3645.8500 | 745.8500 | 204.3000 | 541.5500 |
| 330.0000 | 182d | 7000.0000 | 4100.0000 | 204.3000 | 3895.7000 |
| 335.1270 | 182d | 7512.7000 | 4612.7000 | 204.3000 | 4408.4000 |

**configured_iv_expansion** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Horizon | Position value | Gross PnL | Round-trip cost | Net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 180.4530 | 7d | 479.6873 | -2420.3127 | 204.3000 | -2624.6127 |
| 210.0000 | 7d | 1220.7158 | -1679.2842 | 204.3000 | -1883.5842 |
| 219.1215 | 7d | 1542.5322 | -1357.4678 | 204.3000 | -1561.7678 |
| 257.7900 | 7d | 3402.0867 | 502.0867 | 204.3000 | 297.7867 |
| 260.0000 | 7d | 3531.3294 | 631.3294 | 204.3000 | 427.0294 |
| 296.4585 | 7d | 5968.8857 | 3068.8857 | 204.3000 | 2864.5857 |
| 330.0000 | 7d | 8622.1158 | 5722.1158 | 204.3000 | 5517.8158 |
| 335.1270 | 7d | 9054.0387 | 6154.0387 | 204.3000 | 5949.7387 |
| 180.4530 | 30d | 374.8883 | -2525.1117 | 204.3000 | -2729.4117 |
| 210.0000 | 30d | 1042.5560 | -1857.4440 | 204.3000 | -2061.7440 |
| 219.1215 | 30d | 1344.3181 | -1555.6819 | 204.3000 | -1759.9819 |
| 257.7900 | 30d | 3149.5650 | 249.5650 | 204.3000 | 45.2650 |
| 260.0000 | 30d | 3277.3806 | 377.3806 | 204.3000 | 173.0806 |
| 296.4585 | 30d | 5714.2792 | 2814.2792 | 204.3000 | 2609.9792 |
| 330.0000 | 30d | 8393.0199 | 5493.0199 | 204.3000 | 5288.7199 |
| 335.1270 | 30d | 8829.9585 | 5929.9585 | 204.3000 | 5725.6585 |
| 180.4530 | 60d | 245.5816 | -2654.4184 | 204.3000 | -2858.7184 |
| 210.0000 | 60d | 801.8037 | -2098.1963 | 204.3000 | -2302.4963 |
| 219.1215 | 60d | 1071.8762 | -1828.1238 | 204.3000 | -2032.4238 |
| 257.7900 | 60d | 2791.7174 | -108.2826 | 204.3000 | -312.5826 |
| 260.0000 | 60d | 2917.4645 | 17.4645 | 204.3000 | -186.8355 |
| 296.4585 | 60d | 5358.9348 | 2458.9348 | 204.3000 | 2254.6348 |
| 330.0000 | 60d | 8083.8295 | 5183.8295 | 204.3000 | 4979.5295 |
| 335.1270 | 60d | 8529.3494 | 5629.3494 | 204.3000 | 5425.0494 |
| 180.4530 | 90d | 131.3200 | -2768.6800 | 204.3000 | -2972.9800 |
| 210.0000 | 90d | 552.8113 | -2347.1887 | 204.3000 | -2551.4887 |
| 219.1215 | 90d | 781.6873 | -2118.3127 | 204.3000 | -2322.6127 |
| 257.7900 | 90d | 2389.8803 | -510.1197 | 204.3000 | -714.4197 |
| 260.0000 | 90d | 2513.2241 | -386.7759 | 204.3000 | -591.0759 |
| 296.4585 | 90d | 4970.5189 | 2070.5189 | 204.3000 | 1866.2189 |
| 330.0000 | 90d | 7764.8911 | 4864.8911 | 204.3000 | 4660.5911 |
| 335.1270 | 90d | 8222.4014 | 5322.4014 | 204.3000 | 5118.1014 |
| 180.4530 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 210.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 219.1215 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 257.7900 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 260.0000 | 182d | 0.0000 | -2900.0000 | 204.3000 | -3104.3000 |
| 296.4585 | 182d | 3645.8500 | 745.8500 | 204.3000 | 541.5500 |
| 330.0000 | 182d | 7000.0000 | 4100.0000 | 204.3000 | 3895.7000 |
| 335.1270 | 182d | 7512.7000 | 4612.7000 | 204.3000 | 4408.4000 |

## Rate-curve stresses

- `base_curve` / `BASE_CURVE`: shifts `TTWO  270115C00260000=+0.00bp`, value 2764.2876, gross PnL -135.7124, net PnL -340.0124, status `CONFIGURED_STRESS`.
- `parallel_up` / `PARALLEL_UP`: shifts `TTWO  270115C00260000=+100.00bp`, value 2824.0913, gross PnL -75.9087, net PnL -280.2087, status `CONFIGURED_STRESS`.
- `parallel_down` / `PARALLEL_DOWN`: shifts `TTWO  270115C00260000=-100.00bp`, value 2705.1706, gross PnL -194.8294, net PnL -399.1294, status `CONFIGURED_STRESS`.
- `steepening` / `STEEPENING`: shifts `TTWO  270115C00260000=-35.72bp`, value 2743.0903, gross PnL -156.9097, net PnL -361.2097, status `CONFIGURED_STRESS`.
- `flattening` / `FLATTENING`: shifts `TTWO  270115C00260000=+35.72bp`, value 2785.5726, gross PnL -114.4274, net PnL -318.7274, status `CONFIGURED_STRESS`.
## Breakeven clock and target timing

- `base_constant_leg_iv` at 0d: roots `[263.55867619]`, profitable `['[263.5587, ∞]']`, status `SOLVED`
- `base_constant_leg_iv` at 7d: roots `[264.56845752]`, profitable `['[264.5685, ∞]']`, status `SOLVED`
- `base_constant_leg_iv` at 30d: roots `[267.96922822]`, profitable `['[267.9692, ∞]']`, status `SOLVED`
- `base_constant_leg_iv` at 60d: roots `[272.60599209]`, profitable `['[272.6060, ∞]']`, status `SOLVED`
- `base_constant_leg_iv` at 90d: roots `[277.47867757]`, profitable `['[277.4787, ∞]']`, status `SOLVED`
- `base_constant_leg_iv` at 182d: roots `[291.04300247]`, profitable `['[291.0430, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 0d: roots `[274.44804288]`, profitable `['[274.4480, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 7d: roots `[275.13874094]`, profitable `['[275.1387, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 30d: roots `[277.43526947]`, profitable `['[277.4353, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 60d: roots `[280.48524623]`, profitable `['[280.4852, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 90d: roots `[283.57000552]`, profitable `['[283.5700, ∞]']`, status `SOLVED`
- `configured_iv_crush` at 182d: roots `[291.04300247]`, profitable `['[291.0430, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 0d: roots `[251.2250821]`, profitable `['[251.2251, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 7d: roots `[252.53666976]`, profitable `['[252.5367, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 30d: roots `[256.99676624]`, profitable `['[256.9968, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 60d: roots `[263.19727639]`, profitable `['[263.1973, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 90d: roots `[269.89543636]`, profitable `['[269.8954, ∞]']`, status `SOLVED`
- `configured_iv_expansion` at 182d: roots `[291.04300247]`, profitable `['[291.0430, ∞]']`, status `SOLVED`
- Target 210.0000, `base_constant_leg_iv`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`
- Target 260.0000, `base_constant_leg_iv`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`
- Target 330.0000, `base_constant_leg_iv`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`
- Target 210.0000, `configured_iv_crush`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`
- Target 260.0000, `configured_iv_crush`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`
- Target 330.0000, `configured_iv_crush`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`
- Target 210.0000, `configured_iv_expansion`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`
- Target 260.0000, `configured_iv_expansion`: `LATEST_PROFITABLE_ARRIVAL`, latest `2026-08-31T12:00:00+00:00`
- Target 330.0000, `configured_iv_expansion`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`

## Attribution, FX, probability and risks

- `base_constant_leg_iv_30d` full repricing PnL -471.5037; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-267.2037/0.0000/0.0000/0.0000/-204.3000/0.0000/0.00000000.
- `configured_iv_crush_30d` full repricing PnL -1125.9782; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-237.4342/-684.2440/0.0000/0.0000/-204.3000/0.0000/0.00000000.
- `configured_iv_expansion_30d` full repricing PnL 180.9773; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-296.7374/682.0147/0.0000/0.0000/-204.3000/0.0000/-0.00000000.
- `base_constant_leg_iv_parallel_up_30d` full repricing PnL -421.4378; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-272.0726/0.0000/54.9348/0.0000/-204.3000/0.0000/0.00000000.
- `base_constant_leg_iv_parallel_down_30d` full repricing PnL -521.0250; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-262.4059/0.0000/-54.3192/0.0000/-204.3000/0.0000/0.00000000.
- `base_constant_leg_iv_steepening_30d` full repricing PnL -491.5812; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-266.6438/0.0000/-20.6374/0.0000/-204.3000/0.0000/0.00000000.
- `base_constant_leg_iv_flattening_30d` full repricing PnL -451.3372; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-267.7629/0.0000/20.7257/0.0000/-204.3000/0.0000/0.00000000.
- P(touch): `null` — no configured/promoted P-path model.
- FX mode/status/contribution: `UNKNOWN` / `BLOCKED_UNKNOWN_FX_HANDLING` / `UNKNOWN`
- Intensity: `MODERATE`
- TTWO  270115C00260000: assignment=low; early_exercise=low; pin=low; adjusted_contract=False; human_review=False
- Warning: QuantLib American model values are indicative and not executable quotes
- Warning: Full repricing is primary; Greek/Taylor attribution is explanatory only.
- Warning: All leg-level execution estimates are indicative until combo evidence exists.

- Data status: `AVAILABLE_RESEARCH_ONLY`
- Probability status: `PROBABILITY_MODEL_NOT_AVAILABLE`
- Full repricing is the primary financial value; Taylor/Greek output is explanatory.
- Safety: transmit=`false`, what_if=`true`, order_capability=`forbidden`.
