"""Evaluate recorded exit-policy neighbors around coarse-search finalists."""

from __future__ import annotations

from itertools import product

from take_two_options.candidate_generation.factory import with_exit_policy
from take_two_options.candidate_generation.search_space import StrategySearchSpace
from take_two_options.knowledge.schemas import (
    CompiledStrategyCandidate,
    StrategyRecipe,
    TradeRequest,
)
from take_two_options.optimization.complexity import complexity_penalty
from take_two_options.optimization.trial_registry import TrialRegistry
from take_two_options.simulation.conditional_monte_carlo import ConditionalPathSet
from take_two_options.simulation.evaluation import evaluate_path_set
from take_two_options.simulation.model_ensemble import summarize_models


def fine_search(
    candidates: list[CompiledStrategyCandidate],
    *,
    recipes: dict[str, StrategyRecipe],
    search_spaces: dict[str, StrategySearchSpace],
    path_sets: list[ConditionalPathSet],
    request: TradeRequest,
    registry: TrialRegistry,
) -> list[CompiledStrategyCandidate]:
    evaluated: list[CompiledStrategyCandidate] = []
    for candidate in candidates:
        recipe = recipes[candidate.recipe_id]
        space = search_spaces[candidate.recipe_id]
        for (
            profit_target,
            stop,
            holding_days,
            rolling_rule,
            recovery_rule,
        ) in product(
            space.profit_targets,
            space.stops,
            space.holding_days,
            space.rolling_rules,
            space.capital_recovery_rules,
        ):
            parameters = {
                "profit_target": profit_target,
                "stop_loss": stop,
                "holding_days": holding_days,
                "rolling_rule": rolling_rule,
                "capital_recovery_rule": recovery_rule,
            }
            if rolling_rule != "none":
                registry.register(
                    stage="fine_search",
                    outcome="rejected",
                    architecture=candidate.architecture,
                    candidate_id=candidate.candidate_id,
                    parameters=parameters,
                    reason="future combo quotes are unavailable for deterministic roll execution",
                )
                continue
            if (
                recovery_rule != "none"
                and not candidate.maintenance_policy.partial_recovery_feasible
            ):
                registry.register(
                    stage="fine_search",
                    outcome="rejected",
                    architecture=candidate.architecture,
                    candidate_id=candidate.candidate_id,
                    parameters=parameters,
                    reason="partial capital recovery is impossible with one long contract",
                )
                continue
            variant = with_exit_policy(
                candidate,
                profit_target=profit_target,
                stop_loss=stop,
                holding_days=holding_days,
                rolling_rule=rolling_rule,
                capital_recovery_rule=recovery_rule,
                origin=recipe.profit_targets.origin,
            )
            model_metrics = [
                evaluate_path_set(
                    variant,
                    path_set,
                    request=request,
                    start_date=request.as_of,
                )
                for path_set in path_sets
            ]
            variant.evaluation = summarize_models(model_metrics)
            variant.evaluation.complexity_penalty = complexity_penalty(variant)
            evaluated.append(variant)
            registry.register(
                stage="fine_search",
                outcome="evaluated",
                architecture=variant.architecture,
                candidate_id=variant.candidate_id,
                parameters=parameters,
            )
    return evaluated
