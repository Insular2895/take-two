# CF0 security

## Authentication

There is no registration. `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` are Wrangler secrets. The hash
format is:

```text
v1$pbkdf2-sha256$iterations$salt_base64$derived_key_base64
```

`npm run password:hash` uses a random 128-bit salt, PBKDF2-HMAC-SHA256, 600,000 iterations, and a
256-bit derived key. Verification uses Web Crypto and constant-time byte comparison. Do not lower
the work factor to fit a runtime. Confirm production login CPU behavior on the actual Free account;
if secure verification is demonstrated incompatible, treat this as a deployment blocker and add
Cloudflare Access after attaching a domain instead of weakening the hash.

## Sessions and request protection

- The browser receives a random 256-bit session token.
- D1 stores only its SHA-256 hash.
- Cookie: `HttpOnly; Secure; SameSite=Strict; Path=/`, default 12-hour expiry.
- A separate 256-bit CSRF token is tied to the D1 session and required on mutations.
- Close-preview acknowledgement requires sensitive authentication no older than five minutes.
- Five failed logins per identity in ten minutes cause a temporary D1-backed block.
- Logout revokes the D1 session before expiring the browser cookie.

All API endpoints except login return `401` without a valid session. `/dashboard` redirects to the
login screen. Static JavaScript and CSS contain no dossier or user data. Security headers include a
same-origin CSP, no-store caching, clickjacking protection, no referrer, and disabled sensitive
browser permissions.

## Trading boundary

The repository safety scan fails on executable broker-order method names or `transmit: true` in the
cloud runtime. Close output is an immutable BAG-shaped preview with `transmit=false`, `what_if=true`,
human confirmation, and `order_capability=forbidden`. There is no cancel, modify, exercise,
automatic retry, individual-leg close, or silent legging route.

## Secrets

Use `wrangler secret put`. Never put API keys, usernames, plaintext passwords, hashes, or production
database exports in Git. The authenticated export omits sessions, login attempts, daily security
identities, and every secret.
