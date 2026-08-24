import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { syntheticCreditSpreadDossier, syntheticDemoDossier } from "../src/demo";
import { verifyActionPassword } from "../src/auth";
import { handleRequest } from "../src/index";

interface AccessSession {
  cookie: string;
  csrf: string;
}

const TEST_ACCESS = {
  aud: "local-take-two-control",
  getIdentity: async () => ({ email: "local-admin@take-two.invalid" }),
} as CloudflareAccessContext;
const TEST_ACTION_PASSWORD = "test-action-password-123!";
const TEST_ACTION_PASSWORD_VERIFIER = "v1$hmac-sha256$BwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwcHBwc$yXxGMhJsIjUD7xzr7aV5eTPfQ7gtwCXYw7O0nKMJtMw";

async function accessSession(): Promise<AccessSession> {
  const response = await handleRequest(new Request("https://control.test/api/session"), env, TEST_ACCESS);
  expect(response.status).toBe(200);
  const payload = await response.clone().json<{ csrf_token: string }>();
  const cookie = (response.headers.get("Set-Cookie") ?? "").split(";")[0]!;
  expect(cookie).toContain("__Host-ttwo_csrf=");
  return { cookie, csrf: payload.csrf_token };
}

function request(
  path: string,
  session: AccessSession,
  method = "GET",
  body?: unknown,
  actionPassword: string | null = method === "GET" ? null : TEST_ACTION_PASSWORD,
): Promise<Response> {
  return handleRequest(new Request(`https://control.test${path}`, {
    method,
    headers: {
      Cookie: session.cookie,
      "X-Requested-With": "XMLHttpRequest",
      ...(method === "GET" ? {} : { "X-CSRF-Token": session.csrf, "Content-Type": "application/json" }),
      ...(actionPassword === null ? {} : { "X-Action-Password": actionPassword }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  }), env, TEST_ACCESS);
}

async function importAndMonitor(session: AccessSession): Promise<void> {
  expect((await request("/api/demo/import", session, "POST", {})).status).toBe(201);
  const stub = env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
  expect((await stub.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
}

describe("private Cloudflare Access boundary", () => {
  it("verifies the keyed action-password format without storing a plaintext password", async () => {
    expect(await verifyActionPassword(TEST_ACTION_PASSWORD, TEST_ACTION_PASSWORD_VERIFIER)).toBe(true);
    expect(await verifyActionPassword("wrong-action-password", TEST_ACTION_PASSWORD_VERIFIER)).toBe(false);
    expect(await verifyActionPassword(TEST_ACTION_PASSWORD, "malformed")).toBe(false);
  });

  it("reveals no dashboard or API data without a verified Access context", async () => {
    const dashboard = await handleRequest(new Request("https://control.test/dashboard"), env, undefined);
    expect(dashboard.status).toBe(403);
    expect(await dashboard.text()).not.toContain("TTWO — POSITION CONTROL");
    const api = await handleRequest(new Request("https://control.test/api/dashboard"), env, undefined);
    expect(api.status).toBe(403);
    expect(await api.json()).toEqual({ error: "ACCESS_REQUIRED" });
  });

  it("accepts the simulated local Access identity and serves bundled private assets", async () => {
    const session = await accessSession();
    const dashboard = await request("/dashboard", session);
    expect(dashboard.status).toBe(200);
    const dashboardHtml = await dashboard.text();
    expect(dashboardHtml).toContain("TTWO — POSITION CONTROL");
    expect(dashboardHtml).toContain("action-password-dialog");
    expect((await request("/styles.css", session)).headers.get("Content-Type")).toContain("text/css");
    expect((await request("/app.js", session)).headers.get("Content-Type")).toContain("text/javascript");
  });

  it("rejects Access identities without an email", async () => {
    const access = { aud: "test", getIdentity: async () => ({ user_uuid: "missing-email" }) } as CloudflareAccessContext;
    const response = await handleRequest(new Request("https://control.test/api/dashboard"), env, access);
    expect(response.status).toBe(403);
    expect(await response.json()).toEqual({ error: "ACCESS_REQUIRED" });
  });

  it("enforces CSRF and removes the legacy password endpoints", async () => {
    const session = await accessSession();
    const csrfFailure = await handleRequest(new Request("https://control.test/api/safe-mode", {
      method: "POST", headers: { Cookie: session.cookie, "Content-Type": "application/json" }, body: "{\"enabled\":true}",
    }), env, TEST_ACCESS);
    expect(csrfFailure.status).toBe(403);
    expect((await request("/api/login", session, "POST", {})).status).toBe(404);
    expect((await request("/api/reauth", session, "POST", {})).status).toBe(404);
  });

  it("requires the separate action password for sensitive mutations", async () => {
    const session = await accessSession();
    const missing = await request("/api/demo/import", session, "POST", {}, null);
    expect(missing.status).toBe(403);
    expect(await missing.json()).toEqual({ error: "ACTION_PASSWORD_REQUIRED" });

    const invalid = await request("/api/demo/import", session, "POST", {}, "wrong-action-password");
    expect(invalid.status).toBe(403);
    expect(await invalid.json()).toEqual({ error: "ACTION_PASSWORD_INVALID" });

    const accepted = await request("/api/demo/import", session, "POST", {});
    expect(accepted.status).toBe(201);
  });

  it("fails closed when the action-password secret is absent", async () => {
    const session = await accessSession();
    const missingSecretEnv = Object.create(env) as Env;
    Object.defineProperty(missingSecretEnv, "ACTION_PASSWORD_VERIFIER", { value: "" });
    const response = await handleRequest(new Request("https://control.test/api/safe-mode", {
      method: "POST",
      headers: {
        Cookie: session.cookie,
        "Content-Type": "application/json",
        "X-CSRF-Token": session.csrf,
        "X-Action-Password": TEST_ACTION_PASSWORD,
      },
      body: "{\"enabled\":true}",
    }), missingSecretEnv, TEST_ACCESS);
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({ error: "ACTION_PASSWORD_NOT_CONFIGURED" });
  });

  it("rate-limits action-password guessing after five failures", async () => {
    const session = await accessSession();
    for (let attempt = 1; attempt <= 4; attempt += 1) {
      const response = await request("/api/safe-mode", session, "POST", { enabled: true }, `wrong-${attempt}-password`);
      expect(response.status).toBe(403);
      expect(await response.json()).toEqual({ error: "ACTION_PASSWORD_INVALID" });
    }
    const fifth = await request("/api/safe-mode", session, "POST", { enabled: true }, "wrong-fifth-password");
    expect(fifth.status).toBe(429);
    expect(await fifth.json()).toEqual({ error: "ACTION_PASSWORD_RATE_LIMITED" });
    const stillBlocked = await request("/api/safe-mode", session, "POST", { enabled: true });
    expect(stillBlocked.status).toBe(429);
  });

  it("atomically caps a concurrent action-password guessing burst", async () => {
    const session = await accessSession();
    const responses = await Promise.all(Array.from({ length: 12 }, (_, index) => (
      request("/api/safe-mode", session, "POST", { enabled: true }, `concurrent-wrong-password-${index}`)
    )));
    expect(responses.every((response) => response.status === 403 || response.status === 429)).toBe(true);
    const attempts = await env.DB.prepare("SELECT count(*) AS total FROM action_password_attempts").first<{ total: number }>();
    expect(attempts?.total).toBe(5);
    expect((await request("/api/safe-mode", session, "POST", { enabled: true })).status).toBe(429);
  });
});

describe("D1 persistence and Durable Object monitoring", () => {
  it("survives independent requests with position, history, SAFE MODE, preview, and audit", async () => {
    const session = await accessSession();
    await importAndMonitor(session);
    expect((await request("/api/safe-mode", session, "POST", { enabled: true })).status).toBe(200);
    const previewResponse = await request("/api/close-previews", session, "POST", { quantity: 2 });
    expect(previewResponse.status).toBe(201);
    const dashboard = await (await request("/api/dashboard", session)).json<Record<string, any>>();
    expect(dashboard.position.id).toBe("synthetic-ttwo-position-v1");
    expect(dashboard.latest_pnl.mtm_pnl).toBeCloseTo(464, 8);
    expect(dashboard.latest_pnl.liquidation_pnl).toBeCloseTo(432, 8);
    expect(dashboard.system.safe_mode).toBe(1);
    expect(dashboard.close_previews).toHaveLength(1);
    expect(dashboard.audit_events.map((event: { event_type: string }) => event.event_type)).toContain("SAFE_MODE_ENABLED");
    expect(dashboard.audit_events.map((event: { actor: string }) => event.actor)).toContain("access:local-admin@take-two.invalid");
  });

  it("is idempotent for duplicate/concurrent alarm requests and retains data on provider absence", async () => {
    const session = await accessSession();
    expect((await request("/api/demo/import", session, "POST", {})).status).toBe(201);
    const stub = env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
    await Promise.all([
      stub.fetch("https://monitor/run", { method: "POST" }),
      stub.fetch("https://monitor/run", { method: "POST" }),
    ]);
    const count = await env.DB.prepare("SELECT count(*) AS total FROM pnl_snapshots").first<{ total: number }>();
    expect(count?.total).toBe(1);
    const system = await env.DB.prepare("SELECT market_data_status FROM system_state WHERE singleton=1").first<{ market_data_status: string }>();
    expect(system?.market_data_status).toBe("SYNTHETIC_DEMO");
  });

  it("reports NOT_CONFIGURED without creating a fake quote", async () => {
    const session = await accessSession();
    const dossier = syntheticDemoDossier();
    dossier.position_id = "no-provider-position";
    dossier.dossier_id = "no-provider-dossier";
    dossier.fixture_status = "CANONICAL_EXPORT";
    dossier.last_imported_snapshot = null;
    expect((await request("/api/positions/import", session, "POST", dossier)).status).toBe(201);
    const stub = env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
    await stub.fetch("https://monitor/run", { method: "POST" });
    const system = await env.DB.prepare("SELECT market_data_status FROM system_state WHERE singleton=1").first<{ market_data_status: string }>();
    const snapshots = await env.DB.prepare("SELECT count(*) AS total FROM pnl_snapshots").first<{ total: number }>();
    expect(system?.market_data_status).toBe("NOT_CONFIGURED");
    expect(snapshots?.total).toBe(0);
  });

  it("does not schedule useful work with no active position and supports persisted pause/resume", async () => {
    const session = await accessSession();
    const stub = env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
    expect((await stub.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
    expect((await env.DB.prepare("SELECT count(*) AS total FROM pnl_snapshots").first<{ total: number }>())?.total).toBe(0);
    await importAndMonitor(session);
    expect((await request("/api/monitor/pause", session, "POST", {})).status).toBe(200);
    expect((await env.DB.prepare("SELECT monitoring_paused FROM system_state").first<{ monitoring_paused: number }>())?.monitoring_paused).toBe(1);
    expect((await request("/api/monitor/resume", session, "POST", {})).status).toBe(200);
    expect((await env.DB.prepare("SELECT monitoring_paused FROM system_state").first<{ monitoring_paused: number }>())?.monitoring_paused).toBe(0);
  });
});

describe("preview-only close and actual fill reconciliation", () => {
  it("requires recent Cloudflare Access authentication and never transmits", async () => {
    const session = await accessSession();
    await importAndMonitor(session);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 2 })).json<Record<string, any>>();
    expect(preview.safety).toEqual({ transmit: false, what_if: true, order_capability: "forbidden", security_type: "BAG" });
    expect(preview.legs.map((leg: { action: string }) => leg.action)).toEqual(["SELL_TO_CLOSE", "BUY_TO_CLOSE"]);
    const staleAccess = {
      aud: "production-access-aud",
      getIdentity: async () => ({ email: "admin@example.com", iat: 1 }),
    } as CloudflareAccessContext;
    const staleRequest = new Request(`https://control.test/api/close-previews/${preview.preview_id}/acknowledge`, {
      method: "POST",
      headers: { Cookie: session.cookie, "X-CSRF-Token": session.csrf, "Content-Type": "application/json" },
      body: "{}",
    });
    const staleResponse = await handleRequest(staleRequest, env, staleAccess);
    expect(staleResponse.status).toBe(403);
    expect(await staleResponse.json()).toEqual({ error: "SENSITIVE_ACCESS_REAUTH_REQUIRED" });
    const acknowledged = await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    expect(acknowledged.status).toBe(200);
    expect(await acknowledged.json()).toMatchObject({ status: "CLOSE_PREVIEW_READY", transmitted: false });
  });

  it("persists the €432 estimate, €417 actual result, and -€15 error", async () => {
    const session = await accessSession();
    await importAndMonitor(session);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 2 })).json<Record<string, any>>();
    await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    await request(`/api/close-previews/${preview.preview_id}/manual-close-reported`, session, "POST", {});
    const reconciliation = await request(`/api/close-previews/${preview.preview_id}/reconcile`, session, "POST", {
      timestamp: "2026-08-24T15:00:00.000Z",
      combo_fill_price: 7.864130434782608,
      close_cash_flow_type: "CREDIT",
      quantity_closed: 2,
      commission: 2,
      fx_cost: 5,
      actual_fx_rate: 0.92,
      broker_reference: "SYNTHETIC-IBKR-REF",
    });
    expect(reconciliation.status).toBe(201);
    const result = await reconciliation.json<Record<string, number | string>>();
    expect(result.actual_proceeds).toBeCloseTo(1440, 8);
    expect(result.actual_realized_pnl).toBeCloseTo(417, 8);
    expect(result.estimated_pnl).toBeCloseTo(432, 8);
    expect(result.estimate_error).toBeCloseTo(-15, 8);
    expect(result.state).toBe("CLOSED");
    const stored = await env.DB.prepare("SELECT actual_realized_pnl,estimate_error FROM fills").first<{ actual_realized_pnl: number; estimate_error: number }>();
    expect(stored?.actual_realized_pnl).toBeCloseTo(417, 8);
    expect(stored?.estimate_error).toBeCloseTo(-15, 8);
  });

  it("keeps one of two structures open after a partial close", async () => {
    const session = await accessSession();
    await importAndMonitor(session);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 1 })).json<Record<string, any>>();
    await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    await request(`/api/close-previews/${preview.preview_id}/manual-close-reported`, session, "POST", {});
    const response = await request(`/api/close-previews/${preview.preview_id}/reconcile`, session, "POST", {
      timestamp: "2026-08-24T15:00:00.000Z", combo_fill_price: 7.864130434782608,
      close_cash_flow_type: "CREDIT",
      quantity_closed: 1, commission: 1, fx_cost: 2.5, actual_fx_rate: 0.92,
    });
    const result = await response.json<Record<string, number | string>>();
    expect(result.state).toBe("PARTIAL_CLOSE");
    expect(result.quantity_remaining).toBe(1);
    const position = await env.DB.prepare("SELECT quantity_initial,quantity_remaining,state,realized_pnl FROM positions").first<Record<string, number | string>>();
    expect(position).toMatchObject({ quantity_initial: 2, quantity_remaining: 1, state: "PARTIAL_CLOSE" });
    expect(position?.realized_pnl).not.toBeNull();
  });

  it("reconciles a credit entry closed for a debit without using capital as PnL basis", async () => {
    const session = await accessSession();
    const credit = syntheticCreditSpreadDossier();
    expect((await request("/api/positions/import", session, "POST", credit)).status).toBe(201);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 1 })).json<Record<string, any>>();
    expect(preview.estimated_close_cash_flow_policy).toBeCloseTo(-105, 8);
    await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    await request(`/api/close-previews/${preview.preview_id}/manual-close-reported`, session, "POST", {});
    const response = await request(`/api/close-previews/${preview.preview_id}/reconcile`, session, "POST", {
      timestamp: "2026-08-24T15:00:00.000Z",
      combo_fill_price: 1.00,
      close_cash_flow_type: "DEBIT",
      quantity_closed: 1,
      commission: 2,
      fx_cost: 0,
    });
    expect(response.status).toBe(201);
    const result = await response.json<Record<string, number | string>>();
    expect(result.actual_close_cash_flow_policy).toBeCloseTo(-102, 8);
    expect(result.actual_realized_pnl).toBeCloseTo(198, 8);
    const stored = await env.DB.prepare(
      "SELECT close_cash_flow_type,signed_close_cash_flow_policy,actual_realized_pnl FROM fills",
    ).first<Record<string, number | string>>();
    expect(stored).toMatchObject({ close_cash_flow_type: "DEBIT" });
    expect(stored?.signed_close_cash_flow_policy).toBeCloseTo(-102, 8);
    expect(stored?.actual_realized_pnl).toBeCloseTo(198, 8);
  });

  it("records a losing credit close with costs in the same negative direction", async () => {
    const session = await accessSession();
    const credit = syntheticCreditSpreadDossier();
    expect((await request("/api/positions/import", session, "POST", credit)).status).toBe(201);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 1 })).json<Record<string, any>>();
    await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    await request(`/api/close-previews/${preview.preview_id}/manual-close-reported`, session, "POST", {});
    const result = await (await request(`/api/close-previews/${preview.preview_id}/reconcile`, session, "POST", {
      timestamp: "2026-08-24T15:00:00.000Z",
      combo_fill_price: 6.50,
      close_cash_flow_type: "DEBIT",
      quantity_closed: 1,
      commission: 10,
      fx_cost: 0,
    })).json<Record<string, number>>();
    expect(result.actual_close_cash_flow_policy).toBeCloseTo(-660, 8);
    expect(result.actual_realized_pnl).toBeCloseTo(-360, 8);
  });

  it("allocates signed entry cash flow pro rata on a partial credit close", async () => {
    const session = await accessSession();
    const base = syntheticCreditSpreadDossier();
    const credit = {
      ...base,
      dossier_id: "synthetic-ttwo-credit-partial-v1",
      position_id: "synthetic-ttwo-credit-partial-position-v1",
      quantity: 2,
      entry_cash_flow_policy: 600,
      capital_required_policy: 1400,
      legs: base.legs.map((leg) => ({ ...leg, quantity: 2 })),
    };
    expect((await request("/api/positions/import", session, "POST", credit)).status).toBe(201);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 1 })).json<Record<string, any>>();
    await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    await request(`/api/close-previews/${preview.preview_id}/manual-close-reported`, session, "POST", {});
    const result = await (await request(`/api/close-previews/${preview.preview_id}/reconcile`, session, "POST", {
      timestamp: "2026-08-24T15:00:00.000Z",
      combo_fill_price: 1.10,
      close_cash_flow_type: "DEBIT",
      quantity_closed: 1,
      commission: 3,
      fx_cost: 2,
    })).json<Record<string, number | string>>();
    expect(result.actual_close_cash_flow_policy).toBeCloseTo(-115, 8);
    expect(result.actual_realized_pnl).toBeCloseTo(185, 8);
    expect(result.quantity_remaining).toBe(1);
    const position = await env.DB.prepare(
      "SELECT quantity_remaining,realized_pnl,entry_cash_flow_policy,capital_required_policy FROM positions",
    ).first<Record<string, number>>();
    expect(position?.quantity_remaining).toBe(1);
    expect(position?.realized_pnl).toBeCloseTo(185, 8);
    expect(position?.entry_cash_flow_policy).toBe(600);
    expect(position?.capital_required_policy).toBe(1400);
  });
});
