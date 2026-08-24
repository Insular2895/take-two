import { env, SELF } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { syntheticDemoDossier } from "../src/demo";

interface LoginSession {
  cookie: string;
  csrf: string;
}

async function login(password = "test-password"): Promise<{ response: Response; session: LoginSession | null }> {
  const response = await SELF.fetch("https://control.test/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json", "CF-Connecting-IP": "192.0.2.10" },
    body: JSON.stringify({ username: "admin", password }),
  });
  if (!response.ok) return { response, session: null };
  const payload = await response.clone().json<{ csrf_token: string }>();
  const cookie = (response.headers.get("Set-Cookie") ?? "").split(";")[0]!;
  return { response, session: { cookie, csrf: payload.csrf_token } };
}

function request(path: string, session: LoginSession, method = "GET", body?: unknown): Promise<Response> {
  return SELF.fetch(`https://control.test${path}`, {
    method,
    headers: {
      Cookie: session.cookie,
      ...(method === "GET" ? {} : { "X-CSRF-Token": session.csrf, "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}

async function importAndMonitor(session: LoginSession): Promise<void> {
  expect((await request("/api/demo/import", session, "POST", {})).status).toBe(201);
  const stub = env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
  expect((await stub.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
}

describe("private authentication boundary", () => {
  it("reveals no dashboard or API data without login", async () => {
    const dashboard = await SELF.fetch("https://control.test/dashboard");
    expect(dashboard.status).toBe(200);
    expect(await dashboard.text()).toContain("Accès privé");
    const api = await SELF.fetch("https://control.test/api/dashboard");
    expect(api.status).toBe(401);
    expect(await api.json()).toEqual({ error: "UNAUTHORIZED" });
  });

  it("rejects a wrong password and accepts the configured password", async () => {
    expect((await login("wrong-password")).response.status).toBe(401);
    const success = await login();
    expect(success.response.status).toBe(200);
    expect(success.response.headers.get("Set-Cookie")).toContain("HttpOnly; Secure; SameSite=Strict");
    const dashboard = await request("/dashboard", success.session!);
    expect(dashboard.status).toBe(200);
    expect(await dashboard.text()).toContain("TTWO — POSITION CONTROL");
  });

  it("rate limits after five failures in ten minutes", async () => {
    for (let index = 0; index < 5; index += 1) expect((await login("wrong-password")).response.status).toBe(401);
    expect((await login("wrong-password")).response.status).toBe(429);
  });

  it("enforces CSRF, session expiry, and logout", async () => {
    const { session } = await login();
    expect(session).not.toBeNull();
    const csrfFailure = await SELF.fetch("https://control.test/api/safe-mode", {
      method: "POST", headers: { Cookie: session!.cookie, "Content-Type": "application/json" }, body: "{\"enabled\":true}",
    });
    expect(csrfFailure.status).toBe(403);
    expect((await request("/api/logout", session!, "POST", {})).status).toBe(200);
    expect((await request("/api/dashboard", session!)).status).toBe(401);

    const second = (await login()).session!;
    await env.DB.prepare("UPDATE sessions SET expires_at=?").bind("2020-01-01T00:00:00.000Z").run();
    expect((await request("/api/dashboard", second)).status).toBe(401);
  });
});

describe("D1 persistence and Durable Object monitoring", () => {
  it("survives independent requests with position, history, SAFE MODE, preview, and audit", async () => {
    const session = (await login()).session!;
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
  });

  it("is idempotent for duplicate/concurrent alarm requests and retains data on provider absence", async () => {
    const session = (await login()).session!;
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
    const session = (await login()).session!;
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
    const session = (await login()).session!;
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
  it("requires sensitive re-authentication and never transmits", async () => {
    const session = (await login()).session!;
    await importAndMonitor(session);
    const preview = await (await request("/api/close-previews", session, "POST", { quantity: 2 })).json<Record<string, any>>();
    expect(preview.safety).toEqual({ transmit: false, what_if: true, order_capability: "forbidden", security_type: "BAG" });
    expect(preview.legs.map((leg: { action: string }) => leg.action)).toEqual(["SELL_TO_CLOSE", "BUY_TO_CLOSE"]);
    await env.DB.prepare("UPDATE sessions SET sensitive_authenticated_at=?").bind("2020-01-01T00:00:00.000Z").run();
    expect((await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {})).status).toBe(403);
    expect((await request("/api/reauth", session, "POST", { password: "test-password" })).status).toBe(200);
    const acknowledged = await request(`/api/close-previews/${preview.preview_id}/acknowledge`, session, "POST", {});
    expect(acknowledged.status).toBe(200);
    expect(await acknowledged.json()).toMatchObject({ status: "CLOSE_PREVIEW_READY", transmitted: false });
  });

  it("persists the €432 estimate, €417 actual result, and -€15 error", async () => {
    const session = (await login()).session!;
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
    const session = (await login()).session!;
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
