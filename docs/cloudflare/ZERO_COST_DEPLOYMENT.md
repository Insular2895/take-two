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
npm run action-password:set
```

The Worker fails closed with `403 ACCESS_REQUIRED` until Access is active. In the Cloudflare
dashboard, open **Workers & Pages → take-two-control → Access**, choose **Protect this Worker behind
Access**, select **All traffic**, allow only **Cloudflare account members**, and apply the policy.
No `ADMIN_USERNAME` or `ADMIN_PASSWORD_HASH` secret is required. `npm run action-password:set`
prompts twice without echo, derives a keyed verifier, stores only that verifier in the encrypted
`ACTION_PASSWORD_VERIFIER` Worker secret, and keeps the same verifier in ignored local `.dev.vars`.
For an existing deployment, run the action-password command before deploying code that requires
it. For a first deployment, the runtime returns `503 ACTION_PASSWORD_NOT_CONFIGURED` only on
sensitive mutations until the command completes; reads remain behind Access.

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
npm run action-password:set-local
npm run db:local
npm run dev
```

The local command prompts without echo and writes only the verifier to `.dev.vars`, which remains
ignored by Git. Re-entering the same password generates a new random verifier while preserving the
same user-facing password. Run the complete Worker gate with `npm run check`.

## Rotate the action password

From `cloudflare/`, run `npm run action-password:set` again. The old verifier is replaced remotely
and locally, so the old password stops working immediately. The script never prints either the
password or verifier. Confirm the new password in the dashboard after deployment.

## Market data later

The UI deploys without market data and reports `NOT_CONFIGURED`. After selecting and implementing a
compatible HTTPS provider:

```bash
npx wrangler secret put MARKET_DATA_API_KEY
npx wrangler secret put MARKET_DATA_BASE_URL
npm run deploy
```

Provider costs and entitlements are not included in the zero-hosting-cost claim.
