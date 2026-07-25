"""Convert path executions into the canonical probability and risk metrics."""

from __future__ import annotations

from collections import Counter
from datetime import date
from statistics import fmean, median

from take_two_options.knowledge.schemas import CompiledStrategyCandidate, ModelMetrics, TradeRequest
from take_two_options.research_statistics import (
    conditional_value_at_risk,
    empirical_quantile,
    value_at_risk,
)
from take_two_options.simulation.conditional_monte_carlo import ConditionalPathSet
from take_two_options.simulation.path_execution import execute_path


def evaluate_path_set(
    candidate: CompiledStrategyCandidate,
    path_set: ConditionalPathSet,
    *,
    request: TradeRequest,
    start_date: date,
) -> ModelMetrics:
    results = [
        execute_path(
            candidate,
            path,
            start_date=start_date,
            commission_per_contract_side=request.execution_policy.commission_per_contract_side,
            slippage_per_contract_side=request.execution_policy.slippage_per_contract_side,
        )
        for path in path_set.paths
    ]
    pnls = [result.pnl for result in results]
    maximum_loss = max(candidate.risk.maximum_loss, 0.01)
    returns = [pnl / maximum_loss for pnl in pnls]
    reasons = Counter(result.exit_reason for result in results)
    return ModelMetrics(
        model_id=path_set.model_id,
        paths=len(results),
        seed=path_set.seed,
        probability_profit=sum(value > 0 for value in pnls) / len(pnls),
        probability_gain_50=sum(value > 0.5 for value in returns) / len(returns),
        probability_gain_80=sum(value > 0.8 for value in returns) / len(returns),
        probability_gain_100=sum(value > 1.0 for value in returns) / len(returns),
        probability_loss_50=sum(value < -0.5 for value in returns) / len(returns),
        probability_loss_70=sum(value < -0.7 for value in returns) / len(returns),
        probability_near_total_loss=sum(value < -0.95 for value in returns) / len(returns),
        expected_pnl=fmean(pnls),
        median_pnl=median(pnls),
        quantiles={
            "p05": empirical_quantile(pnls, 0.05),
            "p25": empirical_quantile(pnls, 0.25),
            "p75": empirical_quantile(pnls, 0.75),
            "p95": empirical_quantile(pnls, 0.95),
        },
        var_95=value_at_risk(pnls),
        cvar_95=conditional_value_at_risk(pnls),
        simulated_drawdown=max(result.maximum_drawdown for result in results),
        mean_exit_days=fmean(result.exit_day for result in results),
        take_profit_frequency=reasons["profit_target"] / len(results),
        stop_frequency=reasons["stop_loss"] / len(results),
        exit_reasons=dict(reasons),
    )
