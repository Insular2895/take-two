"""Decision reporting and legacy compatibility exports."""

from take_two_options.reporting.legacy_reporting import (
    render_decision_journal,
    render_json,
    render_markdown,
)

__all__ = ["render_decision_journal", "render_json", "render_markdown"]
