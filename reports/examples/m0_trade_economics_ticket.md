# TTWO — Long call

- Ticket schema: `1.1`
- Fixture status: `SYNTHETIC_TEST_FIXTURE`
- Classification: `research_candidate`
- Market timestamp: `2026-07-18T12:00:00+00:00`
- Currency: `USD`
- Data freshness: `current`
- Expirations: `2027-01-15T21:00:00+00:00`
- Exact DTE: `181.37500000` days
- Lifecycle policy: `SAME_EXPIRY_HOLD_TO_EXPIRY`
- Managed exit deadline: `n/a`
- Intraday precision: `APPROXIMATED_DATE_ENGINE`
- Intraday warning: American FD engine uses date-level exercise grid; intraday exposure is approximate.

## Legs

| Side | Qty | Type | Strike | Expiration | Bid | Ask | Mid | IV | Mid premium | Executable paid | Executable received |
| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| long | 1 | call | 260.00 | 2027-01-15T21:00:00+00:00 | 28.0000 | 30.0000 | 29.0000 | 0.360000 | 2,900.00 USD | 3,000.00 USD | 0.00 USD |

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

## Cost — Entry

- Theoretical midpoint premium paid: 2,900.00 USD
- Theoretical midpoint premium received: 0.00 USD
- Theoretical midpoint net premium: 2,900.00 USD
- Executable premium paid at ask: 3,000.00 USD
- Executable premium received at bid: 0.00 USD
- Net executable debit/credit: 3,000.00 USD
- Entry spread cost: 100.00 USD
- Additional slippage: 1.50 USD
- Commission: 0.65 USD
- FX: UNKNOWN
- **TOTAL ENTRY CASH FLOW: 3,002.15 USD**
- Total capital required: 3,002.15 USD

## Cost — Exit

- Exit path estimate: `CLOSE_BEFORE_EXPIRY`
- Expected closing spread: 100.00 USD
- Expected slippage: 1.50 USD
- Closing commission: 0.65 USD
- Exercise cost if relevant: 0.00 USD
- Assignment cost if relevant: UNKNOWN
- Settlement cost if relevant: 0.00 USD
- Hold-to-expiry cost status: `CONFIGURED_EXERCISE_ASSIGN_SETTLEMENT_COSTS`
- FX: UNKNOWN
- Total close-before-expiry cost: 102.15 USD (`ESTIMATED_CONFIGURED_EXECUTION_MODEL`)

## Round trip

- Total estimated round-trip cost: 204.30 USD
- Round-trip cost / capital: 6.81%

## Risk / payoff

- Margin / buying power: UNKNOWN / UNKNOWN (`NOT_REQUIRED`)
- Capital at risk: 3,002.15 USD
- Maximum loss / profit: 3,002.15 USD / UNKNOWN
- Expiration breakevens: `[290.0215]`
- Lambda / delta-notional / gross-delta leverage: `5.337029` / `4.914173` / `4.914173`

## Time decay

- Net theta today: -8.58 USD per calendar day
- Theta / capital / day: -8.58 USD / -0.29% (`AVAILABLE`)
- Flat Spot Carry is produced by full repricing. Current theta is NOT multiplied by horizon.

| Horizon | Flat Spot Carry | Flat Spot Carry % capital | % maximum loss | Valuation time |
| ---: | ---: | ---: | ---: | --- |
| 0d | 0.00 USD | 0.00% | 0.00% | 2026-07-18T12:00:00+00:00 |
| 1d | -8.58 USD | -0.29% | -0.29% | 2026-07-19T12:00:00+00:00 |
| 7d | -60.50 USD | -2.02% | -2.02% | 2026-07-25T12:00:00+00:00 |
| 30d | -267.20 USD | -8.90% | -8.90% | 2026-08-17T12:00:00+00:00 |
| 60d | -558.93 USD | -18.62% | -18.62% | 2026-09-16T12:00:00+00:00 |
| 90d | -884.85 USD | -29.47% | -29.47% | 2026-10-16T12:00:00+00:00 |
| 181d | -2,764.29 USD | -92.08% | -92.08% | 2027-01-15T21:00:00+00:00 |
- Flat Spot 1d %: -0.29%
- Flat Spot 7d %: -2.02%
- Flat Spot 30d %: -8.90%
- Flat Spot 60d %: -18.62%
- Flat Spot 90d %: -29.47%
- Decay rate 0-7d: -8.64 USD per calendar day
- Decay rate 0-30d: -8.91 USD per calendar day
- Decay rate 30-60d: -9.72 USD per calendar day
- Decay rate 60-90d: -10.86 USD per calendar day
- Decay acceleration 30-60: -0.82 USD
- Decay acceleration 60-90: -1.14 USD
- Decay acceleration status: `ACCELERATING`

## Breakeven clock

- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `base_constant_leg_iv` at 0d: roots `[263.55867619]`, profitable `['[263.5587, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `base_constant_leg_iv` at 7d: roots `[264.56845752]`, profitable `['[264.5685, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `base_constant_leg_iv` at 30d: roots `[267.96922822]`, profitable `['[267.9692, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `base_constant_leg_iv` at 60d: roots `[272.60599209]`, profitable `['[272.6060, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `base_constant_leg_iv` at 90d: roots `[277.47867757]`, profitable `['[277.4787, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `EXPIRATION_BREAKEVEN` / `base_constant_leg_iv` at 182d: roots `[290.02149789]`, profitable `['[290.0215, ∞]']`, exit `HOLD_TO_EXPIRY`, applied exit cost `0.0000`, status `SOLVED` / `APPLIED_KNOWN_EXERCISE_ASSIGN_SETTLEMENT_COST`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_crush` at 0d: roots `[274.44804288]`, profitable `['[274.4480, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_crush` at 7d: roots `[275.13874094]`, profitable `['[275.1387, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_crush` at 30d: roots `[277.43526947]`, profitable `['[277.4353, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_crush` at 60d: roots `[280.48524623]`, profitable `['[280.4852, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_crush` at 90d: roots `[283.57000552]`, profitable `['[283.5700, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `EXPIRATION_BREAKEVEN` / `configured_iv_crush` at 182d: roots `[290.02149789]`, profitable `['[290.0215, ∞]']`, exit `HOLD_TO_EXPIRY`, applied exit cost `0.0000`, status `SOLVED` / `APPLIED_KNOWN_EXERCISE_ASSIGN_SETTLEMENT_COST`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_expansion` at 0d: roots `[251.2250821]`, profitable `['[251.2251, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_expansion` at 7d: roots `[252.53666976]`, profitable `['[252.5367, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_expansion` at 30d: roots `[256.99676624]`, profitable `['[256.9968, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_expansion` at 60d: roots `[263.19727639]`, profitable `['[263.1973, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `CLOSE_BEFORE_EXPIRY_BREAKEVEN` / `configured_iv_expansion` at 90d: roots `[269.89543636]`, profitable `['[269.8954, ∞]']`, exit `CLOSE_BEFORE_EXPIRY`, applied exit cost `102.1500`, status `SOLVED` / `ESTIMATED_CONFIGURED_EXECUTION_MODEL`.
- `EXPIRATION_BREAKEVEN` / `configured_iv_expansion` at 182d: roots `[290.02149789]`, profitable `['[290.0215, ∞]']`, exit `HOLD_TO_EXPIRY`, applied exit cost `0.0000`, status `SOLVED` / `APPLIED_KNOWN_EXERCISE_ASSIGN_SETTLEMENT_COST`.

## Target timing

- Target 210.0000, `base_constant_leg_iv`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`.
- Target 260.0000, `base_constant_leg_iv`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`.
- Target 330.0000, `base_constant_leg_iv`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`.
- Target 210.0000, `configured_iv_crush`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`.
- Target 260.0000, `configured_iv_crush`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`.
- Target 330.0000, `configured_iv_crush`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`.
- Target 210.0000, `configured_iv_expansion`: `NEVER_BREAKEVEN_AT_THIS_TARGET`, latest `none`.
- Target 260.0000, `configured_iv_expansion`: `LATEST_PROFITABLE_ARRIVAL`, latest `2026-08-31T12:00:00+00:00`.
- Target 330.0000, `configured_iv_expansion`: `PROFITABLE_THROUGH_EXPIRY`, latest `2027-01-15T21:00:00+00:00`.

## Spot × time × volatility scenarios

**base_constant_leg_iv** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Requested | Effective | Position value | Gross PnL | Exit path | Exit cost | Net PnL | Return | Status |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 180.4530 | 7d | 7.000d | 201.7212 | -2698.2788 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2902.5788 | -96.68% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 7d | 7.000d | 721.2577 | -2178.7423 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2383.0423 | -79.38% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 7d | 7.000d | 983.2961 | -1916.7039 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2121.0039 | -70.65% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 7d | 7.000d | 2703.7883 | -196.2117 | CLOSE_BEFORE_EXPIRY | 102.1500 | -400.5117 | -13.34% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 7d | 7.000d | 2831.3352 | -68.6648 | CLOSE_BEFORE_EXPIRY | 102.1500 | -272.9648 | -9.09% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 7d | 7.000d | 5321.8021 | 2421.8021 | CLOSE_BEFORE_EXPIRY | 102.1500 | 2217.5021 | 73.86% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 7d | 7.000d | 8105.0981 | 5205.0981 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5000.7981 | 166.57% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 7d | 7.000d | 8559.2631 | 5659.2631 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5454.9631 | 181.70% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 30d | 30.000d | 146.0469 | -2753.9531 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2958.2531 | -98.54% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 30d | 30.000d | 595.8361 | -2304.1639 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2508.4639 | -83.56% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 30d | 30.000d | 836.2370 | -2063.7630 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2268.0630 | -75.55% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 30d | 30.000d | 2497.0839 | -402.9161 | CLOSE_BEFORE_EXPIRY | 102.1500 | -607.2161 | -20.23% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 30d | 30.000d | 2623.2693 | -276.7307 | CLOSE_BEFORE_EXPIRY | 102.1500 | -481.0307 | -16.02% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 30d | 30.000d | 5119.5458 | 2219.5458 | CLOSE_BEFORE_EXPIRY | 102.1500 | 2015.2458 | 67.13% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 30d | 30.000d | 7935.4373 | 5035.4373 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4831.1373 | 160.92% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 30d | 30.000d | 8395.1935 | 5495.1935 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5290.8935 | 176.24% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 60d | 60.000d | 83.2513 | -2816.7487 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3021.0487 | -100.63% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 60d | 60.000d | 431.9223 | -2468.0777 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2672.3777 | -89.02% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 60d | 60.000d | 638.6857 | -2261.3143 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2465.6143 | -82.13% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 60d | 60.000d | 2205.3549 | -694.6451 | CLOSE_BEFORE_EXPIRY | 102.1500 | -898.9451 | -29.94% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 60d | 60.000d | 2329.5597 | -570.4403 | CLOSE_BEFORE_EXPIRY | 102.1500 | -774.7403 | -25.81% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 60d | 60.000d | 4840.7414 | 1940.7414 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1736.4414 | 57.84% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 60d | 60.000d | 7712.3396 | 4812.3396 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4608.0396 | 153.49% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 60d | 60.000d | 8181.0860 | 5281.0860 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5076.7860 | 169.11% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 90d | 90.000d | 35.6444 | -2864.3556 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3068.6556 | -102.22% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 90d | 90.000d | 271.6607 | -2628.3393 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2832.6393 | -94.35% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 90d | 90.000d | 436.0762 | -2463.9238 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2668.2238 | -88.88% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 90d | 90.000d | 1879.4353 | -1020.5647 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1224.8647 | -40.80% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 90d | 90.000d | 2001.3247 | -898.6753 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1102.9753 | -36.74% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 90d | 90.000d | 4541.9584 | 1641.9584 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1437.6584 | 47.89% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 90d | 90.000d | 7491.5313 | 4591.5313 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4387.2313 | 146.14% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 90d | 90.000d | 7971.7336 | 5071.7336 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4867.4336 | 162.13% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 182d | 181.375d | 3645.8500 | 745.8500 | HOLD_TO_EXPIRY | 0.0000 | 643.7000 | 21.44% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 182d | 181.375d | 7000.0000 | 4100.0000 | HOLD_TO_EXPIRY | 0.0000 | 3997.8500 | 133.17% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 182d | 181.375d | 7512.7000 | 4612.7000 | HOLD_TO_EXPIRY | 0.0000 | 4510.5500 | 150.24% | LEG_LEVEL_STRESS_ONLY |

**configured_iv_crush** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Requested | Effective | Position value | Gross PnL | Exit path | Exit cost | Net PnL | Return | Status |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 180.4530 | 7d | 7.000d | 40.8894 | -2859.1106 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3063.4106 | -102.04% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 7d | 7.000d | 301.2676 | -2598.7324 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2803.0324 | -93.37% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 7d | 7.000d | 479.3017 | -2420.6983 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2624.9983 | -87.44% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 7d | 7.000d | 2003.1358 | -896.8642 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1101.1642 | -36.68% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 7d | 7.000d | 2129.9847 | -770.0153 | CLOSE_BEFORE_EXPIRY | 102.1500 | -974.3153 | -32.45% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 7d | 7.000d | 4741.1979 | 1841.1979 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1636.8979 | 54.52% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 7d | 7.000d | 7728.3448 | 4828.3448 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4624.0448 | 154.02% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 7d | 7.000d | 8212.1651 | 5312.1651 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5107.8651 | 170.14% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 30d | 30.000d | 25.0648 | -2874.9352 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3079.2352 | -102.57% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 30d | 30.000d | 232.4311 | -2667.5689 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2871.8689 | -95.66% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 30d | 30.000d | 388.1304 | -2511.8696 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2716.1696 | -90.47% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 30d | 30.000d | 1842.6095 | -1057.3905 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1261.6905 | -42.03% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 30d | 30.000d | 1968.0615 | -931.9385 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1136.2385 | -37.85% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 30d | 30.000d | 4592.7061 | 1692.7061 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1488.4061 | 49.58% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 30d | 30.000d | 7615.1262 | 4715.1262 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4510.8262 | 150.25% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 30d | 30.000d | 8103.6747 | 5203.6747 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4999.3747 | 166.53% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 60d | 60.000d | 10.5283 | -2889.4717 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3093.7717 | -103.05% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 60d | 60.000d | 148.9886 | -2751.0114 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2955.3114 | -98.44% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 60d | 60.000d | 271.6729 | -2628.3271 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2832.6271 | -94.35% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 60d | 60.000d | 1617.4605 | -1282.5395 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1486.8395 | -49.53% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 60d | 60.000d | 1740.8694 | -1159.1306 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1363.4306 | -45.42% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 60d | 60.000d | 4392.5066 | 1492.5066 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1288.2066 | 42.91% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 60d | 60.000d | 7470.9666 | 4570.9666 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4366.6666 | 145.45% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 60d | 60.000d | 7966.3191 | 5066.3191 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4862.0191 | 161.95% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 90d | 90.000d | 2.7542 | -2897.2458 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3101.5458 | -103.31% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 90d | 90.000d | 77.1754 | -2822.8246 | CLOSE_BEFORE_EXPIRY | 102.1500 | -3027.1246 | -100.83% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 90d | 90.000d | 161.9285 | -2738.0715 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2942.3715 | -98.01% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 90d | 90.000d | 1367.9160 | -1532.0840 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1736.3840 | -57.84% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 90d | 90.000d | 1488.9150 | -1411.0850 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1615.3850 | -53.81% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 90d | 90.000d | 4185.4705 | 1285.4705 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1081.1705 | 36.01% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 90d | 90.000d | 7334.2055 | 4434.2055 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4229.9055 | 140.90% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 90d | 90.000d | 7836.8011 | 4936.8011 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4732.5011 | 157.64% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 182d | 181.375d | 3645.8500 | 745.8500 | HOLD_TO_EXPIRY | 0.0000 | 643.7000 | 21.44% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 182d | 181.375d | 7000.0000 | 4100.0000 | HOLD_TO_EXPIRY | 0.0000 | 3997.8500 | 133.17% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 182d | 181.375d | 7512.7000 | 4612.7000 | HOLD_TO_EXPIRY | 0.0000 | 4510.5500 | 150.24% | LEG_LEVEL_STRESS_ONLY |

**configured_iv_expansion** — `LEG_LEVEL_STRESS_ONLY`

| Spot | Requested | Effective | Position value | Gross PnL | Exit path | Exit cost | Net PnL | Return | Status |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 180.4530 | 7d | 7.000d | 479.6873 | -2420.3127 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2624.6127 | -87.42% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 7d | 7.000d | 1220.7158 | -1679.2842 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1883.5842 | -62.74% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 7d | 7.000d | 1542.5322 | -1357.4678 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1561.7678 | -52.02% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 7d | 7.000d | 3402.0867 | 502.0867 | CLOSE_BEFORE_EXPIRY | 102.1500 | 297.7867 | 9.92% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 7d | 7.000d | 3531.3294 | 631.3294 | CLOSE_BEFORE_EXPIRY | 102.1500 | 427.0294 | 14.22% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 7d | 7.000d | 5968.8857 | 3068.8857 | CLOSE_BEFORE_EXPIRY | 102.1500 | 2864.5857 | 95.42% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 7d | 7.000d | 8622.1158 | 5722.1158 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5517.8158 | 183.80% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 7d | 7.000d | 9054.0387 | 6154.0387 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5949.7387 | 198.18% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 30d | 30.000d | 374.8883 | -2525.1117 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2729.4117 | -90.92% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 30d | 30.000d | 1042.5560 | -1857.4440 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2061.7440 | -68.68% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 30d | 30.000d | 1344.3181 | -1555.6819 | CLOSE_BEFORE_EXPIRY | 102.1500 | -1759.9819 | -58.62% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 30d | 30.000d | 3149.5650 | 249.5650 | CLOSE_BEFORE_EXPIRY | 102.1500 | 45.2650 | 1.51% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 30d | 30.000d | 3277.3806 | 377.3806 | CLOSE_BEFORE_EXPIRY | 102.1500 | 173.0806 | 5.77% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 30d | 30.000d | 5714.2792 | 2814.2792 | CLOSE_BEFORE_EXPIRY | 102.1500 | 2609.9792 | 86.94% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 30d | 30.000d | 8393.0199 | 5493.0199 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5288.7199 | 176.16% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 30d | 30.000d | 8829.9585 | 5929.9585 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5725.6585 | 190.72% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 60d | 60.000d | 245.5816 | -2654.4184 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2858.7184 | -95.22% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 60d | 60.000d | 801.8037 | -2098.1963 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2302.4963 | -76.69% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 60d | 60.000d | 1071.8762 | -1828.1238 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2032.4238 | -67.70% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 60d | 60.000d | 2791.7174 | -108.2826 | CLOSE_BEFORE_EXPIRY | 102.1500 | -312.5826 | -10.41% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 60d | 60.000d | 2917.4645 | 17.4645 | CLOSE_BEFORE_EXPIRY | 102.1500 | -186.8355 | -6.22% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 60d | 60.000d | 5358.9348 | 2458.9348 | CLOSE_BEFORE_EXPIRY | 102.1500 | 2254.6348 | 75.10% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 60d | 60.000d | 8083.8295 | 5183.8295 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4979.5295 | 165.87% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 60d | 60.000d | 8529.3494 | 5629.3494 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5425.0494 | 180.71% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 90d | 90.000d | 131.3200 | -2768.6800 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2972.9800 | -99.03% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 90d | 90.000d | 552.8113 | -2347.1887 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2551.4887 | -84.99% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 90d | 90.000d | 781.6873 | -2118.3127 | CLOSE_BEFORE_EXPIRY | 102.1500 | -2322.6127 | -77.36% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 90d | 90.000d | 2389.8803 | -510.1197 | CLOSE_BEFORE_EXPIRY | 102.1500 | -714.4197 | -23.80% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 90d | 90.000d | 2513.2241 | -386.7759 | CLOSE_BEFORE_EXPIRY | 102.1500 | -591.0759 | -19.69% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 90d | 90.000d | 4970.5189 | 2070.5189 | CLOSE_BEFORE_EXPIRY | 102.1500 | 1866.2189 | 62.16% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 90d | 90.000d | 7764.8911 | 4864.8911 | CLOSE_BEFORE_EXPIRY | 102.1500 | 4660.5911 | 155.24% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 90d | 90.000d | 8222.4014 | 5322.4014 | CLOSE_BEFORE_EXPIRY | 102.1500 | 5118.1014 | 170.48% | LEG_LEVEL_STRESS_ONLY |
| 180.4530 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 210.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 219.1215 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 257.7900 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 260.0000 | 182d | 181.375d | 0.0000 | -2900.0000 | HOLD_TO_EXPIRY | 0.0000 | -3002.1500 | -100.00% | LEG_LEVEL_STRESS_ONLY |
| 296.4585 | 182d | 181.375d | 3645.8500 | 745.8500 | HOLD_TO_EXPIRY | 0.0000 | 643.7000 | 21.44% | LEG_LEVEL_STRESS_ONLY |
| 330.0000 | 182d | 181.375d | 7000.0000 | 4100.0000 | HOLD_TO_EXPIRY | 0.0000 | 3997.8500 | 133.17% | LEG_LEVEL_STRESS_ONLY |
| 335.1270 | 182d | 181.375d | 7512.7000 | 4612.7000 | HOLD_TO_EXPIRY | 0.0000 | 4510.5500 | 150.24% | LEG_LEVEL_STRESS_ONLY |

## Statistics

- Expected PnL: `N/A`
- Median PnL: `N/A`
- Reason: `PROBABILITY_MODEL_NOT_AVAILABLE`
- Model: `N/A`
- Calibration status: `PROBABILITY_MODEL_NOT_AVAILABLE`

## Decision scores

- Scope: `RUN_GLOBAL`; source: `ttwo-five-scores-v2`; source candidate: `engine_candidate`.
- Opportunity: `37.0707 / 100`; coverage `100.00%`; confidence `LOW`; version `pre-opra-v2`; status `RUN_GLOBAL_CONTEXT`; missing `[]`.
- Risk: `49.4667 / 100`; coverage `100.00%`; confidence `LOW`; version `pre-opra-v2`; status `RUN_GLOBAL_CONTEXT`; missing `[]`.
- Evidence: `40.3298 / 100`; coverage `80.00%`; confidence `LOW`; version `pre-opra-v2`; status `RUN_GLOBAL_CONTEXT`; missing `['holdout_validation', 'rights_confirmation']`.
- Model Agreement: `31.4614 / 100`; coverage `50.00%`; confidence `VERY_LOW`; version `pre-opra-v2`; status `RUN_GLOBAL_CONTEXT`; missing `['option_expected_return_agreement', 'candidate_ranking_agreement']`.
- Execution Quality: `50.4918 / 100`; coverage `75.00%`; confidence `LOW`; version `pre-opra-v2`; status `RUN_GLOBAL_CONTEXT`; missing `['live_execution_component']`.

## Attribution

- `base_constant_leg_iv_30d` full repricing PnL -471.5037; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-267.2037/0.0000/0.0000/0.0000/-204.3000/0.0000/0.00000000; Taylor residual -9.8212.
- `configured_iv_crush_30d` full repricing PnL -1125.9782; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-237.4342/-684.2440/0.0000/0.0000/-204.3000/0.0000/0.00000000; Taylor residual 49.9739.
- `configured_iv_expansion_30d` full repricing PnL 180.9773; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-296.7374/682.0147/0.0000/0.0000/-204.3000/0.0000/-0.00000000; Taylor residual -69.0942.
- `base_constant_leg_iv_parallel_up_30d` full repricing PnL -421.4378; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-272.0726/0.0000/54.9348/0.0000/-204.3000/0.0000/0.00000000; Taylor residual -19.2162.
- `base_constant_leg_iv_parallel_down_30d` full repricing PnL -521.0250; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-262.4059/0.0000/-54.3192/0.0000/-204.3000/0.0000/0.00000000; Taylor residual 0.1185.
- `base_constant_leg_iv_steepening_30d` full repricing PnL -491.5812; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-266.6438/0.0000/-20.6374/0.0000/-204.3000/0.0000/0.00000000; Taylor residual -8.6576.
- `base_constant_leg_iv_flattening_30d` full repricing PnL -451.3372; spot/time/vol/rates/FX/costs/other/residual = 0.0000/-267.7629/0.0000/20.7257/0.0000/-204.3000/0.0000/0.00000000; Taylor residual -10.8957.

## Event

- No event-date scenario is present in this ticket.

## Liquidity / execution

- `TTWO  270115C00260000` bid/ask/mid `28.0000/30.0000/29.0000`; sizes `24/22`; volume/OI `210/1840`; quote age `0.00s`; model `legacy_weighted_heuristic_v1` (`UNCALIBRATED`).

## Exercise / contract risk

- TTWO  270115C00260000: assignment=low; early_exercise=low; pin=low; adjusted_contract=False; human_review=False

## Classification and safety

- Warning: QuantLib American model values are indicative and not executable quotes
- Warning: Full repricing is primary; Greek/Taylor attribution is explanatory only.
- Warning: All leg-level execution estimates are indicative until combo evidence exists.
- FX mode/status/contribution: `UNKNOWN` / `BLOCKED_UNKNOWN_FX_HANDLING` / `UNKNOWN`
- Intensity: `MODERATE`
- Data status: `AVAILABLE_RESEARCH_ONLY`
- Probability status: `PROBABILITY_MODEL_NOT_AVAILABLE`
- Full repricing is the primary financial value; Taylor/Greek output is explanatory.
- Safety: read_only=`true`, transmit=`false`, what_if=`true`, order_capability=`forbidden`.
