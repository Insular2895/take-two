"""Append-only in-memory registry for every generated or evaluated variant."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Literal

from take_two_options.knowledge.provenance import canonical_json
from take_two_options.knowledge.schemas import Architecture, TrialRecord

TrialStage = Literal[
    "generation",
    "pruning",
    "coarse_search",
    "fine_search",
    "stress",
    "placebo",
    "validation",
    "ranking",
]
TrialOutcome = Literal["generated", "pruned", "evaluated", "failed", "selected", "rejected"]


class TrialRegistry:
    def __init__(self, *, run_id: str, seed: int, config_hash: str) -> None:
        self.run_id = run_id
        self.seed = seed
        self.config_hash = config_hash
        self.records: list[TrialRecord] = []

    def register(
        self,
        *,
        stage: TrialStage,
        outcome: TrialOutcome,
        architecture: Architecture | None = None,
        candidate_id: str | None = None,
        parameters: dict[str, Any] | None = None,
        reason: str = "",
    ) -> TrialRecord:
        record = TrialRecord(
            trial_id=f"{self.run_id}-trial-{len(self.records) + 1:08d}",
            run_id=self.run_id,
            stage=stage,
            architecture=architecture,
            candidate_id=candidate_id,
            parameters=parameters or {},
            outcome=outcome,
            reason=reason,
            seed=self.seed,
            config_hash=self.config_hash,
        )
        self.records.append(record)
        return record

    def counts(self) -> dict[str, int]:
        return dict(Counter(record.stage for record in self.records))

    def write_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(canonical_json(record) + "\n" for record in self.records),
            encoding="utf-8",
        )
