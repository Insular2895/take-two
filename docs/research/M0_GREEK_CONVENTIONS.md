# M0 Greek conventions

Version: `1.0`
Internal time basis: Actual/365 Fixed and calendar-day drift
Pricing measure: `Q`; probability forecasts: `P` only

## Canonical units

| Greek | Internal definition | Published unit |
| --- | --- | --- |
| Delta | `dV/dS` | currency per one spot unit |
| Gamma | `d²V/dS²` | delta per one spot unit |
| Theta | `V(t+1 calendar day)-V(t)` | currency per calendar day |
| Vega | `dV/dsigma × 0.01` | currency per +1 volatility point |
| Rho | `dV/dr × 0.01` | currency per +1 percentage-point rate move |
| Vanna | `d²V/(dS dsigma) × 0.01` | currency per spot unit per volatility point |
| Vomma | `d²V/dsigma² × 0.01²` | currency per volatility-point squared |
| Charm | `Delta(t+1 day)-Delta(t)` | delta drift per calendar day |
| Veta | `Vega(t+1 day)-Vega(t)` | vega drift per calendar day |
| Speed | `dGamma/dS` | gamma per spot unit |
| Color | `Gamma(t+1 day)-Gamma(t)` | gamma drift per calendar day |

Charm, Veta and Color are deliberately published as forward one-calendar-day drifts. Literature
often defines derivatives with respect to time-to-expiry, whose sign can be the opposite. The field
names include `*_drift_1_calendar_day` to prevent silent convention substitution.

## Finite differences

With spot bump `h`, volatility bump `k` in sigma decimals, rate bump `u` in decimals, and one-day
time step `d`:

```text
Delta  = [V(S+h)-V(S-h)] / (2h)
Gamma  = [V(S+h)-2V(S)+V(S-h)] / h²
Vega   = [V(sigma+k)-V(sigma-k)] / (2k) × 0.01
Rho    = [V(r+u)-V(r-u)] / (2u) × 0.01
Vanna  = [V(S+h,sigma+k)-V(S+h,sigma-k)
          -V(S-h,sigma+k)+V(S-h,sigma-k)] / (4hk) × 0.01
Vomma  = [V(sigma+k)-2V(sigma)+V(sigma-k)] / k² × 0.01²
Charm  = Delta(t+d)-Delta(t)
Veta   = Vega(t+d)-Vega(t)
Speed  = [Gamma(S+h)-Gamma(S-h)] / (2h)
Color  = Gamma(t+d)-Gamma(t)
```

The primary run and alternate runs use the same selected full pricer. Spot, volatility, rate and
grid refinements are configuration values. Near expiry, time is clipped at expiration.

## Sign and aggregation

Per-leg Greeks describe a long instrument before position scaling. Position aggregation is:

```text
Greek_position = sum_i side_i × quantity_i × multiplier_i × Greek_leg_i
```

`side=long` is `+1`; `side=short` is `-1`. Stock contributes signed quantity to Delta. No
multiplier is assumed to be 100: the contract value is mandatory. Raw provider values remain
separate from normalized internal values and carry provider convention metadata when supplied.

The expected economic signs are diagnostics, not hard constraints: a long vanilla option usually
has positive Gamma and Vega and negative Theta, while local signs of higher-order Greeks vary with
moneyness, time, rates and IV.

## Numerical confidence

For estimates `g_j` from alternate bumps/grids:

```text
dispersion = max(g_j) - min(g_j)
relative_dispersion = |dispersion| / max(|g_primary|, configured_floor)
```

Configured thresholds map dispersion to `HIGH`, `MEDIUM`, `LOW` or `UNRELIABLE`. A low-magnitude
higher-order Greek can therefore be downgraded even when the option price itself is stable. For
compatible European contracts, Delta/Gamma/Theta/Vega/Rho and analytic Vanna/Vomma are benchmarked
against Black–Scholes–Merton formulas. Benchmark difference is diagnostic and does not override
same-pricer output.

## Literature and repository lineage

- `R-GREEKS-001`: aggregate the whole position with quantity and contract multiplier.
- `R-GREEKS-002`: Greeks and delta neutrality are local states that must be recalculated.
- `R-GREEKS-003`: gamma benefits must be evaluated net of theta and execution costs.
- `R-GREEKS-004`: preserve raw sign/unit conventions before normalization.
- `B-NATENBERG-1994` and `B-PASSARELLI-2012`: qualitative/economic sensitivity lineage.
- `B-HULL-2021`: pricing, Greeks, dividends, rates and numerical-model foundations; its local
  extraction journal is incomplete, so it is supporting BOOK context rather than a new validated
  rule.

## Interpretation limits

- Greeks are local model derivatives, not realized PnL forecasts.
- Full repricing governs scenarios and breakevens.
- Confidence labels measure numerical stability only.
- Date-based American FD values are not exact intraday Greeks.
- A provider Greek cannot be aggregated until unit, sign, model, currency, multiplier, timestamp
  and contract adjustment status are known.
