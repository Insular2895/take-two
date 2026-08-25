# Current testing strategy

The repository uses a fail-closed evidence ladder. A passing unit test proves only the tested
contract; it does not imply numerical, empirical, holdout, paper, or production validity.

## Test layers

1. Unit and schema tests: validation bounds, provenance, `NO_TRADE`, deterministic helpers.
2. Property tests: payoff identities, put-call parity, cross-pricer cases, chronological and
   measure invariants.
3. Numerical tests: absolute plus relative tolerances, synthetic recovery, grid refinement,
   multiple seeds/starts where relevant.
4. Integration and golden tests: fixture-only pipelines and backward-compatible reports.
5. Offline artifact checks: schema exports and self-contained report validation.
6. Safety checks: forbidden broker imports/order symbols, `transmit=True`, unsafe writes, and
   read-only connector behaviour.
7. Empirical gates: point-in-time split, purge/embargo, baselines, placebo, multiple-testing,
   and a separately sealed holdout. These remain blocked without authorized real data.

## Mandatory phase gate

Before each phase commit run its targeted tests, then the full suite, Ruff, mypy, dependency
check, offline schema/artifact checks, and security gate. Stop before the next phase on any
failure. Record synthetic evidence as synthetic and never promote a result past its evidence.

Canonical commands are listed in the Phase 0–11 implementation plan under Phase 10.
