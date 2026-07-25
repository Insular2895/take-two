"""Deterministic conflict detection between structured rules."""

from __future__ import annotations

from collections import defaultdict

from take_two_options.knowledge.loader import KnowledgeCorpus


def detect_conflicts(corpus: KnowledgeCorpus) -> list[str]:
    values: dict[tuple[str, tuple[str, ...]], list[tuple[str, object]]] = defaultdict(list)
    for item in corpus.items:
        conditions = tuple(sorted(item.conditions))
        for parameter in item.parameters_provided:
            values[(parameter.name, conditions)].append((item.knowledge_id, parameter.value))
    conflicts: list[str] = []
    for (parameter_name, conditions), definitions in sorted(values.items()):
        distinct = {repr(value) for _, value in definitions}
        if len(distinct) > 1:
            ids = ", ".join(item_id for item_id, _ in definitions)
            conflicts.append(
                f"parameter {parameter_name!r} has conflicting values under "
                f"{conditions or ('unconditional',)} in {ids}"
            )
    return conflicts
