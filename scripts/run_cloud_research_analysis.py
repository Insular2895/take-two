"""GitHub Actions entry point for one signed Phase M Cloud research analysis."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from take_two_options.cloud.research_callback import sign_request
from take_two_options.cloud.research_contracts import AnalysisJobRequest
from take_two_options.cloud.research_workbench import run_research_analysis

ANALYSIS_ID_PATTERN = re.compile(r"^analysis-[a-f0-9]{24}$")
MAX_RESPONSE_BYTES = 1_048_576


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name}_REQUIRED")
    return value


def _headers(
    *,
    secret: str,
    analysis_id: str,
    method: str,
    pathname: str,
    body: bytes,
) -> dict[str, str]:
    signed = sign_request(
        secret=secret,
        analysis_request_id=analysis_id,
        method=method,
        pathname=pathname,
        body=body,
    )
    return {
        "Content-Type": "application/json",
        "X-TTWO-Timestamp": signed.timestamp,
        "X-TTWO-Nonce": signed.nonce,
        "X-TTWO-Content-SHA256": signed.content_sha256,
        "X-TTWO-Analysis-Id": analysis_id,
        "X-TTWO-Signature": signed.signature,
        "CF-Access-Client-Id": _required("CF_ACCESS_CLIENT_ID"),
        "CF-Access-Client-Secret": _required("CF_ACCESS_CLIENT_SECRET"),
        "User-Agent": "take-two-phase-m-research/1.0",
    }


def _call(
    *,
    base_url: str,
    secret: str,
    analysis_id: str,
    method: str,
    pathname: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = (
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        if payload is not None
        else b""
    )
    target = f"{base_url.rstrip('/')}{pathname}"
    last_error: Exception | None = None
    for attempt in range(3):
        request = Request(
            target,
            data=body if method != "GET" else None,
            method=method,
            headers=_headers(
                secret=secret,
                analysis_id=analysis_id,
                method=method,
                pathname=pathname,
                body=body,
            ),
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310 - governed URL
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise RuntimeError("WORKER_RESPONSE_TOO_LARGE")
                decoded = json.loads(raw or b"{}")
                if not isinstance(decoded, dict):
                    raise RuntimeError("INVALID_WORKER_RESPONSE")
                return {str(key): value for key, value in decoded.items()}
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"WORKER_REQUEST_FAILED: {last_error}")


def _callback(
    base_url: str,
    secret: str,
    analysis_id: str,
    payload: dict[str, Any],
) -> None:
    _call(
        base_url=base_url,
        secret=secret,
        analysis_id=analysis_id,
        method="POST",
        pathname=f"/api/internal/research/analyses/{analysis_id}/callback",
        payload=payload,
    )


def main() -> int:
    analysis_id = _required("ANALYSIS_REQUEST_ID")
    if not ANALYSIS_ID_PATTERN.fullmatch(analysis_id):
        raise RuntimeError("INVALID_ANALYSIS_REQUEST_ID")
    base_url = _required("ANALYSIS_WORKER_BASE_URL")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
        raise RuntimeError("INVALID_ANALYSIS_WORKER_BASE_URL")
    secret = _required("ANALYSIS_CALLBACK_SECRET")
    run_id = _required("GITHUB_RUN_ID")
    git_commit = _required("GITHUB_SHA")
    request_path = f"/api/internal/research/analyses/{analysis_id}/request"
    job_request = AnalysisJobRequest.model_validate(
        _call(
            base_url=base_url,
            secret=secret,
            analysis_id=analysis_id,
            method="GET",
            pathname=request_path,
        )
    )
    common = {
        "analysis_request_id": analysis_id,
        "github_run_id": run_id,
        "git_commit": git_commit,
    }
    _callback(base_url, secret, analysis_id, {"kind": "STARTED", **common})
    try:
        _callback(
            base_url,
            secret,
            analysis_id,
            {"kind": "PROGRESS", "step": "ENUMERATING_COMPLETE_UNIVERSE", **common},
        )
        result = run_research_analysis(
            analysis_request_id=analysis_id,
            budget_request=job_request.budget,
            governed_snapshot=(
                Path(_required("GOVERNED_SNAPSHOT_PATH"))
                if job_request.budget.market_data_mode == "LAST_GOVERNED_SNAPSHOT"
                else None
            ),
        )
        detail_by_id = {item.candidate_id: item for item in result.details}
        batch_size = 20
        for index in range(0, len(result.summaries), batch_size):
            summaries = result.summaries[index : index + batch_size]
            _callback(
                base_url,
                secret,
                analysis_id,
                {
                    "kind": "CANDIDATE_BATCH",
                    "batch_index": index // batch_size,
                    "candidates": [
                        {
                            "summary": summary.model_dump(mode="json"),
                            "detail": detail_by_id[summary.candidate_id].model_dump(mode="json"),
                        }
                        for summary in summaries
                    ],
                    **common,
                },
            )
        final_payload = result.model_dump(
            mode="json",
            exclude={"summaries", "details"},
        )
        _callback(
            base_url,
            secret,
            analysis_id,
            {"kind": "COMPLETE", "result": final_payload, **common},
        )
        print(
            f"{result.status}: {result.total_generated} candidates persisted; "
            f"{result.total_paper_eligible} paper-eligible."
        )
        return 0
    except Exception as error:
        try:
            _callback(
                base_url,
                secret,
                analysis_id,
                {"kind": "FAILED", "error_code": type(error).__name__, **common},
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Research analysis failed: {error}", file=sys.stderr)
        raise
