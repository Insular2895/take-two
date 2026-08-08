from __future__ import annotations

from pathlib import Path

from take_two_options.reporting.pre_opra_final import FinalPreOpraReport

ROOT = Path(__file__).resolve().parents[1]


def test_committed_final_report_is_complete_fail_closed_and_pre_opra() -> None:
    report = FinalPreOpraReport.model_validate_json(
        (ROOT / "reports/pre_opra/final_pre_opra_report_2026-08-08.json").read_text()
    )
    assert report.overall_status == "PRE_OPRA_RESEARCH_COMPLETE"
    assert report.evidence_grade == "development_oos_limited"
    assert report.decision == "NO_POSITION_RECOMMENDED"
    assert report.engine_verdict == "ENGINE_NOT_PROVEN_SUPERIOR"
    assert [section.section_id for section in report.sections] == list("ABCDEFGHIJKLMN")
    assert len(report.baseline_table) == 9
    assert len(report.five_scores) == 5
    assert all(score.score_value >= 0 for score in report.five_scores)
    assert any(score.score_coverage < 1 for score in report.five_scores)
    assert len(report.severe_loss_ladder) == 6
    assert len(report.top_candidates) == 5
    assert report.holdout_state == "UNOPENED"
    assert report.holdout_used is False
    assert report.phase_m_started is False
    assert report.order_capability == "forbidden"


def test_static_dashboard_contains_no_script_or_remote_dependency() -> None:
    page = (ROOT / "reports/pre_opra/final_pre_opra_report_2026-08-08.html").read_text()
    assert "<script" not in page.casefold()
    assert "http://" not in page and "https://" not in page
    assert "PRE_OPRA_RESEARCH_COMPLETE" in page
    assert "NO_POSITION_RECOMMENDED" in page
    assert "ENGINE_NOT_PROVEN_SUPERIOR" in page
    assert "V10 vs baselines" in page
    for score in (
        "opportunity",
        "risk",
        "evidence",
        "model_agreement",
        "execution_quality",
    ):
        assert score in page


def test_run_manifest_pins_code_config_data_seed_and_command() -> None:
    report = FinalPreOpraReport.model_validate_json(
        (ROOT / "reports/pre_opra/final_pre_opra_report_2026-08-08.json").read_text()
    )
    manifest = report.run_manifest
    assert len(manifest.code_commit) == 40
    assert len(manifest.configuration_hash) == 64
    assert len(manifest.dataset_hash) == 64
    assert manifest.seed == 20_260_808
    assert manifest.command == (
        "ttwo-options pre-opra-finalize --config configs/pre_opra/v1/ttwo_research.yaml"
    )
    assert set(manifest.score_versions.values()) == {"pre-opra-v2"}
    assert manifest.schema_version == "2.0"
    assert manifest.artifact_hashes
    assert manifest.holdout_used is False
