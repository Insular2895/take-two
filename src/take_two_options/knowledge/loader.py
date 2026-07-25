"""Load JSON/YAML knowledge objects without interpreting prose."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.knowledge.schemas import (
    KnowledgeItem,
    ModernValidationRecord,
    StrategyRecipe,
)


class KnowledgeLoadError(ValueError):
    """Raised when a structured knowledge document cannot be loaded."""


class KnowledgeCorpus(StrictModel):
    items: list[KnowledgeItem] = Field(default_factory=list)
    recipes: list[StrategyRecipe] = Field(default_factory=list)
    modern_validations: list[ModernValidationRecord] = Field(default_factory=list)
    loaded_files: list[str] = Field(default_factory=list)


def _document(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise KnowledgeLoadError(f"{path}: {error}") from error


def _objects(value: Any, path: Path) -> list[dict[str, Any]]:
    if isinstance(value, dict) and "objects" in value:
        value = value["objects"]
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise KnowledgeLoadError(f"{path}: expected an object or list of objects")
    return value


def load_knowledge(knowledge_dir: Path) -> KnowledgeCorpus:
    if not knowledge_dir.is_dir():
        raise KnowledgeLoadError(f"knowledge directory does not exist: {knowledge_dir}")
    corpus = KnowledgeCorpus()
    roots = [knowledge_dir]
    modern_validation_dir = knowledge_dir.parent / "modern_validation"
    if modern_validation_dir.is_dir():
        roots.append(modern_validation_dir)
    paths = sorted(
        path
        for root in roots
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml"}
    )
    for path in paths:
        for raw in _objects(_document(path), path):
            object_type = raw.get("object_type")
            try:
                if object_type == "knowledge_item":
                    corpus.items.append(KnowledgeItem.model_validate(raw))
                elif object_type == "strategy_recipe":
                    corpus.recipes.append(StrategyRecipe.model_validate(raw))
                elif object_type == "modern_validation":
                    corpus.modern_validations.append(ModernValidationRecord.model_validate(raw))
                else:
                    raise KnowledgeLoadError(
                        f"{path}: unsupported object_type {object_type!r}"
                    )
            except ValueError as error:
                if isinstance(error, KnowledgeLoadError):
                    raise
                raise KnowledgeLoadError(f"{path}: {error}") from error
        corpus.loaded_files.append(str(path))
    if not paths:
        raise KnowledgeLoadError(f"no JSON or YAML knowledge objects found in {knowledge_dir}")
    return corpus
