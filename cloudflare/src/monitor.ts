import { activePosition, audit, incrementUsage, persistProjection } from "./db";
import { calculateProjection, randomId, validateDossier } from "./domain";
import { fetchProviderSnapshot, marketDataProvider } from "./provider";
import type { ProviderSnapshot } from "./types";

function intervalMilliseconds(env: Env, conservation: boolean): number {
  const now = new Date();
  const day = now.getUTCDay();
  const minutes = now.getUTCHours() * 60 + now.getUTCMinutes();
  const expectedUsSession = day >= 1 && day <= 5 && minutes >= 13 * 60 + 30 && minutes < 20 * 60;
  const configured = Number(expectedUsSession ? env.MARKET_INTERVAL_SECONDS : env.OFF_HOURS_INTERVAL_SECONDS);
  return Math.max(configured * (conservation ? 2 : 1), 30) * 1000;
}

async function monitoringEvent(
  db: D1Database,
  positionId: string,
  type: string,
  severity: string,
  detail: Record<string, unknown>,
  dedupeKey: string,
): Promise<void> {
  await db.prepare(
    "INSERT OR IGNORE INTO monitoring_events(id,position_id,timestamp,event_type,severity,detail_json,dedupe_key) VALUES(?,?,?,?,?,?,?)",
  ).bind(randomId("event"), positionId, new Date().toISOString(), type, severity, JSON.stringify(detail), dedupeKey).run();
}

export class TTWOPositionMonitor {
  constructor(private readonly state: DurableObjectState, private readonly env: Env) {}

  async fetch(request: Request): Promise<Response> {
    const path = new URL(request.url).pathname;
    if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
    if (path === "/start" || path === "/resume") {
      await this.state.storage.setAlarm(Date.now() + 1_000);
      return Response.json({ monitoring: "SCHEDULED" });
    }
    if (path === "/pause") {
      await this.state.storage.deleteAlarm();
      return Response.json({ monitoring: "PAUSED" });
    }
    if (path === "/run") {
      await this.alarm();
      return Response.json({ monitoring: "RAN" });
    }
    return new Response("Not Found", { status: 404 });
  }

  async alarm(): Promise<void> {
    const now = Date.now();
    const runningUntil = await this.state.storage.get<number>("running_until");
    if (runningUntil && runningUntil > now) {
      await this.state.storage.setAlarm(runningUntil + 1_000);
      return;
    }
    await this.state.storage.put("running_until", now + 120_000);
    let shouldReschedule = true;
    try {
      const system = await this.env.DB.prepare(
        "SELECT monitoring_paused,conservation_mode FROM system_state WHERE singleton=1",
      ).first<{ monitoring_paused: number; conservation_mode: number }>();
      if (system?.monitoring_paused) {
        shouldReschedule = false;
        return;
      }
      const position = await activePosition(this.env.DB);
      if (!position) {
        shouldReschedule = false;
        return;
      }
      await incrementUsage(this.env.DB, "monitor_alarm_executions");
      const dossier = validateDossier(JSON.parse(position.canonical_dossier_json));
      const provider = marketDataProvider(this.env);
      let snapshot: ProviderSnapshot | null = null;
      let providerError: string | null = null;
      try {
        snapshot = await fetchProviderSnapshot(provider, dossier);
        if (snapshot) await incrementUsage(this.env.DB, "external_market_requests", 5);
      } catch (error) {
        providerError = error instanceof Error ? error.message : "DATA_PROVIDER_ERROR";
      }
      if (!snapshot) snapshot = dossier.last_imported_snapshot;
      const marketStatus = providerError
        ? "DATA_PROVIDER_ERROR"
        : snapshot
          ? snapshot.synthetic ? "SYNTHETIC_DEMO" : "LAST_IMPORTED_SNAPSHOT"
          : "NOT_CONFIGURED";
      await this.env.DB.prepare(
        "UPDATE system_state SET market_data_status=?,last_monitor_run=?,updated_at=? WHERE singleton=1",
      ).bind(marketStatus, new Date().toISOString(), new Date().toISOString()).run();
      if (providerError) {
        const bucket = Math.floor(now / 300_000);
        await monitoringEvent(this.env.DB, position.id, "DATA_PROVIDER_ERROR", "WARNING", { error: providerError }, `provider-error:${position.id}:${bucket}`);
        return;
      }
      if (!snapshot) return;
      const peak = await this.env.DB.prepare(
        "SELECT max(estimated_close_cash_flow_policy) AS value FROM pnl_snapshots WHERE position_id=?",
      ).bind(position.id).first<{ value: number | null }>();
      const projection = calculateProjection(dossier, snapshot, position.quantity_remaining, new Date(), peak?.value ?? null);
      const latest = await this.env.DB.prepare(
        "SELECT timestamp,monitor_action,data_freshness FROM pnl_snapshots WHERE position_id=? ORDER BY timestamp DESC LIMIT 1",
      ).bind(position.id).first<{ timestamp: string; monitor_action: string; data_freshness: string }>();
      const statusChanged = !latest || latest.monitor_action !== projection.monitor_action || latest.data_freshness !== projection.data_freshness;
      const snapshotInterval = Number(this.env.SNAPSHOT_INTERVAL_SECONDS) * (system?.conservation_mode ? 2 : 1) * 1000;
      const snapshotDue = !latest || Date.parse(projection.timestamp) - Date.parse(latest.timestamp) >= snapshotInterval;
      if (statusChanged || snapshotDue) await persistProjection(this.env.DB, position.id, projection);
      if (projection.data_freshness === "STALE") {
        const detail = { required_data_freshness: projection.required_data_freshness };
        await monitoringEvent(this.env.DB, position.id, "DATA_STALE", "WARNING", detail, `stale:${position.id}:${projection.required_data_freshness.effective_timestamp}`);
        if (statusChanged) await audit(this.env.DB, "DATA_STALE", "monitor", position.id, detail);
      }
      if (["INVALID", "INSUFFICIENT_DATA"].includes(projection.data_freshness)) {
        const eventType = projection.data_freshness === "INVALID" ? "DATA_INVALID" : "DATA_INSUFFICIENT";
        const detail = { required_data_freshness: projection.required_data_freshness };
        await monitoringEvent(this.env.DB, position.id, eventType, "WARNING", detail, `${eventType.toLowerCase()}:${position.id}:${projection.timestamp}`);
        if (statusChanged) await audit(this.env.DB, eventType, "monitor", position.id, detail);
      }
      if (statusChanged && projection.monitor_action === "WATCH") {
        await audit(this.env.DB, "WATCH_TRIGGERED", "monitor", position.id, { reasons: projection.monitor_reasons });
      }
      if (statusChanged && projection.monitor_action === "EXIT_REVIEW") {
        await audit(this.env.DB, "EXIT_REVIEW_TRIGGERED", "monitor", position.id, { reasons: projection.monitor_reasons });
      }
      const usage = await this.env.DB.prepare(
        "SELECT worker_api_requests + monitor_alarm_executions AS invocations FROM daily_usage WHERE date=?",
      ).bind(new Date().toISOString().slice(0, 10)).first<{ invocations: number }>();
      const conservation = (usage?.invocations ?? 0) >= 80_000;
      if (conservation !== Boolean(system?.conservation_mode)) {
        await this.env.DB.prepare("UPDATE system_state SET conservation_mode=?,updated_at=? WHERE singleton=1")
          .bind(conservation ? 1 : 0, new Date().toISOString()).run();
      }
    } finally {
      await this.state.storage.delete("running_until");
      if (shouldReschedule) {
        const system = await this.env.DB.prepare("SELECT conservation_mode FROM system_state WHERE singleton=1")
          .first<{ conservation_mode: number }>();
        await this.state.storage.setAlarm(Date.now() + intervalMilliseconds(this.env, Boolean(system?.conservation_mode)));
      } else {
        await this.state.storage.deleteAlarm();
      }
    }
  }
}
