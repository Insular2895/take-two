"""Decomposed research scoring applied only after veto evaluation."""

from __future__ import annotations

from statistics import fmean

from take_two_options.domain import (
    CandidateStatus,
    ExerciseStyle,
    MarketDataBundle,
    PositionSide,
    RiskLevel,
    ScoreBreakdown,
    StrategyCandidate,
    StrategyKind,
)
from take_two_options.fundamentals import catalyst_coverage, thesis_fit
from take_two_options.pricing import payoff_pnl_at_expiration


def _clamp(value: float) -> float:
    return max(0.0, min(value, 1.0))


def score_candidate(
    candidate: StrategyCandidate, bundle: MarketDataBundle
) -> ScoreBreakdown | None:
    if candidate.status is CandidateStatus.BLOCKED:
        candidate.score = None
        return None
    if candidate.risk_metrics is None or candidate.execution_estimate is None:
        raise ValueError("candidate must be priced and validated before scoring")

    risk = candidate.risk_metrics
    execution = candidate.execution_estimate
    max_loss = risk.max_loss
    expected_pnl = sum(
        scenario.probability * payoff_pnl_at_expiration(candidate, scenario.target_price, execution)
        for scenario in bundle.fundamental.scenarios
    )
    expected_base = max(max_loss or 0.0, abs(execution.total_entry_cost), 1.0)
    expected_payoff = _clamp(0.5 + expected_pnl / (2.0 * expected_base))
    if candidate.kind is StrategyKind.NO_TRADE:
        payoff_quality = 0.70
    elif risk.max_gain is None:
        payoff_quality = 0.80
    elif max_loss in {None, 0}:
        payoff_quality = 1.0
    else:
        assert max_loss is not None
        payoff_quality = _clamp(risk.max_gain / (2.0 * max_loss))

    if max_loss is None:
        max_loss_quality = 0.0
    elif max_loss == 0:
        max_loss_quality = 1.0
    else:
        max_loss_quality = _clamp(bundle.portfolio.max_loss_budget / max_loss)

    scenario_pnls = [scenario.pnl for scenario in candidate.scenarios]
    dispersion = max(scenario_pnls, default=0.0) - min(scenario_pnls, default=0.0)
    sensitivity_base = max(risk.max_loss or 0.0, abs(execution.total_entry_cost), 1.0)
    assumption_sensitivity = _clamp(1.0 - dispersion / (4.0 * sensitivity_base))
    cost_base = max(abs(execution.theoretical_mid), 1.0)
    cost_quality = _clamp(1.0 - (execution.fees + execution.slippage) / cost_base)

    complexity = {
        StrategyKind.NO_TRADE: 1.0,
        StrategyKind.STOCK: 1.0,
        StrategyKind.LONG_CALL: 0.90,
        StrategyKind.LONG_PUT: 0.90,
        StrategyKind.BULL_CALL_SPREAD: 0.70,
        StrategyKind.BEAR_PUT_SPREAD: 0.70,
    }[candidate.kind]
    short_american = any(
        leg.side is PositionSide.SHORT
        and leg.option_quote is not None
        and leg.option_quote.contract.exercise_style is ExerciseStyle.AMERICAN
        for leg in candidate.legs
    )
    risk_levels = {
        risk.assignment_risk for risk in candidate.exercise_risks if risk.side is PositionSide.SHORT
    } | {risk.pin_risk for risk in candidate.exercise_risks if risk.side is PositionSide.SHORT}
    if RiskLevel.HIGH in risk_levels:
        assignment_quality = 0.30
    elif RiskLevel.MEDIUM in risk_levels:
        assignment_quality = 0.55
    else:
        assignment_quality = 0.80 if short_american else 1.0

    implied_volatilities = [
        leg.option_quote.implied_volatility
        for leg in candidate.legs
        if leg.option_quote is not None and leg.option_quote.implied_volatility is not None
    ]
    if implied_volatilities:
        mean_iv = fmean(implied_volatilities)
        iv_rv_context = _clamp(
            1.0
            - abs(mean_iv - bundle.annualized_volatility)
            / max(mean_iv, bundle.annualized_volatility)
        )
    else:
        iv_rv_context = 0.70 if candidate.kind is StrategyKind.NO_TRADE else 1.0

    if bundle.volatility_surface is not None:
        surface_expirations = {node.expiration for node in bundle.volatility_surface.nodes}
        surface_strikes = {node.strike for node in bundle.volatility_surface.nodes}
        skew_term_structure = (
            1.0 if len(surface_expirations) >= 2 and len(surface_strikes) >= 3 else 0.55
        )
    elif not implied_volatilities:
        skew_term_structure = 0.75 if candidate.kind is StrategyKind.NO_TRADE else 1.0
    else:
        expirations = {quote.contract.expiration for quote in bundle.option_quotes}
        skew_term_structure = 1.0 if len(expirations) >= 2 else 0.35

    has_short_option = any(
        leg.instrument_type == "option" and leg.side is PositionSide.SHORT for leg in candidate.legs
    )
    margin_quality = 0.80 if has_short_option and bundle.portfolio.margin_known else 1.0
    carry_base = max(risk.max_loss or 0.0, abs(execution.total_entry_cost), 1.0)
    carry = _clamp(1.0 - max(-risk.net_theta, 0.0) * 30.0 / carry_base)
    worst_scenario = min(scenario_pnls, default=0.0)
    adverse_robustness = _clamp(1.0 + worst_scenario / max(carry_base, 1.0))

    evidence_quality = []
    decision_evidence = [
        *candidate.evidence,
        *bundle.underlying.sources,
        *bundle.fundamental.sources,
        bundle.portfolio.source,
        bundle.risk_free_rate_source,
        bundle.volatility_source,
        *(dividend.source for dividend in bundle.dividends),
    ]
    if bundle.dividend_yield_source is not None:
        decision_evidence.append(bundle.dividend_yield_source)
    if bundle.volatility_surface is not None:
        decision_evidence.append(bundle.volatility_surface.source)
    for item in decision_evidence:
        quality = 1.0 if item.confidence_level == "high" else 0.75
        evidence_quality.append(quality if item.confidence_level != "low" else 0.4)
    data_confidence = fmean(evidence_quality) if evidence_quality else 0.0
    components = {
        "thesis_fit": thesis_fit(candidate, bundle.fundamental),
        "catalyst_coverage": catalyst_coverage(candidate, bundle.fundamental),
        "expected_payoff": expected_payoff,
        "payoff_quality": payoff_quality,
        "max_loss_quality": max_loss_quality,
        "assumption_sensitivity": assumption_sensitivity,
        "liquidity": execution.liquidity_score,
        "cost_quality": cost_quality,
        "complexity": complexity,
        "assignment_early_exercise": assignment_quality,
        "iv_rv_context": iv_rv_context,
        "skew_term_structure": skew_term_structure,
        "margin": margin_quality,
        "carry": carry,
        "adverse_robustness": adverse_robustness,
        "data_confidence": data_confidence,
    }
    total = fmean(components.values())
    breakdown = ScoreBreakdown(
        **{key: round(value, 6) for key, value in components.items()},
        total=round(total, 6),
    )
    candidate.score = breakdown
    return breakdown


def rank_candidates(candidates: list[StrategyCandidate]) -> list[str]:
    scored = [candidate for candidate in candidates if candidate.score is not None]
    return [
        candidate.id
        for candidate in sorted(
            scored,
            key=lambda item: (item.score.total if item.score else 0.0, item.id),
            reverse=True,
        )
    ]


def pareto_frontier(candidates: list[StrategyCandidate]) -> list[str]:
    """Return non-dominated candidates across core risk/reward dimensions."""
    scored = [candidate for candidate in candidates if candidate.score is not None]
    dimensions = (
        "thesis_fit",
        "expected_payoff",
        "payoff_quality",
        "max_loss_quality",
        "liquidity",
        "cost_quality",
        "adverse_robustness",
        "data_confidence",
    )

    def dominates(left: StrategyCandidate, right: StrategyCandidate) -> bool:
        assert left.score is not None and right.score is not None
        left_values = [getattr(left.score, name) for name in dimensions]
        right_values = [getattr(right.score, name) for name in dimensions]
        return all(a >= b for a, b in zip(left_values, right_values, strict=True)) and any(
            a > b for a, b in zip(left_values, right_values, strict=True)
        )

    frontier = [
        candidate
        for candidate in scored
        if not any(dominates(other, candidate) for other in scored if other.id != candidate.id)
    ]
    return [candidate.id for candidate in sorted(frontier, key=lambda item: item.id)]
