PRAGMA foreign_keys = ON;

-- Latest broker observation only. This table is deliberately separate from the
-- execution ledger and cannot enable or claim an order.
CREATE TABLE IF NOT EXISTS broker_telemetry_latest (
  telemetry_source_id TEXT PRIMARY KEY,
  telemetry_id TEXT NOT NULL UNIQUE CHECK (telemetry_id GLOB 'broker-telemetry_*'),
  received_at TEXT NOT NULL,
  collected_at TEXT NOT NULL,
  server_time TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode = 'PAPER_READ_ONLY'),
  gateway_connected INTEGER NOT NULL CHECK (gateway_connected = 1),
  paper_account_verified INTEGER NOT NULL CHECK (paper_account_verified = 1),
  account_count INTEGER NOT NULL CHECK (account_count = 1),
  symbol TEXT NOT NULL CHECK (symbol = 'TTWO'),
  position_count INTEGER NOT NULL CHECK (position_count BETWEEN 0 AND 64),
  total_market_value TEXT,
  total_daily_pnl TEXT,
  total_unrealized_pnl TEXT,
  total_realized_pnl TEXT,
  quotes_complete INTEGER NOT NULL CHECK (quotes_complete IN (0, 1)),
  pnl_complete INTEGER NOT NULL CHECK (pnl_complete IN (0, 1)),
  fee_reconciliation_status TEXT NOT NULL CHECK (
    fee_reconciliation_status = 'LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES'
  ),
  error_codes_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL CHECK (
    length(payload_sha256) = 64 AND payload_sha256 NOT GLOB '*[^0-9a-f]*'
  ),
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_broker_telemetry_received
  ON broker_telemetry_latest(received_at DESC);
