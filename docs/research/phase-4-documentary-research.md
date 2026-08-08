# Phase 4 documentary research — point-in-time backtests and holdout

Date: 2026-08-08
Status: `implemented_protocol_empirical_evaluation_blocked`

## Conclusions

- A backtest result is inseparable from its code, configuration, dataset, split policy, trial
  registry and seed. `ExperimentManifest` hashes those inputs and detects post-hoc mutation.
- Feature availability must precede the decision timestamp, labels must not overlap the next
  partition after purge/embargo, and the final holdout must stay hidden until an explicitly
  logged one-time evaluation.
- Bailey, Borwein, López de Prado and Zhu introduce PBO/CSCV to estimate selection-driven
  overfitting across strategy configurations. The existing implementation followed the CSCV
  split idea but used first-occurrence ranks and first-strategy selection for ties. It now uses
  midranks and averages tied in-sample winners, making the result invariant to strategy order.
- Bailey and López de Prado's DSR corrects for multiple trials and non-normal returns. The
  repository's function remains explicitly approximate and uses the complete trial count; it is
  not a substitute for a clean test or holdout.
- Permuting returns and comparing their mean is invalid because permutation preserves the mean.
  The corrected placebo permutes signals relative to realized returns, computes a permutation
  p-value, and checks delayed signals.

## Sources inspected

- David H. Bailey, Jonathan Borwein, Marcos López de Prado and Qiji Jim Zhu, “The Probability
  of Backtest Overfitting,” SSRN 2326253, Journal of Computational Finance, 2015. Primary SSRN
  bibliographic record and abstract inspected; SSRN denied automated full-page access during
  this run, so no uninspected page/formula is claimed.
- David H. Bailey and Marcos López de Prado, “The Deflated Sharpe Ratio: Correcting for
  Selection Bias, Backtest Overfitting and Non-Normality,” SSRN 2460551 / *Journal of Portfolio
  Management* 40(5), 2014. Primary SSRN bibliographic record and publisher metadata inspected.
- Larry Wasserman, *All of Statistics*, 2004, remains the general source for resampling and
  statistical testing; no specialized PBO claim is attributed to it.
- FRED/ALFRED real-time-period documentation, already verified in Phase 0, supports separating
  observation time from information availability time.

## Implementation and limits

- Closed splits expose only final-holdout count, not IDs. The actual dataset is still absent, so
  `validation/holdout_protocol_v10.yaml` remains `awaiting_authorized_dataset` and no evaluation
  ledger entry has been created.
- The in-memory ledger is hash-chained, allows one `evaluate`, permits reporting, and blocks all
  later tuning. Persistence can serialize entries later, but creating a fake empty/real access
  record was deliberately avoided.
- The permutation placebo is a valid alignment null for supplied signals; exchangeability may
  still fail under serial dependence. Phase 5 adds block-resampling tools for dependent series.
- PBO/DSR are diagnostics, not proof against every form of research overfitting.
- V7–V9 stay contaminated and can never become the new final holdout.
