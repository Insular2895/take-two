"""Validate identity, lifecycle, provenance, and compilation readiness."""

from __future__ import annotations

from collections import Counter

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.knowledge.conflicts import detect_conflicts
from take_two_options.knowledge.loader import KnowledgeCorpus
from take_two_options.knowledge.schemas import (
    ExecutionStatus,
    KnowledgeLifecycle,
    ParameterOrigin,
)


class KnowledgeValidationResult(StrictModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    item_count: int = Field(ge=0)
    recipe_count: int = Field(ge=0)
    modern_validation_count: int = Field(ge=0)


def validate_knowledge(corpus: KnowledgeCorpus) -> KnowledgeValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    all_ids = [
        *(item.knowledge_id for item in corpus.items),
        *(recipe.recipe_id for recipe in corpus.recipes),
        *(record.validation_id for record in corpus.modern_validations),
    ]
    duplicates = sorted(item_id for item_id, count in Counter(all_ids).items() if count > 1)
    errors.extend(f"duplicate stable identifier: {item_id}" for item_id in duplicates)

    source_ids = {
        source.source_id for item in corpus.items for source in item.sources
    }
    source_ids.update(
        source.source_id for recipe in corpus.recipes for source in recipe.sources
    )
    source_ids.update(
        source.source_id
        for validation in corpus.modern_validations
        for source in validation.sources
    )
    for item in corpus.items:
        for parameter in item.parameters_provided:
            if parameter.origin is ParameterOrigin.SOURCED and not parameter.source_id:
                errors.append(
                    f"{item.knowledge_id}: sourced parameter {parameter.name} lacks source_id"
                )
            if parameter.source_id and parameter.source_id not in source_ids:
                errors.append(
                    f"{item.knowledge_id}: unknown parameter source {parameter.source_id}"
                )
        if item.lifecycle is KnowledgeLifecycle.COMPILABLE and item.action is None:
            errors.append(f"{item.knowledge_id}: compilable item lacks action")

    target_ids = {
        *(item.knowledge_id for item in corpus.items),
        *(recipe.recipe_id for recipe in corpus.recipes),
    }
    for record in corpus.modern_validations:
        for target_id in record.target_ids:
            if target_id not in target_ids:
                errors.append(f"{record.validation_id}: unknown target {target_id}")

    for recipe in corpus.recipes:
        if recipe.lifecycle is KnowledgeLifecycle.COMPILABLE and not recipe.validation_history:
            warnings.append(f"{recipe.recipe_id}: no validation history")
        if recipe.execution_status is ExecutionStatus.LIVE_ASSISTED_ELIGIBLE:
            errors.append(
                f"{recipe.recipe_id}: knowledge cannot authorize live-assisted eligibility"
            )
        for group_name, numeric_range in (
            ("profit_targets", recipe.profit_targets),
            ("stops", recipe.stops),
            ("holding_days", recipe.holding_days),
        ):
            if numeric_range.origin is ParameterOrigin.UNKNOWN:
                errors.append(f"{recipe.recipe_id}: {group_name} cannot have unknown origin")

    conflicts = detect_conflicts(corpus)
    return KnowledgeValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        conflicts=conflicts,
        item_count=len(corpus.items),
        recipe_count=len(corpus.recipes),
        modern_validation_count=len(corpus.modern_validations),
    )
