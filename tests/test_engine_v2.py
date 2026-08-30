from __future__ import annotations

import inspect

from take_two_options.decision.pipeline import analyze_trade


def test_canonical_pipeline_remains_explicit_read_only_orchestration() -> None:
    source = inspect.getsource(analyze_trade)
    assert "enumerate_candidates" in source
    assert "coarse_search" in source
    assert "fine_search" in source
    assert "decide_verdict" in source
    assert "submit_order" not in source
    assert "place_order" not in source
