from take_two_options.domain import CandidateStatus, MarketDataBundle
from take_two_options.engine import analyze_bundle
from take_two_options.reporting import render_decision_journal, render_json, render_markdown


def test_complete_fixture_compares_required_alternatives(bundle: MarketDataBundle) -> None:
    report = analyze_bundle(bundle)
    kinds = {candidate.kind.value for candidate in report.candidates}

    assert {"no_trade", "stock", "long_call", "long_put"} <= kinds
    assert {"bull_call_spread", "bear_put_spread"} <= kinds
    assert all(candidate.status is not CandidateStatus.BLOCKED for candidate in report.candidates)
    assert report.decision_posture == "read_only_research"
    assert report.pareto_candidate_ids
    assert set(report.pareto_candidate_ids) <= {candidate.id for candidate in report.candidates}


def test_report_outputs_are_serializable_and_execution_free(bundle: MarketDataBundle) -> None:
    report = analyze_bundle(bundle)
    json_output = render_json(report)
    markdown_output = render_markdown(report)
    journal = render_decision_journal(report)

    assert '"report_id": "TTWO-RESEARCH-20260718T120000Z"' in json_output
    assert "live_order_ready" not in json_output
    assert "not an investment recommendation" in markdown_output
    assert "TTWO  270115C00260000" in markdown_output
    assert "Score components" in markdown_output
    assert "Pareto research set" in markdown_output
    assert "Order capability: `forbidden`" in journal


def test_fundamental_direction_changes_fit_not_option_mechanics(bundle: MarketDataBundle) -> None:
    bullish = analyze_bundle(bundle.model_copy(deep=True))
    bearish_bundle = bundle.model_copy(deep=True)
    bearish_bundle.fundamental.direction = "bearish"
    bearish = analyze_bundle(bearish_bundle)
    bullish_call = next(item for item in bullish.candidates if item.id == "ttwo-long-call")
    bearish_call = next(item for item in bearish.candidates if item.id == "ttwo-long-call")

    assert bullish_call.risk_metrics == bearish_call.risk_metrics
    assert bullish_call.score is not None
    assert bearish_call.score is not None
    assert bullish_call.score.thesis_fit > bearish_call.score.thesis_fit
