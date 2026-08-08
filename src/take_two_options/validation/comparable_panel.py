"""Build a point-in-time comparable TTWO strategy panel from private EOD quotes."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from datetime import UTC, date, datetime
from statistics import fmean
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import PositionSide, StrictModel
from take_two_options.historical_data.market_context import MarketContextDataset, canonical_hash
from take_two_options.historical_data.option_observations import HistoricalOptionObservation
from take_two_options.validation.baseline_comparison import (
    MANDATORY_STRATEGIES,
    ComparableStrategy,
    StrategyReturnSeries,
)


class PanelLeg(StrictModel):
    option_symbol: str
    side: PositionSide
    strike: float
    expiration: date
    signal_implied_volatility: float | None
    signal_delta: float | None


class PanelOutcome(StrictModel):
    strategy: ComparableStrategy
    gross_return: float
    net_return: float = Field(ge=-1)
    transaction_cost_eur: float = Field(ge=0)
    deployed_capital_eur: float = Field(ge=0)
    maximum_loss_eur: float = Field(ge=0)
    quantity: int = Field(ge=0)
    selected_rule: str
    legs: list[PanelLeg]


class ComparablePanelObservation(StrictModel):
    observation_id: str
    signal_date: date
    decision_cutoff: datetime
    entry_date: date
    exit_date: date
    option_target_dte: int = Field(gt=0)
    signal_momentum_20: float
    signal_realized_volatility_20: float = Field(ge=0)
    outcomes: list[PanelOutcome]

    @model_validator(mode="after")
    def enforce_comparability(self) -> ComparablePanelObservation:
        if not self.signal_date < self.entry_date < self.exit_date:
            raise ValueError("panel dates must satisfy signal < entry < exit")
        if {outcome.strategy for outcome in self.outcomes} != set(MANDATORY_STRATEGIES):
            raise ValueError("each panel observation must include every mandatory strategy")
        return self


class ComparablePanelDataset(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    dataset_id: str
    ticker: Literal["TTWO"] = "TTWO"
    generated_at: datetime
    observations: list[ComparablePanelObservation] = Field(min_length=4)
    source_hashes: dict[str, str]
    frozen_rules: dict[str, str | float | int]
    retrospective_coverage_filter: Literal[True] = True
    final_holdout_used: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("panel generated_at must be timezone-aware")
        return value.astimezone(UTC)

    @property
    def dataset_hash(self) -> str:
        return canonical_hash(self.model_dump(mode="json"))


class ComparablePanelSettings(StrictModel):
    full_chain_min_quotes: int = Field(default=100, ge=20)
    target_dte: int = Field(default=21, ge=7, le=365)
    fixed_delta_target: float = Field(default=0.35, gt=0, lt=1)
    bull_spread_width_pct: float = Field(default=0.10, gt=0, le=0.50)
    maximum_relative_spread: float = Field(default=0.30, gt=0, le=2)
    minimum_open_interest: float = Field(default=20, ge=0)
    capital_eur: float = Field(default=1000, gt=0)
    maximum_contracts: int = Field(default=4, ge=1)
    commission_per_contract_side: float = Field(default=0.65, ge=0)
    slippage_per_contract_side: float = Field(default=0.05, ge=0)
    share_round_trip_cost_fraction: float = Field(default=0.002, ge=0, le=0.10)
    random_draws: int = Field(default=25, ge=5, le=1000)
    seed: int = 20_260_808
    v10_momentum_gate: float = Field(default=-0.05, ge=-1, le=1)
    v10_high_momentum: float = Field(default=0.05, ge=-1, le=1)
    v10_high_volatility: float = Field(default=0.40, gt=0, le=5)


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _bsm_call(spot: float, strike: float, time_years: float, rate: float, sigma: float) -> float:
    root_time = math.sqrt(time_years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * time_years) / (sigma * root_time)
    d2 = d1 - sigma * root_time
    return spot * _normal_cdf(d1) - strike * math.exp(-rate * time_years) * _normal_cdf(d2)


def implied_volatility_and_delta(
    *, spot: float, strike: float, maturity_days: int, rate: float, price: float
) -> tuple[float, float] | None:
    """Invert a zero-dividend call; for TTWO this matches an American call absent dividends."""

    time_years = maturity_days / 365.0
    lower_bound = max(0.0, spot - strike * math.exp(-rate * time_years))
    if time_years <= 0 or not lower_bound <= price < spot:
        return None
    low, high = 0.005, 5.0
    if _bsm_call(spot, strike, time_years, rate, high) < price:
        return None
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if _bsm_call(spot, strike, time_years, rate, midpoint) < price:
            low = midpoint
        else:
            high = midpoint
    sigma = (low + high) / 2.0
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * time_years) / (
        sigma * math.sqrt(time_years)
    )
    return sigma, _normal_cdf(d1)


def _interpolated_rate(
    context: MarketContextDataset, *, cutoff: datetime, maturity_days: int
) -> float:
    eligible = [curve for curve in context.risk_free_curves if curve.available_at <= cutoff]
    if not eligible:
        raise ValueError("no point-in-time Treasury curve is available")
    rates = eligible[-1].rates_by_maturity_days
    tenors = sorted(rates)
    if maturity_days <= tenors[0]:
        return rates[tenors[0]]
    if maturity_days >= tenors[-1]:
        return rates[tenors[-1]]
    upper_index = next(index for index, value in enumerate(tenors) if value >= maturity_days)
    lower_tenor, upper_tenor = tenors[upper_index - 1], tenors[upper_index]
    weight = (maturity_days - lower_tenor) / (upper_tenor - lower_tenor)
    return rates[lower_tenor] * (1 - weight) + rates[upper_tenor] * weight


def _fx(context: MarketContextDataset, cutoff: datetime) -> float:
    eligible = [point for point in context.fx_rates if point.available_at <= cutoff]
    if not eligible:
        raise ValueError("no point-in-time EUR/USD rate is available")
    return eligible[-1].usd_per_eur


def _spot_close(context: MarketContextDataset, target: date) -> float:
    eligible = [bar for bar in context.underlying_bars if bar.market_time.date() <= target]
    if not eligible:
        raise ValueError(f"no underlying bar is available for {target}")
    return eligible[-1].close


def _signal_regime(context: MarketContextDataset, cutoff: datetime) -> tuple[float, float]:
    eligible = [bar for bar in context.underlying_bars if bar.available_at <= cutoff]
    if len(eligible) < 21:
        raise ValueError("at least 21 available underlying bars are required")
    window = eligible[-21:]
    momentum = window[-1].close / window[0].close - 1.0
    returns = [
        math.log(window[index].close / window[index - 1].close) for index in range(1, len(window))
    ]
    mean = fmean(returns)
    variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
    return momentum, math.sqrt(variance * 252)


def _eligible_call(row: HistoricalOptionObservation, settings: ComparablePanelSettings) -> bool:
    if row.option_type.value != "call" or row.bid is None or row.ask is None or row.mid is None:
        return False
    if row.bid <= 0 or row.mid <= 0 or row.ask < row.bid:
        return False
    relative_spread = (row.ask - row.bid) / row.mid
    return (
        relative_spread <= settings.maximum_relative_spread
        and (row.open_interest or 0) >= settings.minimum_open_interest
    )


def _option_outcome(
    *,
    strategy: ComparableStrategy,
    legs: list[tuple[HistoricalOptionObservation, PositionSide, float | None, float | None]],
    entry: dict[str, HistoricalOptionObservation],
    exit_quotes: dict[str, HistoricalOptionObservation],
    entry_fx: float,
    exit_fx: float,
    settings: ComparablePanelSettings,
    rule: str,
) -> PanelOutcome | None:
    entry_mid_usd = 0.0
    exit_mid_usd = 0.0
    entry_cash_usd = 0.0
    exit_cash_usd = 0.0
    for signal, side, _, _ in legs:
        entry_row = entry[signal.option_symbol]
        exit_row = exit_quotes[signal.option_symbol]
        if any(
            value is None
            for value in (
                entry_row.bid,
                entry_row.ask,
                entry_row.mid,
                exit_row.bid,
                exit_row.ask,
                exit_row.mid,
            )
        ):
            return None
        assert entry_row.bid is not None
        assert entry_row.ask is not None
        assert entry_row.mid is not None
        assert exit_row.bid is not None
        assert exit_row.ask is not None
        assert exit_row.mid is not None
        sign = 1.0 if side is PositionSide.LONG else -1.0
        entry_mid_usd += sign * float(entry_row.mid) * 100
        exit_mid_usd += sign * float(exit_row.mid) * 100
        entry_execution = (
            float(entry_row.ask) if side is PositionSide.LONG else float(entry_row.bid)
        )
        exit_execution = float(exit_row.bid) if side is PositionSide.LONG else float(exit_row.ask)
        entry_cash_usd += sign * entry_execution * 100
        exit_cash_usd += sign * exit_execution * 100
    fee_per_structure = len(legs) * (
        settings.commission_per_contract_side + settings.slippage_per_contract_side
    )
    debit_per_structure = entry_cash_usd + fee_per_structure
    budget_usd = settings.capital_eur * entry_fx
    if debit_per_structure <= 0:
        return None
    quantity = min(settings.maximum_contracts, math.floor(budget_usd / debit_per_structure))
    if quantity < 1:
        return None
    gross_pnl_usd = (exit_mid_usd - entry_mid_usd) * quantity
    net_pnl_usd = (exit_cash_usd - entry_cash_usd) * quantity - 2 * fee_per_structure * quantity
    gross_pnl_eur = gross_pnl_usd / exit_fx
    net_pnl_eur = net_pnl_usd / exit_fx
    net_return = max(-1.0, net_pnl_eur / settings.capital_eur)
    gross_return = gross_pnl_eur / settings.capital_eur
    cost_eur = max(0.0, gross_pnl_eur - net_pnl_eur)
    maximum_loss_eur = min(settings.capital_eur, debit_per_structure * quantity / entry_fx)
    return PanelOutcome(
        strategy=strategy,
        gross_return=gross_return,
        net_return=net_return,
        transaction_cost_eur=cost_eur,
        deployed_capital_eur=debit_per_structure * quantity / entry_fx,
        maximum_loss_eur=maximum_loss_eur,
        quantity=quantity,
        selected_rule=rule,
        legs=[
            PanelLeg(
                option_symbol=signal.option_symbol,
                side=side,
                strike=signal.strike,
                expiration=signal.expiration,
                signal_implied_volatility=iv,
                signal_delta=delta,
            )
            for signal, side, iv, delta in legs
        ],
    )


def _zero_outcome(strategy: ComparableStrategy, rule: str) -> PanelOutcome:
    return PanelOutcome(
        strategy=strategy,
        gross_return=0.0,
        net_return=0.0,
        transaction_cost_eur=0.0,
        deployed_capital_eur=0.0,
        maximum_loss_eur=0.0,
        quantity=0,
        selected_rule=rule,
        legs=[],
    )


def build_comparable_panel(
    option_rows: list[HistoricalOptionObservation],
    context: MarketContextDataset,
    settings: ComparablePanelSettings,
    *,
    generated_at: datetime,
) -> ComparablePanelDataset:
    by_date: dict[date, list[HistoricalOptionObservation]] = defaultdict(list)
    for row in option_rows:
        by_date[row.quote_time.date()].append(row)
    chain_dates = sorted(
        day for day, rows in by_date.items() if len(rows) >= settings.full_chain_min_quotes
    )
    observations: list[ComparablePanelObservation] = []
    generator = random.Random(settings.seed)
    for signal_date, entry_date, exit_date in zip(
        chain_dates, chain_dates[1:], chain_dates[2:], strict=False
    ):
        signal_rows = by_date[signal_date]
        entry_by_symbol = {row.option_symbol: row for row in by_date[entry_date]}
        exit_by_symbol = {row.option_symbol: row for row in by_date[exit_date]}
        common = [
            row
            for row in signal_rows
            if row.option_symbol in entry_by_symbol
            and row.option_symbol in exit_by_symbol
            and row.expiration > exit_date
            and _eligible_call(row, settings)
        ]
        if not common:
            continue
        expirations = sorted({row.expiration for row in common})
        expiration = min(
            expirations,
            key=lambda value: abs((value - signal_date).days - settings.target_dte),
        )
        calls = [row for row in common if row.expiration == expiration]
        if len(calls) < 3:
            continue
        spot = fmean(row.underlying_price or 0 for row in calls)
        decision_cutoff = max(row.available_at for row in calls)
        maturity_days = (expiration - signal_date).days
        rate = _interpolated_rate(context, cutoff=decision_cutoff, maturity_days=maturity_days)
        analytics: dict[str, tuple[float, float]] = {}
        for row in calls:
            if row.mid is not None:
                result = implied_volatility_and_delta(
                    spot=spot,
                    strike=row.strike,
                    maturity_days=maturity_days,
                    rate=rate,
                    price=row.mid,
                )
                if result is not None:
                    analytics[row.option_symbol] = result
        atm = min(calls, key=lambda row: (abs(row.strike - spot), row.strike))
        delta_candidates = [row for row in calls if row.option_symbol in analytics]
        if not delta_candidates:
            continue
        fixed_delta = min(
            delta_candidates,
            key=lambda row: (
                abs(analytics[row.option_symbol][1] - settings.fixed_delta_target),
                row.strike,
            ),
        )
        higher = [row for row in calls if row.strike > atm.strike]
        if not higher:
            continue
        short_call = min(
            higher,
            key=lambda row: (
                abs(row.strike - spot * (1 + settings.bull_spread_width_pct)),
                row.strike,
            ),
        )
        entry_cutoff = max(row.available_at for row in entry_by_symbol.values())
        exit_cutoff = max(row.available_at for row in exit_by_symbol.values())
        entry_fx = _fx(context, entry_cutoff)
        exit_fx = _fx(context, exit_cutoff)
        atm_analytics = analytics.get(atm.option_symbol, (None, None))
        delta_analytics = analytics[fixed_delta.option_symbol]
        short_analytics = analytics.get(short_call.option_symbol, (None, None))
        atm_outcome = _option_outcome(
            strategy=ComparableStrategy.ATM_LONG_CALL,
            legs=[(atm, PositionSide.LONG, *atm_analytics)],
            entry=entry_by_symbol,
            exit_quotes=exit_by_symbol,
            entry_fx=entry_fx,
            exit_fx=exit_fx,
            settings=settings,
            rule="nearest listed strike to signal spot; lower strike tie-break",
        )
        delta_outcome = _option_outcome(
            strategy=ComparableStrategy.FIXED_DELTA_LONG_CALL,
            legs=[(fixed_delta, PositionSide.LONG, *delta_analytics)],
            entry=entry_by_symbol,
            exit_quotes=exit_by_symbol,
            entry_fx=entry_fx,
            exit_fx=exit_fx,
            settings=settings,
            rule=f"nearest recomputed call delta to {settings.fixed_delta_target:.2f}",
        )
        spread_outcome = _option_outcome(
            strategy=ComparableStrategy.STANDARD_BULL_CALL_SPREAD,
            legs=[
                (atm, PositionSide.LONG, *atm_analytics),
                (short_call, PositionSide.SHORT, *short_analytics),
            ],
            entry=entry_by_symbol,
            exit_quotes=exit_by_symbol,
            entry_fx=entry_fx,
            exit_fx=exit_fx,
            settings=settings,
            rule=f"ATM long plus nearest listed {settings.bull_spread_width_pct:.0%} OTM short",
        )
        if atm_outcome is None or delta_outcome is None or spread_outcome is None:
            continue
        affordable_candidates: list[PanelOutcome] = []
        for row in calls:
            values = analytics.get(row.option_symbol, (None, None))
            outcome = _option_outcome(
                strategy=ComparableStrategy.RANDOM_ADMISSIBLE,
                legs=[(row, PositionSide.LONG, *values)],
                entry=entry_by_symbol,
                exit_quotes=exit_by_symbol,
                entry_fx=entry_fx,
                exit_fx=exit_fx,
                settings=settings,
                rule=f"deterministic seeded draw from admissible calls; seed={settings.seed}",
            )
            if outcome is not None:
                affordable_candidates.append(outcome)
        if not affordable_candidates:
            continue
        affordable_random = [
            generator.choice(affordable_candidates) for _ in range(settings.random_draws)
        ]
        random_outcome = PanelOutcome(
            strategy=ComparableStrategy.RANDOM_ADMISSIBLE,
            gross_return=fmean(item.gross_return for item in affordable_random),
            net_return=fmean(item.net_return for item in affordable_random),
            transaction_cost_eur=fmean(item.transaction_cost_eur for item in affordable_random),
            deployed_capital_eur=fmean(item.deployed_capital_eur for item in affordable_random),
            maximum_loss_eur=fmean(item.maximum_loss_eur for item in affordable_random),
            quantity=0,
            selected_rule=(
                f"mean of {len(affordable_random)} seeded draws with replacement from "
                f"{len(affordable_candidates)} admissible calls"
            ),
            legs=[],
        )
        momentum, realized_volatility = _signal_regime(context, decision_cutoff)
        if momentum <= settings.v10_momentum_gate:
            engine = _zero_outcome(
                ComparableStrategy.ENGINE_CANDIDATE,
                "frozen V10 gate: no position under adverse 20-session momentum",
            )
        elif realized_volatility >= settings.v10_high_volatility:
            engine = spread_outcome.model_copy(
                update={
                    "strategy": ComparableStrategy.ENGINE_CANDIDATE,
                    "selected_rule": "frozen V10 rule: bull spread in high-volatility regime",
                }
            )
        elif momentum >= settings.v10_high_momentum:
            engine = delta_outcome.model_copy(
                update={
                    "strategy": ComparableStrategy.ENGINE_CANDIDATE,
                    "selected_rule": "frozen V10 rule: fixed-delta call in positive momentum",
                }
            )
        else:
            engine = atm_outcome.model_copy(
                update={
                    "strategy": ComparableStrategy.ENGINE_CANDIDATE,
                    "selected_rule": "frozen V10 rule: ATM call in neutral regime",
                }
            )
        entry_spot = _spot_close(context, entry_date)
        exit_spot = _spot_close(context, exit_date)
        share_gross = (exit_spot / exit_fx) / (entry_spot / entry_fx) - 1.0
        share_net = max(-1.0, share_gross - settings.share_round_trip_cost_fraction)
        share_cost = settings.capital_eur * settings.share_round_trip_cost_fraction
        underlying = PanelOutcome(
            strategy=ComparableStrategy.UNDERLYING,
            gross_return=share_gross,
            net_return=share_net,
            transaction_cost_eur=share_cost,
            deployed_capital_eur=settings.capital_eur,
            maximum_loss_eur=settings.capital_eur,
            quantity=0,
            selected_rule="one-period TTWO shares with EUR/USD translation",
            legs=[],
        )
        buy_hold = underlying.model_copy(
            update={
                "strategy": ComparableStrategy.BUY_AND_HOLD,
                "net_return": share_gross,
                "transaction_cost_eur": 0.0,
                "selected_rule": "continuous TTWO share holding; boundary costs applied later",
            }
        )
        observations.append(
            ComparablePanelObservation(
                observation_id=f"panel-{signal_date.isoformat()}",
                signal_date=signal_date,
                decision_cutoff=decision_cutoff,
                entry_date=entry_date,
                exit_date=exit_date,
                option_target_dte=settings.target_dte,
                signal_momentum_20=momentum,
                signal_realized_volatility_20=realized_volatility,
                outcomes=[
                    _zero_outcome(ComparableStrategy.CASH, "cash capital baseline"),
                    _zero_outcome(
                        ComparableStrategy.NO_POSITION, "explicit no-position alternative"
                    ),
                    underlying,
                    buy_hold,
                    atm_outcome,
                    delta_outcome,
                    spread_outcome,
                    random_outcome,
                    engine,
                ],
            )
        )
    if observations:
        first_buy_hold = next(
            item
            for item in observations[0].outcomes
            if item.strategy is ComparableStrategy.BUY_AND_HOLD
        )
        last_buy_hold = next(
            item
            for item in observations[-1].outcomes
            if item.strategy is ComparableStrategy.BUY_AND_HOLD
        )
        half_cost = settings.share_round_trip_cost_fraction / 2
        first_buy_hold.net_return -= half_cost
        first_buy_hold.transaction_cost_eur += settings.capital_eur * half_cost
        last_buy_hold.net_return -= half_cost
        last_buy_hold.transaction_cost_eur += settings.capital_eur * half_cost
    return ComparablePanelDataset(
        dataset_id="ttwo-comparable-baseline-panel-v1",
        generated_at=generated_at,
        observations=observations,
        source_hashes={
            "historical_options": canonical_hash(
                [row.model_dump(mode="json") for row in option_rows]
            ),
            "market_context": canonical_hash(context.model_dump(mode="json")),
        },
        frozen_rules={
            "target_dte": settings.target_dte,
            "fixed_delta_target": settings.fixed_delta_target,
            "bull_spread_width_pct": settings.bull_spread_width_pct,
            "random_seed": settings.seed,
            "random_draws": settings.random_draws,
            "v10_momentum_gate": settings.v10_momentum_gate,
            "v10_high_momentum": settings.v10_high_momentum,
            "v10_high_volatility": settings.v10_high_volatility,
        },
    )


def panel_return_series(panel: ComparablePanelDataset) -> list[StrategyReturnSeries]:
    observation_ids = [item.observation_id for item in panel.observations]
    output: list[StrategyReturnSeries] = []
    for strategy in MANDATORY_STRATEGIES:
        outcomes = [
            next(outcome for outcome in observation.outcomes if outcome.strategy is strategy)
            for observation in panel.observations
        ]
        output.append(
            StrategyReturnSeries(
                strategy=strategy,
                observation_ids=observation_ids,
                gross_returns=[item.gross_return for item in outcomes],
                net_returns=[item.net_return for item in outcomes],
                transaction_costs=[item.transaction_cost_eur for item in outcomes],
            )
        )
    return output
