PRAGMA foreign_keys = ON;

-- The broker control plane is additive and fail-closed. A migration never enables it.
ALTER TABLE system_state ADD COLUMN broker_mode TEXT NOT NULL DEFAULT 'DISABLED'
  CHECK (broker_mode IN ('DISABLED', 'PAPER'));
ALTER TABLE system_state ADD COLUMN broker_kill_switch INTEGER NOT NULL DEFAULT 1
  CHECK (broker_kill_switch IN (0, 1));
ALTER TABLE system_state ADD COLUMN broker_bridge_status TEXT NOT NULL DEFAULT 'NOT_CONFIGURED'
  CHECK (broker_bridge_status IN ('NOT_CONFIGURED', 'OFFLINE', 'HEALTHY', 'DEGRADED'));
ALTER TABLE system_state ADD COLUMN broker_last_heartbeat TEXT;
ALTER TABLE system_state ADD COLUMN broker_bridge_id TEXT;

CREATE TABLE IF NOT EXISTS position_exit_policies (
  position_id TEXT PRIMARY KEY REFERENCES positions(id),
  mode TEXT NOT NULL CHECK (mode = 'PAPER'),
  policy_currency TEXT NOT NULL,
  warning_net_liquidation_value REAL NOT NULL CHECK (warning_net_liquidation_value >= 0),
  automatic_exit_net_liquidation_value REAL NOT NULL CHECK (automatic_exit_net_liquidation_value >= 0),
  maximum_exit_slippage_policy REAL NOT NULL CHECK (maximum_exit_slippage_policy >= 0),
  maximum_quote_age_seconds INTEGER NOT NULL DEFAULT 30
    CHECK (maximum_quote_age_seconds BETWEEN 5 AND 60),
  automatic_exit_enabled INTEGER NOT NULL DEFAULT 0 CHECK (automatic_exit_enabled IN (0, 1)),
  native_protection_required INTEGER NOT NULL DEFAULT 1 CHECK (native_protection_required = 1),
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  CHECK (warning_net_liquidation_value >= automatic_exit_net_liquidation_value)
);

CREATE TABLE IF NOT EXISTS broker_execution_intents (
  intent_id TEXT PRIMARY KEY CHECK (intent_id GLOB 'broker-intent_*'),
  idempotency_key TEXT NOT NULL UNIQUE,
  position_id TEXT NOT NULL REFERENCES positions(id),
  preview_id TEXT REFERENCES close_previews(preview_id),
  intent_type TEXT NOT NULL CHECK (intent_type IN (
    'MANUAL_CLOSE', 'AUTOMATIC_FLOOR_EXIT', 'NATIVE_PROTECTIVE_EXIT'
  )),
  mode TEXT NOT NULL CHECK (mode = 'PAPER'),
  status TEXT NOT NULL CHECK (status IN (
    'READY', 'CLAIMED', 'BROKER_ACKNOWLEDGED', 'PARTIAL_FILL', 'FILLED',
    'REJECTED', 'CANCELLED', 'EXPIRED', 'AMBIGUOUS', 'BLOCKED'
  )),
  requested_quantity INTEGER NOT NULL CHECK (requested_quantity > 0),
  order_ref TEXT NOT NULL UNIQUE,
  command_json TEXT NOT NULL,
  source_actor TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  claimed_by TEXT,
  claimed_at TEXT,
  claim_expires_at TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  completed_at TEXT,
  last_error_code TEXT,
  CHECK (preview_id IS NOT NULL OR intent_type != 'MANUAL_CLOSE')
);
CREATE INDEX IF NOT EXISTS idx_broker_intents_dispatch
  ON broker_execution_intents(status, created_at);
CREATE INDEX IF NOT EXISTS idx_broker_intents_position
  ON broker_execution_intents(position_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_one_active_intent_per_position
  ON broker_execution_intents(position_id)
  WHERE status IN ('READY', 'CLAIMED', 'BROKER_ACKNOWLEDGED', 'PARTIAL_FILL', 'AMBIGUOUS');

CREATE TRIGGER IF NOT EXISTS broker_intent_identity_immutable
BEFORE UPDATE OF idempotency_key, position_id, preview_id, intent_type, mode,
  requested_quantity, order_ref, command_json, source_actor, created_at, expires_at
ON broker_execution_intents
BEGIN SELECT RAISE(ABORT, 'broker intent identity is immutable'); END;

CREATE TABLE IF NOT EXISTS broker_execution_events (
  event_id TEXT PRIMARY KEY CHECK (event_id GLOB 'broker-event_*'),
  broker_event_key TEXT NOT NULL UNIQUE,
  intent_id TEXT NOT NULL REFERENCES broker_execution_intents(intent_id),
  event_type TEXT NOT NULL CHECK (event_type IN (
    'CLAIMED', 'BROKER_ACKNOWLEDGED', 'PARTIAL_FILL', 'FILLED', 'COMMISSION_REPORT',
    'REJECTED', 'CANCELLED', 'EXPIRED', 'AMBIGUOUS', 'RECOVERY_OBSERVATION'
  )),
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  bridge_id TEXT NOT NULL,
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  broker_exec_id TEXT,
  detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_broker_events_intent
  ON broker_execution_events(intent_id, occurred_at ASC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_events_exec
  ON broker_execution_events(broker_exec_id, event_type)
  WHERE broker_exec_id IS NOT NULL;
CREATE TRIGGER IF NOT EXISTS broker_events_no_update
BEFORE UPDATE ON broker_execution_events
BEGIN SELECT RAISE(ABORT, 'broker execution events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_events_no_delete
BEFORE DELETE ON broker_execution_events
BEGIN SELECT RAISE(ABORT, 'broker execution events are append-only'); END;

CREATE TABLE IF NOT EXISTS broker_bridge_nonces (
  nonce TEXT PRIMARY KEY,
  bridge_id TEXT NOT NULL,
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_broker_bridge_nonces_time
  ON broker_bridge_nonces(received_at);

CREATE TABLE IF NOT EXISTS broker_bridge_heartbeats (
  heartbeat_id TEXT PRIMARY KEY CHECK (heartbeat_id GLOB 'broker-heartbeat_*'),
  bridge_id TEXT NOT NULL,
  received_at TEXT NOT NULL,
  gateway_connected INTEGER NOT NULL CHECK (gateway_connected IN (0, 1)),
  paper_account_verified INTEGER NOT NULL CHECK (paper_account_verified IN (0, 1)),
  open_intent_count INTEGER NOT NULL CHECK (open_intent_count >= 0),
  detail_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_broker_heartbeat_time
  ON broker_bridge_heartbeats(received_at DESC);
CREATE TRIGGER IF NOT EXISTS broker_heartbeats_no_update
BEFORE UPDATE ON broker_bridge_heartbeats
BEGIN SELECT RAISE(ABORT, 'broker heartbeats are append-only'); END;
CREATE TRIGGER IF NOT EXISTS broker_heartbeats_no_delete
BEFORE DELETE ON broker_bridge_heartbeats
BEGIN SELECT RAISE(ABORT, 'broker heartbeats are append-only'); END;
