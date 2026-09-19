import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { handleRequest } from "../src/index";

const TEST_ACCESS = {
  aud: "local-take-two-control",
  getIdentity: async () => ({ email: "local-admin@take-two.invalid" }),
} as CloudflareAccessContext;
const TELEMETRY_SECRET = "telemetry-test-secret-that-is-longer-than-thirty-two-bytes";
const BRIDGE_SECRET = "bridge-test-secret-that-is-longer-than-thirty-two-bytes";
const TELEMETRY_ID = "oci-a1-paper-telemetry-01";

function telemetryEnv(): Env {
  const result = Object.create(env) as Env;
  Object.defineProperty(result, "BROKER_TELEMETRY_SHARED_SECRET", { value: TELEMETRY_SECRET });
  Object.defineProperty(result, "BROKER_TELEMETRY_ID", { value: TELEMETRY_ID });
  Object.defineProperty(result, "BROKER_BRIDGE_SHARED_SECRET", { value: BRIDGE_SECRET });
  Object.defineProperty(result, "BROKER_BRIDGE_ID", { value: "oci-a1-paper-01" });
  return result;
}

async function accessSession(testEnv: Env): Promise<{ cookie: string }> {
  const response = await handleRequest(new Request("https://control.test/api/session"), testEnv, TEST_ACCESS);
  return { cookie: (response.headers.get("Set-Cookie") ?? "").split(";")[0]! };
}

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

async function signedRequest(
  testEnv: Env,
  path: string,
  body: unknown,
  options: { secret?: string; nonce?: string; telemetryHeaders?: boolean } = {},
): Promise<Response> {
  const bodyText = JSON.stringify(body);
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = options.nonce ?? crypto.randomUUID().replaceAll("-", "");
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(bodyText)));
  const canonical = [timestamp, nonce, "POST", path, hex(digest)].join("\n");
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(options.secret ?? TELEMETRY_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = hex(new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(canonical))));
  const telemetryHeaders = options.telemetryHeaders !== false;
  return handleRequest(new Request(`https://control.test${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(telemetryHeaders ? {
        "X-TTWO-Telemetry-Id": TELEMETRY_ID,
        "X-TTWO-Telemetry-Timestamp": timestamp,
        "X-TTWO-Telemetry-Nonce": nonce,
        "X-TTWO-Telemetry-Signature": signature,
      } : {
        "X-TTWO-Bridge-Id": "oci-a1-paper-01",
        "X-TTWO-Bridge-Timestamp": timestamp,
        "X-TTWO-Bridge-Nonce": nonce,
        "X-TTWO-Bridge-Signature": signature,
      }),
    },
    body: bodyText,
  }), testEnv, undefined);
}

function telemetryPayload(): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    mode: "PAPER_READ_ONLY",
    gateway_connected: true,
    paper_account_verified: true,
    account_count: 1,
    symbol: "TTWO",
    server_time: now,
    collected_at: now,
    positions: [{
      con_id: 101,
      security_type: "OPT",
      local_symbol: "TTWO  270115C00250000",
      currency: "USD",
      expiry: "20270115",
      strike: "250",
      right: "C",
      multiplier: "100",
      quantity: "2",
      average_cost: "550.25",
      market_value: "1250",
      daily_pnl: "20",
      unrealized_pnl: "125",
      realized_pnl: "0",
      quote: {
        bid: "6.10",
        ask: "6.40",
        last: "6.25",
        close: "6.00",
        mark: "6.25",
        midpoint: "6.25",
        market_data_type: "REALTIME",
        observed_at: now,
        bid_ask_complete: true,
      },
    }],
    totals: { market_value: "1250", daily_pnl: "20", unrealized_pnl: "125", realized_pnl: "0" },
    quotes_complete: true,
    pnl_complete: true,
    fee_reconciliation_status: "LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES",
    error_codes: [2104, 2106],
  };
}

describe("IBKR Paper read-only telemetry", () => {
  it("is absent by default and never claims execution capability", async () => {
    const testEnv = telemetryEnv();
    const session = await accessSession(testEnv);
    const response = await handleRequest(new Request("https://control.test/api/broker/telemetry", {
      headers: { Cookie: session.cookie, "X-Requested-With": "XMLHttpRequest" },
    }), testEnv, TEST_ACCESS);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      status: "NOT_CONFIGURED",
      received_at: null,
      telemetry: null,
      execution_enabled: false,
    });
  });

  it("accepts, replaces and serves a strictly redacted signed snapshot", async () => {
    const testEnv = telemetryEnv();
    const first = await signedRequest(testEnv, "/internal/broker/telemetry", telemetryPayload());
    expect(first.status).toBe(200);
    expect(await first.json()).toMatchObject({ accepted: true, telemetry_status: "FRESH", position_count: 1 });
    expect((await signedRequest(testEnv, "/internal/broker/telemetry", telemetryPayload())).status).toBe(200);
    expect((await env.DB.prepare("SELECT count(*) AS total FROM broker_telemetry_latest")
      .first<{ total: number }>())?.total).toBe(1);

    const session = await accessSession(testEnv);
    const response = await handleRequest(new Request("https://control.test/api/broker/telemetry", {
      headers: { Cookie: session.cookie, "X-Requested-With": "XMLHttpRequest" },
    }), testEnv, TEST_ACCESS);
    const payload = await response.json<Record<string, any>>();
    expect(payload).toMatchObject({
      status: "FRESH",
      execution_enabled: false,
      telemetry: {
        mode: "PAPER_READ_ONLY",
        symbol: "TTWO",
        totals: { unrealized_pnl: "125" },
      },
    });
    expect(JSON.stringify(payload)).not.toContain("DU");
    expect(JSON.stringify(payload).toLowerCase()).not.toContain("account_identifier");
  });

  it("rejects replay, extra identity fields and inconsistent totals", async () => {
    const testEnv = telemetryEnv();
    const nonce = "fixedtelemetrynonce1234567890";
    expect((await signedRequest(testEnv, "/internal/broker/telemetry", telemetryPayload(), { nonce })).status).toBe(200);
    const replay = await signedRequest(testEnv, "/internal/broker/telemetry", telemetryPayload(), { nonce });
    expect(replay.status).toBe(409);
    expect(await replay.json()).toEqual({ error: "BROKER_TELEMETRY_REPLAY_DETECTED" });

    const identity = telemetryPayload();
    identity.account_identifier = "FORBIDDEN";
    expect((await signedRequest(testEnv, "/internal/broker/telemetry", identity)).status).toBe(400);

    const inconsistent = telemetryPayload();
    (inconsistent.totals as Record<string, unknown>).unrealized_pnl = "999";
    expect((await signedRequest(testEnv, "/internal/broker/telemetry", inconsistent)).status).toBe(400);
  });

  it("does not accept bridge HMAC on telemetry or telemetry HMAC on claim routes", async () => {
    const testEnv = telemetryEnv();
    const wrongTelemetrySecret = await signedRequest(
      testEnv,
      "/internal/broker/telemetry",
      telemetryPayload(),
      { secret: BRIDGE_SECRET },
    );
    expect(wrongTelemetrySecret.status).toBe(403);
    expect(await wrongTelemetrySecret.json()).toEqual({ error: "INVALID_BROKER_TELEMETRY_SIGNATURE" });

    const telemetryCredentialOnClaim = await signedRequest(
      testEnv,
      "/internal/broker/intents/claim",
      {},
    );
    expect(telemetryCredentialOnClaim.status).toBe(403);
    expect(await telemetryCredentialOnClaim.json()).toEqual({ error: "INVALID_BROKER_BRIDGE_ID" });
  });

  it("marks an old last-received snapshot offline", async () => {
    const testEnv = telemetryEnv();
    expect((await signedRequest(testEnv, "/internal/broker/telemetry", telemetryPayload())).status).toBe(200);
    await env.DB.prepare("UPDATE broker_telemetry_latest SET received_at=?")
      .bind(new Date(Date.now() - 10 * 60_000).toISOString()).run();
    const session = await accessSession(testEnv);
    const response = await handleRequest(new Request("https://control.test/api/broker/telemetry", {
      headers: { Cookie: session.cookie, "X-Requested-With": "XMLHttpRequest" },
    }), testEnv, TEST_ACCESS);
    expect((await response.json<Record<string, unknown>>()).status).toBe("OFFLINE");
  });
});
