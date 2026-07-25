"""Legacy V1 explainable vetoes kept for non-regression."""

from __future__ import annotations

from take_two_options.domain import (
    CandidateStatus,
    DataFreshness,
    EvidenceStatus,
    MarketDataBundle,
    PositionSide,
    RuleEvaluation,
    Severity,
    StrategyCandidate,
    StrategyKind,
)


def _add_rule(
    candidate: StrategyCandidate,
    *,
    rule_id: str,
    passed: bool,
    message: str,
    blocks: bool = False,
    severity: Severity | None = None,
    evidence_ids: list[str] | None = None,
) -> None:
    candidate.rule_evaluations.append(
        RuleEvaluation(
            rule_id=rule_id,
            status=EvidenceStatus.READ_ONLY_GATE,
            passed=passed,
            severity=severity or (Severity.BLOCKER if blocks else Severity.INFO),
            message=message,
            blocks=blocks,
            evidence_ids=evidence_ids or [],
        )
    )
    if blocks and candidate.kind is not StrategyKind.NO_TRADE:
        candidate.veto_reasons.append(f"{rule_id}: {message}")


def freshness_is_stale(freshness: DataFreshness, bundle: MarketDataBundle) -> bool:
    declared_stale = freshness.is_stale or freshness.status.value != "current"
    if freshness.max_age_seconds is None:
        return declared_stale
    age_seconds = (bundle.analysis_timestamp - freshness.as_of).total_seconds()
    return declared_stale or age_seconds < 0 or age_seconds > freshness.max_age_seconds


def apply_vetoes(candidate: StrategyCandidate, bundle: MarketDataBundle) -> CandidateStatus:
    """Apply data, execution, risk, event, and evidence gates in deterministic order."""
    candidate.veto_reasons = []
    initial_rules = list(candidate.rule_evaluations)
    evidence_ids = [item.id for item in candidate.evidence]

    missing_provenance = (
        not candidate.evidence or not bundle.underlying.sources or not bundle.fundamental.sources
    )
    _add_rule(
        candidate,
        rule_id="VETO-PROVENANCE",
        passed=not missing_provenance,
        message="Decision inputs must have explicit provenance",
        blocks=missing_provenance,
        evidence_ids=evidence_ids,
    )

    decision_evidence = [
        *candidate.evidence,
        *bundle.underlying.sources,
        *bundle.fundamental.sources,
        bundle.portfolio.source,
        bundle.risk_free_rate_source,
        bundle.volatility_source,
        *(dividend.source for dividend in bundle.dividends),
    ]
    if bundle.dividend_yield_source is not None:
        decision_evidence.append(bundle.dividend_yield_source)
    if bundle.volatility_surface is not None:
        decision_evidence.append(bundle.volatility_surface.source)
    invalid_evidence = [
        item.id
        for item in decision_evidence
        if item.used_for_decision and not item.status.can_authorize_research
    ]
    _add_rule(
        candidate,
        rule_id="VETO-EVIDENCE-STATUS",
        passed=not invalid_evidence,
        message=(
            "All decision evidence is validated for research"
            if not invalid_evidence
            else f"Non-authorizing evidence: {', '.join(invalid_evidence)}"
        ),
        blocks=bool(invalid_evidence),
        evidence_ids=evidence_ids,
    )

    invalid_rules = [
        rule.rule_id
        for rule in initial_rules
        if not rule.status.can_authorize_research or (not rule.passed and rule.blocks)
    ]
    _add_rule(
        candidate,
        rule_id="VETO-RULE-STATUS",
        passed=not invalid_rules,
        message=(
            "Candidate rules are usable as read-only gates"
            if not invalid_rules
            else f"Blocked or unvalidated rules: {', '.join(invalid_rules)}"
        ),
        blocks=bool(invalid_rules),
        evidence_ids=evidence_ids,
    )

    underlying_stale = freshness_is_stale(bundle.underlying.freshness, bundle)
    _add_rule(
        candidate,
        rule_id="VETO-UNDERLYING-FRESHNESS",
        passed=not underlying_stale,
        message="Underlying snapshot must be current for its declared fixture window",
        blocks=underlying_stale,
    )

    freshness_inputs = {
        "FUNDAMENTALS": bundle.fundamental.freshness,
        "PORTFOLIO": bundle.portfolio.freshness,
        "RISK-FREE-RATE": bundle.risk_free_rate_freshness,
        "VOLATILITY": bundle.volatility_freshness,
    }
    for label, freshness in freshness_inputs.items():
        stale = freshness_is_stale(freshness, bundle)
        _add_rule(
            candidate,
            rule_id=f"VETO-{label}-FRESHNESS",
            passed=not stale,
            message=f"{label.lower()} input must be current within its declared maximum age",
            blocks=stale,
        )

    if bundle.dividend_yield_freshness is not None:
        stale_dividend_yield = freshness_is_stale(bundle.dividend_yield_freshness, bundle)
        _add_rule(
            candidate,
            rule_id="VETO-DIVIDEND-YIELD-FRESHNESS",
            passed=not stale_dividend_yield,
            message="Dividend-yield input must be current",
            blocks=stale_dividend_yield,
        )
    if bundle.volatility_surface is not None:
        stale_surface = freshness_is_stale(bundle.volatility_surface.freshness, bundle)
        _add_rule(
            candidate,
            rule_id="VETO-VOL-SURFACE-FRESHNESS",
            passed=not stale_surface,
            message="Volatility surface must be current",
            blocks=stale_surface,
            evidence_ids=[bundle.volatility_surface.source.id],
        )
    for index, dividend in enumerate(bundle.dividends, start=1):
        stale_dividend = freshness_is_stale(dividend.freshness, bundle)
        _add_rule(
            candidate,
            rule_id=f"VETO-DIVIDEND-{index}-FRESHNESS",
            passed=not stale_dividend,
            message=f"Dividend forecast for {dividend.ex_date.isoformat()} must be current",
            blocks=stale_dividend,
            evidence_ids=[dividend.source.id],
        )

    for leg_index, leg in enumerate(candidate.legs, start=1):
        if leg.instrument_type != "option" or leg.option_quote is None:
            continue
        quote = leg.option_quote
        contract = quote.contract
        prefix = f"LEG-{leg_index}"
        stale = freshness_is_stale(quote.freshness, bundle)
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-FRESHNESS",
            passed=not stale,
            message=f"{contract.local_symbol} quote must be current",
            blocks=stale,
            evidence_ids=[quote.source.id],
        )
        quote_valid = (
            quote.bid is not None
            and quote.ask is not None
            and quote.bid > 0
            and quote.ask > 0
            and quote.ask >= quote.bid
        )
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-BID-ASK",
            passed=quote_valid,
            message=f"{contract.local_symbol} requires a positive, ordered bid/ask",
            blocks=not quote_valid,
            evidence_ids=[quote.source.id],
        )
        contract_valid = bool(
            contract.multiplier
            and contract.deliverable
            and contract.settlement_cycle
            and contract.exercise_style
        )
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-CONTRACT",
            passed=contract_valid,
            message=f"{contract.local_symbol} contract semantics must be complete",
            blocks=not contract_valid,
            evidence_ids=[quote.source.id],
        )
        adjusted_unknown = contract.adjusted_contract and not contract.adjustment_understood
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-ADJUSTMENT",
            passed=not adjusted_unknown,
            message=f"{contract.local_symbol} adjusted deliverable must be understood",
            blocks=adjusted_unknown,
            evidence_ids=[quote.source.id],
        )
        source_invalid = not quote.source.status.can_authorize_research
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-SOURCE",
            passed=not source_invalid,
            message=f"{contract.local_symbol} quote source must authorize research use",
            blocks=source_invalid,
            evidence_ids=[quote.source.id],
        )
        liquidity_missing = quote.volume is None or quote.open_interest is None
        liquidity_zero = (quote.volume or 0) <= 0 or (quote.open_interest or 0) <= 0
        spread_too_wide = False
        if quote_valid and quote.mid:
            spread_too_wide = (quote.ask - quote.bid) / quote.mid > 0.35  # type: ignore[operator]
        liquidity_veto = liquidity_missing or liquidity_zero or spread_too_wide
        _add_rule(
            candidate,
            rule_id=f"VETO-{prefix}-LIQUIDITY",
            passed=not liquidity_veto,
            message=(
                f"{contract.local_symbol} requires non-zero volume/OI and <=35% relative spread"
            ),
            blocks=liquidity_veto,
            evidence_ids=[quote.source.id],
        )

    untreated_actions = [
        action.description for action in bundle.underlying.corporate_actions if not action.handled
    ]
    untreated_events = [
        event.name for event in bundle.underlying.events if event.critical and not event.handled
    ]
    _add_rule(
        candidate,
        rule_id="VETO-CORPORATE-ACTIONS",
        passed=not untreated_actions,
        message=(
            "Corporate actions are explicitly handled"
            if not untreated_actions
            else f"Untreated corporate actions: {', '.join(untreated_actions)}"
        ),
        blocks=bool(untreated_actions),
    )
    _add_rule(
        candidate,
        rule_id="VETO-EVENT-RISK",
        passed=not untreated_events,
        message=(
            "Critical market events are explicitly handled"
            if not untreated_events
            else f"Untreated critical events: {', '.join(untreated_events)}"
        ),
        blocks=bool(untreated_events),
    )

    option_legs = [leg for leg in candidate.legs if leg.instrument_type == "option"]
    has_short_option = any(leg.side is PositionSide.SHORT for leg in option_legs)
    costs_missing = False
    if option_legs:
        costs_missing = (
            bundle.portfolio.commission_per_option_contract is None
            or bundle.portfolio.slippage_per_option_contract is None
        )
    elif candidate.kind is StrategyKind.STOCK:
        costs_missing = (
            bundle.portfolio.stock_commission is None or bundle.portfolio.stock_slippage_bps is None
        )
    _add_rule(
        candidate,
        rule_id="VETO-COSTS",
        passed=not costs_missing,
        message="Fees and slippage must be explicit for the instrument",
        blocks=costs_missing,
    )

    margin_unknown = has_short_option and (
        not bundle.portfolio.margin_known
        or candidate.execution_estimate is None
        or candidate.execution_estimate.margin_requirement is None
    )
    _add_rule(
        candidate,
        rule_id="VETO-MARGIN",
        passed=not margin_unknown,
        message="Broker margin must be known for any structure containing a short option",
        blocks=margin_unknown,
    )

    risk_unknown = candidate.risk_metrics is None or candidate.risk_metrics.max_loss is None
    unbounded = candidate.risk_metrics is not None and candidate.risk_metrics.unbounded_risk
    _add_rule(
        candidate,
        rule_id="VETO-MAX-LOSS",
        passed=not risk_unknown,
        message="Maximum loss must be explicitly calculated",
        blocks=risk_unknown,
    )
    _add_rule(
        candidate,
        rule_id="VETO-UNBOUNDED-RISK",
        passed=not unbounded,
        message="Unbounded-risk structures are disabled in V1",
        blocks=unbounded,
    )

    expires_too_soon = any(
        leg.option_quote is not None
        and leg.option_quote.contract.expiration < bundle.fundamental.catalyst_window_end
        for leg in option_legs
    )
    _add_rule(
        candidate,
        rule_id="VETO-CATALYST-COVERAGE",
        passed=not expires_too_soon,
        message="Option expiration must cover the declared catalyst window",
        blocks=expires_too_soon,
    )

    scenarios_missing = not candidate.scenarios
    _add_rule(
        candidate,
        rule_id="VETO-SCENARIOS",
        passed=not scenarios_missing,
        message="Delay, gap, IV, event, and liquidity scenarios must be visible",
        blocks=scenarios_missing,
    )

    if has_short_option:
        candidate.human_validation_required = True
        risk_summary = "; ".join(
            f"{risk.contract_symbol}: assignment={risk.assignment_risk.value}, "
            f"pin risk={risk.pin_risk.value}"
            for risk in candidate.exercise_risks
            if risk.side is PositionSide.SHORT
        )
        _add_rule(
            candidate,
            rule_id="GATE-ASSIGNMENT-PIN",
            passed=True,
            message=(
                "American assignment and pin risk require human review"
                + (f" ({risk_summary})" if risk_summary else "")
            ),
            severity=Severity.WARNING,
        )

    uncalibrated_models = [
        model.value
        for model in bundle.simulation.models
        if (
            model.value == "merton_jump_diffusion"
            and bundle.simulation.jump.calibration_status.value != "calibrated"
        )
        or (
            model.value == "heston_full_truncation"
            and bundle.simulation.heston.calibration_status.value != "calibrated"
        )
    ]
    _add_rule(
        candidate,
        rule_id="GATE-MODEL-CALIBRATION",
        passed=not uncalibrated_models,
        message=(
            "Configured simulation models are calibrated"
            if not uncalibrated_models
            else f"Screen-grade uncalibrated models: {', '.join(uncalibrated_models)}"
        ),
        severity=Severity.WARNING if uncalibrated_models else Severity.INFO,
    )

    if candidate.kind is StrategyKind.NO_TRADE:
        candidate.status = CandidateStatus.NO_TRADE
    elif candidate.veto_reasons:
        candidate.status = CandidateStatus.BLOCKED
    elif candidate.human_validation_required:
        candidate.status = CandidateStatus.HUMAN_REVIEW_REQUIRED
    else:
        candidate.status = CandidateStatus.RESEARCH_CANDIDATE
    return candidate.status
