from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from take_two_options.execution_revalidation import (
    ComboGuaranteeMode,
    ExecutionEconomicsSnapshot,
    ExecutionLegIdentity,
    ExecutionMarketSnapshot,
    ExecutionRevalidationService,
    FiveScoreSnapshot,
    GreekVector,
    MarketDataType,
    MaterialExecutionDriftPolicy,
    RevalidationVerdict,
    SelectedExecutionContext,
    canonical_hash,
)

NOW = datetime(2026, 9, 19, 14, 30, tzinfo=UTC)
HASH = "a" * 64


def leg(*, currency: str = "EUR") -> ExecutionLegIdentity:
    return ExecutionLegIdentity(
        con_id=900001,
        local_symbol="TTWO  270115C00250000",
        trading_class="TTWO",
        expiration="20270115",
        strike=250,
        right="C",
        multiplier=100,
        currency=currency,
        exchange="SMART",
        ratio=1,
        application_action="BUY_TO_OPEN",
        wire_action="BUY",
    )


def market(
    *,
    spot: float = 240,
    iv: float = 0.45,
    captured_at: datetime = NOW,
    fresh: bool = True,
    market_data_type: MarketDataType = MarketDataType.LIVE,
    combo: bool = True,
    fx: bool = False,
) -> ExecutionMarketSnapshot:
    return ExecutionMarketSnapshot(
        snapshot_id=f"snapshot-{spot}-{iv}-{captured_at.isoformat()}",
        captured_at=captured_at,
        ticker="TTWO",
        spot=spot,
        market_data_type=market_data_type,
        underlying_timestamp=captured_at,
        leg_timestamps={900001: captured_at},
        leg_bid_ask={900001: (5.10, 5.40)},
        leg_implied_volatility={900001: iv},
        provider_leg_greeks={900001: None},
        combo_bid=5.10 if combo else None,
        combo_ask=5.40 if combo else None,
        combo_timestamp=captured_at if combo else None,
        synthetic_combo_bid=5.10,
        synthetic_combo_ask=5.40,
        signed_price_convention_verified=True,
        fx_rate_to_eur=0.85 if fx else None,
        fx_timestamp=captured_at if fx else None,
        rate_curve_hash=HASH,
        dividend_input_hash=HASH,
        open_interest={900001: 500},
        volume={900001: 20},
        bid_size={900001: 10},
        ask_size={900001: 12},
        trading_hours="20260919:0930-20260919:1600",
        liquid_hours="20260919:0930-20260919:1600",
        time_zone_id="US/Eastern",
        quote_age_seconds=1,
        underlying_fresh=fresh,
        option_leg_freshness={900001: fresh},
        bag_fresh=fresh,
        fx_fresh=fresh if fx else None,
        rate_inputs_fresh=fresh,
        dividend_inputs_fresh=fresh,
        required_inputs_fresh=fresh,
    )


def economics(
    *,
    limit: float,
    greeks: GreekVector | None = None,
    capital: float | None = None,
    expected_pnl: float | None = 200,
) -> ExecutionEconomicsSnapshot:
    cost = limit * 100
    capital_value = cost if capital is None else capital
    return ExecutionEconomicsSnapshot(
        source_engine_version="canonical-economics-test/1",
        proposed_combo_limit=limit,
        cash_flow_type="DEBIT",
        signed_entry_cash_flow=-cost,
        expected_commissions=2.0,
        slippage_estimate=1.0,
        fx_transaction_cost=0.0,
        capital_required=capital_value,
        broker_buying_power_requirement=None,
        max_loss=capital_value,
        max_profit=2_000 - cost,
        breakevens=(250 + limit,),
        expected_pnl=expected_pnl,
        expected_return=None if expected_pnl is None else expected_pnl / capital_value,
        probability_profit=0.6,
        probability_loss=0.4,
        var_95=400,
        cvar_95=500,
        return_on_capital=None if expected_pnl is None else expected_pnl / capital_value,
        return_on_risk=None if expected_pnl is None else expected_pnl / capital_value,
        theta_per_capital_day=-0.002,
        greeks=greeks or GreekVector(delta=0.5, gamma=0.02, vega=0.3, theta=-0.04),
        flat_spot_pnl={"+1d": -4.0, "+7d": -25.0, "+30d": -100.0},
        spot_time_iv_matrix_hash=HASH,
        volatility_shock_hash=HASH,
        event_crush_hash=HASH,
        touch_probabilities={"upper": 0.4},
        liquidity_diagnostics={"spread": 0.30},
        five_scores=FiveScoreSnapshot(
            opportunity=60,
            risk=55,
            evidence=50,
            model_agreement=45,
            execution_quality=40,
            formula_version="five-score-v1",
        ),
    )


def context(
    *,
    original_market: ExecutionMarketSnapshot | None = None,
    currency: str = "EUR",
) -> SelectedExecutionContext:
    original_market = original_market or market()
    legs = (leg(currency=currency),)
    identity = {
        "structure_type": "LONG_CALL",
        "quantity": 1,
        "legs": [item.model_dump(mode="json") for item in legs],
    }
    return SelectedExecutionContext(
        original_analysis_id="analysis-original",
        candidate_id="cand-original",
        selection_id="selection-original",
        dossier_id="planned-dossier-original",
        original_trade_economics_ticket_hash="b" * 64,
        original_market_snapshot_hash=original_market.evidence_hash,
        git_commit="f2bb94d",
        config_hash="c" * 64,
        structure_type="LONG_CALL",
        quantity=1,
        policy_currency="EUR",
        legs=legs,
        structure_hash=canonical_hash(identity),
        original_market=original_market,
        original_economics=economics(limit=5.25),
        analysis_hard_ceiling_eur=1_500,
    )


@dataclass
class Provider:
    value: ExecutionMarketSnapshot

    def refresh(self, _context: SelectedExecutionContext) -> ExecutionMarketSnapshot:
        return self.value


class Engine:
    def __init__(self, *, capital: float | None = None, expected_pnl: float | None = 200) -> None:
        self.calls = 0
        self.capital = capital
        self.expected_pnl = expected_pnl

    def reprice_same_structure(
        self,
        execution_context: SelectedExecutionContext,
        current_market: ExecutionMarketSnapshot,
        proposed_limit: float,
    ) -> ExecutionEconomicsSnapshot:
        self.calls += 1
        original = execution_context.original_market
        changed = (
            current_market.spot != original.spot
            or current_market.leg_implied_volatility != original.leg_implied_volatility
            or current_market.captured_at != original.captured_at
        )
        greek = GreekVector(
            delta=0.55,
            gamma=0.018,
            vega=0.34,
            theta=-0.045,
        ) if changed else execution_context.original_economics.greeks
        return economics(
            limit=proposed_limit,
            greeks=greek,
            capital=self.capital,
            expected_pnl=self.expected_pnl,
        )


def no_policy() -> MaterialExecutionDriftPolicy:
    return MaterialExecutionDriftPolicy(policy_version="UNAPPROVED/1")


def configured_policy(**changes: Any) -> MaterialExecutionDriftPolicy:
    values: dict[str, Any] = {
        "policy_version": "TEST/1",
        "max_expected_pnl_deterioration": 1_000,
        "max_spot_move_fraction": 1,
    }
    values.update(changes)
    return MaterialExecutionDriftPolicy(**values)


def ticket_for(
    current_market: ExecutionMarketSnapshot,
    *,
    execution_context: SelectedExecutionContext | None = None,
    engine: Engine | None = None,
    limit: float = 5.30,
    tick: float | None = 0.05,
    policy: MaterialExecutionDriftPolicy | None = None,
    is_reprice: bool = True,
) -> tuple[Any, Engine]:
    used_engine = engine or Engine()
    service = ExecutionRevalidationService(Provider(current_market), used_engine)
    return (
        service.build_ticket(
            execution_context or context(),
            proposed_limit=limit,
            valid_tick=tick,
            drift_policy=policy or no_policy(),
            now=NOW + timedelta(seconds=2),
            is_reprice=is_reprice,
            previous_ticket_id="execution-revalidation-1111111111111111" if is_reprice else None,
            broker_combo_guarantee_mode=ComboGuaranteeMode.GUARANTEED,
        ),
        used_engine,
    )


def test_same_market_limit_change_keeps_greeks_but_recomputes_entry_economics() -> None:
    original = market()
    execution_context = context(original_market=original)
    ticket, engine = ticket_for(original, execution_context=execution_context)
    assert engine.calls == 1
    assert ticket.proposed_execution_economics.greeks == execution_context.original_economics.greeks
    assert (
        ticket.proposed_execution_economics.max_loss
        != execution_context.original_economics.max_loss
    )
    assert ticket.verdict is RevalidationVerdict.REVIEW_REQUIRED


def test_spot_iv_and_time_changes_recompute_greeks_and_economics() -> None:
    for changed in (
        market(spot=245),
        market(iv=0.50),
        market(captured_at=NOW + timedelta(minutes=1)),
    ):
        ticket, engine = ticket_for(changed, policy=configured_policy())
        assert engine.calls == 1
        assert ticket.proposed_execution_economics.greeks.delta == 0.55
        assert ticket.verdict is RevalidationVerdict.EXECUTABLE_REPRICE_PROPOSAL


def test_economic_deterioration_requires_fresh_universe_analysis() -> None:
    ticket, _ = ticket_for(
        market(spot=230),
        engine=Engine(expected_pnl=-500),
        policy=configured_policy(max_expected_pnl_deterioration=100),
    )
    assert ticket.verdict is RevalidationVerdict.REANALYSIS_REQUIRED
    assert ticket.reanalysis_request is not None

    class Rerunner:
        def rerun(self, request: Any, current_market: Any) -> dict[str, Any]:
            return {
                "original_candidate_id": request.original_candidate_id,
                "current_best_candidate_id": "cand-new-dominant",
                "rank_changes": {"cand-original": [1, 3]},
                "original_artifacts_preserved": True,
                "snapshot": current_market.evidence_hash,
            }

    result = ExecutionRevalidationService.rerun_universe_if_required(ticket, Rerunner())
    assert result["current_best_candidate_id"] == "cand-new-dominant"
    assert result["rank_changes"]["cand-original"] == [1, 3]


def test_budget_tick_and_freshness_fail_closed() -> None:
    over_budget, _ = ticket_for(
        market(),
        engine=Engine(capital=1_500.01),
        policy=configured_policy(),
    )
    assert "HARD_BUDGET_EXCEEDED" in over_budget.blockers
    assert over_budget.verdict is RevalidationVerdict.BLOCKED

    invalid_tick, _ = ticket_for(market(), limit=5.32, policy=configured_policy())
    assert "INVALID_MARKET_RULE_TICK" in invalid_tick.blockers

    missing_bag, _ = ticket_for(market(combo=False), policy=configured_policy())
    assert "MISSING_BAG_QUOTE" in missing_bag.blockers

    stale, _ = ticket_for(market(fresh=False), policy=configured_policy())
    assert "REPRICE_UNAVAILABLE_DATA_STALE" in stale.blockers

    delayed, _ = ticket_for(
        market(market_data_type=MarketDataType.DELAYED),
        policy=configured_policy(),
    )
    assert "MARKET_DATA_NOT_LIVE" in delayed.blockers


def test_fx_is_required_only_for_cross_currency_execution() -> None:
    usd_context = context(currency="USD")
    missing_fx, _ = ticket_for(
        market(fx=False),
        execution_context=usd_context,
        policy=configured_policy(),
    )
    assert "FX_EVIDENCE_REQUIRED" in missing_fx.blockers

    with_fx, _ = ticket_for(
        market(fx=True),
        execution_context=usd_context,
        policy=configured_policy(),
    )
    assert "FX_EVIDENCE_REQUIRED" not in with_fx.blockers

    same_currency, _ = ticket_for(market(fx=False), policy=configured_policy())
    assert "FX_EVIDENCE_REQUIRED" not in same_currency.blockers


def test_component_freshness_cannot_hide_behind_fresh_sibling_quotes() -> None:
    baseline = market()
    stale_underlying, _ = ticket_for(
        baseline.model_copy(update={"underlying_fresh": False}),
        policy=configured_policy(),
    )
    assert "UNDERLYING_QUOTE_STALE" in stale_underlying.blockers

    stale_leg, _ = ticket_for(
        baseline.model_copy(update={"option_leg_freshness": {900001: False}}),
        policy=configured_policy(),
    )
    assert "OPTION_LEG_QUOTE_STALE" in stale_leg.blockers

    stale_bag, _ = ticket_for(
        baseline.model_copy(update={"bag_fresh": False}),
        policy=configured_policy(),
    )
    assert "BAG_QUOTE_STALE" in stale_bag.blockers


def test_cross_currency_stale_fx_blocks_but_same_currency_does_not() -> None:
    stale_fx = market(fx=True).model_copy(update={"fx_fresh": False})
    usd_ticket, _ = ticket_for(
        stale_fx,
        execution_context=context(currency="USD"),
        policy=configured_policy(),
    )
    assert "FX_EVIDENCE_REQUIRED" in usd_ticket.blockers

    eur_ticket, _ = ticket_for(stale_fx, policy=configured_policy())
    assert "FX_EVIDENCE_REQUIRED" not in eur_ticket.blockers


def test_market_snapshot_must_cover_exactly_every_selected_leg() -> None:
    incomplete = market().model_copy(
        update={"provider_leg_greeks": {900002: None}},
    )
    ticket, _ = ticket_for(incomplete, policy=configured_policy())
    assert "OPTION_LEG_MARKET_COVERAGE_MISMATCH" in ticket.blockers
    assert ticket.verdict is RevalidationVerdict.BLOCKED


def test_hard_blocker_takes_priority_over_material_drift() -> None:
    stale_and_drifted = market(spot=230, fresh=False)
    ticket, _ = ticket_for(
        stale_and_drifted,
        engine=Engine(expected_pnl=-500),
        policy=configured_policy(max_expected_pnl_deterioration=100),
    )
    assert ticket.material_drift.status.value == "MATERIAL_DRIFT"
    assert ticket.verdict is RevalidationVerdict.BLOCKED
    assert ticket.reanalysis_request is None


def test_iv_regime_and_five_score_drift_are_explicit_policy_inputs() -> None:
    class ScoreDriftEngine(Engine):
        def reprice_same_structure(
            self,
            execution_context: SelectedExecutionContext,
            current_market: ExecutionMarketSnapshot,
            proposed_limit: float,
        ) -> ExecutionEconomicsSnapshot:
            value = super().reprice_same_structure(
                execution_context,
                current_market,
                proposed_limit,
            )
            return value.model_copy(
                update={
                    "five_scores": value.five_scores.model_copy(
                        update={"execution_quality": 20},
                    ),
                },
            )

    ticket, _ = ticket_for(
        market(iv=0.50),
        engine=ScoreDriftEngine(),
        policy=configured_policy(
            max_leg_iv_absolute_change=0.01,
            max_five_score_deterioration=10,
            max_execution_quality_deterioration=10,
        ),
    )
    assert ticket.verdict is RevalidationVerdict.REANALYSIS_REQUIRED
    assert set(ticket.material_drift.breached_metrics) >= {
        "maximum_leg_iv_absolute_change",
        "maximum_five_score_deterioration",
        "execution_quality_deterioration",
    }
    assert ticket.original_market == context().original_market
