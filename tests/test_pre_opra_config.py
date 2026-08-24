from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.config.loader import load_pre_opra_config, pre_opra_config_hash

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/pre_opra/v1/ttwo_research.yaml"


def test_unified_pre_opra_config_contains_required_governance_groups() -> None:
    config = load_pre_opra_config(CONFIG)
    payload = config.model_dump(mode="json")
    assert set(payload) == {
        "schema_version",
        "research_request",
        "market_context",
        "capital_constraints",
        "risk_profile",
        "strategy_universe",
        "model_universe",
        "scenario_set",
        "execution_assumptions",
        "validation_policy",
        "optimization_objective",
        "report_policy",
        "trade_economics",
        "extensions",
    }
    assert config.execution_assumptions.order_capability == "forbidden"
    assert config.execution_assumptions.preview_only is True
    assert len(pre_opra_config_hash(config)) == 64


def test_sourced_value_cannot_omit_source_lineage() -> None:
    config = load_pre_opra_config(CONFIG)
    payload = config.model_dump(mode="json")
    payload["risk_profile"]["target_return"]["status"] = "sourced"
    with pytest.raises(ValidationError, match="require source_ids"):
        type(config).model_validate(payload)


def test_scenario_probabilities_must_be_complete_and_sum_to_one() -> None:
    config = load_pre_opra_config(CONFIG)
    payload = config.model_dump(mode="json")
    payload["scenario_set"]["scenarios"][0]["probability"] = {
        "value": 0.5,
        "origin": "user_assumption",
        "status": "draft_to_validate",
        "source_ids": [],
        "rationale": "test",
    }
    with pytest.raises(ValidationError, match="all or none"):
        type(config).model_validate(payload)
