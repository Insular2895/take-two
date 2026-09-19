PRAGMA foreign_keys = ON;

-- This migration stores prospective Paper-entry evidence.  It does not activate a
-- bridge, change system_state, disable the broker Read-Only setting, or authorize Live.
CREATE TABLE IF NOT EXISTS material_execution_drift_policies (
  policy_id TEXT PRIMARY KEY,
  policy_version TEXT NOT NULL UNIQUE,
  approval_status TEXT NOT NULL CHECK (approval_status IN ('DRAFT','APPROVED','RETIRED')),
  thresholds_json TEXT NOT NULL,
  thresholds_hash TEXT NOT NULL CHECK (length(thresholds_hash) = 64),
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  approved_at TEXT,
  approved_by TEXT,
  CHECK (
    (approval_status = 'APPROVED' AND approved_at IS NOT NULL AND approved_by IS NOT NULL) OR
    approval_status != 'APPROVED'
  )
);
CREATE TRIGGER IF NOT EXISTS material_execution_drift_policies_no_update
BEFORE UPDATE ON material_execution_drift_policies
BEGIN SELECT RAISE(ABORT, 'material drift policies are immutable'); END;
CREATE TRIGGER IF NOT EXISTS material_execution_drift_policies_no_delete
BEFORE DELETE ON material_execution_drift_policies
BEGIN SELECT RAISE(ABORT, 'material drift policies are immutable'); END;

CREATE TABLE IF NOT EXISTS execution_revalidation_tickets (
  ticket_id TEXT PRIMARY KEY,
  analysis_request_id TEXT NOT NULL REFERENCES analysis_requests(analysis_request_id),
  candidate_id TEXT NOT NULL,
  selection_id TEXT NOT NULL REFERENCES candidate_selections(selection_id),
  dossier_id TEXT NOT NULL REFERENCES planned_positions(dossier_id),
  previous_ticket_id TEXT REFERENCES execution_revalidation_tickets(ticket_id),
  drift_policy_id TEXT REFERENCES material_execution_drift_policies(policy_id),
  structure_hash TEXT NOT NULL CHECK (length(structure_hash) = 64),
  original_market_snapshot_hash TEXT NOT NULL CHECK (length(original_market_snapshot_hash) = 64),
  current_market_snapshot_hash TEXT NOT NULL CHECK (length(current_market_snapshot_hash) = 64),
  original_economics_hash TEXT NOT NULL CHECK (length(original_economics_hash) = 64),
  proposed_economics_hash TEXT NOT NULL CHECK (length(proposed_economics_hash) = 64),
  ticket_hash TEXT NOT NULL UNIQUE CHECK (length(ticket_hash) = 64),
  proposed_limit REAL NOT NULL CHECK (proposed_limit > 0),
  valid_tick REAL NOT NULL CHECK (valid_tick > 0),
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  combo_submission_mode TEXT NOT NULL CHECK (combo_submission_mode = 'WHOLE_BAG'),
  broker_combo_guarantee_mode TEXT NOT NULL CHECK (
    broker_combo_guarantee_mode IN ('GUARANTEED','NON_GUARANTEED','UNKNOWN')
  ),
  execution_environment TEXT NOT NULL CHECK (execution_environment = 'IBKR_PAPER_SIMULATOR'),
  material_drift_status TEXT NOT NULL CHECK (material_drift_status IN (
    'WITHIN_POLICY','MATERIAL_DRIFT','REQUIRES_POLICY','INSUFFICIENT_EVIDENCE'
  )),
  verdict TEXT NOT NULL CHECK (verdict IN (
    'EXECUTABLE','EXECUTABLE_REPRICE_PROPOSAL','REVIEW_REQUIRED',
    'REANALYSIS_REQUIRED','BLOCKED'
  )),
  blockers_json TEXT NOT NULL,
  ticket_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  FOREIGN KEY (analysis_request_id, candidate_id)
    REFERENCES analysis_candidate_summaries(analysis_request_id, candidate_id)
);
CREATE INDEX IF NOT EXISTS idx_execution_revalidation_dossier
  ON execution_revalidation_tickets(dossier_id, created_at DESC);
CREATE TRIGGER IF NOT EXISTS execution_revalidation_tickets_no_update
BEFORE UPDATE ON execution_revalidation_tickets
BEGIN SELECT RAISE(ABORT, 'execution revalidation tickets are immutable'); END;
CREATE TRIGGER IF NOT EXISTS execution_revalidation_tickets_no_delete
BEFORE DELETE ON execution_revalidation_tickets
BEGIN SELECT RAISE(ABORT, 'execution revalidation tickets are immutable'); END;

CREATE TABLE IF NOT EXISTS paper_entry_previews (
  preview_id TEXT PRIMARY KEY,
  dossier_id TEXT NOT NULL REFERENCES planned_positions(dossier_id),
  ticket_id TEXT NOT NULL UNIQUE REFERENCES execution_revalidation_tickets(ticket_id),
  preview_hash TEXT NOT NULL UNIQUE CHECK (length(preview_hash) = 64),
  structure_hash TEXT NOT NULL CHECK (length(structure_hash) = 64),
  proposed_limit REAL NOT NULL CHECK (proposed_limit > 0),
  requested_quantity INTEGER NOT NULL CHECK (requested_quantity > 0),
  status TEXT NOT NULL CHECK (status = 'PREVIEW_READY'),
  preview_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_previews_no_update
BEFORE UPDATE ON paper_entry_previews
BEGIN SELECT RAISE(ABORT, 'paper entry previews are immutable'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_previews_no_delete
BEFORE DELETE ON paper_entry_previews
BEGIN SELECT RAISE(ABORT, 'paper entry previews are immutable'); END;

CREATE TABLE IF NOT EXISTS paper_entry_confirmations (
  confirmation_id TEXT PRIMARY KEY,
  preview_id TEXT NOT NULL UNIQUE REFERENCES paper_entry_previews(preview_id),
  ticket_id TEXT NOT NULL REFERENCES execution_revalidation_tickets(ticket_id),
  confirmation_hash TEXT NOT NULL UNIQUE CHECK (length(confirmation_hash) = 64),
  confirmed_preview_hash TEXT NOT NULL CHECK (length(confirmed_preview_hash) = 64),
  confirmed_ticket_hash TEXT NOT NULL CHECK (length(confirmed_ticket_hash) = 64),
  confirmation_json TEXT NOT NULL,
  confirmed_at TEXT NOT NULL,
  confirmed_by TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_confirmations_no_update
BEFORE UPDATE ON paper_entry_confirmations
BEGIN SELECT RAISE(ABORT, 'paper entry confirmations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_confirmations_no_delete
BEFORE DELETE ON paper_entry_confirmations
BEGIN SELECT RAISE(ABORT, 'paper entry confirmations are immutable'); END;

CREATE TABLE IF NOT EXISTS paper_entry_operator_attestations (
  attestation_id TEXT PRIMARY KEY,
  confirmation_id TEXT NOT NULL REFERENCES paper_entry_confirmations(confirmation_id),
  paper_account_hash TEXT NOT NULL CHECK (length(paper_account_hash) = 64),
  session_username_hash TEXT NOT NULL CHECK (length(session_username_hash) = 64),
  stable_client_id INTEGER NOT NULL CHECK (stable_client_id > 0),
  paper_port INTEGER NOT NULL CHECK (paper_port IN (4002, 7497)),
  loopback_verified INTEGER NOT NULL CHECK (loopback_verified = 1),
  single_du_account_verified INTEGER NOT NULL CHECK (single_du_account_verified = 1),
  read_only_temporarily_disabled INTEGER NOT NULL CHECK (read_only_temporarily_disabled IN (0, 1)),
  maintain_resubmit_disabled INTEGER NOT NULL CHECK (maintain_resubmit_disabled = 1),
  api_detail_logging_enabled INTEGER NOT NULL CHECK (api_detail_logging_enabled = 1),
  no_competing_session_attested INTEGER NOT NULL CHECK (no_competing_session_attested = 1),
  kill_switch_version TEXT NOT NULL,
  attestation_hash TEXT NOT NULL UNIQUE CHECK (length(attestation_hash) = 64),
  attested_at TEXT NOT NULL,
  attested_by TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_attestations_no_update
BEFORE UPDATE ON paper_entry_operator_attestations
BEGIN SELECT RAISE(ABORT, 'paper entry attestations are append-only'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_attestations_no_delete
BEFORE DELETE ON paper_entry_operator_attestations
BEGIN SELECT RAISE(ABORT, 'paper entry attestations are append-only'); END;

CREATE TABLE IF NOT EXISTS paper_entry_intents (
  intent_id TEXT PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  dossier_id TEXT NOT NULL REFERENCES planned_positions(dossier_id),
  ticket_id TEXT NOT NULL REFERENCES execution_revalidation_tickets(ticket_id),
  preview_id TEXT NOT NULL REFERENCES paper_entry_previews(preview_id),
  confirmation_id TEXT NOT NULL UNIQUE REFERENCES paper_entry_confirmations(confirmation_id),
  attestation_id TEXT REFERENCES paper_entry_operator_attestations(attestation_id),
  order_ref TEXT NOT NULL UNIQUE,
  requested_quantity INTEGER NOT NULL CHECK (requested_quantity > 0),
  status TEXT NOT NULL CHECK (status IN (
    'CONFIRMED','READY','CLAIMED','BROKER_SUBMISSION_ATTEMPTED','PENDING_SUBMIT',
    'PRE_SUBMITTED','WORKING','PARTIALLY_FILLED','FILLED','PENDING_CANCEL',
    'CANCELLED','API_CANCELLED','REJECTED','INACTIVE','EXPIRED','AMBIGUOUS',
    'RECONCILIATION_REQUIRED','BLOCKED'
  )),
  dispatch_authorized INTEGER NOT NULL DEFAULT 0 CHECK (dispatch_authorized IN (0, 1)),
  command_hash TEXT NOT NULL UNIQUE CHECK (length(command_hash) = 64),
  command_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  claimed_by TEXT,
  claimed_at TEXT,
  claim_expires_at TEXT,
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  completed_at TEXT,
  last_error_code INTEGER
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_paper_entry_per_dossier
  ON paper_entry_intents(dossier_id)
  WHERE status IN (
    'CONFIRMED','READY','CLAIMED','BROKER_SUBMISSION_ATTEMPTED','PENDING_SUBMIT',
    'PRE_SUBMITTED','WORKING','PARTIALLY_FILLED','AMBIGUOUS','RECONCILIATION_REQUIRED'
  );
CREATE TRIGGER IF NOT EXISTS paper_entry_intent_identity_immutable
BEFORE UPDATE OF idempotency_key,dossier_id,ticket_id,preview_id,confirmation_id,
  order_ref,requested_quantity,command_hash,command_json,created_at,expires_at
ON paper_entry_intents
BEGIN SELECT RAISE(ABORT, 'paper entry intent identity is immutable'); END;

CREATE TABLE IF NOT EXISTS paper_entry_what_if_evidence (
  what_if_id TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES paper_entry_intents(intent_id),
  status TEXT NOT NULL CHECK (status IN (
    'BROKER_WHAT_IF_CONFIRMED','BROKER_WHAT_IF_UNSUPPORTED',
    'BROKER_WHAT_IF_INCOMPLETE','BROKER_WHAT_IF_FAILED'
  )),
  margin_eur REAL,
  commission_eur REAL,
  evidence_hash TEXT NOT NULL UNIQUE CHECK (length(evidence_hash) = 64),
  evidence_json TEXT NOT NULL,
  observed_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_what_if_no_update
BEFORE UPDATE ON paper_entry_what_if_evidence
BEGIN SELECT RAISE(ABORT, 'paper what-if evidence is append-only'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_what_if_no_delete
BEFORE DELETE ON paper_entry_what_if_evidence
BEGIN SELECT RAISE(ABORT, 'paper what-if evidence is append-only'); END;

CREATE TABLE IF NOT EXISTS paper_entry_lifecycle_events (
  event_id TEXT PRIMARY KEY,
  broker_event_key TEXT NOT NULL UNIQUE,
  intent_id TEXT NOT NULL REFERENCES paper_entry_intents(intent_id),
  event_kind TEXT NOT NULL CHECK (event_kind IN (
    'CONFIRMED','CLAIMED','SUBMISSION_ATTEMPTED','OPEN_ORDER','OPEN_ORDER_END',
    'ORDER_STATUS','ERROR','EXECUTION','EXECUTION_END','COMMISSION_REPORT',
    'COMPLETED_ORDER','COMPLETED_ORDERS_END','RECOVERY_OBSERVATION','REPRICE_PROPOSAL'
  )),
  raw_broker_status TEXT,
  canonical_execution_status TEXT,
  execution_condition TEXT,
  broker_order_id INTEGER,
  broker_perm_id INTEGER,
  broker_exec_id TEXT,
  evidence_hash TEXT NOT NULL CHECK (length(evidence_hash) = 64),
  evidence_json TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paper_entry_events_intent_time
  ON paper_entry_lifecycle_events(intent_id, occurred_at ASC, received_at ASC);
CREATE TRIGGER IF NOT EXISTS paper_entry_events_no_update
BEFORE UPDATE ON paper_entry_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'paper entry lifecycle events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_events_no_delete
BEFORE DELETE ON paper_entry_lifecycle_events
BEGIN SELECT RAISE(ABORT, 'paper entry lifecycle events are append-only'); END;

CREATE TABLE IF NOT EXISTS paper_entry_executions (
  exec_id TEXT PRIMARY KEY,
  intent_id TEXT NOT NULL REFERENCES paper_entry_intents(intent_id),
  broker_order_id INTEGER NOT NULL,
  broker_perm_id INTEGER,
  shares REAL NOT NULL CHECK (shares > 0),
  cumulative_quantity REAL NOT NULL CHECK (cumulative_quantity > 0),
  remaining_quantity REAL NOT NULL CHECK (remaining_quantity >= 0),
  price REAL NOT NULL CHECK (price >= 0),
  execution_environment TEXT NOT NULL CHECK (execution_environment = 'IBKR_PAPER_SIMULATOR'),
  fill_evidence TEXT NOT NULL CHECK (fill_evidence = 'PAPER_SIMULATED_FILL'),
  evidence_hash TEXT NOT NULL CHECK (length(evidence_hash) = 64),
  execution_json TEXT NOT NULL,
  executed_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_executions_no_update
BEFORE UPDATE ON paper_entry_executions
BEGIN SELECT RAISE(ABORT, 'paper entry executions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_executions_no_delete
BEFORE DELETE ON paper_entry_executions
BEGIN SELECT RAISE(ABORT, 'paper entry executions are append-only'); END;

CREATE TABLE IF NOT EXISTS paper_entry_commissions (
  exec_id TEXT PRIMARY KEY REFERENCES paper_entry_executions(exec_id),
  intent_id TEXT NOT NULL REFERENCES paper_entry_intents(intent_id),
  commission REAL NOT NULL,
  currency TEXT NOT NULL,
  evidence_hash TEXT NOT NULL CHECK (length(evidence_hash) = 64),
  commission_json TEXT NOT NULL,
  received_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS paper_entry_commissions_no_update
BEFORE UPDATE ON paper_entry_commissions
BEGIN SELECT RAISE(ABORT, 'paper entry commissions are append-only'); END;
CREATE TRIGGER IF NOT EXISTS paper_entry_commissions_no_delete
BEFORE DELETE ON paper_entry_commissions
BEGIN SELECT RAISE(ABORT, 'paper entry commissions are append-only'); END;
