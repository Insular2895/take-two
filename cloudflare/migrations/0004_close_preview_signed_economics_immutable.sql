-- Keep the new signed close cash-flow estimate inside the immutable preview economics set.
DROP TRIGGER IF EXISTS close_preview_economics_immutable;

CREATE TRIGGER close_preview_economics_immutable
BEFORE UPDATE OF position_id, created_at, quantity, pre_close_market_value,
  pre_close_liquidation_value, estimated_close_cash_flow_policy, estimated_pnl,
  estimated_return, estimated_commission, estimated_slippage, estimated_fx,
  engine_action, quote_timestamp, quote_provider, legs_json ON close_previews
BEGIN SELECT RAISE(ABORT, 'close preview economics are immutable'); END;
