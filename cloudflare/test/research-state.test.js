import { describe, expect, it } from "vitest";

import {
  filterCandidateUniverse,
  paginateCandidates,
  percentileHeatmap,
  sortCandidates,
} from "../public/research-state.js";

const candidates = [
  { candidate_id: "a", architecture: "spread", engine_rank: 1, capital_required: 900, maximum_loss: 800, paper_eligible: true, research_eligible: true, budget_status: "WITHIN" },
  { candidate_id: "b", architecture: "spread", engine_rank: 2, capital_required: null, maximum_loss: 500, paper_eligible: false, research_eligible: true, budget_status: "BELOW" },
  { candidate_id: "c", architecture: "call", engine_rank: 3, capital_required: 1100, maximum_loss: 1100, paper_eligible: true, research_eligible: true, budget_status: "ABOVE" },
];

describe("research candidate browser state", () => {
  it("keeps engine rank immutable while applying an independent user sort", () => {
    const sorted = sortCandidates(candidates, "maximum_loss");
    expect(sorted.map((item) => item.candidate_id)).toEqual(["b", "a", "c"]);
    expect(candidates.map((item) => item.engine_rank)).toEqual([1, 2, 3]);
  });

  it("places N/A last and gives it a neutral heatmap cell", () => {
    expect(sortCandidates(candidates, "capital_required").at(-1).candidate_id).toBe("b");
    const heatmap = percentileHeatmap(candidates, ["capital_required"], { capital_required: "ASC" });
    expect(heatmap.b.capital_required).toEqual({ percentile: null, tone: "neutral" });
    expect(heatmap.a.capital_required.tone).toBe("strong-good");
  });

  it("recomputes percentiles on the visible post-filter universe", () => {
    const visible = filterCandidateUniverse(candidates, { architectures: ["spread"], view: "all" });
    const heatmap = percentileHeatmap(visible, ["maximum_loss"]);
    expect(Object.keys(heatmap)).toEqual(["a", "b"]);
    expect(heatmap.b.maximum_loss.tone).toBe("strong-good");
  });

  it("paginates without deleting candidates and supports first-class views", () => {
    const page = paginateCandidates(candidates, 2, 2);
    expect(page.items.map((item) => item.candidate_id)).toEqual(["c"]);
    expect(page.total).toBe(3);
    expect(filterCandidateUniverse(candidates, { view: "paper" })).toHaveLength(2);
    expect(filterCandidateUniverse(candidates, { view: "research" }).map((item) => item.candidate_id)).toEqual(["b"]);
    expect(filterCandidateUniverse(candidates, { view: "architecture" })).toHaveLength(2);
  });
});
