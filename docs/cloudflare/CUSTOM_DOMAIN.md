# Attach a custom domain later

The initial application works on the Wrangler-provided `workers.dev` URL. Buying a domain is
optional and does not change the Worker, D1, Durable Object, API, dashboard, or market adapter.

1. Buy a domain from OVH, Hostinger, or another registrar.
2. Add the domain as a zone in Cloudflare.
3. At the registrar, replace nameservers with the pair Cloudflare provides; wait for activation.
4. In Cloudflare, create/confirm the DNS hostname, for example `trade.example.com`.
5. Open **Workers & Pages → take-two-control → Settings → Domains & Routes → Add → Custom domain**.
6. Attach `trade.example.com` and verify HTTPS/Access before changing bookmarks.

Cloudflare documents the current procedure at
[Worker custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/).
Do not hard-code the hostname in the application; cookies use `Path=/` without a fixed domain.

Cloudflare Access is mandatory, not optional defense in depth. Confirm that the Worker-level
**All traffic** policy covers the new hostname before using it. Test Access login/logout, the
Worker's fail-closed `ctx.access` check, CSRF, export, SAFE MODE, monitor controls, and close-preview
reauthentication after the routing change.
