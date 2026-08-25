# Manual IBKR whole-structure close

CF0 does not connect to TWS or IB Gateway and cannot transmit an order. It prepares one complete
structure preview to help the human reproduce a BAG close manually in IBKR.

## Preview

Select `CLOSE STRUCTURE`. The immutable preview preserves every contract identity, expiry, strike,
right, multiplier, ratio, and remaining quantity, and reverses directions:

- current long → `SELL TO CLOSE`;
- current short → `BUY TO CLOSE`.

If any complete inverse leg is missing or invalid, CF0 returns
`COMBO_CLOSE_PREVIEW_UNAVAILABLE`. It never offers “easy leg first” or an individual-leg fallback.
Acknowledgement requires a Cloudflare Access authentication no older than five minutes. A stale
identity is logged out and must sign in again before retrying. Acknowledgement produces only
`CLOSE_PREVIEW_READY` plus the instruction to close the entire combo manually in IBKR; it does not
change broker truth or display “order sent”. A separate action password is required for
acknowledgement, the subsequent declaration of a manual IBKR close, and final fill reconciliation.
The browser requests it for each sensitive mutation and never saves it.

## Reconciliation

Only after the human reports the manual close does the position become
`RECONCILIATION_REQUIRED`. Enter the actual close timestamp, combo fill price, quantity, commission,
FX cost, required actual FX rate, and optional IBKR reference. CF0 stores:

- the original estimated proceeds/PnL/fees unchanged;
- actual proceeds and actual realized PnL from the manual fill;
- estimate error and fill reference.

Closing one of two structures yields `PARTIAL_CLOSE`, keeps one remaining structure monitored, and
separates realized from unrealized economics. Only a fully reconciled remaining quantity of zero
yields `CLOSED`. Button clicks alone never assert that a broker trade occurred.

The synthetic acceptance case persists €1,023 entry cash, €1,455 estimated close proceeds, €432
estimated PnL, €1,440 actual proceeds, €417 actual realized PnL, and −€15 estimate error.
