from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from take_two_options.quantitative.historical_surfaces import (
    HistoricalSurfaceQuote,
    HistoricalSurfaceReport,
    QuoteUse,
    validate_surface_history,
)

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = datetime(2026, 1, 5, 21, tzinfo=UTC)


def _quotes() -> list[HistoricalSurfaceQuote]:
    output = []
    for expiry, maturity, base in (("e1", 0.25, 0.30), ("e2", 0.50, 0.32)):
        for index, k in enumerate((-0.4, -0.2, 0.0, 0.2, 0.4)):
            output.append(
                HistoricalSurfaceQuote(
                    snapshot_id="s1",
                    expiration_id=expiry,
                    maturity_years=maturity,
                    log_forward_moneyness=k,
                    implied_volatility=base + 0.03 * k * k,
                    available_at=CUTOFF - timedelta(minutes=1),
                    decision_cutoff=CUTOFF,
                    use=QuoteUse.INTERPOLATED if index == 1 else QuoteUse.OBSERVED,
                    source_id="synthetic-fixture",
                )
            )
    return output


def test_surface_history_fits_slices_and_marks_synthetic_boundary() -> None:
    report = validate_surface_history(
        _quotes(),
        ticker="XYZ",
        dataset_hash="a" * 64,
        synthetic=True,
        license_authorized=True,
    )
    assert report.status == "FIXTURE_ONLY_NOT_VALIDATED"
    assert len(report.snapshots[0].slices) == 2
    assert report.snapshots[0].interpolated_quotes == 2
    assert report.holdout_used is False
    assert not report.heston_gate.eligible


def test_post_cutoff_quote_is_excluded_and_visible() -> None:
    quotes = _quotes()
    quotes[0] = quotes[0].model_copy(update={"available_at": CUTOFF + timedelta(minutes=1)})
    report = validate_surface_history(
        quotes,
        ticker="XYZ",
        dataset_hash="b" * 64,
        synthetic=True,
        license_authorized=True,
    )
    assert report.snapshots[0].post_cutoff_quotes_excluded == 1
    assert report.snapshots[0].status == "BLOCKED_INSUFFICIENT_DATA"


def test_committed_tt_gets_no_fabricated_surface_or_heston_parameters() -> None:
    report = HistoricalSurfaceReport.model_validate_json(
        (ROOT / "reports/pre_opra/historical_surfaces_2026-08-08.json").read_text()
    )
    assert report.status == "BLOCKED_MISSING_GOVERNED_INPUTS"
    assert report.snapshots == []
    assert not report.heston_gate.eligible
    assert "risk-free curve" in " ".join(report.missing_inputs)
