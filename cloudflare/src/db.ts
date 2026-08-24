import type { CloudPositionDossier, PnlProjection } from "./types";
import { randomId } from "./domain";

export interface PositionRow {
  id: string;
  dossier_id: string;
  ticker: string;
  structure_name: string;
  state: string;
  opened_at: string;
  closed_at: string | null;
  quantity_initial: number;
  quantity_remaining: number;
  native_currency: string;
  policy_currency: string;
  entry_cash: number;
  realized_pnl: number | null;
  managed_exit_deadline: string | null;
  canonical_dossier_json: string;
  created_at: string;
  updated_at: string;
}

export async function audit(
  db: D1Database,
  eventType: string,
  actor: string,
  positionId: string | null = null,
  detail: Record<string, unknown> = {},
  requestId: string | null = null,
): Promise<void> {
  await db.prepare(
    "INSERT INTO audit_events(id,timestamp,event_type,actor,position_id,detail_json,request_id) VALUES(?,?,?,?,?,?,?)",
  ).bind(randomId("audit"), new Date().toISOString(), eventType, actor, positionId, JSON.stringify(detail), requestId).run();
}

export async function incrementUsage(
  db: D1Database,
  field: "worker_api_requests" | "monitor_alarm_executions" | "external_market_requests" | "d1_snapshot_writes",
  amount = 1,
): Promise<void> {
  const date = new Date().toISOString().slice(0, 10);
  await db.prepare(
    `INSERT INTO daily_usage(date,${field},updated_at) VALUES(?,?,?)
     ON CONFLICT(date) DO UPDATE SET ${field}=${field}+excluded.${field}, updated_at=excluded.updated_at`,
  ).bind(date, amount, new Date().toISOString()).run();
}

export async function activePosition(db: D1Database): Promise<PositionRow | null> {
  return db.prepare(
    "SELECT * FROM positions WHERE state IN ('PAPER_OPEN','LIVE_ASSISTED_OPEN','PARTIAL_CLOSE','RECONCILIATION_REQUIRED') ORDER BY updated_at DESC LIMIT 1",
  ).first<PositionRow>();
}

export async function importDossier(db: D1Database, dossier: CloudPositionDossier): Promise<void> {
  const now = new Date().toISOString();
  const statements: D1PreparedStatement[] = [
    db.prepare(
      `INSERT INTO positions(id,dossier_id,ticker,structure_name,state,opened_at,quantity_initial,quantity_remaining,
       native_currency,policy_currency,entry_cash,managed_exit_deadline,canonical_dossier_json,ticket_hash,config_hash,git_commit,created_at,updated_at)
       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    ).bind(
      dossier.position_id, dossier.dossier_id, dossier.ticker, dossier.structure_name,
      dossier.initial_position_state, dossier.opened_at, dossier.quantity, dossier.quantity,
      dossier.entry_native_currency, dossier.policy_currency, dossier.actual_entry_cash,
      dossier.managed_exit_deadline, JSON.stringify(dossier), dossier.trade_economics_ticket_hash,
      dossier.config_hash, dossier.git_commit, now, now,
    ),
    ...dossier.legs.map((leg) => db.prepare(
      `INSERT INTO position_legs(position_id,leg_id,contract_identity,con_id,local_symbol,side,close_action,ratio,
       quantity_initial,multiplier,option_right,strike,expiration,entry_bid,entry_ask) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    ).bind(
      dossier.position_id, leg.leg_id, leg.contract_identity, leg.con_id, leg.local_symbol, leg.side,
      leg.close_action, leg.ratio, leg.quantity, leg.multiplier, leg.option_right, leg.strike,
      leg.expiration, leg.entry_bid, leg.entry_ask,
    )),
  ];
  if (dossier.latest_promoted_model_snapshot) {
    const snapshot = dossier.latest_promoted_model_snapshot;
    statements.push(db.prepare(
      "INSERT INTO model_snapshots(id,position_id,timestamp,source,status,snapshot_json,created_at) VALUES(?,?,?,?,?,?,?)",
    ).bind(
      randomId("model"), dossier.position_id, String(snapshot.timestamp), String(snapshot.source),
      String(snapshot.status), JSON.stringify(snapshot), now,
    ));
  }
  await db.batch(statements);
  await audit(db, "POSITION_IMPORTED", "admin", dossier.position_id, { dossier_id: dossier.dossier_id, fixture_status: dossier.fixture_status });
}

export async function latestProjection(db: D1Database, positionId: string): Promise<Record<string, unknown> | null> {
  return db.prepare("SELECT * FROM pnl_snapshots WHERE position_id=? ORDER BY timestamp DESC LIMIT 1").bind(positionId).first<Record<string, unknown>>();
}

export async function persistProjection(db: D1Database, positionId: string, projection: PnlProjection): Promise<void> {
  await db.prepare(
    `INSERT INTO pnl_snapshots(id,position_id,timestamp,spot,market_value_native,market_value_policy,mtm_pnl,mtm_return,
     liquidation_value,liquidation_pnl,liquidation_return,liquidation_estimate_mode,estimated_exit_commission,
     estimated_exit_slippage,estimated_exit_fx,iv,theta,greeks_json,monitor_action,data_freshness,provider)
     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
  ).bind(
    randomId("pnl"), positionId, projection.timestamp, projection.spot, projection.market_value_native,
    projection.market_value_policy, projection.mtm_pnl, projection.mtm_return, projection.liquidation_value,
    projection.liquidation_pnl, projection.liquidation_return, projection.liquidation_estimate_mode,
    projection.estimated_exit_commission, projection.estimated_exit_slippage, projection.estimated_exit_fx,
    projection.current_iv, projection.current_greeks.theta ?? null, JSON.stringify(projection.current_greeks), projection.monitor_action,
    projection.data_freshness, projection.provider,
  ).run();
  await incrementUsage(db, "d1_snapshot_writes");
}
