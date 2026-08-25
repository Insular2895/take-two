import { describe, expect, it } from "vitest";

import parity from "../../fixtures/cloudflare/monitoring_parity.json";
import { syntheticCreditSpreadDossier, syntheticDemoDossier } from "../src/demo";
import {
  calculateProjection,
  calculateRequiredDataFreshness,
  estimateDailyUsage,
  inverseStructureLegs,
  validateDossier,
} from "../src/domain";
import type { CloudPositionDossier } from "../src/types";

const NOW = new Date("2026-08-24T14:30:30.000Z");

function dossier() {
  return syntheticDemoDossier(new Date("2026-08-24T14:30:00.000Z"));
}

describe("lightweight economic projection", () => {
  it("keeps MTM, liquidation, and canonical expected PnL separate", () => {
    const value = dossier();
    const projection = calculateProjection(value, value.last_imported_snapshot!, 2, NOW);
    expect(projection.market_value_policy).toBeCloseTo(parity.baseline.market_value, 8);
    expect(projection.mtm_pnl).toBeCloseTo(parity.baseline.mtm_pnl, 8);
    expect(projection.liquidation_value).toBeCloseTo(parity.baseline.liquidation_value, 8);
    expect(projection.liquidation_pnl).toBeCloseTo(parity.baseline.liquidation_pnl, 8);
    expect(value.latest_promoted_model_snapshot?.expected_remaining_pnl).toBe(parity.baseline.expected_remaining_pnl);
    expect(projection.liquidation_estimate_mode).toBe("LEGWISE_CONSERVATIVE_ESTIMATE");
    expect(projection.monitor_action).toBe("HOLD");
  });

  it("does not assume unknown FX execution cost is zero", () => {
    const value = dossier();
    value.last_imported_snapshot!.estimated_exit_fx = null;
    value.last_imported_snapshot!.estimated_exit_fx_status = "UNKNOWN";
    const projection = calculateProjection(value, value.last_imported_snapshot!, 2, NOW);
    expect(projection.liquidation_value).toBeNull();
    expect(projection.liquidation_pnl).toBeNull();
  });

  it("marks stale data before evaluating economic exit rules", () => {
    const value = dossier();
    value.last_imported_snapshot!.underlying_timestamp = "2026-08-24T14:00:00.000Z";
    expect(calculateProjection(value, value.last_imported_snapshot!, 2, NOW).monitor_action).toBe("DATA_STALE");
  });

  it("uses the oldest required option timestamp and blocks economic exits first", () => {
    const value = dossier();
    value.exit_plan.profit_target = 0.01;
    value.last_imported_snapshot!.underlying_timestamp = "2026-08-24T14:30:29.000Z";
    value.last_imported_snapshot!.option_quotes[0]!.timestamp = "2026-08-24T14:30:28.000Z";
    value.last_imported_snapshot!.option_quotes[1]!.timestamp = "2026-08-24T14:25:00.000Z";
    const projection = calculateProjection(value, value.last_imported_snapshot!, 2, NOW);
    expect(projection.required_data_freshness.effective_timestamp).toBe("2026-08-24T14:25:00.000Z");
    expect(projection.data_freshness).toBe("STALE");
    expect(projection.monitor_action).toBe("DATA_STALE");
    expect(projection.monitor_reasons).not.toContain("profit_target");
  });

  it("requires fresh FX only when policy conversion is used", () => {
    const value = dossier();
    value.last_imported_snapshot!.fx_timestamp = "2026-08-24T14:20:00.000Z";
    expect(calculateProjection(value, value.last_imported_snapshot!, 2, NOW).data_freshness).toBe("STALE");

    const sameCurrency = syntheticCreditSpreadDossier(new Date("2026-08-24T14:30:00.000Z"));
    sameCurrency.last_imported_snapshot!.fx_timestamp = null;
    expect(calculateProjection(sameCurrency, sameCurrency.last_imported_snapshot!, 1, NOW).data_freshness).toBe("FRESH");
  });

  it("requires combo freshness only when the combo quote is used", () => {
    const value = syntheticCreditSpreadDossier(new Date("2026-08-24T14:30:00.000Z"));
    value.last_imported_snapshot!.combo_quote!.timestamp = "2026-08-24T14:20:00.000Z";
    expect(calculateProjection(value, value.last_imported_snapshot!, 1, NOW).data_freshness).toBe("STALE");
    delete value.last_imported_snapshot!.combo_quote;
    expect(calculateProjection(value, value.last_imported_snapshot!, 1, NOW).data_freshness).toBe("FRESH");
  });

  it("fails closed for future and missing required timestamps", () => {
    const future = dossier();
    future.last_imported_snapshot!.option_quotes[0]!.timestamp = "2026-08-24T14:32:30.000Z";
    const futureProjection = calculateProjection(future, future.last_imported_snapshot!, 2, NOW);
    expect(futureProjection.data_freshness).toBe("INVALID");
    expect(futureProjection.monitor_action).toBe("BLOCKED_INSUFFICIENT_DATA");
    expect(futureProjection.monitor_reasons).toContain("MARKET_TIMESTAMP_FROM_FUTURE");

    const missing = dossier();
    missing.last_imported_snapshot!.option_quotes[1]!.timestamp = null;
    const missingProjection = calculateProjection(missing, missing.last_imported_snapshot!, 2, NOW);
    expect(missingProjection.data_freshness).toBe("INSUFFICIENT_DATA");
    expect(missingProjection.required_data_freshness.effective_timestamp).toBeNull();
    expect(missingProjection.monitor_action).toBe("BLOCKED_INSUFFICIENT_DATA");
  });

  it("tracks an absent required leg as insufficient instead of fresh", () => {
    const value = dossier();
    value.last_imported_snapshot!.option_quotes.pop();
    const freshness = calculateRequiredDataFreshness(
      value,
      value.last_imported_snapshot!,
      "LEGWISE_CONSERVATIVE_ESTIMATE",
      NOW,
    );
    expect(freshness.status).toBe("INSUFFICIENT_DATA");
    expect(freshness.reasons.some((reason) => reason.startsWith("MISSING_OPTION_QUOTE"))).toBe(true);
  });

  it("accounts for debit and credit structures with signed cash flows", () => {
    const debit = dossier();
    const debitProjection = calculateProjection(debit, debit.last_imported_snapshot!, 2, NOW);
    expect(debit.entry_cash_flow_policy).toBe(-1023);
    expect(debit.capital_required_policy).toBe(1023);
    expect(debitProjection.market_value_policy).toBeCloseTo(1487, 8);
    expect(debitProjection.mtm_pnl).toBeCloseTo(464, 8);
    expect(debitProjection.estimated_close_cash_flow_policy).toBeCloseTo(1455, 8);
    expect(debitProjection.liquidation_pnl).toBeCloseTo(432, 8);

    const credit = syntheticCreditSpreadDossier(new Date("2026-08-24T14:30:00.000Z"));
    const creditProjection = calculateProjection(credit, credit.last_imported_snapshot!, 1, NOW);
    expect(credit.entry_cash_flow_policy).toBe(300);
    expect(credit.capital_required_policy).toBe(700);
    expect(creditProjection.market_value_policy).toBeCloseTo(-120, 8);
    expect(creditProjection.mtm_pnl).toBeCloseTo(180, 8);
    expect(creditProjection.estimated_close_cash_flow_policy).toBeCloseTo(-105, 8);
    expect(creditProjection.liquidation_pnl).toBeCloseTo(195, 8);
  });

  const expected = Object.fromEntries(parity.cases.map((item) => [item.case_id, item.expected_action]));
  const actionCases: Array<[string, (value: CloudPositionDossier) => void, string]> = [
    ["thesis invalidation", (value) => { value.last_imported_snapshot!.thesis_invalidated = true; }, expected.thesis_invalidation!],
    ["insufficient data", (value) => { value.last_imported_snapshot!.data_sufficient = false; }, expected.insufficient_data!],
    ["profit target", (value) => { value.exit_plan.profit_target = 0.40; }, expected.profit_target!],
    ["stop loss", (value) => { value.entry_cash_flow_policy = -2500; value.capital_required_policy = 2500; value.exit_plan.operational_stop_loss = 0.30; }, expected.stop_loss!],
    ["time exit", (value) => { value.exit_plan.exit_days_before_expiration = 365; }, expected.time_exit!],
    ["IV crush", (value) => { value.exit_plan.iv_crush_threshold = 0.01; }, expected.iv_crush!],
    ["theta watch", (value) => { value.exit_plan.rules.find((rule) => rule.rule_id === "theta_limit")!.threshold = 0.1; }, expected.theta_threshold!],
  ];

  it.each(actionCases)("matches the canonical action family for %s", (_name, mutate, expected) => {
    const value = dossier();
    mutate(value);
    expect(calculateProjection(value, value.last_imported_snapshot!, 2, NOW).monitor_action).toBe(expected);
  });
});

describe("whole-structure safety", () => {
  it("generates exact inverse combo legs only", () => {
    const legs = inverseStructureLegs(dossier(), 2);
    expect(legs).toHaveLength(2);
    expect(legs.map((leg) => [leg.action, leg.quantity, leg.contract_identity])).toEqual([
      ["SELL_TO_CLOSE", 2, "TTWO  270115C00250000"],
      ["BUY_TO_CLOSE", 2, "TTWO  270115C00300000"],
    ]);
  });

  it("rejects a weakened dossier safety boundary", () => {
    const value = { ...dossier(), transmit: true };
    expect(() => validateDossier(value)).toThrow("unsafe capability flags");
  });

  it("adapts only the proven legacy synthetic debit dossier", () => {
    const current = dossier();
    const {
      entry_cash_flow_policy: _entryCashFlow,
      capital_required_policy: _capitalRequired,
      ...legacyFields
    } = current;
    const legacySnapshot = { ...current.last_imported_snapshot } as Record<string, unknown>;
    delete legacySnapshot.underlying_timestamp;
    const legacy = {
      ...legacyFields,
      schema_version: "1.0",
      actual_entry_cash: 1023,
      last_imported_snapshot: legacySnapshot,
    };
    const adapted = validateDossier(legacy);
    expect(adapted.schema_version).toBe("1.1");
    expect(adapted.entry_cash_flow_policy).toBe(-1023);
    expect(adapted.capital_required_policy).toBe(1023);
    expect(calculateProjection(adapted, adapted.last_imported_snapshot!, 2, NOW).liquidation_pnl).toBeCloseTo(432, 8);

    expect(() => validateDossier({ ...legacy, fixture_status: "CANONICAL_EXPORT" })).toThrow(
      "ENTRY_CASH_FLOW_SIGN_UNPROVEN",
    );
  });
});

describe("free-tier guardrail", () => {
  it("keeps default application estimates below the internal soft budget", () => {
    const estimate = estimateDailyUsage();
    expect(estimate.workerInvocations).toBeLessThan(60_000);
    expect(estimate.internalBudgetStatus).toBe("NORMAL");
    expect(estimate.label).toBe("APPLICATION_ESTIMATE_ONLY");
  });

  it("fails closed for an unsafe configuration", () => {
    expect(estimateDailyUsage(1, 24, 1, 1).internalBudgetStatus).toBe("UNSAFE");
  });
});
