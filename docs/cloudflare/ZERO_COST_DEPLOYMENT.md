# Zero-cost workers.dev deployment

The design uses Workers Free, D1 Free, a SQLite-backed Durable Object, and Cloudflare Access on the
Zero Trust Free plan. “€0” describes Cloudflare hosting while usage stays inside current Free
quotas; a domain, market data, broker commissions, and FX are separate costs.

## First deployment

Requires Node.js 22 or newer and a Cloudflare account with Zero Trust initialized.

```bash
cd cloudflare
npm install
npx wrangler login
npx wrangler d1 create take-two-control
```

Copy the returned `database_id` into `cloudflare/wrangler.jsonc`. Do not change or delete an
existing production database ID.

```bash
npx wrangler d1 migrations apply take-two-control --remote
npm run check
npm run deploy
```

The Worker fails closed with `403 ACCESS_REQUIRED` until Access is active. In the Cloudflare
dashboard, open **Workers & Pages → take-two-control → Access**, choose **Protect this Worker behind
Access**, select **All traffic**, allow only **Cloudflare account members**, and apply the policy.
No `ADMIN_USERNAME` or `ADMIN_PASSWORD_HASH` secret is required.

The deployment output supplies the real URL:

```text
https://take-two-control.<cloudflare-account-subdomain>.workers.dev
```

After every deployment, verify the Access tab still shows **All traffic**, then test the URL in a
private browser window. The Cloudflare sign-in page must appear before any dashboard content.

## Local development

`wrangler.jsonc` contains a non-production simulated Access identity for `wrangler dev` only:

```bash
cd cloudflare
npm install
npm run db:local
npm run dev
```

No local application password is needed. `.dev.vars` is reserved for future local provider secrets
and remains ignored by Git. Run the complete Worker gate with `npm run check`.

## Market data later

The UI deploys without market data and reports `NOT_CONFIGURED`. After selecting and implementing a
compatible HTTPS provider:

```bash
npx wrangler secret put MARKET_DATA_API_KEY
npx wrangler secret put MARKET_DATA_BASE_URL
npm run deploy
```

Provider costs and entitlements are not included in the zero-hosting-cost claim.
