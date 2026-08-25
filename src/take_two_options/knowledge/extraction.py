"""Validate book-specific extraction outputs produced outside the decision engine."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field

from take_two_options.domain import StrictModel
from take_two_options.knowledge.loader import KnowledgeCorpus, KnowledgeLoadError, load_knowledge
from take_two_options.knowledge.validator import validate_knowledge


class BookExtractionConfig(StrictModel):
    book_id: str
    title: str
    prompt_path: Path
    local_pdf_path: Path | None = None
    markdown_workspace: Path
    output_directory: Path
    required_sections: list[str] = Field(min_length=25)
    llm_role: str = "extract_normalize_retrieve_only"
    decision_authority: bool = False


def validate_extraction_output(path: Path) -> KnowledgeCorpus:
    corpus = load_knowledge(path)
    validation = validate_knowledge(corpus)
    if not validation.valid:
        raise KnowledgeLoadError("; ".join(validation.errors))
    return corpus


def write_extraction_manifest(
    config: BookExtractionConfig,
    corpus: KnowledgeCorpus,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "book_id": config.book_id,
                "title": config.title,
                "prompt_path": str(config.prompt_path),
                "local_pdf_path": (
                    str(config.local_pdf_path) if config.local_pdf_path else None
                ),
                "pdf_committed": False,
                "knowledge_items": len(corpus.items),
                "strategy_recipes": len(corpus.recipes),
                "decision_authority": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
