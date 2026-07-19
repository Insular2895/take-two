"""Conservative candidate generation from a supplied read-only bundle."""

from __future__ import annotations

from take_two_options.domain import (
    EvidenceReference,
    EvidenceStatus,
    MarketDataBundle,
    OptionQuote,
    OptionType,
    PositionSide,
    RuleEvaluation,
    Severity,
    StrategyCandidate,
    StrategyKind,
    StrategyLeg,
)


def _corpus_evidence(bundle: MarketDataBundle) -> list[EvidenceReference]:
    timestamp = bundle.analysis_timestamp
    return [
        EvidenceReference(
            id="CORPUS-CLEAN-RULESET-2026",
            title="Clean usable ruleset 2026",
            source_type="repository_rulebook",
            uri="option-research-engine/research/documentary/CLEAN_USABLE_RULESET_2026.md",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=timestamp,
            confidence_level="high",
            notes="Authorizes only conservative read-only research gates",
        ),
        EvidenceReference(
            id="CORPUS-TTWO-OPERATIONAL-2026",
            title="TTWO GTA VI operational research 2026",
            source_type="repository_research_note",
            uri="option-research-engine/research/documentary/TTWO_GTA6_OPERATIONAL_RESEARCH_2026.md",
            status=EvidenceStatus.READ_ONLY_GATE,
            accessed_at=timestamp,
            confidence_level="medium",
            notes="Facts must be refreshed before any human decision",
        ),
    ]


def _base_rules(evidence: list[EvidenceReference]) -> list[RuleEvaluation]:
    evidence_ids = [item.id for item in evidence]
    return [
        RuleEvaluation(
            rule_id="R-DECISION-001",
            status=EvidenceStatus.READ_ONLY_GATE,
            passed=True,
            severity=Severity.INFO,
            message="Compare no-trade, stock, directional option, and bounded spread alternatives",
            evidence_ids=evidence_ids,
        ),
        RuleEvaluation(
            rule_id="R-GREEKS-001",
            status=EvidenceStatus.READ_ONLY_GATE,
            passed=True,
            severity=Severity.INFO,
            message="Aggregate Greeks using each contract multiplier",
            evidence_ids=evidence_ids,
        ),
        RuleEvaluation(
            rule_id="R-OPTIONS-001",
            status=EvidenceStatus.READ_ONLY_GATE,
            passed=True,
            severity=Severity.INFO,
            message="Keep thesis, catalyst, invalidation, IV, liquidity, and max loss explicit",
            evidence_ids=evidence_ids,
        ),
    ]


def _eligible_quotes(bundle: MarketDataBundle, option_type: OptionType) -> list[OptionQuote]:
    quotes = [
        quote
        for quote in bundle.option_quotes
        if quote.contract.option_type is option_type
        and quote.contract.expiration > bundle.analysis_timestamp
    ]
    return sorted(
        quotes,
        key=lambda quote: (
            quote.contract.expiration < bundle.fundamental.catalyst_window_end,
            abs(quote.contract.strike - bundle.underlying.price),
            quote.contract.expiration,
        ),
    )


def _same_expiration(quotes: list[OptionQuote], anchor: OptionQuote) -> list[OptionQuote]:
    return [quote for quote in quotes if quote.contract.expiration == anchor.contract.expiration]


def generate_candidates(bundle: MarketDataBundle) -> list[StrategyCandidate]:
    evidence = _corpus_evidence(bundle)
    rules = _base_rules(evidence)
    common = {
        "evidence": evidence,
        "rule_evaluations": rules,
        "human_validation_required": True,
    }
    candidates = [
        StrategyCandidate(
            id="ttwo-no-trade",
            kind=StrategyKind.NO_TRADE,
            name="No trade / wait for proof",
            description=(
                "Reference alternative that preserves capital and waits for refreshed evidence"
            ),
            assumptions=["No position is opened"],
            failure_modes=["Opportunity cost if the thesis resolves before evidence is refreshed"],
            **common,
        ),
        StrategyCandidate(
            id="ttwo-stock-research",
            kind=StrategyKind.STOCK,
            name="TTWO stock research proxy",
            description=(
                "Illustrative long-stock comparison using a non-executable research quantity"
            ),
            legs=[
                StrategyLeg(
                    instrument_type="stock",
                    side=PositionSide.LONG,
                    quantity=bundle.portfolio.research_share_quantity,
                    underlying_symbol=bundle.underlying.ticker,
                    stock_price=bundle.underlying.price,
                )
            ],
            assumptions=["Research quantity is not a sizing recommendation"],
            failure_modes=["Full equity downside", "Event delay", "Multiple compression"],
            **common,
        ),
    ]

    calls = _eligible_quotes(bundle, OptionType.CALL)
    puts = _eligible_quotes(bundle, OptionType.PUT)
    if calls:
        long_call = calls[0]
        candidates.append(
            StrategyCandidate(
                id="ttwo-long-call",
                kind=StrategyKind.LONG_CALL,
                name="Long call",
                description="Defined-premium bullish exposure across the catalyst window",
                legs=[
                    StrategyLeg(
                        instrument_type="option",
                        side=PositionSide.LONG,
                        quantity=1,
                        option_quote=long_call,
                    )
                ],
                assumptions=[
                    "QuantLib American model values are indicative and not executable quotes"
                ],
                failure_modes=["IV crush", "Theta decay", "Catalyst delay beyond expiration"],
                **common,
            )
        )
        higher_calls = [
            quote
            for quote in _same_expiration(calls, long_call)
            if quote.contract.strike > long_call.contract.strike
        ]
        if higher_calls:
            short_call = min(higher_calls, key=lambda quote: quote.contract.strike)
            candidates.append(
                StrategyCandidate(
                    id="ttwo-bull-call-spread",
                    kind=StrategyKind.BULL_CALL_SPREAD,
                    name="Bull call spread",
                    description="Bounded-risk bullish vertical with capped upside",
                    legs=[
                        StrategyLeg(
                            instrument_type="option",
                            side=PositionSide.LONG,
                            quantity=1,
                            option_quote=long_call,
                        ),
                        StrategyLeg(
                            instrument_type="option",
                            side=PositionSide.SHORT,
                            quantity=1,
                            option_quote=short_call,
                        ),
                    ],
                    assumptions=["Both legs execute together at the modeled executable net debit"],
                    failure_modes=["Capped upside", "Assignment and pin risk", "Legging risk"],
                    **common,
                )
            )

    if puts:
        long_put = puts[0]
        candidates.append(
            StrategyCandidate(
                id="ttwo-long-put",
                kind=StrategyKind.LONG_PUT,
                name="Long put",
                description="Defined-premium bearish or downside-event research exposure",
                legs=[
                    StrategyLeg(
                        instrument_type="option",
                        side=PositionSide.LONG,
                        quantity=1,
                        option_quote=long_put,
                    )
                ],
                assumptions=[
                    "QuantLib American model values are indicative and not executable quotes"
                ],
                failure_modes=["IV crush", "Theta decay", "Bullish gap"],
                **common,
            )
        )
        lower_puts = [
            quote
            for quote in _same_expiration(puts, long_put)
            if quote.contract.strike < long_put.contract.strike
        ]
        if lower_puts:
            short_put = max(lower_puts, key=lambda quote: quote.contract.strike)
            candidates.append(
                StrategyCandidate(
                    id="ttwo-bear-put-spread",
                    kind=StrategyKind.BEAR_PUT_SPREAD,
                    name="Bear put spread",
                    description="Bounded-risk bearish vertical with capped payoff",
                    legs=[
                        StrategyLeg(
                            instrument_type="option",
                            side=PositionSide.LONG,
                            quantity=1,
                            option_quote=long_put,
                        ),
                        StrategyLeg(
                            instrument_type="option",
                            side=PositionSide.SHORT,
                            quantity=1,
                            option_quote=short_put,
                        ),
                    ],
                    assumptions=["Both legs execute together at the modeled executable net debit"],
                    failure_modes=[
                        "Capped downside payoff",
                        "Assignment and pin risk",
                        "Legging risk",
                    ],
                    **common,
                )
            )
    return candidates
