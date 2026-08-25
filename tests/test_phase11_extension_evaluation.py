from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.validation.extension_evaluation import (
    AdvancedExtensionAssessment,
    ExtensionGateEvidence,
    Phase11ExtensionReview,
    build_phase11_extension_review,
    classify_extension,
)

ROOT = Path(__file__).resolve().parents[1]


def test_phase11_review_is_exact_and_integrates_no_advanced_model() -> None:
    expected = build_phase11_extension_review()
    committed = Phase11ExtensionReview.model_validate_json(
        (ROOT / "validation/phase11_extension_review.json").read_text(encoding="utf-8")
    )
    assert committed == expected
    assert committed.overall_status == "NO_ADVANCED_MODEL_IMPLEMENTATION"
    assert committed.candidate_for_implementation == []
    assert committed.integrated_advanced_models == []
    assert {item.status for item in committed.assessments} == {"defer", "reject"}
    assert all(not item.evidence.oos_material_gain_demonstrated for item in committed.assessments)
    assert all(not item.implementation_allowed for item in committed.assessments)
    assert committed.order_capability == "forbidden"


def test_candidate_status_requires_every_material_evidence_gate() -> None:
    incomplete = ExtensionGateEvidence(authorized_data_ready=True)
    assert classify_extension(incomplete, out_of_scope_current_release=False) == "defer"
    complete = ExtensionGateEvidence(
        authorized_data_ready=True,
        identifiable_against_baseline=True,
        oos_material_gain_demonstrated=True,
        ranking_sensitivity_completed=True,
        numerical_cost_benchmarked=True,
        independent_review_completed=True,
    )
    assert classify_extension(complete, out_of_scope_current_release=False) == (
        "candidate_for_implementation"
    )
    payload = build_phase11_extension_review().assessments[0].model_dump()
    payload["status"] = "candidate_for_implementation"
    with pytest.raises(ValidationError, match="exceeds computed status"):
        AdvancedExtensionAssessment.model_validate(payload)
