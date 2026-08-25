PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS analysis_requests (
  analysis_request_id TEXT PRIMARY KEY CHECK (analysis_request_id GLOB 'analysis-[0-9a-f]*'),
  request_hash TEXT NOT NULL CHECK (length(request_hash) = 64),
  preferred_budget REAL NOT NULL CHECK (preferred_budget > 0),
  target_budget REAL NOT NULL CHECK (target_budget >= preferred_budget),
  maximum_budget REAL NOT NULL CHECK (maximum_budget >= target_budget),
  minimum_spend_policy TEXT NOT NULL CHECK (minimum_spend_policy IN ('SOFT','HARD')),
  market_data_mode TEXT NOT NULL CHECK (market_data_mode IN ('LAST_GOVERNED_SNAPSHOT','SYNTHETIC_DEMO')),
  currency TEXT NOT NULL CHECK (currency = 'EUR'),
  status TEXT NOT NULL CHECK (status IN ('CREATED','QUEUED','RUNNING','COMPLETE','NO_TRADE','FAILED','CANCELLED')),
  active_slot INTEGER NOT NULL DEFAULT 1 CHECK (active_slot = 1),
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  queued_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  github_run_id TEXT,
  git_commit TEXT,
  snapshot_id TEXT,
  snapshot_as_of TEXT,
  snapshot_hash TEXT,
  catalog_hash TEXT,
  config_hash TEXT,
  phase_m_context_id TEXT,
  phase_m_context_hash TEXT,
  verdict TEXT,
  total_generated INTEGER CHECK (total_generated >= 0),
  total_pruned INTEGER CHECK (total_pruned >= 0),
  total_research_eligible INTEGER CHECK (total_research_eligible >= 0),
  total_paper_eligible INTEGER CHECK (total_paper_eligible >= 0),
  combinations_by_architecture_json TEXT,
  best_overall_ids_json TEXT,
  best_by_architecture_json TEXT,
  no_trade_reasons_json TEXT,
  warnings_json TEXT,
  failure_code TEXT,
  CHECK (preferred_budget <= target_budget AND target_budget <= maximum_budget)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_one_active
  ON analysis_requests(active_slot)
  WHERE status IN ('CREATED','QUEUED','RUNNING');
CREATE INDEX IF NOT EXISTS idx_analysis_history
  ON analysis_requests(created_at DESC);

CREATE TRIGGER IF NOT EXISTS analysis_request_identity_immutable
BEFORE UPDATE OF request_hash, preferred_budget, target_budget, maximum_budget,
  minimum_spend_policy, market_data_mode, currency, created_at, created_by
ON analysis_requests
BEGIN SELECT RAISE(ABORT, 'analysis request identity is immutable'); END;

CREATE TABLE IF NOT EXISTS analysis_runs (
  event_id TEXT PRIMARY KEY,
  analysis_request_id TEXT NOT NULL REFERENCES analysis_requests(analysis_request_id),
  created_at TEXT NOT NULL,
  event_type TEXT NOT NULL,
  step TEXT,
  github_run_id TEXT,
  git_commit TEXT,
  detail_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_analysis_runs
  ON analysis_runs(analysis_request_id, created_at ASC);
CREATE TRIGGER IF NOT EXISTS analysis_runs_no_update
BEFORE UPDATE ON analysis_runs BEGIN SELECT RAISE(ABORT, 'analysis runs are append-only'); END;
CREATE TRIGGER IF NOT EXISTS analysis_runs_no_delete
BEFORE DELETE ON analysis_runs BEGIN SELECT RAISE(ABORT, 'analysis runs are append-only'); END;

CREATE TABLE IF NOT EXISTS analysis_candidate_summaries (
  analysis_request_id TEXT NOT NULL REFERENCES analysis_requests(analysis_request_id),
  candidate_id TEXT NOT NULL,
  architecture TEXT NOT NULL,
  recipe_id TEXT NOT NULL,
  engine_rank INTEGER NOT NULL CHECK (engine_rank > 0),
  pareto_rank INTEGER,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  leg_count INTEGER NOT NULL CHECK (leg_count > 0),
  expiration TEXT NOT NULL,
  dte INTEGER NOT NULL CHECK (dte >= 0),
  signed_entry_cash_flow REAL NOT NULL,
  capital_required REAL,
  maximum_loss REAL,
  maximum_gain REAL,
  break_even_points_json TEXT NOT NULL,
  net_delta REAL,
  net_theta REAL,
  average_implied_volatility REAL,
  maximum_relative_spread REAL,
  minimum_open_interest INTEGER,
  expected_pnl REAL,
  probability_profit REAL,
  cvar_95 REAL,
  data_freshness TEXT NOT NULL CHECK (data_freshness IN ('FRESH','STALE','UNKNOWN')),
  budget_status TEXT NOT NULL,
  eligible INTEGER NOT NULL CHECK (eligible IN (0,1)),
  research_eligible INTEGER NOT NULL CHECK (research_eligible IN (0,1)),
  paper_eligible INTEGER NOT NULL CHECK (paper_eligible IN (0,1)),
  pruned INTEGER NOT NULL CHECK (pruned IN (0,1)),
  reason_codes_json TEXT NOT NULL,
  score_probability REAL,
  score_payoff REAL,
  score_risk REAL,
  score_robustness REAL,
  score_executability REAL,
  trade_economics_ticket_hash TEXT NOT NULL CHECK (length(trade_economics_ticket_hash) = 64),
  PRIMARY KEY (analysis_request_id, candidate_id),
  UNIQUE (analysis_request_id, engine_rank)
);
CREATE INDEX IF NOT EXISTS idx_candidates_architecture
  ON analysis_candidate_summaries(analysis_request_id, architecture, engine_rank);
CREATE INDEX IF NOT EXISTS idx_candidates_paper
  ON analysis_candidate_summaries(analysis_request_id, paper_eligible, engine_rank);

CREATE TABLE IF NOT EXISTS analysis_candidate_details (
  analysis_request_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  PRIMARY KEY (analysis_request_id, candidate_id),
  FOREIGN KEY (analysis_request_id, candidate_id)
    REFERENCES analysis_candidate_summaries(analysis_request_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS candidate_selections (
  selection_id TEXT PRIMARY KEY,
  analysis_request_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  selected_at TEXT NOT NULL,
  selected_by TEXT NOT NULL,
  trade_economics_ticket_hash TEXT NOT NULL CHECK (length(trade_economics_ticket_hash) = 64),
  phase_m_context_id TEXT NOT NULL,
  phase_m_context_hash TEXT NOT NULL CHECK (length(phase_m_context_hash) = 64),
  snapshot_id TEXT NOT NULL,
  snapshot_hash TEXT NOT NULL CHECK (length(snapshot_hash) = 64),
  git_commit TEXT NOT NULL,
  UNIQUE (analysis_request_id, candidate_id),
  FOREIGN KEY (analysis_request_id, candidate_id)
    REFERENCES analysis_candidate_summaries(analysis_request_id, candidate_id)
);
CREATE TRIGGER IF NOT EXISTS candidate_selections_no_update
BEFORE UPDATE ON candidate_selections BEGIN SELECT RAISE(ABORT, 'candidate selections are immutable'); END;
CREATE TRIGGER IF NOT EXISTS candidate_selections_no_delete
BEFORE DELETE ON candidate_selections BEGIN SELECT RAISE(ABORT, 'candidate selections are immutable'); END;

CREATE TABLE IF NOT EXISTS planned_positions (
  dossier_id TEXT PRIMARY KEY,
  selection_id TEXT NOT NULL UNIQUE REFERENCES candidate_selections(selection_id),
  analysis_request_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state = 'PLANNED'),
  planned_entry_cash_flow REAL,
  estimated_capital_required REAL,
  actual_entry_cash_flow REAL CHECK (actual_entry_cash_flow IS NULL),
  actual_opened_at TEXT CHECK (actual_opened_at IS NULL),
  dossier_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS planned_positions_no_update
BEFORE UPDATE ON planned_positions BEGIN SELECT RAISE(ABORT, 'planned dossiers are immutable'); END;
CREATE TRIGGER IF NOT EXISTS planned_positions_no_delete
BEFORE DELETE ON planned_positions BEGIN SELECT RAISE(ABORT, 'planned dossiers are immutable'); END;

CREATE TABLE IF NOT EXISTS analysis_callback_nonces (
  nonce TEXT PRIMARY KEY,
  analysis_request_id TEXT NOT NULL REFERENCES analysis_requests(analysis_request_id),
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_callback_nonces_time
  ON analysis_callback_nonces(received_at);
