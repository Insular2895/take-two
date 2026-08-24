# Changelog

## 0.12.0 — 2026-08-24

### M0 Greeks, Carry & Trade Economics hardening

- Added versioned strict models for advanced Greeks, numerical confidence, carry, volatility
  stresses, breakeven clocks, touch probability, costs, margin, FX, attribution, intensity and the
  `TradeEconomicsTicket`.
- Added same-full-pricer Vanna, Vomma, Charm, Veta, Speed and Color with configurable multi-bump and
  grid-refinement diagnostics plus European analytic benchmarks.
- Added full-repriced flat-spot carry, Spot × Time × IV matrices, generic multi-root breakevens,
  target-arrival timing and factor-order-invariant Shapley attribution.
- Split entry, estimated exit and round-trip economics; eliminated false-zero execution and margin
  fallbacks; retained indicative per-leg combo status.
- Added explicit dividend-treatment guards, rate-curve metadata, exact DTE and date-engine
  intraday precision statuses.
- Extended future read-only OPRA contracts with optional contract identity, adjustment and provider
  Greek metadata without connecting a provider.
- Added the versioned configuration section, JSON Schema, renderer, synthetic golden reports,
  numerical/property tests, implementation specification and 2026 source audit.
- Preserved `transmit=false`, `what_if=true`, `order_capability=forbidden`; final holdout untouched.
