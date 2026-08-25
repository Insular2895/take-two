from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

from take_two_options.candidate_generation.enumerator import enumerate_candidates
from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.candidate_generation.pruning import prune_candidate
from take_two_options.decision.request import load_trade_request
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import Architecture, MarketSnapshot
from take_two_options.optimization.pareto import pareto_rank
from take_two_options.quantitative.numerical_validation import NumericalStatus, compare_values
from take_two_options.reporting.evidence_grade import (
    ComponentEvidenceClaim,
    EstimateWithUncertainty,
    FinalDecisionEvidenceReport,
    ProbabilityWithUncertainty,
    calculate_decision_evidence_grade,
    final_decision_markdown,
)

ROOT = Path(__file__).resolve().parents[1]


def test_xyz_fixture_exercises_symbol_agnostic_quantitative_core() -> None:
    snapshot = MarketSnapshot.model_validate_json(
        (ROOT / "fixtures/portability/xyz_option_chain.json").read_text(encoding="utf-8")
    )
    request = load_trade_request(ROOT / "configs/trades/ttwo_gta6_1000eur.yaml").model_copy(
        update={
            "request_id": "xyz-portability-v1",
            "ticker": "XYZ",
            "as_of": date(2026, 1, 2),
            "currency": "USD",
            "budget": 2_000.0,
            "maximum_loss": 2_000.0,
            "horizon_min_days": 300,
            "horizon_max_days": 400,
            "allowed_structures": [
                Architecture.LONG_CALL,
                Architecture.BULL_CALL_SPREAD,
            ],
            "fx_rate_to_usd": None,
            "fx_rate_as_of": None,
        }
    )
    catalog = compile_knowledge(load_knowledge(ROOT / "research/knowledge_items"))
    catalog = catalog.model_copy(
        update={
            "recipes": [
                recipe
                for recipe in catalog.recipes
                if recipe.architecture in request.allowed_structures
            ]
        }
    )

    enumeration = enumerate_candidates(catalog, request, snapshot)
    admissible = [
        candidate for candidate in enumeration.candidates if not prune_candidate(candidate)
    ]
    assert admissible
    assert all(leg.quote.symbol.startswith("XYZ") for item in admissible for leg in item.legs)
    assert terminal_payoff(admissible[0].legs, 150.0) > 0
    assert admissible[0].risk.maximum_loss > 0
    assert pareto_rank(admissible)

    numerical = compare_values(
        reference_name="identity",
        candidate_name="xyz",
        reference_value=1.0,
        candidate_value=1.0,
        absolute_tolerance=0.0,
        relative_tolerance=0.0,
    )
    assert numerical.status is NumericalStatus.PASSED

    evidence = calculate_decision_evidence_grade(
        [ComponentEvidenceClaim(component_id="xyz-core", implemented=True, tests_passed=True)]
    )
    report = FinalDecisionEvidenceReport(
        report_id="xyz-portability-v1",
        ticker="XYZ",
        as_of=datetime(2026, 1, 2, 20, tzinfo=UTC),
        decision_status="BLOCKED",
        selected_candidate_id=admissible[0].candidate_id,
        evidence_grade=evidence,
        estimates=[
            EstimateWithUncertainty(
                estimate_id="max-loss",
                label="Maximum loss",
                central=admissible[0].risk.maximum_loss,
                interval=(admissible[0].risk.maximum_loss, admissible[0].risk.maximum_loss),
                unit="USD",
                measure="not_applicable",
                uncertainty_diagnostic="Deterministic contract payoff from a synthetic fixture.",
                source_ids=["xyz-synthetic-fixture"],
            )
        ],
        probabilities=[
            ProbabilityWithUncertainty(
                probability_id="not-estimated",
                label="Probability of profit",
                central=None,
                interval=None,
                origin="unavailable",
                uncertainty_diagnostic="No empirical XYZ distribution exists.",
                source_ids=["xyz-synthetic-fixture"],
            )
        ],
        assumptions=["Synthetic XYZ portability fixture."],
        favorable_scenarios=["Underlying appreciates."],
        failure_scenarios=["Option expires without value."],
        model_risks=["No empirical calibration."],
        data_limits=["Fixture-only input."],
        ranking_reasons=["Structural test only."],
        no_trade_reasons=["Synthetic input cannot support a financial decision."],
        source_ids=["xyz-synthetic-fixture"],
        synthetic_or_fixture_input=True,
    )
    assert final_decision_markdown(report).startswith("# XYZ ")
    assert report.order_capability == "forbidden"
