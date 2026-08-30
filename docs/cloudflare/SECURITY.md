# CF0 security

## Authentication

Production authentication is provided only by Cloudflare Access. The Worker-level policy must
cover **All traffic** and allow only approved Cloudflare account members. There is no application
username, registration, login endpoint, or application session. A separate action password is not
a login mechanism: it is required only after Access authentication for sensitive mutations.

The Worker also fails closed: every request requires a direct `ctx.access` context and an Access
identity containing an email address. This application deliberately bundles its private HTML, CSS,
and JavaScript as Worker text modules instead of using the Static Assets router, because that router
does not propagate `ctx.access` to the user Worker. Assets and APIs therefore share the same
application-level Access check.

The Access dashboard policy remains external configuration. Removing or bypassing it is an
operational security change, even though the Worker would continue returning `403 ACCESS_REQUIRED`
without a verified Access context.

## Sessions and request protection

- Cloudflare Access owns authentication tokens, authorization, expiry, and revocation.
- The Worker records the verified Access email as the actor for human audit events.
- A random 256-bit `__Host-ttwo_csrf` cookie is `HttpOnly; Secure; SameSite=Strict; Path=/` and must
  match the `X-CSRF-Token` header on every mutation.
- Close-preview acknowledgement requires the Access identity login timestamp to be no older than
  five minutes. A stale session is logged out through `/cdn-cgi/access/logout` before retry.
- Imports, SAFE MODE, monitoring pause/resume, close acknowledgement, manual-close reporting, and
  actual-fill reconciliation also require `X-Action-Password` server-side. The browser prompts for
  every action and never saves the supplied password.
- The Worker permits at most five failed action-password checks per verified Access identity in a
  rolling 15-minute window. Failures, rate limiting, and successful confirmations are audited
  without logging the password.
- The logout button uses Cloudflare Access logout; no application logout endpoint exists.
- AJAX calls send `X-Requested-With: XMLHttpRequest` so an expired Access session can return `401`
  and force a browser refresh.

All private HTML, JavaScript, CSS, and API responses require Access. Security headers include a
same-origin CSP, `no-store`, clickjacking protection, no referrer, and disabled sensitive browser
permissions. The legacy `sessions` and `login_attempts` tables may remain in an existing D1 schema
for non-destructive compatibility, but the runtime does not read or write them. The separate
`action_password_attempts` table contains only a hashed Access identity, timestamps, and action
labels for rate limiting. Each request atomically reserves one of five attempt slots before secret
verification, preventing a concurrent burst from bypassing the limit.

## Trading boundary

The repository safety scan fails on executable broker-order method names or `transmit: true` in the
cloud runtime. Close output is an immutable BAG-shaped preview with `transmit=false`, `what_if=true`,
human confirmation, and `order_capability=forbidden`. There is no cancel, modify, exercise,
automatic retry, individual-leg close, or silent legging route.

The IBKR telemetry path is a separate capability boundary. Cloudflare Access first requires a
dedicated Service Auth token; the Worker then verifies a telemetry-only HMAC identity, timestamp,
body hash and one-time nonce. Its secret is not accepted by broker claim/event routes, and the
bridge HMAC is not accepted by the telemetry route. The exact-key payload rejects account IDs,
unexpected identity fields, non-paper mode, non-TTWO positions, inconsistent quote midpoints,
mismatched totals, stale collection times and oversized bodies. D1 contains only the latest
redacted projection and the browser endpoint always returns `execution_enabled=false`.

## Secrets

Cloudflare Access removes the application login password. `ACTION_PASSWORD_VERIFIER` is a keyed
HMAC-SHA-256 verifier stored as an encrypted Worker secret; it contains no plaintext password and
is fast enough for Workers Free. Generate and install it only with `npm run action-password:set`,
which prompts without echo and also writes the verifier—not the password—to ignored `.dev.vars`.
Never put API keys, credentials, Access tokens, production database exports, or private identity
data in Git. The authenticated export omits authentication/rate-limit tables, daily security
identities, and every secret.

The action password is defense in depth for an unlocked or stolen Access browser session. It does
not protect against a complete Cloudflare account takeover capable of replacing Worker code or
secrets. The no-order boundary remains the primary financial blast-radius control.

Machine service tokens and the telemetry HMAC are encrypted operational secrets. They belong only
in Cloudflare and the root-owned VM environment file, never in `.dev.vars`, screenshots, chat,
logs, GitHub Actions output, or the repository.
