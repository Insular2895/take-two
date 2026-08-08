"""Pathwise multi-model strategy valuation and exit-policy evaluation."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from statistics import fmean

from take_two_options.domain import OptionType
from take_two_options.intelligence._numpy import NDArray, np
from take_two_options.intelligence.schemas import (
    CandidateExitPlan,
    CandidateRobustness,
    ExitPolicyConfig,
    ExitRuleDefinition,
    MonitorAction,
    SimulationRegime,
    StrategyModelMetrics,
)
from take_two_options.intelligence.stochastic import StochasticPathSet
from take_two_options.quantitative.contracts import DEFAULT_QUANT_CONVENTIONS
from take_two_options.thesis_scanner.schemas import ThesisCandidate, ThesisScanReport


@dataclass(frozen=True)
class StrategyPathValuation:
    candidate_id: str
    model_key: str
    pnl_usd: NDArray
    exit_days: NDArray
    metrics: StrategyModelMetrics


def _normal_cdf(values: NDArray) -> NDArray:
    """Fast vectorized normal CDF approximation with sub-basis-point accuracy."""
    absolute = np.abs(values)
    t = 1.0 / (1.0 + 0.2316419 * absolute)
    density = np.exp(-0.5 * absolute**2) / math.sqrt(2 * math.pi)
    polynomial = t * (
        0.319381530
        + t
        * (
            -0.356563782
            + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))
        )
    )
    positive = 1.0 - density * polynomial
    return np.where(values >= 0, positive, 1.0 - positive)


def _black_scholes(
    *,
    spot: NDArray,
    strike: float,
    time_years: float,
    volatility: NDArray,
    rate: float,
    dividend_yield: float,
    option_type: OptionType,
) -> NDArray:
    if time_years <= 0:
        return (
            np.maximum(spot - strike, 0.0)
            if option_type is OptionType.CALL
            else np.maximum(strike - spot, 0.0)
        )
    safe_spot = np.maximum(spot, 1e-12)
    safe_volatility = np.maximum(volatility, 1e-6)
    root_time = math.sqrt(time_years)
    d1 = (
        np.log(safe_spot / strike)
        + (rate - dividend_yield + 0.5 * safe_volatility**2) * time_years
    ) / (safe_volatility * root_time)
    d2 = d1 - safe_volatility * root_time
    if option_type is OptionType.CALL:
        return safe_spot * math.exp(-dividend_yield * time_years) * _normal_cdf(
            d1
        ) - strike * math.exp(-rate * time_years) * _normal_cdf(d2)
    return strike * math.exp(-rate * time_years) * _normal_cdf(
        -d2
    ) - safe_spot * math.exp(-dividend_yield * time_years) * _normal_cdf(-d1)


def generate_exit_plan(
    candidate: ThesisCandidate,
    *,
    policy: ExitPolicyConfig,
) -> CandidateExitPlan:
    return CandidateExitPlan(
        candidate_id=candidate.candidate_id,
        profit_target=policy.profit_target,
        partial_profit_target=policy.partial_profit_target,
        operational_stop_loss=policy.operational_stop_loss,
        exit_days_before_expiration=policy.exit_days_before_expiration,
        iv_crush_threshold=policy.iv_crush_threshold,
        trailing_drawdown=policy.trailing_drawdown,
        fundamental_invalidations=list(candidate.invalidation_conditions),
        temporal_invalidation=(
            f"Review/exit at {policy.exit_days_before_expiration} calendar days "
            "before expiration unless an explicitly approved roll supersedes it."
        ),
        iv_invalidation=(
            f"Human exit review if modeled IV falls by at least "
            f"{policy.iv_crush_threshold:.0%} from entry."
        ),
        catalyst_rule=(
            "Review immediately before and after the catalyst; no automatic hold-through."
        ),
        trailing_rule=(
            f"After the partial-profit threshold, review an exit after a "
            f"{policy.trailing_drawdown:.0%} drawdown from peak modeled value."
        ),
        rules=[
            ExitRuleDefinition(
                rule_id="profit_target",
                description="Review a complete exit after the configured return target.",
                threshold=policy.profit_target,
                severity="warning",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["prudent_liquidation_value", "actual_cost"],
            ),
            ExitRuleDefinition(
                rule_id="partial_profit_target",
                description="Review a partial reduction after the configured return target.",
                threshold=policy.partial_profit_target,
                severity="warning",
                suggested_action=MonitorAction.REDUCE,
                required_data=["prudent_liquidation_value", "actual_cost"],
            ),
            ExitRuleDefinition(
                rule_id="operational_stop_loss",
                description="Operational maximum loss review; not an automatic stop order.",
                threshold=policy.operational_stop_loss,
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["prudent_liquidation_value", "actual_cost"],
            ),
            ExitRuleDefinition(
                rule_id="fundamental_invalidation",
                description="A preserved thesis invalidation condition became true.",
                threshold=True,
                severity="critical",
                suggested_action=MonitorAction.THESIS_INVALIDATED,
                required_data=["thesis_review"],
            ),
            ExitRuleDefinition(
                rule_id="time_exit",
                description="Review exit before expiration.",
                threshold=policy.exit_days_before_expiration,
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["days_to_expiration"],
            ),
            ExitRuleDefinition(
                rule_id="iv_crush",
                description="Review reduction after an implied-volatility crush.",
                threshold=policy.iv_crush_threshold,
                severity="warning",
                suggested_action=MonitorAction.REDUCE,
                required_data=["entry_iv", "current_iv"],
            ),
            ExitRuleDefinition(
                rule_id="liquidity_deterioration",
                description="Review exit when liquidity falls below policy.",
                threshold=policy.minimum_liquidity_score,
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["liquidity_score", "bid_ask"],
            ),
            ExitRuleDefinition(
                rule_id="expected_value_negative",
                description="Review exit if expected remaining P&L becomes negative.",
                threshold=0.0,
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["expected_remaining_pnl"],
            ),
            ExitRuleDefinition(
                rule_id="cvar_limit",
                description="Review exit if remaining CVaR breaches policy.",
                threshold=policy.maximum_cvar_fraction,
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["remaining_cvar_95", "actual_cost"],
            ),
            ExitRuleDefinition(
                rule_id="data_insufficient",
                description="Block monitoring decisions when required data is missing.",
                threshold=True,
                severity="critical",
                suggested_action=MonitorAction.BLOCKED_INSUFFICIENT_DATA,
                required_data=["quotes", "greeks", "probabilities", "liquidity"],
            ),
            ExitRuleDefinition(
                rule_id="data_stale",
                description="Block a fresh decision when the snapshot is stale.",
                threshold=False,
                severity="critical",
                suggested_action=MonitorAction.DATA_STALE,
                required_data=["snapshot_timestamp"],
            ),
            ExitRuleDefinition(
                rule_id="trailing_drawdown",
                description="Review exit after drawdown from prudent liquidation peak.",
                threshold=policy.trailing_drawdown,
                severity="warning",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=[
                    "peak_prudent_liquidation_value",
                    "prudent_liquidation_value",
                    "actual_cost",
                ],
            ),
            ExitRuleDefinition(
                rule_id="temporal_invalidation",
                description="Review exit when the preserved thesis horizon expires.",
                threshold="dossier_horizon_days",
                severity="critical",
                suggested_action=MonitorAction.EXIT_REVIEW,
                required_data=["opened_at", "horizon_days"],
            ),
            *(
                [
                    ExitRuleDefinition(
                        rule_id="theta_limit",
                        description="Review exit when daily theta loss exceeds policy.",
                        threshold=policy.maximum_theta_loss_per_day_usd,
                        severity="warning",
                        suggested_action=MonitorAction.REDUCE,
                        required_data=["current_greeks.theta"],
                    )
                ]
                if policy.maximum_theta_loss_per_day_usd is not None
                else []
            ),
            *(
                [
                    ExitRuleDefinition(
                        rule_id="exit_before_catalyst",
                        description="Review exit inside the pre-catalyst window.",
                        threshold=policy.exit_before_catalyst_days,
                        severity="warning",
                        suggested_action=MonitorAction.EXIT_REVIEW,
                        required_data=["catalyst_date", "snapshot_timestamp"],
                    )
                ]
                if policy.exit_before_catalyst_days is not None
                else []
            ),
            *(
                [
                    ExitRuleDefinition(
                        rule_id="exit_after_catalyst",
                        description="Review exit after the post-catalyst holding window.",
                        threshold=policy.exit_after_catalyst_days,
                        severity="warning",
                        suggested_action=MonitorAction.EXIT_REVIEW,
                        required_data=["catalyst_date", "snapshot_timestamp"],
                    )
                ]
                if policy.exit_after_catalyst_days is not None
                else []
            ),
        ],
    )


def _position_values(
    candidate: ThesisCandidate,
    path_set: StochasticPathSet,
    *,
    horizon_days: int,
    rate: float,
    dividend_yield: float,
) -> tuple[NDArray, NDArray]:
    steps = path_set.spots.shape[1] - 1
    day_grid = np.linspace(0.0, horizon_days, steps + 1)
    values = np.zeros_like(path_set.spots)
    for step, day in enumerate(day_grid):
        remaining_days = max(candidate.dte - day, 0.0)
        volatility = np.sqrt(np.maximum(path_set.variances[:, step], 1e-12))
        for leg in candidate.base_candidate.legs:
            option_value = _black_scholes(
                spot=path_set.spots[:, step],
                strike=leg.quote.strike,
                time_years=remaining_days / DEFAULT_QUANT_CONVENTIONS.calendar_day_basis,
                volatility=volatility,
                rate=rate,
                dividend_yield=dividend_yield,
                option_type=leg.quote.option_type,
            )
            values[:, step] += (
                leg.side.sign * leg.quantity * leg.quote.multiplier * option_value
            )
    return values, day_grid


def _empirical_metrics(
    candidate: ThesisCandidate,
    path_set: StochasticPathSet,
    *,
    values: NDArray,
    day_grid: NDArray,
    exit_policy: ExitPolicyConfig,
) -> StrategyPathValuation:
    cost = candidate.execution.total_cost_usd
    if cost <= 0:
        raise ValueError("candidate total cost must be positive")
    pnl_paths = values - cost
    initial_volatility = np.sqrt(np.maximum(path_set.variances[:, 0], 1e-12))
    volatility_paths = np.sqrt(np.maximum(path_set.variances, 1e-12))
    paths, steps_plus_one = pnl_paths.shape
    realized = np.empty(paths, dtype=float)
    exit_days = np.empty(paths, dtype=float)
    reasons: Counter[str] = Counter()
    days_to_profit: list[float] = []
    maximum_drawdown = 0.0
    for path in range(paths):
        path_values = values[path]
        running_peak = np.maximum.accumulate(path_values)
        maximum_drawdown = max(
            maximum_drawdown,
            float(np.max(np.maximum(running_peak - path_values, 0.0))),
        )
        profitable = np.flatnonzero(pnl_paths[path] > 0)
        if profitable.size:
            days_to_profit.append(float(day_grid[int(profitable[0])]))
        selected_step = steps_plus_one - 1
        selected_reason = "horizon"
        peak_pnl = -float("inf")
        for step in range(1, steps_plus_one):
            pnl = float(pnl_paths[path, step])
            peak_pnl = max(peak_pnl, pnl)
            days_to_expiration = max(candidate.dte - float(day_grid[step]), 0.0)
            iv_drop = 1.0 - (
                float(volatility_paths[path, step]) / float(initial_volatility[path])
            )
            if pnl >= exit_policy.profit_target * cost:
                selected_step = step
                selected_reason = "profit_target"
                break
            if pnl <= -exit_policy.operational_stop_loss * cost:
                selected_step = step
                selected_reason = "operational_stop"
                break
            if (
                peak_pnl >= exit_policy.partial_profit_target * cost
                and peak_pnl - pnl >= exit_policy.trailing_drawdown * cost
            ):
                selected_step = step
                selected_reason = "trailing_review"
                break
            if iv_drop >= exit_policy.iv_crush_threshold:
                selected_step = step
                selected_reason = "iv_crush_review"
                break
            if days_to_expiration <= exit_policy.exit_days_before_expiration:
                selected_step = step
                selected_reason = "time_exit"
                break
        realized[path] = pnl_paths[path, selected_step]
        exit_days[path] = day_grid[selected_step]
        reasons[selected_reason] += 1
    lower = float(np.quantile(realized, 0.05))
    upper = float(np.quantile(realized, 0.95))
    tail = realized[realized <= lower]
    var_95 = max(0.0, -lower)
    cvar_95 = max(0.0, -float(np.mean(tail))) if tail.size else var_95
    standard_error = (
        float(np.std(realized, ddof=1)) / math.sqrt(paths)
        if paths > 1
        else 0.0
    )
    half = max(paths // 2, 1)
    half_mean = float(np.mean(realized[:half]))
    full_mean = float(np.mean(realized))
    convergence_delta = abs(half_mean - full_mean) / max(cost, 1e-9)
    convergence_status = "converged" if convergence_delta <= 0.10 else "unstable"
    horizon = float(day_grid[-1])
    warnings = list(path_set.warnings)
    if convergence_status == "unstable":
        warnings.append(
            "Monte-Carlo mean changed by more than 10% of entry cost between "
            "the first-half and full sample."
        )
    metrics = StrategyModelMetrics(
        candidate_id=candidate.candidate_id,
        model=path_set.model,
        regime=path_set.regime,
        paths=paths,
        seed=path_set.seed,
        steps=steps_plus_one - 1,
        expected_pnl_usd=full_mean,
        median_pnl_usd=float(np.median(realized)),
        standard_error_usd=standard_error,
        confidence_interval_95_low_usd=full_mean - 1.96 * standard_error,
        confidence_interval_95_high_usd=full_mean + 1.96 * standard_error,
        convergence_status=convergence_status,
        convergence_delta_fraction=convergence_delta,
        model_valid=bool(np.isfinite(realized).all()),
        calibration_status=(
            "partial"
            if path_set.model.value == "local_volatility"
            else "illustrative"
        ),
        probability_profit=float(np.mean(realized > 0)),
        probability_total_loss=float(np.mean(realized <= -0.95 * cost)),
        probability_x2=float(np.mean(realized >= cost)),
        probability_x3=float(np.mean(realized >= 2 * cost)),
        probability_x5=float(np.mean(realized >= 4 * cost)),
        var_95_usd=var_95,
        cvar_95_usd=cvar_95,
        maximum_drawdown_usd=maximum_drawdown,
        reasonable_worst_pnl_usd=lower,
        reasonable_best_pnl_usd=upper,
        mean_days_to_profit=fmean(days_to_profit) if days_to_profit else None,
        probability_exit_before_horizon=float(np.mean(exit_days < horizon)),
        exit_reasons=dict(reasons),
        warnings=warnings,
    )
    return StrategyPathValuation(
        candidate_id=candidate.candidate_id,
        model_key=f"{path_set.model.value}:{path_set.regime.value}",
        pnl_usd=realized,
        exit_days=exit_days,
        metrics=metrics,
    )


def value_candidate_across_models(
    candidate: ThesisCandidate,
    path_sets: list[StochasticPathSet],
    *,
    horizon_days: int,
    rate: float,
    dividend_yield: float,
    exit_policy: ExitPolicyConfig,
) -> list[StrategyPathValuation]:
    valuations: list[StrategyPathValuation] = []
    for path_set in path_sets:
        values, day_grid = _position_values(
            candidate,
            path_set,
            horizon_days=horizon_days,
            rate=rate,
            dividend_yield=dividend_yield,
        )
        valuations.append(
            _empirical_metrics(
                candidate,
                path_set,
                values=values,
                day_grid=day_grid,
                exit_policy=exit_policy,
            )
        )
    return valuations


def summarize_robustness(
    candidate: ThesisCandidate,
    valuations: list[StrategyPathValuation],
) -> CandidateRobustness:
    if not valuations:
        raise ValueError("robustness requires model valuations")
    expectations = [item.metrics.expected_pnl_usd for item in valuations]
    probability_profits = [item.metrics.probability_profit for item in valuations]
    cvars = [item.metrics.cvar_95_usd for item in valuations]
    neutral = [
        item.metrics.expected_pnl_usd
        for item in valuations
        if item.metrics.regime is SimulationRegime.NEUTRAL
    ]
    adverse_cvars = [
        item.metrics.cvar_95_usd
        for item in valuations
        if item.metrics.regime in {SimulationRegime.ADVERSE, SimulationRegime.RUPTURE}
    ]
    profitable_fraction = sum(value > 0 for value in expectations) / len(expectations)
    dispersion = max(neutral) - min(neutral) if len(neutral) > 1 else 0.0
    cost = max(candidate.execution.total_cost_usd, 1e-9)
    dispersion_penalty = min(dispersion / cost, 1.0)
    adverse_penalty = min(max(adverse_cvars, default=0.0) / cost, 1.0)
    score = 100 * max(
        0.0,
        profitable_fraction * 0.65
        + (1 - dispersion_penalty) * 0.20
        + (1 - adverse_penalty) * 0.15,
    )
    flags: list[str] = []
    invalid_models = sum(not item.metrics.model_valid for item in valuations)
    if profitable_fraction < 0.5:
        flags.append("Fewer than half of model/regime combinations have positive expectation.")
    if dispersion > cost * 0.5:
        flags.append("Neutral model expectation dispersion exceeds 50% of entry cost.")
    if max(adverse_cvars, default=0.0) > cost * 0.8:
        flags.append("Adverse CVaR exceeds 80% of entry cost.")
    if invalid_models:
        flags.append(f"{invalid_models} model/regime result(s) are numerically invalid.")
    expected_dispersion = max(expectations) - min(expectations)
    probability_dispersion = max(probability_profits) - min(probability_profits)
    cvar_dispersion = max(cvars) - min(cvars)
    verdict = (
        "data_insufficient"
        if all(item.metrics.calibration_status != "calibrated" for item in valuations)
        else "model_dependent"
        if probability_dispersion > 0.25 or expected_dispersion > cost
        else "fragile"
        if profitable_fraction < 0.5 or max(adverse_cvars, default=0.0) > cost * 0.8
        else "conditionally_robust"
        if flags
        else "robust"
    )
    return CandidateRobustness(
        candidate_id=candidate.candidate_id,
        profitable_model_fraction=profitable_fraction,
        worst_expected_pnl_usd=min(expectations),
        neutral_model_dispersion_usd=dispersion,
        adverse_cvar_usd=max(adverse_cvars, default=0.0),
        probability_profit_dispersion=probability_dispersion,
        expected_pnl_dispersion_usd=expected_dispersion,
        cvar_dispersion_usd=cvar_dispersion,
        invalid_model_count=invalid_models,
        robustness_score=score,
        verdict=verdict,
        model_risk_flags=flags,
    )


def select_candidate_pool(report: ThesisScanReport, maximum: int) -> list[ThesisCandidate]:
    """Use independent V10 rankings to form a bounded, deduplicated valuation pool."""
    candidates = {item.candidate_id: item for item in report.candidates}
    ordered_ids: list[str] = []
    rank_lists = [ranking.scores for ranking in report.rankings]
    depth = 0
    while len(ordered_ids) < maximum and any(depth < len(items) for items in rank_lists):
        for scores in rank_lists:
            if depth >= len(scores):
                continue
            candidate_id = scores[depth].candidate_id
            if candidate_id not in ordered_ids:
                ordered_ids.append(candidate_id)
                if len(ordered_ids) >= maximum:
                    break
        depth += 1
    return [candidates[candidate_id] for candidate_id in ordered_ids if candidate_id in candidates]
