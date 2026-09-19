from __future__ import annotations

from pathlib import Path

import take_two_options

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_package_export_is_decision_pipeline() -> None:
    assert take_two_options.__all__ == ["analyze_trade"]
    assert take_two_options.analyze_trade.__module__ == "take_two_options.decision.pipeline"


def test_legacy_orchestration_and_scoring_are_deleted() -> None:
    package = ROOT / "src/take_two_options"
    assert not (package / "engine.py").exists()
    assert not (package / "scoring.py").exists()

    current_sources = [
        path for path in package.rglob("*.py") if "__pycache__" not in path.parts
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in current_sources)
    assert "take_two_options.engine" not in source
    assert "take_two_options.scoring" not in source
    assert "analyze_bundle" not in source
