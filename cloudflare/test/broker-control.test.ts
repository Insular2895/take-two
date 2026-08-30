import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { syntheticDemoDossier } from "../src/demo";
import { handleRequest } from "../src/index";

const TEST_ACCESS = {
  aud: "local-take-two-control",
  getIdentity: async () => ({ email: "local-admin@take-two.invalid" }),
} as CloudflareAccessContext;
const ACTION_PASSWORD = "test-action-password-123!";
const BRIDGE_SECRET = "bridge-test-secret-that-is-longer-than-thirty-two-bytes";
const BRIDGE_ID = "oci-a1-paper-01";

function brokerEnv(): Env {
  const result = Object.create(env) as Env;
  Object.defineProperty(result, "BROKER_BRIDGE_SHARED_SECRET", { value: BRIDGE_SECRET });
  return result;
}

async function accessSession(testEnv: Env): Promise<{ cookie: string; csrf: string }> {
  const response = await handleRequest(new Request("https://control.test/api/session"), testEnv, TEST_ACCESS);
  const payload = await response.clone().json<{ csrf_token: string }>();
  return {
    cookie: (response.headers.get("Set-Cookie") ?? "").split(";")[0]!,
    csrf: payload.csrf_token,
  };
}

async function browserRequest(
  testEnv: Env,
  session: { cookie: string; csrf: string },
  path: string,
  method = "GET",
  body?: unknown,
): Promise<Response> {
  return handleRequest(new Request(`https://control.test${path}`, {
    method,
    headers: {
      Cookie: session.cookie,
      "X-Requested-With": "XMLHttpRequest",
      ...(method === "GET" ? {} : {
        "X-CSRF-Token": session.csrf,
        "X-Action-Password": ACTION_PASSWORD,
        "Content-Type": "application/json",
      }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  }), testEnv, TEST_ACCESS);
}

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

async function signedBridgeRequest(
  testEnv: Env,
  path: string,
  body: unknown,
  nonce = crypto.randomUUID().replaceAll("-", ""),
): Promise<Response> {
  const bodyText = JSON.stringify(body);
  const timestamp = String(Math.floor(Date.now() / 1000));
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(bodyText)));
  const canonical = [timestamp, nonce, "POST", path, hex(digest)].join("\n");
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(BRIDGE_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(canonical)));
  return handleRequest(new Request(`https://control.test${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-TTWO-Bridge-Id": BRIDGE_ID,
      "X-TTWO-Bridge-Timestamp": timestamp,
      "X-TTWO-Bridge-Nonce": nonce,
      "X-TTWO-Bridge-Signature": hex(signature),
    },
    body: bodyText,
  }), testEnv, undefined);
}

async function healthyHeartbeat(testEnv: Env): Promise<Response> {
  return signedBridgeRequest(testEnv, "/internal/broker/heartbeat", {
    gateway_connected: true,
    paper_account_verified: true,
    open_intent_count: 0,
    detail: { runtime: "test" },
  });
}

function canonicalPaperDossier(suffix: string) {
  const dossier = syntheticDemoDossier();
  const now = new Date().toISOString();
  dossier.fixture_status = "CANONICAL_EXPORT";
  dossier.dossier_id = `paper-bridge-dossier-${suffix}`;
  dossier.position_id = `paper-bridge-position-${suffix}`;
  dossier.created_at = now;
  dossier.opened_at = now;
  dossier.last_imported_snapshot!.timestamp = now;
  dossier.last_imported_snapshot!.underlying_timestamp = now;
  dossier.last_imported_snapshot!.provider = "IBKR_PAPER_TEST";
  dossier.last_imported_snapshot!.source = "TEST_ONLY";
  dossier.last_imported_snapshot!.quality = "TEST_ONLY";
  dossier.last_imported_snapshot!.synthetic = false;
  dossier.last_imported_snapshot!.fx_timestamp = now;
  dossier.last_imported_snapshot!.combo_quote = {
    price: 7.95,
    cash_flow_type: "CREDIT",
    timestamp: now,
  };
  for (const quote of dossier.last_imported_snapshot!.option_quotes) quote.timestamp = now;
  return dossier;
}

describe("isolated IBKR paper control plane", () => {
  it("starts disabled with its kill switch engaged", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const response = await browserRequest(testEnv, session, "/api/broker/status");
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      mode: "DISABLED",
      kill_switch: true,
      dispatch_ready: false,
      safety: { live_mode_available: false, account_prefix_required: "DU", public_broker_port: false },
    });
  });

  it("authenticates bridge messages and rejects a replayed nonce", async () => {
    const testEnv = brokerEnv();
    const nonce = "fixedreplaynonce1234567890";
    const first = await signedBridgeRequest(testEnv, "/internal/broker/heartbeat", {
      gateway_connected: true,
      paper_account_verified: true,
      open_intent_count: 0,
    }, nonce);
    expect(first.status).toBe(200);
    const replay = await signedBridgeRequest(testEnv, "/internal/broker/heartbeat", {
      gateway_connected: true,
      paper_account_verified: true,
      open_intent_count: 0,
    }, nonce);
    expect(replay.status).toBe(409);
    expect(await replay.json()).toEqual({ error: "BROKER_BRIDGE_REPLAY_DETECTED" });
  });

  it("queues one fresh paper close and claims it exactly once", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const dossier = canonicalPaperDossier("manual");
    expect((await browserRequest(testEnv, session, "/api/positions/import", "POST", dossier)).status).toBe(201);
    const monitor = testEnv.MONITOR.get(testEnv.MONITOR.idFromName("single-ttwo-position-monitor"));
    expect((await monitor.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);

    expect((await healthyHeartbeat(testEnv)).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/control", "POST", {
      mode: "PAPER",
      kill_switch: false,
    })).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/exit-policy", "POST", {
      warning_net_liquidation_value: 900,
      automatic_exit_net_liquidation_value: 800,
      maximum_exit_slippage_policy: 25,
      maximum_quote_age_seconds: 60,
      automatic_exit_enabled: true,
    })).status).toBe(200);

    const previewResponse = await browserRequest(testEnv, session, "/api/close-previews", "POST", { quantity: 2 });
    expect(previewResponse.status).toBe(201);
    const preview = await previewResponse.json<{ preview_id: string }>();
    const confirmed = await browserRequest(
      testEnv,
      session,
      `/api/close-previews/${preview.preview_id}/acknowledge`,
      "POST",
      {},
    );
    expect(confirmed.status).toBe(202);
    expect(await confirmed.json()).toMatchObject({ status: "PAPER_CLOSE_QUEUED", transmitted: false });

    const claim = await signedBridgeRequest(testEnv, "/internal/broker/intents/claim", {});
    expect(claim.status).toBe(200);
    const claimed = await claim.json<Record<string, any>>();
    expect(claimed.status).toBe("CLAIMED");
    expect(claimed.command).toMatchObject({
      mode: "PAPER",
      intent_type: "MANUAL_CLOSE",
      pricing_policy: "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
      account_guard: { required_prefix: "DU", live_accounts_forbidden: true },
    });
    expect((await signedBridgeRequest(testEnv, "/internal/broker/intents/claim", {})).status).toBe(204);
    expect((await env.DB.prepare("SELECT count(*) AS total FROM broker_execution_intents").first<{ total: number }>())?.total).toBe(1);
  });

  it("queues an automatic floor exit once and blocks an overlapping manual intent", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    expect((await browserRequest(
      testEnv,
      session,
      "/api/positions/import",
      "POST",
      canonicalPaperDossier("automatic"),
    )).status).toBe(201);
    expect((await healthyHeartbeat(testEnv)).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/control", "POST", {
      mode: "PAPER",
      kill_switch: false,
    })).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/exit-policy", "POST", {
      warning_net_liquidation_value: 1600,
      automatic_exit_net_liquidation_value: 1500,
      maximum_exit_slippage_policy: 25,
      maximum_quote_age_seconds: 60,
      automatic_exit_enabled: true,
    })).status).toBe(200);
    const monitor = testEnv.MONITOR.get(testEnv.MONITOR.idFromName("single-ttwo-position-monitor"));
    expect((await monitor.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
    expect((await monitor.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
    const intent = await env.DB.prepare(
      "SELECT intent_type,status FROM broker_execution_intents",
    ).first<{ intent_type: string; status: string }>();
    expect(intent).toEqual({ intent_type: "AUTOMATIC_FLOOR_EXIT", status: "READY" });
    expect((await env.DB.prepare(
      "SELECT count(*) AS total FROM broker_execution_intents",
    ).first<{ total: number }>())?.total).toBe(1);

    const preview = await (await browserRequest(
      testEnv,
      session,
      "/api/close-previews",
      "POST",
      { quantity: 2 },
    )).json<{ preview_id: string }>();
    const overlapping = await browserRequest(
      testEnv,
      session,
      `/api/close-previews/${preview.preview_id}/acknowledge`,
      "POST",
      {},
    );
    expect(overlapping.status).toBe(409);
    expect(await overlapping.json()).toEqual({ error: "PAPER_POSITION_INTENT_ALREADY_ACTIVE" });
  });

  it("engages the broker kill switch when SAFE MODE is enabled", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    expect((await browserRequest(testEnv, session, "/api/safe-mode", "POST", { enabled: true })).status).toBe(200);
    const status = await (await browserRequest(testEnv, session, "/api/broker/status")).json<Record<string, unknown>>();
    expect(status.kill_switch).toBe(true);
    expect(status.dispatch_ready).toBe(false);
  });
});
