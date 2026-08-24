import { describe, expect, it } from "vitest";

import parity from "../../fixtures/cloudflare/monitoring_parity.json";
import { syntheticDemoDossier } from "../src/demo";
import { calculateProjection, estimateDailyUsage, inverseStructureLegs, validateDossier } from "../src/domain";
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
    value.last_imported_snapshot!.timestamp = "2026-08-24T14:00:00.000Z";
    expect(calculateProjection(value, value.last_imported_snapshot!, 2, NOW).monitor_action).toBe("DATA_STALE");
  });

  const expected = Object.fromEntries(parity.cases.map((item) => [item.case_id, item.expected_action]));
  const actionCases: Array<[string, (value: CloudPositionDossier) => void, string]> = [
    ["thesis invalidation", (value) => { value.last_imported_snapshot!.thesis_invalidated = true; }, expected.thesis_invalidation!],
    ["insufficient data", (value) => { value.last_imported_snapshot!.data_sufficient = false; }, expected.insufficient_data!],
    ["profit target", (value) => { value.exit_plan.profit_target = 0.40; }, expected.profit_target!],
    ["stop loss", (value) => { value.actual_entry_cash = 2500; value.exit_plan.operational_stop_loss = 0.30; }, expected.stop_loss!],
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
