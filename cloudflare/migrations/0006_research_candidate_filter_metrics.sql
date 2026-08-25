ALTER TABLE analysis_candidate_summaries ADD COLUMN strategy_name TEXT;
ALTER TABLE analysis_candidate_summaries ADD COLUMN leg_summary TEXT;
ALTER TABLE analysis_candidate_summaries ADD COLUMN common_expiry INTEGER CHECK (common_expiry IN (0,1));
ALTER TABLE analysis_candidate_summaries ADD COLUMN entry_cash_flow_type TEXT CHECK (entry_cash_flow_type IN ('DEBIT','CREDIT','FLAT'));
ALTER TABLE analysis_candidate_summaries ADD COLUMN expected_return REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN return_on_capital REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN return_on_risk REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN probability_loss_25 REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN probability_loss_50 REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN probability_loss_70 REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN var_95 REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN risk_on_capital REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN distance_to_target_budget REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN headroom_to_hard_maximum REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN theta_per_capital_day REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN flat_spot_7d REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN flat_spot_30d REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN flat_spot_60d REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN flat_spot_90d REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN net_gamma REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN net_vega REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN score_opportunity REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN score_evidence REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN score_model_agreement REAL;
ALTER TABLE analysis_candidate_summaries ADD COLUMN score_execution_quality REAL;

CREATE INDEX IF NOT EXISTS idx_candidates_budget_capital
  ON analysis_candidate_summaries(analysis_request_id, capital_required, engine_rank);
CREATE INDEX IF NOT EXISTS idx_candidates_dte
  ON analysis_candidate_summaries(analysis_request_id, dte, engine_rank);
