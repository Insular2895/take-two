"""Cheap broad search before path-dependent repricing."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean

from pydantic import Field

from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.domain import StrictModel
from take_two_options.knowledge.schemas import CompiledStrategyCandidate
from take_two_options.optimization.trial_registry import TrialRegistry
from take_two_options.simulation.conditional_monte_carlo import ConditionalPathSet


class CoarseCandidateScore(StrictModel):
    candidate_id: str
    conservative_expected_pnl: float
    worst_model_loss_probability: float = Field(ge=0, le=1)


class CoarseSearchResult(StrictModel):
    selected: list[CompiledStrategyCandidate]
    scores: list[CoarseCandidateScore]


def coarse_search(
    candidates: list[CompiledStrategyCandidate],
    path_sets: list[ConditionalPathSet],
    registry: TrialRegistry,
    *,
    maximum_per_architecture: int = 2,
) -> CoarseSearchResult:
    scored: list[tuple[CompiledStrategyCandidate, CoarseCandidateScore]] = []
    for candidate in candidates:
        model_expectations: list[float] = []
        model_loss_probabilities: list[float] = []
        for path_set in path_sets:
            terminal = [path[-1] for path in path_set.paths[:256]]
            pnls = [
                terminal_payoff(candidate.legs, spot)
                - candidate.risk.entry_debit
                - candidate.risk.fees
                - candidate.risk.slippage
                for spot in terminal
            ]
            model_expectations.append(fmean(pnls))
            model_loss_probabilities.append(
                sum(pnl < -0.7 * candidate.risk.maximum_loss for pnl in pnls) / len(pnls)
            )
        score = CoarseCandidateScore(
            candidate_id=candidate.candidate_id,
            conservative_expected_pnl=min(model_expectations),
            worst_model_loss_probability=max(model_loss_probabilities),
        )
        scored.append((candidate, score))
        registry.register(
            stage="coarse_search",
            outcome="evaluated",
            architecture=candidate.architecture,
            candidate_id=candidate.candidate_id,
            parameters={
                "models": [path_set.model_id for path_set in path_sets],
                "paths_per_model": min(len(path_sets[0].paths), 256),
            },
        )
    by_architecture: dict[str, list[tuple[CompiledStrategyCandidate, CoarseCandidateScore]]] = (
        defaultdict(list)
    )
    for candidate, score in scored:
        by_architecture[candidate.architecture.value].append((candidate, score))
    selected: list[CompiledStrategyCandidate] = []
    for architecture_scores in by_architecture.values():
        architecture_scores.sort(
            key=lambda item: (
                -item[1].conservative_expected_pnl,
                item[1].worst_model_loss_probability,
                item[0].risk.maximum_loss,
                item[0].candidate_id,
            )
        )
        selected.extend(
            candidate for candidate, _ in architecture_scores[:maximum_per_architecture]
        )
    score_models = [score for _, score in scored]
    score_models.sort(key=lambda score: score.candidate_id)
    return CoarseSearchResult(selected=selected, scores=score_models)
