import { verifyTelemetryRequest } from "./broker-security";
import { randomId } from "./domain";

const TELEMETRY_FRESH_MS = 90_000;
const TELEMETRY_OFFLINE_MS = 5 * 60_000;
const MAX_POSITIONS = 64;
const DECIMAL_TEXT = /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/;

interface QuoteTelemetryBody {
  bid: string | null;
  ask: string | null;
  last: string | null;
  close: string | null;
  mark: string | null;
  midpoint: string | null;
  market_data_type: "REALTIME" | "FROZEN" | "DELAYED" | "DELAYED_FROZEN" | "UNKNOWN";
  observed_at: string;
  bid_ask_complete: boolean;
}

interface PositionTelemetryBody {
  con_id: number;
  security_type: string;
  local_symbol: string;
  currency: string;
  expiry: string;
  strike: string | null;
  right: string;
  multiplier: string;
  quantity: string;
  average_cost: string | null;
  market_value: string | null;
  daily_pnl: string | null;
  unrealized_pnl: string | null;
  realized_pnl: string | null;
  quote: QuoteTelemetryBody | null;
}

interface BrokerTelemetryBody {
  mode: "PAPER_READ_ONLY";
  gateway_connected: true;
  paper_account_verified: true;
  account_count: 1;
  symbol: "TTWO";
  server_time: string;
  collected_at: string;
  positions: PositionTelemetryBody[];
  totals: {
    market_value: string | null;
    daily_pnl: string | null;
    unrealized_pnl: string | null;
    realized_pnl: string | null;
  };
  quotes_complete: boolean;
  pnl_complete: boolean;
  fee_reconciliation_status: "LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES";
  error_codes: number[];
}

interface TelemetryRow {
  telemetry_source_id: string;
  telemetry_id: string;
  received_at: string;
  collected_at: string;
  server_time: string;
  payload_json: string;
  payload_sha256: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireExactKeys(value: Record<string, unknown>, keys: readonly string[]): void {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (actual.length !== expected.length || actual.some((key, index) => key !== expected[index])) {
    throw new Error("INVALID_BROKER_TELEMETRY_KEYS");
  }
}

function parseIso(value: unknown, code: string): number {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T/.test(value)) throw new Error(code);
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) throw new Error(code);
  return timestamp;
}

function decimalValue(value: unknown, code: string, nullable = true): number | null {
  if (value === null && nullable) return null;
  if (typeof value !== "string" || value.length > 64 || !DECIMAL_TEXT.test(value)) throw new Error(code);
  const number = Number(value);
  if (!Number.isFinite(number) || Math.abs(number) > 1e15) throw new Error(code);
  return number;
}

function nearlyEqual(left: number, right: number): boolean {
  return Math.abs(left - right) <= Math.max(1e-9, Math.abs(right) * 1e-10);
}

function validateQuote(value: unknown, collectedAt: number): QuoteTelemetryBody | null {
  if (value === null) return null;
  if (!isRecord(value)) throw new Error("INVALID_BROKER_TELEMETRY_QUOTE");
  requireExactKeys(value, [
    "bid", "ask", "last", "close", "mark", "midpoint", "market_data_type",
    "observed_at", "bid_ask_complete",
  ]);
  const quote = value as unknown as QuoteTelemetryBody;
  const bid = decimalValue(quote.bid, "INVALID_BROKER_TELEMETRY_QUOTE");
  const ask = decimalValue(quote.ask, "INVALID_BROKER_TELEMETRY_QUOTE");
  const midpoint = decimalValue(quote.midpoint, "INVALID_BROKER_TELEMETRY_QUOTE");
  for (const field of [quote.last, quote.close, quote.mark]) {
    const parsed = decimalValue(field, "INVALID_BROKER_TELEMETRY_QUOTE");
    if (parsed !== null && parsed <= 0) throw new Error("INVALID_BROKER_TELEMETRY_QUOTE");
  }
  if ((bid !== null && bid <= 0) || (ask !== null && ask <= 0)) {
    throw new Error("INVALID_BROKER_TELEMETRY_QUOTE");
  }
  const complete = bid !== null && ask !== null;
  if (quote.bid_ask_complete !== complete ||
      !["REALTIME", "FROZEN", "DELAYED", "DELAYED_FROZEN", "UNKNOWN"].includes(quote.market_data_type)) {
    throw new Error("INVALID_BROKER_TELEMETRY_QUOTE");
  }
  if (complete && ask! >= bid!) {
    if (midpoint === null || !nearlyEqual(midpoint, (bid! + ask!) / 2)) {
      throw new Error("INVALID_BROKER_TELEMETRY_QUOTE_MIDPOINT");
    }
  } else if (midpoint !== null) {
    throw new Error("INVALID_BROKER_TELEMETRY_QUOTE_MIDPOINT");
  }
  const observedAt = parseIso(quote.observed_at, "INVALID_BROKER_TELEMETRY_QUOTE_TIME");
  if (observedAt > collectedAt + 60_000) throw new Error("INVALID_BROKER_TELEMETRY_QUOTE_TIME");
  return quote;
}

function validatePosition(value: unknown, collectedAt: number): PositionTelemetryBody {
  if (!isRecord(value)) throw new Error("INVALID_BROKER_TELEMETRY_POSITION");
  requireExactKeys(value, [
    "con_id", "security_type", "local_symbol", "currency", "expiry", "strike", "right",
    "multiplier", "quantity", "average_cost", "market_value", "daily_pnl",
    "unrealized_pnl", "realized_pnl", "quote",
  ]);
  const position = value as unknown as PositionTelemetryBody;
  if (!Number.isInteger(position.con_id) || position.con_id <= 0 ||
      !/^[A-Z]{2,8}$/.test(position.security_type) ||
      typeof position.local_symbol !== "string" || position.local_symbol.length < 1 || position.local_symbol.length > 120 ||
      !/^[A-Z]{3}$/.test(position.currency) || !/^\d{0,8}$/.test(position.expiry) ||
      !/^[A-Z]?$/.test(position.right)) {
    throw new Error("INVALID_BROKER_TELEMETRY_POSITION");
  }
  const strike = decimalValue(position.strike, "INVALID_BROKER_TELEMETRY_POSITION");
  const multiplier = decimalValue(position.multiplier, "INVALID_BROKER_TELEMETRY_POSITION", false);
  const quantity = decimalValue(position.quantity, "INVALID_BROKER_TELEMETRY_POSITION", false);
  if ((strike !== null && strike < 0) || multiplier === null || multiplier <= 0 || quantity === null || quantity === 0) {
    throw new Error("INVALID_BROKER_TELEMETRY_POSITION");
  }
  for (const field of [position.average_cost, position.market_value, position.daily_pnl, position.unrealized_pnl, position.realized_pnl]) {
    decimalValue(field, "INVALID_BROKER_TELEMETRY_POSITION");
  }
  position.quote = validateQuote(position.quote, collectedAt);
  return position;
}

function sumIfComplete(positions: PositionTelemetryBody[], field: keyof PositionTelemetryBody): number | null {
  const values = positions.map((position) => decimalValue(position[field], "INVALID_BROKER_TELEMETRY_TOTAL"));
  return values.some((value) => value === null)
    ? null
    : values.reduce<number>((sum, value) => sum + Number(value), 0);
}

function validateTelemetry(bodyText: string, receivedAt: string): BrokerTelemetryBody {
  let raw: unknown;
  try {
    raw = JSON.parse(bodyText);
  } catch {
    throw new Error("INVALID_BROKER_TELEMETRY_JSON");
  }
  if (!isRecord(raw)) throw new Error("INVALID_BROKER_TELEMETRY_JSON");
  requireExactKeys(raw, [
    "mode", "gateway_connected", "paper_account_verified", "account_count", "symbol",
    "server_time", "collected_at", "positions", "totals", "quotes_complete", "pnl_complete",
    "fee_reconciliation_status", "error_codes",
  ]);
  const body = raw as unknown as BrokerTelemetryBody;
  if (body.mode !== "PAPER_READ_ONLY" || body.gateway_connected !== true ||
      body.paper_account_verified !== true || body.account_count !== 1 || body.symbol !== "TTWO" ||
      body.fee_reconciliation_status !== "LIVE_PNL_NOT_YET_RECONCILED_WITH_EXECUTION_FEES" ||
      !Array.isArray(body.positions) || body.positions.length > MAX_POSITIONS ||
      typeof body.quotes_complete !== "boolean" || typeof body.pnl_complete !== "boolean") {
    throw new Error("INVALID_BROKER_TELEMETRY");
  }
  const received = Date.parse(receivedAt);
  const collected = parseIso(body.collected_at, "INVALID_BROKER_TELEMETRY_TIME");
  const serverTime = parseIso(body.server_time, "INVALID_BROKER_TELEMETRY_TIME");
  if (collected > received + 60_000 || received - collected > 180_000 ||
      serverTime > received + 60_000 || received - serverTime > 5 * 60_000) {
    throw new Error("INVALID_BROKER_TELEMETRY_TIME_WINDOW");
  }

  body.positions = body.positions.map((position) => validatePosition(position, collected));
  const conIds = new Set(body.positions.map((position) => position.con_id));
  if (conIds.size !== body.positions.length) throw new Error("INVALID_BROKER_TELEMETRY_DUPLICATE_CON_ID");

  if (!isRecord(body.totals)) throw new Error("INVALID_BROKER_TELEMETRY_TOTAL");
  requireExactKeys(body.totals as unknown as Record<string, unknown>, [
    "market_value", "daily_pnl", "unrealized_pnl", "realized_pnl",
  ]);
  const totalFields = {
    market_value: "market_value",
    daily_pnl: "daily_pnl",
    unrealized_pnl: "unrealized_pnl",
    realized_pnl: "realized_pnl",
  } as const;
  for (const [totalField, positionField] of Object.entries(totalFields)) {
    const supplied = decimalValue(body.totals[totalField as keyof typeof body.totals], "INVALID_BROKER_TELEMETRY_TOTAL");
    const expected = sumIfComplete(body.positions, positionField);
    if ((supplied === null) !== (expected === null) ||
        (supplied !== null && expected !== null && !nearlyEqual(supplied, expected))) {
      throw new Error("INVALID_BROKER_TELEMETRY_TOTAL");
    }
  }
  const quotesComplete = body.positions.every((position) => position.quote?.bid_ask_complete === true);
  const pnlComplete = body.positions.every((position) =>
    position.market_value !== null && position.daily_pnl !== null &&
    position.unrealized_pnl !== null && position.realized_pnl !== null
  );
  if (body.quotes_complete !== quotesComplete || body.pnl_complete !== pnlComplete) {
    throw new Error("INVALID_BROKER_TELEMETRY_COMPLETENESS");
  }
  if (!Array.isArray(body.error_codes) || body.error_codes.length > 64 ||
      body.error_codes.some((code) => !Number.isInteger(code) || Math.abs(code) > 999_999) ||
      body.error_codes.some((code, index) => index > 0 && code <= body.error_codes[index - 1]!)) {
    throw new Error("INVALID_BROKER_TELEMETRY_ERROR_CODES");
  }
  return body;
}

function telemetryStatus(receivedAt: string, now = Date.now()): "FRESH" | "STALE" | "OFFLINE" {
  const age = now - Date.parse(receivedAt);
  if (age <= TELEMETRY_FRESH_MS) return "FRESH";
  return age <= TELEMETRY_OFFLINE_MS ? "STALE" : "OFFLINE";
}

async function recordTelemetry(request: Request, env: Env): Promise<Response> {
  const verified = await verifyTelemetryRequest(request, env);
  const body = validateTelemetry(verified.bodyText, verified.receivedAt);
  const telemetryId = randomId("broker-telemetry");
  await env.DB.prepare(
    `INSERT INTO broker_telemetry_latest(
      telemetry_source_id,telemetry_id,received_at,collected_at,server_time,mode,
      gateway_connected,paper_account_verified,account_count,symbol,position_count,
      total_market_value,total_daily_pnl,total_unrealized_pnl,total_realized_pnl,
      quotes_complete,pnl_complete,fee_reconciliation_status,error_codes_json,
      payload_sha256,payload_json
    ) VALUES(?,?,?,?,?,'PAPER_READ_ONLY',1,1,1,'TTWO',?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(telemetry_source_id) DO UPDATE SET
      telemetry_id=excluded.telemetry_id,received_at=excluded.received_at,
      collected_at=excluded.collected_at,server_time=excluded.server_time,
      position_count=excluded.position_count,total_market_value=excluded.total_market_value,
      total_daily_pnl=excluded.total_daily_pnl,total_unrealized_pnl=excluded.total_unrealized_pnl,
      total_realized_pnl=excluded.total_realized_pnl,quotes_complete=excluded.quotes_complete,
      pnl_complete=excluded.pnl_complete,fee_reconciliation_status=excluded.fee_reconciliation_status,
      error_codes_json=excluded.error_codes_json,payload_sha256=excluded.payload_sha256,
      payload_json=excluded.payload_json`,
  ).bind(
    verified.telemetryId, telemetryId, verified.receivedAt, body.collected_at, body.server_time,
    body.positions.length, body.totals.market_value, body.totals.daily_pnl,
    body.totals.unrealized_pnl, body.totals.realized_pnl,
    body.quotes_complete ? 1 : 0, body.pnl_complete ? 1 : 0,
    body.fee_reconciliation_status, JSON.stringify(body.error_codes),
    verified.payloadSha256, JSON.stringify(body),
  ).run();
  return Response.json({ accepted: true, telemetry_status: "FRESH", position_count: body.positions.length });
}

async function readTelemetry(env: Env): Promise<Response> {
  const configuredId = env.BROKER_TELEMETRY_ID?.trim();
  const row = configuredId
    ? await env.DB.prepare("SELECT * FROM broker_telemetry_latest WHERE telemetry_source_id=?")
      .bind(configuredId).first<TelemetryRow>()
    : await env.DB.prepare("SELECT * FROM broker_telemetry_latest ORDER BY received_at DESC LIMIT 1")
      .first<TelemetryRow>();
  if (!row) {
    return Response.json({
      status: "NOT_CONFIGURED",
      received_at: null,
      telemetry: null,
      execution_enabled: false,
    });
  }
  let telemetry: BrokerTelemetryBody;
  try {
    telemetry = JSON.parse(row.payload_json) as BrokerTelemetryBody;
  } catch {
    throw new Error("BROKER_TELEMETRY_STORAGE_INVALID");
  }
  return Response.json({
    status: telemetryStatus(row.received_at),
    received_at: row.received_at,
    payload_sha256: row.payload_sha256,
    telemetry,
    execution_enabled: false,
  });
}

export async function routeTelemetryInternal(request: Request, env: Env, path: string): Promise<Response | null> {
  if (path !== "/internal/broker/telemetry") return null;
  if (request.method !== "POST") return new Response("Method Not Allowed", { status: 405 });
  return recordTelemetry(request, env);
}

export async function routeTelemetryAuthenticated(request: Request, env: Env, path: string): Promise<Response | null> {
  if (path === "/api/broker/telemetry" && request.method === "GET") return readTelemetry(env);
  return null;
}
