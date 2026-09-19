import {
  CANONICAL_EXECUTION_STATUSES,
  EXECUTION_CONDITIONS,
  LIFECYCLE_EVIDENCE_EVENTS,
  coarseIntentStatus,
  validateLifecycleDetail,
} from "./broker-lifecycle";
import type {
  CanonicalExecutionStatus,
  ExecutionCondition,
  LifecycleEvidenceEvent,
} from "./broker-lifecycle";
import { randomId } from "./domain";

export interface StoredBridgeEventBody {
  broker_event_key?: string;
  event_type?: string;
  occurred_at?: string;
  broker_order_id?: number | null;
  broker_perm_id?: number | null;
  broker_exec_id?: string | null;
  detail?: Record<string, unknown>;
}

interface IntentIdentity {
  intent_id: string;
  order_ref: string;
  requested_quantity: number;
  created_at: string;
  position_id: string;
}

interface LatestStateRow {
  canonical_execution_status: CanonicalExecutionStatus;
  cumulative_filled_quantity: number;
  remaining_quantity: number;
  transmitted_to_broker: number;
  bridge_claimed_at: string | null;
  broker_submission_attempted_at: string | null;
  broker_acknowledged_at: string | null;
  submitted_at: string | null;
  working_since: string | null;
  last_market_update_at: string | null;
  time_in_force: string | null;
}

const PROJECTION_TRANSITIONS: Record<CanonicalExecutionStatus, readonly CanonicalExecutionStatus[]> = {
  CREATED: CANONICAL_EXECUTION_STATUSES,
  REVALIDATING: [
    "REVALIDATING", "PREVIEW_READY", "EXPIRED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  EXECUTION_PREVIEW: CANONICAL_EXECUTION_STATUSES.filter((item) => item !== "CREATED"),
  PREVIEW_READY: [
    "PREVIEW_READY", "CONFIRMED", "EXPIRED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  CONFIRMED: [
    "CONFIRMED", "READY", "CLAIMED", "EXPIRED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  READY: ["READY", "CLAIMED", "LOCAL_NOT_TRANSMITTED", "EXPIRED"],
  CLAIMED: [
    "CLAIMED", "BROKER_SUBMISSION_ATTEMPTED", "LOCAL_NOT_TRANSMITTED", "PENDING_SUBMIT",
    "PRE_SUBMITTED", "WORKING",
    "PARTIALLY_FILLED", "FILLED", "PENDING_CANCEL", "CANCELLED", "API_CANCELLED",
    "REJECTED", "INACTIVE", "EXPIRED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  BROKER_SUBMISSION_ATTEMPTED: [
    "BROKER_SUBMISSION_ATTEMPTED", "PENDING_SUBMIT", "PRE_SUBMITTED", "WORKING",
    "PARTIALLY_FILLED", "FILLED", "PENDING_CANCEL", "CANCELLED", "API_CANCELLED",
    "REJECTED", "INACTIVE", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  LOCAL_NOT_TRANSMITTED: ["LOCAL_NOT_TRANSMITTED"],
  PENDING_SUBMIT: [
    "PENDING_SUBMIT", "PRE_SUBMITTED", "WORKING", "PARTIALLY_FILLED", "FILLED",
    "PENDING_CANCEL", "CANCELLED", "API_CANCELLED", "REJECTED", "INACTIVE",
    "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  PRE_SUBMITTED: [
    "PRE_SUBMITTED", "WORKING", "PARTIALLY_FILLED", "FILLED", "PENDING_CANCEL",
    "CANCELLED", "API_CANCELLED", "REJECTED", "INACTIVE", "AMBIGUOUS",
    "RECONCILIATION_REQUIRED",
  ],
  WORKING: [
    "WORKING", "PARTIALLY_FILLED", "FILLED", "PENDING_CANCEL", "CANCELLED",
    "API_CANCELLED", "REJECTED", "INACTIVE", "EXPIRED", "AMBIGUOUS",
    "RECONCILIATION_REQUIRED",
  ],
  PARTIALLY_FILLED: [
    "PARTIALLY_FILLED", "FILLED", "PENDING_CANCEL", "CANCELLED", "API_CANCELLED",
    "REJECTED", "INACTIVE", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  FILLED: ["FILLED"],
  PENDING_CANCEL: [
    "PENDING_CANCEL", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "API_CANCELLED",
    "REJECTED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  CANCELLED: ["CANCELLED"],
  API_CANCELLED: ["API_CANCELLED"],
  REJECTED: ["REJECTED"],
  INACTIVE: [
    "INACTIVE", "PENDING_SUBMIT", "PRE_SUBMITTED", "WORKING", "PARTIALLY_FILLED", "FILLED",
    "CANCELLED", "API_CANCELLED", "REJECTED", "AMBIGUOUS", "RECONCILIATION_REQUIRED",
  ],
  EXPIRED: ["EXPIRED"],
  AMBIGUOUS: [
    "AMBIGUOUS", "RECONCILIATION_REQUIRED", "WORKING", "PARTIALLY_FILLED", "FILLED",
    "CANCELLED", "API_CANCELLED", "REJECTED", "EXPIRED",
  ],
  RECONCILIATION_REQUIRED: [
    "RECONCILIATION_REQUIRED", "WORKING", "PARTIALLY_FILLED", "FILLED", "CANCELLED",
    "API_CANCELLED", "REJECTED", "EXPIRED",
  ],
};

function projectionTransitionAllowed(
  previous: LatestStateRow | null,
  canonical: CanonicalExecutionStatus,
  filled: number | null,
): boolean {
  if (!previous) return true;
  if (filled !== null && filled < previous.cumulative_filled_quantity) return false;
  return PROJECTION_TRANSITIONS[previous.canonical_execution_status].includes(canonical);
}

const LEGACY_CANONICAL: Record<string, CanonicalExecutionStatus> = {
  BROKER_ACKNOWLEDGED: "WORKING",
  PARTIAL_FILL: "PARTIALLY_FILLED",
  FILLED: "FILLED",
  REJECTED: "REJECTED",
  CANCELLED: "CANCELLED",
  EXPIRED: "EXPIRED",
  AMBIGUOUS: "AMBIGUOUS",
};

const LEGACY_CONDITION: Record<string, ExecutionCondition> = {
  BROKER_ACKNOWLEDGED: "WORKING_NO_FILL_YET",
  PARTIAL_FILL: "PARTIAL_FILL_ACTIVE",
  AMBIGUOUS: "STATE_UNKNOWN",
};

const LEGACY_EVIDENCE_KIND: Record<string, string> = {
  BROKER_ACKNOWLEDGED: "ORDER_STATUS",
  PARTIAL_FILL: "EXECUTION",
  FILLED: "EXECUTION",
  REJECTED: "ERROR",
  CANCELLED: "ORDER_STATUS",
  EXPIRED: "ORDER_STATUS",
  AMBIGUOUS: "RECOVERY_OBSERVATION",
  COMMISSION_REPORT: "COMMISSION_REPORT",
  RECOVERY_OBSERVATION: "RECOVERY_OBSERVATION",
};

async function sha256Hex(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return [...digest].map((item) => item.toString(16).padStart(2, "0")).join("");
}

function finiteOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringOrNull(value: unknown, maximum = 100): string | null {
  return typeof value === "string" && value ? value.slice(0, maximum) : null;
}

function booleanInteger(value: unknown): number | null {
  return typeof value === "boolean" ? (value ? 1 : 0) : null;
}

const BROKER_ACCOUNT_PATTERN = /\b(?:DU|U|F|DF)\d{4,}\b/gi;
const INLINE_SECRET_PATTERN = /(password|passwd|token|secret|api[_ -]?key)\s*[:=]\s*[^\s,;]+/gi;

function redactLifecycleEvidence(value: unknown): unknown {
  if (Array.isArray(value)) return value.slice(0, 500).map(redactLifecycleEvidence);
  if (value && typeof value === "object") {
    const redacted: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      const normalizedKey = key.toLowerCase();
      const sensitiveKey = ["account", "password", "passwd", "secret", "token", "api_key"]
        .some((marker) => normalizedKey.includes(marker));
      if (sensitiveKey) {
        redacted[key] = "[REDACTED]";
      } else if (normalizedKey === "advanced_rejection_json" && typeof item === "string") {
        try {
          redacted[key] = JSON.stringify(redactLifecycleEvidence(JSON.parse(item)));
        } catch {
          redacted[key] = redactLifecycleEvidence(item);
        }
      } else {
        redacted[key] = redactLifecycleEvidence(item);
      }
    }
    return redacted;
  }
  if (typeof value === "string") {
    return value
      .replace(BROKER_ACCOUNT_PATTERN, "[REDACTED_ACCOUNT]")
      .replace(INLINE_SECRET_PATTERN, "$1=[REDACTED]")
      .slice(0, 8_000);
  }
  return value;
}

function lifecycleEventStatement(
  db: D1Database,
  input: {
    key: string;
    intentId: string;
    evidenceKind: string;
    rawStatus: string | null;
    canonical: CanonicalExecutionStatus | null;
    condition: ExecutionCondition | null;
    occurredAt: string;
    receivedAt: string;
    bridgeId: string;
    orderId: number | null;
    permId: number | null;
    execId: string | null;
    rawHash: string;
    evidence: Record<string, unknown>;
  },
): D1PreparedStatement {
  return db.prepare(
    `INSERT OR IGNORE INTO broker_order_lifecycle_events(
      lifecycle_event_id,broker_event_key,intent_id,evidence_kind,raw_broker_status,
      canonical_execution_status,execution_condition,occurred_at,received_at,bridge_id,
      broker_order_id,broker_perm_id,broker_exec_id,raw_evidence_hash,evidence_json
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
  ).bind(
    randomId("broker-lifecycle"), input.key, input.intentId, input.evidenceKind,
    input.rawStatus, input.canonical, input.condition, input.occurredAt, input.receivedAt,
    input.bridgeId, input.orderId, input.permId, input.execId, input.rawHash,
    JSON.stringify(input.evidence),
  );
}

function latestStateStatement(
  db: D1Database,
  intent: IntentIdentity,
  input: {
    canonical: CanonicalExecutionStatus;
    condition: ExecutionCondition;
    occurredAt: string;
    rawStatus?: string | null;
    orderId?: number | null;
    permId?: number | null;
    filled?: number | null;
    remaining?: number | null;
    averageFillPrice?: number | null;
    lastFillPrice?: number | null;
    timeInForce?: string | null;
    cancellationCause?: string | null;
    rejectionCategory?: string | null;
    bridgeClaimedAt?: string | null;
    submissionAttemptedAt?: string | null;
    transmitted?: number | null;
    acknowledgedAt?: string | null;
    submittedAt?: string | null;
    workingSince?: string | null;
    lastMarketUpdateAt?: string | null;
  },
  previous: LatestStateRow | null,
): D1PreparedStatement {
  const filled = input.filled ?? previous?.cumulative_filled_quantity ?? 0;
  const remaining = input.remaining ?? previous?.remaining_quantity ?? intent.requested_quantity;
  const transmitted = input.transmitted ?? previous?.transmitted_to_broker ?? 0;
  return db.prepare(
    `INSERT INTO broker_order_state_latest(
      intent_id,order_ref,broker_order_id,broker_perm_id,raw_broker_status,
      canonical_execution_status,execution_condition,requested_quantity,
      cumulative_filled_quantity,remaining_quantity,average_fill_price,last_fill_price,
      time_in_force,cancellation_cause,rejection_category,intent_created_at,
      bridge_claimed_at,broker_submission_attempted_at,transmitted_to_broker,
      broker_acknowledged_at,submitted_at,working_since,last_status_at,
      last_market_update_at,updated_at
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(intent_id) DO UPDATE SET
      broker_order_id=coalesce(excluded.broker_order_id,broker_order_id),
      broker_perm_id=coalesce(excluded.broker_perm_id,broker_perm_id),
      raw_broker_status=coalesce(excluded.raw_broker_status,raw_broker_status),
      canonical_execution_status=excluded.canonical_execution_status,
      execution_condition=excluded.execution_condition,
      cumulative_filled_quantity=excluded.cumulative_filled_quantity,
      remaining_quantity=excluded.remaining_quantity,
      average_fill_price=coalesce(excluded.average_fill_price,average_fill_price),
      last_fill_price=coalesce(excluded.last_fill_price,last_fill_price),
      time_in_force=coalesce(excluded.time_in_force,time_in_force),
      cancellation_cause=coalesce(excluded.cancellation_cause,cancellation_cause),
      rejection_category=coalesce(excluded.rejection_category,rejection_category),
      bridge_claimed_at=coalesce(excluded.bridge_claimed_at,bridge_claimed_at),
      broker_submission_attempted_at=coalesce(
        excluded.broker_submission_attempted_at,broker_submission_attempted_at
      ),
      transmitted_to_broker=excluded.transmitted_to_broker,
      broker_acknowledged_at=coalesce(excluded.broker_acknowledged_at,broker_acknowledged_at),
      submitted_at=coalesce(excluded.submitted_at,submitted_at),
      working_since=coalesce(excluded.working_since,working_since),
      last_status_at=excluded.last_status_at,
      last_market_update_at=coalesce(excluded.last_market_update_at,last_market_update_at),
      updated_at=excluded.updated_at
    WHERE excluded.last_status_at >= broker_order_state_latest.last_status_at`,
  ).bind(
    intent.intent_id, intent.order_ref, input.orderId ?? null, input.permId ?? null,
    input.rawStatus ?? null, input.canonical, input.condition, intent.requested_quantity,
    filled, remaining, input.averageFillPrice ?? null, input.lastFillPrice ?? null,
    input.timeInForce ?? previous?.time_in_force ?? null, input.cancellationCause ?? null,
    input.rejectionCategory ?? null, intent.created_at,
    input.bridgeClaimedAt ?? previous?.bridge_claimed_at ?? null,
    input.submissionAttemptedAt ?? previous?.broker_submission_attempted_at ?? null,
    transmitted,
    input.acknowledgedAt ?? previous?.broker_acknowledged_at ?? null,
    input.submittedAt ?? previous?.submitted_at ?? null,
    input.workingSince ?? previous?.working_since ?? null,
    input.occurredAt,
    input.lastMarketUpdateAt ?? previous?.last_market_update_at ?? null,
    input.occurredAt,
  );
}

export async function recordInitialLifecycle(
  db: D1Database,
  intent: IntentIdentity,
): Promise<void> {
  const createdHash = await sha256Hex(`${intent.intent_id}:INTENT_CREATED`);
  const readyHash = await sha256Hex(`${intent.intent_id}:READY`);
  await db.batch([
    lifecycleEventStatement(db, {
      key: `intent-created:${intent.intent_id}`,
      intentId: intent.intent_id,
      evidenceKind: "INTENT_CREATED",
      rawStatus: null,
      canonical: "CREATED",
      condition: "NONE",
      occurredAt: intent.created_at,
      receivedAt: intent.created_at,
      bridgeId: "control-plane",
      orderId: null,
      permId: null,
      execId: null,
      rawHash: createdHash,
      evidence: { source: "broker_execution_intents", status: "CREATED" },
    }),
    lifecycleEventStatement(db, {
      key: `intent-ready:${intent.intent_id}`,
      intentId: intent.intent_id,
      evidenceKind: "READY",
      rawStatus: null,
      canonical: "READY",
      condition: "NONE",
      occurredAt: intent.created_at,
      receivedAt: intent.created_at,
      bridgeId: "control-plane",
      orderId: null,
      permId: null,
      execId: null,
      rawHash: readyHash,
      evidence: { source: "broker_execution_intents", status: "READY" },
    }),
    latestStateStatement(db, intent, {
      canonical: "READY",
      condition: "NONE",
      occurredAt: intent.created_at,
      transmitted: 0,
    }, null),
  ]);
}

export async function recordClaimedLifecycle(
  db: D1Database,
  intent: IntentIdentity,
  bridgeId: string,
  claimedAt: string,
): Promise<void> {
  const rawHash = await sha256Hex(`${intent.intent_id}:CLAIMED:${bridgeId}:${claimedAt}`);
  const previous = await db.prepare(
    "SELECT * FROM broker_order_state_latest WHERE intent_id=?",
  ).bind(intent.intent_id).first<LatestStateRow>();
  await db.batch([
    lifecycleEventStatement(db, {
      key: `claim:${intent.intent_id}:${claimedAt}`,
      intentId: intent.intent_id,
      evidenceKind: "CLAIMED",
      rawStatus: null,
      canonical: "CLAIMED",
      condition: "NONE",
      occurredAt: claimedAt,
      receivedAt: claimedAt,
      bridgeId,
      orderId: null,
      permId: null,
      execId: null,
      rawHash,
      evidence: { source: "control-plane-claim", bridge_id: bridgeId },
    }),
    latestStateStatement(db, intent, {
      canonical: "CLAIMED",
      condition: "NONE",
      occurredAt: claimedAt,
      bridgeClaimedAt: claimedAt,
    }, previous),
  ]);
}

export async function recordControlStatusLifecycle(
  db: D1Database,
  intent: IntentIdentity,
  input: {
    canonical: "EXPIRED" | "RECONCILIATION_REQUIRED";
    condition: "NONE" | "STATE_UNKNOWN";
    evidenceKind: "ORDER_STATUS" | "LEASE_EXPIRED";
    occurredAt: string;
    reason: string;
  },
): Promise<void> {
  const key = `control:${input.reason}:${intent.intent_id}:${input.occurredAt}`;
  const rawHash = await sha256Hex(key);
  const previous = await db.prepare(
    "SELECT * FROM broker_order_state_latest WHERE intent_id=?",
  ).bind(intent.intent_id).first<LatestStateRow>();
  const statements = [lifecycleEventStatement(db, {
      key,
      intentId: intent.intent_id,
      evidenceKind: input.evidenceKind,
      rawStatus: input.reason,
      canonical: input.canonical,
      condition: input.condition,
      occurredAt: input.occurredAt,
      receivedAt: input.occurredAt,
      bridgeId: "control-plane",
      orderId: null,
      permId: null,
      execId: null,
      rawHash,
      evidence: { source: "control-plane", reason: input.reason },
    })];
  if (projectionTransitionAllowed(previous, input.canonical, null)) {
    statements.push(latestStateStatement(db, intent, {
      canonical: input.canonical,
      condition: input.condition,
      occurredAt: input.occurredAt,
      rawStatus: input.reason,
      cancellationCause: input.reason === "CLAIM_LEASE_EXPIRED" ? "SESSION_LOST" : null,
    }, previous));
  }
  await db.batch(statements);
}

function normalizedLegacyDetail(eventType: string, detail: Record<string, unknown>) {
  const canonical = LEGACY_CANONICAL[eventType] ?? null;
  return {
    raw_evidence_hash: null,
    raw_broker_status: eventType,
    canonical_execution_status: canonical,
    execution_condition: LEGACY_CONDITION[eventType] ?? (canonical ? "NONE" : null),
    filled: finiteOrNull(detail.filled ?? detail.cumulative_quantity),
    remaining: finiteOrNull(detail.remaining),
    average_fill_price: finiteOrNull(detail.average_fill_price),
    last_fill_price: finiteOrNull(detail.last_fill_price),
    transmitted_to_broker: canonical && canonical !== "LOCAL_NOT_TRANSMITTED" ? true : null,
    time_in_force: stringOrNull(detail.time_in_force, 12),
    cancellation_cause: stringOrNull(detail.cancellation_cause, 40),
    normalized_category: stringOrNull(detail.normalized_category, 60),
  };
}

export async function lifecycleEventOwner(db: D1Database, key: string): Promise<string | null> {
  const row = await db.prepare(
    "SELECT intent_id FROM broker_order_lifecycle_events WHERE broker_event_key=?",
  ).bind(key).first<{ intent_id: string }>();
  return row?.intent_id ?? null;
}

export async function persistBridgeLifecycleEvidence(
  db: D1Database,
  bridgeId: string,
  receivedAt: string,
  intent: IntentIdentity,
  body: StoredBridgeEventBody,
  bodyText: string,
): Promise<{ canonical: CanonicalExecutionStatus | null; coarse: string | null }> {
  const eventType = String(body.event_type ?? "");
  const detail = redactLifecycleEvidence(body.detail ?? {}) as Record<string, unknown>;
  const isNewEvidence = LIFECYCLE_EVIDENCE_EVENTS.includes(eventType as LifecycleEvidenceEvent);
  const normalized = isNewEvidence
    ? validateLifecycleDetail(eventType as LifecycleEvidenceEvent, detail)
    : normalizedLegacyDetail(eventType, detail);
  const rawHash: string = isNewEvidence
    ? String(normalized.raw_evidence_hash)
    : await sha256Hex(bodyText);
  const canonical = normalized.canonical_execution_status;
  const condition = normalized.execution_condition as ExecutionCondition | null;
  if (canonical && !CANONICAL_EXECUTION_STATUSES.includes(canonical)) {
    throw new Error("INVALID_BROKER_LIFECYCLE_STATUS");
  }
  if (condition && !EXECUTION_CONDITIONS.includes(condition)) {
    throw new Error("INVALID_BROKER_LIFECYCLE_CONDITION");
  }
  const occurredAt = String(body.occurred_at);
  const eventKey = String(body.broker_event_key);
  const evidenceKind = isNewEvidence ? eventType : LEGACY_EVIDENCE_KIND[eventType];
  if (!evidenceKind) throw new Error("INVALID_BROKER_LIFECYCLE_EVENT_TYPE");
  const previous = await db.prepare(
    "SELECT * FROM broker_order_state_latest WHERE intent_id=?",
  ).bind(intent.intent_id).first<LatestStateRow>();
  const executionIdentity = body.broker_exec_id ?? stringOrNull(detail.exec_id, 100);
  if (["EXECUTION", "COMMISSION_REPORT"].includes(eventType) && executionIdentity) {
    const existingExecution = await db.prepare(
      "SELECT intent_id FROM broker_executions WHERE exec_id=?",
    ).bind(executionIdentity).first<{ intent_id: string }>();
    if (existingExecution && existingExecution.intent_id !== intent.intent_id) {
      throw new Error("BROKER_EXECUTION_ID_CONFLICT");
    }
  }
  const statements: D1PreparedStatement[] = [lifecycleEventStatement(db, {
    key: eventKey,
    intentId: intent.intent_id,
    evidenceKind,
    rawStatus: normalized.raw_broker_status,
    canonical,
    condition,
    occurredAt,
    receivedAt,
    bridgeId,
    orderId: body.broker_order_id ?? null,
    permId: body.broker_perm_id ?? null,
    execId: body.broker_exec_id ?? null,
    rawHash,
    evidence: detail,
  })];

  if (canonical && projectionTransitionAllowed(previous, canonical, normalized.filled)) {
    const submitted = ["PENDING_SUBMIT", "PRE_SUBMITTED", "WORKING", "PARTIALLY_FILLED", "FILLED"]
      .includes(canonical);
    const acknowledged = ["PRE_SUBMITTED", "WORKING", "PARTIALLY_FILLED", "FILLED"]
      .includes(canonical);
    statements.push(latestStateStatement(db, intent, {
      canonical,
      condition: condition ?? "NONE",
      occurredAt,
      rawStatus: normalized.raw_broker_status,
      orderId: body.broker_order_id ?? null,
      permId: body.broker_perm_id ?? null,
      filled: normalized.filled,
      remaining: normalized.remaining,
      averageFillPrice: normalized.average_fill_price,
      lastFillPrice: normalized.last_fill_price,
      timeInForce: normalized.time_in_force,
      cancellationCause: normalized.cancellation_cause,
      rejectionCategory: normalized.normalized_category,
      submissionAttemptedAt: eventType === "SUBMISSION_ATTEMPTED" ? occurredAt : null,
      transmitted: booleanInteger(normalized.transmitted_to_broker),
      acknowledgedAt: acknowledged ? occurredAt : null,
      submittedAt: submitted ? occurredAt : null,
      workingSince: canonical === "WORKING" ? occurredAt : null,
      lastMarketUpdateAt: stringOrNull(detail.last_market_update_at, 40),
    }, previous));
  } else if (eventType === "SUBMISSION_ATTEMPTED") {
    statements.push(db.prepare(
      `UPDATE broker_order_state_latest SET
       broker_submission_attempted_at=coalesce(broker_submission_attempted_at,?),updated_at=?
       WHERE intent_id=?`,
    ).bind(occurredAt, receivedAt, intent.intent_id));
  }

  if (eventType === "ERROR") {
    statements.push(db.prepare(
      `INSERT OR IGNORE INTO broker_order_errors(
        error_event_key,intent_id,broker_order_id,broker_perm_id,broker_error_code,
        redacted_broker_message,advanced_rejection_json,normalized_category,precaution,
        occurred_at,raw_evidence_hash
      ) VALUES(?,?,?,?,?,?,?,?,?,?,?)`,
    ).bind(
      eventKey, intent.intent_id, body.broker_order_id ?? null, body.broker_perm_id ?? null,
      detail.broker_error_code, detail.redacted_broker_message,
      stringOrNull(detail.advanced_rejection_json, 8_000),
      normalized.normalized_category ?? "UNKNOWN_BROKER_REJECTION",
      detail.precaution === true ? 1 : 0, occurredAt, rawHash,
    ));
  }
  if (eventType === "EXECUTION") {
    if (!body.broker_exec_id) throw new Error("INVALID_BROKER_EXECUTION_ID");
    const shares = finiteOrNull(detail.shares);
    const cumulative = finiteOrNull(detail.cumulative_quantity);
    const price = finiteOrNull(detail.price);
    if (shares === null || shares <= 0 || cumulative === null || cumulative <= 0 ||
        price === null || price < 0) throw new Error("INVALID_BROKER_EXECUTION_VALUES");
    statements.push(db.prepare(
      `INSERT OR IGNORE INTO broker_executions(
        exec_id,intent_id,broker_order_id,broker_perm_id,execution_time,side,shares,
        cumulative_quantity,price,exchange,liquidation,combo_bid_near_fill,
        combo_ask_near_fill,execution_delay_seconds,slippage_vs_decision_midpoint,
        slippage_vs_executable_quote,partial_fill_sequence,raw_evidence_hash
      ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    ).bind(
      body.broker_exec_id, intent.intent_id, body.broker_order_id ?? null,
      body.broker_perm_id ?? null, String(detail.execution_time ?? occurredAt),
      stringOrNull(detail.side, 16), shares, cumulative, price,
      stringOrNull(detail.exchange, 40), booleanInteger(detail.liquidation),
      finiteOrNull(detail.combo_bid_near_fill), finiteOrNull(detail.combo_ask_near_fill),
      finiteOrNull(detail.execution_delay_seconds),
      finiteOrNull(detail.slippage_vs_decision_midpoint),
      finiteOrNull(detail.slippage_vs_executable_quote),
      Number.isInteger(detail.partial_fill_sequence) ? detail.partial_fill_sequence : null,
      rawHash,
    ));
  }
  if (eventType === "COMMISSION_REPORT") {
    const execId = body.broker_exec_id ?? stringOrNull(detail.exec_id, 100);
    const commission = finiteOrNull(detail.commission);
    const currency = stringOrNull(detail.currency, 12);
    if (!execId || commission === null || !currency) {
      throw new Error("INVALID_BROKER_COMMISSION_EVIDENCE");
    }
    statements.push(db.prepare(
      `INSERT OR IGNORE INTO broker_commissions(
        exec_id,intent_id,commission,currency,realized_pnl,yield_value,
        yield_redemption_date,occurred_at,raw_evidence_hash
      ) VALUES(?,?,?,?,?,?,?,?,?)`,
    ).bind(
      execId, intent.intent_id, commission, currency,
      finiteOrNull(detail.realized_pnl), finiteOrNull(detail.yield_value),
      Number.isInteger(detail.yield_redemption_date) ? detail.yield_redemption_date : null,
      occurredAt, rawHash,
    ));
  }
  if (eventType === "SUBMISSION_ATTEMPTED" && detail.market_snapshot) {
    const snapshot = detail.market_snapshot as Record<string, unknown>;
    statements.push(marketSnapshotStatement(db, intent.intent_id, snapshot, rawHash));
  }
  if (eventType === "REPRICE_PROPOSAL") {
    statements.push(repriceProposalStatement(db, intent.intent_id, detail));
  }
  await db.batch(statements);
  return { canonical, coarse: canonical ? coarseIntentStatus(canonical) : null };
}

function marketSnapshotStatement(
  db: D1Database,
  intentId: string,
  snapshot: Record<string, unknown>,
  rawHash: string,
): D1PreparedStatement {
  const legsAreValid = Array.isArray(snapshot.legs) && snapshot.legs.length > 0 &&
    snapshot.legs.every((leg) => {
      if (!leg || typeof leg !== "object" || Array.isArray(leg)) return false;
      const value = leg as Record<string, unknown>;
      return Number.isInteger(value.con_id) && Number(value.con_id) > 0 &&
        Number.isInteger(value.ratio) && Number(value.ratio) > 0 &&
        typeof value.action === "string" && value.action.length > 0;
    });
  if (!legsAreValid || !Number.isInteger(snapshot.quantity) || Number(snapshot.quantity) <= 0 ||
      typeof snapshot.ticker !== "string" || snapshot.ticker.length === 0 ||
      typeof snapshot.strategy !== "string" || snapshot.strategy.length === 0 ||
      typeof snapshot.market_data_type !== "string" ||
      typeof snapshot.data_freshness !== "string" ||
      typeof snapshot.signed_price_convention_status !== "string" ||
      !Number.isFinite(Date.parse(String(snapshot.snapshot_timestamp ?? ""))) ||
      !["DEBIT", "CREDIT"].includes(String(snapshot.cash_flow_type)) ||
      finiteOrNull(snapshot.requested_limit) === null || Number(snapshot.requested_limit) < 0) {
    throw new Error("INVALID_BROKER_MARKET_SNAPSHOT");
  }
  return db.prepare(
    `INSERT OR IGNORE INTO broker_market_snapshots(
      snapshot_id,intent_id,captured_at,ticker,candidate_id,strategy,quantity,legs_json,
      market_data_type,data_freshness,combo_bid,combo_ask,combo_midpoint,
      synthetic_combo_bid,synthetic_combo_ask,signed_price_convention_status,
      requested_limit,cash_flow_type,expected_commission,capital_required,maximum_loss,
      spread_absolute,spread_percent,quote_age_seconds,snapshot_json,raw_evidence_hash
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
  ).bind(
    randomId("broker-market-snapshot"), intentId, snapshot.snapshot_timestamp,
    snapshot.ticker, stringOrNull(snapshot.candidate_id, 180), snapshot.strategy,
    snapshot.quantity, JSON.stringify(snapshot.legs), snapshot.market_data_type,
    snapshot.data_freshness, finiteOrNull(snapshot.combo_bid), finiteOrNull(snapshot.combo_ask),
    finiteOrNull(snapshot.combo_midpoint), finiteOrNull(snapshot.synthetic_combo_bid),
    finiteOrNull(snapshot.synthetic_combo_ask), snapshot.signed_price_convention_status,
    snapshot.requested_limit, snapshot.cash_flow_type, finiteOrNull(snapshot.expected_commission),
    finiteOrNull(snapshot.capital_required), finiteOrNull(snapshot.maximum_loss),
    finiteOrNull(snapshot.spread_absolute), finiteOrNull(snapshot.spread_percent),
    finiteOrNull(snapshot.quote_age_seconds), JSON.stringify(snapshot), rawHash,
  );
}

function repriceProposalStatement(
  db: D1Database,
  intentId: string,
  detail: Record<string, unknown>,
): D1PreparedStatement {
  const statuses = [
    "READY_FOR_HUMAN_PREVIEW",
    "REPRICE_UNAVAILABLE_DATA_STALE",
    "REPRICE_UNAVAILABLE_PRICE_CONVENTION_UNVERIFIED",
    "BLOCKED_AUTHORIZED_BOUND",
    "BLOCKED_HARD_BUDGET",
    "BLOCKED_MAX_LOSS",
    "BLOCKED_ORDER_SHAPE_CHANGED",
    "BLOCKED_DIRECTION",
  ];
  if (detail.automatic_action_allowed !== false ||
      !["DEBIT", "CREDIT"].includes(String(detail.cash_flow_type)) ||
      !statuses.includes(String(detail.status)) ||
      !/^broker-reprice_[a-zA-Z0-9._-]+$/.test(String(detail.proposal_id ?? "")) ||
      !Number.isFinite(Date.parse(String(detail.created_at ?? ""))) ||
      !/^[a-f0-9]{64}$/.test(String(detail.original_order_shape_hash ?? "")) ||
      !/^[a-f0-9]{64}$/.test(String(detail.proposed_order_shape_hash ?? ""))) {
    throw new Error("INVALID_BROKER_REPRICE_PROPOSAL");
  }
  const requiredNumbers = [
    detail.current_limit,
    detail.proposed_limit,
    detail.price_difference,
    detail.incremental_capital_impact,
    detail.authorized_boundary,
  ];
  if (requiredNumbers.some((item) => finiteOrNull(item) === null)) {
    throw new Error("INVALID_BROKER_REPRICE_PROPOSAL");
  }
  if (Number(detail.current_limit) < 0 || Number(detail.proposed_limit) < 0 ||
      Number(detail.incremental_capital_impact) < 0 || Number(detail.authorized_boundary) < 0) {
    throw new Error("INVALID_BROKER_REPRICE_PROPOSAL");
  }
  return db.prepare(
    `INSERT OR IGNORE INTO broker_reprice_proposals(
      proposal_id,intent_id,created_at,status,cash_flow_type,current_limit,
      proposed_limit,current_combo_bid,current_combo_ask,price_difference,
      incremental_capital_impact,remaining_hard_budget_headroom,authorized_boundary,
      new_estimated_pnl_economics,original_order_shape_hash,proposed_order_shape_hash,
      automatic_action_allowed,proposal_json
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)`,
  ).bind(
    String(detail.proposal_id ?? randomId("broker-reprice")), intentId,
    String(detail.created_at), detail.status, detail.cash_flow_type, detail.current_limit,
    detail.proposed_limit, finiteOrNull(detail.current_combo_bid),
    finiteOrNull(detail.current_combo_ask), detail.price_difference,
    detail.incremental_capital_impact, finiteOrNull(detail.remaining_hard_budget_headroom),
    detail.authorized_boundary, finiteOrNull(detail.new_estimated_pnl_economics),
    detail.original_order_shape_hash, detail.proposed_order_shape_hash, JSON.stringify(detail),
  );
}

export async function executionDiagnosticsForPosition(
  db: D1Database,
  positionId: string,
): Promise<Record<string, unknown>> {
  const latest = await db.prepare(
    `SELECT s.*,i.intent_type,i.status AS coarse_intent_status
     FROM broker_order_state_latest s
     JOIN broker_execution_intents i ON i.intent_id=s.intent_id
     WHERE i.position_id=? ORDER BY s.updated_at DESC LIMIT 1`,
  ).bind(positionId).first<Record<string, unknown>>();
  if (!latest) return {
    latest: null, timeline: [], errors: [], executions: [], commissions: [],
    market_snapshot: null, reprice_proposals: [],
  };
  const workingSince = Date.parse(String(latest.working_since ?? ""));
  latest.seconds_working = Number.isFinite(workingSince)
    ? Math.max(0, Math.floor((Date.now() - workingSince) / 1_000))
    : null;
  const intentId = String(latest.intent_id);
  const results = await db.batch([
    db.prepare(
      `SELECT evidence_kind,raw_broker_status,canonical_execution_status,
       execution_condition,occurred_at,received_at,broker_order_id,broker_perm_id,
       broker_exec_id FROM broker_order_lifecycle_events
       WHERE intent_id=? ORDER BY occurred_at ASC,received_at ASC LIMIT 200`,
    ).bind(intentId),
    db.prepare(
      `SELECT broker_error_code,redacted_broker_message,normalized_category,
       precaution,occurred_at FROM broker_order_errors
       WHERE intent_id=? ORDER BY occurred_at ASC LIMIT 200`,
    ).bind(intentId),
    db.prepare(
      `SELECT exec_id,execution_time,side,shares,cumulative_quantity,price,exchange,
       combo_bid_near_fill,combo_ask_near_fill,execution_delay_seconds,
       slippage_vs_decision_midpoint,slippage_vs_executable_quote,partial_fill_sequence
       FROM broker_executions WHERE intent_id=? ORDER BY execution_time ASC LIMIT 500`,
    ).bind(intentId),
    db.prepare(
      `SELECT c.* FROM broker_commissions c JOIN broker_executions e ON e.exec_id=c.exec_id
       WHERE e.intent_id=? ORDER BY c.occurred_at ASC LIMIT 500`,
    ).bind(intentId),
    db.prepare("SELECT * FROM broker_market_snapshots WHERE intent_id=?").bind(intentId),
    db.prepare(
      `SELECT * FROM broker_reprice_proposals WHERE intent_id=? ORDER BY created_at DESC LIMIT 20`,
    ).bind(intentId),
  ]);
  return {
    latest,
    timeline: results[0]?.results ?? [],
    errors: results[1]?.results ?? [],
    executions: results[2]?.results ?? [],
    commissions: results[3]?.results ?? [],
    market_snapshot: results[4]?.results?.[0] ?? null,
    reprice_proposals: results[5]?.results ?? [],
  };
}
