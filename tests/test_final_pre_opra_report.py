from __future__ import annotations

from pathlib import Path

from take_two_options.reporting.pre_opra_final import FinalPreOpraReport

ROOT = Path(__file__).resolve().parents[1]


def test_committed_final_report_is_complete_fail_closed_and_pre_opra() -> None:
    report = FinalPreOpraReport.model_validate_json(
        (ROOT / "reports/pre_opra/final_pre_opra_report_2026-08-08.json").read_text()
    )
    assert report.overall_status == "BLOCKED_BY_DATA"
    assert report.evidence_grade == "software_tested_only"
    assert report.decision == "NO_POSITION_RECOMMENDED"
    assert [phase.phase for phase in report.phase_results] == list("ABCDEFGHIJKL")
    assert set(report.score_status.values()) == {"unavailable"}
    assert report.holdout_state == "UNOPENED"
    assert report.holdout_used is False
    assert report.phase_m_started is False
    assert report.order_capability == "forbidden"


def test_static_dashboard_contains_no_script_or_remote_dependency() -> None:
    page = (ROOT / "reports/pre_opra/final_pre_opra_report_2026-08-08.html").read_text()
    assert "<script" not in page.casefold()
    assert "http://" not in page and "https://" not in page
    assert "BLOCKED_BY_DATA" in page
    assert "NO_POSITION_RECOMMENDED" in page
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
    assert "build_pre_opra_final_report.py" in manifest.command
    assert manifest.holdout_used is False
