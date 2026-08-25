# Changelog

## 0.12.7 — 2026-08-25

### Cloud comparison clarity and maximum-gain currency correction

- Replaced the cramped two-column comparison cards with a wide, aligned comparison table for two
  to four candidates, including structure, legs, expiry, risk, budget, model availability and
  five-score availability.
- Enlarged the close target, strengthened its focus/contrast, retained native dialog/Escape
  behavior, and added responsive horizontal comparison with a sticky metric column.
- Replaced ambiguous research `N/A` labels with `NON CALCULÉ` plus explicit reasons, while showing
  `NON BORNÉ` for architectures whose theoretical upside has no finite cap.
- Clarified signed entry cash flow and the distinction between entry debit, maximum loss, and the
  effective capital requirement.
- Corrected bounded maximum gain from native USD into policy EUR, with a read-only compatibility
  conversion for summaries produced by the original deployed CF0.2 revision.
- Preserved synthetic-only data, null model outputs, immutable native economics tickets,
  `transmit=false`, and `order_capability=forbidden`.

## 0.12.6 — 2026-08-24

### Phase M governed context propagation

- Added one immutable, serializable `PhaseMDecisionContext` combining the canonical prospective
  policy with optional point-in-time FX, FX-cost, and broker-capital evidence plus deterministic
  config/context hashes and explicit provenance.
- Propagated that context through `analyze_trade`, candidate enumeration/factory, deep
  trade-economics tickets, decision reports, and optional Cloud position dossier identifiers while
  preserving the context-free legacy path.
- Removed Phase M lifecycle/FX fallback behavior, retained explicit unknown FX cost and broker
  capital semantics, and made the prospective lifecycle field required.
- Added a provider-free `trade phase-m-context` CLI, a generated context schema, end-to-end context
  tests, and pre/post implementation audits without changing historical artifacts or five scores.
- Preserved `HOLDOUT=UNOPENED`, `OPRA=NOT_STARTED`, `transmit=false`, `what_if=true`, and
  `order_capability=forbidden`.

## 0.12.5 — 2026-08-24

### Sensitive-action password

- Kept Cloudflare Access as the only login while adding a separate action password for imports,
  SAFE MODE, monitoring changes, close acknowledgement, manual-close reporting, and fill
  reconciliation.
- Stored only a keyed HMAC-SHA-256 verifier as a Cloudflare Worker secret, never the plaintext
  password, and added a masked setup/rotation command for remote and ignored local configuration.
- Added per-Access-identity D1 throttling at five failures per 15 minutes, secret-free audit events,
  a reusable password dialog, negative integration coverage, and retained the strict no-order
  boundary.

## 0.12.4 — 2026-08-24

### Cloudflare Access production authentication

- Replaced the incompatible Worker PBKDF2 login with Worker-level Cloudflare Access for all traffic;
  the application now fails closed unless a direct verified `ctx.access` identity contains an email.
- Bundled the private HTML, CSS, and JavaScript as Worker text modules so the Static Assets router
  cannot hide the Access context from application code.
- Retained mutation CSRF with a 256-bit `__Host-` cookie and changed sensitive close-preview
  reauthentication to require a Cloudflare Access login timestamp no older than five minutes.
- Removed application password endpoints, secrets, UI, and tooling; Access logout and identity-aware
  audit actors now replace the legacy D1 session flow without adding order capability.

## 0.12.3 — 2026-08-24

### M0.2.1 final budget semantics cleanup

- Made the explicit account liquidity reserve economically active through known available capital,
  deployable capital, an effective hard ceiling, AUTO caps, diagnostics, config, and CLI inputs.
- Replaced the candidate factory's one-day mixed-expiry literal with one injected typed lifecycle
  configuration shared through ticket, scenario, breakeven, and target-arrival validation.
- Separated point-in-time FX rate from evidenced FX execution cost, supporting fixed/bps values and
  fail-closed unknown-cost paper eligibility without inventing a zero.
- Kept V2 at 2.0 and ticket schema at 1.2 through optional compatible fields; preserved historical
  hashes, five scores, unopened holdout, `OPRA=NOT_STARTED`, and the no-order boundary.

## 0.12.2 — 2026-08-24

### M0.2 flexible budget configurator and capital safety

- Added separate `BudgetPolicyV1Legacy` and `FlexibleBudgetPolicyV2` contracts with asymmetric
  target tolerances, SOFT/HARD/OFF lower policy, explicit/AUTO loss and buying-power caps, and no
  hidden V2 reserve.
- Centralized entry-cash, maximum-loss, buying-power and point-in-time FX gates in
  `evaluate_budget_policy`; credit cash is floored at zero and unknown capital remains null.
- Added per-quantity V2 diagnostics to whole-contract generation without changing the five scores.
- Removed common-expiry terminal payoff from V2 calendar/diagonal authorization and added the
  research-only `LifecycleCapitalRequirement` fail-closed path.
- Versioned the trade-economics ticket to 1.2 while retaining 1.0/1.1 readers, added the Budget
  renderer, prospective Phase M config/CLI, schemas, reports, and regression coverage.
- Preserved historical/OOS artifacts, the unopened holdout, `OPRA=NOT_STARTED`, and the no-order
  boundary.

## 0.12.1 — 2026-08-24

### M0.1 final pre-OPRA trade economics corrections

- Split theoretical midpoint premiums from executable ask-paid/bid-received premiums while
  preserving readable ticket 1.0 compatibility fields and exact signed cost reconciliation.
- Added explicit close, hold-to-expiry, exercise/assignment/settlement and mixed-expiry managed
  exit paths; expiration no longer receives fictitious option-closing costs.
- Expanded the Markdown ticket with complete carry/decay economics, net PnL distribution metrics,
  canonical five-score snapshots, event timing and applied exit costs.
- Enforced real-world path-state requirements for expected PnL, event-date-aware IV crush, and the
  configurable `CLOSE_BEFORE_FIRST_EXPIRY` lifecycle policy.
- Regenerated schema 1.1 golden/probability fixtures without opening the holdout, connecting OPRA,
  or adding any order capability.

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
