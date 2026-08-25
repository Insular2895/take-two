export type AnalysisStatus =
  | "CREATED" | "QUEUED" | "RUNNING" | "COMPLETE"
  | "NO_TRADE" | "FAILED" | "CANCELLED";

export interface AnalysisBudgetRequest {
  preferred_budget: number;
  target_budget: number;
  maximum_budget: number;
  minimum_spend_policy: "SOFT" | "HARD";
  market_data_mode: "LAST_GOVERNED_SNAPSHOT" | "SYNTHETIC_DEMO";
  currency: "EUR";
}

export interface CandidateSummaryRecord {
  candidate_id: string;
  architecture: string;
  recipe_id: string;
  strategy_name: string;
  leg_summary: string;
  engine_rank: number;
  pareto_rank: number | null;
  quantity: number;
  leg_count: number;
  expiration: string;
  common_expiry: boolean;
  dte: number;
  signed_entry_cash_flow: number;
  entry_cash_flow_type: "DEBIT" | "CREDIT" | "FLAT";
  capital_required: number | null;
  maximum_loss: number | null;
  maximum_gain: number | null;
  break_even_points: number[];
  net_delta: number | null;
  net_theta: number | null;
  average_implied_volatility: number | null;
  maximum_relative_spread: number | null;
  minimum_open_interest: number | null;
  expected_pnl: number | null;
  expected_return: number | null;
  return_on_capital: number | null;
  return_on_risk: number | null;
  probability_profit: number | null;
  probability_loss_25: number | null;
  probability_loss_50: number | null;
  probability_loss_70: number | null;
  var_95: number | null;
  cvar_95: number | null;
  risk_on_capital: number | null;
  distance_to_target_budget: number | null;
  headroom_to_hard_maximum: number | null;
  theta_per_capital_day: number | null;
  flat_spot_7d: number | null;
  flat_spot_30d: number | null;
  flat_spot_60d: number | null;
  flat_spot_90d: number | null;
  net_gamma: number | null;
  net_vega: number | null;
  data_freshness: "FRESH" | "STALE" | "UNKNOWN";
  budget_status: string;
  eligible: boolean;
  research_eligible: boolean;
  paper_eligible: boolean;
  pruned: boolean;
  reason_codes: string[];
  score_probability: number | null;
  score_payoff: number | null;
  score_risk: number | null;
  score_robustness: number | null;
  score_executability: number | null;
  score_opportunity: number | null;
  score_evidence: number | null;
  score_model_agreement: number | null;
  score_execution_quality: number | null;
  trade_economics_ticket_hash: string;
}

export interface CallbackCandidate {
  summary: CandidateSummaryRecord;
  detail: Record<string, unknown>;
}
