PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  token_hash TEXT NOT NULL UNIQUE,
  csrf_token TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  sensitive_authenticated_at TEXT NOT NULL,
  revoked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_hash, expires_at);

CREATE TABLE IF NOT EXISTS system_state (
  singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
  safe_mode INTEGER NOT NULL DEFAULT 0 CHECK (safe_mode IN (0, 1)),
  monitoring_paused INTEGER NOT NULL DEFAULT 0 CHECK (monitoring_paused IN (0, 1)),
  market_data_status TEXT NOT NULL DEFAULT 'NOT_CONFIGURED',
  last_monitor_run TEXT,
  conservation_mode INTEGER NOT NULL DEFAULT 0 CHECK (conservation_mode IN (0, 1)),
  updated_at TEXT NOT NULL
);
INSERT OR IGNORE INTO system_state(singleton, updated_at) VALUES (1, datetime('now'));

CREATE TABLE IF NOT EXISTS positions (
  id TEXT PRIMARY KEY,
  dossier_id TEXT NOT NULL UNIQUE,
  ticker TEXT NOT NULL,
  structure_name TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('PLANNED','PAPER_OPEN','LIVE_ASSISTED_OPEN','PARTIAL_CLOSE','RECONCILIATION_REQUIRED','CLOSED','CANCELLED')),
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  quantity_initial INTEGER NOT NULL CHECK (quantity_initial > 0),
  quantity_remaining INTEGER NOT NULL CHECK (quantity_remaining >= 0),
  native_currency TEXT NOT NULL,
  policy_currency TEXT NOT NULL,
  entry_cash REAL NOT NULL,
  realized_pnl REAL,
  managed_exit_deadline TEXT,
  canonical_dossier_json TEXT NOT NULL,
  ticket_hash TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  git_commit TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_positions_active ON positions(state, updated_at);

CREATE TABLE IF NOT EXISTS position_legs (
  position_id TEXT NOT NULL REFERENCES positions(id),
  leg_id TEXT NOT NULL,
  contract_identity TEXT NOT NULL,
  con_id INTEGER,
  local_symbol TEXT,
  side TEXT NOT NULL CHECK (side IN ('LONG','SHORT')),
  close_action TEXT NOT NULL CHECK (close_action IN ('SELL_TO_CLOSE','BUY_TO_CLOSE')),
  ratio INTEGER NOT NULL CHECK (ratio > 0),
  quantity_initial INTEGER NOT NULL CHECK (quantity_initial > 0),
  multiplier REAL NOT NULL CHECK (multiplier > 0),
  option_right TEXT NOT NULL CHECK (option_right IN ('CALL','PUT')),
  strike REAL NOT NULL,
  expiration TEXT NOT NULL,
  entry_bid REAL NOT NULL,
  entry_ask REAL NOT NULL,
  PRIMARY KEY (position_id, leg_id),
  UNIQUE (position_id, contract_identity)
);

CREATE TABLE IF NOT EXISTS fills (
  fill_id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL REFERENCES positions(id),
  preview_id TEXT REFERENCES close_previews(preview_id),
  timestamp TEXT NOT NULL,
  quantity_closed INTEGER NOT NULL CHECK (quantity_closed > 0),
  combo_fill_price REAL NOT NULL,
  native_proceeds REAL NOT NULL,
  policy_proceeds REAL NOT NULL,
  commission REAL NOT NULL CHECK (commission >= 0),
  fx_cost REAL NOT NULL CHECK (fx_cost >= 0),
  actual_realized_pnl REAL NOT NULL,
  estimate_error REAL,
  broker_reference TEXT,
  source TEXT NOT NULL CHECK (source = 'MANUAL_IBKR_RECONCILIATION'),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pnl_snapshots (
  id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL REFERENCES positions(id),
  timestamp TEXT NOT NULL,
  spot REAL NOT NULL,
  market_value_native REAL NOT NULL,
  market_value_policy REAL NOT NULL,
  mtm_pnl REAL NOT NULL,
  mtm_return REAL NOT NULL,
  liquidation_value REAL,
  liquidation_pnl REAL,
  liquidation_return REAL,
  liquidation_estimate_mode TEXT NOT NULL CHECK (liquidation_estimate_mode IN ('COMBO_QUOTE','LEGWISE_CONSERVATIVE_ESTIMATE')),
  estimated_exit_commission REAL,
  estimated_exit_slippage REAL,
  estimated_exit_fx REAL,
  iv REAL,
  theta REAL,
  greeks_json TEXT,
  monitor_action TEXT NOT NULL,
  data_freshness TEXT NOT NULL,
  provider TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pnl_position_time ON pnl_snapshots(position_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS model_snapshots (
  id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL REFERENCES positions(id),
  timestamp TEXT NOT NULL,
  source TEXT NOT NULL,
  status TEXT NOT NULL,
  snapshot_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS close_previews (
  preview_id TEXT PRIMARY KEY,
  position_id TEXT NOT NULL REFERENCES positions(id),
  created_at TEXT NOT NULL,
  acknowledged_at TEXT,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  pre_close_market_value REAL NOT NULL,
  pre_close_liquidation_value REAL NOT NULL,
  estimated_pnl REAL NOT NULL,
  estimated_return REAL NOT NULL,
  estimated_commission REAL,
  estimated_slippage REAL,
  estimated_fx REAL,
  engine_action TEXT NOT NULL,
  quote_timestamp TEXT NOT NULL,
  quote_provider TEXT NOT NULL,
  legs_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('CREATED','ACKNOWLEDGED','RECONCILIATION_REQUIRED','RECONCILED','CANCELLED'))
);
CREATE INDEX IF NOT EXISTS idx_preview_position ON close_previews(position_id, created_at DESC);

CREATE TABLE IF NOT EXISTS monitoring_events (
  id TEXT PRIMARY KEY,
  position_id TEXT REFERENCES positions(id),
  timestamp TEXT NOT NULL,
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  dedupe_key TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  timestamp TEXT NOT NULL,
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL,
  position_id TEXT REFERENCES positions(id),
  detail_json TEXT NOT NULL,
  request_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_events(timestamp DESC);

CREATE TRIGGER IF NOT EXISTS audit_events_no_update
BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS close_preview_economics_immutable
BEFORE UPDATE OF position_id, created_at, quantity, pre_close_market_value,
  pre_close_liquidation_value, estimated_pnl, estimated_return,
  estimated_commission, estimated_slippage, estimated_fx, engine_action,
  quote_timestamp, quote_provider, legs_json ON close_previews
BEGIN SELECT RAISE(ABORT, 'close preview economics are immutable'); END;

CREATE TABLE IF NOT EXISTS daily_usage (
  date TEXT PRIMARY KEY,
  worker_api_requests INTEGER NOT NULL DEFAULT 0,
  monitor_alarm_executions INTEGER NOT NULL DEFAULT 0,
  external_market_requests INTEGER NOT NULL DEFAULT 0,
  d1_snapshot_writes INTEGER NOT NULL DEFAULT 0,
  label TEXT NOT NULL DEFAULT 'APPLICATION_ESTIMATE_ONLY',
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS login_attempts (
  id TEXT PRIMARY KEY,
  identity_hash TEXT NOT NULL,
  attempted_at TEXT NOT NULL,
  success INTEGER NOT NULL CHECK (success IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_identity_time ON login_attempts(identity_hash, attempted_at DESC);
