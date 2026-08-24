# CF0 security

## Authentication

Production authentication is provided only by Cloudflare Access. The Worker-level policy must
cover **All traffic** and allow only approved Cloudflare account members. There is no application
username, password, registration, login endpoint, or password secret.

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
- The logout button uses Cloudflare Access logout; no application logout endpoint exists.
- AJAX calls send `X-Requested-With: XMLHttpRequest` so an expired Access session can return `401`
  and force a browser refresh.

All private HTML, JavaScript, CSS, and API responses require Access. Security headers include a
same-origin CSP, `no-store`, clickjacking protection, no referrer, and disabled sensitive browser
permissions. The legacy `sessions` and `login_attempts` tables may remain in an existing D1 schema
for non-destructive compatibility, but the runtime does not read or write them.

## Trading boundary

The repository safety scan fails on executable broker-order method names or `transmit: true` in the
cloud runtime. Close output is an immutable BAG-shaped preview with `transmit=false`, `what_if=true`,
human confirmation, and `order_capability=forbidden`. There is no cancel, modify, exercise,
automatic retry, individual-leg close, or silent legging route.

## Secrets

Cloudflare Access removes the application password secrets. Use `wrangler secret put` only for
future provider credentials. Never put API keys, credentials, Access tokens, production database
exports, or private identity data in Git. The authenticated export omits legacy auth tables, daily
security identities, and every secret.
