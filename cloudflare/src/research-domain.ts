import type { AnalysisBudgetRequest, CandidateSummaryRecord } from "./research-types";

const BUDGET_KEYS = [
  "currency",
  "market_data_mode",
  "maximum_budget",
  "minimum_spend_policy",
  "preferred_budget",
  "target_budget",
] as const;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("INVALID_ANALYSIS_BUDGET_REQUEST");
  }
  return value as Record<string, unknown>;
}

export function exactKeys(value: Record<string, unknown>, expected: readonly string[]): void {
  const actual = Object.keys(value).sort();
  const canonical = [...expected].sort();
  if (actual.length !== canonical.length || actual.some((key, index) => key !== canonical[index])) {
    throw new Error("INVALID_UNKNOWN_FIELD");
  }
}

function finitePositive(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    throw new Error("INVALID_BUDGET_VALUE");
  }
  return value;
}

export function parseAnalysisBudgetRequest(value: unknown): AnalysisBudgetRequest {
  const raw = object(value);
  exactKeys(raw, BUDGET_KEYS);
  const preferred = finitePositive(raw.preferred_budget);
  const target = finitePositive(raw.target_budget);
  const maximum = finitePositive(raw.maximum_budget);
  if (!(preferred <= target && target <= maximum)) throw new Error("INVALID_BUDGET_ORDER");
  if (raw.minimum_spend_policy !== "SOFT" && raw.minimum_spend_policy !== "HARD") {
    throw new Error("INVALID_MINIMUM_SPEND_POLICY");
  }
  if (
    raw.market_data_mode !== "LAST_GOVERNED_SNAPSHOT" &&
    raw.market_data_mode !== "SYNTHETIC_DEMO"
  ) throw new Error("INVALID_MARKET_DATA_MODE");
  if (raw.currency !== "EUR") throw new Error("INVALID_BUDGET_CURRENCY");
  return {
    preferred_budget: preferred,
    target_budget: target,
    maximum_budget: maximum,
    minimum_spend_policy: raw.minimum_spend_policy,
    market_data_mode: raw.market_data_mode,
    currency: raw.currency,
  };
}

export function canonicalBudgetJson(value: AnalysisBudgetRequest): string {
  return JSON.stringify({
    currency: value.currency,
    market_data_mode: value.market_data_mode,
    maximum_budget: value.maximum_budget,
    minimum_spend_policy: value.minimum_spend_policy,
    preferred_budget: value.preferred_budget,
    target_budget: value.target_budget,
  });
}

export function policyCurrencyMaximumGain(
  maximumGain: unknown,
  legacyFxRate: unknown,
): number | null {
  if (maximumGain === null || maximumGain === undefined) return null;
  const value = Number(maximumGain);
  if (!Number.isFinite(value)) throw new Error("INVALID_CANDIDATE_NUMBER");
  if (legacyFxRate === null || legacyFxRate === undefined) return value;
  const rate = Number(legacyFxRate);
  if (!Number.isFinite(rate) || rate <= 0) throw new Error("INVALID_LEGACY_GAIN_FX_RATE");
  return Math.round(value * rate * 10_000) / 10_000;
}

export function candidateFromRow(row: Record<string, unknown>): CandidateSummaryRecord {
  const publicRow = { ...row };
  delete publicRow.break_even_points_json;
  delete publicRow.reason_codes_json;
  delete publicRow.legacy_maximum_gain_fx_rate;
  return {
    ...publicRow,
    break_even_points: JSON.parse(String(row.break_even_points_json)) as number[],
    reason_codes: JSON.parse(String(row.reason_codes_json)) as string[],
    eligible: Boolean(row.eligible),
    research_eligible: Boolean(row.research_eligible),
    paper_eligible: Boolean(row.paper_eligible),
    pruned: Boolean(row.pruned),
    common_expiry: Boolean(row.common_expiry),
    pareto_rank: row.pareto_rank === null ? null : Number(row.pareto_rank),
    capital_required: row.capital_required === null ? null : Number(row.capital_required),
    maximum_loss: row.maximum_loss === null ? null : Number(row.maximum_loss),
    maximum_gain: policyCurrencyMaximumGain(
      row.maximum_gain,
      row.legacy_maximum_gain_fx_rate,
    ),
    net_delta: row.net_delta === null ? null : Number(row.net_delta),
    net_theta: row.net_theta === null ? null : Number(row.net_theta),
    average_implied_volatility: row.average_implied_volatility === null
      ? null : Number(row.average_implied_volatility),
    maximum_relative_spread: row.maximum_relative_spread === null
      ? null : Number(row.maximum_relative_spread),
    minimum_open_interest: row.minimum_open_interest === null
      ? null : Number(row.minimum_open_interest),
    expected_pnl: row.expected_pnl === null ? null : Number(row.expected_pnl),
    probability_profit: row.probability_profit === null ? null : Number(row.probability_profit),
    cvar_95: row.cvar_95 === null ? null : Number(row.cvar_95),
    expected_return: row.expected_return === null ? null : Number(row.expected_return),
    return_on_capital: row.return_on_capital === null ? null : Number(row.return_on_capital),
    return_on_risk: row.return_on_risk === null ? null : Number(row.return_on_risk),
    probability_loss_25: row.probability_loss_25 === null ? null : Number(row.probability_loss_25),
    probability_loss_50: row.probability_loss_50 === null ? null : Number(row.probability_loss_50),
    probability_loss_70: row.probability_loss_70 === null ? null : Number(row.probability_loss_70),
    var_95: row.var_95 === null ? null : Number(row.var_95),
    risk_on_capital: row.risk_on_capital === null ? null : Number(row.risk_on_capital),
    distance_to_target_budget: row.distance_to_target_budget === null
      ? null : Number(row.distance_to_target_budget),
    headroom_to_hard_maximum: row.headroom_to_hard_maximum === null
      ? null : Number(row.headroom_to_hard_maximum),
    theta_per_capital_day: row.theta_per_capital_day === null
      ? null : Number(row.theta_per_capital_day),
    flat_spot_7d: row.flat_spot_7d === null ? null : Number(row.flat_spot_7d),
    flat_spot_30d: row.flat_spot_30d === null ? null : Number(row.flat_spot_30d),
    flat_spot_60d: row.flat_spot_60d === null ? null : Number(row.flat_spot_60d),
    flat_spot_90d: row.flat_spot_90d === null ? null : Number(row.flat_spot_90d),
    net_gamma: row.net_gamma === null ? null : Number(row.net_gamma),
    net_vega: row.net_vega === null ? null : Number(row.net_vega),
    score_probability: row.score_probability === null ? null : Number(row.score_probability),
    score_payoff: row.score_payoff === null ? null : Number(row.score_payoff),
    score_risk: row.score_risk === null ? null : Number(row.score_risk),
    score_robustness: row.score_robustness === null ? null : Number(row.score_robustness),
    score_executability: row.score_executability === null
      ? null : Number(row.score_executability),
    score_opportunity: row.score_opportunity === null ? null : Number(row.score_opportunity),
    score_evidence: row.score_evidence === null ? null : Number(row.score_evidence),
    score_model_agreement: row.score_model_agreement === null
      ? null : Number(row.score_model_agreement),
    score_execution_quality: row.score_execution_quality === null
      ? null : Number(row.score_execution_quality),
    candidate_id: String(row.candidate_id),
    architecture: String(row.architecture),
    recipe_id: String(row.recipe_id),
    strategy_name: String(row.strategy_name),
    leg_summary: String(row.leg_summary),
    engine_rank: Number(row.engine_rank),
    quantity: Number(row.quantity),
    leg_count: Number(row.leg_count),
    expiration: String(row.expiration),
    dte: Number(row.dte),
    signed_entry_cash_flow: Number(row.signed_entry_cash_flow),
    entry_cash_flow_type: String(row.entry_cash_flow_type) as CandidateSummaryRecord["entry_cash_flow_type"],
    data_freshness: String(row.data_freshness) as CandidateSummaryRecord["data_freshness"],
    budget_status: String(row.budget_status),
    trade_economics_ticket_hash: String(row.trade_economics_ticket_hash),
  };
}
