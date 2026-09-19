import { hasFreshSensitiveAuth, requireActionPassword, requireCsrf } from "./auth";
import { sha256Hex } from "./broker-security";
import { audit } from "./db";
import { randomId } from "./domain";
import type { AuthContext } from "./types";

const HASH = /^[a-f0-9]{64}$/;
const ALLOWED_VERDICTS = new Set(["EXECUTABLE", "EXECUTABLE_REPRICE_PROPOSAL"]);
const ALL_VERDICTS = new Set([
  ...ALLOWED_VERDICTS,
  "REVIEW_REQUIRED",
  "REANALYSIS_REQUIRED",
  "BLOCKED",
]);
const MATERIAL_DRIFT_STATUSES = new Set([
  "WITHIN_POLICY",
  "MATERIAL_DRIFT",
  "REQUIRES_POLICY",
  "INSUFFICIENT_EVIDENCE",
]);

function record(value: unknown, code: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(code);
  return value as Record<string, unknown>;
}

function finite(value: unknown, code: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(code);
  return value;
}

function positiveInteger(value: unknown, code: string): number {
  if (!Number.isInteger(value) || Number(value) <= 0) throw new Error(code);
  return Number(value);
}

function text(value: unknown, code: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(code);
  return value;
}

function hash(value: unknown, code: string): string {
  const result = text(value, code);
  if (!HASH.test(result)) throw new Error(code);
  return result;
}

function parseJson(textValue: string, code: string): Record<string, unknown> {
  try {
    return record(JSON.parse(textValue), code);
  } catch {
    throw new Error(code);
  }
}

interface RevalidationEnvelope {
  ticket_json?: unknown;
  ticket_hash?: unknown;
  expires_at?: unknown;
}

export async function persistExecutionRevalidationTicket(
  env: Env,
  bodyText: string,
  receivedAt: string,
): Promise<Response> {
  const envelope = parseJson(bodyText, "INVALID_EXECUTION_REVALIDATION_ENVELOPE") as RevalidationEnvelope;
  const ticketJson = text(envelope.ticket_json, "INVALID_EXECUTION_REVALIDATION_TICKET_JSON");
  const ticketHash = hash(envelope.ticket_hash, "INVALID_EXECUTION_REVALIDATION_TICKET_HASH");
  if (await sha256Hex(ticketJson) !== ticketHash) {
    throw new Error("EXECUTION_REVALIDATION_TICKET_HASH_MISMATCH");
  }
  const ticket = parseJson(ticketJson, "INVALID_EXECUTION_REVALIDATION_TICKET");
  const expiresAt = text(envelope.expires_at, "INVALID_EXECUTION_REVALIDATION_EXPIRY");
  if (!Number.isFinite(Date.parse(expiresAt)) || Date.parse(expiresAt) <= Date.parse(receivedAt)) {
    throw new Error("EXECUTION_REVALIDATION_TICKET_ALREADY_STALE");
  }
  if (
    ticket.schema_version !== "execution-revalidation/1.0" ||
    ticket.execution_environment !== "IBKR_PAPER_SIMULATOR" ||
    ticket.human_confirmation_required !== true ||
    ticket.automatic_repricing_allowed !== false ||
    ticket.live_execution_allowed !== false
  ) throw new Error("INVALID_EXECUTION_REVALIDATION_SAFETY_FLAGS");
  const blockers = ticket.blockers;
  if (!Array.isArray(blockers) || blockers.some((item) => typeof item !== "string")) {
    throw new Error("INVALID_EXECUTION_REVALIDATION_BLOCKERS");
  }
  const market = record(ticket.current_market, "INVALID_EXECUTION_MARKET_SNAPSHOT");
  const economics = record(
    ticket.proposed_execution_economics,
    "INVALID_EXECUTION_ECONOMICS",
  );
  const materialDrift = record(ticket.material_drift, "INVALID_MATERIAL_DRIFT_RESULT");
  if (!ALL_VERDICTS.has(String(ticket.verdict))) {
    throw new Error("INVALID_EXECUTION_REVALIDATION_VERDICT");
  }
  if (!MATERIAL_DRIFT_STATUSES.has(String(materialDrift.status))) {
    throw new Error("INVALID_MATERIAL_DRIFT_STATUS");
  }
  if (ticket.combo_submission_mode !== "WHOLE_BAG") {
    throw new Error("INVALID_COMBO_SUBMISSION_MODE");
  }
  if (!["GUARANTEED", "NON_GUARANTEED", "UNKNOWN"].includes(
    String(ticket.broker_combo_guarantee_mode),
  )) throw new Error("INVALID_COMBO_GUARANTEE_MODE");
  const analysisId = text(ticket.original_analysis_id, "INVALID_EXECUTION_ANALYSIS_ID");
  const candidateId = text(ticket.candidate_id, "INVALID_EXECUTION_CANDIDATE_ID");
  const selectionId = text(ticket.selection_id, "INVALID_EXECUTION_SELECTION_ID");
  const dossierId = text(ticket.dossier_id, "INVALID_EXECUTION_DOSSIER_ID");
  const governed = await env.DB.prepare(
    `SELECT pp.dossier_id,pp.selection_id,pp.analysis_request_id,pp.candidate_id,pp.state,
      cs.trade_economics_ticket_hash,cs.snapshot_hash
     FROM planned_positions pp JOIN candidate_selections cs USING(selection_id)
     WHERE pp.dossier_id=?`,
  ).bind(dossierId).first<Record<string, unknown>>();
  if (!governed || governed.state !== "PLANNED") throw new Error("PLANNED_DOSSIER_REQUIRED");
  if (
    governed.selection_id !== selectionId || governed.analysis_request_id !== analysisId ||
    governed.candidate_id !== candidateId ||
    governed.trade_economics_ticket_hash !== ticket.original_trade_economics_ticket_hash ||
    governed.snapshot_hash !== ticket.original_market_snapshot_hash
  ) throw new Error("EXECUTION_REVALIDATION_LINEAGE_MISMATCH");
  const legs = ticket.legs;
  if (!Array.isArray(legs) || legs.length === 0) throw new Error("EXECUTION_LEGS_REQUIRED");
  for (const rawLeg of legs) {
    const leg = record(rawLeg, "INVALID_EXECUTION_LEG");
    if (
      !Number.isInteger(leg.con_id) || Number(leg.con_id) <= 0 ||
      !Number.isInteger(leg.ratio) || Number(leg.ratio) <= 0 ||
      !["BUY_TO_OPEN", "SELL_TO_OPEN"].includes(String(leg.application_action)) ||
      !["BUY", "SELL"].includes(String(leg.wire_action)) ||
      (leg.application_action === "BUY_TO_OPEN" && leg.wire_action !== "BUY") ||
      (leg.application_action === "SELL_TO_OPEN" && leg.wire_action !== "SELL")
    ) throw new Error("INVALID_EXECUTION_LEG");
  }
  const currentMarketHash = hash(
    ticket.current_market_snapshot_hash,
    "INVALID_CURRENT_MARKET_HASH",
  );
  const originalEconomicsHash = await sha256Hex(JSON.stringify(ticket.original_economics));
  const proposedEconomicsHash = await sha256Hex(JSON.stringify(economics));
  const ticketId = text(ticket.ticket_id, "INVALID_EXECUTION_TICKET_ID");
  const proposedLimit = finite(ticket.proposed_limit, "INVALID_PROPOSED_LIMIT");
  const validTick = finite(ticket.valid_tick, "INVALID_VALID_TICK");
  const quantity = positiveInteger(ticket.quantity, "INVALID_EXECUTION_QUANTITY");
  if (proposedLimit <= 0 || validTick <= 0) throw new Error("INVALID_EXECUTION_PRICE");
  const existing = await env.DB.prepare(
    "SELECT ticket_hash FROM execution_revalidation_tickets WHERE ticket_id=?",
  ).bind(ticketId).first<{ ticket_hash: string }>();
  if (existing) {
    if (existing.ticket_hash !== ticketHash) {
      throw new Error("EXECUTION_REVALIDATION_TICKET_IDENTITY_CONFLICT");
    }
    return Response.json({
      accepted: true,
      duplicate: true,
      ticket_id: ticketId,
      ticket_hash: ticketHash,
    });
  }
  await env.DB.prepare(
    `INSERT INTO execution_revalidation_tickets(
      ticket_id,analysis_request_id,candidate_id,selection_id,dossier_id,previous_ticket_id,
      drift_policy_id,structure_hash,original_market_snapshot_hash,current_market_snapshot_hash,
      original_economics_hash,proposed_economics_hash,ticket_hash,proposed_limit,valid_tick,
      quantity,combo_submission_mode,broker_combo_guarantee_mode,execution_environment,
      material_drift_status,verdict,blockers_json,ticket_json,created_at,expires_at
    ) VALUES(?,?,?,?,?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
  ).bind(
    ticketId, analysisId, candidateId,
    selectionId, dossierId, ticket.previous_execution_ticket_id ?? null,
    hash(ticket.structure_hash, "INVALID_EXECUTION_STRUCTURE_HASH"),
    hash(ticket.original_market_snapshot_hash, "INVALID_ORIGINAL_MARKET_HASH"),
    currentMarketHash, originalEconomicsHash, proposedEconomicsHash, ticketHash,
    proposedLimit, validTick, quantity,
    ticket.combo_submission_mode, ticket.broker_combo_guarantee_mode,
    ticket.execution_environment, materialDrift.status, ticket.verdict,
    JSON.stringify(blockers), ticketJson,
    text(ticket.created_at, "INVALID_EXECUTION_TICKET_CREATED_AT"), expiresAt,
  ).run();
  return Response.json({
    accepted: true,
    duplicate: false,
    ticket_id: ticketId,
    ticket_hash: ticketHash,
  });
}

async function createPreview(
  request: Request,
  env: Env,
  auth: AuthContext,
  body: unknown,
): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "CREATE_PAPER_ENTRY_PREVIEW");
  const value = record(body, "INVALID_PAPER_ENTRY_PREVIEW_REQUEST");
  const dossierId = text(value.dossier_id, "INVALID_PAPER_ENTRY_DOSSIER_ID");
  const ticketId = text(value.ticket_id, "INVALID_PAPER_ENTRY_TICKET_ID");
  const row = await env.DB.prepare(
    `SELECT t.*,pp.dossier_json,pp.state AS dossier_state
     FROM execution_revalidation_tickets t JOIN planned_positions pp USING(dossier_id)
     WHERE t.ticket_id=? AND t.dossier_id=?`,
  ).bind(ticketId, dossierId).first<Record<string, unknown>>();
  if (!row || row.dossier_state !== "PLANNED") throw new Error("PLANNED_DOSSIER_REQUIRED");
  if (!ALLOWED_VERDICTS.has(String(row.verdict))) {
    throw new Error("EXECUTION_REVALIDATION_NOT_EXECUTABLE");
  }
  const blockers = JSON.parse(String(row.blockers_json)) as unknown[];
  if (blockers.length) throw new Error("EXECUTION_REVALIDATION_HAS_BLOCKERS");
  if (Date.parse(String(row.expires_at)) <= Date.now()) {
    throw new Error("EXECUTION_REVALIDATION_TICKET_STALE");
  }
  if (row.broker_combo_guarantee_mode !== "GUARANTEED") {
    throw new Error("BLOCKED_NON_GUARANTEED_COMBO");
  }
  const ticket = parseJson(String(row.ticket_json), "INVALID_STORED_EXECUTION_TICKET");
  const previewId = randomId("paper-entry-preview");
  const preview = {
    schema_version: "paper-entry-preview/1.0",
    preview_id: previewId,
    dossier_id: dossierId,
    ticket_id: ticketId,
    execution_environment: "IBKR_PAPER_SIMULATOR",
    structure_hash: row.structure_hash,
    quantity: row.quantity,
    proposed_limit: row.proposed_limit,
    valid_tick: row.valid_tick,
    current_market: ticket.current_market,
    economic_revalidation: ticket.proposed_execution_economics,
    deltas: ticket.deltas,
    material_drift: ticket.material_drift,
    broker_state: "EXECUTION_LOCKED",
    fill_state: null,
    reason: "EXPLICIT_HUMAN_CONFIRMATION_REQUIRED",
    transmitted: false,
    live_execution_allowed: false,
  };
  const previewJson = JSON.stringify(preview);
  const previewHash = await sha256Hex(previewJson);
  const createdAt = new Date().toISOString();
  await env.DB.prepare(
    `INSERT INTO paper_entry_previews(
      preview_id,dossier_id,ticket_id,preview_hash,structure_hash,proposed_limit,
      requested_quantity,status,preview_json,created_at,expires_at,created_by
    ) VALUES(?,?,?,?,?,?,?,'PREVIEW_READY',?,?,?,?)`,
  ).bind(
    previewId, dossierId, ticketId, previewHash, row.structure_hash, row.proposed_limit,
    row.quantity, previewJson, createdAt, row.expires_at, auth.actor,
  ).run();
  await audit(env.DB, "PAPER_ENTRY_PREVIEW_READY", auth.actor, null, {
    dossier_id: dossierId,
    ticket_id: ticketId,
    preview_id: previewId,
  });
  return Response.json({ ...preview, preview_hash: previewHash, status: "PREVIEW_READY" }, {
    status: 201,
  });
}

async function confirmPreview(
  request: Request,
  env: Env,
  auth: AuthContext,
  previewId: string,
): Promise<Response> {
  requireCsrf(request, auth);
  if (!hasFreshSensitiveAuth(auth)) {
    return Response.json({ error: "SENSITIVE_ACCESS_REAUTH_REQUIRED" }, { status: 403 });
  }
  await requireActionPassword(request, env, auth, "CONFIRM_PAPER_ENTRY_PREVIEW");
  const row = await env.DB.prepare(
    `SELECT p.*,t.ticket_hash,t.ticket_json,t.verdict,t.blockers_json,t.expires_at AS ticket_expires_at
     FROM paper_entry_previews p JOIN execution_revalidation_tickets t USING(ticket_id)
     WHERE p.preview_id=?`,
  ).bind(previewId).first<Record<string, unknown>>();
  if (!row || row.status !== "PREVIEW_READY") throw new Error("PAPER_ENTRY_PREVIEW_REQUIRED");
  if (Date.parse(String(row.expires_at)) <= Date.now()) throw new Error("PAPER_ENTRY_PREVIEW_STALE");
  if (!ALLOWED_VERDICTS.has(String(row.verdict))) {
    throw new Error("EXECUTION_REVALIDATION_NOT_EXECUTABLE");
  }
  if ((JSON.parse(String(row.blockers_json)) as unknown[]).length) {
    throw new Error("EXECUTION_REVALIDATION_HAS_BLOCKERS");
  }
  const storedPreviewHash = await sha256Hex(String(row.preview_json));
  if (storedPreviewHash !== row.preview_hash) throw new Error("PAPER_ENTRY_PREVIEW_HASH_MISMATCH");
  const ticket = parseJson(String(row.ticket_json), "INVALID_STORED_EXECUTION_TICKET");
  const economics = record(ticket.proposed_execution_economics, "INVALID_EXECUTION_ECONOMICS");
  const legs = (ticket.legs as Array<Record<string, unknown>>).map((leg) => ({
    con_id: leg.con_id,
    ratio: leg.ratio,
    action: leg.application_action,
    wire_action: leg.wire_action,
    local_symbol: leg.local_symbol,
    trading_class: leg.trading_class,
    expiration: leg.expiration,
    strike: leg.strike,
    right: leg.right,
    multiplier: leg.multiplier,
    currency: leg.currency,
    exchange: leg.exchange,
  }));
  const confirmationId = randomId("paper-entry-confirmation");
  const confirmedAt = new Date().toISOString();
  const confirmation = {
    schema_version: "paper-entry-confirmation/1.0",
    confirmation_id: confirmationId,
    preview_id: previewId,
    ticket_id: row.ticket_id,
    preview_hash: row.preview_hash,
    ticket_hash: row.ticket_hash,
    confirmed_at: confirmedAt,
    confirmed_by: auth.actor,
    execution_environment: "IBKR_PAPER_SIMULATOR",
    human_confirmation: true,
  };
  const confirmationJson = JSON.stringify(confirmation);
  const confirmationHash = await sha256Hex(confirmationJson);
  const state = await env.DB.prepare(
    "SELECT broker_kill_switch,updated_at FROM system_state WHERE singleton=1",
  ).first<Record<string, unknown>>();
  const killSwitchVersion = await sha256Hex(JSON.stringify(state ?? {}));
  const intentId = randomId("paper-entry");
  const orderRef = `TTWO-PE-${intentId.slice(-24)}`;
  const command = {
    schema_version: "2.0",
    intent_id: intentId,
    intent_type: "PAPER_ENTRY",
    mode: "PAPER",
    account_guard: { required_prefix: "DU", live_accounts_forbidden: true },
    position_id: null,
    preview_id: previewId,
    order_ref: orderRef,
    ticker: "TTWO",
    native_currency: String(legs[0]?.currency ?? ""),
    requested_quantity: ticket.quantity,
    legs,
    maximum_exit_slippage_policy: 0,
    pricing_policy: "REFRESH_COMBO_QUOTE_AND_USE_BOUNDED_LIMIT",
    time_in_force: "DAY",
    transmit: true,
    entry_authorization: {
      candidate_approved: true,
      dossier_current: true,
      bag_semantics_verified: true,
      original_analysis_id: ticket.original_analysis_id,
      candidate_id: ticket.candidate_id,
      selection_id: ticket.selection_id,
      dossier_id: ticket.dossier_id,
      revalidation_ticket_id: ticket.ticket_id,
      revalidation_ticket_hash: row.ticket_hash,
      ticket_created_at: ticket.created_at,
      ticket_expires_at: row.ticket_expires_at,
      confirmation_id: confirmationId,
      confirmation_hash: confirmationHash,
      structure_type: ticket.structure_type ?? "GOVERNED_CANDIDATE",
      structure_hash: ticket.structure_hash,
      current_market_snapshot_hash: ticket.current_market_snapshot_hash,
      current_git_commit: ticket.current_git_commit,
      current_config_hash: ticket.current_config_hash,
      proposed_limit: ticket.proposed_limit,
      valid_tick: ticket.valid_tick,
      capital_required_eur: economics.capital_required,
      maximum_loss_eur: economics.max_loss,
      expected_commissions_eur: economics.expected_commissions,
      cash_flow_type: economics.cash_flow_type,
      combo_submission_mode: ticket.combo_submission_mode,
      broker_combo_guarantee_mode: ticket.broker_combo_guarantee_mode,
      kill_switch_version: killSwitchVersion,
      what_if_fallback_authorized: false,
      what_if_fallback_policy_version: null,
    },
  };
  const commandJson = JSON.stringify(command);
  const commandHash = await sha256Hex(commandJson);
  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO paper_entry_confirmations(
        confirmation_id,preview_id,ticket_id,confirmation_hash,confirmed_preview_hash,
        confirmed_ticket_hash,confirmation_json,confirmed_at,confirmed_by
      ) VALUES(?,?,?,?,?,?,?,?,?)`,
    ).bind(
      confirmationId, previewId, row.ticket_id, confirmationHash, row.preview_hash,
      row.ticket_hash, confirmationJson, confirmedAt, auth.actor,
    ),
    env.DB.prepare(
      `INSERT INTO paper_entry_intents(
        intent_id,idempotency_key,dossier_id,ticket_id,preview_id,confirmation_id,
        order_ref,requested_quantity,status,dispatch_authorized,command_hash,command_json,
        created_at,expires_at
      ) VALUES(?,?,?,?,?,?,?,?,'CONFIRMED',0,?,?,?,?)`,
    ).bind(
      intentId, `paper-entry-confirmation:${confirmationId}`, row.dossier_id, row.ticket_id,
      previewId, confirmationId, orderRef, ticket.quantity, commandHash, commandJson,
      confirmedAt, row.expires_at,
    ),
  ]);
  await audit(env.DB, "PAPER_ENTRY_CONFIRMED_LOCKED", auth.actor, null, {
    dossier_id: row.dossier_id,
    ticket_id: row.ticket_id,
    preview_id: previewId,
    confirmation_id: confirmationId,
    intent_id: intentId,
    dispatch_authorized: false,
  });
  return Response.json({
    status: "CONFIRMED",
    execution_state: "EXECUTION_LOCKED",
    intent_id: intentId,
    confirmation_id: confirmationId,
    dispatch_authorized: false,
    transmitted: false,
    next_required_step: "OPERATOR_PREFLIGHT_AND_SEPARATE_PAPER_ARM",
  }, { status: 202 });
}

async function status(env: Env): Promise<Response> {
  const latest = await env.DB.prepare(
    `SELECT i.intent_id,i.dossier_id,i.ticket_id,i.preview_id,i.confirmation_id,i.status,
      i.dispatch_authorized,i.order_ref,i.broker_order_id,i.broker_perm_id,i.created_at,
      i.completed_at,i.last_error_code,t.verdict,t.material_drift_status,t.proposed_limit
     FROM paper_entry_intents i JOIN execution_revalidation_tickets t USING(ticket_id)
     ORDER BY i.created_at DESC LIMIT 1`,
  ).first<Record<string, unknown>>();
  return Response.json({
    latest: latest ?? null,
    execution_environment: "IBKR_PAPER_SIMULATOR",
    paper_adapter_code: "READY_OFFLINE",
    paper_runtime_default: "DISABLED",
    paper_real_order_test: "NOT_RUN",
    live_execution: "FORBIDDEN",
  });
}

export async function routePaperEntryAuthenticated(
  request: Request,
  env: Env,
  auth: AuthContext,
  path: string,
  readJsonBody: () => Promise<unknown>,
): Promise<Response | null> {
  if (path === "/api/broker/paper-entry/status" && request.method === "GET") {
    return status(env);
  }
  if (path === "/api/broker/paper-entry/preview" && request.method === "POST") {
    return createPreview(request, env, auth, await readJsonBody());
  }
  const confirm = path.match(/^\/api\/broker\/paper-entry\/previews\/([^/]+)\/confirm$/);
  if (confirm && request.method === "POST") {
    return confirmPreview(request, env, auth, decodeURIComponent(confirm[1]!));
  }
  return null;
}
