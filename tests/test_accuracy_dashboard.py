from pathlib import Path

from take_two_options.accuracy import MarketDataAccuracyReport
from take_two_options.accuracy_dashboard import build_accuracy_dashboard_artifact


def test_dashboard_prioritizes_opportunities_winners_and_architectures() -> None:
    report_path = (
        Path(__file__).parents[1]
        / "experiments"
        / "legacy"
        / "v9"
        / "reports"
        / "ttwo_v9_budget_report.json"
    )
    report = MarketDataAccuracyReport.model_validate_json(report_path.read_text(encoding="utf-8"))

    artifact = build_accuracy_dashboard_artifact(report, report_path=str(report_path))

    datasets = artifact["snapshot"]["datasets"]
    assert datasets["current_candidates"]
    assert datasets["historical_winners"]
    assert datasets["architectures"]
    assert all(row["outcome"] == "winner" for row in datasets["historical_winners"])
    long_call = next(
        row for row in datasets["current_candidates"] if row["strategy"] == "long_call"
    )
    assert "ACHETER 1 CALL (option d'achat)" in long_call["ticket_ibkr"]
    assert "ordre LMT ACHAT au DEBIT" in long_call["ticket_ibkr"]
    assert "Pourquoi:" in long_call["statut_et_blocage"]
    assert "TTWO monte assez vite" in long_call["scenario_gagnant"]
    assert "Test:" in long_call["preuves_et_risque"]
    assert len(datasets["budget_candidates"]) == 4
    single = next(
        row for row in datasets["budget_candidates"] if row["budget_plan_id"] == "single_long"
    )
    assert single["risk_eur"] <= 1_000
    assert "strike $250" in single["ticket_ibkr"]
    assert "strike $270" in single["ticket_ibkr"]
    assert "verifier la cotation IBKR live" in single["ticket_ibkr"]
    assert "au-dessus de $260.59" in single["scenario_gagnant"]
    assert "1/1 poches disponibles" in single["plan_et_budget"]
    blocks = [block["id"] for block in artifact["manifest"]["blocks"]]
    assert blocks[:5] == [
        "summary_metrics",
        "budget_candidates_block",
        "current_candidates_block",
        "historical_winners_block",
        "architecture_catalog_block",
    ]
