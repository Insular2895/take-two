export type PositionState =
  | "PLANNED"
  | "PAPER_OPEN"
  | "LIVE_ASSISTED_OPEN"
  | "PARTIAL_CLOSE"
  | "RECONCILIATION_REQUIRED"
  | "CLOSED"
  | "CANCELLED";

export type MonitorAction =
  | "HOLD"
  | "WATCH"
  | "REDUCE"
  | "EXIT_REVIEW"
  | "THESIS_INVALIDATED"
  | "DATA_STALE"
  | "BLOCKED_INSUFFICIENT_DATA";

export type CashFlowType = "CREDIT" | "DEBIT";
export type ProjectionFreshnessStatus = "FRESH" | "STALE" | "INVALID" | "INSUFFICIENT_DATA";

export interface ProjectionFreshness {
  effective_timestamp: string | null;
  underlying_timestamp: string | null;
  oldest_option_timestamp: string | null;
  option_timestamps: Record<string, string | null>;
  fx_timestamp: string | null;
  combo_timestamp: string | null;
  age_seconds: number | null;
  status: ProjectionFreshnessStatus;
  reasons: string[];
}

export interface CloudLeg {
  leg_id: string;
  contract_identity: string;
  con_id: number | null;
  local_symbol: string | null;
  underlying: string;
  instrument_type: "option";
  side: "LONG" | "SHORT";
  close_action: "SELL_TO_CLOSE" | "BUY_TO_CLOSE";
  ratio: number;
  quantity: number;
  multiplier: number;
  option_right: "CALL" | "PUT";
  strike: number;
  expiration: string;
  entry_bid: number;
  entry_ask: number;
  entry_mid: number;
  entry_executable_price: number;
}

export interface CloudPositionDossier {
  schema_version: "1.1";
  fixture_status: "CANONICAL_EXPORT" | "SYNTHETIC_DEMO";
  dossier_id: string;
  position_id: string;
  created_at: string;
  opened_at: string;
  initial_position_state: "PLANNED" | "PAPER_OPEN" | "LIVE_ASSISTED_OPEN";
  ticker: string;
  structure_name: string;
  structure_type: string;
  legs: CloudLeg[];
  quantity: number;
  multiplier: number;
  entry_native_currency: string;
  policy_currency: string;
  entry_cash_flow_policy: number;
  capital_required_policy: number;
  actual_entry_fx: {
    rate_to_policy_currency: number | null;
    rate_source: string | null;
    rate_timestamp: string | null;
    transaction_cost: number | null;
    transaction_cost_status: "NOT_APPLICABLE" | "KNOWN" | "ESTIMATED" | "UNKNOWN";
    transaction_cost_source: string | null;
  };
  actual_entry_commissions: number;
  actual_entry_slippage: number;
  initial_spot: number;
  initial_iv: Record<string, number>;
  initial_greeks: Record<string, number>;
  expirations: string[];
  managed_exit_deadline: string | null;
  initial_scenario_probabilities: Record<string, number> | null;
  latest_promoted_model_snapshot: Record<string, unknown> | null;
  flat_spot_diagnostics: {
    timestamp: string;
    source: string;
    flat_spot_7d: number | null;
    flat_spot_30d: number | null;
    flat_spot_60d: number | null;
    flat_spot_90d: number | null;
  } | null;
  five_scores: Record<string, unknown> | null;
  budget_diagnostics: Record<string, unknown>;
  exit_plan: {
    status: "CONFIGURED" | "NOT_CONFIGURED";
    profit_target: number | null;
    partial_profit_target: number | null;
    operational_stop_loss: number | null;
    exit_days_before_expiration: number | null;
    iv_crush_threshold: number | null;
    trailing_drawdown: number | null;
    rules: Array<{ rule_id: string; threshold: number | string | boolean; suggested_action: MonitorAction }>;
    human_review_required: true;
  };
  last_imported_snapshot: ProviderSnapshot | null;
  trade_economics_ticket_hash: string;
  trade_economics_schema_version: string;
  phase_m_context_id?: string | null;
  phase_m_context_hash?: string | null;
  git_commit: string;
  config_hash: string;
  config_hash_source: string;
  market_snapshot_hash: string;
  market_snapshot_hash_source: string;
  read_only: true;
  transmit: false;
  what_if: true;
  human_confirmation_required: true;
  order_capability: "forbidden";
}

export interface OptionQuote {
  contract_identity: string;
  bid: number;
  ask: number;
  timestamp: string | null;
  provider: string;
  source: string;
  quality: string;
  iv?: number;
  greeks?: Record<string, number>;
}

export interface ProviderSnapshot {
  /** Legacy ordering timestamp; canonical freshness never derives from this field. */
  timestamp: string;
  underlying_timestamp: string | null;
  provider: string;
  source: string;
  quality: string;
  synthetic: boolean;
  spot: number;
  option_quotes: OptionQuote[];
  fx_rate_to_policy_currency: number | null;
  fx_source: string | null;
  fx_timestamp: string | null;
  estimated_exit_commission: number | null;
  estimated_exit_slippage: number | null;
  estimated_exit_fx: number | null;
  estimated_exit_fx_status: "NOT_APPLICABLE" | "KNOWN" | "ESTIMATED" | "UNKNOWN";
  current_iv: number | null;
  current_greeks: Record<string, number>;
  thesis_invalidated: boolean;
  data_sufficient: boolean;
  combo_quote?: { price: number; cash_flow_type: CashFlowType; timestamp: string | null };
}

export interface PnlProjection {
  timestamp: string;
  spot: number;
  market_value_native: number;
  market_value_policy: number;
  mtm_pnl: number;
  mtm_return: number;
  estimated_close_cash_flow_policy: number | null;
  /** @deprecated compatibility alias for estimated_close_cash_flow_policy. */
  liquidation_value: number | null;
  liquidation_pnl: number | null;
  liquidation_return: number | null;
  liquidation_estimate_mode: "COMBO_QUOTE" | "LEGWISE_CONSERVATIVE_ESTIMATE";
  estimated_exit_commission: number | null;
  estimated_exit_slippage: number | null;
  estimated_exit_fx: number | null;
  current_iv: number | null;
  current_greeks: Record<string, number>;
  monitor_action: MonitorAction;
  monitor_reasons: string[];
  data_freshness: ProjectionFreshnessStatus;
  required_data_freshness: ProjectionFreshness;
  provider: string;
}

export interface LegacyCloudPositionDossierV10
  extends Omit<
    CloudPositionDossier,
    "schema_version" | "entry_cash_flow_policy" | "capital_required_policy"
  > {
  schema_version: "1.0";
  actual_entry_cash: number;
}

export interface AuthContext {
  actor: string;
  email: string;
  csrfToken: string;
  csrfCookieNeedsSet: boolean;
  accessIssuedAt: number;
}
