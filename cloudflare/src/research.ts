import { requireActionPassword, requireCsrf } from "./auth";
import { audit } from "./db";
import { randomId } from "./domain";
import {
  candidateFromRow,
  canonicalBudgetJson,
  exactKeys,
  parseAnalysisBudgetRequest,
} from "./research-domain";
import { decodeInternalJson, sha256Hex, verifyInternalRequest } from "./research-security";
import type { AuthContext } from "./types";
import type { AnalysisBudgetRequest, CallbackCandidate, CandidateSummaryRecord } from "./research-types";

const ANALYSIS_ID = /^analysis-[a-f0-9]{24}$/;
const CANDIDATE_ID = /^cand-[a-f0-9]{16}$/;
const HASH = /^[a-f0-9]{64}$/;
const GIT_COMMIT = /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/;
const ACTIVE_STATUSES = new Set(["CREATED", "QUEUED", "RUNNING"]);
const COMPLETE_STATUSES = new Set(["COMPLETE", "NO_TRADE"]);
const LAUNCH_COOLDOWN_MS = 30_000;

function randomAnalysisId(): string {
  return `analysis-${[...crypto.getRandomValues(new Uint8Array(12))]
    .map((byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

function record(value: unknown, code = "INVALID_RESEARCH_PAYLOAD"): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error(code);
  return value as Record<string, unknown>;
}

function json(value: unknown): string {
  return JSON.stringify(value ?? null);
}

export async function dispatchAnalysis(env: Env, analysisId: string): Promise<void> {
  const token = env.GITHUB_ACTIONS_TOKEN?.trim() ?? "";
  const repository = env.GITHUB_REPOSITORY?.trim() ?? "";
  const workflow = env.GITHUB_WORKFLOW?.trim() ?? "";
  const ref = env.GITHUB_GOVERNED_REF?.trim() ?? "";
  if (!token) throw new Error("GITHUB_ACTIONS_TOKEN_NOT_CONFIGURED");
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repository)) {
    throw new Error("INVALID_GITHUB_REPOSITORY_CONFIG");
  }
  if (!/^[A-Za-z0-9_.-]+\.ya?ml$/.test(workflow)) {
    throw new Error("INVALID_GITHUB_WORKFLOW_CONFIG");
  }
  if (!/^[A-Za-z0-9._/-]{1,128}$/.test(ref)) throw new Error("INVALID_GITHUB_REF_CONFIG");
  const response = await fetch(
    `https://api.github.com/repos/${repository}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`,
    {
      method: "POST",
      headers: {
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "User-Agent": "take-two-control-worker",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({ ref, inputs: { analysis_request_id: analysisId } }),
    },
  );
  if (response.status !== 204 && response.status !== 200) {
    throw new Error(`GITHUB_WORKFLOW_DISPATCH_FAILED_${response.status}`);
  }
}

async function launchAnalysis(
  request: Request,
  env: Env,
  auth: AuthContext,
  body: unknown,
): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "LAUNCH_RESEARCH_ANALYSIS");
  const budget = parseAnalysisBudgetRequest(body);
  const requestHash = await sha256Hex(canonicalBudgetJson(budget));
  const active = await env.DB.prepare(
    `SELECT analysis_request_id,request_hash,status FROM analysis_requests
     WHERE status IN ('CREATED','QUEUED','RUNNING') ORDER BY created_at DESC LIMIT 1`,
  ).first<Record<string, unknown>>();
  if (active) {
    if (String(active.request_hash) === requestHash) {
      return Response.json({
        analysis_request_id: active.analysis_request_id,
        status: active.status,
        idempotent: true,
      });
    }
    return Response.json({ error: "ANALYSIS_ALREADY_ACTIVE" }, { status: 409 });
  }
  const latest = await env.DB.prepare(
    "SELECT created_at FROM analysis_requests ORDER BY created_at DESC LIMIT 1",
  ).first<{ created_at: string }>();
  if (latest && Date.now() - Date.parse(latest.created_at) < LAUNCH_COOLDOWN_MS) {
    return Response.json({ error: "ANALYSIS_LAUNCH_COOLDOWN" }, { status: 429 });
  }
  const analysisId = randomAnalysisId();
  const createdAt = new Date().toISOString();
  await env.DB.batch([
    env.DB.prepare(
      `INSERT INTO analysis_requests(
        analysis_request_id,request_hash,preferred_budget,target_budget,maximum_budget,
        minimum_spend_policy,market_data_mode,currency,status,created_at,created_by
      ) VALUES(?,?,?,?,?,?,?,?, 'CREATED',?,?)`,
    ).bind(
      analysisId, requestHash, budget.preferred_budget, budget.target_budget,
      budget.maximum_budget, budget.minimum_spend_policy, budget.market_data_mode,
      budget.currency, createdAt, auth.actor,
    ),
    env.DB.prepare(
      `INSERT INTO analysis_runs(event_id,analysis_request_id,created_at,event_type,step,detail_json)
       VALUES(?,?,?,'CREATED','REQUEST_VALIDATED','{}')`,
    ).bind(randomId("analysis-event"), analysisId, createdAt),
  ]);
  try {
    await dispatchAnalysis(env, analysisId);
    const queuedAt = new Date().toISOString();
    await env.DB.batch([
      env.DB.prepare(
        "UPDATE analysis_requests SET status='QUEUED',queued_at=? WHERE analysis_request_id=? AND status='CREATED'",
      ).bind(queuedAt, analysisId),
      env.DB.prepare(
        `INSERT INTO analysis_runs(event_id,analysis_request_id,created_at,event_type,step,detail_json)
         VALUES(?,?,?,'QUEUED','GITHUB_WORKFLOW_DISPATCHED','{}')`,
      ).bind(randomId("analysis-event"), analysisId, queuedAt),
    ]);
    await audit(env.DB, "RESEARCH_ANALYSIS_QUEUED", auth.actor, null, {
      analysis_request_id: analysisId,
      request_hash: requestHash,
      market_data_mode: budget.market_data_mode,
    });
    return Response.json({ analysis_request_id: analysisId, status: "QUEUED" }, { status: 202 });
  } catch (error) {
    const failure = error instanceof Error ? error.message : "GITHUB_WORKFLOW_DISPATCH_FAILED";
    await env.DB.prepare(
      "UPDATE analysis_requests SET status='FAILED',failure_code=?,completed_at=? WHERE analysis_request_id=?",
    ).bind(failure, new Date().toISOString(), analysisId).run();
    throw error;
  }
}

function analysisResponse(row: Record<string, unknown>): Record<string, unknown> {
  const parsed = { ...row };
  for (const field of [
    "combinations_by_architecture_json", "best_overall_ids_json", "best_by_architecture_json",
    "no_trade_reasons_json", "warnings_json",
  ]) {
    const value = parsed[field];
    parsed[field.replace(/_json$/, "")] = value === null || value === undefined
      ? null : JSON.parse(String(value));
    delete parsed[field];
  }
  return parsed;
}

async function listAnalyses(env: Env): Promise<Response> {
  const result = await env.DB.prepare(
    `SELECT analysis_request_id,request_hash,preferred_budget,target_budget,maximum_budget,
      minimum_spend_policy,market_data_mode,currency,status,created_at,queued_at,started_at,
      completed_at,verdict,total_generated,total_pruned,total_research_eligible,
      total_paper_eligible,failure_code FROM analysis_requests ORDER BY created_at DESC LIMIT 100`,
  ).all<Record<string, unknown>>();
  return Response.json({ analyses: result.results, safety: safety() });
}

async function analysisDetail(env: Env, analysisId: string): Promise<Response> {
  const analysis = await env.DB.prepare(
    "SELECT * FROM analysis_requests WHERE analysis_request_id=?",
  ).bind(analysisId).first<Record<string, unknown>>();
  if (!analysis) return Response.json({ error: "ANALYSIS_NOT_FOUND" }, { status: 404 });
  const runs = await env.DB.prepare(
    "SELECT * FROM analysis_runs WHERE analysis_request_id=? ORDER BY created_at ASC",
  ).bind(analysisId).all<Record<string, unknown>>();
  return Response.json({ analysis: analysisResponse(analysis), runs: runs.results, safety: safety() });
}

async function candidateList(env: Env, analysisId: string): Promise<Response> {
  const result = await env.DB.prepare(
    "SELECT * FROM analysis_candidate_summaries WHERE analysis_request_id=? ORDER BY engine_rank ASC",
  ).bind(analysisId).all<Record<string, unknown>>();
  return Response.json({
    analysis_request_id: analysisId,
    candidates: result.results.map(candidateFromRow),
    complete_universe: true,
    safety: safety(),
  });
}

async function candidateDetail(env: Env, analysisId: string, candidateId: string): Promise<Response> {
  const row = await env.DB.prepare(
    `SELECT s.*,d.detail_json FROM analysis_candidate_summaries s
     JOIN analysis_candidate_details d USING(analysis_request_id,candidate_id)
     WHERE s.analysis_request_id=? AND s.candidate_id=?`,
  ).bind(analysisId, candidateId).first<Record<string, unknown>>();
  if (!row) return Response.json({ error: "CANDIDATE_NOT_FOUND" }, { status: 404 });
  return Response.json({
    summary: candidateFromRow(row),
    detail: JSON.parse(String(row.detail_json)),
    safety: safety(),
  });
}

function safety(): Record<string, boolean | string> {
  return { read_only: true, transmit: false, order_capability: "forbidden" };
}

async function selectCandidate(
  request: Request,
  env: Env,
  auth: AuthContext,
  analysisId: string,
  candidateId: string,
): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "SELECT_RESEARCH_CANDIDATE");
  const row = await env.DB.prepare(
    `SELECT a.status,a.snapshot_id,a.snapshot_hash,a.phase_m_context_id,a.phase_m_context_hash,
      a.git_commit,s.*,d.detail_json
     FROM analysis_requests a JOIN analysis_candidate_summaries s USING(analysis_request_id)
     JOIN analysis_candidate_details d USING(analysis_request_id,candidate_id)
     WHERE a.analysis_request_id=? AND s.candidate_id=?`,
  ).bind(analysisId, candidateId).first<Record<string, unknown>>();
  if (!row) return Response.json({ error: "CANDIDATE_NOT_FOUND" }, { status: 404 });
  if (!COMPLETE_STATUSES.has(String(row.status))) {
    return Response.json({ error: "ANALYSIS_NOT_COMPLETE" }, { status: 409 });
  }
  if (!Boolean(row.paper_eligible) || Boolean(row.pruned)) {
    return Response.json({ error: "CANDIDATE_NOT_PAPER_ELIGIBLE" }, { status: 409 });
  }
  for (const field of ["snapshot_hash", "phase_m_context_hash", "trade_economics_ticket_hash"]) {
    if (!HASH.test(String(row[field]))) throw new Error("INVALID_SELECTION_PROVENANCE");
  }
  const selectionId = randomId("selection");
  const dossierId = randomId("planned-dossier");
  const selectedAt = new Date().toISOString();
  const detail = JSON.parse(String(row.detail_json)) as Record<string, unknown>;
  const dossier = {
    schema_version: "phase-m-planned-position/1.0",
    dossier_id: dossierId,
    state: "PLANNED",
    analysis_request_id: analysisId,
    candidate_id: candidateId,
    trade_economics_ticket_hash: row.trade_economics_ticket_hash,
    phase_m_context_id: row.phase_m_context_id,
    phase_m_context_hash: row.phase_m_context_hash,
    snapshot_id: row.snapshot_id,
    snapshot_hash: row.snapshot_hash,
    git_commit: row.git_commit,
    planned_entry_cash_flow: row.signed_entry_cash_flow,
    estimated_capital_required: row.capital_required,
    actual_entry_cash_flow: null,
    actual_opened_at: null,
    candidate_detail: detail,
    execution: { configured: false, transmitted: false, order_capability: "forbidden" },
  };
  try {
    await env.DB.batch([
      env.DB.prepare(
        `INSERT INTO candidate_selections(selection_id,analysis_request_id,candidate_id,
          selected_at,selected_by,trade_economics_ticket_hash,phase_m_context_id,
          phase_m_context_hash,snapshot_id,snapshot_hash,git_commit)
         VALUES(?,?,?,?,?,?,?,?,?,?,?)`,
      ).bind(
        selectionId, analysisId, candidateId, selectedAt, auth.actor,
        row.trade_economics_ticket_hash, row.phase_m_context_id, row.phase_m_context_hash,
        row.snapshot_id, row.snapshot_hash, row.git_commit,
      ),
      env.DB.prepare(
        `INSERT INTO planned_positions(dossier_id,selection_id,analysis_request_id,candidate_id,
          state,planned_entry_cash_flow,estimated_capital_required,actual_entry_cash_flow,
          actual_opened_at,dossier_json,created_at,created_by)
         VALUES(?,?,?,?,'PLANNED',?,?,NULL,NULL,?,?,?)`,
      ).bind(
        dossierId, selectionId, analysisId, candidateId, row.signed_entry_cash_flow,
        row.capital_required, JSON.stringify(dossier), selectedAt, auth.actor,
      ),
    ]);
  } catch {
    const existing = await env.DB.prepare(
      "SELECT selection_id FROM candidate_selections WHERE analysis_request_id=? AND candidate_id=?",
    ).bind(analysisId, candidateId).first<{ selection_id: string }>();
    if (existing) {
      return Response.json({ selection_id: existing.selection_id, idempotent: true, safety: safety() });
    }
    throw new Error("CANDIDATE_SELECTION_FAILED");
  }
  await audit(env.DB, "RESEARCH_CANDIDATE_SELECTED", auth.actor, null, {
    analysis_request_id: analysisId,
    candidate_id: candidateId,
    selection_id: selectionId,
    dossier_id: dossierId,
  });
  return Response.json({
    selection_id: selectionId,
    dossier,
    message: "IBKR EXECUTION NOT CONFIGURED",
    safety: safety(),
  }, { status: 201 });
}

async function cancelAnalysis(
  request: Request,
  env: Env,
  auth: AuthContext,
  analysisId: string,
): Promise<Response> {
  requireCsrf(request, auth);
  await requireActionPassword(request, env, auth, "CANCEL_RESEARCH_ANALYSIS");
  const completedAt = new Date().toISOString();
  const result = await env.DB.prepare(
    `UPDATE analysis_requests SET status='CANCELLED',completed_at=?
     WHERE analysis_request_id=? AND status IN ('CREATED','QUEUED','RUNNING')`,
  ).bind(completedAt, analysisId).run();
  if (!result.meta.changes) return Response.json({ error: "ANALYSIS_NOT_CANCELLABLE" }, { status: 409 });
  await audit(env.DB, "RESEARCH_ANALYSIS_CANCELLED", auth.actor, null, {
    analysis_request_id: analysisId,
    github_job_may_finish_without_being_admitted: true,
  });
  return Response.json({ analysis_request_id: analysisId, status: "CANCELLED", safety: safety() });
}

function callbackSummary(raw: unknown): CandidateSummaryRecord {
  const value = record(raw, "INVALID_CANDIDATE_SUMMARY") as unknown as CandidateSummaryRecord;
  if (!CANDIDATE_ID.test(value.candidate_id) || !Number.isInteger(value.engine_rank) || value.engine_rank < 1) {
    throw new Error("INVALID_CANDIDATE_SUMMARY");
  }
  if (!HASH.test(value.trade_economics_ticket_hash)) throw new Error("INVALID_CANDIDATE_TICKET_HASH");
  for (const numeric of [
    value.signed_entry_cash_flow, value.capital_required, value.maximum_loss, value.maximum_gain,
    value.net_delta, value.net_theta, value.average_implied_volatility,
    value.maximum_relative_spread, value.expected_pnl, value.expected_return,
    value.return_on_capital, value.return_on_risk, value.probability_profit,
    value.probability_loss_25, value.probability_loss_50, value.probability_loss_70,
    value.var_95, value.cvar_95, value.risk_on_capital, value.distance_to_target_budget,
    value.headroom_to_hard_maximum, value.theta_per_capital_day, value.flat_spot_7d,
    value.flat_spot_30d, value.flat_spot_60d, value.flat_spot_90d, value.net_gamma,
    value.net_vega, value.score_opportunity, value.score_evidence,
    value.score_model_agreement, value.score_execution_quality,
  ]) {
    if (numeric !== null && !Number.isFinite(numeric)) throw new Error("INVALID_CANDIDATE_NUMBER");
  }
  return value;
}

function candidateStatements(env: Env, analysisId: string, items: CallbackCandidate[]): D1PreparedStatement[] {
  const statements: D1PreparedStatement[] = [];
  const columns = [
    "analysis_request_id", "candidate_id", "architecture", "recipe_id", "strategy_name",
    "leg_summary",
    "engine_rank", "pareto_rank", "quantity", "leg_count", "expiration", "common_expiry",
    "dte", "signed_entry_cash_flow", "entry_cash_flow_type", "capital_required",
    "maximum_loss", "maximum_gain", "break_even_points_json", "net_delta", "net_theta",
    "average_implied_volatility", "maximum_relative_spread", "minimum_open_interest",
    "expected_pnl", "expected_return", "return_on_capital", "return_on_risk",
    "probability_profit", "probability_loss_25", "probability_loss_50", "probability_loss_70",
    "var_95", "cvar_95", "risk_on_capital", "distance_to_target_budget",
    "headroom_to_hard_maximum", "theta_per_capital_day", "flat_spot_7d", "flat_spot_30d",
    "flat_spot_60d", "flat_spot_90d", "net_gamma", "net_vega", "data_freshness",
    "budget_status", "eligible", "research_eligible", "paper_eligible", "pruned",
    "reason_codes_json", "score_probability", "score_payoff", "score_risk",
    "score_robustness", "score_executability", "score_opportunity", "score_evidence",
    "score_model_agreement", "score_execution_quality", "trade_economics_ticket_hash",
  ];
  const placeholders = columns.map(() => "?").join(",");
  for (const item of items) {
    const summary = callbackSummary(item.summary);
    const detail = record(item.detail, "INVALID_CANDIDATE_DETAIL");
    if (detail.candidate_id !== summary.candidate_id) throw new Error("CANDIDATE_DETAIL_ID_MISMATCH");
    const detailJson = JSON.stringify(detail);
    if (detailJson.length > 64 * 1024) throw new Error("CANDIDATE_DETAIL_TOO_LARGE");
    const values = [
      analysisId, summary.candidate_id, summary.architecture, summary.recipe_id,
      summary.strategy_name, summary.leg_summary, summary.engine_rank, summary.pareto_rank, summary.quantity,
      summary.leg_count, summary.expiration, summary.common_expiry ? 1 : 0, summary.dte,
      summary.signed_entry_cash_flow, summary.entry_cash_flow_type, summary.capital_required,
      summary.maximum_loss, summary.maximum_gain, json(summary.break_even_points),
      summary.net_delta, summary.net_theta, summary.average_implied_volatility,
      summary.maximum_relative_spread, summary.minimum_open_interest, summary.expected_pnl,
      summary.expected_return, summary.return_on_capital, summary.return_on_risk,
      summary.probability_profit, summary.probability_loss_25, summary.probability_loss_50,
      summary.probability_loss_70, summary.var_95, summary.cvar_95, summary.risk_on_capital,
      summary.distance_to_target_budget, summary.headroom_to_hard_maximum,
      summary.theta_per_capital_day, summary.flat_spot_7d, summary.flat_spot_30d,
      summary.flat_spot_60d, summary.flat_spot_90d, summary.net_gamma, summary.net_vega,
      summary.data_freshness, summary.budget_status, summary.eligible ? 1 : 0,
      summary.research_eligible ? 1 : 0, summary.paper_eligible ? 1 : 0,
      summary.pruned ? 1 : 0, json(summary.reason_codes), summary.score_probability,
      summary.score_payoff, summary.score_risk, summary.score_robustness,
      summary.score_executability, summary.score_opportunity, summary.score_evidence,
      summary.score_model_agreement, summary.score_execution_quality,
      summary.trade_economics_ticket_hash,
    ];
    statements.push(
      env.DB.prepare(
        `INSERT OR IGNORE INTO analysis_candidate_summaries(${columns.join(",")})
         VALUES(${placeholders})`,
      ).bind(...values),
      env.DB.prepare(
        `INSERT OR IGNORE INTO analysis_candidate_details(analysis_request_id,candidate_id,detail_json)
         VALUES(?,?,?)`,
      ).bind(analysisId, summary.candidate_id, detailJson),
    );
  }
  return statements;
}

async function receiveCallback(
  request: Request,
  env: Env,
  analysisId: string,
): Promise<Response> {
  const verified = await verifyInternalRequest(request, env, analysisId);
  const payload = record(decodeInternalJson(verified.body), "INVALID_CALLBACK_PAYLOAD");
  const kind = String(payload.kind ?? "");
  if (payload.analysis_request_id !== analysisId) throw new Error("CALLBACK_ANALYSIS_ID_MISMATCH");
  const analysis = await env.DB.prepare(
    "SELECT status,github_run_id,git_commit FROM analysis_requests WHERE analysis_request_id=?",
  ).bind(analysisId).first<{ status: string; github_run_id: string | null; git_commit: string | null }>();
  if (!analysis) return Response.json({ error: "ANALYSIS_NOT_FOUND" }, { status: 404 });
  if (analysis.status === "CANCELLED") {
    return Response.json({ error: "ANALYSIS_CANCELLED" }, { status: 409 });
  }
  const now = new Date().toISOString();
  const runId = String(payload.github_run_id ?? "");
  const gitCommit = String(payload.git_commit ?? "");
  if (!runId || !GIT_COMMIT.test(gitCommit)) throw new Error("INVALID_CALLBACK_PROVENANCE");
  if (kind === "STARTED") {
    exactKeys(payload, ["analysis_request_id", "git_commit", "github_run_id", "kind"]);
    if (
      analysis.status === "RUNNING" && analysis.github_run_id === runId &&
      analysis.git_commit === gitCommit
    ) return Response.json({ accepted: true, idempotent: true, status: "RUNNING" });
    await env.DB.batch([
      env.DB.prepare(
        `UPDATE analysis_requests SET status='RUNNING',started_at=coalesce(started_at,?),
          github_run_id=?,git_commit=? WHERE analysis_request_id=? AND status IN ('CREATED','QUEUED','RUNNING')`,
      ).bind(now, runId, gitCommit, analysisId),
      env.DB.prepare(
        `INSERT OR IGNORE INTO analysis_runs(event_id,analysis_request_id,created_at,event_type,step,
          github_run_id,git_commit,detail_json) VALUES(?,?,?,'RUNNING','PYTHON_JOB_STARTED',?,?, '{}')`,
      ).bind(`analysis-started-${analysisId}`, analysisId, now, runId, gitCommit),
    ]);
    return Response.json({ accepted: true, status: "RUNNING" });
  }
  if (!ACTIVE_STATUSES.has(analysis.status)) {
    if (
      (COMPLETE_STATUSES.has(analysis.status) && kind === "COMPLETE") ||
      (analysis.status === "FAILED" && kind === "FAILED")
    ) {
      return Response.json({ accepted: true, idempotent: true, status: analysis.status });
    }
    return Response.json({ error: "ANALYSIS_NOT_ACTIVE" }, { status: 409 });
  }
  if (kind === "PROGRESS") {
    exactKeys(payload, ["analysis_request_id", "git_commit", "github_run_id", "kind", "step"]);
    const step = String(payload.step ?? "");
    if (!/^[A-Z0-9_]{3,80}$/.test(step)) throw new Error("INVALID_ANALYSIS_PROGRESS_STEP");
    await env.DB.prepare(
      `INSERT OR IGNORE INTO analysis_runs(event_id,analysis_request_id,created_at,event_type,step,
        github_run_id,git_commit,detail_json) VALUES(?,?,?,'PROGRESS',?,?,?,'{}')`,
    ).bind(
      `analysis-progress-${analysisId}-${step.toLowerCase()}`,
      analysisId,
      now,
      step,
      runId,
      gitCommit,
    ).run();
    return Response.json({ accepted: true, step });
  }
  if (kind === "CANDIDATE_BATCH") {
    exactKeys(payload, [
      "analysis_request_id", "batch_index", "candidates", "git_commit", "github_run_id", "kind",
    ]);
    if (!Number.isInteger(payload.batch_index) || Number(payload.batch_index) < 0) {
      throw new Error("INVALID_CANDIDATE_BATCH_INDEX");
    }
    if (!Array.isArray(payload.candidates) || payload.candidates.length < 1 || payload.candidates.length > 20) {
      throw new Error("INVALID_CANDIDATE_BATCH_SIZE");
    }
    const candidates = payload.candidates.map((item) => {
      const candidate = record(item, "INVALID_CALLBACK_CANDIDATE");
      exactKeys(candidate, ["detail", "summary"]);
      return candidate as unknown as CallbackCandidate;
    });
    await env.DB.batch(candidateStatements(env, analysisId, candidates));
    return Response.json({ accepted: true, candidates: candidates.length });
  }
  if (kind === "FAILED") {
    exactKeys(payload, [
      "analysis_request_id", "error_code", "git_commit", "github_run_id", "kind",
    ]);
    const errorCode = String(payload.error_code ?? "PYTHON_RESEARCH_FAILED").slice(0, 120);
    await env.DB.prepare(
      `UPDATE analysis_requests SET status='FAILED',failure_code=?,completed_at=?,
        github_run_id=?,git_commit=? WHERE analysis_request_id=? AND status IN ('CREATED','QUEUED','RUNNING')`,
    ).bind(errorCode, now, runId, gitCommit, analysisId).run();
    return Response.json({ accepted: true, status: "FAILED" });
  }
  if (kind === "COMPLETE") {
    exactKeys(payload, ["analysis_request_id", "git_commit", "github_run_id", "kind", "result"]);
    const result = record(payload.result, "INVALID_ANALYSIS_RESULT");
    const status = String(result.status);
    if (status !== "COMPLETE" && status !== "NO_TRADE") throw new Error("INVALID_FINAL_STATUS");
    const totalGenerated = Number(result.total_generated);
    const persisted = await env.DB.prepare(
      "SELECT count(*) AS total FROM analysis_candidate_summaries WHERE analysis_request_id=?",
    ).bind(analysisId).first<{ total: number }>();
    if (!Number.isInteger(totalGenerated) || persisted?.total !== totalGenerated) {
      throw new Error("INCOMPLETE_CANDIDATE_UNIVERSE");
    }
    for (const field of ["snapshot_hash", "catalog_hash", "config_hash", "phase_m_context_hash"]) {
      if (!HASH.test(String(result[field]))) throw new Error("INVALID_FINAL_PROVENANCE");
    }
    if (result.analysis_request_id !== analysisId) throw new Error("FINAL_ANALYSIS_ID_MISMATCH");
    await env.DB.batch([
      env.DB.prepare(
        `UPDATE analysis_requests SET status=?,completed_at=?,github_run_id=?,git_commit=?,
          snapshot_id=?,snapshot_as_of=?,snapshot_hash=?,catalog_hash=?,config_hash=?,
          phase_m_context_id=?,phase_m_context_hash=?,verdict=?,total_generated=?,total_pruned=?,
          total_research_eligible=?,total_paper_eligible=?,combinations_by_architecture_json=?,
          best_overall_ids_json=?,best_by_architecture_json=?,no_trade_reasons_json=?,warnings_json=?
         WHERE analysis_request_id=? AND status IN ('CREATED','QUEUED','RUNNING')`,
      ).bind(
        status, now, runId, gitCommit, result.snapshot_id, result.snapshot_as_of,
        result.snapshot_hash, result.catalog_hash, result.config_hash, result.phase_m_context_id,
        result.phase_m_context_hash, result.verdict, totalGenerated, result.total_pruned,
        result.total_research_eligible, result.total_paper_eligible,
        json(result.combinations_by_architecture), json(result.best_overall_ids),
        json(result.best_by_architecture), json(result.no_trade_reasons), json(result.warnings),
        analysisId,
      ),
      env.DB.prepare(
        `INSERT INTO analysis_runs(event_id,analysis_request_id,created_at,event_type,step,
          github_run_id,git_commit,detail_json) VALUES(?,?,?,?,?,?,?,?)`,
      ).bind(
        randomId("analysis-event"), analysisId, now, status, "COMPLETE_UNIVERSE_PERSISTED",
        runId, gitCommit, json({ total_generated: totalGenerated, verdict: result.verdict }),
      ),
    ]);
    return Response.json({ accepted: true, status, total_generated: totalGenerated });
  }
  throw new Error("INVALID_CALLBACK_KIND");
}

async function internalRequest(env: Env, request: Request, analysisId: string): Promise<Response> {
  await verifyInternalRequest(request, env, analysisId);
  const row = await env.DB.prepare(
    `SELECT analysis_request_id,request_hash,preferred_budget,target_budget,maximum_budget,
      minimum_spend_policy,market_data_mode,currency,created_at,status
     FROM analysis_requests WHERE analysis_request_id=?`,
  ).bind(analysisId).first<Record<string, unknown>>();
  if (!row) return Response.json({ error: "ANALYSIS_NOT_FOUND" }, { status: 404 });
  if (!ACTIVE_STATUSES.has(String(row.status))) {
    return Response.json({ error: "ANALYSIS_NOT_ACTIVE" }, { status: 409 });
  }
  const budget: AnalysisBudgetRequest = {
    preferred_budget: Number(row.preferred_budget),
    target_budget: Number(row.target_budget),
    maximum_budget: Number(row.maximum_budget),
    minimum_spend_policy: String(row.minimum_spend_policy) as "SOFT" | "HARD",
    market_data_mode: String(row.market_data_mode) as AnalysisBudgetRequest["market_data_mode"],
    currency: "EUR",
  };
  return Response.json({
    analysis_request_id: row.analysis_request_id,
    request_hash: row.request_hash,
    budget,
    created_at: row.created_at,
  });
}

export async function routeInternalResearch(
  request: Request,
  env: Env,
  path: string,
): Promise<Response | null> {
  const requestMatch = path.match(/^\/api\/internal\/research\/analyses\/(analysis-[a-f0-9]{24})\/request$/);
  if (requestMatch && request.method === "GET") {
    return internalRequest(env, request, requestMatch[1]!);
  }
  const callbackMatch = path.match(/^\/api\/internal\/research\/analyses\/(analysis-[a-f0-9]{24})\/callback$/);
  if (callbackMatch && request.method === "POST") {
    return receiveCallback(request, env, callbackMatch[1]!);
  }
  if (path.startsWith("/api/internal/research/")) {
    return Response.json({ error: "NOT_FOUND" }, { status: 404 });
  }
  return null;
}

export async function routeResearchAuthenticated(
  request: Request,
  env: Env,
  auth: AuthContext,
  path: string,
  readJson: () => Promise<unknown>,
): Promise<Response | null> {
  if (path === "/api/research/analyses" && request.method === "GET") return listAnalyses(env);
  if (path === "/api/research/analyses" && request.method === "POST") {
    return launchAnalysis(request, env, auth, await readJson());
  }
  if (path === "/api/research/execution-capability" && request.method === "GET") {
    return Response.json({ configured: false, message: "IBKR EXECUTION NOT CONFIGURED", safety: safety() });
  }
  const analysis = path.match(/^\/api\/research\/analyses\/(analysis-[a-f0-9]{24})$/);
  if (analysis && request.method === "GET") return analysisDetail(env, analysis[1]!);
  const candidates = path.match(/^\/api\/research\/analyses\/(analysis-[a-f0-9]{24})\/candidates$/);
  if (candidates && request.method === "GET") return candidateList(env, candidates[1]!);
  const detail = path.match(
    /^\/api\/research\/analyses\/(analysis-[a-f0-9]{24})\/candidates\/(cand-[a-f0-9]{16})$/,
  );
  if (detail && request.method === "GET") return candidateDetail(env, detail[1]!, detail[2]!);
  const select = path.match(
    /^\/api\/research\/analyses\/(analysis-[a-f0-9]{24})\/candidates\/(cand-[a-f0-9]{16})\/select$/,
  );
  if (select && request.method === "POST") {
    return selectCandidate(request, env, auth, select[1]!, select[2]!);
  }
  const cancel = path.match(/^\/api\/research\/analyses\/(analysis-[a-f0-9]{24})\/cancel$/);
  if (cancel && request.method === "POST") return cancelAnalysis(request, env, auth, cancel[1]!);
  if (path.startsWith("/api/research/")) return Response.json({ error: "NOT_FOUND" }, { status: 404 });
  return null;
}
