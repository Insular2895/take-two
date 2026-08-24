"""Load and hash the versioned pre-OPRA configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

from take_two_options.config.contracts import PreOpraConfig, ProspectiveBudgetConfig
from take_two_options.knowledge.provenance import stable_hash


def load_pre_opra_config(path: Path) -> PreOpraConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("pre-OPRA configuration must be a YAML mapping")
    return PreOpraConfig.model_validate(payload)


def pre_opra_config_hash(config: PreOpraConfig) -> str:
    return stable_hash(config.model_dump(mode="json"))


def load_prospective_budget_config(path: Path) -> ProspectiveBudgetConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("prospective budget configuration must be a YAML mapping")
    return ProspectiveBudgetConfig.model_validate(payload)
