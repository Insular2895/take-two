PRAGMA foreign_keys = ON;

-- Offline-only order lifecycle evidence. This migration does not enable PAPER mode,
-- install an execution adapter, or authorize transmission.
CREATE TABLE IF NOT EXISTS broker_order_state_latest (
  intent_id TEXT PRIMARY KEY REFERENCES broker_execution_intents(intent_id),
  order_ref TEXT NOT NULL UNIQUE,
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  raw_broker_status TEXT,
  canonical_execution_status TEXT NOT NULL CHECK (canonical_execution_status IN (
    'CREATED','REVALIDATING','EXECUTION_PREVIEW','PREVIEW_READY','CONFIRMED','READY',
    'CLAIMED','BROKER_SUBMISSION_ATTEMPTED','LOCAL_NOT_TRANSMITTED',
    'PENDING_SUBMIT','PRE_SUBMITTED','WORKING','PARTIALLY_FILLED','FILLED',
    'PENDING_CANCEL','CANCELLED','API_CANCELLED','REJECTED','INACTIVE','EXPIRED',
    'AMBIGUOUS','RECONCILIATION_REQUIRED'
  )),
  execution_condition TEXT NOT NULL CHECK (execution_condition IN (
    'NONE','WORKING_NO_FILL_YET','PARTIAL_FILL_ACTIVE','BROKER_HELD',
    'TIF_CONDITION_NOT_SATISFIED','STATE_UNKNOWN'
  )),
  requested_quantity REAL NOT NULL CHECK (requested_quantity > 0),
  cumulative_filled_quantity REAL NOT NULL DEFAULT 0 CHECK (cumulative_filled_quantity >= 0),
  remaining_quantity REAL NOT NULL CHECK (remaining_quantity >= 0),
  average_fill_price REAL,
  last_fill_price REAL,
  time_in_force TEXT,
  cancellation_cause TEXT CHECK (cancellation_cause IS NULL OR cancellation_cause IN (
    'USER_REQUESTED','API_REQUESTED','TWS_REQUESTED','BROKER_CANCELLED',
    'EXCHANGE_CANCELLED','TIF_EXPIRED','PRECAUTION','INVALID_ORDER',
    'PRICE_PROTECTION','SESSION_LOST','UNKNOWN'
  )),
  rejection_category TEXT CHECK (rejection_category IS NULL OR rejection_category IN (
    'ACCOUNT_PERMISSION','INSUFFICIENT_BUYING_POWER','MARKET_DATA_PERMISSION',
    'ORDER_PRECAUTION','LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE','INVALID_CONTRACT',
    'INVALID_COMBO','UNSUPPORTED_ORDER_TYPE','EXCHANGE_RESTRICTION',
    'ACCOUNT_STATE','SESSION_STATE','DUPLICATE_ORDER','MESSAGE_RATE','TICKER_LIMIT',
    'INVALID_ORDER','INVALID_TICK','INCOMPATIBLE_TIF','SUBMISSION_FAILED',
    'MODIFICATION_FAILED','HALTED_SECURITY','INVALID_SIZE','CANCELLATION',
    'WHAT_IF_UNSUPPORTED','API_TRADING_NOT_ALLOWED','COMBO_GUARANTEE',
    'UNKNOWN_BROKER_REJECTION'
  )),
  intent_created_at TEXT NOT NULL,
  bridge_claimed_at TEXT,
  broker_submission_attempted_at TEXT,
  transmitted_to_broker INTEGER NOT NULL DEFAULT 0 CHECK (transmitted_to_broker IN (0, 1)),
  broker_acknowledged_at TEXT,
  submitted_at TEXT,
  working_since TEXT,
  last_status_at TEXT NOT NULL,
  last_market_update_at TEXT,
  updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_order_state_perm_id
  ON broker_order_state_latest(broker_perm_id)
  WHERE broker_perm_id IS NOT NULL AND broker_perm_id > 0;

CREATE TABLE IF NOT EXISTS broker_order_lifecycle_events (
  lifecycle_event_id TEXT PRIMARY KEY CHECK (lifecycle_event_id GLOB 'broker-lifecycle_*'),
  broker_event_key TEXT NOT NULL UNIQUE,
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  evidence_kind TEXT NOT NULL CHECK (evidence_kind IN (
    'INTENT_CREATED','EXECUTION_PREVIEW','READY','CLAIMED','SUBMISSION_ATTEMPTED',
    'LOCAL_NOT_TRANSMITTED','OPEN_ORDER','OPEN_ORDER_END','ORDER_STATUS','ERROR',
    'EXECUTION','EXECUTION_END','COMMISSION_REPORT','COMPLETED_ORDER',
    'COMPLETED_ORDERS_END','RECOVERY_OBSERVATION','REPRICE_PROPOSAL','LEASE_EXPIRED'
  )),
  raw_broker_status TEXT,
  canonical_execution_status TEXT CHECK (canonical_execution_status IS NULL OR canonical_execution_status IN (
    'CREATED','REVALIDATING','EXECUTION_PREVIEW','PREVIEW_READY','CONFIRMED','READY',
    'CLAIMED','BROKER_SUBMISSION_ATTEMPTED','LOCAL_NOT_TRANSMITTED',
    'PENDING_SUBMIT','PRE_SUBMITTED','WORKING','PARTIALLY_FILLED','FILLED',
    'PENDING_CANCEL','CANCELLED','API_CANCELLED','REJECTED','INACTIVE','EXPIRED',
    'AMBIGUOUS','RECONCILIATION_REQUIRED'
  )),
  execution_condition TEXT CHECK (execution_condition IS NULL OR execution_condition IN (
    'NONE','WORKING_NO_FILL_YET','PARTIAL_FILL_ACTIVE','BROKER_HELD',
    'TIF_CONDITION_NOT_SATISFIED','STATE_UNKNOWN'
  )),
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  bridge_id TEXT NOT NULL,
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  broker_exec_id TEXT,
  raw_evidence_hash TEXT NOT NULL CHECK (
    length(raw_evidence_hash) = 64 AND raw_evidence_hash NOT GLOB '*[^0-9a-f]*'
  ),
  evidence_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_broker_lifecycle_intent_time
  ON broker_order_lifecycle_events(intent_id, occurred_at ASC, received_at ASC);
CREATE TRIGGER IF NOT EXISTS broker_lifecycle_events_no_update
BEFORE UPDATE ON broker_order_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'broker lifecycle events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_lifecycle_events_no_delete
BEFORE DELETE ON broker_order_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'broker lifecycle events are append-only'); END;

CREATE TABLE IF NOT EXISTS broker_order_errors (
  error_event_key TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  broker_error_code INTEGER NOT NULL,
  redacted_broker_message TEXT NOT NULL,
  advanced_rejection_json TEXT,
  normalized_category TEXT NOT NULL CHECK (normalized_category IN (
    'ACCOUNT_PERMISSION','INSUFFICIENT_BUYING_POWER','MARKET_DATA_PERMISSION',
    'ORDER_PRECAUTION','LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE','INVALID_CONTRACT',
    'INVALID_COMBO','UNSUPPORTED_ORDER_TYPE','EXCHANGE_RESTRICTION',
    'ACCOUNT_STATE','SESSION_STATE','DUPLICATE_ORDER','MESSAGE_RATE','TICKER_LIMIT',
    'INVALID_ORDER','INVALID_TICK','INCOMPATIBLE_TIF','SUBMISSION_FAILED',
    'MODIFICATION_FAILED','HALTED_SECURITY','INVALID_SIZE','CANCELLATION',
    'WHAT_IF_UNSUPPORTED','API_TRADING_NOT_ALLOWED','COMBO_GUARANTEE',
    'UNKNOWN_BROKER_REJECTION'
  )),
  precaution INTEGER NOT NULL DEFAULT 0 CHECK (precaution IN (0, 1)),
  occurred_at TEXT NOT NULL,
  raw_evidence_hash TEXT NOT NULL CHECK (length(raw_evidence_hash) = 64)
);
CREATE INDEX IF NOT EXISTS idx_broker_errors_intent
  ON broker_order_errors(intent_id, occurred_at ASC);
CREATE TRIGGER IF NOT EXISTS broker_order_errors_no_update
BEFORE UPDATE ON broker_order_errors
BEGIN SELECT RAISE(ABORT, 'broker order errors are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_order_errors_no_delete
BEFORE DELETE ON broker_order_errors
BEGIN SELECT RAISE(ABORT, 'broker order errors are append-only'); END;

CREATE TABLE IF NOT EXISTS broker_executions (
  exec_id TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  execution_time TEXT NOT NULL,
  side TEXT,
  shares REAL NOT NULL CHECK (shares > 0),
  cumulative_quantity REAL NOT NULL CHECK (cumulative_quantity > 0),
  price REAL NOT NULL CHECK (price >= 0),
  exchange TEXT,
  liquidation INTEGER CHECK (liquidation IS NULL OR liquidation IN (0, 1)),
  combo_bid_near_fill REAL CHECK (combo_bid_near_fill IS NULL OR combo_bid_near_fill >= 0),
  combo_ask_near_fill REAL CHECK (combo_ask_near_fill IS NULL OR combo_ask_near_fill >= 0),
  execution_delay_seconds REAL CHECK (execution_delay_seconds IS NULL OR execution_delay_seconds >= 0),
  slippage_vs_decision_midpoint REAL,
  slippage_vs_executable_quote REAL,
  partial_fill_sequence INTEGER CHECK (partial_fill_sequence IS NULL OR partial_fill_sequence > 0),
  execution_environment TEXT NOT NULL DEFAULT 'IBKR_PAPER_SIMULATOR'
    CHECK (execution_environment = 'IBKR_PAPER_SIMULATOR'),
  fill_evidence TEXT NOT NULL DEFAULT 'PAPER_SIMULATED_FILL'
    CHECK (fill_evidence = 'PAPER_SIMULATED_FILL'),
  raw_evidence_hash TEXT NOT NULL CHECK (length(raw_evidence_hash) = 64)
);
CREATE INDEX IF NOT EXISTS idx_broker_executions_intent
  ON broker_executions(intent_id, execution_time ASC);
CREATE TRIGGER IF NOT EXISTS broker_executions_no_update
BEFORE UPDATE ON broker_executions
BEGIN SELECT RAISE(ABORT, 'broker executions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_executions_no_delete
BEFORE DELETE ON broker_executions
BEGIN SELECT RAISE(ABORT, 'broker executions are append-only'); END;

CREATE TABLE IF NOT EXISTS broker_commissions (
  exec_id TEXT PRIMARY KEY REFERENCES broker_executions(exec_id),
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  commission REAL NOT NULL,
  currency TEXT NOT NULL,
  realized_pnl REAL,
  yield_value REAL,
  yield_redemption_date INTEGER,
  occurred_at TEXT NOT NULL,
  raw_evidence_hash TEXT NOT NULL CHECK (length(raw_evidence_hash) = 64)
);
CREATE TRIGGER IF NOT EXISTS broker_commissions_no_update
BEFORE UPDATE ON broker_commissions
BEGIN SELECT RAISE(ABORT, 'broker commissions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_commissions_no_delete
BEFORE DELETE ON broker_commissions
BEGIN SELECT RAISE(ABORT, 'broker commissions are append-only'); END;

CREATE TABLE IF NOT EXISTS broker_market_snapshots (
  snapshot_id TEXT PRIMARY KEY CHECK (snapshot_id GLOB 'broker-market-snapshot_*'),
  intent_id TEXT NOT NULL UNIQUE REFERENCES broker_execution_intents(intent_id),
  captured_at TEXT NOT NULL,
  ticker TEXT NOT NULL,
  candidate_id TEXT,
  strategy TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  legs_json TEXT NOT NULL,
  market_data_type TEXT NOT NULL,
  data_freshness TEXT NOT NULL,
  combo_bid REAL,
  combo_ask REAL,
  combo_midpoint REAL,
  synthetic_combo_bid REAL,
  synthetic_combo_ask REAL,
  signed_price_convention_status TEXT NOT NULL,
  requested_limit REAL NOT NULL CHECK (requested_limit >= 0),
  cash_flow_type TEXT NOT NULL CHECK (cash_flow_type IN ('DEBIT','CREDIT')),
  expected_commission REAL,
  capital_required REAL,
  maximum_loss REAL,
  spread_absolute REAL,
  spread_percent REAL,
  quote_age_seconds REAL,
  snapshot_json TEXT NOT NULL,
  raw_evidence_hash TEXT NOT NULL CHECK (length(raw_evidence_hash) = 64)
);
CREATE TRIGGER IF NOT EXISTS broker_market_snapshots_no_update
BEFORE UPDATE ON broker_market_snapshots
BEGIN SELECT RAISE(ABORT, 'broker market snapshots are immutable'); END;
CREATE TRIGGER IF NOT EXISTS broker_market_snapshots_no_delete
BEFORE DELETE ON broker_market_snapshots
BEGIN SELECT RAISE(ABORT, 'broker market snapshots are immutable'); END;

CREATE TABLE IF NOT EXISTS broker_reprice_proposals (
  proposal_id TEXT PRIMARY KEY CHECK (proposal_id GLOB 'broker-reprice_*'),
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  created_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'READY_FOR_HUMAN_PREVIEW','REPRICE_UNAVAILABLE_DATA_STALE',
    'REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED','BLOCKED_AUTHORIZED_BOUND',
    'BLOCKED_HARD_BUDGET','BLOCKED_MAX_LOSS','BLOCKED_ORDER_SHAPE_CHANGED','BLOCKED_DIRECTION'
  )),
  cash_flow_type TEXT NOT NULL CHECK (cash_flow_type IN ('DEBIT','CREDIT')),
  current_limit REAL NOT NULL CHECK (current_limit >= 0),
  proposed_limit REAL NOT NULL CHECK (proposed_limit >= 0),
  current_combo_bid REAL,
  current_combo_ask REAL,
  price_difference REAL NOT NULL,
  incremental_capital_impact REAL NOT NULL CHECK (incremental_capital_impact >= 0),
  remaining_hard_budget_headroom REAL,
  authorized_boundary REAL NOT NULL CHECK (authorized_boundary >= 0),
  new_estimated_pnl_economics REAL,
  original_order_shape_hash TEXT NOT NULL,
  proposed_order_shape_hash TEXT NOT NULL,
  automatic_action_allowed INTEGER NOT NULL DEFAULT 0 CHECK (automatic_action_allowed = 0),
  proposal_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_broker_reprice_intent
  ON broker_reprice_proposals(intent_id, created_at DESC);
CREATE TRIGGER IF NOT EXISTS broker_reprice_no_update
BEFORE UPDATE ON broker_reprice_proposals
BEGIN SELECT RAISE(ABORT, 'broker reprice proposals are immutable previews'); END;
CREATE TRIGGER IF NOT EXISTS broker_reprice_no_delete
BEFORE DELETE ON broker_reprice_proposals
BEGIN SELECT RAISE(ABORT, 'broker reprice proposals are immutable previews'); END;
