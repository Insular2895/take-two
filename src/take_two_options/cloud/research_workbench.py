"""Exhaustive, governed Phase M research for the Cloud workbench."""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import UTC, date, datetime
from functools import reduce
from math import gcd
from pathlib import Path

from take_two_options.budget import (
    FXAccountMode,
    FXExecutionCost,
    FXExecutionCostStatus,
    FXRate,
)
from take_two_options.candidate_generation.enumerator import enumerate_candidates
from take_two_options.candidate_generation.pruning import prune_candidate
from take_two_options.cloud.research_contracts import (
    AnalysisBudgetRequest,
    CandidateDetail,
    CandidateSummary,
    MarketDataMode,
    ResearchAnalysisResult,
)
from take_two_options.config.loader import load_prospective_budget_config
from take_two_options.decision.request import load_trade_request
from take_two_options.domain import ExerciseStyle, OptionType
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import (
    CompiledStrategyCandidate,
    MarketSnapshot,
    QuoteSnapshot,
)
from take_two_options.optimization.complexity import complexity_penalty
from take_two_options.optimization.pareto import pareto_rank
from take_two_options.phase_m_context import build_phase_m_decision_context
from take_two_options.quantitative.contracts import EvidenceLevel

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REQUEST = ROOT / "configs/trades/ttwo_gta6_1000eur.yaml"
DEFAULT_BUDGET_CONFIG = ROOT / "configs/phase_m/v2/ttwo_prospective_budget.yaml"
DEFAULT_KNOWLEDGE = ROOT / "research/knowledge_items"


def synthetic_demo_snapshot() -> MarketSnapshot:
    """Return an explicit synthetic chain; it is never represented as live data."""

    as_of = datetime(2026, 7, 25, 20, 0, tzinfo=UTC)
    spot = 240.0
    expirations = [date(2027, 3, 19), date(2027, 6, 18), date(2027, 11, 19)]
    strikes = list(range(200, 281, 10))
    quotes: list[QuoteSnapshot] = []
    for expiration in expirations:
        dte = (expiration - as_of.date()).days
        time_scale = math.sqrt(max(dte, 1) / 365)
        for strike in strikes:
            distance = abs(strike - spot)
            for option_type in (OptionType.CALL, OptionType.PUT):
                intrinsic = (
                    max(spot - strike, 0.0)
                    if option_type is OptionType.CALL
                    else max(strike - spot, 0.0)
                )
                time_value = max(1.5, 22 * time_scale * math.exp(-distance / 55))
                mid = intrinsic + time_value
                spread = max(0.20, min(1.80, mid * 0.06))
                bid = round(max(0.05, mid - spread / 2), 2)
                ask = round(max(bid, mid + spread / 2), 2)
                call_delta = max(0.05, min(0.95, 0.5 + (spot - strike) / 160))
                delta = call_delta if option_type is OptionType.CALL else call_delta - 1
                symbol = f"TTWO-{expiration:%Y%m%d}-{option_type.value[0].upper()}-{strike}"
                quotes.append(
                    QuoteSnapshot(
                        symbol=symbol,
                        expiration=expiration,
                        option_type=option_type,
                        exercise_style=ExerciseStyle.AMERICAN,
                        strike=float(strike),
                        bid=bid,
                        ask=ask,
                        volume=80 + (280 - abs(int(strike - spot) * 3)),
                        open_interest=400 + (400 - abs(int(strike - spot) * 5)),
                        implied_volatility=round(0.36 + distance / 2_000, 6),
                        delta=round(delta, 6),
                        quote_timestamp=as_of,
                        multiplier=100,
                        multiplier_status=EvidenceLevel.KNOWN,
                        contract_adjustment_status=EvidenceLevel.KNOWN,
                        deliverable_description="standard listed deliverable",
                        price_quality="modeled",
                        source_id="synthetic-demo-chain-v1",
                    )
                )
    return MarketSnapshot(
        snapshot_id="synthetic-demo-ttwo-2026-07-25-v1",
        ticker="TTWO",
        as_of=as_of,
        spot=spot,
        spot_timestamp=as_of,
        quote_quality="indicative",
        source_ids=["synthetic-demo-chain-v1"],
        quotes=quotes,
        available_expirations=expirations,
        data_warnings=[
            "SYNTHETIC_DEMO: modeled fixture only; no current or executable market quote.",
            "Greeks are simplified fixture values and must not be used for a trade decision.",
        ],
    )


def _market_snapshot(mode: MarketDataMode, governed_snapshot: Path | None) -> MarketSnapshot:
    if mode is MarketDataMode.SYNTHETIC_DEMO:
        return synthetic_demo_snapshot()
    if governed_snapshot is None:
        raise ValueError("LAST_GOVERNED_SNAPSHOT_NOT_CONFIGURED")
    return MarketSnapshot.model_validate_json(governed_snapshot.read_text(encoding="utf-8"))


def _quantity(candidate: CompiledStrategyCandidate) -> int:
    return reduce(gcd, (leg.quantity for leg in candidate.legs))


def _relative_spread(candidate: CompiledStrategyCandidate) -> float | None:
    spreads = []
    for leg in candidate.legs:
        if leg.quote.bid is None or leg.quote.ask is None:
            return None
        mid = (leg.quote.bid + leg.quote.ask) / 2
        if mid > 0:
            spreads.append((leg.quote.ask - leg.quote.bid) / mid)
    return max(spreads) if spreads else None


def _model_metric(candidate: CompiledStrategyCandidate, name: str) -> float | None:
    values = [float(getattr(metric, name)) for metric in candidate.evaluation.model_metrics]
    if not values:
        return None
    if name in {"cvar_95"}:
        return max(values)
    return min(values)


def _ticket(candidate: CompiledStrategyCandidate, snapshot: MarketSnapshot) -> dict[str, object]:
    """Immutable research economics ticket, explicitly non-executable."""

    return {
        "schema_version": "phase-m-cloud-research/1.0",
        "candidate_id": candidate.candidate_id,
        "snapshot_id": snapshot.snapshot_id,
        "phase_m_context_id": candidate.phase_m_context_id,
        "phase_m_context_hash": candidate.phase_m_context_hash,
        "economics": {
            "entry_debit_native": candidate.risk.entry_debit,
            "fees_native": candidate.risk.fees,
            "slippage_native": candidate.risk.slippage,
            "total_cost_native": candidate.risk.total_cost,
            "maximum_loss_native": candidate.risk.maximum_loss,
            "maximum_gain_native": candidate.risk.maximum_gain,
            "break_even_points": candidate.risk.break_even_points,
            "budget_diagnostics": (
                candidate.budget_diagnostics.model_dump(mode="json")
                if candidate.budget_diagnostics is not None
                else None
            ),
        },
        "legs": [
            {
                "symbol": leg.quote.symbol,
                "side": leg.side.value,
                "quantity": leg.quantity,
                "entry_price": leg.entry_price,
                "expiration": leg.quote.expiration.isoformat(),
                "strike": leg.quote.strike,
                "option_type": leg.quote.option_type.value,
                "multiplier": leg.quote.multiplier,
            }
            for leg in candidate.legs
        ],
        "safety": {"read_only": True, "transmit": False, "order_capability": "forbidden"},
    }


def _summary(
    candidate: CompiledStrategyCandidate,
    *,
    rank: int,
    request_as_of: date,
    snapshot: MarketSnapshot,
    reasons: list[str],
) -> CandidateSummary:
    expirations = sorted({leg.quote.expiration for leg in candidate.legs})
    diagnostics = candidate.budget_diagnostics
    deltas = [
        leg.side.sign * leg.quantity * (leg.quote.delta or 0.0)
        for leg in candidate.legs
        if leg.quote.delta is not None
    ]
    ivs = [leg.quote.implied_volatility for leg in candidate.legs if leg.quote.implied_volatility]
    signed_entry = -candidate.risk.total_cost
    if diagnostics is not None and diagnostics.fx_rate_to_policy_currency is not None:
        signed_entry *= diagnostics.fx_rate_to_policy_currency
    maximum_gain = candidate.risk.maximum_gain
    if (
        maximum_gain is not None
        and diagnostics is not None
        and diagnostics.fx_rate_to_policy_currency is not None
    ):
        maximum_gain *= diagnostics.fx_rate_to_policy_currency
    ticket = _ticket(candidate, snapshot)
    return CandidateSummary(
        candidate_id=candidate.candidate_id,
        architecture=candidate.architecture.value,
        recipe_id=candidate.recipe_id,
        strategy_name=candidate.recipe_id.removesuffix("-v1").replace("-", " ").title(),
        leg_summary=" | ".join(
            f"{leg.side.value.upper()} {leg.quantity}× {leg.quote.option_type.value.upper()} "
            f"{leg.quote.strike:g} {leg.quote.expiration.isoformat()}"
            for leg in candidate.legs
        ),
        engine_rank=rank,
        pareto_rank=candidate.pareto_rank,
        quantity=_quantity(candidate),
        leg_count=len(candidate.legs),
        expiration=" / ".join(item.isoformat() for item in expirations),
        common_expiry=len(expirations) == 1,
        dte=max((item - request_as_of).days for item in expirations),
        signed_entry_cash_flow=round(signed_entry, 4),
        entry_cash_flow_type=(
            "DEBIT" if signed_entry < 0 else "CREDIT" if signed_entry > 0 else "FLAT"
        ),
        capital_required=(diagnostics.effective_capital_requirement if diagnostics else None),
        maximum_loss=(diagnostics.maximum_loss if diagnostics else candidate.risk.maximum_loss),
        maximum_gain=(round(maximum_gain, 4) if maximum_gain is not None else None),
        break_even_points=candidate.risk.break_even_points,
        net_delta=round(sum(deltas), 6) if deltas else None,
        net_theta=None,
        average_implied_volatility=(round(sum(ivs) / len(ivs), 6) if ivs else None),
        maximum_relative_spread=_relative_spread(candidate),
        minimum_open_interest=min(
            (
                leg.quote.open_interest
                for leg in candidate.legs
                if leg.quote.open_interest is not None
            ),
            default=None,
        ),
        expected_pnl=candidate.evaluation.conservative_expected_pnl,
        probability_profit=_model_metric(candidate, "probability_profit"),
        cvar_95=_model_metric(candidate, "cvar_95"),
        distance_to_target_budget=(
            diagnostics.budget_delta_to_target if diagnostics is not None else None
        ),
        headroom_to_hard_maximum=(
            diagnostics.headroom_to_hard_ceiling if diagnostics is not None else None
        ),
        data_freshness="FRESH" if snapshot.snapshot_id.startswith("synthetic-demo-") else "UNKNOWN",
        budget_status=(diagnostics.budget_status.value if diagnostics else "UNKNOWN"),
        eligible=bool(diagnostics and diagnostics.eligible and not reasons),
        research_eligible=bool(diagnostics and diagnostics.research_eligible),
        paper_eligible=bool(diagnostics and diagnostics.paper_eligible and not reasons),
        pruned=bool(reasons),
        reason_codes=reasons,
        trade_economics_ticket_hash=stable_hash(ticket),
    )


def _detail(
    candidate: CompiledStrategyCandidate,
    summary: CandidateSummary,
    snapshot: MarketSnapshot,
) -> CandidateDetail:
    ticket = _ticket(candidate, snapshot)
    return CandidateDetail(
        candidate_id=candidate.candidate_id,
        engine_rank_method="HARD_VETO_PARETO_BUDGET_DISTANCE_V1",
        legs=[
            {
                "symbol": leg.quote.symbol,
                "side": leg.side.value,
                "quantity": leg.quantity,
                "option_type": leg.quote.option_type.value,
                "strike": leg.quote.strike,
                "expiration": leg.quote.expiration.isoformat(),
                "bid": leg.quote.bid,
                "ask": leg.quote.ask,
                "entry_price": leg.entry_price,
                "multiplier": leg.quote.multiplier,
                "delta": leg.quote.delta,
                "implied_volatility": leg.quote.implied_volatility,
                "open_interest": leg.quote.open_interest,
            }
            for leg in candidate.legs
        ],
        economics={
            "signed_entry_cash_flow": summary.signed_entry_cash_flow,
            "capital_required": summary.capital_required,
            "maximum_loss": summary.maximum_loss,
            "maximum_gain": summary.maximum_gain,
            "fees_native": candidate.risk.fees,
            "slippage_native": candidate.risk.slippage,
            "currency": "EUR",
        },
        payoff={
            "break_even_points": candidate.risk.break_even_points,
            "bounded": candidate.risk.bounded,
            "flat_spots": None,
        },
        time_decay={
            "net_theta": None,
            "theta_per_capital_day": None,
            "flat_spot_1d": None,
            "flat_spot_7d": None,
            "flat_spot_30d": None,
            "flat_spot_60d": None,
            "flat_spot_90d": None,
            "status": "N/A — canonical repricing was not run for this exhaustive summary job",
        },
        scenario_matrix={
            "status": "N/A — no canonical spot × time × IV matrix was generated",
            "browser_repricing": False,
        },
        volatility={
            "current_average_iv": summary.average_implied_volatility,
            "entry_iv": None,
            "stress_scenarios": None,
            "status": "SYNTHETIC_DEMO inputs are illustrative",
        },
        distribution={
            "expected_pnl": summary.expected_pnl,
            "probability_profit": summary.probability_profit,
            "var_95": summary.var_95,
            "cvar_95": summary.cvar_95,
            "status": "N/A — no valid probability model was run",
        },
        scores={
            "opportunity": None,
            "risk": None,
            "evidence": None,
            "model_agreement": None,
            "execution_quality": None,
            "composite_score": None,
            "status": "N/A — historical five-score formulas were not invoked or changed",
        },
        budget_diagnostics=(
            candidate.budget_diagnostics.model_dump(mode="json")
            if candidate.budget_diagnostics is not None
            else None
        ),
        lifecycle_capital_requirement=(
            candidate.lifecycle_capital_requirement.model_dump(mode="json")
            if candidate.lifecycle_capital_requirement is not None
            else None
        ),
        assumptions=candidate.assumptions,
        uncertainties=candidate.uncertainties,
        limitations=[
            "Research result only; it is not financial advice or an executable quote.",
            "Missing probability, PnL, CVaR, theta, and five-score values remain N/A.",
            "Synthetic leg quotes do not prove a simultaneous combo fill.",
        ],
        explanation=[
            f"Engine rank {summary.engine_rank} follows hard vetoes, Pareto rank, "
            "budget distance, then candidate ID.",
            f"Budget status is {summary.budget_status}; "
            f"paper eligibility is {summary.paper_eligible}.",
        ],
        phase_m_context_id=candidate.phase_m_context_id or "",
        phase_m_context_hash=candidate.phase_m_context_hash or "",
        trade_economics_ticket=ticket,
    )


def _ranking_key(candidate: CompiledStrategyCandidate, target: float) -> tuple[object, ...]:
    diagnostics = candidate.budget_diagnostics
    reasons = prune_candidate(candidate)
    capital = diagnostics.effective_capital_requirement if diagnostics else None
    return (
        bool(reasons),
        not bool(diagnostics and diagnostics.paper_eligible),
        candidate.pareto_rank or 1_000_000,
        abs((capital if capital is not None else float("inf")) - target),
        candidate.risk.maximum_loss,
        candidate.candidate_id,
    )


def run_research_analysis(
    *,
    analysis_request_id: str,
    budget_request: AnalysisBudgetRequest,
    governed_snapshot: Path | None = None,
) -> ResearchAnalysisResult:
    """Enumerate and retain the complete admitted catalog/request universe."""

    snapshot = _market_snapshot(budget_request.market_data_mode, governed_snapshot)
    request = load_trade_request(DEFAULT_REQUEST)
    base_config = load_prospective_budget_config(DEFAULT_BUDGET_CONFIG)
    policy = budget_request.apply_to(base_config.budget_policy)
    config = base_config.model_copy(update={"budget_policy": policy})
    evidence_time = min(snapshot.as_of, datetime(2026, 7, 25, 20, 0, tzinfo=UTC))
    fx = FXRate(
        source_currency="USD",
        policy_currency="EUR",
        rate_to_policy_currency=1 / 1.1435,
        timestamp=evidence_time,
        source="synthetic-demo-fx-v1",
    )
    fx_cost = FXExecutionCost(
        mode=FXAccountMode.CONVERT_AT_ENTRY_AND_EXIT,
        status=FXExecutionCostStatus.ESTIMATED,
        cost_basis_points=10.0,
        source="synthetic-demo-fx-cost-v1",
        timestamp=evidence_time,
        assumptions=["Synthetic 10 bps fixture; account-specific cost is not validated."],
    )
    context = build_phase_m_decision_context(
        config,
        prospective_config_source="configs/phase_m/v2/ttwo_prospective_budget.yaml",
        fx_rate=fx,
        fx_execution_cost=fx_cost,
        created_at=evidence_time,
        source_ids=[snapshot.snapshot_id],
    )
    catalog = compile_knowledge(load_knowledge(DEFAULT_KNOWLEDGE))
    enumeration = enumerate_candidates(
        catalog,
        request,
        snapshot,
        budget_policy=policy,
        fx=fx,
        fx_cost=fx_cost,
        mixed_expiry_lifecycle=config.mixed_expiry_lifecycle,
        phase_m_context_id=context.context_id,
        phase_m_context_hash=context.context_hash,
    )
    for candidate in enumeration.candidates:
        candidate.evaluation.complexity_penalty = complexity_penalty(candidate)
    eligible_for_pareto = [
        candidate for candidate in enumeration.candidates if not prune_candidate(candidate)
    ]
    pareto_rank(eligible_for_pareto)
    ranked = sorted(
        enumeration.candidates,
        key=lambda candidate: _ranking_key(candidate, budget_request.target_budget),
    )
    summaries: list[CandidateSummary] = []
    details: list[CandidateDetail] = []
    for rank, candidate in enumerate(ranked, start=1):
        reasons = prune_candidate(candidate)
        candidate.status = "pruned" if reasons else "admissible"
        summary = _summary(
            candidate,
            rank=rank,
            request_as_of=request.as_of,
            snapshot=snapshot,
            reasons=reasons,
        )
        summaries.append(summary)
        details.append(_detail(candidate, summary, snapshot))

    paper = [item for item in summaries if item.paper_eligible]
    research = [item for item in summaries if item.research_eligible]
    by_architecture: dict[str, str] = {}
    for item in summaries:
        by_architecture.setdefault(item.architecture, item.candidate_id)
    status = "COMPLETE" if paper else "NO_TRADE"
    no_trade_reasons = [] if paper else ["NO_CANDIDATE_PASSED_PAPER_ELIGIBILITY_GATES"]
    return ResearchAnalysisResult(
        analysis_request_id=analysis_request_id,
        status=status,
        verdict="RESEARCH_CANDIDATES_AVAILABLE" if paper else "NO_TRADE",
        generated_at=datetime.now(UTC),
        market_data_mode=budget_request.market_data_mode,
        snapshot_id=snapshot.snapshot_id,
        snapshot_as_of=snapshot.as_of,
        snapshot_hash=stable_hash(snapshot),
        catalog_hash=catalog.knowledge_hash,
        config_hash=context.prospective_config_hash,
        phase_m_context_id=context.context_id,
        phase_m_context_hash=context.context_hash,
        total_generated=len(summaries),
        total_pruned=sum(item.pruned for item in summaries),
        total_research_eligible=len(research),
        total_paper_eligible=len(paper),
        combinations_by_architecture=enumeration.combinations_by_architecture,
        best_overall_ids=[item.candidate_id for item in summaries[:25]],
        best_by_architecture=by_architecture,
        no_trade_reasons=no_trade_reasons,
        warnings=[*snapshot.data_warnings, *enumeration.warnings],
        summaries=summaries,
        details=details,
        safety={"read_only": True, "transmit": False, "order_capability": "forbidden"},
    )


def batches(values: list[object], size: int = 20) -> Iterable[list[object]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]
