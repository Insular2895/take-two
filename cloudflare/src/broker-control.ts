import { hasFreshSensitiveAuth, requireActionPassword, requireCsrf } from "./auth";
import { verifyBridgeRequest } from "./broker-security";
import { activePosition, audit } from "./db";
import type { PositionRow } from "./db";
import { inverseStructureLegs, randomId, validateDossier } from "./domain";
import type { AuthContext, PnlProjection } from "./types";

const BRIDGE_FRESHNESS_MS = 90_000;
const CLAIM_LEASE_MS = 45_000;

interface BrokerStateRow {
  safe_mode: number;
  broker_mode: "DISABLED" | "PAPER";
  broker_kill_switch: number;
  broker_bridge_status: "NOT_CONFIGURED" | "OFFLINE" | "HEALTHY" | "DEGRADED";
  broker_last_heartbeat: string | null;
  broker_bridge_id: string | null;
}

interface ExitPolicyBody {
  warning_net_liquidation_value?: number;
  automatic_exit_net_liquidation_value?: number;
  maximum_exit_slippage_policy?: number;
  maximum_quote_age_seconds?: number;
  automatic_exit_enabled?: boolean;
}

interface BridgeEventBody {
  broker_event_key?: string;
  event_type?: string;
  occurred_at?: string;
  broker_order_id?: number | null;
  broker_perm_id?: number | null;
  broker_exec_id?: string | null;
  detail?: Record<string, unknown>;
}

function parseBody<T>(text: string): T {
  try {
    const value = JSON.parse(text) as T;
    if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error();
    return value;
  } catch {
    throw new Error("INVALID_BROKER_BRIDGE_JSON");
  }
}

async function brokerState(db: D1Database): Promise<BrokerStateRow> {
  const state = await db.prepare(
    `SELECT safe_mode,broker_mode,broker_kill_switch,broker_bridge_status,
     broker_last_heartbeat,broker_bridge_id FROM system_state WHERE singleton=1`,
  ).first<BrokerStateRow>();
  if (!state) throw new Error("BROKER_CONTROL_STATE_MISSING");
  return state;
}

function heartbeatIsFresh(state: BrokerStateRow, now = Date.now()): boolean {
  return state.broker_bridge_status === "HEALTHY" && state.broker_last_heartbeat !== null &&
    Number.isFinite(Date.parse(state.broker_last_heartbeat)) &&
    now - Date.parse(state.broker_last_heartbeat) <= BRIDGE_FRESHNESS_MS;
}

async function brokerStatus(env: Env): Promise<Response> {
  const state = await brokerState(env.DB);
  const position = await activePosition(env.DB);
  const policy = position
    ? await env.DB.prepare("SELECT * FROM position_exit_policies WHERE position_id=?")
      .bind(position.id).first<Record<string, unknown>>()
    : null;
  const intents = position
    ? await env.DB.prepare(
      `SELECT intent_id,intent_type,status,requested_quantity,order_ref,created_at,expires_at,
       attempt_count,broker_order_id,broker_perm_id,completed_at,last_error_code
       FROM broker_execution_intents WHERE position_id=? ORDER BY created_at DESC LIMIT 20`,
    ).bind(position.id).all<Record<string, unknown>>()
    : { results: [] };
  return Response.json({
    mode: state.broker_mode,
    kill_switch: Boolean(state.broker_kill_switch),
    bridge_status: heartbeatIsFresh(state) ? "HEALTHY" : state.broker_bridge_status === "NOT_CONFIGURED" ? "NOT_CONFIGURED" : "OFFLINE",
    last_heartbeat: state.broker_last_heartbeat,
    bridge_id: state.broker_bridge_id,
    dispatch_ready: state.broker_mode === "PAPER" && !state.safe_mode &&
      !state.broker_kill_switch && heartbeatIsFresh(state),
    active_position_id: position?.id ?? null,
    exit_policy: policy,
    recent_intents: intents.results,
    safety: { live_mode_available: false, account_prefix_required: "DU", public_broker_port: false },
  });
}

async function configureBrokerControl(
  request: Request,
  env: Env,
  auth: AuthContext,
  body: unknown,
): Promise<Response> {
  requireCsrf(request, auth);
  if (!hasFreshSensitiveAuth(auth)) return Response.json({ error: "SENSITIVE_ACCESS_REAUTH_REQUIRED" }, { status: 403 });
  await requireActionPassword(request, env, auth, "CONFIGURE_PAPER_BROKER_CONTROL");
  const value = body as { mode?: unknown; kill_switch?: unknown };
  if (!value || !["DISABLED", "PAPER"].includes(String(value.mode)) || typeof value.kill_switch !== "boolean") {
    throw new Error("INVALID_BROKER_CONTROL_VALUE");
  }
  const mode = String(value.mode) as "DISABLED" | "PAPER";
  const killSwitch = mode === "DISABLED" ? true : value.kill_switch;
  const state = await brokerState(env.DB);
  if (mode === "PAPER" && !killSwitch) {
    if (!env.BROKER_BRIDGE_SHARED_SECRET || env.BROKER_BRIDGE_SHARED_SECRET.trim().length < 32) {
      throw new Error("BROKER_BRIDGE_SECRET_NOT_CONFIGURED");
    }
    if (!heartbeatIsFresh(state)) return Response.json({ error: "BROKER_BRIDGE_NOT_HEALTHY" }, { status: 409 });
  }
  const now = new Date().toISOString();
  await env.DB.prepare(
    "UPDATE system_state SET broker_mode=?,broker_kill_switch=?,updated_at=? WHERE singleton=1",
  ).bind(mode, killSwitch ? 1 : 0, now).run();
  await audit(env.DB, "BROKER_CONTROL_CHANGED", auth.actor, null, { mode, kill_switch: killSwitch });
  return Response.json({ mode, kill_switch: killSwitch, live_mode_available: false });
}

async function configureExitPolicy(
  request: Request,
  env: Env,
  auth: AuthContext,
  body: ExitPolicyBody,
): Promise<Response> {
  requireCsrf(request, auth);
  if (!hasFreshSensitiveAuth(auth)) return Response.json({ error: "SENSITIVE_ACCESS_REAUTH_REQUIRED" }, { status: 403 });
  await requireActionPassword(request, env, auth, "CONFIGURE_PAPER_EXIT_POLICY");
  const position = await activePosition(env.DB);
  if (!position) return Response.json({ error: "NO_ACTIVE_POSITION" }, { status: 409 });
  if (position.state !== "PAPER_OPEN" && position.state !== "PARTIAL_CLOSE") {
    return Response.json({ error: "PAPER_POSITION_REQUIRED" }, { status: 409 });
  }
  const warning = body.warning_net_liquidation_value;
  const exit = body.automatic_exit_net_liquidation_value;
  const slippage = body.maximum_exit_slippage_policy;
  const quoteAge = body.maximum_quote_age_seconds ?? 30;
  if (![warning, exit, slippage].every((item) => typeof item === "number" && Number.isFinite(item)) ||
      warning! < 0 || exit! < 0 || warning! < exit! || slippage! < 0 ||
      !Number.isInteger(quoteAge) || quoteAge < 5 || quoteAge > 60 ||
      typeof body.automatic_exit_enabled !== "boolean") {
    throw new Error("INVALID_EXIT_POLICY");
  }
  const now = new Date().toISOString();
  await env.DB.prepare(
    `INSERT INTO position_exit_policies(
      position_id,mode,policy_currency,warning_net_liquidation_value,
      automatic_exit_net_liquidation_value,maximum_exit_slippage_policy,
      maximum_quote_age_seconds,automatic_exit_enabled,native_protection_required,
      created_at,created_by,updated_at,updated_by
    ) VALUES(?,'PAPER',?,?,?,?,?,?,1,?,?,?,?)
    ON CONFLICT(position_id) DO UPDATE SET
      warning_net_liquidation_value=excluded.warning_net_liquidation_value,
      automatic_exit_net_liquidation_value=excluded.automatic_exit_net_liquidation_value,
      maximum_exit_slippage_policy=excluded.maximum_exit_slippage_policy,
      maximum_quote_age_seconds=excluded.maximum_quote_age_seconds,
      automatic_exit_enabled=excluded.automatic_exit_enabled,
      updated_at=excluded.updated_at,updated_by=excluded.updated_by`,
  ).bind(
    position.id, position.policy_currency, warning, exit, slippage, quoteAge,
    body.automatic_exit_enabled ? 1 : 0, now, auth.actor, now, auth.actor,
  ).run();
  await audit(env.DB, "PAPER_EXIT_POLICY_CONFIGURED", auth.actor, position.id, {
    warning_net_liquidation_value: warning,
    automatic_exit_net_liquidation_value: exit,
    maximum_exit_slippage_policy: slippage,
    maximum_quote_age_seconds: quoteAge,
    automatic_exit_enabled: body.automatic_exit_enabled,
  });
  return Response.json({ configured: true, position_id: position.id, mode: "PAPER" });
}

export async function queueAcknowledgedPaperClose(
  env: Env,
  auth: AuthContext,
  previewId: string,
): Promise<Record<string, unknown> | null> {
  const state = await brokerState(env.DB);
  if (state.broker_mode === "DISABLED") return null;
  if (state.safe_mode || state.broker_kill_switch || !heartbeatIsFresh(state)) {
    throw new Error("PAPER_BROKER_DISPATCH_BLOCKED");
  }
  const preview = await env.DB.prepare(
    `SELECT cp.*,p.state AS position_state,p.ticker,p.native_currency,p.policy_currency,
     p.quantity_remaining FROM close_previews cp JOIN positions p ON p.id=cp.position_id
     WHERE cp.preview_id=?`,
  ).bind(previewId).first<Record<string, unknown>>();
  if (!preview || preview.status !== "ACKNOWLEDGED") throw new Error("ACKNOWLEDGED_PREVIEW_REQUIRED");
  if (!["PAPER_OPEN", "PARTIAL_CLOSE"].includes(String(preview.position_state))) {
    throw new Error("PAPER_POSITION_REQUIRED");
  }
  const policy = await env.DB.prepare("SELECT * FROM position_exit_policies WHERE position_id=?")
    .bind(String(preview.position_id)).first<Record<string, unknown>>();
  if (!policy) throw new Error("PAPER_EXIT_POLICY_REQUIRED");
  const quoteTimestamp = Date.parse(String(preview.quote_timestamp));
  if (!Number.isFinite(quoteTimestamp) || Date.now() - quoteTimestamp > Number(policy.maximum_quote_age_seconds) * 1000) {
    throw new Error("PAPER_CLOSE_QUOTE_STALE");
  }
  if (String(preview.quote_provider).toUpperCase().includes("SYNTHETIC")) {
    throw new Error("PAPER_CLOSE_SYNTHETIC_DATA_FORBIDDEN");
  }
  const legs = JSON.parse(String(preview.legs_json)) as Array<Record<string, unknown>>;
  if (!Array.isArray(legs) || legs.length === 0 || legs.some((leg) => !Number.isInteger(leg.con_id) || Number(leg.con_id) <= 0)) {
    throw new Error("PAPER_CLOSE_CONTRACT_IDS_REQUIRED");
  }
  const intentId = randomId("broker-intent");
  const orderRef = `TTWO-P-${intentId.slice(-24)}`;
  const createdAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + Number(policy.maximum_quote_age_seconds) * 1000).toISOString();
  const command = {
    schema_version: "1.0",
    intent_id: intentId,
    intent_type: "MANUAL_CLOSE",
    mode: "PAPER",
    account_guard: { required_prefix: "DU", live_accounts_forbidden: true },
    position_id: preview.position_id,
    preview_id: previewId,
    order_ref: orderRef,
    ticker: preview.ticker,
    native_currency: preview.native_currency,
    requested_quantity: preview.quantity,
    legs,
    quote_timestamp: preview.quote_timestamp,
    quote_provider: preview.quote_provider,
    estimated_close_cash_flow_policy: preview.estimated_close_cash_flow_policy,
    estimated_commission_policy: preview.estimated_commission,
    estimated_slippage_policy: preview.estimated_slippage,
    maximum_exit_slippage_policy: policy.maximum_exit_slippage_policy,
    pricing_policy: "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
  };
  await env.DB.prepare(
    `INSERT OR IGNORE INTO broker_execution_intents(
      intent_id,idempotency_key,position_id,preview_id,intent_type,mode,status,
      requested_quantity,order_ref,command_json,source_actor,created_at,expires_at
    ) VALUES(?, ?, ?, ?, 'MANUAL_CLOSE', 'PAPER', 'READY', ?, ?, ?, ?, ?, ?)`,
  ).bind(
    intentId, `manual-close:${previewId}`, preview.position_id, previewId, preview.quantity,
    orderRef, JSON.stringify(command), auth.actor, createdAt, expiresAt,
  ).run();
  const stored = await env.DB.prepare(
    "SELECT intent_id,status,order_ref,created_at,expires_at FROM broker_execution_intents WHERE idempotency_key=?",
  ).bind(`manual-close:${previewId}`).first<Record<string, unknown>>();
  if (!stored) throw new Error("PAPER_POSITION_INTENT_ALREADY_ACTIVE");
  await audit(env.DB, "PAPER_CLOSE_QUEUED", auth.actor, String(preview.position_id), {
    preview_id: previewId,
    intent_id: stored?.intent_id,
    order_ref: stored?.order_ref,
  });
  return { ...stored, mode: "PAPER", live_mode_available: false };
}

export type AutomaticExitEvaluation = "NOT_CONFIGURED" | "HOLD" | "WARNING" | "QUEUED" | "BLOCKED";

export async function evaluateAutomaticPaperExit(
  env: Env,
  position: PositionRow,
  projection: PnlProjection,
): Promise<AutomaticExitEvaluation> {
  if (position.state !== "PAPER_OPEN" && position.state !== "PARTIAL_CLOSE") return "NOT_CONFIGURED";
  const policy = await env.DB.prepare("SELECT * FROM position_exit_policies WHERE position_id=?")
    .bind(position.id).first<Record<string, unknown>>();
  if (!policy || !policy.automatic_exit_enabled) return "NOT_CONFIGURED";
  if (projection.data_freshness !== "FRESH" || projection.estimated_close_cash_flow_policy === null) return "BLOCKED";

  const currentValue = projection.estimated_close_cash_flow_policy;
  const warningFloor = Number(policy.warning_net_liquidation_value);
  const exitFloor = Number(policy.automatic_exit_net_liquidation_value);
  if (currentValue > warningFloor) return "HOLD";
  if (currentValue > exitFloor) {
    await audit(env.DB, "PAPER_EXIT_FLOOR_WARNING", "monitor", position.id, {
      current_net_liquidation_value: currentValue,
      warning_net_liquidation_value: warningFloor,
      automatic_exit_net_liquidation_value: exitFloor,
    }, `paper-floor-warning:${position.id}:${projection.timestamp}`);
    return "WARNING";
  }

  const state = await brokerState(env.DB);
  if (state.broker_mode !== "PAPER" || state.safe_mode || state.broker_kill_switch || !heartbeatIsFresh(state)) {
    await audit(env.DB, "PAPER_AUTOMATIC_EXIT_BLOCKED", "monitor", position.id, {
      safe_mode: Boolean(state.safe_mode),
      kill_switch: Boolean(state.broker_kill_switch),
      bridge_healthy: heartbeatIsFresh(state),
    }, `paper-auto-blocked:${position.id}:${projection.timestamp}`);
    return "BLOCKED";
  }
  if (String(projection.provider).toUpperCase().includes("SYNTHETIC")) return "BLOCKED";
  if ((projection.required_data_freshness.age_seconds ?? Number.POSITIVE_INFINITY) > Number(policy.maximum_quote_age_seconds)) {
    return "BLOCKED";
  }
  const dossier = validateDossier(JSON.parse(position.canonical_dossier_json));
  const legs = inverseStructureLegs(dossier, position.quantity_remaining);
  if (legs.some((leg) => !Number.isInteger(leg.con_id) || Number(leg.con_id) <= 0)) return "BLOCKED";

  const intentId = randomId("broker-intent");
  const orderRef = `TTWO-P-${intentId.slice(-24)}`;
  const createdAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + Number(policy.maximum_quote_age_seconds) * 1000).toISOString();
  const idempotencyKey = `automatic-floor:${position.id}:${policy.updated_at}`;
  const command = {
    schema_version: "1.0",
    intent_id: intentId,
    intent_type: "AUTOMATIC_FLOOR_EXIT",
    mode: "PAPER",
    account_guard: { required_prefix: "DU", live_accounts_forbidden: true },
    position_id: position.id,
    preview_id: null,
    order_ref: orderRef,
    ticker: position.ticker,
    native_currency: position.native_currency,
    requested_quantity: position.quantity_remaining,
    legs,
    quote_timestamp: projection.required_data_freshness.effective_timestamp,
    quote_provider: projection.provider,
    estimated_close_cash_flow_policy: currentValue,
    estimated_commission_policy: projection.estimated_exit_commission,
    estimated_slippage_policy: projection.estimated_exit_slippage,
    maximum_exit_slippage_policy: policy.maximum_exit_slippage_policy,
    trigger: {
      kind: "NET_LIQUIDATION_VALUE_FLOOR",
      observed_value: currentValue,
      configured_floor: exitFloor,
    },
    pricing_policy: "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
  };
  const inserted = await env.DB.prepare(
    `INSERT OR IGNORE INTO broker_execution_intents(
      intent_id,idempotency_key,position_id,preview_id,intent_type,mode,status,
      requested_quantity,order_ref,command_json,source_actor,created_at,expires_at
    ) VALUES(?, ?, ?, NULL, 'AUTOMATIC_FLOOR_EXIT', 'PAPER', 'READY', ?, ?, ?, 'monitor', ?, ?)`,
  ).bind(
    intentId, idempotencyKey, position.id, position.quantity_remaining, orderRef,
    JSON.stringify(command), createdAt, expiresAt,
  ).run();
  if (inserted.meta.changes) {
    await audit(env.DB, "PAPER_AUTOMATIC_EXIT_QUEUED", "monitor", position.id, {
      intent_id: intentId,
      current_net_liquidation_value: currentValue,
      automatic_exit_net_liquidation_value: exitFloor,
    });
    return "QUEUED";
  }
  const duplicate = await env.DB.prepare(
    "SELECT intent_id FROM broker_execution_intents WHERE idempotency_key=?",
  ).bind(idempotencyKey).first<{ intent_id: string }>();
  return duplicate ? "QUEUED" : "BLOCKED";
}

async function recordHeartbeat(env: Env, bridgeId: string, receivedAt: string, bodyText: string): Promise<Response> {
  const body = parseBody<{
    gateway_connected?: boolean;
    paper_account_verified?: boolean;
    open_intent_count?: number;
    detail?: Record<string, unknown>;
  }>(bodyText);
  if (typeof body.gateway_connected !== "boolean" || typeof body.paper_account_verified !== "boolean" ||
      !Number.isInteger(body.open_intent_count) || Number(body.open_intent_count) < 0) {
    throw new Error("INVALID_BROKER_HEARTBEAT");
  }
  const status = body.gateway_connected && body.paper_account_verified ? "HEALTHY" : "DEGRADED";
  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO broker_bridge_heartbeats(
        heartbeat_id,bridge_id,received_at,gateway_connected,paper_account_verified,open_intent_count,detail_json
      ) VALUES(?,?,?,?,?,?,?)`,
    ).bind(
      randomId("broker-heartbeat"), bridgeId, receivedAt, body.gateway_connected ? 1 : 0,
      body.paper_account_verified ? 1 : 0, body.open_intent_count, JSON.stringify(body.detail ?? {}),
    ),
    env.DB.prepare(
      "UPDATE system_state SET broker_bridge_status=?,broker_last_heartbeat=?,broker_bridge_id=?,updated_at=? WHERE singleton=1",
    ).bind(status, receivedAt, bridgeId, receivedAt),
  ]);
  return Response.json({ accepted: true, bridge_status: status });
}

async function claimNextIntent(env: Env, bridgeId: string, receivedAt: string): Promise<Response> {
  const state = await brokerState(env.DB);
  if (state.broker_mode !== "PAPER" || state.safe_mode || state.broker_kill_switch || !heartbeatIsFresh(state) || state.broker_bridge_id !== bridgeId) {
    return Response.json({ error: "PAPER_BROKER_DISPATCH_BLOCKED" }, { status: 409 });
  }
  await env.DB.prepare(
    `UPDATE broker_execution_intents SET status='AMBIGUOUS',completed_at=?,last_error_code='CLAIM_LEASE_EXPIRED'
     WHERE status='CLAIMED' AND claim_expires_at < ?`,
  ).bind(receivedAt, receivedAt).run();
  await env.DB.prepare(
    `UPDATE broker_execution_intents SET status='EXPIRED',completed_at=?,last_error_code='DISPATCH_WINDOW_EXPIRED'
     WHERE status='READY' AND expires_at < ?`,
  ).bind(receivedAt, receivedAt).run();
  const candidate = await env.DB.prepare(
    "SELECT intent_id FROM broker_execution_intents WHERE status='READY' AND expires_at>=? ORDER BY created_at ASC LIMIT 1",
  ).bind(receivedAt).first<{ intent_id: string }>();
  if (!candidate) return new Response(null, { status: 204 });
  const claimExpiresAt = new Date(Date.parse(receivedAt) + CLAIM_LEASE_MS).toISOString();
  const claimed = await env.DB.prepare(
    `UPDATE broker_execution_intents SET status='CLAIMED',claimed_by=?,claimed_at=?,claim_expires_at=?,attempt_count=attempt_count+1
     WHERE intent_id=? AND status='READY'`,
  ).bind(bridgeId, receivedAt, claimExpiresAt, candidate.intent_id).run();
  if (!claimed.meta.changes) return new Response(null, { status: 204 });
  const intent = await env.DB.prepare("SELECT * FROM broker_execution_intents WHERE intent_id=?")
    .bind(candidate.intent_id).first<Record<string, unknown>>();
  await env.DB.prepare(
    `INSERT INTO broker_execution_events(
      event_id,broker_event_key,intent_id,event_type,occurred_at,received_at,bridge_id,detail_json
    ) VALUES(?,? ,?,'CLAIMED',?,?,?,'{}')`,
  ).bind(
    randomId("broker-event"), `claim:${candidate.intent_id}:${receivedAt}`, candidate.intent_id,
    receivedAt, receivedAt, bridgeId,
  ).run();
  return Response.json({
    intent_id: intent?.intent_id,
    status: intent?.status,
    claim_expires_at: intent?.claim_expires_at,
    command: JSON.parse(String(intent?.command_json)),
  });
}

const EVENT_STATUS: Record<string, string> = {
  BROKER_ACKNOWLEDGED: "BROKER_ACKNOWLEDGED",
  PARTIAL_FILL: "PARTIAL_FILL",
  FILLED: "FILLED",
  REJECTED: "REJECTED",
  CANCELLED: "CANCELLED",
  EXPIRED: "EXPIRED",
  AMBIGUOUS: "AMBIGUOUS",
};

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  CLAIMED: ["BROKER_ACKNOWLEDGED", "PARTIAL_FILL", "FILLED", "REJECTED", "CANCELLED", "EXPIRED", "AMBIGUOUS"],
  BROKER_ACKNOWLEDGED: ["PARTIAL_FILL", "FILLED", "REJECTED", "CANCELLED", "AMBIGUOUS"],
  PARTIAL_FILL: ["PARTIAL_FILL", "FILLED", "CANCELLED", "AMBIGUOUS"],
  AMBIGUOUS: ["BROKER_ACKNOWLEDGED", "PARTIAL_FILL", "FILLED", "REJECTED", "CANCELLED"],
};

async function recordBrokerEvent(
  env: Env,
  bridgeId: string,
  receivedAt: string,
  intentId: string,
  bodyText: string,
): Promise<Response> {
  const body = parseBody<BridgeEventBody>(bodyText);
  const eventType = String(body.event_type ?? "");
  const allowedEvents = [...Object.keys(EVENT_STATUS), "COMMISSION_REPORT", "RECOVERY_OBSERVATION"];
  if (!allowedEvents.includes(eventType) || !/^[a-zA-Z0-9:._-]{8,180}$/.test(String(body.broker_event_key ?? "")) ||
      !Number.isFinite(Date.parse(String(body.occurred_at ?? ""))) ||
      (body.broker_order_id != null && !Number.isInteger(body.broker_order_id)) ||
      (body.broker_perm_id != null && !Number.isInteger(body.broker_perm_id)) ||
      (body.broker_exec_id != null && !/^[a-zA-Z0-9._-]{1,100}$/.test(body.broker_exec_id))) {
    throw new Error("INVALID_BROKER_EVENT");
  }
  const intent = await env.DB.prepare("SELECT * FROM broker_execution_intents WHERE intent_id=?")
    .bind(intentId).first<Record<string, unknown>>();
  if (!intent) return Response.json({ error: "BROKER_INTENT_NOT_FOUND" }, { status: 404 });
  if (intent.claimed_by && intent.claimed_by !== bridgeId) return Response.json({ error: "BROKER_INTENT_CLAIM_MISMATCH" }, { status: 409 });

  const existing = await env.DB.prepare("SELECT event_id FROM broker_execution_events WHERE broker_event_key=?")
    .bind(body.broker_event_key).first<{ event_id: string }>();
  if (existing) return Response.json({ accepted: true, duplicate: true, event_id: existing.event_id });

  const nextStatus = EVENT_STATUS[eventType];
  if (nextStatus && !(ALLOWED_TRANSITIONS[String(intent.status)] ?? []).includes(nextStatus)) {
    return Response.json({ error: "BROKER_EVENT_TRANSITION_INVALID" }, { status: 409 });
  }
  const eventId = randomId("broker-event");
  const terminal = ["FILLED", "REJECTED", "CANCELLED", "EXPIRED", "AMBIGUOUS"].includes(nextStatus ?? "");
  const statements: D1PreparedStatement[] = [env.DB.prepare(
    `INSERT INTO broker_execution_events(
      event_id,broker_event_key,intent_id,event_type,occurred_at,received_at,bridge_id,
      broker_order_id,broker_perm_id,broker_exec_id,detail_json
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)`,
  ).bind(
    eventId, body.broker_event_key, intentId, eventType, body.occurred_at, receivedAt, bridgeId,
    body.broker_order_id ?? null, body.broker_perm_id ?? null, body.broker_exec_id ?? null,
    JSON.stringify(body.detail ?? {}),
  )];
  if (nextStatus) {
    statements.push(env.DB.prepare(
      `UPDATE broker_execution_intents SET status=?,broker_order_id=coalesce(?,broker_order_id),
       broker_perm_id=coalesce(?,broker_perm_id),completed_at=?,last_error_code=? WHERE intent_id=?`,
    ).bind(
      nextStatus, body.broker_order_id ?? null, body.broker_perm_id ?? null,
      terminal ? receivedAt : null,
      ["REJECTED", "CANCELLED", "EXPIRED", "AMBIGUOUS"].includes(nextStatus)
        ? String(body.detail?.error_code ?? nextStatus)
        : null,
      intentId,
    ));
  }
  await env.DB.batch(statements);
  await audit(env.DB, `PAPER_BROKER_${eventType}`, `bridge:${bridgeId}`, String(intent.position_id), {
    intent_id: intentId,
    broker_order_id: body.broker_order_id ?? null,
    broker_perm_id: body.broker_perm_id ?? null,
  });
  return Response.json({ accepted: true, duplicate: false, event_id: eventId, intent_status: nextStatus ?? intent.status });
}

export async function routeBrokerInternal(request: Request, env: Env, path: string): Promise<Response | null> {
  if (!path.startsWith("/internal/broker/")) return null;
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  const verified = await verifyBridgeRequest(request, env);
  if (path === "/internal/broker/heartbeat") {
    return recordHeartbeat(env, verified.bridgeId, verified.receivedAt, verified.bodyText);
  }
  if (path === "/internal/broker/intents/claim") {
    return claimNextIntent(env, verified.bridgeId, verified.receivedAt);
  }
  const eventMatch = path.match(/^\/internal\/broker\/intents\/([^/]+)\/events$/);
  if (eventMatch) {
    return recordBrokerEvent(
      env,
      verified.bridgeId,
      verified.receivedAt,
      decodeURIComponent(eventMatch[1]!),
      verified.bodyText,
    );
  }
  return Response.json({ error: "NOT_FOUND" }, { status: 404 });
}

export async function routeBrokerAuthenticated(
  request: Request,
  env: Env,
  auth: AuthContext,
  path: string,
  readJsonBody: () => Promise<unknown>,
): Promise<Response | null> {
  if (path === "/api/broker/status" && request.method === "GET") return brokerStatus(env);
  if (path === "/api/broker/control" && request.method === "POST") {
    return configureBrokerControl(request, env, auth, await readJsonBody());
  }
  if (path === "/api/broker/exit-policy" && request.method === "POST") {
    return configureExitPolicy(request, env, auth, await readJsonBody() as ExitPolicyBody);
  }
  return null;
}
