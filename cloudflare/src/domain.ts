import type {
  CloudLeg,
  CloudPositionDossier,
  MonitorAction,
  PnlProjection,
  ProviderSnapshot,
} from "./types";

const SHA256 = /^[a-f0-9]{64}$/;
const GIT_COMMIT = /^[a-f0-9]{7,40}$/;
const CURRENCY = /^[A-Z]{3}$/;

function requireCondition(condition: boolean, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validDate(value: unknown): value is string {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}

export function validateDossier(value: unknown): CloudPositionDossier {
  requireCondition(isRecord(value), "INVALID_DOSSIER: expected an object");
  const dossier = value as unknown as CloudPositionDossier;
  requireCondition(dossier.schema_version === "1.0", "INVALID_DOSSIER: schema_version");
  requireCondition(
    dossier.fixture_status === "CANONICAL_EXPORT" || dossier.fixture_status === "SYNTHETIC_DEMO",
    "INVALID_DOSSIER: fixture_status",
  );
  requireCondition(typeof dossier.position_id === "string" && dossier.position_id.length > 0, "INVALID_DOSSIER: position_id");
  requireCondition(typeof dossier.dossier_id === "string" && dossier.dossier_id.length > 0, "INVALID_DOSSIER: dossier_id");
  requireCondition(validDate(dossier.created_at) && validDate(dossier.opened_at), "INVALID_DOSSIER: timestamps");
  requireCondition(
    ["PLANNED", "PAPER_OPEN", "LIVE_ASSISTED_OPEN"].includes(dossier.initial_position_state),
    "INVALID_DOSSIER: state",
  );
  requireCondition(CURRENCY.test(dossier.entry_native_currency) && CURRENCY.test(dossier.policy_currency), "INVALID_DOSSIER: currency");
  requireCondition(Number.isInteger(dossier.quantity) && dossier.quantity > 0, "INVALID_DOSSIER: quantity");
  requireCondition(Number.isFinite(dossier.multiplier) && dossier.multiplier > 0, "INVALID_DOSSIER: multiplier");
  requireCondition(Number.isFinite(dossier.actual_entry_cash) && dossier.actual_entry_cash > 0, "INVALID_DOSSIER: entry cash");
  requireCondition(Number.isFinite(dossier.initial_spot) && dossier.initial_spot > 0, "INVALID_DOSSIER: initial spot");
  requireCondition(
    dossier.read_only === true && dossier.transmit === false && dossier.what_if === true &&
      dossier.human_confirmation_required === true && dossier.order_capability === "forbidden",
    "INVALID_DOSSIER: unsafe capability flags",
  );
  requireCondition(SHA256.test(dossier.trade_economics_ticket_hash), "INVALID_DOSSIER: ticket hash");
  requireCondition(SHA256.test(dossier.config_hash), "INVALID_DOSSIER: config hash");
  requireCondition(SHA256.test(dossier.market_snapshot_hash), "INVALID_DOSSIER: market hash");
  requireCondition(GIT_COMMIT.test(dossier.git_commit), "INVALID_DOSSIER: git commit");
  requireCondition(Array.isArray(dossier.legs) && dossier.legs.length > 0, "INVALID_DOSSIER: legs");
  const identities = new Set<string>();
  for (const leg of dossier.legs) {
    requireCondition(typeof leg.contract_identity === "string" && leg.contract_identity.length > 0, "INVALID_DOSSIER: leg identity");
    requireCondition(!identities.has(leg.contract_identity), "INVALID_DOSSIER: duplicate leg identity");
    identities.add(leg.contract_identity);
    requireCondition(leg.con_id !== null || Boolean(leg.local_symbol), "INVALID_DOSSIER: missing broker identity");
    requireCondition(Number.isInteger(leg.ratio) && leg.ratio > 0, "INVALID_DOSSIER: leg ratio");
    requireCondition(leg.quantity === leg.ratio * dossier.quantity, "INVALID_DOSSIER: leg quantity");
    requireCondition(leg.multiplier === dossier.multiplier, "INVALID_DOSSIER: leg multiplier");
    requireCondition(validDate(leg.expiration), "INVALID_DOSSIER: expiration");
    requireCondition(
      (leg.side === "LONG" && leg.close_action === "SELL_TO_CLOSE") ||
        (leg.side === "SHORT" && leg.close_action === "BUY_TO_CLOSE"),
      "INVALID_DOSSIER: close direction",
    );
    requireCondition(leg.entry_bid >= 0 && leg.entry_ask >= leg.entry_bid, "INVALID_DOSSIER: entry quote");
  }
  const dossierExpirations = [...new Set(dossier.expirations)].sort();
  const legExpirations = [...new Set(dossier.legs.map((leg) => leg.expiration))].sort();
  requireCondition(JSON.stringify(dossierExpirations) === JSON.stringify(legExpirations), "INVALID_DOSSIER: expiration set");
  return dossier;
}

function quoteMap(snapshot: ProviderSnapshot): Map<string, ProviderSnapshot["option_quotes"][number]> {
  const result = new Map(snapshot.option_quotes.map((quote) => [quote.contract_identity, quote]));
  requireCondition(result.size === snapshot.option_quotes.length, "DUPLICATE_OPTION_QUOTE");
  return result;
}

function evaluateMonitorAction(
  dossier: CloudPositionDossier,
  snapshot: ProviderSnapshot,
  liquidationReturn: number | null,
  mtmReturn: number,
  fresh: boolean,
  now: Date,
  peakLiquidationValue: number | null,
  liquidationValue: number | null,
): { action: MonitorAction; reasons: string[] } {
  if (!snapshot.data_sufficient) return { action: "BLOCKED_INSUFFICIENT_DATA", reasons: ["data_insufficient"] };
  if (!fresh) return { action: "DATA_STALE", reasons: ["data_stale"] };
  if (snapshot.thesis_invalidated) return { action: "THESIS_INVALIDATED", reasons: ["fundamental_invalidation"] };
  const plan = dossier.exit_plan;
  if (plan.status !== "CONFIGURED") return { action: "HOLD", reasons: ["exit_plan_not_configured"] };
  const basisReturn = liquidationReturn ?? mtmReturn;
  if (plan.operational_stop_loss !== null && basisReturn <= -plan.operational_stop_loss) {
    return { action: "EXIT_REVIEW", reasons: ["operational_stop_loss"] };
  }
  const minimumDte = Math.min(...dossier.expirations.map((date) => (Date.parse(date) - now.getTime()) / 86_400_000));
  if (plan.exit_days_before_expiration !== null && minimumDte <= plan.exit_days_before_expiration) {
    return { action: "EXIT_REVIEW", reasons: ["time_exit"] };
  }
  if (plan.profit_target !== null && basisReturn >= plan.profit_target) {
    return { action: "EXIT_REVIEW", reasons: ["profit_target"] };
  }
  if (plan.partial_profit_target !== null && basisReturn >= plan.partial_profit_target) {
    return { action: "REDUCE", reasons: ["partial_profit_target"] };
  }
  const initialIvValues = Object.values(dossier.initial_iv);
  const initialIv = initialIvValues.reduce((sum, value) => sum + value, 0) / Math.max(initialIvValues.length, 1);
  if (plan.iv_crush_threshold !== null && snapshot.current_iv !== null && 1 - snapshot.current_iv / initialIv >= plan.iv_crush_threshold) {
    return { action: "EXIT_REVIEW", reasons: ["iv_crush"] };
  }
  const thetaRule = plan.rules.find((rule) => rule.rule_id === "theta_limit" && typeof rule.threshold === "number");
  if (thetaRule && Math.max(-(snapshot.current_greeks.theta ?? 0), 0) >= Number(thetaRule.threshold)) {
    return { action: thetaRule.suggested_action, reasons: ["theta_limit"] };
  }
  if (
    plan.trailing_drawdown !== null && peakLiquidationValue !== null && liquidationValue !== null &&
    (peakLiquidationValue - liquidationValue) / dossier.actual_entry_cash >= plan.trailing_drawdown
  ) {
    return { action: "EXIT_REVIEW", reasons: ["trailing_drawdown"] };
  }
  return { action: "HOLD", reasons: ["no_configured_trigger"] };
}

export function calculateProjection(
  dossier: CloudPositionDossier,
  snapshot: ProviderSnapshot,
  quantityRemaining = dossier.quantity,
  now = new Date(),
  peakLiquidationValue: number | null = null,
): PnlProjection {
  requireCondition(quantityRemaining > 0 && quantityRemaining <= dossier.quantity, "INVALID_REMAINING_QUANTITY");
  const quotes = quoteMap(snapshot);
  let markNative = 0;
  let liquidationNative = 0;
  for (const leg of dossier.legs) {
    const quote = quotes.get(leg.contract_identity);
    requireCondition(Boolean(quote), `MISSING_OPTION_QUOTE:${leg.contract_identity}`);
    requireCondition(quote!.bid >= 0 && quote!.ask >= quote!.bid, `INVALID_OPTION_QUOTE:${leg.contract_identity}`);
    const contracts = leg.ratio * quantityRemaining;
    const sign = leg.side === "LONG" ? 1 : -1;
    markNative += sign * ((quote!.bid + quote!.ask) / 2) * contracts * leg.multiplier;
    liquidationNative += sign * (leg.side === "LONG" ? quote!.bid : quote!.ask) * contracts * leg.multiplier;
  }
  let mode: PnlProjection["liquidation_estimate_mode"] = "LEGWISE_CONSERVATIVE_ESTIMATE";
  if (snapshot.combo_quote) {
    liquidationNative = snapshot.combo_quote.bid * quantityRemaining * dossier.multiplier;
    mode = "COMBO_QUOTE";
  }
  const sameCurrency = dossier.entry_native_currency === dossier.policy_currency;
  const fxRate = sameCurrency ? 1 : snapshot.fx_rate_to_policy_currency;
  requireCondition(fxRate !== null && fxRate > 0, "FX_RATE_UNAVAILABLE");
  const entryBasis = dossier.actual_entry_cash * (quantityRemaining / dossier.quantity);
  const marketValuePolicy = markNative * fxRate;
  const grossLiquidationPolicy = liquidationNative * fxRate;
  const exitCostsKnown =
    snapshot.estimated_exit_commission !== null &&
    snapshot.estimated_exit_slippage !== null &&
    (sameCurrency || snapshot.estimated_exit_fx_status !== "UNKNOWN") &&
    snapshot.estimated_exit_fx !== null;
  const liquidationValue = exitCostsKnown
    ? grossLiquidationPolicy - snapshot.estimated_exit_commission! - snapshot.estimated_exit_slippage! - snapshot.estimated_exit_fx!
    : null;
  const mtmPnl = marketValuePolicy - entryBasis;
  const liquidationPnl = liquidationValue === null ? null : liquidationValue - entryBasis;
  const ageSeconds = (now.getTime() - Date.parse(snapshot.timestamp)) / 1000;
  const fresh = ageSeconds >= -5 && ageSeconds <= 120;
  const action = evaluateMonitorAction(
    dossier,
    snapshot,
    liquidationPnl === null ? null : liquidationPnl / entryBasis,
    mtmPnl / entryBasis,
    fresh,
    now,
    peakLiquidationValue,
    liquidationValue,
  );
  return {
    timestamp: snapshot.timestamp,
    spot: snapshot.spot,
    market_value_native: markNative,
    market_value_policy: marketValuePolicy,
    mtm_pnl: mtmPnl,
    mtm_return: mtmPnl / entryBasis,
    liquidation_value: liquidationValue,
    liquidation_pnl: liquidationPnl,
    liquidation_return: liquidationPnl === null ? null : liquidationPnl / entryBasis,
    liquidation_estimate_mode: mode,
    estimated_exit_commission: snapshot.estimated_exit_commission,
    estimated_exit_slippage: snapshot.estimated_exit_slippage,
    estimated_exit_fx: snapshot.estimated_exit_fx,
    current_iv: snapshot.current_iv,
    current_greeks: snapshot.current_greeks,
    monitor_action: action.action,
    monitor_reasons: action.reasons,
    data_freshness: fresh ? "FRESH" : "STALE",
    provider: snapshot.provider,
  };
}

export interface CloseLegPreview {
  leg_id: string;
  contract_identity: string;
  con_id: number | null;
  local_symbol: string | null;
  action: "SELL_TO_CLOSE" | "BUY_TO_CLOSE";
  quantity: number;
  ratio: number;
  multiplier: number;
  option_right: "CALL" | "PUT";
  strike: number;
  expiration: string;
}

export function inverseStructureLegs(dossier: CloudPositionDossier, quantity: number): CloseLegPreview[] {
  requireCondition(Number.isInteger(quantity) && quantity > 0 && quantity <= dossier.quantity, "COMBO_CLOSE_PREVIEW_UNAVAILABLE");
  const result = dossier.legs.map((leg: CloudLeg) => ({
    leg_id: leg.leg_id,
    contract_identity: leg.contract_identity,
    con_id: leg.con_id,
    local_symbol: leg.local_symbol,
    action: leg.close_action,
    quantity: leg.ratio * quantity,
    ratio: leg.ratio,
    multiplier: leg.multiplier,
    option_right: leg.option_right,
    strike: leg.strike,
    expiration: leg.expiration,
  }));
  requireCondition(result.length === dossier.legs.length && result.every((leg) => leg.contract_identity), "COMBO_CLOSE_PREVIEW_UNAVAILABLE");
  return result;
}

export interface UsageEstimate {
  label: "APPLICATION_ESTIMATE_ONLY";
  monitorAlarms: number;
  browserApiRequests: number;
  workerInvocations: number;
  externalMarketRequests: number;
  d1SnapshotWrites: number;
  estimatedD1RowsWritten: number;
  internalBudgetStatus: "NORMAL" | "SOFT_WARNING" | "DEGRADE" | "UNSAFE";
}

export function estimateDailyUsage(
  marketIntervalSeconds = 30,
  browserVisibleHours = 8,
  browserPollSeconds = 10,
  snapshotIntervalSeconds = 60,
  marketSessionHours = 6.5,
): UsageEstimate {
  const marketSeconds = marketSessionHours * 3600;
  const offHoursSeconds = (24 - marketSessionHours) * 3600;
  const monitorAlarms = Math.ceil(marketSeconds / marketIntervalSeconds) + Math.ceil(offHoursSeconds / 300);
  const browserApiRequests = Math.ceil(browserVisibleHours * 3600 / browserPollSeconds);
  const workerInvocations = monitorAlarms + browserApiRequests + 100;
  const d1SnapshotWrites = Math.ceil(marketSeconds / Math.max(snapshotIntervalSeconds, marketIntervalSeconds)) + Math.ceil(offHoursSeconds / 300);
  const status = workerInvocations >= 90_000 ? "UNSAFE" : workerInvocations >= 80_000 ? "DEGRADE" : workerInvocations >= 60_000 ? "SOFT_WARNING" : "NORMAL";
  return {
    label: "APPLICATION_ESTIMATE_ONLY",
    monitorAlarms,
    browserApiRequests,
    workerInvocations,
    externalMarketRequests: monitorAlarms * 5,
    d1SnapshotWrites,
    estimatedD1RowsWritten: browserApiRequests + monitorAlarms * 3 + d1SnapshotWrites * 2 + 100,
    internalBudgetStatus: status,
  };
}

export function randomId(prefix: string): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return `${prefix}_${Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}
