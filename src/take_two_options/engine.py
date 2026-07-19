"""End-to-end read-only analysis orchestration."""

from __future__ import annotations

from take_two_options.candidates import generate_candidates
from take_two_options.domain import DecisionReport, MarketDataBundle, ModelReadiness
from take_two_options.pricing import analyze_risk
from take_two_options.scenarios import deterministic_scenarios, monte_carlo_scenarios
from take_two_options.scoring import pareto_frontier, rank_candidates, score_candidate
from take_two_options.validation import apply_vetoes, freshness_is_stale
from take_two_options.vol_surface import surface_diagnostics


def analyze_bundle(bundle: MarketDataBundle) -> DecisionReport:
    candidates = generate_candidates(bundle)
    for candidate in candidates:
        analyze_risk(candidate, bundle)
        deterministic_scenarios(candidate, bundle)
        monte_carlo_scenarios(candidate, bundle)
        apply_vetoes(candidate, bundle)
        score_candidate(candidate, bundle)

    data_issues: list[str] = []
    if freshness_is_stale(bundle.underlying.freshness, bundle):
        data_issues.append("Underlying snapshot is not current")
    if any(freshness_is_stale(quote.freshness, bundle) for quote in bundle.option_quotes):
        data_issues.append("At least one option quote is not current")
    if any(not action.handled for action in bundle.underlying.corporate_actions):
        data_issues.append("At least one corporate action is untreated")
    if any(event.critical and not event.handled for event in bundle.underlying.events):
        data_issues.append("At least one critical event is untreated")
    if freshness_is_stale(bundle.fundamental.freshness, bundle):
        data_issues.append("Fundamental snapshot is not current")
    if freshness_is_stale(bundle.portfolio.freshness, bundle):
        data_issues.append("Portfolio cost/margin assumptions are not current")
    if freshness_is_stale(bundle.risk_free_rate_freshness, bundle):
        data_issues.append("Risk-free rate input is not current")
    if freshness_is_stale(bundle.volatility_freshness, bundle):
        data_issues.append("Volatility input is not current")
    if bundle.volatility_surface is not None and freshness_is_stale(
        bundle.volatility_surface.freshness, bundle
    ):
        data_issues.append("Volatility surface is not current")

    diagnostics = surface_diagnostics(bundle)
    model_limitations = [
        "Model outputs are screen-grade until calibrated on source-backed TTWO history",
        "Synthetic fixtures and heuristic thresholds do not constitute out-of-sample evidence",
        "Assignment and pin levels are deterministic flags, not event probabilities",
    ]
    if not diagnostics.available:
        model_limitations.append("No explicit volatility surface is supplied")
    if diagnostics.extrapolated_contracts:
        model_limitations.append("Some contracts require IV extrapolation or fallback")
    if bundle.simulation.jump.calibration_status.value != "calibrated":
        model_limitations.append("Merton jump parameters are not source-backed calibrated")
    if bundle.simulation.heston.calibration_status.value != "calibrated":
        model_limitations.append("Heston parameters are not source-backed calibrated")

    return DecisionReport(
        report_id=f"TTWO-RESEARCH-{bundle.analysis_timestamp.strftime('%Y%m%dT%H%M%SZ')}",
        created_at=bundle.analysis_timestamp,
        bundle=bundle,
        candidates=candidates,
        ranked_candidate_ids=rank_candidates(candidates),
        pareto_candidate_ids=pareto_frontier(candidates),
        global_warnings=[
            "Research output only: not an investment recommendation or order instruction.",
            "Fixture market data is illustrative and must be replaced with timestamped live data.",
            (
                "Scores compare assumptions; they do not authorize execution, sizing, "
                "or risk activation."
            ),
            (
                "American values use QuantLib finite differences; assignment and pin flags "
                "still require human review."
            ),
            "Jump and stochastic-volatility scenarios are model comparisons, not forecasts.",
        ],
        data_issues=data_issues,
        model_readiness=ModelReadiness.SCREEN_GRADE,
        model_limitations=model_limitations,
        surface_diagnostics=diagnostics,
    )
