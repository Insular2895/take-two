# Phase M-CF0.2.1 — Comparison clarity and payoff semantics

Date: 2026-08-25
Status: implemented, pending production visual confirmation

## User-visible problem

The production screenshots showed a 680 px comparison dialog trying to fit two candidate cards.
The close control blended into the edge, long budget labels overflowed, candidate legs were absent,
and several unrelated meanings were collapsed into the same `N/A` label.

The audit is scoped to the user-provided screenshots and the bundled HTML/CSS/JavaScript. A live
post-change browser capture was unavailable in the implementation environment, so production
visual confirmation remains explicit rather than inferred from tests.

## Verified semantics

- Signed entry cash flow is from the account perspective. A negative `DEBIT` is cash paid to open;
  a positive `CREDIT` is cash received.
- For a common-expiry bounded debit structure, maximum loss can equal the entry outlay. The effective
  capital requirement is nevertheless computed independently as the maximum of known entry cash,
  maximum loss, buying power, and lifecycle requirements. Small displayed differences can come from
  policy-currency FX execution cost and rounding.
- A long call's finite maximum-gain value is not missing: its theoretical upside is unbounded. The
  Options Industry Council describes maximum loss as premium paid and maximum gain as unlimited:
  https://www.optionseducation.org/strategies/all-strategies/long-call
- A bull call spread has a bounded maximum gain equal to strike width less net premium paid, and a
  maximum loss equal to the net premium paid:
  https://www.optionseducation.org/strategies/all-strategies/bull-call-spread-debit-call-spread
- Expected P&L, probability of profit, CVaR, theta paths and five scores are intentionally null in
  this exhaustive summary job because no valid probability/repricing model or historical score
  formula is run. Null remains distinct from zero.

## Correction found during audit

Bounded `maximum_gain` was calculated in native USD by the candidate factory but passed unchanged
into an EUR summary. The UI therefore showed a dollar amount with an euro symbol. New summaries now
convert the bounded gain with the governed point-in-time FX rate, while the immutable ticket keeps
its explicitly named `maximum_gain_native` value. A commit-scoped, read-only compatibility
conversion corrects API presentation for the original deployed revision without rewriting its D1
history or native ticket.

## UI result

- wide comparison dialog up to 1280 px;
- visible 44 × 44 close target with keyboard focus ring;
- one table column per candidate and one aligned row per metric;
- strategy, engine rank, legs, expiry and DTE retained in every header;
- explanations beside entry flow, capital, loss, gain, budget and model metrics;
- `NON BORNÉ` distinguished from `NON CALCULÉ`;
- responsive horizontal scroll with a sticky metric column;
- main cards also replace ambiguous candidate `N/A` values and clarify entry cash flow.

## Safety and limits

This change does not run a probability model, reprice options in the browser, validate a live combo
fill, open OPRA, connect IBKR, or add order capability. It improves truthful presentation and fixes
one currency projection. Synthetic results remain illustrative research, not financial advice.
