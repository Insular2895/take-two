import { describe, expect, it } from "vitest";
import { selectTrackedClosePreview } from "../public/preview-state.js";

describe("close preview browser state", () => {
  it("retains a created preview across the re-authentication refresh", () => {
    const created = { preview_id: "preview-created", status: "CREATED" };

    expect(selectTrackedClosePreview([created])).toBe(created);
  });

  it("prioritizes an actionable preview over a newer created preview", () => {
    const created = { preview_id: "preview-created", status: "CREATED" };
    const acknowledged = { preview_id: "preview-acknowledged", status: "ACKNOWLEDGED" };

    expect(selectTrackedClosePreview([created, acknowledged])).toBe(acknowledged);
  });

  it("drops terminal previews", () => {
    expect(selectTrackedClosePreview([
      { preview_id: "preview-reconciled", status: "RECONCILED" },
    ])).toBeNull();
  });
});
