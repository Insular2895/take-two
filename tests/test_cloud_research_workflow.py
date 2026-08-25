from __future__ import annotations

from pathlib import Path

import yaml

from take_two_options.cloud.research_callback import sign_request


def test_phase_m_workflow_has_one_non_executable_input() -> None:
    path = Path(".github/workflows/phase-m-research-analysis.yml")
    text = path.read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    triggers = document.get("on", document.get(True))
    assert set(triggers) == {"workflow_dispatch"}
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"analysis_request_id"}
    assert document["permissions"] == {"contents": "read"}
    assert "${{ inputs.analysis_request_id }}" in text
    assert "run: ${{" not in text
    assert "python scripts/run_cloud_research_analysis.py" in text
    assert "IBKR" not in text
    assert "OPRA" not in text


def test_callback_signature_covers_identity_method_path_and_body() -> None:
    signed = sign_request(
        secret="test-secret",
        analysis_request_id="analysis-aaaaaaaaaaaaaaaaaaaaaaaa",
        method="POST",
        pathname="/api/internal/research/analyses/analysis-aaaaaaaaaaaaaaaaaaaaaaaa/callback",
        body=b'{"kind":"STARTED"}',
        timestamp=1_700_000_000,
        nonce="fixed-nonce-0001",
    )
    assert signed.content_sha256 == (
        "fd332b1429c8a69d9ec46c2995ddf9c249d7ebc558b55e80fd078eb280795f3a"
    )
    assert signed.signature == "51e50a45315630e0fe1ed9ae83986bef2be27ef78018c1c76eace1221452e3d9"
