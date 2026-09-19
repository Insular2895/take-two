import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";

import { syntheticDemoDossier } from "../src/demo";
import { classifyLiquidationPnl, evaluateAutomaticPaperExit } from "../src/broker-control";
import { activePosition } from "../src/db";
import { calculateProjection } from "../src/domain";
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

async function prepareClaimedIntent(testEnv: Env, suffix: string) {
  const session = await accessSession(testEnv);
  const dossier = canonicalPaperDossier(suffix);
  expect((await browserRequest(
    testEnv,
    session,
    "/api/positions/import",
    "POST",
    dossier,
  )).status).toBe(201);
  const monitor = testEnv.MONITOR.get(testEnv.MONITOR.idFromName("single-ttwo-position-monitor"));
  expect((await monitor.fetch("https://monitor/run", { method: "POST" })).status).toBe(200);
  expect((await healthyHeartbeat(testEnv)).status).toBe(200);
  expect((await browserRequest(testEnv, session, "/api/broker/control", "POST", {
    mode: "PAPER",
    kill_switch: false,
  })).status).toBe(200);
  expect((await browserRequest(testEnv, session, "/api/broker/exit-policy", "POST", {
    trigger_metric: "LIQUIDATION_PNL_POLICY",
    warning_liquidation_pnl_policy: -200,
    automatic_exit_liquidation_pnl_policy: -300,
    maximum_exit_slippage_policy: 25,
    maximum_quote_age_seconds: 60,
    automatic_exit_enabled: true,
  })).status).toBe(200);
  const preview = await (await browserRequest(
    testEnv,
    session,
    "/api/close-previews",
    "POST",
    { quantity: 2 },
  )).json<{ preview_id: string }>();
  expect((await browserRequest(
    testEnv,
    session,
    `/api/close-previews/${preview.preview_id}/acknowledge`,
    "POST",
    {},
  )).status).toBe(202);
  const claim = await signedBridgeRequest(testEnv, "/internal/broker/intents/claim", {});
  expect(claim.status).toBe(200);
  const claimed = await claim.json<Record<string, any>>();
  return { session, dossier, claimed };
}

describe("isolated IBKR paper control plane", () => {
  it("reports the Paper entry adapter as offline-ready while runtime remains disabled", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const response = await browserRequest(
      testEnv,
      session,
      "/api/broker/paper-entry/status",
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      latest: null,
      execution_environment: "IBKR_PAPER_SIMULATOR",
      paper_adapter_code: "READY_OFFLINE",
      paper_runtime_default: "DISABLED",
      paper_real_order_test: "NOT_RUN",
      live_execution: "FORBIDDEN",
    });
  });

  it("rejects a signed revalidation ticket that weakens safety flags", async () => {
    const testEnv = brokerEnv();
    const ticketJson = JSON.stringify({
      schema_version: "execution-revalidation/1.0",
      execution_environment: "IBKR_PAPER_SIMULATOR",
      human_confirmation_required: false,
      automatic_repricing_allowed: false,
      live_execution_allowed: false,
    });
    const digest = new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(ticketJson)),
    );
    const response = await signedBridgeRequest(testEnv, "/internal/broker/revalidation", {
      ticket_json: ticketJson,
      ticket_hash: hex(digest),
      expires_at: new Date(Date.now() + 60_000).toISOString(),
    });
    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      error: "INVALID_EXECUTION_REVALIDATION_SAFETY_FLAGS",
    });
  });

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
      trigger_metric: "LIQUIDATION_PNL_POLICY",
      warning_liquidation_pnl_policy: -200,
      automatic_exit_liquidation_pnl_policy: -300,
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
      time_in_force: "DAY",
      transmit: false,
      account_guard: { required_prefix: "DU", live_accounts_forbidden: true },
    });
    expect((await signedBridgeRequest(testEnv, "/internal/broker/intents/claim", {})).status).toBe(204);
    expect((await env.DB.prepare("SELECT count(*) AS total FROM broker_execution_intents").first<{ total: number }>())?.total).toBe(1);
  });

  it("queues an automatic floor exit once and blocks an overlapping manual intent", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const automaticDossier = canonicalPaperDossier("automatic");
    automaticDossier.entry_cash_flow_policy = -3000;
    automaticDossier.capital_required_policy = 3000;
    expect((await browserRequest(
      testEnv,
      session,
      "/api/positions/import",
      "POST",
      automaticDossier,
    )).status).toBe(201);
    expect((await healthyHeartbeat(testEnv)).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/control", "POST", {
      mode: "PAPER",
      kill_switch: false,
    })).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/exit-policy", "POST", {
      trigger_metric: "LIQUIDATION_PNL_POLICY",
      warning_liquidation_pnl_policy: -1500,
      automatic_exit_liquidation_pnl_policy: -1525,
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

  it("uses signed liquidation PnL identically for debit and credit structures", () => {
    const projection = (
      liquidationPnl: number | null,
      closeCashFlow: number | null,
      costs: number | null = 0,
    ) => ({
      liquidation_pnl: liquidationPnl,
      estimated_close_cash_flow_policy: closeCashFlow,
      estimated_exit_commission: costs,
      estimated_exit_slippage: costs,
      estimated_exit_fx: costs,
    });

    expect(classifyLiquidationPnl(projection(20, -80), -50, -100)).toBe("HOLD"); // credit profitable
    expect(classifyLiquidationPnl(projection(-60, -160), -50, -100)).toBe("WARNING"); // credit losing
    expect(classifyLiquidationPnl(projection(-120, -220), -50, -100)).toBe("EXIT"); // credit severe loss
    expect(classifyLiquidationPnl(projection(-20, 80), -50, -100)).toBe("HOLD"); // debit profitable
    expect(classifyLiquidationPnl(projection(-60, 40), -50, -100)).toBe("WARNING"); // debit losing

    // A negative close cash flow is economically normal for a credit structure and
    // can never trigger the policy without a breached liquidation PnL threshold.
    expect(classifyLiquidationPnl(projection(20, -10_000), -50, -100)).toBe("HOLD");
    expect(classifyLiquidationPnl(projection(null, -220), -50, -100)).toBe("BLOCKED");
    expect(classifyLiquidationPnl(projection(null, -220, null), -50, -100)).toBe("BLOCKED");
  });

  it("fails closed when migrating a legacy positive-threshold policy", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const dossier = canonicalPaperDossier("legacy-policy");
    expect((await browserRequest(testEnv, session, "/api/positions/import", "POST", dossier)).status).toBe(201);
    const now = new Date().toISOString();
    await testEnv.DB.prepare(
      `INSERT INTO position_exit_policies(
        position_id,mode,policy_currency,warning_net_liquidation_value,
        automatic_exit_net_liquidation_value,maximum_exit_slippage_policy,
        maximum_quote_age_seconds,automatic_exit_enabled,native_protection_required,
        created_at,created_by,updated_at,updated_by
      ) VALUES(?,'PAPER','EUR',900,800,25,30,1,1,?,'legacy',?,'legacy')`,
    ).bind(dossier.position_id, now, now).run();

    // Simulate the data transform contained in migration 0009 for an upgrade DB.
    await testEnv.DB.prepare(
      `INSERT OR IGNORE INTO position_exit_policies_v2(
        position_id,mode,policy_version,trigger_metric,policy_currency,
        warning_liquidation_pnl_policy,automatic_exit_liquidation_pnl_policy,
        maximum_exit_slippage_policy,maximum_quote_age_seconds,automatic_exit_enabled,
        native_protection_required,configuration_status,legacy_policy_detected,
        created_at,created_by,updated_at,updated_by
      ) SELECT position_id,mode,2,'LIQUIDATION_PNL_POLICY',policy_currency,NULL,NULL,
        maximum_exit_slippage_policy,maximum_quote_age_seconds,0,native_protection_required,
        'REQUIRES_EXPLICIT_RECONFIGURATION',1,created_at,created_by,updated_at,updated_by
        FROM position_exit_policies WHERE position_id=?`,
    ).bind(dossier.position_id).run();
    const migrated = await testEnv.DB.prepare(
      "SELECT * FROM position_exit_policies_v2 WHERE position_id=?",
    ).bind(dossier.position_id).first<Record<string, unknown>>();
    expect(migrated).toMatchObject({
      trigger_metric: "LIQUIDATION_PNL_POLICY",
      configuration_status: "REQUIRES_EXPLICIT_RECONFIGURATION",
      legacy_policy_detected: 1,
      automatic_exit_enabled: 0,
      warning_liquidation_pnl_policy: null,
      automatic_exit_liquidation_pnl_policy: null,
    });
  });

  it("blocks automatic exits for every missing-data and operational safety gate", async () => {
    const testEnv = brokerEnv();
    const session = await accessSession(testEnv);
    const dossier = canonicalPaperDossier("blocked-gates");
    dossier.entry_cash_flow_policy = -3000;
    dossier.capital_required_policy = 3000;
    expect((await browserRequest(testEnv, session, "/api/positions/import", "POST", dossier)).status).toBe(201);
    expect((await healthyHeartbeat(testEnv)).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/control", "POST", {
      mode: "PAPER",
      kill_switch: false,
    })).status).toBe(200);
    expect((await browserRequest(testEnv, session, "/api/broker/exit-policy", "POST", {
      trigger_metric: "LIQUIDATION_PNL_POLICY",
      warning_liquidation_pnl_policy: -1500,
      automatic_exit_liquidation_pnl_policy: -1525,
      maximum_exit_slippage_policy: 25,
      maximum_quote_age_seconds: 60,
      automatic_exit_enabled: true,
    })).status).toBe(200);
    const position = await activePosition(testEnv.DB);
    expect(position).not.toBeNull();
    const projection = calculateProjection(
      dossier,
      dossier.last_imported_snapshot!,
      dossier.quantity,
      new Date(),
    );

    expect(await evaluateAutomaticPaperExit(testEnv, position!, {
      ...projection,
      liquidation_pnl: null,
      estimated_exit_commission: null,
    })).toBe("BLOCKED");
    expect(await evaluateAutomaticPaperExit(testEnv, position!, {
      ...projection,
      liquidation_pnl: null,
      estimated_exit_fx: null,
    })).toBe("BLOCKED");
    expect(await evaluateAutomaticPaperExit(testEnv, position!, {
      ...projection,
      data_freshness: "STALE",
    })).toBe("BLOCKED");
    expect(await evaluateAutomaticPaperExit(testEnv, position!, {
      ...projection,
      data_freshness: "INSUFFICIENT_DATA",
    })).toBe("BLOCKED");
    expect(await evaluateAutomaticPaperExit(testEnv, position!, {
      ...projection,
      provider: "SYNTHETIC_TEST",
    })).toBe("BLOCKED");

    const missingConIdDossier = structuredClone(dossier);
    missingConIdDossier.legs[0]!.con_id = null;
    const missingConIdPosition = {
      ...position!,
      canonical_dossier_json: JSON.stringify(missingConIdDossier),
    };
    expect(await evaluateAutomaticPaperExit(
      testEnv,
      missingConIdPosition,
      projection,
    )).toBe("BLOCKED");

    await testEnv.DB.prepare("UPDATE system_state SET broker_kill_switch=1 WHERE singleton=1").run();
    expect(await evaluateAutomaticPaperExit(testEnv, position!, projection)).toBe("BLOCKED");
    await testEnv.DB.prepare(
      "UPDATE system_state SET broker_kill_switch=0,safe_mode=1 WHERE singleton=1",
    ).run();
    expect(await evaluateAutomaticPaperExit(testEnv, position!, projection)).toBe("BLOCKED");
    await testEnv.DB.prepare(
      "UPDATE system_state SET safe_mode=0,broker_mode='DISABLED',broker_kill_switch=1 WHERE singleton=1",
    ).run();
    expect(await evaluateAutomaticPaperExit(testEnv, position!, projection)).toBe("BLOCKED");
    await testEnv.DB.prepare(
      `UPDATE system_state SET broker_mode='PAPER',broker_kill_switch=0,
       broker_bridge_status='OFFLINE' WHERE singleton=1`,
    ).run();
    expect(await evaluateAutomaticPaperExit(testEnv, position!, projection)).toBe("BLOCKED");

    expect((await testEnv.DB.prepare(
      "SELECT count(*) AS total FROM broker_execution_intents",
    ).first<{ total: number }>())?.total).toBe(0);
  });

  it("persists an idempotent working-without-fill diagnosis and exposes exact evidence", async () => {
    const testEnv = brokerEnv();
    const { session, claimed } = await prepareClaimedIntent(testEnv, "working-no-fill");
    const occurredAt = new Date(Date.now() + 1_000).toISOString();
    const event = {
      broker_event_key: "working-no-fill:order-status:1",
      event_type: "ORDER_STATUS",
      occurred_at: occurredAt,
      broker_order_id: 7001,
      broker_perm_id: 9001,
      detail: {
        raw_evidence_hash: "a".repeat(64),
        raw_broker_status: "Submitted",
        canonical_execution_status: "WORKING",
        execution_condition: "WORKING_NO_FILL_YET",
        filled: 0,
        remaining: 2,
        average_fill_price: 0,
        last_fill_price: 0,
        transmitted_to_broker: true,
        time_in_force: "DAY",
      },
    };
    const path = `/internal/broker/intents/${claimed.intent_id}/events`;
    const accepted = await signedBridgeRequest(testEnv, path, event);
    expect(accepted.status).toBe(200);
    expect(await accepted.json()).toMatchObject({
      accepted: true,
      duplicate: false,
      intent_status: "BROKER_ACKNOWLEDGED",
      canonical_execution_status: "WORKING",
    });
    const duplicate = await signedBridgeRequest(testEnv, path, event);
    expect(duplicate.status).toBe(200);
    expect(await duplicate.json()).toMatchObject({ accepted: true, duplicate: true });

    expect(await testEnv.DB.prepare(
      `SELECT canonical_execution_status,execution_condition,raw_broker_status,
       cumulative_filled_quantity,remaining_quantity,transmitted_to_broker,time_in_force
       FROM broker_order_state_latest WHERE intent_id=?`,
    ).bind(claimed.intent_id).first()).toEqual({
      canonical_execution_status: "WORKING",
      execution_condition: "WORKING_NO_FILL_YET",
      raw_broker_status: "Submitted",
      cumulative_filled_quantity: 0,
      remaining_quantity: 2,
      transmitted_to_broker: 1,
      time_in_force: "DAY",
    });
    expect((await testEnv.DB.prepare(
      "SELECT count(*) AS total FROM broker_order_lifecycle_events WHERE broker_event_key=?",
    ).bind(event.broker_event_key).first<{ total: number }>())?.total).toBe(1);

    const status = await (await browserRequest(testEnv, session, "/api/broker/status"))
      .json<Record<string, any>>();
    expect(status.execution.latest).toMatchObject({
      canonical_execution_status: "WORKING",
      execution_condition: "WORKING_NO_FILL_YET",
      raw_broker_status: "Submitted",
    });
    expect(status.execution.timeline.at(-1)).toMatchObject({
      evidence_kind: "ORDER_STATUS",
      canonical_execution_status: "WORKING",
    });
  });

  it("keeps partial and complete executions plus commissions as immutable broker evidence", async () => {
    const testEnv = brokerEnv();
    const { session, claimed } = await prepareClaimedIntent(testEnv, "fills");
    const path = `/internal/broker/intents/${claimed.intent_id}/events`;
    const base = Date.now() + 1_000;
    const partial = {
      broker_event_key: "fill-evidence:partial:1",
      event_type: "EXECUTION",
      occurred_at: new Date(base).toISOString(),
      broker_order_id: 7002,
      broker_perm_id: 9002,
      broker_exec_id: "exec-partial-1",
      detail: {
        raw_evidence_hash: "b".repeat(64),
        raw_broker_status: "Submitted",
        canonical_execution_status: "PARTIALLY_FILLED",
        execution_condition: "PARTIAL_FILL_ACTIVE",
        cumulative_quantity: 1,
        remaining: 1,
        average_fill_price: 7.9,
        last_fill_price: 7.9,
        shares: 1,
        price: 7.9,
        side: "BUY",
        exchange: "CBOE",
        execution_time: new Date(base).toISOString(),
        combo_bid_near_fill: 7.85,
        combo_ask_near_fill: 8.05,
        execution_delay_seconds: 8.2,
        slippage_vs_decision_midpoint: -0.05,
        slippage_vs_executable_quote: 0,
        partial_fill_sequence: 1,
        transmitted_to_broker: true,
      },
    };
    expect((await signedBridgeRequest(testEnv, path, partial)).status).toBe(200);

    const complete = {
      broker_event_key: "fill-evidence:complete:2",
      event_type: "EXECUTION",
      occurred_at: new Date(base + 1_000).toISOString(),
      broker_order_id: 7002,
      broker_perm_id: 9002,
      broker_exec_id: "exec-complete-2",
      detail: {
        raw_evidence_hash: "c".repeat(64),
        raw_broker_status: "Filled",
        canonical_execution_status: "FILLED",
        execution_condition: "NONE",
        cumulative_quantity: 2,
        remaining: 0,
        average_fill_price: 7.95,
        last_fill_price: 8,
        shares: 1,
        price: 8,
        side: "BUY",
        exchange: "CBOE",
        execution_time: new Date(base + 1_000).toISOString(),
        combo_bid_near_fill: 7.9,
        combo_ask_near_fill: 8.1,
        execution_delay_seconds: 9.2,
        slippage_vs_decision_midpoint: 0.05,
        slippage_vs_executable_quote: 0.1,
        partial_fill_sequence: 2,
        transmitted_to_broker: true,
      },
    };
    expect((await signedBridgeRequest(testEnv, path, complete)).status).toBe(200);
    expect((await signedBridgeRequest(testEnv, path, {
      broker_event_key: "fill-evidence:late-working:3",
      event_type: "ORDER_STATUS",
      occurred_at: new Date(base + 1_500).toISOString(),
      broker_order_id: 7002,
      broker_perm_id: 9002,
      detail: {
        raw_evidence_hash: "9".repeat(64),
        raw_broker_status: "Submitted",
        canonical_execution_status: "WORKING",
        execution_condition: "WORKING_NO_FILL_YET",
        filled: 0,
        remaining: 2,
        transmitted_to_broker: true,
        time_in_force: "DAY",
      },
    })).status).toBe(200);
    expect((await signedBridgeRequest(testEnv, path, {
      broker_event_key: "fill-evidence:commission:2",
      event_type: "COMMISSION_REPORT",
      occurred_at: new Date(base + 2_000).toISOString(),
      broker_exec_id: "exec-complete-2",
      detail: {
        raw_evidence_hash: "d".repeat(64),
        commission: 1.2,
        currency: "EUR",
        realized_pnl: -4.5,
      },
    })).status).toBe(200);

    const status = await (await browserRequest(testEnv, session, "/api/broker/status"))
      .json<Record<string, any>>();
    expect(status.execution.latest).toMatchObject({
      canonical_execution_status: "FILLED",
      cumulative_filled_quantity: 2,
      remaining_quantity: 0,
      average_fill_price: 7.95,
    });
    expect(status.execution.executions).toHaveLength(2);
    expect(status.execution.executions[1]).toMatchObject({
      combo_bid_near_fill: 7.9,
      combo_ask_near_fill: 8.1,
      execution_delay_seconds: 9.2,
      partial_fill_sequence: 2,
    });
    expect(status.execution.commissions).toHaveLength(1);
    expect(status.execution.commissions[0]).toMatchObject({
      exec_id: "exec-complete-2",
      commission: 1.2,
      currency: "EUR",
    });
    await expect(testEnv.DB.prepare(
      "UPDATE broker_executions SET price=1 WHERE exec_id='exec-complete-2'",
    ).run()).rejects.toThrow(/append-only/);
  });

  it("classifies broker precaution evidence without inventing a liquidity diagnosis", async () => {
    const testEnv = brokerEnv();
    const { session, claimed } = await prepareClaimedIntent(testEnv, "precaution");
    const path = `/internal/broker/intents/${claimed.intent_id}/events`;
    const event = {
      broker_event_key: "broker-error:price-precaution:109",
      event_type: "ERROR",
      occurred_at: new Date(Date.now() + 1_000).toISOString(),
      broker_order_id: 7003,
      detail: {
        raw_evidence_hash: "e".repeat(64),
        raw_broker_status: "Inactive",
        canonical_execution_status: "REJECTED",
        execution_condition: "NONE",
        transmitted_to_broker: true,
        broker_error_code: 109,
        redacted_broker_message: "Order price outside range for DU123456 token=unsafe-value",
        advanced_rejection_json: "{\"account\":\"DU123456\",\"api_key\":\"unsafe-value\",\"reason\":\"price-range\"}",
        normalized_category: "LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE",
        precaution: true,
        order_rejected: true,
      },
    };
    const response = await signedBridgeRequest(testEnv, path, event);
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      canonical_execution_status: "REJECTED",
      intent_status: "REJECTED",
    });
    const status = await (await browserRequest(testEnv, session, "/api/broker/status"))
      .json<Record<string, any>>();
    expect(status.execution.errors[0]).toMatchObject({
      broker_error_code: 109,
      normalized_category: "LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE",
      precaution: 1,
    });
    expect(status.execution.errors[0].redacted_broker_message).toContain("[REDACTED_ACCOUNT]");
    expect(status.execution.errors[0].redacted_broker_message).toContain("token=[REDACTED]");
    const persisted = await testEnv.DB.prepare(
      "SELECT redacted_broker_message,advanced_rejection_json FROM broker_order_errors WHERE error_event_key=?",
    ).bind(event.broker_event_key).first<Record<string, string>>();
    expect(JSON.stringify(persisted)).not.toContain("DU123456");
    expect(JSON.stringify(persisted)).not.toContain("unsafe-value");
    expect(JSON.stringify(status.execution).toLowerCase()).not.toContain("no liquidity");
    await expect(testEnv.DB.prepare(
      "UPDATE broker_order_errors SET broker_error_code=200 WHERE error_event_key=?",
    ).bind(event.broker_event_key).run()).rejects.toThrow(/append-only/);
  });

  it("blocks a local non-transmitted order before any gateway submission", async () => {
    const testEnv = brokerEnv();
    const { claimed } = await prepareClaimedIntent(testEnv, "local-only");
    const response = await signedBridgeRequest(
      testEnv,
      `/internal/broker/intents/${claimed.intent_id}/events`,
      {
        broker_event_key: "local-order:not-transmitted:1",
        event_type: "LOCAL_NOT_TRANSMITTED",
        occurred_at: new Date(Date.now() + 1_000).toISOString(),
        detail: {
          raw_evidence_hash: "f".repeat(64),
          raw_broker_status: "LOCAL_NOT_TRANSMITTED",
          canonical_execution_status: "LOCAL_NOT_TRANSMITTED",
          execution_condition: "NONE",
          filled: 0,
          remaining: 2,
          transmitted_to_broker: false,
          time_in_force: "DAY",
        },
      },
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toMatchObject({
      intent_status: "BLOCKED",
      canonical_execution_status: "LOCAL_NOT_TRANSMITTED",
    });
    expect(await testEnv.DB.prepare(
      `SELECT canonical_execution_status,transmitted_to_broker
       FROM broker_order_state_latest WHERE intent_id=?`,
    ).bind(claimed.intent_id).first()).toEqual({
      canonical_execution_status: "LOCAL_NOT_TRANSMITTED",
      transmitted_to_broker: 0,
    });
  });

  it("stores an immutable submission snapshot and a preview-only bounded reprice", async () => {
    const testEnv = brokerEnv();
    const { session, claimed } = await prepareClaimedIntent(testEnv, "reprice-preview");
    const path = `/internal/broker/intents/${claimed.intent_id}/events`;
    const base = Date.now() + 1_000;
    expect((await signedBridgeRequest(testEnv, path, {
      broker_event_key: "submission:snapshot:1",
      event_type: "SUBMISSION_ATTEMPTED",
      occurred_at: new Date(base).toISOString(),
      broker_order_id: 7004,
      detail: {
        raw_evidence_hash: "1".repeat(64),
        raw_broker_status: null,
        canonical_execution_status: null,
        execution_condition: "NONE",
        transmitted_to_broker: null,
        market_snapshot: {
          snapshot_timestamp: new Date(base).toISOString(),
          ticker: "SPY",
          candidate_id: "candidate-reprice-preview",
          strategy: "IRON_CONDOR",
          quantity: 2,
          legs: [{ con_id: 101, action: "BUY", ratio: 1 }],
          market_data_type: "LIVE",
          data_freshness: "LIVE",
          combo_bid: 7.9,
          combo_ask: 8.1,
          combo_midpoint: 8,
          synthetic_combo_bid: 7.85,
          synthetic_combo_ask: 8.15,
          signed_price_convention_status: "VERIFIED",
          requested_limit: 7.95,
          cash_flow_type: "CREDIT",
          expected_commission: 2.4,
          capital_required: 500,
          maximum_loss: 500,
          spread_absolute: 0.2,
          spread_percent: 2.5,
          quote_age_seconds: 0.4,
        },
      },
    })).status).toBe(200);

    expect((await signedBridgeRequest(testEnv, path, {
      broker_event_key: "reprice:preview:1",
      event_type: "REPRICE_PROPOSAL",
      occurred_at: new Date(base + 1_000).toISOString(),
      detail: {
        raw_evidence_hash: "2".repeat(64),
        proposal_id: "broker-reprice_preview-1",
        created_at: new Date(base + 1_000).toISOString(),
        status: "READY_FOR_HUMAN_PREVIEW",
        cash_flow_type: "CREDIT",
        current_limit: 7.95,
        proposed_limit: 7.9,
        current_combo_bid: 7.9,
        current_combo_ask: 8.1,
        price_difference: -0.05,
        incremental_capital_impact: 10,
        remaining_hard_budget_headroom: 40,
        authorized_boundary: 7.85,
        new_estimated_pnl_economics: -12.4,
        original_order_shape_hash: "3".repeat(64),
        proposed_order_shape_hash: "3".repeat(64),
        automatic_action_allowed: false,
      },
    })).status).toBe(200);

    const status = await (await browserRequest(testEnv, session, "/api/broker/status"))
      .json<Record<string, any>>();
    expect(status.execution.latest).toMatchObject({
      canonical_execution_status: "CLAIMED",
      transmitted_to_broker: 0,
      broker_submission_attempted_at: new Date(base).toISOString(),
    });
    expect(status.execution.market_snapshot).toMatchObject({
      ticker: "SPY",
      data_freshness: "LIVE",
      requested_limit: 7.95,
      cash_flow_type: "CREDIT",
    });
    expect(status.execution.reprice_proposals[0]).toMatchObject({
      status: "READY_FOR_HUMAN_PREVIEW",
      automatic_action_allowed: 0,
      proposed_limit: 7.9,
      authorized_boundary: 7.85,
    });
    await expect(testEnv.DB.prepare(
      "UPDATE broker_reprice_proposals SET proposed_limit=1 WHERE proposal_id='broker-reprice_preview-1'",
    ).run()).rejects.toThrow(/immutable previews/);
  });
});
