import {
  attachCsrfCookie,
  authenticateAccess,
  hasFreshSensitiveAuth,
  requireActionPassword,
  requireCsrf,
} from "./auth";
import { queueAcknowledgedPaperClose, routeBrokerAuthenticated, routeBrokerInternal } from "./broker-control";
import { activePosition, audit, importDossier, incrementUsage, latestProjection, persistProjection } from "./db";
import { syntheticDemoDossier } from "./demo";
import { calculateProjection, estimateDailyUsage, inverseStructureLegs, randomId, validateDossier } from "./domain";
import { TTWOPositionMonitor } from "./monitor";
import { routeInternalResearch, routeResearchAuthenticated } from "./research";
import type { AuthContext, CloudPositionDossier } from "./types";
import dashboardHtml from "../public/dashboard.txt";
import appJavaScript from "../public/app.txt";
import previewStateJavaScript from "../public/preview-state.txt";
import researchStateJavaScript from "../public/research-state.txt";
import stylesCss from "../public/styles.txt";

export { TTWOPositionMonitor };

const SECURITY_HEADERS: Record<string, string> = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

function withSecurity(response: Response): Response {
  const secured = new Response(response.body, response);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) secured.headers.set(name, value);
  return secured;
}

function apiError(error: unknown): Response {
  const message = error instanceof Error ? error.message : "INTERNAL_ERROR";
  let status = 500;
  if (["CSRF_INVALID", "ACTION_PASSWORD_REQUIRED", "ACTION_PASSWORD_INVALID"].includes(message)) status = 403;
  else if (
    message.startsWith("INVALID_CALLBACK") || message === "CALLBACK_BODY_HASH_MISMATCH" ||
    message === "CALLBACK_TIMESTAMP_OUTSIDE_WINDOW" ||
    message.startsWith("INVALID_BROKER_BRIDGE") ||
    message === "BROKER_BRIDGE_TIMESTAMP_OUTSIDE_WINDOW"
  ) status = 403;
  else if (message === "ACTION_PASSWORD_RATE_LIMITED") status = 429;
  else if (message === "CALLBACK_BODY_TOO_LARGE") status = 413;
  else if (message === "CALLBACK_REPLAY_DETECTED" || message === "BROKER_BRIDGE_REPLAY_DETECTED") status = 409;
  else if (message === "BROKER_BRIDGE_BODY_TOO_LARGE") status = 413;
  else if (
    message === "ACTION_PASSWORD_NOT_CONFIGURED" ||
    message === "ANALYSIS_CALLBACK_SECRET_NOT_CONFIGURED" ||
    message === "GITHUB_ACTIONS_TOKEN_NOT_CONFIGURED" ||
    message === "BROKER_BRIDGE_SECRET_NOT_CONFIGURED"
  ) status = 503;
  else if (message.startsWith("GITHUB_WORKFLOW_DISPATCH_FAILED_")) status = 502;
  else if (
    message.startsWith("PAPER_BROKER_") || message.startsWith("PAPER_CLOSE_") ||
    message === "PAPER_EXIT_POLICY_REQUIRED" || message === "PAPER_POSITION_REQUIRED" ||
    message === "ACKNOWLEDGED_PREVIEW_REQUIRED" || message === "PAPER_POSITION_INTENT_ALREADY_ACTIVE"
  ) status = 409;
  else if (
    message.startsWith("INVALID_") || message.startsWith("COMBO_") ||
    message.startsWith("MISSING_") || message.startsWith("ENTRY_") ||
    message.startsWith("CAPITAL_") || message === "FX_RATE_UNAVAILABLE"
  ) status = 400;
  return Response.json({ error: message }, { status });
}

async function jsonBody<T>(request: Request): Promise<T> {
  const contentType = request.headers.get("Content-Type") ?? "";
  if (!contentType.includes("application/json")) throw new Error("INVALID_CONTENT_TYPE");
  return request.json<T>();
}

function monitorStub(env: Env): DurableObjectStub {
  return env.MONITOR.get(env.MONITOR.idFromName("single-ttwo-position-monitor"));
}

const STATIC_ASSETS: Record<string, { body: string; contentType: string }> = {
  "/dashboard.html": { body: dashboardHtml, contentType: "text/html; charset=utf-8" },
  "/app.js": { body: appJavaScript, contentType: "text/javascript; charset=utf-8" },
  "/preview-state.js": { body: previewStateJavaScript, contentType: "text/javascript; charset=utf-8" },
  "/research-state.js": { body: researchStateJavaScript, contentType: "text/javascript; charset=utf-8" },
  "/styles.css": { body: stylesCss, contentType: "text/css; charset=utf-8" },
};

function serveAsset(pathname: string): Response {
  const asset = STATIC_ASSETS[pathname];
  if (!asset) return new Response("Not found", { status: 404 });
  return new Response(asset.body, { headers: { "Content-Type": asset.contentType } });
}

async function dashboardPayload(env: Env, auth: AuthContext): Promise<Response> {
  const position = await activePosition(env.DB) ?? await env.DB.prepare("SELECT * FROM positions ORDER BY updated_at DESC LIMIT 1").first<Record<string, unknown>>();
  const positionId = position ? String(position.id) : null;
  const statements = positionId
    ? [
      env.DB.prepare("SELECT * FROM pnl_snapshots WHERE position_id=? ORDER BY timestamp DESC LIMIT 720").bind(positionId),
      env.DB.prepare("SELECT * FROM close_previews WHERE position_id=? ORDER BY created_at DESC LIMIT 20").bind(positionId),
      env.DB.prepare("SELECT * FROM fills WHERE position_id=? ORDER BY timestamp DESC LIMIT 20").bind(positionId),
      env.DB.prepare("SELECT * FROM monitoring_events WHERE position_id=? ORDER BY timestamp DESC LIMIT 50").bind(positionId),
      env.DB.prepare("SELECT * FROM audit_events WHERE position_id=? OR position_id IS NULL ORDER BY timestamp DESC LIMIT 50").bind(positionId),
    ]
    : [];
  const results = statements.length ? await env.DB.batch(statements) : [];
  const system = await env.DB.prepare("SELECT * FROM system_state WHERE singleton=1").first<Record<string, unknown>>();
  const usage = await env.DB.prepare("SELECT * FROM daily_usage WHERE date=?").bind(new Date().toISOString().slice(0, 10)).first<Record<string, unknown>>();
  return Response.json({
    csrf_token: auth.csrfToken,
    identity: { email: auth.email },
    system,
    position: position
      ? { ...position, canonical_dossier: JSON.parse(String(position.canonical_dossier_json)), canonical_dossier_json: undefined }
      : null,
    pnl_history: results[0]?.results ?? [],
    latest_pnl: results[0]?.results[0] ?? null,
    close_previews: results[1]?.results ?? [],
    fills: results[2]?.results ?? [],
    monitoring_events: results[3]?.results ?? [],
    audit_events: results[4]?.results ?? [],
    usage: usage ?? { label: "APPLICATION_ESTIMATE_ONLY" },
    usage_estimate: estimateDailyUsage(),
    safety: { read_only: true, transmit: false, what_if: true, order_capability: "forbidden" },
  });
}

async function setSafeMode(request: Request, env: Env, auth: AuthContext): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "SET_SAFE_MODE");
  const body = await jsonBody<{ enabled?: boolean }>(request);
  if (typeof body.enabled !== "boolean") throw new Error("INVALID_SAFE_MODE_VALUE");
  const now = new Date().toISOString();
  await env.DB.prepare(
    "UPDATE system_state SET safe_mode=?,broker_kill_switch=CASE WHEN ?=1 THEN 1 ELSE broker_kill_switch END,updated_at=? WHERE singleton=1",
  ).bind(body.enabled ? 1 : 0, body.enabled ? 1 : 0, now).run();
  if (body.enabled) {
    await env.DB.prepare(
      "UPDATE broker_execution_intents SET status='BLOCKED',completed_at=?,last_error_code='SAFE_MODE_ENABLED' WHERE status='READY'",
    ).bind(now).run();
  }
  await audit(env.DB, body.enabled ? "SAFE_MODE_ENABLED" : "SAFE_MODE_DISABLED", auth.actor);
  return Response.json({ safe_mode: body.enabled });
}

async function setMonitoring(request: Request, env: Env, auth: AuthContext, paused: boolean): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, paused ? "PAUSE_MONITORING" : "RESUME_MONITORING");
  const now = new Date().toISOString();
  await env.DB.prepare("UPDATE system_state SET monitoring_paused=?,updated_at=? WHERE singleton=1").bind(paused ? 1 : 0, now).run();
  await monitorStub(env).fetch(`https://monitor/${paused ? "pause" : "resume"}`, { method: "POST" });
  await audit(env.DB, paused ? "MONITOR_PAUSED" : "MONITOR_RESUMED", auth.actor);
  return Response.json({ monitoring_paused: paused });
}

async function importPosition(request: Request, env: Env, auth: AuthContext, demo = false): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, demo ? "IMPORT_SYNTHETIC_DEMO" : "IMPORT_POSITION");
  const state = await env.DB.prepare("SELECT safe_mode FROM system_state WHERE singleton=1").first<{ safe_mode: number }>();
  if (state?.safe_mode) return Response.json({ error: "SAFE_MODE_BLOCKS_IMPORT" }, { status: 409 });
  const existing = await activePosition(env.DB);
  if (existing) return Response.json({ error: "ACTIVE_POSITION_ALREADY_EXISTS" }, { status: 409 });
  const raw = demo ? syntheticDemoDossier() : await jsonBody<unknown>(request);
  const dossier = validateDossier(raw);
  if (dossier.ticker !== "TTWO") throw new Error("INVALID_DOSSIER: CF0 supports TTWO only");
  await importDossier(env.DB, dossier, auth.actor);
  if (dossier.initial_position_state !== "PLANNED") {
    if (dossier.last_imported_snapshot) {
      await persistProjection(
        env.DB,
        dossier.position_id,
        calculateProjection(dossier, dossier.last_imported_snapshot),
      );
    }
    await env.DB.prepare("UPDATE system_state SET monitoring_paused=0,updated_at=? WHERE singleton=1").bind(new Date().toISOString()).run();
    await monitorStub(env).fetch("https://monitor/start", { method: "POST" });
    await audit(env.DB, "MONITOR_STARTED", auth.actor, dossier.position_id, { trigger: "POSITION_IMPORT" });
  }
  return Response.json({ imported: true, position_id: dossier.position_id, fixture_status: dossier.fixture_status }, { status: 201 });
}

async function createClosePreview(request: Request, env: Env, auth: AuthContext): Promise<Response> {
  requireCsrf(request, auth);
  const body = await jsonBody<{ quantity?: number }>(request);
  const position = await activePosition(env.DB);
  if (!position) return Response.json({ error: "NO_ACTIVE_POSITION" }, { status: 409 });
  const dossier = validateDossier(JSON.parse(position.canonical_dossier_json));
  const quantity = body.quantity ?? position.quantity_remaining;
  if (quantity > position.quantity_remaining) throw new Error("COMBO_CLOSE_PREVIEW_UNAVAILABLE");
  const projection = await latestProjection(env.DB, position.id);
  if (!projection || projection.liquidation_value === null || projection.liquidation_pnl === null || projection.liquidation_return === null) {
    return Response.json({ error: "COMBO_CLOSE_PREVIEW_UNAVAILABLE" }, { status: 409 });
  }
  const legs = inverseStructureLegs(dossier, quantity);
  const scale = quantity / position.quantity_remaining;
  const effectiveTimestamp = projection.required_data_effective_timestamp === null
    ? String(projection.timestamp)
    : String(projection.required_data_effective_timestamp);
  const freshnessReasons = (() => {
    try { return JSON.parse(String(projection.freshness_reasons_json ?? "[]")) as string[]; }
    catch { return ["FRESHNESS_REASONS_UNREADABLE"]; }
  })();
  const requiredDataFreshness = {
    effective_timestamp: projection.required_data_effective_timestamp,
    underlying_timestamp: projection.underlying_timestamp,
    oldest_option_timestamp: projection.oldest_option_timestamp,
    fx_timestamp: projection.fx_timestamp,
    combo_timestamp: projection.combo_timestamp,
    age_seconds: projection.required_data_age_seconds,
    status: projection.data_freshness,
    reasons: freshnessReasons,
  };
  const previewId = randomId("preview");
  const createdAt = new Date().toISOString();
  await env.DB.prepare(
    `INSERT INTO close_previews(preview_id,position_id,created_at,quantity,pre_close_market_value,
     pre_close_liquidation_value,estimated_pnl,estimated_return,estimated_commission,estimated_slippage,
     estimated_fx,engine_action,quote_timestamp,quote_provider,legs_json,status,estimated_close_cash_flow_policy)
     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'CREATED',?)`,
  ).bind(
    previewId, position.id, createdAt, quantity, Number(projection.market_value_policy) * scale,
    Number(projection.liquidation_value) * scale, Number(projection.liquidation_pnl) * scale,
    Number(projection.liquidation_return), projection.estimated_exit_commission === null ? null : Number(projection.estimated_exit_commission) * scale,
    projection.estimated_exit_slippage === null ? null : Number(projection.estimated_exit_slippage) * scale,
    projection.estimated_exit_fx === null ? null : Number(projection.estimated_exit_fx) * scale,
    String(projection.monitor_action), effectiveTimestamp,
    String(projection.provider), JSON.stringify(legs),
    Number(projection.estimated_close_cash_flow_policy) * scale,
  ).run();
  await audit(env.DB, "CLOSE_PREVIEW_CREATED", auth.actor, position.id, { preview_id: previewId, quantity });
  return Response.json({
    preview_id: previewId,
    status: "CREATED",
    quantity,
    structure_name: position.structure_name,
    legs,
    market_value: Number(projection.market_value_policy) * scale,
    estimated_close_cash_flow_policy: Number(projection.estimated_close_cash_flow_policy) * scale,
    liquidation_value: Number(projection.liquidation_value) * scale,
    estimated_pnl: Number(projection.liquidation_pnl) * scale,
    estimated_return: Number(projection.liquidation_return),
    engine_action: projection.monitor_action,
    quote_timestamp: projection.required_data_effective_timestamp,
    required_data_freshness: requiredDataFreshness,
    quote_provider: projection.provider,
    safety: { transmit: false, what_if: true, order_capability: "forbidden", security_type: "BAG" },
  }, { status: 201 });
}

async function acknowledgeClose(request: Request, env: Env, auth: AuthContext, previewId: string): Promise<Response> {
  requireCsrf(request, auth);
  if (!hasFreshSensitiveAuth(auth)) return Response.json({ error: "SENSITIVE_ACCESS_REAUTH_REQUIRED" }, { status: 403 });
  await requireActionPassword(request, env, auth, "ACKNOWLEDGE_CLOSE_PREVIEW");
  const acknowledgedAt = new Date().toISOString();
  const result = await env.DB.prepare(
    "UPDATE close_previews SET acknowledged_at=?,status='ACKNOWLEDGED' WHERE preview_id=? AND status='CREATED'",
  ).bind(acknowledgedAt, previewId).run();
  if (!result.meta.changes) return Response.json({ error: "PREVIEW_NOT_ACKNOWLEDGEABLE" }, { status: 409 });
  const preview = await env.DB.prepare("SELECT position_id FROM close_previews WHERE preview_id=?").bind(previewId).first<{ position_id: string }>();
  await audit(env.DB, "CLOSE_PREVIEW_ACKNOWLEDGED", auth.actor, preview?.position_id ?? null, { preview_id: previewId });
  const queued = await queueAcknowledgedPaperClose(env, auth, previewId);
  if (queued) {
    return Response.json({ status: "PAPER_CLOSE_QUEUED", intent: queued, transmitted: false }, { status: 202 });
  }
  return Response.json({ status: "CLOSE_PREVIEW_READY", instruction: "Close this entire combo manually in IBKR.", transmitted: false });
}

async function reportManualClose(request: Request, env: Env, auth: AuthContext, previewId: string): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "REPORT_MANUAL_CLOSE");
  const preview = await env.DB.prepare("SELECT position_id,status FROM close_previews WHERE preview_id=?").bind(previewId).first<{ position_id: string; status: string }>();
  if (!preview || preview.status !== "ACKNOWLEDGED") return Response.json({ error: "ACKNOWLEDGED_PREVIEW_REQUIRED" }, { status: 409 });
  await env.DB.batch([
    env.DB.prepare("UPDATE close_previews SET status='RECONCILIATION_REQUIRED' WHERE preview_id=?").bind(previewId),
    env.DB.prepare("UPDATE positions SET state='RECONCILIATION_REQUIRED',updated_at=? WHERE id=?").bind(new Date().toISOString(), preview.position_id),
  ]);
  await audit(env.DB, "MANUAL_CLOSE_REPORTED", auth.actor, preview.position_id, { preview_id: previewId });
  return Response.json({ status: "RECONCILIATION_REQUIRED" });
}

interface FillRequest {
  timestamp?: string;
  combo_fill_price?: number;
  close_cash_flow_type?: "CREDIT" | "DEBIT";
  quantity_closed?: number;
  commission?: number;
  fx_cost?: number;
  actual_fx_rate?: number;
  broker_reference?: string;
}

async function reconcileFill(request: Request, env: Env, auth: AuthContext, previewId: string): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "RECONCILE_ACTUAL_FILL");
  const body = await jsonBody<FillRequest>(request);
  const preview = await env.DB.prepare("SELECT * FROM close_previews WHERE preview_id=?").bind(previewId).first<Record<string, unknown>>();
  if (!preview || preview.status !== "RECONCILIATION_REQUIRED") return Response.json({ error: "RECONCILIATION_NOT_READY" }, { status: 409 });
  const position = await env.DB.prepare("SELECT * FROM positions WHERE id=?").bind(String(preview.position_id)).first<Record<string, unknown>>();
  if (!position) return Response.json({ error: "POSITION_NOT_FOUND" }, { status: 404 });
  const timestamp = body.timestamp ?? "";
  const quantity = body.quantity_closed ?? 0;
  const fillPrice = body.combo_fill_price ?? Number.NaN;
  const closeCashFlowType = body.close_cash_flow_type;
  const commission = body.commission ?? Number.NaN;
  const fxCost = body.fx_cost ?? Number.NaN;
  if (!Number.isFinite(Date.parse(timestamp)) || !Number.isInteger(quantity) || quantity <= 0 || quantity > Number(position.quantity_remaining) || quantity > Number(preview.quantity)) {
    throw new Error("INVALID_FILL_IDENTITY_OR_QUANTITY");
  }
  if (
    ![fillPrice, commission, fxCost].every(Number.isFinite) || fillPrice < 0 ||
    commission < 0 || fxCost < 0 || !closeCashFlowType ||
    !["CREDIT", "DEBIT"].includes(closeCashFlowType)
  ) throw new Error("INVALID_FILL_ECONOMICS");
  const dossier = validateDossier(JSON.parse(String(position.canonical_dossier_json)));
  const sameCurrency = dossier.entry_native_currency === dossier.policy_currency;
  const fxRate = sameCurrency ? 1 : body.actual_fx_rate;
  if (!fxRate || fxRate <= 0) throw new Error("FX_RATE_UNAVAILABLE");
  const closeSign = closeCashFlowType === "CREDIT" ? 1 : -1;
  const signedGrossCloseCashFlowNative = closeSign * fillPrice * quantity * dossier.multiplier;
  const signedCloseCashFlowPolicy = signedGrossCloseCashFlowNative * fxRate - commission - fxCost;
  const allocatedEntryCashFlow = dossier.entry_cash_flow_policy * quantity / dossier.quantity;
  const realized = allocatedEntryCashFlow + signedCloseCashFlowPolicy;
  const estimated = Number(preview.estimated_pnl) * quantity / Number(preview.quantity);
  const estimateError = realized - estimated;
  const remaining = Number(position.quantity_remaining) - quantity;
  const newState = remaining === 0 ? "CLOSED" : "PARTIAL_CLOSE";
  const now = new Date().toISOString();
  const fillId = randomId("fill");
  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO fills(fill_id,position_id,preview_id,timestamp,quantity_closed,combo_fill_price,native_proceeds,
       policy_proceeds,commission,fx_cost,actual_realized_pnl,estimate_error,broker_reference,source,created_at,
       close_cash_flow_type,signed_close_cash_flow_policy)
       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'MANUAL_IBKR_RECONCILIATION',?,?,?)`,
    ).bind(
      fillId, position.id, previewId, timestamp, quantity, fillPrice,
      signedGrossCloseCashFlowNative, signedCloseCashFlowPolicy, commission, fxCost, realized,
      estimateError, body.broker_reference ?? null, now, closeCashFlowType,
      signedCloseCashFlowPolicy,
    ),
    env.DB.prepare(
      "UPDATE positions SET quantity_remaining=?,realized_pnl=coalesce(realized_pnl,0)+?,state=?,closed_at=?,updated_at=? WHERE id=?",
    ).bind(remaining, realized, newState, remaining === 0 ? timestamp : null, now, position.id),
    env.DB.prepare("UPDATE close_previews SET status='RECONCILED' WHERE preview_id=?").bind(previewId),
  ]);
  if (remaining > 0 && dossier.last_imported_snapshot) {
    const remainingProjection = calculateProjection(
      dossier,
      dossier.last_imported_snapshot,
      remaining,
      new Date(),
    );
    await persistProjection(env.DB, String(position.id), remainingProjection);
  }
  await audit(env.DB, "FILL_RECONCILED", auth.actor, String(position.id), { fill_id: fillId, preview_id: previewId, actual_realized_pnl: realized, estimate_error: estimateError });
  await audit(env.DB, remaining === 0 ? "POSITION_CLOSED" : "POSITION_PARTIALLY_CLOSED", auth.actor, String(position.id), { quantity_closed: quantity, quantity_remaining: remaining });
  return Response.json({
    fill_id: fillId,
    state: newState,
    quantity_remaining: remaining,
    actual_close_cash_flow_policy: signedCloseCashFlowPolicy,
    actual_proceeds: signedCloseCashFlowPolicy,
    actual_realized_pnl: realized,
    estimated_pnl: estimated,
    estimate_error: estimateError,
  }, { status: 201 });
}

async function exportData(env: Env, auth: AuthContext): Promise<Response> {
  const tables = [
    "positions", "position_legs", "fills", "pnl_snapshots", "model_snapshots",
    "close_previews", "monitoring_events", "audit_events", "analysis_requests",
    "analysis_runs", "analysis_candidate_summaries", "analysis_candidate_details",
    "candidate_selections", "planned_positions", "position_exit_policies",
    "broker_execution_intents", "broker_execution_events", "broker_bridge_heartbeats",
  ] as const;
  const results = await env.DB.batch(tables.map((table) => env.DB.prepare(`SELECT * FROM ${table}`)));
  const payload = Object.fromEntries(tables.map((table, index) => [table, results[index]?.results ?? []]));
  await audit(env.DB, "DATA_EXPORTED", auth.actor, null, { format: "json", secrets_included: false });
  return new Response(JSON.stringify({ exported_at: new Date().toISOString(), schema_version: "1.1", ...payload }, null, 2), {
    headers: { "Content-Type": "application/json", "Content-Disposition": `attachment; filename="take-two-control-${new Date().toISOString().slice(0, 10)}.json"` },
  });
}

async function routeAuthenticated(request: Request, env: Env, auth: AuthContext, path: string): Promise<Response> {
  await incrementUsage(env.DB, "worker_api_requests");
  const broker = await routeBrokerAuthenticated(
    request,
    env,
    auth,
    path,
    () => jsonBody<unknown>(request),
  );
  if (broker) return broker;
  const research = await routeResearchAuthenticated(
    request,
    env,
    auth,
    path,
    () => jsonBody<unknown>(request),
  );
  if (research) return research;
  if (path === "/api/session" && request.method === "GET") return Response.json({ authenticated: true, csrf_token: auth.csrfToken, identity: { email: auth.email } });
  if (path === "/api/dashboard" && request.method === "GET") return dashboardPayload(env, auth);
  if (path === "/api/positions/import" && request.method === "POST") return importPosition(request, env, auth);
  if (path === "/api/demo/import" && request.method === "POST") return importPosition(request, env, auth, true);
  if (path === "/api/safe-mode" && request.method === "POST") return setSafeMode(request, env, auth);
  if (path === "/api/monitor/pause" && request.method === "POST") return setMonitoring(request, env, auth, true);
  if (path === "/api/monitor/resume" && request.method === "POST") return setMonitoring(request, env, auth, false);
  if (path === "/api/close-previews" && request.method === "POST") return createClosePreview(request, env, auth);
  const acknowledge = path.match(/^\/api\/close-previews\/([^/]+)\/acknowledge$/);
  if (acknowledge && request.method === "POST") return acknowledgeClose(request, env, auth, decodeURIComponent(acknowledge[1]!));
  const reported = path.match(/^\/api\/close-previews\/([^/]+)\/manual-close-reported$/);
  if (reported && request.method === "POST") return reportManualClose(request, env, auth, decodeURIComponent(reported[1]!));
  const reconcile = path.match(/^\/api\/close-previews\/([^/]+)\/reconcile$/);
  if (reconcile && request.method === "POST") return reconcileFill(request, env, auth, decodeURIComponent(reconcile[1]!));
  if (path === "/api/export" && request.method === "GET") return exportData(env, auth);
  if (path === "/api/usage-estimate" && request.method === "GET") return Response.json(estimateDailyUsage());
  return Response.json({ error: "NOT_FOUND" }, { status: 404 });
}

export async function handleRequest(
  request: Request,
  env: Env,
  access: CloudflareAccessContext | undefined,
): Promise<Response> {
  try {
    const path = new URL(request.url).pathname;
    const internalBroker = await routeBrokerInternal(request, env, path);
    if (internalBroker) return withSecurity(internalBroker);
    const internalResearch = await routeInternalResearch(request, env, path);
    if (internalResearch) return withSecurity(internalResearch);
    const auth = await authenticateAccess(request, access);
    if (!auth) {
      const denied = path.startsWith("/api/")
        ? Response.json({ error: "ACCESS_REQUIRED" }, { status: 403 })
        : new Response("Cloudflare Access required", { status: 403 });
      return withSecurity(denied);
    }

    let response: Response;
    if (path === "/") response = Response.redirect(new URL("/dashboard", request.url), 302);
    else if (path === "/dashboard.html") response = Response.redirect(new URL("/dashboard", request.url), 302);
    else if (path === "/dashboard") response = serveAsset("/dashboard.html");
    else if (path.startsWith("/api/")) response = await routeAuthenticated(request, env, auth, path);
    else response = serveAsset(path);
    return withSecurity(attachCsrfCookie(response, auth));
  } catch (error) {
    return withSecurity(apiError(error));
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return handleRequest(request, env, ctx.access);
  },
} satisfies ExportedHandler<Env>;
