# Final holdout ledger status

Status on 2026-08-08: `not_created_no_dataset`.

The hash-chained ledger contract is implemented in
`src/take_two_options/validation/experiment_protocol.py`. No ledger entry is committed because
there is no authorized final-holdout dataset or dataset SHA-256. Creating a `seal` or `evaluate`
entry now would fabricate an access event. V7–V9 remain contaminated and ineligible.
