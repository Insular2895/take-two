# Zero-cost workers.dev deployment

The design uses only Workers Free, D1 Free, and a SQLite-backed Durable Object on the Free plan.
“€0” describes Cloudflare hosting while usage stays inside Free quotas; a domain, market data,
broker commissions, and FX are separate costs.

## First deployment

Requires Node.js 22 or newer and a Cloudflare account.

```bash
cd cloudflare
npm install
npx wrangler login
npx wrangler d1 create take-two-control
```

Copy the returned `database_id` into `cloudflare/wrangler.jsonc`, replacing
`REPLACE_WITH_D1_DATABASE_ID`. Do not change or delete an existing production database ID.

```bash
npx wrangler d1 migrations apply take-two-control --remote
npm run password:hash
npx wrangler secret put ADMIN_PASSWORD_HASH
npx wrangler secret put ADMIN_USERNAME
npm run deploy
```

Paste the generated versioned hash, not the password, into `ADMIN_PASSWORD_HASH`. The deployment
output supplies the real URL:

```text
https://take-two-control.<cloudflare-account-subdomain>.workers.dev
```

No URL is claimed until Wrangler actually deploys it. Secrets are not present in `wrangler.jsonc`,
D1, browser code, logs, fixtures, or this repository.

## Local development

Create local-only secret values in `.dev.vars` (ignored by Git), then:

```bash
cd cloudflare
npm install
npm run db:local
npm run dev
```

Use a strong hash produced by `npm run password:hash`. Never reuse production credentials locally.
Run the complete Worker gate with `npm run check`.

## Market data later

The UI deploys without market data and reports `NOT_CONFIGURED`. After selecting and implementing a
compatible HTTPS provider:

```bash
npx wrangler secret put MARKET_DATA_API_KEY
npx wrangler secret put MARKET_DATA_BASE_URL
npm run deploy
```

Provider costs and entitlements are not included in the zero-hosting-cost claim.
