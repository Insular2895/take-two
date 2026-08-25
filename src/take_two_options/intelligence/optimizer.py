"""Exact integer allocation under budget, loss, liquidity, and contract constraints."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from take_two_options.intelligence._numpy import NDArray, np
from take_two_options.intelligence.schemas import (
    AllocationLine,
    AllocationResult,
    ContinuousDiagnostics,
    OptimizerProfileConfig,
    SimulationRegime,
)
from take_two_options.intelligence.valuation import StrategyPathValuation
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.optimization.allocation_pareto import (
    AllocationObjectiveKind,
    AllocationOptimizationReport,
    AllocationParetoPoint,
    OptimizationObjectiveContract,
    allocation_pareto_frontier,
    evaluate_scalar_objective,
)
from take_two_options.thesis_scanner.schemas import ThesisCandidate


@dataclass(frozen=True)
class _ScoredAllocation:
    counts: tuple[int, ...]
    cost_eur: float
    maximum_loss_eur: float
    expected_usd: float
    worst_case_expected_usd: float
    volatility_usd: float
    cvar_usd: float
    execution_risk_usd: float
    model_dispersion_usd: float
    objective: float


def _integer_vectors(
    contract_counts: list[int],
    *,
    maximum_contracts: int,
) -> Iterable[tuple[int, ...]]:
    current = [0] * len(contract_counts)

    def visit(index: int, contracts_used: int) -> Iterable[tuple[int, ...]]:
        if index == len(contract_counts):
            yield tuple(current)
            return
        per_unit = contract_counts[index]
        maximum_units = (maximum_contracts - contracts_used) // per_unit
        for units in range(maximum_units + 1):
            current[index] = units
            yield from visit(index + 1, contracts_used + units * per_unit)
        current[index] = 0

    yield from visit(0, 0)


def _tail_loss(values: NDArray) -> float:
    threshold = float(np.quantile(values, 0.05))
    tail = values[values <= threshold]
    return max(0.0, -float(np.mean(tail))) if tail.size else max(0.0, -threshold)


def _group_weights(
    valuations: list[StrategyPathValuation],
    regime_weights: dict[SimulationRegime, float],
) -> dict[str, float]:
    models_by_regime: dict[SimulationRegime, set[str]] = {}
    for valuation in valuations:
        metrics = valuation.metrics
        models_by_regime.setdefault(metrics.regime, set()).add(metrics.model.value)
    return {
        valuation.model_key: regime_weights.get(valuation.metrics.regime, 0.0)
        / max(len(models_by_regime[valuation.metrics.regime]), 1)
        for valuation in valuations
    }


def _continuous_diagnostics(
    *,
    counts: tuple[int, ...],
    candidates: list[ThesisCandidate],
    valuations: dict[str, list[StrategyPathValuation]],
    weights: dict[str, float],
    risk_aversion: float,
    budget_usd: float,
) -> ContinuousDiagnostics:
    expected = np.asarray(
        [
            sum(
                weights[item.model_key] * float(np.mean(item.pnl_usd))
                for item in valuations[candidate.candidate_id]
            )
            for candidate in candidates
        ],
        dtype=float,
    )
    covariance = np.zeros((len(candidates), len(candidates)), dtype=float)
    for model_key, weight in weights.items():
        matrix = np.column_stack(
            [
                next(
                    item.pnl_usd
                    for item in valuations[candidate.candidate_id]
                    if item.model_key == model_key
                )
                for candidate in candidates
            ]
        )
        if matrix.shape[0] > 1:
            covariance += weight * np.asarray(np.cov(matrix, rowvar=False), dtype=float)
    if covariance.ndim == 0:
        covariance = np.asarray([[float(covariance)]])
    x = np.asarray(counts, dtype=float)
    gradient = expected / budget_usd - (2 * risk_aversion * covariance @ x / budget_usd**2)
    hessian = -2 * risk_aversion * covariance / budget_usd**2
    eigenvalues = np.linalg.eigvalsh((hessian + hessian.T) / 2)
    return ContinuousDiagnostics(
        gradient=gradient.tolist(),
        hessian=hessian.tolist(),
        hessian_eigenvalues=eigenvalues.tolist(),
        concave_quadratic_component=bool(np.all(eigenvalues <= 1e-10)),
        notes=[
            "Candidate order: " + ", ".join(item.candidate_id for item in candidates),
            "Gradient/Hessian cover the smooth mean-variance surrogate only.",
            "CVaR, execution penalties, and integer constraints are handled by exact enumeration.",
        ],
    )


def optimize_allocations_with_frontier(
    *,
    candidates: list[ThesisCandidate],
    valuations: dict[str, list[StrategyPathValuation]],
    regime_weights: dict[SimulationRegime, float],
    profile_name: str,
    profile: OptimizerProfileConfig,
    budget_eur: float,
    maximum_loss_eur: float,
    maximum_contracts: int,
    eur_usd_rate: float,
    maximum_positions: int = 4,
    maximum_concentration: float = 1.0,
    minimum_liquidity_score: float = 0.0,
    maximum_relative_spread: float = 1.0,
    delta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    gamma_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    vega_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    theta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    allow_multiple_strategies: bool = True,
    objective_contract: OptimizationObjectiveContract | None = None,
) -> AllocationOptimizationReport:
    """Enumerate the finite integer set; retaining cash and no-trade are explicit choices."""
    if not candidates:
        raise ValueError("allocation optimization requires candidates")
    if set(valuations) != {candidate.candidate_id for candidate in candidates}:
        raise ValueError("every optimization candidate requires valuations")
    reference_valuations = valuations[candidates[0].candidate_id]
    weights = _group_weights(reference_valuations, regime_weights)
    if abs(sum(weights.values()) - 1.0) > 1e-8:
        raise ValueError("regime/model weights must sum to one")
    model_keys = set(weights)
    for candidate in candidates:
        if {item.model_key for item in valuations[candidate.candidate_id]} != model_keys:
            raise ValueError("candidate path valuation groups must align exactly")
    contract_counts = [
        sum(leg.quantity for leg in candidate.base_candidate.legs) for candidate in candidates
    ]
    costs_eur = [candidate.execution.total_cost_eur for candidate in candidates]
    losses_eur = [candidate.maximum_loss_eur for candidate in candidates]
    execution_risk_usd = [
        candidate.decision_metrics.maximum_leg_relative_spread * candidate.execution.total_cost_usd
        for candidate in candidates
    ]
    budget_usd = budget_eur * eur_usd_rate
    objective_contract = objective_contract or OptimizationObjectiveContract(
        objective_id=f"{profile_name}-weighted-mean-risk",
        kind=AllocationObjectiveKind.WEIGHTED_MEAN_RISK,
        risk_aversion=profile.risk_aversion,
        cvar_aversion=profile.cvar_aversion,
        execution_penalty=profile.execution_penalty,
        model_risk_penalty=profile.model_risk_penalty,
        regime_weight_semantics="configured_heuristic_sensitivity",
    )
    scored: list[_ScoredAllocation] = []
    for counts in _integer_vectors(contract_counts, maximum_contracts=maximum_contracts):
        is_cash = not any(counts)
        cost_eur = sum(count * cost for count, cost in zip(counts, costs_eur, strict=True))
        loss_eur = sum(count * loss for count, loss in zip(counts, losses_eur, strict=True))
        if cost_eur > budget_eur + 1e-9 or loss_eur > maximum_loss_eur + 1e-9:
            continue
        selected_positions = sum(count > 0 for count in counts)
        if selected_positions > maximum_positions:
            continue
        if not allow_multiple_strategies and selected_positions > 1:
            continue
        if cost_eur > 0 and any(
            count * cost / cost_eur > maximum_concentration + 1e-9
            for count, cost in zip(counts, costs_eur, strict=True)
            if count > 0
        ):
            continue
        selected_candidates = [
            candidate for count, candidate in zip(counts, candidates, strict=True) if count > 0
        ]
        if any(
            candidate.decision_metrics.maximum_leg_relative_spread > maximum_relative_spread + 1e-12
            for candidate in selected_candidates
        ):
            continue
        liquidity_scores = [
            max(
                0.0,
                1.0
                - candidate.decision_metrics.maximum_leg_relative_spread
                / max(maximum_relative_spread, 1e-12),
            )
            for candidate in selected_candidates
        ]
        if any(score + 1e-12 < minimum_liquidity_score for score in liquidity_scores):
            continue
        exposures = {
            "delta": sum(
                count * candidate.net_greeks.delta
                for count, candidate in zip(counts, candidates, strict=True)
            ),
            "gamma": sum(
                count * candidate.net_greeks.gamma
                for count, candidate in zip(counts, candidates, strict=True)
            ),
            "vega": sum(
                count * candidate.net_greeks.vega
                for count, candidate in zip(counts, candidates, strict=True)
            ),
            "theta": sum(
                count * candidate.net_greeks.theta
                for count, candidate in zip(counts, candidates, strict=True)
            ),
        }
        exposure_ranges = {
            "delta": delta_exposure_range,
            "gamma": gamma_exposure_range,
            "vega": vega_exposure_range,
            "theta": theta_exposure_range,
        }
        if not is_cash and any(
            value < exposure_ranges[name][0] - 1e-12 or value > exposure_ranges[name][1] + 1e-12
            for name, value in exposures.items()
        ):
            continue
        group_pnls: dict[str, NDArray] = {}
        for model_key in model_keys:
            combined = sum(
                (
                    count
                    * next(
                        item.pnl_usd
                        for item in valuations[candidate.candidate_id]
                        if item.model_key == model_key
                    )
                    for count, candidate in zip(counts, candidates, strict=True)
                ),
                np.zeros_like(reference_valuations[0].pnl_usd),
            )
            group_pnls[model_key] = combined
        group_expectations = {key: float(np.mean(values)) for key, values in group_pnls.items()}
        expected = sum(weights[key] * value for key, value in group_expectations.items())
        worst_case_expected = min(group_expectations.values(), default=0.0)
        variance = sum(
            weights[key]
            * (float(np.var(values, ddof=1)) + (float(np.mean(values)) - expected) ** 2)
            for key, values in group_pnls.items()
        )
        stress_groups = [
            item
            for item in reference_valuations
            if item.metrics.regime in {SimulationRegime.ADVERSE, SimulationRegime.RUPTURE}
        ]
        cvar = max(
            (_tail_loss(group_pnls[item.model_key]) for item in stress_groups),
            default=0.0,
        )
        execution = sum(
            count * risk for count, risk in zip(counts, execution_risk_usd, strict=True)
        )
        dispersion = (
            max(group_expectations.values()) - min(group_expectations.values())
            if group_expectations
            else 0.0
        )
        objective = evaluate_scalar_objective(
            objective_contract,
            weighted_expected_usd=expected,
            worst_case_expected_usd=worst_case_expected,
            variance_usd2=variance,
            cvar_usd=cvar,
            execution_risk_usd=execution,
            model_dispersion_usd=dispersion,
            budget_usd=budget_usd,
        )
        scored.append(
            _ScoredAllocation(
                counts=counts,
                cost_eur=cost_eur,
                maximum_loss_eur=loss_eur,
                expected_usd=expected,
                worst_case_expected_usd=worst_case_expected,
                volatility_usd=math.sqrt(max(variance, 0.0)),
                cvar_usd=cvar,
                execution_risk_usd=execution,
                model_dispersion_usd=dispersion,
                objective=objective,
            )
        )
    scored.sort(
        key=lambda item: (
            item.objective,
            item.expected_usd,
            -item.cvar_usd,
            -sum(item.counts),
        ),
        reverse=True,
    )
    ranked = list(enumerate(scored, start=1))

    def allocation_id_for(item: _ScoredAllocation) -> str:
        identity = {
            "profile": profile_name,
            "objective_id": objective_contract.objective_id,
            "objective_version": objective_contract.version,
            "counts": item.counts,
            "candidates": [candidate.candidate_id for candidate in candidates],
        }
        return f"v11-allocation-{stable_hash(identity)[:16]}"

    pareto_frontier = allocation_pareto_frontier(
        [
            AllocationParetoPoint(
                allocation_id=allocation_id_for(item),
                counts=item.counts,
                expected_return_fraction=item.expected_usd / budget_usd,
                worst_case_return_fraction=(item.worst_case_expected_usd / budget_usd),
                volatility_fraction=item.volatility_usd / budget_usd,
                cvar_fraction=item.cvar_usd / budget_usd,
                cost_fraction=item.cost_eur / budget_eur,
                maximum_loss_fraction=item.maximum_loss_eur / budget_eur,
                execution_risk_fraction=item.execution_risk_usd / budget_usd,
                model_dispersion_fraction=item.model_dispersion_usd / budget_usd,
                scalar_objective=item.objective,
                no_trade=not any(item.counts),
            )
            for item in scored
        ]
    )
    no_trade_allocation_id = next(
        point.allocation_id for point in pareto_frontier if point.no_trade
    )
    selected = ranked[: profile.maximum_allocations]
    cash_baseline = next(
        ((rank, item) for rank, item in ranked if not any(item.counts)),
        None,
    )
    if (
        cash_baseline is not None
        and profile.maximum_allocations > 1
        and all(any(item.counts) for _, item in selected)
    ):
        selected[-1] = cash_baseline
        selected.sort(key=lambda pair: pair[0])
    results: list[AllocationResult] = []
    for rank, item in selected:
        lines = [
            AllocationLine(
                candidate_id=candidate.candidate_id,
                strategy_units=count,
                option_contracts=count * contracts,
                cost_eur=count * cost,
                maximum_loss_eur=count * loss,
            )
            for count, candidate, contracts, cost, loss in zip(
                item.counts,
                candidates,
                contract_counts,
                costs_eur,
                losses_eur,
                strict=True,
            )
            if count > 0
        ]
        total_cost = sum(line.cost_eur for line in lines)
        total_loss = sum(line.maximum_loss_eur for line in lines)
        total_contracts = sum(line.option_contracts for line in lines)
        selected_positions = len(lines)
        concentration = (
            max((line.cost_eur / total_cost for line in lines), default=0.0)
            if total_cost > 0
            else 0.0
        )
        aggregate_greeks = {
            "delta": sum(
                count * candidate.net_greeks.delta
                for count, candidate in zip(item.counts, candidates, strict=True)
            ),
            "gamma": sum(
                count * candidate.net_greeks.gamma
                for count, candidate in zip(item.counts, candidates, strict=True)
            ),
            "vega": sum(
                count * candidate.net_greeks.vega
                for count, candidate in zip(item.counts, candidates, strict=True)
            ),
            "theta": sum(
                count * candidate.net_greeks.theta
                for count, candidate in zip(item.counts, candidates, strict=True)
            ),
        }
        no_trade = not lines
        active_constraints = [
            name
            for name, used, limit in (
                ("budget", total_cost, budget_eur),
                ("maximum_loss", total_loss, maximum_loss_eur),
                ("maximum_contracts", float(total_contracts), float(maximum_contracts)),
                ("maximum_positions", float(selected_positions), float(maximum_positions)),
                ("maximum_concentration", concentration, maximum_concentration),
            )
            if limit > 0 and used >= 0.95 * limit
        ]
        for name, value in aggregate_greeks.items():
            if no_trade:
                break
            lower, upper = {
                "delta": delta_exposure_range,
                "gamma": gamma_exposure_range,
                "vega": vega_exposure_range,
                "theta": theta_exposure_range,
            }[name]
            span = max(upper - lower, 1e-9)
            if value - lower <= 0.05 * span or upper - value <= 0.05 * span:
                active_constraints.append(f"{name}_exposure")
        results.append(
            AllocationResult(
                allocation_id=allocation_id_for(item),
                profile=profile_name,
                rank=rank,
                lines=lines,
                cash_reserve_eur=max(budget_eur - total_cost, 0.0),
                expected_pnl_eur=item.expected_usd / eur_usd_rate,
                volatility_eur=item.volatility_usd / eur_usd_rate,
                cvar_95_eur=item.cvar_usd / eur_usd_rate,
                execution_risk_eur=item.execution_risk_usd / eur_usd_rate,
                model_dispersion_eur=item.model_dispersion_usd / eur_usd_rate,
                objective=item.objective,
                constraint_checks={
                    "budget": total_cost <= budget_eur + 1e-9,
                    "maximum_loss": total_loss <= maximum_loss_eur + 1e-9,
                    "maximum_contracts": total_contracts <= maximum_contracts,
                    "maximum_positions": selected_positions <= maximum_positions,
                    "maximum_concentration": concentration <= maximum_concentration + 1e-9,
                    "multiple_strategies_policy": (
                        allow_multiple_strategies or selected_positions <= 1
                    ),
                    "delta_exposure": (
                        no_trade
                        or delta_exposure_range[0]
                        <= aggregate_greeks["delta"]
                        <= delta_exposure_range[1]
                    ),
                    "gamma_exposure": (
                        no_trade
                        or gamma_exposure_range[0]
                        <= aggregate_greeks["gamma"]
                        <= gamma_exposure_range[1]
                    ),
                    "vega_exposure": (
                        no_trade
                        or vega_exposure_range[0]
                        <= aggregate_greeks["vega"]
                        <= vega_exposure_range[1]
                    ),
                    "theta_exposure": (
                        no_trade
                        or theta_exposure_range[0]
                        <= aggregate_greeks["theta"]
                        <= theta_exposure_range[1]
                    ),
                    "whole_contracts": all(
                        isinstance(value, int) and value >= 0 for value in item.counts
                    ),
                    "bounded_debit_margin": total_cost <= budget_eur + 1e-9,
                    "v10_liquidity_gate": all(
                        candidate.status.value != "blocked"
                        for count, candidate in zip(
                            item.counts,
                            candidates,
                            strict=True,
                        )
                        if count > 0
                    ),
                },
                diagnostics=_continuous_diagnostics(
                    counts=item.counts,
                    candidates=candidates,
                    valuations=valuations,
                    weights=weights,
                    risk_aversion=objective_contract.risk_aversion,
                    budget_usd=budget_usd,
                ),
                no_trade=no_trade,
                active_constraints=active_constraints,
                near_miss_allocations=[
                    f"Global feasible rank {other_rank}: objective={other.objective:.6f}"
                    for other_rank, other in ranked
                    if other_rank > rank
                ][:3],
                constraint_sensitivity=[
                    (
                        "No allocation is forced; relaxing a hard constraint requires "
                        "an explicit policy change and a full rerun."
                    ),
                    (
                        "The selected solution may change if budget, loss, contracts, "
                        "positions, concentration, liquidity, or Greek ranges change."
                    ),
                ],
                cash_reason=(
                    "Cash/NO_TRADE is the required zero-allocation reference with objective zero."
                    if no_trade
                    else "Unused cash is retained because whole contracts and hard constraints "
                    "make the residual budget non-deployable without weakening policy."
                ),
                reasons=(
                    ["Cash baseline is retained as an explicit feasible reference."]
                    if no_trade
                    else [
                        "Exact whole-contract enumeration; unused budget is retained as cash.",
                        f"Objective contract {objective_contract.objective_id} "
                        f"version {objective_contract.version} is explicit.",
                    ]
                ),
            )
        )
    return AllocationOptimizationReport(
        objective=objective_contract,
        feasible_allocations=len(scored),
        pareto_frontier=pareto_frontier,
        selected_allocations=results,
        no_trade_allocation_id=no_trade_allocation_id,
        assumptions=(
            "The feasible integer set is enumerated exhaustively within configured caps.",
            "Pareto dominance is non-compensatory across return, risk, cost, loss, "
            "execution, and model dispersion.",
            "Configured heuristic regime weights are not calibrated probabilities.",
        ),
    )


def optimize_allocations(
    *,
    candidates: list[ThesisCandidate],
    valuations: dict[str, list[StrategyPathValuation]],
    regime_weights: dict[SimulationRegime, float],
    profile_name: str,
    profile: OptimizerProfileConfig,
    budget_eur: float,
    maximum_loss_eur: float,
    maximum_contracts: int,
    eur_usd_rate: float,
    maximum_positions: int = 4,
    maximum_concentration: float = 1.0,
    minimum_liquidity_score: float = 0.0,
    maximum_relative_spread: float = 1.0,
    delta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    gamma_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    vega_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    theta_exposure_range: tuple[float, float] = (-1_000_000.0, 1_000_000.0),
    allow_multiple_strategies: bool = True,
    objective_contract: OptimizationObjectiveContract | None = None,
) -> list[AllocationResult]:
    """Compatibility API returning scalar-ranked selections from the richer report."""

    if not candidates:
        return []
    return optimize_allocations_with_frontier(
        candidates=candidates,
        valuations=valuations,
        regime_weights=regime_weights,
        profile_name=profile_name,
        profile=profile,
        budget_eur=budget_eur,
        maximum_loss_eur=maximum_loss_eur,
        maximum_contracts=maximum_contracts,
        eur_usd_rate=eur_usd_rate,
        maximum_positions=maximum_positions,
        maximum_concentration=maximum_concentration,
        minimum_liquidity_score=minimum_liquidity_score,
        maximum_relative_spread=maximum_relative_spread,
        delta_exposure_range=delta_exposure_range,
        gamma_exposure_range=gamma_exposure_range,
        vega_exposure_range=vega_exposure_range,
        theta_exposure_range=theta_exposure_range,
        allow_multiple_strategies=allow_multiple_strategies,
        objective_contract=objective_contract,
    ).selected_allocations
