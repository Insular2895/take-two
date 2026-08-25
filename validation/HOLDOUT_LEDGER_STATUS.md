# Final holdout ledger status

Status on 2026-08-08: `UNOPENED` and unprovisioned.

The persistent hash-chained state machine is implemented in
`src/take_two_options/validation/final_holdout.py`. The committed first line is only an
`initialize` event: it records no dataset hash and performs no content access. A future authorized
dataset must first be provisioned with an immutable hash. The only opening transition is
`UNOPENED → OPENED_ONCE`, exactly once. `CONTAMINATED` and `INVALID` are terminal, and tuning is
not an allowed ledger event. V7–V9 remain contaminated and ineligible.
