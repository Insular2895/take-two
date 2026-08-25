"""American pre-expiry and terminal scenario analysis for V10.1 candidates."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from take_two_options.american import (
    american_scenario_analytics,
    american_scenario_value,
    historical_option_analytics,
)
from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.domain import PositionSide
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import (
    Architecture,
    CandidateLeg,
    CompiledStrategyCandidate,
    QuoteSnapshot,
)
from take_two_options.thesis_scanner.enumeration import EnumeratedCandidate
from take_two_options.thesis_scanner.schemas import (
    IVCase,
    LegExecutionMetric,
    NetGreeks,
    StructureDecisionMetrics,
    TargetPnlRow,
    TerminalValueThreshold,
    ThesisCandidate,
    ThesisCandidateStatus,
    ThesisChain,
    ThesisExecution,
    ThesisScanPolicy,
    ThesisScanRequest,
    ThesisScenarioPoint,
)


@dataclass(frozen=True)
class EvaluationResult:
    candidates: tuple[ThesisCandidate, ...]
    blocked_reasons: dict[str, int]


def terminal_value_thresholds(
    legs: list[CandidateLeg],
    *,
    total_cost_usd: float,
) -> list[TerminalValueThreshold]:
    """Solve exact terminal spots where gross position value reaches 2x/3x/5x cost."""
    if total_cost_usd <= 0:
        raise ValueError("total cost must be positive")
    strikes = sorted({leg.quote.strike for leg in legs})
    boundaries = [0.0, *strikes]
    thresholds: list[TerminalValueThreshold] = []
    for multiple in (2, 3, 5):
        target_value = multiple * total_cost_usd
        roots: set[float] = set()
        for left, right in zip(boundaries, boundaries[1:], strict=False):
            left_value = terminal_payoff(legs, left)
            right_value = terminal_payoff(legs, right)
            slope = (right_value - left_value) / (right - left)
            if abs(slope) <= 1e-12:
                if abs(left_value - target_value) <= 1e-7:
                    roots.add(round(left, 4))
                continue
            root = left + (target_value - left_value) / slope
            if left - 1e-7 <= root <= right + 1e-7:
                roots.add(round(max(root, 0.0), 4))

        last = boundaries[-1]
        last_value = terminal_payoff(legs, last)
        high_slope = terminal_payoff(legs, last + 1.0) - last_value
        if abs(high_slope) <= 1e-12:
            if abs(last_value - target_value) <= 1e-7:
                roots.add(round(last, 4))
        else:
            root = last + (target_value - last_value) / high_slope
            if root >= last - 1e-7:
                roots.add(round(max(root, 0.0), 4))

        spots = sorted(roots)
        attainable = bool(spots)
        message = (
            "Cours TTWO à l’échéance : "
            + " ou ".join(f"${spot:,.2f}" for spot in spots)
            if attainable
            else "Impossible — gain plafonné par la structure."
        )
        thresholds.append(
            TerminalValueThreshold(
                multiple=multiple,
                target_position_value_usd=round(target_value, 4),
                target_net_profit_usd=round((multiple - 1) * total_cost_usd, 4),
                attainable=attainable,
                spot_prices=spots,
                message=message,
            )
        )
    return thresholds


def _base_volatility(
    quote: QuoteSnapshot,
    *,
    chain: ThesisChain,
    policy: ThesisScanPolicy,
) -> tuple[float, str | None]:
    if quote.implied_volatility is not None:
        return quote.implied_volatility, None
    midpoint = (quote.bid + quote.ask) / 2
    analytics = historical_option_analytics(
        spot=chain.spot,
        strike=quote.strike,
        valuation_date=chain.as_of.date(),
        expiration_date=quote.expiration,
        option_type=quote.option_type,
        target_price=midpoint,
        rate=policy.risk_free_rate,
        dividend_yield=policy.continuous_dividend_yield,
    )
    return analytics.implied_volatility, "IV_INVERTED_FROM_AMERICAN_MIDPOINT"


def _scenario_dates(
    *,
    start: date,
    catalyst: date,
    expiration: date,
) -> list[date]:
    values = {
        start,
        catalyst,
        expiration,
        *(
            start + timedelta(days=days)
            for days in (30, 60, 90)
            if start + timedelta(days=days) <= expiration
        ),
    }
    return sorted(value for value in values if start <= value <= expiration)


def _scenario_spots(
    *,
    chain: ThesisChain,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
) -> list[float]:
    values = {
        *request.target_prices,
        *(chain.spot * multiplier for multiplier in policy.spot_grid_multipliers),
    }
    return sorted(round(value, 4) for value in values if value > 0)


def _position_value(
    legs: list[CandidateLeg],
    *,
    spot: float,
    valuation_date: date,
    expiration: date,
    volatility_by_symbol: dict[str, float],
    volatility_multiplier: float,
    policy: ThesisScanPolicy,
) -> float:
    if valuation_date >= expiration:
        return terminal_payoff(legs, spot)
    value = 0.0
    for leg in legs:
        volatility = min(
            max(volatility_by_symbol[leg.quote.symbol] * volatility_multiplier, 0.0001),
            5.0,
        )
        option_value = american_scenario_value(
            spot=spot,
            strike=leg.quote.strike,
            valuation_date=valuation_date,
            expiration_date=expiration,
            option_type=leg.quote.option_type,
            volatility=volatility,
            rate=policy.risk_free_rate,
            dividend_yield=policy.continuous_dividend_yield,
        )
        value += leg.side.sign * leg.quantity * leg.quote.multiplier * option_value
    return value


def _execution(
    item: EnumeratedCandidate,
    *,
    chain: ThesisChain,
    policy: ThesisScanPolicy,
) -> ThesisExecution:
    candidate = item.candidate
    theoretical_mid = sum(
        leg.side.sign * leg.quantity * leg.quote.multiplier * ((leg.quote.bid + leg.quote.ask) / 2)
        for leg in candidate.legs
    )
    strategy_units = min(leg.quantity for leg in candidate.legs if leg.side is PositionSide.LONG)
    return ThesisExecution(
        theoretical_mid_debit_usd=round(theoretical_mid, 4),
        theoretical_mid_debit_eur=round(
            theoretical_mid / policy.eur_usd_rate,
            4,
        ),
        conservative_debit_usd=candidate.risk.entry_debit,
        conservative_debit_eur=round(
            candidate.risk.entry_debit / policy.eur_usd_rate,
            4,
        ),
        slippage_usd=candidate.risk.slippage,
        slippage_eur=round(
            candidate.risk.slippage / policy.eur_usd_rate,
            4,
        ),
        commissions_usd=candidate.risk.fees,
        commissions_eur=round(
            candidate.risk.fees / policy.eur_usd_rate,
            4,
        ),
        total_cost_usd=candidate.risk.total_cost,
        total_cost_eur=round(candidate.risk.total_cost / policy.eur_usd_rate, 4),
        indicative_limit_price_per_share=round(
            (candidate.risk.entry_debit + candidate.risk.slippage) / (100 * strategy_units),
            4,
        ),
        fx_rate=policy.eur_usd_rate,
        fx_rate_date=policy.fx_rate_date,
        fx_rate_source=policy.fx_rate_source,
        quote_date=chain.as_of,
        notes=[
            (
                "Mid debit is diagnostic only; conservative debit uses ask for "
                "longs and bid for shorts"
            ),
            "Fees and configured slippage are included in total cost and maximum loss",
            (
                "Limit price includes configured premium slippage but excludes "
                "commissions; it is not a live order"
            ),
        ],
    )


def _net_greeks(
    item: EnumeratedCandidate,
    *,
    chain: ThesisChain,
    policy: ThesisScanPolicy,
    volatility_by_symbol: dict[str, float],
) -> NetGreeks:
    totals = {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "rho": 0.0}
    for leg in item.candidate.legs:
        analytics = american_scenario_analytics(
            contract_symbol=leg.quote.symbol,
            spot=chain.spot,
            strike=leg.quote.strike,
            valuation_date=chain.as_of.date(),
            expiration_date=leg.quote.expiration,
            option_type=leg.quote.option_type,
            volatility=volatility_by_symbol[leg.quote.symbol],
            rate=policy.risk_free_rate,
            dividend_yield=policy.continuous_dividend_yield,
        )
        scale = leg.side.sign * leg.quantity * leg.quote.multiplier
        for name in totals:
            totals[name] += scale * getattr(analytics, name)
    return NetGreeks(**{name: round(value, 6) for name, value in totals.items()})


def _display_name(item: EnumeratedCandidate, dte: int, leaps_dte: int) -> str:
    candidate = item.candidate
    strikes = "/".join(f"{leg.quote.strike:g}" for leg in candidate.legs)
    if candidate.architecture.value == "long_call":
        prefix = "LEAPS call" if dte >= leaps_dte else "Long call"
    elif candidate.architecture.value == "bull_call_spread":
        prefix = "Bull call spread"
    else:
        prefix = "Call butterfly"
    return f"{prefix} {strikes} · {candidate.legs[0].quote.expiration.isoformat()}"


def _candidate_scenarios(
    item: EnumeratedCandidate,
    *,
    chain: ThesisChain,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    volatility_by_symbol: dict[str, float],
) -> list[ThesisScenarioPoint]:
    candidate = item.candidate
    expiration = candidate.legs[0].quote.expiration
    start = chain.as_of.date()
    dates = _scenario_dates(
        start=start,
        catalyst=request.catalyst_date,
        expiration=expiration,
    )
    spots = _scenario_spots(chain=chain, request=request, policy=policy)
    initial_value = _position_value(
        candidate.legs,
        spot=chain.spot,
        valuation_date=start,
        expiration=expiration,
        volatility_by_symbol=volatility_by_symbol,
        volatility_multiplier=1,
        policy=policy,
    )
    points: list[ThesisScenarioPoint] = []
    for valuation_date in dates:
        for spot in spots:
            current_spot_value = _position_value(
                candidate.legs,
                spot=spot,
                valuation_date=start,
                expiration=expiration,
                volatility_by_symbol=volatility_by_symbol,
                volatility_multiplier=1,
                policy=policy,
            )
            time_value = _position_value(
                candidate.legs,
                spot=spot,
                valuation_date=valuation_date,
                expiration=expiration,
                volatility_by_symbol=volatility_by_symbol,
                volatility_multiplier=1,
                policy=policy,
            )
            for iv_case in IVCase:
                multiplier = policy.iv_case_multipliers[iv_case]
                scenario_value = _position_value(
                    candidate.legs,
                    spot=spot,
                    valuation_date=valuation_date,
                    expiration=expiration,
                    volatility_by_symbol=volatility_by_symbol,
                    volatility_multiplier=multiplier,
                    policy=policy,
                )
                pnl = scenario_value - candidate.risk.total_cost
                underlying_effect = current_spot_value - initial_value
                theta_effect = time_value - current_spot_value
                iv_effect = scenario_value - time_value
                execution_effect = initial_value - candidate.risk.total_cost
                residual = pnl - (underlying_effect + theta_effect + iv_effect + execution_effect)
                scenario_identity = {
                    "candidate": candidate.candidate_id,
                    "date": valuation_date,
                    "spot": spot,
                    "iv_case": iv_case.value,
                }
                points.append(
                    ThesisScenarioPoint(
                        scenario_id=f"scn-{stable_hash(scenario_identity)[:16]}",
                        spot=spot,
                        valuation_date=valuation_date,
                        days_forward=(valuation_date - start).days,
                        iv_case=iv_case,
                        iv_multiplier=multiplier,
                        terminal=valuation_date == expiration,
                        estimated_value_usd=round(scenario_value, 4),
                        pnl_usd=round(pnl, 4),
                        pnl_eur=round(pnl / policy.eur_usd_rate, 4),
                        underlying_effect_usd=round(underlying_effect, 4),
                        theta_effect_usd=round(theta_effect, 4),
                        iv_effect_usd=round(iv_effect, 4),
                        execution_cost_effect_usd=round(execution_effect, 4),
                        residual_usd=round(residual, 6),
                    )
                )
    return points


def _target_pnl_rows(
    scenarios: list[ThesisScenarioPoint],
    *,
    request: ThesisScanRequest,
    expiration: date,
) -> list[TargetPnlRow]:
    rows: list[TargetPnlRow] = []
    for target in request.target_prices:
        catalyst = {
            point.iv_case: point
            for point in scenarios
            if point.valuation_date == request.catalyst_date
            and abs(point.spot - target) < 1e-6
        }
        terminal = next(
            point
            for point in scenarios
            if point.valuation_date == expiration
            and point.iv_case is IVCase.STABLE
            and abs(point.spot - target) < 1e-6
        )
        rows.append(
            TargetPnlRow(
                spot=target,
                catalyst_iv_down_usd=catalyst[IVCase.DOWN].pnl_usd,
                catalyst_iv_down_eur=catalyst[IVCase.DOWN].pnl_eur,
                catalyst_iv_stable_usd=catalyst[IVCase.STABLE].pnl_usd,
                catalyst_iv_stable_eur=catalyst[IVCase.STABLE].pnl_eur,
                catalyst_iv_up_usd=catalyst[IVCase.UP].pnl_usd,
                catalyst_iv_up_eur=catalyst[IVCase.UP].pnl_eur,
                expiration_usd=terminal.pnl_usd,
                expiration_eur=terminal.pnl_eur,
            )
        )
    return rows


def _structure_language(
    candidate: CompiledStrategyCandidate,
) -> tuple[str, str, float | None, float | None, float | None, list[float]]:
    risk = candidate.risk
    break_evens = risk.break_even_points
    strikes = sorted({leg.quote.strike for leg in candidate.legs})
    if candidate.architecture is Architecture.LONG_CALL:
        strike = candidate.legs[0].quote.strike
        break_even = break_evens[0]
        lose_if = (
            f"Tu perds tout ou partie de la mise si TTWO termine sous ${break_even:,.2f}; "
            f"à ou sous ${strike:,.2f}, la prime peut être perdue intégralement."
        )
        win_if = (
            f"Tu gagnes à l’échéance si TTWO dépasse ${break_even:,.2f}; "
            "le gain contractuel reste théoriquement illimité."
        )
        return lose_if, win_if, None, None, None, break_evens
    if candidate.architecture is Architecture.BULL_CALL_SPREAD:
        lower, upper = strikes
        break_even = break_evens[0]
        lose_if = (
            f"Tu perds tout ou partie de la mise si TTWO termine sous ${break_even:,.2f}; "
            f"à ou sous ${lower:,.2f}, la perte maximale est atteinte."
        )
        win_if = (
            f"Tu gagnes à l’échéance au-dessus de ${break_even:,.2f}; "
            f"le gain est plafonné à partir de ${upper:,.2f}."
        )
        return lose_if, win_if, upper - lower, upper, None, break_evens
    lower, center, upper = strikes
    lose_if = (
        f"Tu perds hors de la zone ${break_evens[0]:,.2f}–${break_evens[-1]:,.2f}; "
        f"à ou sous ${lower:,.2f}, ou à ou au-dessus de ${upper:,.2f}, "
        "la perte maximale est atteinte."
    )
    win_if = (
        f"Tu gagnes si TTWO termine dans la zone ${break_evens[0]:,.2f}–"
        f"${break_evens[-1]:,.2f}; le gain maximal est atteint à ${center:,.2f}."
    )
    return (
        lose_if,
        win_if,
        center - lower,
        None,
        center,
        break_evens,
    )


def _aware(timestamp: datetime) -> datetime:
    return timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=UTC)


def _decision_metrics(
    candidate: CompiledStrategyCandidate,
    *,
    execution: ThesisExecution,
    greeks: NetGreeks,
    scenarios: list[ThesisScenarioPoint],
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    scan_time: datetime,
    expected_pnl_usd: float | None,
) -> StructureDecisionMetrics:
    target_rows = _target_pnl_rows(
        scenarios,
        request=request,
        expiration=candidate.legs[0].quote.expiration,
    )
    modeled_points = [
        point
        for point in scenarios
        if any(abs(point.spot - target) < 1e-6 for target in request.target_prices)
    ]
    best_modeled_gain_usd = max(0.0, max(point.pnl_usd for point in modeled_points))
    iv_down_impact_usd = min(
        row.catalyst_iv_down_usd - row.catalyst_iv_stable_usd for row in target_rows
    )
    has_short_legs = any(leg.side is PositionSide.SHORT for leg in candidate.legs)
    quote_ages: list[int] = []
    leg_execution: list[LegExecutionMetric] = []
    for leg in candidate.legs:
        quote = leg.quote
        quote_timestamp = _aware(quote.quote_timestamp)
        age_seconds = max(0, int((_aware(scan_time) - quote_timestamp).total_seconds()))
        quote_ages.append(age_seconds)
        midpoint = (quote.bid + quote.ask) / 2
        leg_execution.append(
            LegExecutionMetric(
                symbol=quote.symbol,
                quote_timestamp=quote_timestamp,
                quote_age_seconds=age_seconds,
                bid=quote.bid,
                ask=quote.ask,
                midpoint=round(midpoint, 6),
                relative_spread=round(
                    (quote.ask - quote.bid) / midpoint if midpoint > 0 else 0,
                    8,
                ),
                open_interest=quote.open_interest,
                volume=quote.volume,
                price_quality=quote.price_quality,
                source_id=quote.source_id,
            )
        )
    open_interests = [leg.quote.open_interest for leg in candidate.legs]
    volumes = [leg.quote.volume for leg in candidate.legs]
    (
        lose_if,
        win_if,
        strike_width,
        capped_gain_from_spot,
        butterfly_center,
        profit_zone,
    ) = _structure_language(candidate)
    maximum_loss = candidate.risk.maximum_loss
    maximum_gain = candidate.risk.maximum_gain
    total_cost = execution.total_cost_usd
    strategy_units = min(
        leg.quantity for leg in candidate.legs if leg.side is PositionSide.LONG
    )
    data_qualities = sorted({leg.quote.price_quality for leg in candidate.legs})
    needs_research_warning = len(candidate.legs) > 1 or any(
        quality != "live_broker" for quality in data_qualities
    )
    return StructureDecisionMetrics(
        loss_budget_fraction=round(
            (maximum_loss / policy.eur_usd_rate) / request.budget_eur,
            8,
        ),
        stake_loss_fraction=round(maximum_loss / total_cost, 8),
        total_option_contracts=sum(leg.quantity for leg in candidate.legs),
        strategy_units=strategy_units,
        contractual_gain_unbounded=maximum_gain is None,
        contractual_max_gain_usd=maximum_gain,
        contractual_max_gain_eur=(
            round(maximum_gain / policy.eur_usd_rate, 4)
            if maximum_gain is not None
            else None
        ),
        best_modeled_gain_usd=round(best_modeled_gain_usd, 4),
        best_modeled_gain_eur=round(best_modeled_gain_usd / policy.eur_usd_rate, 4),
        expected_pnl_eur=(
            round(expected_pnl_usd / policy.eur_usd_rate, 4)
            if expected_pnl_usd is not None
            else None
        ),
        contractual_gain_loss_ratio=(
            round(maximum_gain / maximum_loss, 8) if maximum_gain is not None else None
        ),
        modeled_gain_loss_ratio=round(best_modeled_gain_usd / maximum_loss, 8),
        terminal_value_thresholds=terminal_value_thresholds(
            candidate.legs,
            total_cost_usd=total_cost,
        ),
        target_pnl_rows=target_rows,
        strike_width=strike_width,
        capped_gain_from_spot=capped_gain_from_spot,
        butterfly_center_strike=butterfly_center,
        profit_zone=profit_zone,
        lose_if=lose_if,
        win_if=win_if,
        theta_to_stake_daily=round(abs(greeks.theta) / total_cost, 8),
        iv_down_impact_usd=round(iv_down_impact_usd, 4),
        iv_down_impact_eur=round(iv_down_impact_usd / policy.eur_usd_rate, 4),
        maximum_leg_relative_spread=max(
            metric.relative_spread for metric in leg_execution
        ),
        minimum_open_interest=(
            min(value for value in open_interests if value is not None)
            if all(value is not None for value in open_interests)
            else None
        ),
        minimum_volume=(
            min(value for value in volumes if value is not None)
            if all(value is not None for value in volumes)
            else None
        ),
        total_premium_loss_possible=maximum_loss >= total_cost - 1e-7,
        has_short_legs=has_short_legs,
        assignment_risk=has_short_legs,
        pin_risk=has_short_legs,
        iv_crush_exposure=greeks.vega > 0,
        catalyst_delay_exposure=abs(greeks.theta) > 0,
        quote_age_seconds=max(quote_ages),
        quote_timestamp=min(metric.quote_timestamp for metric in leg_execution),
        source_ids=sorted({leg.quote.source_id for leg in candidate.legs}),
        data_qualities=data_qualities,
        leg_execution=leg_execution,
        research_estimate_warning=(
            "Estimation de recherche — ce prix n’est pas une cotation combo exécutable."
            if needs_research_warning
            else None
        ),
    )


def evaluate_candidates(
    *,
    enumerated: tuple[EnumeratedCandidate, ...],
    chain: ThesisChain,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    scan_time: datetime,
) -> EvaluationResult:
    """Evaluate every candidate that passed the explicit hard filters."""
    unique_quotes = {
        leg.quote.symbol: leg.quote for item in enumerated for leg in item.candidate.legs
    }
    volatility_by_symbol: dict[str, float] = {}
    volatility_warnings: dict[str, str] = {}
    invalid_symbols: set[str] = set()
    for symbol, quote in sorted(unique_quotes.items()):
        try:
            volatility, warning = _base_volatility(
                quote,
                chain=chain,
                policy=policy,
            )
            volatility_by_symbol[symbol] = volatility
            if warning:
                volatility_warnings[symbol] = warning
        except (ValueError, RuntimeError):
            invalid_symbols.add(symbol)

    blocked: Counter[str] = Counter()
    results: list[ThesisCandidate] = []
    for item in enumerated:
        candidate = item.candidate
        if any(leg.quote.symbol in invalid_symbols for leg in candidate.legs):
            blocked["IV_UNAVAILABLE"] += 1
            continue
        warnings = {
            *item.warnings,
            *chain.warnings,
            *(
                volatility_warnings[leg.quote.symbol]
                for leg in candidate.legs
                if leg.quote.symbol in volatility_warnings
            ),
        }
        if any(
            volatility_by_symbol[leg.quote.symbol] * policy.iv_case_multipliers[IVCase.UP] > 5
            for leg in candidate.legs
        ):
            warnings.add("IV_UP_SCENARIO_CLIPPED_AT_500_PERCENT")
        execution = _execution(item, chain=chain, policy=policy)
        scenarios = _candidate_scenarios(
            item,
            chain=chain,
            request=request,
            policy=policy,
            volatility_by_symbol=volatility_by_symbol,
        )
        targets: dict[str, float] = {}
        for target in request.target_prices:
            match = next(
                point
                for point in scenarios
                if point.valuation_date == request.catalyst_date
                and point.iv_case is IVCase.STABLE
                and abs(point.spot - target) < 1e-6
            )
            targets[f"{target:.2f}"] = match.pnl_usd
        expected_pnl = None
        probability_success = None
        if request.scenario_probabilities is not None:
            expected_pnl = round(
                sum(
                    targets[f"{target:.2f}"] * probability
                    for target, probability in zip(
                        request.target_prices,
                        request.scenario_probabilities,
                        strict=True,
                    )
                ),
                4,
            )
            probability_success = round(
                sum(
                    probability
                    for target, probability in zip(
                        request.target_prices,
                        request.scenario_probabilities,
                        strict=True,
                    )
                    if targets[f"{target:.2f}"] > 0
                ),
                8,
            )
        dte = (candidate.legs[0].quote.expiration - chain.as_of.date()).days
        modeled_return = max(targets.values()) / candidate.risk.maximum_loss
        status = ThesisCandidateStatus.WATCHLIST if warnings else ThesisCandidateStatus.ELIGIBLE
        greeks = _net_greeks(
            item,
            chain=chain,
            policy=policy,
            volatility_by_symbol=volatility_by_symbol,
        )
        decision_metrics = _decision_metrics(
            candidate,
            execution=execution,
            greeks=greeks,
            scenarios=scenarios,
            request=request,
            policy=policy,
            scan_time=scan_time,
            expected_pnl_usd=expected_pnl,
        )
        results.append(
            ThesisCandidate(
                candidate_id=candidate.candidate_id,
                architecture=candidate.architecture,
                maturity_class=(
                    "leaps"
                    if candidate.architecture.value == "long_call"
                    and dte >= policy.leaps_minimum_dte
                    else "standard"
                ),
                display_name=_display_name(item, dte, policy.leaps_minimum_dte),
                base_candidate=candidate,
                status=status,
                dte=dte,
                expiration=candidate.legs[0].quote.expiration,
                execution=execution,
                net_greeks=greeks,
                scenario_points=scenarios,
                target_pnl_stable_at_catalyst_usd=targets,
                maximum_loss_eur=round(
                    candidate.risk.maximum_loss / policy.eur_usd_rate,
                    4,
                ),
                maximum_gain_eur=(
                    round(candidate.risk.maximum_gain / policy.eur_usd_rate, 4)
                    if candidate.risk.maximum_gain is not None
                    else None
                ),
                expected_pnl_usd=expected_pnl,
                probability_success=probability_success,
                maximum_return_on_risk=round(max(0.0, modeled_return), 6),
                blockers=[],
                warnings=sorted(warnings),
                selection_reasons=[
                    "Bounded-risk bullish structure passed every configured hard filter"
                ],
                invalidation_conditions=[
                    "Bullish thesis or catalyst timing changes materially",
                    "Live maximum debit exceeds the displayed preview",
                    "Contract deliverable, multiplier, or quote provenance differs in IBKR",
                ],
                historical_confidence=policy.historical_confidence,
                decision_metrics=decision_metrics,
            )
        )
    results.sort(key=lambda candidate: candidate.candidate_id)
    return EvaluationResult(
        candidates=tuple(results),
        blocked_reasons=dict(sorted(blocked.items())),
    )
