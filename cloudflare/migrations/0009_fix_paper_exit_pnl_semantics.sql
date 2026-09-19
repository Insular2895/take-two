PRAGMA foreign_keys = ON;

-- V2 policies are deliberately separate from the ambiguous V1
-- net-liquidation-value fields created by migration 0007.  Existing rows are
-- copied in a disabled, reconfiguration-required state: positive legacy values
-- are never reinterpreted as signed PnL thresholds.
CREATE TABLE IF NOT EXISTS position_exit_policies_v2 (
  position_id TEXT PRIMARY KEY REFERENCES positions(id),
  mode TEXT NOT NULL CHECK (mode = 'PAPER'),
  policy_version INTEGER NOT NULL CHECK (policy_version = 2),
  trigger_metric TEXT NOT NULL CHECK (trigger_metric = 'LIQUIDATION_PNL_POLICY'),
  policy_currency TEXT NOT NULL,
  warning_liquidation_pnl_policy REAL CHECK (warning_liquidation_pnl_policy <= 0),
  automatic_exit_liquidation_pnl_policy REAL
    CHECK (automatic_exit_liquidation_pnl_policy <= 0),
  maximum_exit_slippage_policy REAL NOT NULL CHECK (maximum_exit_slippage_policy >= 0),
  maximum_quote_age_seconds INTEGER NOT NULL DEFAULT 30
    CHECK (maximum_quote_age_seconds BETWEEN 5 AND 60),
  automatic_exit_enabled INTEGER NOT NULL DEFAULT 0 CHECK (automatic_exit_enabled IN (0, 1)),
  native_protection_required INTEGER NOT NULL DEFAULT 1 CHECK (native_protection_required = 1),
  configuration_status TEXT NOT NULL CHECK (
    configuration_status IN ('CONFIGURED', 'REQUIRES_EXPLICIT_RECONFIGURATION')
  ),
  legacy_policy_detected INTEGER NOT NULL DEFAULT 0 CHECK (legacy_policy_detected IN (0, 1)),
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL,
  CHECK (
    warning_liquidation_pnl_policy IS NULL OR
    automatic_exit_liquidation_pnl_policy IS NULL OR
    warning_liquidation_pnl_policy >= automatic_exit_liquidation_pnl_policy
  ),
  CHECK (
    automatic_exit_enabled = 0 OR (
      configuration_status = 'CONFIGURED' AND
      warning_liquidation_pnl_policy IS NOT NULL AND
      automatic_exit_liquidation_pnl_policy IS NOT NULL
    )
  )
);

INSERT OR IGNORE INTO position_exit_policies_v2(
  position_id,mode,policy_version,trigger_metric,policy_currency,
  warning_liquidation_pnl_policy,automatic_exit_liquidation_pnl_policy,
  maximum_exit_slippage_policy,maximum_quote_age_seconds,automatic_exit_enabled,
  native_protection_required,configuration_status,legacy_policy_detected,
  created_at,created_by,updated_at,updated_by
)
SELECT
  position_id,mode,2,'LIQUIDATION_PNL_POLICY',policy_currency,
  NULL,NULL,maximum_exit_slippage_policy,maximum_quote_age_seconds,0,
  native_protection_required,'REQUIRES_EXPLICIT_RECONFIGURATION',1,
  created_at,created_by,updated_at,updated_by
FROM position_exit_policies;
