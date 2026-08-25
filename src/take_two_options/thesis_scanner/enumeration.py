"""Strict bullish-structure enumeration for the V10 scanner."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from take_two_options.candidate_generation.factory import build_candidate
from take_two_options.domain import OptionType, PositionSide
from take_two_options.knowledge.schemas import (
    Architecture,
    Catalyst,
    CompiledStrategyCandidate,
    DataRefreshPolicy,
    ExecutionPolicy,
    HoldoutPolicy,
    LiquidityPolicy,
    MaintenancePreferences,
    QuoteSnapshot,
    StrategyCatalog,
    TradeRequest,
)
from take_two_options.thesis_scanner.schemas import (
    QuoteRejectionSummary,
    ThesisChain,
    ThesisQuote,
    ThesisScanPolicy,
    ThesisScanRequest,
)


@dataclass(frozen=True)
class EnumeratedCandidate:
    candidate: CompiledStrategyCandidate
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EnumerationResult:
    candidates: tuple[EnumeratedCandidate, ...]
    quote_rejections: QuoteRejectionSummary
    generated_by_architecture: dict[str, int]
    generated_candidates: int
    blocked_reasons: dict[str, int]


def _relative_spread(quote: ThesisQuote) -> float:
    assert quote.bid is not None
    assert quote.ask is not None
    midpoint = (quote.bid + quote.ask) / 2
    return (quote.ask - quote.bid) / midpoint if midpoint > 0 else float("inf")


def _quote_reasons(
    quote: ThesisQuote,
    *,
    chain: ThesisChain,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    scan_time: datetime,
) -> list[str]:
    reasons: list[str] = []
    cutoff = request.catalyst_date + timedelta(days=request.expiration_buffer_days)
    if quote.option_type is not OptionType.CALL:
        reasons.append("NOT_A_CALL")
    if quote.expiration < cutoff:
        reasons.append("EXPIRATION_BEFORE_CATALYST_BUFFER")
    if quote.quote_timestamp is None:
        reasons.append("QUOTE_TIMESTAMP_MISSING")
    else:
        timestamp = quote.quote_timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        if timestamp > chain.as_of + timedelta(minutes=5):
            reasons.append("QUOTE_TIMESTAMP_AFTER_CHAIN")
        if (scan_time.date() - timestamp.date()).days > policy.maximum_quote_age_days:
            reasons.append("QUOTE_STALE")
    if quote.bid is None or quote.ask is None:
        reasons.append("BID_ASK_MISSING")
    elif quote.bid <= 0 or quote.ask <= 0:
        reasons.append("BID_ASK_NON_POSITIVE")
    elif quote.bid > quote.ask:
        reasons.append("CROSSED_QUOTE")
    elif _relative_spread(quote) > policy.maximum_relative_spread:
        reasons.append("LEG_SPREAD_TOO_WIDE")
    if quote.multiplier is None or quote.multiplier_status == "unknown":
        reasons.append("MULTIPLIER_UNKNOWN")
    elif quote.multiplier != 100:
        reasons.append("NONSTANDARD_MULTIPLIER")
    if quote.standard_contract is False:
        reasons.append("NONSTANDARD_CONTRACT")
    moneyness = quote.strike / chain.spot
    if not policy.minimum_moneyness <= moneyness <= policy.maximum_moneyness:
        reasons.append("STRIKE_OUTSIDE_CONFIGURED_MONEYNESS")
    if quote.open_interest is not None and quote.open_interest < policy.minimum_open_interest:
        reasons.append("OPEN_INTEREST_BELOW_MINIMUM")
    if quote.volume is not None and quote.volume < policy.minimum_volume:
        reasons.append("VOLUME_BELOW_MINIMUM")
    return reasons


def _quote_warnings(quote: ThesisQuote) -> list[str]:
    warnings: list[str] = []
    if quote.open_interest is None:
        warnings.append("OPEN_INTEREST_UNAVAILABLE")
    if quote.volume is None:
        warnings.append("VOLUME_UNAVAILABLE")
    if quote.multiplier_status != "confirmed":
        warnings.append("MULTIPLIER_ASSUMED_NOT_BROKER_CONFIRMED")
    if quote.standard_contract is None:
        warnings.append("DELIVERABLE_STANDARD_STATUS_UNKNOWN")
    if quote.price_quality != "opra":
        warnings.append(f"NON_EXECUTABLE_QUOTE_QUALITY:{quote.price_quality}")
    return warnings


def _snapshot(quote: ThesisQuote) -> QuoteSnapshot:
    assert quote.bid is not None
    assert quote.ask is not None
    assert quote.quote_timestamp is not None
    assert quote.multiplier is not None
    quality = {
        "opra": "live_broker",
        "indicative": "indicative",
        "eod_bid_ask": "eod_bid_ask",
        "synthetic": "modeled",
        "unknown": "indicative",
    }[quote.price_quality]
    return QuoteSnapshot(
        symbol=quote.symbol,
        expiration=quote.expiration,
        option_type=quote.option_type,
        strike=quote.strike,
        bid=quote.bid,
        ask=quote.ask,
        volume=quote.volume,
        open_interest=quote.open_interest,
        implied_volatility=quote.implied_volatility,
        delta=quote.delta,
        quote_timestamp=quote.quote_timestamp,
        multiplier=quote.multiplier,
        price_quality=quality,
        source_id=quote.source_id,
    )


def _trade_request(
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    chain: ThesisChain,
    *,
    maximum_dte: int,
) -> TradeRequest:
    minimum_dte = max(
        (
            request.catalyst_date
            + timedelta(days=request.expiration_buffer_days)
            - chain.as_of.date()
        ).days,
        1,
    )
    return TradeRequest(
        request_id="v10-thesis-scan",
        ticker=request.ticker,
        as_of=chain.as_of.date(),
        currency="EUR",
        budget=request.budget_eur,
        maximum_loss=request.max_loss_eur,
        directional_thesis="bullish",
        thesis_summary="User-supplied bullish thesis; scanner does not validate it.",
        thesis_invalidation_conditions=[
            "Bullish catalyst thesis is invalidated or materially delayed",
            "Live combo price exceeds the displayed maximum debit",
        ],
        horizon_min_days=minimum_dte,
        horizon_max_days=max(maximum_dte, minimum_dte),
        catalysts=[
            Catalyst(
                catalyst_id="user-catalyst",
                name="User-supplied catalyst",
                start=request.catalyst_date,
                end=request.catalyst_date,
            )
        ],
        allowed_structures=[
            Architecture.LONG_CALL,
            Architecture.BULL_CALL_SPREAD,
            Architecture.CALL_BUTTERFLY,
        ],
        maximum_contracts=policy.maximum_contracts,
        liquidity_policy=LiquidityPolicy(
            policy_id="v10-explicit-liquidity",
            minimum_open_interest=0,
            minimum_volume=0,
            maximum_relative_spread=policy.maximum_relative_spread,
            allow_missing_volume=True,
            provenance=policy.policy_id,
            status="calibration_required",
        ),
        execution_policy=ExecutionPolicy(
            policy_id="v10-conservative-execution",
            commission_per_contract_side=policy.commission_per_contract_side,
            slippage_per_contract_side=policy.slippage_per_contract_side,
            quote_quality_required="indicative",
            provenance=policy.policy_id,
        ),
        maintenance_preferences=MaintenancePreferences(
            allow_rolling=False,
            allow_capital_recovery=False,
            allow_scaling_out=False,
            review_frequency_days=7,
        ),
        data_refresh_policy=DataRefreshPolicy(
            policy_id="v10-chain-input",
            providers=["cache"],
            maximum_age_days=policy.maximum_quote_age_days,
        ),
        final_holdout_policy=HoldoutPolicy(
            policy_id="v10-thesis-warning-only",
            minimum_train_observations=1,
            minimum_validation_observations=1,
            minimum_test_observations=1,
            minimum_holdout_observations=1,
            provenance="Historical V9 evidence lowers confidence but does not block thesis mode",
        ),
        fx_rate_to_usd=policy.eur_usd_rate,
        fx_rate_as_of=policy.fx_rate_date,
        safety_reserve_fraction=0,
    )


def _global_blockers(*, policy: ThesisScanPolicy, scan_time: datetime) -> list[str]:
    blockers: list[str] = []
    if policy.fx_rate_date > scan_time.date():
        blockers.append("FX_RATE_FROM_FUTURE")
    elif (scan_time.date() - policy.fx_rate_date).days > policy.maximum_fx_age_days:
        blockers.append("FX_RATE_STALE")
    if policy.risk_free_rate_date > scan_time.date():
        blockers.append("RISK_FREE_RATE_FROM_FUTURE")
    return blockers


def enumerate_bullish_candidates(
    *,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    chain: ThesisChain,
    catalog: StrategyCatalog,
    scan_time: datetime,
) -> EnumerationResult:
    """Enumerate every configured bullish debit structure over usable calls."""
    rejection_counts: Counter[str] = Counter()
    usable: list[tuple[ThesisQuote, QuoteSnapshot, tuple[str, ...]]] = []
    for quote in chain.quotes:
        reasons = _quote_reasons(
            quote,
            chain=chain,
            request=request,
            policy=policy,
            scan_time=scan_time,
        )
        if reasons:
            rejection_counts.update(set(reasons))
            continue
        usable.append((quote, _snapshot(quote), tuple(sorted(set(_quote_warnings(quote))))))

    quote_rejections = QuoteRejectionSummary(
        total_quotes=len(chain.quotes),
        usable_calls=len(usable),
        reasons=dict(sorted(rejection_counts.items())),
    )
    if not usable:
        return EnumerationResult(
            candidates=(),
            quote_rejections=quote_rejections,
            generated_by_architecture={},
            generated_candidates=0,
            blocked_reasons=dict(sorted(rejection_counts.items())),
        )

    recipes = {
        recipe.architecture: recipe
        for recipe in catalog.recipes
        if recipe.architecture
        in {
            Architecture.LONG_CALL,
            Architecture.BULL_CALL_SPREAD,
            Architecture.CALL_BUTTERFLY,
        }
    }
    missing = {
        architecture.value
        for architecture in {
            Architecture.LONG_CALL,
            Architecture.BULL_CALL_SPREAD,
            Architecture.CALL_BUTTERFLY,
        }
        if architecture not in recipes
    }
    if missing:
        raise ValueError(f"compiled strategy recipes missing: {sorted(missing)}")

    maximum_dte = max((item[0].expiration - chain.as_of.date()).days for item in usable)
    trade_request = _trade_request(
        request,
        policy,
        chain,
        maximum_dte=maximum_dte,
    )
    by_expiry: dict[
        date,
        list[tuple[ThesisQuote, QuoteSnapshot, tuple[str, ...]]],
    ] = defaultdict(list)
    for item in usable:
        by_expiry[item[0].expiration].append(item)
    for expiry in by_expiry:
        by_expiry[expiry].sort(key=lambda item: (item[0].strike, item[0].symbol))

    global_blockers = _global_blockers(policy=policy, scan_time=scan_time)
    generated: Counter[str] = Counter()
    blocked: Counter[str] = Counter()
    admissible: list[EnumeratedCandidate] = []

    def add(
        *,
        architecture: Architecture,
        leg_specs: list[tuple[PositionSide, int, QuoteSnapshot]],
        quantity: int,
        warnings: list[str],
    ) -> None:
        generated[architecture.value] += 1
        candidate = build_candidate(
            architecture=architecture,
            recipe=recipes[architecture],
            leg_specs=leg_specs,
            quantity=quantity,
            request=trade_request,
            horizon_compatible=True,
        )
        blockers = [*global_blockers, *candidate.hard_vetoes]
        if candidate.risk.entry_debit <= 0:
            blockers.append("NON_DEBIT_OR_MARGIN_REQUIREMENT")
        if candidate.risk.total_cost <= 0:
            blockers.append("NON_POSITIVE_TOTAL_COST")
        if blockers:
            blocked.update(set(blockers))
            return
        admissible.append(
            EnumeratedCandidate(
                candidate=candidate,
                warnings=tuple(sorted(set(warnings))),
            )
        )

    for _expiry, items in sorted(by_expiry.items(), key=lambda pair: pair[0]):
        for _, snapshot_quote, warnings in items:
            for quantity in range(1, policy.maximum_contracts + 1):
                add(
                    architecture=Architecture.LONG_CALL,
                    leg_specs=[(PositionSide.LONG, 1, snapshot_quote)],
                    quantity=quantity,
                    warnings=list(warnings),
                )

        maximum_spread_quantity = policy.maximum_contracts // 2
        if maximum_spread_quantity:
            for lower_index, lower in enumerate(items):
                for upper in items[lower_index + 1 :]:
                    width = upper[0].strike - lower[0].strike
                    if width > policy.maximum_vertical_width:
                        break
                    for quantity in range(1, maximum_spread_quantity + 1):
                        add(
                            architecture=Architecture.BULL_CALL_SPREAD,
                            leg_specs=[
                                (PositionSide.LONG, 1, lower[1]),
                                (PositionSide.SHORT, 1, upper[1]),
                            ],
                            quantity=quantity,
                            warnings=[*lower[2], *upper[2]],
                        )

        maximum_butterfly_quantity = policy.maximum_contracts // 4
        if maximum_butterfly_quantity:
            by_strike = {item[0].strike: item for item in items}
            strikes = sorted(by_strike)
            for center_strike in strikes:
                for lower_strike in (strike for strike in strikes if strike < center_strike):
                    width = center_strike - lower_strike
                    if width > policy.maximum_butterfly_wing_width:
                        continue
                    upper_strike = center_strike + width
                    if upper_strike not in by_strike:
                        continue
                    lower_item = by_strike[lower_strike]
                    center_item = by_strike[center_strike]
                    upper_item = by_strike[upper_strike]
                    for quantity in range(1, maximum_butterfly_quantity + 1):
                        add(
                            architecture=Architecture.CALL_BUTTERFLY,
                            leg_specs=[
                                (PositionSide.LONG, 1, lower_item[1]),
                                (PositionSide.SHORT, 2, center_item[1]),
                                (PositionSide.LONG, 1, upper_item[1]),
                            ],
                            quantity=quantity,
                            warnings=[
                                *lower_item[2],
                                *center_item[2],
                                *upper_item[2],
                            ],
                        )

    admissible.sort(key=lambda item: item.candidate.candidate_id)
    return EnumerationResult(
        candidates=tuple(admissible),
        quote_rejections=quote_rejections,
        generated_by_architecture=dict(sorted(generated.items())),
        generated_candidates=sum(generated.values()),
        blocked_reasons=dict(sorted(blocked.items())),
    )
