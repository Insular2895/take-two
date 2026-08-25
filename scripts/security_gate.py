"""Fail-closed repository checks for secrets, networked HTML, and order capability."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from take_two_options.intelligence.execution import (
    assert_all_execution_paths_forbidden,
)

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRECTORIES = (
    "src",
    "tests",
    "configs",
    "docs",
    "fixtures",
    "schemas",
    "scripts",
    "services",
    ".github",
)
SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "stripe_live_key": re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
}
NETWORK_HTML_PATTERNS = (
    "fetch(",
    "XMLHttpRequest",
    "WebSocket(",
    'src="http://',
    'src="https://',
    "src='http://",
    "src='https://",
)


def _text_files() -> list[Path]:
    files = [
        path
        for path in ROOT.iterdir()
        if path.is_file()
        and path.suffix in {".md", ".toml", ".yaml", ".yml", ".json", ".py"}
    ]
    for directory_name in SCAN_DIRECTORIES:
        directory = ROOT / directory_name
        if not directory.exists():
            continue
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and path.suffix not in {".pyc", ".png", ".jpg", ".jpeg"}
        )
    return sorted(files)


def main() -> int:
    failures: list[str] = []
    for path in _text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, secret_pattern in SECRET_PATTERNS.items():
            if secret_pattern.search(text):
                failures.append(f"{path.relative_to(ROOT)}: potential {label}")
    tracked_files = set(
        subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    )
    tracked_env_files = [
        name
        for name in tracked_files
        if Path(name).name.startswith(".env")
        and Path(name).name not in {".env.example", ".env.sample"}
    ]
    failures.extend(f"{name}: environment file must not be committed" for name in tracked_env_files)
    for path in (ROOT / "reports" / "v11").glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for html_pattern in NETWORK_HTML_PATTERNS:
            if html_pattern in text:
                failures.append(
                    f"{path.relative_to(ROOT)}: network-capable HTML ({html_pattern})"
                )
    execution_boundary = assert_all_execution_paths_forbidden()
    result = {
        "status": "passed" if not failures else "failed",
        "execution_boundary": execution_boundary,
        "failures": failures,
    }
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
