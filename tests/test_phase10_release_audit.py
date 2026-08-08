from pathlib import Path

from take_two_options.validation.release_audit import (
    ReleaseEvidenceReview,
    build_release_evidence_review,
)

ROOT = Path(__file__).resolve().parents[1]


def test_phase10_release_review_is_deterministic_and_conservative() -> None:
    expected = build_release_evidence_review(ROOT)
    committed = ReleaseEvidenceReview.model_validate_json(
        (ROOT / "validation/phase10_release_review.json").read_text(encoding="utf-8")
    )
    assert committed == expected
    assert committed.research_release_status == "READY_RESEARCH_ONLY"
    assert committed.financial_promotion_status == "BLOCKED_MISSING_REAL_EVIDENCE"
    assert committed.maximum_decision_claim == "software_tested_only"
    assert committed.active_experiment_manifests == []
    assert committed.reproduced_experiment_manifests == []
    assert committed.contaminated_holdouts == ["v7", "v8", "v9"]
    assert committed.final_holdout_status == "not_created_no_dataset"
    assert committed.invalid_promoted_claims == []
    assert committed.order_capability == "forbidden"
