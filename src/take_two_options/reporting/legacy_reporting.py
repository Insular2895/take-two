"""Legacy V1 report rendering kept for non-regression."""

from __future__ import annotations

from take_two_options.domain import DecisionReport, StrategyCandidate, StrategyLeg
from take_two_options.reporting.trade_economics import render_trade_economics_markdown


def render_json(report: DecisionReport) -> str:
    return report.model_dump_json(indent=2)


def _money(value: float | None) -> str:
    if value is None:
        return "unbounded/unknown"
    normalized = 0.0 if abs(value) < 0.005 else value
    return f"${normalized:,.2f}"


def _leg_markdown(index: int, leg: StrategyLeg) -> str:
    if leg.instrument_type == "stock":
        return (
            f"- Leg {index}: `{leg.side.value}` {leg.quantity} `{leg.underlying_symbol}` "
            f"at {_money(leg.stock_price)}"
        )
    assert leg.option_quote is not None
    quote = leg.option_quote
    contract = quote.contract
    return (
        f"- Leg {index}: `{leg.side.value}` {leg.quantity} `{contract.local_symbol}`; "
        f"{contract.option_type.value} {contract.strike:g}, expiry "
        f"`{contract.expiration.isoformat()}`, bid/ask {_money(quote.bid)}/{_money(quote.ask)}, "
        f"multiplier {contract.multiplier:g}, deliverable `{contract.deliverable}`"
    )


def _candidate_markdown(candidate: StrategyCandidate) -> list[str]:
    risk = candidate.risk_metrics
    execution = candidate.execution_estimate
    break_even = "none"
    if risk is not None and risk.break_even_points:
        break_even = ", ".join(f"${point:,.2f}" for point in risk.break_even_points)
    lines = [
        f"### {candidate.name}",
        "",
        f"- ID: `{candidate.id}`",
        f"- Status: `{candidate.status.value}`",
        f"- Description: {candidate.description}",
    ]
    lines.extend(_leg_markdown(index, leg) for index, leg in enumerate(candidate.legs, start=1))
    if not candidate.legs:
        lines.append("- Legs: none")
    if execution is not None:
        lines.extend(
            [
                f"- Executable debit: {_money(execution.executable_debit)}",
                f"- Executable credit: {_money(execution.executable_credit)}",
                f"- Fees / slippage: {_money(execution.fees)} / {_money(execution.slippage)}",
                f"- Liquidity heuristic: {execution.liquidity_score:.3f}",
                f"- Margin estimate: {_money(execution.margin_requirement)}",
            ]
        )
    if risk is not None:
        lines.extend(
            [
                f"- Maximum gain: {_money(risk.max_gain)}",
                f"- Maximum loss: {_money(risk.max_loss)}",
                f"- Break-even: {break_even}",
                f"- Net Greeks delta/gamma/theta/vega/rho: {risk.net_delta:.3f} / "
                f"{risk.net_gamma:.3f} / {risk.net_theta:.3f} / {risk.net_vega:.3f} / "
                f"{risk.net_rho:.3f}",
            ]
        )
    if candidate.pricing_results:
        lines.append("- Option model diagnostics:")
        for result in candidate.pricing_results:
            lines.append(
                f"  - `{result.contract_symbol}`: `{result.model.value}` price "
                f"{_money(result.price)}, European {_money(result.european_benchmark)}, "
                f"early-exercise premium {_money(result.early_exercise_premium)}"
            )
    if candidate.exercise_risks:
        lines.append("- Exercise-risk diagnostics:")
        for assessment in candidate.exercise_risks:
            lines.append(
                f"  - `{assessment.contract_symbol}` `{assessment.side.value}`: assignment "
                f"`{assessment.assignment_risk.value}`, pin `{assessment.pin_risk.value}`, "
                f"extrinsic {_money(assessment.extrinsic_value)}"
            )
    if candidate.score:
        lines.append(f"- Score summary: {candidate.score.total:.3f}")
        lines.append("- Score components:")
        for name, value in candidate.score.model_dump(exclude={"total"}).items():
            lines.append(f"  - `{name}`: {value:.3f}")
    else:
        lines.append("- Score: vetoed")
    if candidate.veto_reasons:
        lines.append(f"- Vetoes: {'; '.join(candidate.veto_reasons)}")
    lines.append(f"- Assumptions: {'; '.join(candidate.assumptions) or 'none'}")
    lines.append(f"- Failure modes: {'; '.join(candidate.failure_modes) or 'none'}")
    lines.append(f"- Contradictions: {'; '.join(candidate.contradictions) or 'none recorded'}")
    lines.extend(["", "Scenario P&L (illustrative):", ""])
    for scenario in candidate.scenarios:
        attribution = ""
        if scenario.attribution:
            attribution_item = scenario.attribution
            attribution = (
                f"; attribution D/G/T/V/R/C/resid "
                f"{_money(attribution_item.delta)}/{_money(attribution_item.gamma)}/"
                f"{_money(attribution_item.theta)}/{_money(attribution_item.vega)}/"
                f"{_money(attribution_item.rho)}/{_money(attribution_item.execution_costs)}/"
                f"{_money(attribution_item.residual)}"
            )
        lines.append(
            f"- `{scenario.name}`: {_money(scenario.pnl)} at spot {_money(scenario.spot)}"
            f"{attribution}"
        )
    lines.extend(["", "Rules and evidence:", ""])
    for rule in candidate.rule_evaluations:
        marker = "PASS" if rule.passed else "FAIL"
        lines.append(f"- `{marker}` `{rule.rule_id}` ({rule.status.value}): {rule.message}")
    for evidence in candidate.evidence:
        lines.append(
            f"- Evidence `{evidence.id}` ({evidence.status.value}, {evidence.confidence_level}): "
            f"`{evidence.uri}`"
        )
    if candidate.trade_economics is not None:
        lines.extend(
            [
                "",
                render_trade_economics_markdown(
                    candidate.trade_economics,
                    heading_level=4,
                ),
            ]
        )
    lines.append("")
    return lines


def render_markdown(report: DecisionReport) -> str:
    bundle = report.bundle
    lines = [
        "# TTWO options research decision report",
        "",
        (
            "> Read-only research. This report is not an investment recommendation and "
            "cannot authorize an order."
        ),
        "",
        "## Input posture",
        "",
        f"- Report: `{report.report_id}`",
        f"- Analysis timestamp: `{report.created_at.isoformat()}`",
        f"- Model readiness: `{report.model_readiness.value}`",
        f"- Underlying: `{bundle.underlying.ticker}` at {_money(bundle.underlying.price)}",
        f"- Market-data source: `{bundle.underlying.freshness.source}`",
        f"- Fundamental direction: `{bundle.fundamental.direction}`",
        f"- Thesis: {bundle.fundamental.thesis}",
        f"- Catalyst: {bundle.fundamental.catalyst}",
        f"- Invalidation: {bundle.fundamental.invalidation}",
        (
            "- Expectations implied: "
            f"{bundle.fundamental.expectations_implied or 'not supplied by the fixture'}"
        ),
        (
            "- Ranked research alternatives: "
            + ", ".join(f"`{item}`" for item in report.ranked_candidate_ids)
        ),
        (
            "- Pareto research set: "
            + ", ".join(f"`{item}`" for item in report.pareto_candidate_ids)
        ),
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in report.global_warnings)
    if report.model_limitations:
        lines.extend(["", "## Model limitations", ""])
        lines.extend(f"- {limitation}" for limitation in report.model_limitations)
    if report.surface_diagnostics is not None:
        surface = report.surface_diagnostics
        lines.extend(
            [
                "",
                "## Volatility surface",
                "",
                f"- Available: `{str(surface.available).lower()}`",
                f"- Expiries / strikes: {surface.expiry_count} / {surface.strike_count}",
                f"- Interpolated / extrapolated contracts: "
                f"{surface.interpolated_contracts} / {surface.extrapolated_contracts}",
            ]
        )
    if report.data_issues:
        lines.extend(["", "## Data issues", ""])
        lines.extend(f"- {issue}" for issue in report.data_issues)
    lines.extend(["", "## Candidates", ""])
    for candidate in report.candidates:
        lines.extend(_candidate_markdown(candidate))
    lines.extend(
        [
            "## Required before any future execution layer",
            "",
            (
                "- Refresh spot, complete option chain, IV surface, rates, events, dividends, "
                "borrow, fees, and margin."
            ),
            "- Reconcile broker contract semantics and executable combo quotes.",
            (
                "- Independently validate thesis, catalyst dates, invalidation, payoff, "
                "assignment, and exit rules."
            ),
            (
                "- Complete paper validation and explicit human approval under a separately "
                "reviewed execution policy."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def render_decision_journal(report: DecisionReport) -> str:
    lines = [
        "# TTWO V2 decision journal",
        "",
        f"- Report ID: `{report.report_id}`",
        f"- Freeze time: `{report.created_at.isoformat()}`",
        "- Decision posture: `read_only_research`",
        f"- Model readiness: `{report.model_readiness.value}`",
        "- Human action: `wait_for_proof`",
        "- Order capability: `forbidden`",
        "",
        "## Candidate dispositions",
        "",
    ]
    for candidate in report.candidates:
        reason = "; ".join(candidate.veto_reasons) or "Human validation remains required"
        lines.append(f"- `{candidate.id}` -> `{candidate.status.value}`: {reason}")
    lines.extend(
        [
            "",
            "## Re-underwrite trigger",
            "",
            (
                "Re-run only after replacing fixture values with source-backed, timestamped "
                "market and event data."
            ),
            "",
        ]
    )
    return "\n".join(lines)
