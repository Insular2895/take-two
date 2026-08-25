# CF0 analysis compute architecture

Status: implemented locally on 2026-08-25; deployment and secrets remain to be configured.

## Trust and data flow

```text
Access-authenticated browser
  → Worker validates exact budget + CSRF + action password
  → immutable request in D1
  → Worker dispatches fixed repository/workflow/ref with analysis_request_id only
  → GitHub runner fetches request through Access service token + HMAC
  → canonical Python catalog/request/budget/context enumeration
  → signed batches of 20 summaries/details
  → D1 verifies total before terminal status
  → Access-authenticated browser reads D1
```

D1 is the source of truth. GitHub logs and workflow status are compute evidence, not application
state. A Mac, VS Code, local server, or open terminal is not required after deployment.

## Fixed dispatch boundary

The Worker owns `GITHUB_REPOSITORY`, `GITHUB_WORKFLOW`, and `GITHUB_GOVERNED_REF`; the token is the
Worker secret `GITHUB_ACTIONS_TOKEN`. The only workflow input is an identifier matching
`analysis-[a-f0-9]{24}`. The workflow must exist on the repository default branch for
`workflow_dispatch`. A fine-grained token needs repository Actions write permission to invoke the
dispatch endpoint.

Browser data is never interpolated into a shell command. The workflow exposes the validated ID as
an environment variable and runs a fixed Python script.

## Signed internal protocol

GitHub sends a Cloudflare Access service token at the edge and an application HMAC at the Worker.
The signed payload is:

```text
timestamp\nnonce\nanalysis_request_id\nHTTP_METHOD\npathname\nsha256(body)
```

The Worker requires the ID to agree across URL and header, a five-minute timestamp window, a unique
nonce persisted in D1, a matching body hash, a constant-time signature match, and a 512 KiB body
cap. Nonces expire from the replay table after 24 hours. Candidate batches are capped at 20 so the
summary/detail writes remain within free-plan per-invocation operation constraints.

Required secret/configuration boundary:

- Worker secrets: `GITHUB_ACTIONS_TOKEN`, `ANALYSIS_CALLBACK_SECRET`;
- GitHub Actions secrets: `ANALYSIS_WORKER_BASE_URL`, `ANALYSIS_CALLBACK_SECRET`,
  `CF_ACCESS_CLIENT_ID`, `CF_ACCESS_CLIENT_SECRET`;
- GitHub variable only for governed mode: `GOVERNED_SNAPSHOT_PATH`;
- existing Worker secret: `ACTION_PASSWORD_VERIFIER`.

The Cloudflare service token must be included in a `Service Auth` policy on the same Access
application. Human browser paths still require the account-member Access policy.

## D1 model

Migrations `0005_phase_m_research_workbench.sql` and
`0006_research_candidate_filter_metrics.sql` add:

- `analysis_requests`: immutable inputs, lifecycle, counts, provenance, verdict;
- `analysis_runs`: append-only truthful step history;
- `analysis_candidate_summaries`: full sortable/filterable compact universe;
- `analysis_candidate_details`: structured per-candidate economics and limitations;
- `candidate_selections`: immutable provenance ledger;
- `planned_positions`: immutable `PLANNED` dossier, actual fields null;
- `analysis_callback_nonces`: HMAC anti-replay state.

No raw option chain, filesystem path, broker credential, GitHub token, callback secret, or Access
token is stored in D1.

## Free-tier implications

The synthetic fixture currently generates 600 candidates and therefore 1,200 candidate rows plus
indexes per analysis. This fits the present design, but zero cost is conditional, not guaranteed.
Cloudflare currently documents 100,000 Worker requests/day, 5 million D1 rows read/day,
100,000 rows written/day, 5 GB aggregate D1 free storage, and a 500 MB per-database Free limit.
GitHub-hosted Actions is free for public repositories; private repositories consume plan-specific
included minutes and can be billed beyond them. Usage and D1 size must be monitored before repeated
or much larger governed snapshots.

Official references:

- https://docs.github.com/en/rest/actions/workflows
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- https://docs.github.com/en/actions/concepts/security/script-injections
- https://docs.github.com/en/actions/concepts/billing-and-usage
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers/platform/pricing/
- https://developers.cloudflare.com/d1/platform/limits/
- https://developers.cloudflare.com/workers/local-development/
