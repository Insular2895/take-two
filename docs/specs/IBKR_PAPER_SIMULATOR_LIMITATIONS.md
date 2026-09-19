# IBKR Paper simulator limitations

## Correct interpretation

IBKR Paper is an account simulator, not exchange validation. Every execution from it must carry:

```text
execution_environment = IBKR_PAPER_SIMULATOR
fill_evidence          = PAPER_SIMULATED_FILL
```

It must never be displayed as `EXCHANGE_VALIDATED_FILL`.

IBKR currently documents that Paper fills are simulated from the top of book, deep book is not
simulated, combo trading and order types are limited, and penny trading for US options is not
supported in Paper. Consequently a valid working Paper order that does not fill is not proof that
the real market has no liquidity. `PAPER_SIMULATOR_LIMITATION_POSSIBLE` is a permissible bounded
diagnostic; `NO_REAL_MARKET_LIQUIDITY` is not.

Official reference: [IBKR Paper Trading Account limitations](https://ibkrcampus.com/campus/glossary-terms/paper-trading-account/).

## Three independent results

| Result | Pass criterion |
|---|---|
| System execution path | Correct command, broker receipt evidence, callbacks, no duplicate, reconciled state, frozen economics. |
| Paper simulator fill | IBKR Paper emitted an execution callback and simulated fill. |
| Live executability | `NOT_PROVEN_BY_PAPER_ALONE`. |

A simulator-specific no-fill can fail the second result without failing the first.

## Tick policy

The application validates the real contract/BAG market rule using current PriceIncrement bands.
It does not hard-code a fake Paper penny/nickel rule. For the first plumbing test, the operator
chooses a displayed valid BAG price; a penny-improvement fill is not an acceptance criterion.

## No-fill labels

Evidence-backed labels include `WORKING_BELOW_MARKET`, `WORKING_INSIDE_SPREAD`,
`WORKING_AT_MARKET_EDGE`, `OBSERVED_MARKETABLE_BUT_NOT_FILLED`, `QUOTE_MOVED_AWAY`,
`MARKET_DATA_STALE`, `BROKER_HELD`, `PAPER_SIMULATOR_LIMITATION_POSSIBLE` and
`UNKNOWN_NO_FILL_REASON`. “Nobody accepted the order” is not an evidence-backed statement.

## Facts that still require Paper observation

Exact combo simulator increments, signed BAG price behavior, fill behavior, supported what-if,
precautions, commissions, margin and reconnect/session behavior are all `NOT_PROVEN_OFFLINE`.

