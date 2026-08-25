export const METRIC_METADATA = Object.freeze({
  engine_rank: { label: "Engine rank", direction: "LOWER" },
  expected_pnl: { label: "Expected PnL", direction: "HIGHER" },
  expected_return: { label: "Expected return", direction: "HIGHER" },
  maximum_gain: { label: "Maximum profit", direction: "HIGHER" },
  return_on_capital: { label: "Return / capital", direction: "HIGHER" },
  return_on_risk: { label: "Return / risk", direction: "HIGHER" },
  probability_profit: { label: "P(profit)", direction: "HIGHER" },
  probability_loss_25: { label: "P(loss >25%)", direction: "LOWER" },
  probability_loss_50: { label: "P(loss >50%)", direction: "LOWER" },
  probability_loss_70: { label: "P(loss >70%)", direction: "LOWER" },
  capital_required: { label: "Capital required", direction: "NEUTRAL" },
  signed_entry_cash_flow: { label: "Entry cash flow", direction: "NEUTRAL" },
  distance_to_target_budget: { label: "Distance to target", direction: "LOWER" },
  headroom_to_hard_maximum: { label: "Hard-max headroom", direction: "HIGHER" },
  maximum_loss: { label: "Perte max", direction: "LOWER" },
  var_95: { label: "VaR 95", direction: "LOWER" },
  cvar_95: { label: "CVaR 95", direction: "LOWER" },
  risk_on_capital: { label: "Risk / capital", direction: "LOWER" },
  net_theta: { label: "Theta", direction: "HIGHER" },
  theta_per_capital_day: { label: "Theta / capital / day", direction: "HIGHER" },
  flat_spot_7d: { label: "Flat Spot +7d", direction: "HIGHER" },
  flat_spot_30d: { label: "Flat Spot +30d", direction: "HIGHER" },
  flat_spot_60d: { label: "Flat Spot +60d", direction: "HIGHER" },
  flat_spot_90d: { label: "Flat Spot +90d", direction: "HIGHER" },
  dte: { label: "DTE", direction: "NEUTRAL" },
  average_implied_volatility: { label: "IV", direction: "NEUTRAL" },
  maximum_relative_spread: { label: "Bid/ask spread", direction: "LOWER" },
  minimum_open_interest: { label: "Liquidity", direction: "HIGHER" },
  net_delta: { label: "Delta net", direction: "NEUTRAL" },
  net_gamma: { label: "Gamma", direction: "NEUTRAL" },
  net_vega: { label: "Vega", direction: "NEUTRAL" },
  score_opportunity: { label: "Opportunity", direction: "HIGHER" },
  score_risk: { label: "Risk score", direction: "HIGHER" },
  score_evidence: { label: "Evidence", direction: "HIGHER" },
  score_model_agreement: { label: "Model Agreement", direction: "HIGHER" },
  score_execution_quality: { label: "Execution Quality", direction: "HIGHER" },
});

function numeric(value) {
  return typeof value === "number" && Number.isFinite(value);
}

export function filterCandidateUniverse(candidates, filters = {}) {
  const bestByArchitecture = new Map();
  for (const candidate of candidates) {
    const previous = bestByArchitecture.get(candidate.architecture);
    if (!previous || candidate.engine_rank < previous.engine_rank) {
      bestByArchitecture.set(candidate.architecture, candidate);
    }
  }
  return candidates.filter((candidate) => {
    if (filters.search) {
      const haystack = `${candidate.architecture} ${candidate.leg_summary} ${candidate.expiration} ${candidate.candidate_id}`.toLowerCase();
      if (!haystack.includes(filters.search.toLowerCase())) return false;
    }
    if (filters.architectures?.length && !filters.architectures.includes(candidate.architecture)) return false;
    if (filters.budgetStatus && candidate.budget_status !== filters.budgetStatus) return false;
    if (filters.entryType && candidate.entry_cash_flow_type !== filters.entryType) return false;
    if (filters.freshness === "FRESH" && candidate.data_freshness !== "FRESH") return false;
    if (filters.expiryType === "COMMON" && !candidate.common_expiry) return false;
    if (filters.expiryType === "MIXED" && candidate.common_expiry) return false;
    for (const [metric, bounds] of Object.entries(filters.ranges || {})) {
      if (bounds.min === null && bounds.max === null) continue;
      if (!numeric(candidate[metric])) return false;
      if (bounds.min !== null && candidate[metric] < bounds.min) return false;
      if (bounds.max !== null && candidate[metric] > bounds.max) return false;
    }
    if (filters.view === "best" && candidate.engine_rank > 25) return false;
    if (filters.view === "top" && candidate.engine_rank > 100) return false;
    if (filters.view === "architecture" && bestByArchitecture.get(candidate.architecture) !== candidate) return false;
    if (filters.view === "paper" && !candidate.paper_eligible) return false;
    if (filters.view === "research" && (!candidate.research_eligible || candidate.paper_eligible)) return false;
    return true;
  });
}

export function sortCandidates(candidates, metric = "engine_rank", requestedDirection = null) {
  const metadata = METRIC_METADATA[metric] ?? METRIC_METADATA.engine_rank;
  const direction = requestedDirection === "DESC"
    ? -1 : requestedDirection === "ASC" ? 1 : metadata.direction === "HIGHER" ? -1 : 1;
  return candidates.slice().sort((left, right) => {
    const leftValue = left[metric];
    const rightValue = right[metric];
    if (!numeric(leftValue) && !numeric(rightValue)) return left.engine_rank - right.engine_rank;
    if (!numeric(leftValue)) return 1;
    if (!numeric(rightValue)) return -1;
    const compared = (leftValue - rightValue) * direction;
    return compared || left.engine_rank - right.engine_rank;
  });
}

export function percentileHeatmap(candidates, metrics = Object.keys(METRIC_METADATA), directionOverrides = {}) {
  const result = Object.fromEntries(candidates.map((candidate) => [candidate.candidate_id, {}]));
  for (const metric of metrics) {
    const metadata = METRIC_METADATA[metric] ?? { direction: "NEUTRAL" };
    const direction = metadata.direction === "NEUTRAL"
      ? directionOverrides[metric] === "DESC" ? "HIGHER" : directionOverrides[metric] === "ASC" ? "LOWER" : "NEUTRAL"
      : metadata.direction;
    const values = candidates
      .filter((candidate) => numeric(candidate[metric]))
      .map((candidate) => candidate[metric])
      .sort((left, right) => left - right);
    for (const candidate of candidates) {
      const value = candidate[metric];
      if (!numeric(value) || direction === "NEUTRAL") {
        result[candidate.candidate_id][metric] = { percentile: null, tone: "neutral" };
        continue;
      }
      const below = values.filter((item) => item < value).length;
      const equal = values.filter((item) => item === value).length;
      const raw = values.length <= 1 ? 0.5 : (below + (equal - 1) / 2) / (values.length - 1);
      const percentile = direction === "LOWER" ? 1 - raw : raw;
      result[candidate.candidate_id][metric] = {
        percentile,
        tone: percentile >= 0.90 ? "strong-good" : percentile >= 0.70 ? "good"
          : percentile >= 0.50 ? "light-good" : percentile >= 0.35 ? "middle"
            : percentile >= 0.20 ? "weak" : "bad",
      };
    }
  }
  return result;
}

export function paginateCandidates(candidates, page = 1, pageSize = 20) {
  const size = Math.max(1, Math.floor(pageSize));
  const pages = Math.max(1, Math.ceil(candidates.length / size));
  const selectedPage = Math.min(Math.max(1, Math.floor(page)), pages);
  return {
    items: candidates.slice((selectedPage - 1) * size, selectedPage * size),
    page: selectedPage,
    pages,
    total: candidates.length,
  };
}
