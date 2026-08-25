"""Compile validated knowledge into deterministic rules and strategy recipes."""

from __future__ import annotations

from datetime import UTC, datetime

from take_two_options.knowledge.loader import KnowledgeCorpus
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import (
    CompiledRule,
    EmpiricalStatus,
    ExecutionStatus,
    KnowledgeLifecycle,
    MarketValidity,
    StrategyCatalog,
)
from take_two_options.knowledge.validator import validate_knowledge


class KnowledgeCompilationError(ValueError):
    """Raised when invalid knowledge is presented to the compiler."""


def _blocking_reasons(
    *,
    lifecycle: KnowledgeLifecycle,
    market_validity: MarketValidity,
    empirical_status: EmpiricalStatus,
    execution_status: ExecutionStatus,
    validation_statuses: list[str],
) -> list[str]:
    reasons: list[str] = []
    if lifecycle is not KnowledgeLifecycle.COMPILABLE:
        reasons.append(f"lifecycle={lifecycle.value}")
    if market_validity in {MarketValidity.HISTORICAL_ONLY, MarketValidity.UNKNOWN}:
        reasons.append(f"market_validity={market_validity.value}")
    if empirical_status is EmpiricalStatus.FAILED:
        reasons.append("empirical_status=FAILED")
    if execution_status not in {
        ExecutionStatus.TTWO_TESTABLE,
        ExecutionStatus.RESEARCH_ONLY,
        ExecutionStatus.PAPER_ELIGIBLE,
    }:
        reasons.append(f"execution_status={execution_status.value}")
    if not validation_statuses:
        reasons.append("modern_validation_missing")
    elif not any(status == "passed" for status in validation_statuses):
        reasons.append("modern_validation_not_passed")
    return reasons


def compile_knowledge(corpus: KnowledgeCorpus) -> StrategyCatalog:
    validation = validate_knowledge(corpus)
    if not validation.valid:
        raise KnowledgeCompilationError("; ".join(validation.errors))
    validation_by_target: dict[str, list[str]] = {}
    for record in corpus.modern_validations:
        for target_id in record.target_ids:
            validation_by_target.setdefault(target_id, []).append(record.overall_status)

    rules: list[CompiledRule] = []
    recipes = []
    blocked: dict[str, list[str]] = {}
    for item in corpus.items:
        reasons = _blocking_reasons(
            lifecycle=item.lifecycle,
            market_validity=item.market_validity,
            empirical_status=item.empirical_status,
            execution_status=item.execution_status,
            validation_statuses=validation_by_target.get(item.knowledge_id, []),
        )
        if reasons:
            blocked[item.knowledge_id] = reasons
            continue
        rules.append(
            CompiledRule(
                rule_id=f"compiled:{item.knowledge_id}",
                source_knowledge_id=item.knowledge_id,
                condition=" AND ".join(item.conditions) or "always",
                action=item.action or "",
                parameter_values={
                    parameter.name: parameter.value for parameter in item.parameters_provided
                },
                parameter_origins={
                    parameter.name: parameter.origin for parameter in item.parameters_provided
                },
                source_ids=[source.source_id for source in item.sources],
            )
        )
    for recipe in corpus.recipes:
        reasons = _blocking_reasons(
            lifecycle=recipe.lifecycle,
            market_validity=recipe.market_validity,
            empirical_status=recipe.empirical_status,
            execution_status=recipe.execution_status,
            validation_statuses=validation_by_target.get(recipe.recipe_id, []),
        )
        if reasons:
            blocked[recipe.recipe_id] = reasons
        else:
            recipes.append(recipe)

    knowledge_payload = {
        "items": corpus.items,
        "recipes": corpus.recipes,
        "validations": corpus.modern_validations,
    }
    return StrategyCatalog(
        compiled_at=datetime.now(UTC),
        knowledge_hash=stable_hash(knowledge_payload),
        rules=rules,
        recipes=recipes,
        blocked_items=blocked,
        contradictions=validation.conflicts,
    )
