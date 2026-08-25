# CF0 Research Workbench

Status: implemented locally on 2026-08-25. Research-only; no live market data or execution.

## Product contract

The private Cloudflare application has two top-level workspaces:

- `RESEARCH`: submit one governed budget request, follow its durable status, browse the complete
  persisted candidate universe, compare up to four candidates, and select a paper-eligible result;
- `POSITION`: the existing CF0 monitoring, PnL, Safe Mode, close preview, and manual fill
  reconciliation flow, unchanged in capability.

The safety banner is global: `read_only=true`, `transmit=false`, and
`order_capability=forbidden`. The Research UI never accepts a repository, workflow, branch, market
symbol, provider credential, broker credential, or arbitrary Python input.

## Budget request

The immutable `AnalysisBudgetRequest` contains exactly:

| UI field | Default | BudgetPolicyV2 mapping |
|---|---:|---|
| preferred budget | €800 | `target_budget - under_target_tolerance` |
| target budget | €1,000 | `target_budget` |
| maximum budget | €1,500 | `target_budget + max_overspend` |
| minimum policy | `SOFT` | `minimum_spend_policy` (`SOFT` or `HARD`) |
| market data | `SYNTHETIC_DEMO` | approved enum only |

Validation rejects unknown fields, non-finite values, non-positive money, non-EUR currency, and any
ordering other than `preferred <= target <= maximum`. Hard-ceiling comparisons remain those of the
canonical V2 evaluator: machine representation tolerance only, never an economic allowance.

## Analysis lifecycle

`CREATED → QUEUED → RUNNING → COMPLETE | NO_TRADE | FAILED | CANCELLED` is persisted in D1.
Progress is a list of truthful named steps, not a fabricated percentage. One partial unique index
allows at most one active analysis. An identical active request is idempotently reused; a different
active request returns conflict; completed launches have a short cooldown.

`NO_TRADE` is a terminal result with persisted reasons. A top view never deletes candidates. The
browser downloads all compact summaries for one completed analysis, then applies filters, sort,
heatmap, and pagination locally.

## Selection

Selection requires Cloudflare Access, CSRF, and the existing action password. It stores an immutable
selection containing the economics-ticket hash, Phase M context ID/hash, snapshot ID/hash, and Git
commit. It also creates a separate `PLANNED` dossier whose actual entry cash flow and actual open
timestamp are null. It does not create an active monitored position.

The conceptual `EXÉCUTER` control only returns `IBKR EXECUTION NOT CONFIGURED`. There is no manual
opening tutorial, per-leg fallback, broker session, or order endpoint.

## Data modes

- `SYNTHETIC_DEMO`: explicit deterministic modeled fixture; never described as live or executable.
- `LAST_GOVERNED_SNAPSHOT`: runner-side path must be configured to a committed governed snapshot;
  absence fails the analysis.

`LIVE` is not an accepted value.

## Future work — NOT YET ENABLED

- OPRA/live provider launch may replace the snapshot adapter after entitlement, freshness, and
  shadow-data validation.
- Personal IBKR execution may consume a selected planned dossier after a separate financial and
  security review.
- Commercial users may eventually authorize their own broker connections; no multi-tenant identity,
  secrets, billing, or execution design is implemented here.
