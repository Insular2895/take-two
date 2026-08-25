import { env } from "cloudflare:test";
import { afterEach, describe, expect, it, vi } from "vitest";

import { handleRequest } from "../src/index";
import { parseAnalysisBudgetRequest } from "../src/research-domain";
import { hmacHex, sha256Hex } from "../src/research-security";

const CALLBACK_SECRET = "test-analysis-callback-secret-at-least-32-bytes";
const ACTION_PASSWORD = "test-action-password-123!";
const ACCESS = {
  aud: "local-take-two-control",
  getIdentity: async () => ({ email: "local-admin@take-two.invalid" }),
} as CloudflareAccessContext;

afterEach(() => vi.unstubAllGlobals());

async function session(): Promise<{ cookie: string; csrf: string }> {
  const response = await handleRequest(new Request("https://control.test/api/session"), env, ACCESS);
  const payload = await response.clone().json<{ csrf_token: string }>();
  return {
    cookie: (response.headers.get("Set-Cookie") ?? "").split(";")[0]!,
    csrf: payload.csrf_token,
  };
}

async function signedRequest(
  path: string,
  analysisId: string,
  method = "POST",
  payload?: unknown,
  nonce = crypto.randomUUID().replaceAll("-", ""),
  timestamp = Math.floor(Date.now() / 1000),
): Promise<Request> {
  const body = payload === undefined ? "" : JSON.stringify(payload);
  const bodyHash = await sha256Hex(body);
  const signature = await hmacHex(
    CALLBACK_SECRET,
    [timestamp, nonce, analysisId, method, path, bodyHash].join("\n"),
  );
  return new Request(`https://control.test${path}`, {
    method,
    headers: {
      ...(payload === undefined ? {} : { "Content-Type": "application/json" }),
      "X-TTWO-Timestamp": String(timestamp),
      "X-TTWO-Nonce": nonce,
      "X-TTWO-Content-SHA256": bodyHash,
      "X-TTWO-Analysis-Id": analysisId,
      "X-TTWO-Signature": signature,
    },
    ...(method === "GET" ? {} : { body }),
  });
}

async function insertAnalysis(analysisId: string): Promise<void> {
  await env.DB.prepare(
    `INSERT INTO analysis_requests(analysis_request_id,request_hash,preferred_budget,
      target_budget,maximum_budget,minimum_spend_policy,market_data_mode,currency,
      status,created_at,created_by) VALUES(?,?,?,?,?,?,?,'EUR','QUEUED',?,?)`,
  ).bind(
    analysisId, "a".repeat(64), 800, 1000, 1500, "SOFT", "SYNTHETIC_DEMO",
    new Date().toISOString(), "access:test@example.com",
  ).run();
}

describe("Phase M research request boundary", () => {
  it("rejects unknown fields, non-finite values, and invalid budget order", () => {
    expect(() => parseAnalysisBudgetRequest({
      preferred_budget: 800,
      target_budget: 1000,
      maximum_budget: 1500,
      minimum_spend_policy: "SOFT",
      market_data_mode: "SYNTHETIC_DEMO",
      currency: "EUR",
      repository: "attacker/repository",
    })).toThrow("INVALID_UNKNOWN_FIELD");
    expect(() => parseAnalysisBudgetRequest({
      preferred_budget: 1200,
      target_budget: 1000,
      maximum_budget: 1500,
      minimum_spend_policy: "SOFT",
      market_data_mode: "SYNTHETIC_DEMO",
      currency: "EUR",
    })).toThrow("INVALID_BUDGET_ORDER");
  });

  it("launches with only an immutable analysis id in the governed dispatch", async () => {
    const outbound = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
      expect(body).toEqual({
        ref: "main",
        inputs: { analysis_request_id: expect.stringMatching(/^analysis-[a-f0-9]{24}$/) },
      });
      expect(init?.headers).toMatchObject({ Authorization: "Bearer github-test-token" });
      return new Response(null, { status: 204 });
    });
    vi.stubGlobal("fetch", outbound);
    const auth = await session();
    const response = await handleRequest(new Request("https://control.test/api/research/analyses", {
      method: "POST",
      headers: {
        Cookie: auth.cookie,
        "Content-Type": "application/json",
        "X-CSRF-Token": auth.csrf,
        "X-Action-Password": ACTION_PASSWORD,
      },
      body: JSON.stringify({
        preferred_budget: 800,
        target_budget: 1000,
        maximum_budget: 1500,
        minimum_spend_policy: "SOFT",
        market_data_mode: "SYNTHETIC_DEMO",
        currency: "EUR",
      }),
    }), env, ACCESS);
    expect(response.status).toBe(202);
    expect(outbound).toHaveBeenCalledOnce();
    const conflicting = await handleRequest(new Request("https://control.test/api/research/analyses", {
      method: "POST",
      headers: {
        Cookie: auth.cookie,
        "Content-Type": "application/json",
        "X-CSRF-Token": auth.csrf,
        "X-Action-Password": ACTION_PASSWORD,
      },
      body: JSON.stringify({
        preferred_budget: 800,
        target_budget: 1100,
        maximum_budget: 1500,
        minimum_spend_policy: "SOFT",
        market_data_mode: "SYNTHETIC_DEMO",
        currency: "EUR",
      }),
    }), env, ACCESS);
    expect(conflicting.status).toBe(409);
    expect(outbound).toHaveBeenCalledOnce();
    const stored = await env.DB.prepare("SELECT status,created_by FROM analysis_requests")
      .first<{ status: string; created_by: string }>();
    expect(stored).toEqual({ status: "QUEUED", created_by: "access:local-admin@take-two.invalid" });
  });
});

describe("signed runner protocol and immutable persistence", () => {
  it("rejects tampering, expired timestamps, and replay without Access", async () => {
    const analysisId = "analysis-111111111111111111111111";
    await insertAnalysis(analysisId);
    const path = `/api/internal/research/analyses/${analysisId}/request`;
    const valid = await signedRequest(path, analysisId, "GET", undefined, "nonce-valid-request-1");
    expect((await handleRequest(valid, env, undefined)).status).toBe(200);
    const replay = await signedRequest(path, analysisId, "GET", undefined, "nonce-valid-request-1");
    expect((await handleRequest(replay, env, undefined)).status).toBe(409);
    const expired = await signedRequest(
      path,
      analysisId,
      "GET",
      undefined,
      "nonce-expired-request-2",
      Math.floor(Date.now() / 1000) - 600,
    );
    expect((await handleRequest(expired, env, undefined)).status).toBe(403);
    const tampered = await signedRequest(path, analysisId, "GET", undefined, "nonce-tampered-request-3");
    tampered.headers.set("X-TTWO-Content-SHA256", "f".repeat(64));
    expect((await handleRequest(tampered, env, undefined)).status).toBe(403);
    const callbackPath = `/api/internal/research/analyses/${analysisId}/callback`;
    const oversizedPayload = { padding: "x".repeat(512 * 1024) };
    const oversized = await signedRequest(
      callbackPath,
      analysisId,
      "POST",
      oversizedPayload,
      "nonce-oversized-request-4",
    );
    expect((await handleRequest(oversized, env, undefined)).status).toBe(413);
  });

  it("persists a complete browsable universe and creates only a PLANNED dossier", async () => {
    const analysisId = "analysis-222222222222222222222222";
    const candidateId = "cand-3333333333333333";
    const run = "12345";
    const commit = "4".repeat(40);
    await insertAnalysis(analysisId);
    const callbackPath = `/api/internal/research/analyses/${analysisId}/callback`;
    const common = { analysis_request_id: analysisId, github_run_id: run, git_commit: commit };
    const started = await signedRequest(
      callbackPath, analysisId, "POST", { kind: "STARTED", ...common }, "nonce-started-0001",
    );
    expect((await handleRequest(started, env, undefined)).status).toBe(200);
    const summary = {
      candidate_id: candidateId,
      architecture: "bull_call_spread",
      recipe_id: "bull-call-spread-v1",
      strategy_name: "Bull Call Spread",
      leg_summary: "LONG 1× CALL 240 | SHORT 1× CALL 260",
      engine_rank: 1,
      pareto_rank: 1,
      quantity: 1,
      leg_count: 2,
      expiration: "2027-11-19",
      common_expiry: true,
      dte: 482,
      signed_entry_cash_flow: -800,
      entry_cash_flow_type: "DEBIT",
      capital_required: 800,
      maximum_loss: 800,
      maximum_gain: 1200,
      break_even_points: [248],
      net_delta: 0.3,
      net_theta: null,
      average_implied_volatility: 0.36,
      maximum_relative_spread: 0.08,
      minimum_open_interest: 400,
      expected_pnl: null,
      expected_return: null,
      return_on_capital: null,
      return_on_risk: null,
      probability_profit: null,
      probability_loss_25: null,
      probability_loss_50: null,
      probability_loss_70: null,
      var_95: null,
      cvar_95: null,
      risk_on_capital: null,
      distance_to_target_budget: -200,
      headroom_to_hard_maximum: 700,
      theta_per_capital_day: null,
      flat_spot_7d: null,
      flat_spot_30d: null,
      flat_spot_60d: null,
      flat_spot_90d: null,
      net_gamma: null,
      net_vega: null,
      data_freshness: "FRESH",
      budget_status: "WITHIN_PREFERRED_RANGE",
      eligible: true,
      research_eligible: true,
      paper_eligible: true,
      pruned: false,
      reason_codes: [],
      score_probability: null,
      score_payoff: null,
      score_risk: null,
      score_robustness: null,
      score_executability: null,
      score_opportunity: null,
      score_evidence: null,
      score_model_agreement: null,
      score_execution_quality: null,
      trade_economics_ticket_hash: "5".repeat(64),
    };
    const detail = {
      candidate_id: candidateId,
      phase_m_context_id: "phase-m-context-6666666666666666",
      phase_m_context_hash: "6".repeat(64),
      legs: [],
      limitations: [],
      explanation: [],
      trade_economics_ticket: {},
    };
    const batch = await signedRequest(callbackPath, analysisId, "POST", {
      kind: "CANDIDATE_BATCH",
      batch_index: 0,
      candidates: [{ summary, detail }],
      ...common,
    }, "nonce-batch-0000002");
    expect((await handleRequest(batch, env, undefined)).status).toBe(200);
    const result = {
      analysis_request_id: analysisId,
      status: "COMPLETE",
      verdict: "RESEARCH_CANDIDATES_AVAILABLE",
      market_data_mode: "SYNTHETIC_DEMO",
      snapshot_id: "synthetic-demo-v1",
      snapshot_as_of: "2026-07-25T20:00:00Z",
      snapshot_hash: "7".repeat(64),
      catalog_hash: "8".repeat(64),
      config_hash: "9".repeat(64),
      phase_m_context_id: "phase-m-context-6666666666666666",
      phase_m_context_hash: "6".repeat(64),
      total_generated: 1,
      total_pruned: 0,
      total_research_eligible: 1,
      total_paper_eligible: 1,
      combinations_by_architecture: { bull_call_spread: 1 },
      best_overall_ids: [candidateId],
      best_by_architecture: { bull_call_spread: candidateId },
      no_trade_reasons: [],
      warnings: ["SYNTHETIC_DEMO"],
      safety: { read_only: true, transmit: false, order_capability: "forbidden" },
    };
    const complete = await signedRequest(
      callbackPath, analysisId, "POST", { kind: "COMPLETE", result, ...common },
      "nonce-complete-0003",
    );
    expect((await handleRequest(complete, env, undefined)).status).toBe(200);

    const auth = await session();
    const list = await handleRequest(
      new Request(`https://control.test/api/research/analyses/${analysisId}/candidates`, {
        headers: { Cookie: auth.cookie },
      }), env, ACCESS,
    );
    expect((await list.json<{ candidates: unknown[] }>()).candidates).toHaveLength(1);
    const selected = await handleRequest(new Request(
      `https://control.test/api/research/analyses/${analysisId}/candidates/${candidateId}/select`,
      {
        method: "POST",
        headers: {
          Cookie: auth.cookie,
          "Content-Type": "application/json",
          "X-CSRF-Token": auth.csrf,
          "X-Action-Password": ACTION_PASSWORD,
        },
        body: "{}",
      },
    ), env, ACCESS);
    expect(selected.status).toBe(201);
    expect(await selected.json()).toMatchObject({
      message: "IBKR EXECUTION NOT CONFIGURED",
      dossier: {
        state: "PLANNED",
        actual_entry_cash_flow: null,
        actual_opened_at: null,
        execution: { configured: false, transmitted: false, order_capability: "forbidden" },
      },
    });
    expect((await env.DB.prepare("SELECT count(*) AS total FROM positions").first<{ total: number }>())?.total).toBe(0);
    expect((await env.DB.prepare("SELECT state FROM planned_positions").first<{ state: string }>())?.state).toBe("PLANNED");
  });
});
