-- Phase M-CF0.1: additive migration for signed cash flows and required-data freshness.
-- Legacy names remain for export compatibility but are no longer canonical.

ALTER TABLE positions ADD COLUMN schema_version TEXT;
ALTER TABLE positions ADD COLUMN entry_cash_flow_policy REAL;
ALTER TABLE positions ADD COLUMN capital_required_policy REAL;

-- The deployed CF0 fixture is explicitly synthetic and debit-only.  Its positive legacy
-- entry_cash therefore proves a paid debit for this one compatibility path.
UPDATE positions
SET schema_version = '1.0',
    entry_cash_flow_policy = -entry_cash,
    capital_required_policy = entry_cash
WHERE json_extract(canonical_dossier_json, '$.schema_version') = '1.0'
  AND json_extract(canonical_dossier_json, '$.fixture_status') = 'SYNTHETIC_DEMO'
  AND entry_cash > 0;

-- No strategy-name or sign heuristic is permitted for other 1.0 rows.
UPDATE positions
SET state = 'RECONCILIATION_REQUIRED',
    schema_version = coalesce(json_extract(canonical_dossier_json, '$.schema_version'), 'UNKNOWN')
WHERE entry_cash_flow_policy IS NULL OR capital_required_policy IS NULL;

ALTER TABLE fills ADD COLUMN close_cash_flow_type TEXT
  CHECK (close_cash_flow_type IN ('CREDIT', 'DEBIT'));
ALTER TABLE fills ADD COLUMN signed_close_cash_flow_policy REAL;

-- Existing fills belong to the proven synthetic debit fixture and represented cash received.
UPDATE fills
SET close_cash_flow_type = 'CREDIT',
    signed_close_cash_flow_policy = policy_proceeds
WHERE position_id IN (
  SELECT id FROM positions
  WHERE json_extract(canonical_dossier_json, '$.fixture_status') = 'SYNTHETIC_DEMO'
);

ALTER TABLE pnl_snapshots ADD COLUMN estimated_close_cash_flow_policy REAL;
ALTER TABLE pnl_snapshots ADD COLUMN required_data_effective_timestamp TEXT;
ALTER TABLE pnl_snapshots ADD COLUMN underlying_timestamp TEXT;
ALTER TABLE pnl_snapshots ADD COLUMN oldest_option_timestamp TEXT;
ALTER TABLE pnl_snapshots ADD COLUMN fx_timestamp TEXT;
ALTER TABLE pnl_snapshots ADD COLUMN combo_timestamp TEXT;
ALTER TABLE pnl_snapshots ADD COLUMN required_data_age_seconds REAL;
ALTER TABLE pnl_snapshots ADD COLUMN freshness_reasons_json TEXT;

UPDATE pnl_snapshots
SET estimated_close_cash_flow_policy = liquidation_value;

ALTER TABLE close_previews ADD COLUMN estimated_close_cash_flow_policy REAL;
UPDATE close_previews
SET estimated_close_cash_flow_policy = pre_close_liquidation_value;
