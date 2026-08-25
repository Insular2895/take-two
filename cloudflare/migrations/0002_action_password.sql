CREATE TABLE IF NOT EXISTS action_password_attempts (
  id TEXT PRIMARY KEY,
  identity_hash TEXT NOT NULL,
  attempted_at TEXT NOT NULL,
  action TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_action_password_attempts_identity_time
ON action_password_attempts(identity_hash, attempted_at DESC);
