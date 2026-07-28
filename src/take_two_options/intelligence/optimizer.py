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
from take_two_options.thesis_scanner.schemas import ThesisCandidate


@dataclass(frozen=True)
class _ScoredAllocation:
    counts: tuple[int, ...]
    expected_usd: float
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
    gradient = expected / budget_usd - (
        2 * risk_aversion * covariance @ x / budget_usd**2
    )
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
) -> list[AllocationResult]:
    """Enumerate the finite integer set; retaining cash and no-trade are explicit choices."""
    if not candidates:
        return []
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
        sum(leg.quantity for leg in candidate.base_candidate.legs)
        for candidate in candidates
    ]
    costs_eur = [candidate.execution.total_cost_eur for candidate in candidates]
    losses_eur = [candidate.maximum_loss_eur for candidate in candidates]
    execution_risk_usd = [
        candidate.decision_metrics.maximum_leg_relative_spread
        * candidate.execution.total_cost_usd
        for candidate in candidates
    ]
    budget_usd = budget_eur * eur_usd_rate
    scored: list[_ScoredAllocation] = []
    for counts in _integer_vectors(contract_counts, maximum_contracts=maximum_contracts):
        cost_eur = sum(count * cost for count, cost in zip(counts, costs_eur, strict=True))
        loss_eur = sum(count * loss for count, loss in zip(counts, losses_eur, strict=True))
        if cost_eur > budget_eur + 1e-9 or loss_eur > maximum_loss_eur + 1e-9:
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
        group_expectations = {
            key: float(np.mean(values)) for key, values in group_pnls.items()
        }
        expected = sum(weights[key] * value for key, value in group_expectations.items())
        variance = sum(
            weights[key]
            * (
                float(np.var(values, ddof=1))
                + (float(np.mean(values)) - expected) ** 2
            )
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
            count * risk
            for count, risk in zip(counts, execution_risk_usd, strict=True)
        )
        dispersion = (
            max(group_expectations.values()) - min(group_expectations.values())
            if group_expectations
            else 0.0
        )
        objective = (
            expected / budget_usd
            - profile.risk_aversion * variance / budget_usd**2
            - profile.cvar_aversion * cvar / budget_usd
            - profile.execution_penalty * execution / budget_usd
            - profile.model_risk_penalty * dispersion / budget_usd
        )
        scored.append(
            _ScoredAllocation(
                counts=counts,
                expected_usd=expected,
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
    selected = ranked[: profile.maximum_allocations]
    cash_baseline = next(
        (
            (rank, item)
            for rank, item in ranked
            if not any(item.counts)
        ),
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
        no_trade = not lines
        identity = {
            "profile": profile_name,
            "counts": item.counts,
            "candidates": [candidate.candidate_id for candidate in candidates],
        }
        results.append(
            AllocationResult(
                allocation_id=f"v11-allocation-{stable_hash(identity)[:16]}",
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
                    risk_aversion=profile.risk_aversion,
                    budget_usd=budget_usd,
                ),
                no_trade=no_trade,
                reasons=(
                    [
                        "Holding cash dominates all enumerated allocations under this profile."
                    ]
                    if no_trade
                    else [
                        "Exact whole-contract enumeration; unused budget is retained as cash.",
                        "Objective includes expectation, variance, adverse CVaR, execution, "
                        "and model dispersion.",
                    ]
                ),
            )
        )
    return results
