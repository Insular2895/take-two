export const CANONICAL_EXECUTION_STATUSES = [
  "CREATED",
  "REVALIDATING",
  "EXECUTION_PREVIEW",
  "PREVIEW_READY",
  "CONFIRMED",
  "READY",
  "CLAIMED",
  "BROKER_SUBMISSION_ATTEMPTED",
  "LOCAL_NOT_TRANSMITTED",
  "PENDING_SUBMIT",
  "PRE_SUBMITTED",
  "WORKING",
  "PARTIALLY_FILLED",
  "FILLED",
  "PENDING_CANCEL",
  "CANCELLED",
  "API_CANCELLED",
  "REJECTED",
  "INACTIVE",
  "EXPIRED",
  "AMBIGUOUS",
  "RECONCILIATION_REQUIRED",
] as const;

export type CanonicalExecutionStatus = typeof CANONICAL_EXECUTION_STATUSES[number];

export const EXECUTION_CONDITIONS = [
  "NONE",
  "WORKING_NO_FILL_YET",
  "PARTIAL_FILL_ACTIVE",
  "BROKER_HELD",
  "TIF_CONDITION_NOT_SATISFIED",
  "STATE_UNKNOWN",
] as const;

export type ExecutionCondition = typeof EXECUTION_CONDITIONS[number];

export const CANCELLATION_CAUSES = [
  "USER_REQUESTED",
  "API_REQUESTED",
  "TWS_REQUESTED",
  "BROKER_CANCELLED",
  "EXCHANGE_CANCELLED",
  "TIF_EXPIRED",
  "PRECAUTION",
  "INVALID_ORDER",
  "PRICE_PROTECTION",
  "SESSION_LOST",
  "UNKNOWN",
] as const;

export const REJECTION_CATEGORIES = [
  "ACCOUNT_PERMISSION",
  "INSUFFICIENT_BUYING_POWER",
  "MARKET_DATA_PERMISSION",
  "ORDER_PRECAUTION",
  "LIMIT_PRICE_OUTSIDE_ALLOWED_RANGE",
  "INVALID_CONTRACT",
  "INVALID_COMBO",
  "UNSUPPORTED_ORDER_TYPE",
  "EXCHANGE_RESTRICTION",
  "ACCOUNT_STATE",
  "SESSION_STATE",
  "DUPLICATE_ORDER",
  "MESSAGE_RATE",
  "TICKER_LIMIT",
  "INVALID_ORDER",
  "INVALID_TICK",
  "INCOMPATIBLE_TIF",
  "SUBMISSION_FAILED",
  "MODIFICATION_FAILED",
  "HALTED_SECURITY",
  "INVALID_SIZE",
  "CANCELLATION",
  "WHAT_IF_UNSUPPORTED",
  "API_TRADING_NOT_ALLOWED",
  "COMBO_GUARANTEE",
  "UNKNOWN_BROKER_REJECTION",
] as const;

export const LIFECYCLE_EVIDENCE_EVENTS = [
  "LOCAL_NOT_TRANSMITTED",
  "SUBMISSION_ATTEMPTED",
  "OPEN_ORDER",
  "OPEN_ORDER_END",
  "ORDER_STATUS",
  "ERROR",
  "EXECUTION",
  "EXECUTION_END",
  "COMMISSION_REPORT",
  "COMPLETED_ORDER",
  "COMPLETED_ORDERS_END",
  "RECOVERY_OBSERVATION",
  "REPRICE_PROPOSAL",
] as const;

export type LifecycleEvidenceEvent = typeof LIFECYCLE_EVIDENCE_EVENTS[number];

export interface CanonicalLifecycleDetail {
  raw_evidence_hash: string;
  raw_broker_status: string | null;
  canonical_execution_status: CanonicalExecutionStatus | null;
  execution_condition: ExecutionCondition | null;
  filled: number | null;
  remaining: number | null;
  average_fill_price: number | null;
  last_fill_price: number | null;
  transmitted_to_broker: boolean | null;
  time_in_force: string | null;
  cancellation_cause: typeof CANCELLATION_CAUSES[number] | null;
  normalized_category: typeof REJECTION_CATEGORIES[number] | null;
}

function optionalFinite(value: unknown, name: string): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`INVALID_BROKER_LIFECYCLE_${name}`);
  }
  return value;
}

function optionalEnum<T extends string>(
  value: unknown,
  allowed: readonly T[],
  name: string,
): T | null {
  if (value === null || value === undefined) return null;
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    throw new Error(`INVALID_BROKER_LIFECYCLE_${name}`);
  }
  return value as T;
}

export function validateLifecycleDetail(
  eventType: LifecycleEvidenceEvent,
  detail: Record<string, unknown>,
): CanonicalLifecycleDetail {
  const rawHash = detail.raw_evidence_hash;
  if (typeof rawHash !== "string" || !/^[a-f0-9]{64}$/.test(rawHash)) {
    throw new Error("INVALID_BROKER_LIFECYCLE_EVIDENCE_HASH");
  }
  const canonical = optionalEnum(
    detail.canonical_execution_status,
    CANONICAL_EXECUTION_STATUSES,
    "STATUS",
  );
  const condition = optionalEnum(detail.execution_condition, EXECUTION_CONDITIONS, "CONDITION");
  const filled = optionalFinite(
    detail.filled ?? detail.cumulative_quantity,
    "FILLED_QUANTITY",
  );
  const remaining = optionalFinite(detail.remaining, "REMAINING_QUANTITY");
  if ((filled !== null && filled < 0) || (remaining !== null && remaining < 0)) {
    throw new Error("INVALID_BROKER_LIFECYCLE_QUANTITY");
  }
  if (eventType === "ORDER_STATUS" && (!canonical || !condition || filled === null || remaining === null)) {
    throw new Error("INVALID_BROKER_ORDER_STATUS_EVIDENCE");
  }
  if (eventType === "EXECUTION" && !canonical) {
    throw new Error("INVALID_BROKER_EXECUTION_EVIDENCE");
  }
  if (eventType === "ERROR") {
    if (!Number.isInteger(detail.broker_error_code) || typeof detail.redacted_broker_message !== "string") {
      throw new Error("INVALID_BROKER_ERROR_EVIDENCE");
    }
    const browserVisible = `${detail.redacted_broker_message}${detail.advanced_rejection_json ?? ""}`;
    if (/\b(?:DU|U|F|DF)\d{4,}\b/i.test(browserVisible)) {
      throw new Error("INVALID_BROKER_ERROR_UNREDACTED_ACCOUNT");
    }
    if (!optionalEnum(detail.normalized_category, REJECTION_CATEGORIES, "REJECTION_CATEGORY")) {
      throw new Error("INVALID_BROKER_ERROR_REJECTION_CATEGORY");
    }
  }
  return {
    raw_evidence_hash: rawHash,
    raw_broker_status: typeof detail.raw_broker_status === "string"
      ? detail.raw_broker_status.slice(0, 80)
      : null,
    canonical_execution_status: canonical,
    execution_condition: condition,
    filled,
    remaining,
    average_fill_price: optionalFinite(detail.average_fill_price, "AVERAGE_FILL_PRICE"),
    last_fill_price: optionalFinite(detail.last_fill_price, "LAST_FILL_PRICE"),
    transmitted_to_broker: typeof detail.transmitted_to_broker === "boolean"
      ? detail.transmitted_to_broker
      : null,
    time_in_force: typeof detail.time_in_force === "string"
      ? detail.time_in_force.slice(0, 12).toUpperCase()
      : null,
    cancellation_cause: optionalEnum(
      detail.cancellation_cause,
      CANCELLATION_CAUSES,
      "CANCELLATION_CAUSE",
    ),
    normalized_category: optionalEnum(
      detail.normalized_category,
      REJECTION_CATEGORIES,
      "REJECTION_CATEGORY",
    ),
  };
}

export function coarseIntentStatus(
  canonical: CanonicalExecutionStatus,
): "CLAIMED" | "BROKER_ACKNOWLEDGED" | "PARTIAL_FILL" | "FILLED" |
  "REJECTED" | "CANCELLED" | "EXPIRED" | "AMBIGUOUS" | "BLOCKED" {
  if (canonical === "CLAIMED") return "CLAIMED";
  if (canonical === "PARTIALLY_FILLED") return "PARTIAL_FILL";
  if (canonical === "FILLED") return "FILLED";
  if (canonical === "REJECTED") return "REJECTED";
  if (["CANCELLED", "API_CANCELLED"].includes(canonical)) return "CANCELLED";
  if (canonical === "EXPIRED") return "EXPIRED";
  if (["AMBIGUOUS", "RECONCILIATION_REQUIRED"].includes(canonical)) return "AMBIGUOUS";
  if (canonical === "LOCAL_NOT_TRANSMITTED") return "BLOCKED";
  return "BROKER_ACKNOWLEDGED";
}

export function evidenceKind(eventType: LifecycleEvidenceEvent): string {
  return eventType;
}
