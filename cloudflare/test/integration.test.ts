import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { syntheticDemoDossier } from "../src/demo";
import { handleRequest } from "../src/index";

interface AccessSession {
  cookie: string;
  csrf: string;
}

const TEST_ACCESS = {
  aud: "local-take-two-control",
  getIdentity: async () => ({ email: "local-admin@take-two.invalid" }),
} as CloudflareAccessContext;

async function accessSession(): Promise<AccessSession> {
  const response = await handleRequest(new Request("https://control.test/api/session"), env, TEST_ACCESS);
  expect(response.status).toBe(200);
  const payload = await response.clone().json<{ csrf_token: string }>();
  const cookie = (response.headers.get("Set-Cookie") ?? "").split(";")[0]!;
  expect(cookie).toContain("__Host-ttwo_csrf=");
  return { cookie, csrf: payload.csrf_token };
}

function request(path: string, session: AccessSession, method = "GET", body?: unknown): Promise<Response> {
  return handleRequest(new Request(`https://control.test${path}`, {
    method,
    headers: {
      Cookie: session.cookie,
      "X-Requested-With": "XMLHttpRequest",
      ...(method === "GET" ? {} : { "X-CSRF-Token": session.csrf, "Content-Type": "application/json" }),
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
    expect(await dashboard.text()).toContain("TTWO — POSITION CONTROL");
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
      quantity_closed: 1, commission: 1, fx_cost: 2.5, actual_fx_rate: 0.92,
    });
    const result = await response.json<Record<string, number | string>>();
    expect(result.state).toBe("PARTIAL_CLOSE");
    expect(result.quantity_remaining).toBe(1);
    const position = await env.DB.prepare("SELECT quantity_initial,quantity_remaining,state,realized_pnl FROM positions").first<Record<string, number | string>>();
    expect(position).toMatchObject({ quantity_initial: 2, quantity_remaining: 1, state: "PARTIAL_CLOSE" });
    expect(position?.realized_pnl).not.toBeNull();
  });
});
