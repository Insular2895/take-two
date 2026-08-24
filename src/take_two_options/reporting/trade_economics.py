"""Human-readable renderer for the versioned M0.1 trade-economics ticket."""

from __future__ import annotations

from take_two_options.trade_economics_models import GreekMeasure, TradeEconomicsTicket


def _amount(value: float | None, currency: str) -> str:
    return "UNKNOWN" if value is None else f"{value:,.2f} {currency}"


def _number(value: float | None, digits: int = 6) -> str:
    return "UNKNOWN" if value is None else f"{value:.{digits}f}"


def _percentage(value: float | None) -> str:
    return "UNKNOWN" if value is None else f"{value * 100:.2f}%"


def _budget_amount(value: float | None, currency: str, *, signed: bool = False) -> str:
    if value is None:
        return "UNKNOWN"
    symbol = {"EUR": "€", "USD": "$"}.get(currency, f"{currency} ")
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{symbol}{value:,.2f}"


def _greek(measure: GreekMeasure | None) -> str:
    if measure is None:
        return "disabled"
    return f"{measure.value:.6f} {measure.unit} ({measure.confidence.value})"


def render_trade_economics_markdown(
    ticket: TradeEconomicsTicket,
    *,
    heading_level: int = 1,
) -> str:
    """Render every financially material M0.1 ticket section from the typed object."""
    heading_level = min(max(heading_level, 1), 5)
    h1 = "#" * heading_level
    h2 = "#" * min(heading_level + 1, 6)
    currency = ticket.currency
    lines = [
        f"{h1} {ticket.underlying} — {ticket.strategy_name}",
        "",
        f"- Ticket schema: `{ticket.schema_version}`",
        f"- Fixture status: `{ticket.fixture_status}`",
        f"- Classification: `{ticket.classification}`",
        f"- Market timestamp: `{ticket.exact_market_timestamp.isoformat()}`",
        f"- Currency: `{currency}`",
        f"- Data freshness: `{ticket.data_freshness_status}`",
        f"- Expirations: `{', '.join(value.isoformat() for value in ticket.expirations)}`",
        f"- Exact DTE: `{ticket.dte_exact_days:.8f}` days",
        f"- Lifecycle policy: `{ticket.lifecycle_policy}`",
        f"- Managed exit deadline: "
        f"`{ticket.managed_exit_deadline.isoformat() if ticket.managed_exit_deadline else 'n/a'}`",
        f"- Intraday precision: `{ticket.intraday_precision_status.value}`",
    ]
    if ticket.intraday_precision_warning:
        lines.append(f"- Intraday warning: {ticket.intraday_precision_warning}")
    if ticket.managed_exit_deadline is not None:
        lines.append(
            "- Calendar/diagonal lifecycle after the first leg expiry is intentionally not "
            "modeled. M0.1 assumes managed closure before first expiry."
        )
        lines.extend(
            [
                "- Mixed-expiry lifecycle policy: "
                f"`{ticket.mixed_expiry_lifecycle_policy or 'UNKNOWN'}`",
                "- Mixed-expiry close buffer: "
                f"`{ticket.mixed_expiry_close_buffer_calendar_days}` calendar days",
                "- Lifecycle config source / version: "
                f"`{ticket.lifecycle_config_source or 'UNKNOWN'}` / "
                f"`{ticket.lifecycle_config_version or 'UNKNOWN'}`",
            ]
        )

    if ticket.budget_diagnostics is not None:
        budget = ticket.budget_diagnostics
        budget_currency = budget.currency
        allowed_overspend = budget.hard_authorized_ceiling - budget.target_budget
        account_headroom = _budget_amount(
            budget.account_headroom_after_trade,
            budget_currency,
            signed=True,
        )
        lines.extend(
            [
                "",
                f"{h2} Budget",
                "",
                f"- Policy version: `{budget.budget_policy_version}`",
                f"- Currency: `{budget_currency}`",
                f"- Target: {_budget_amount(budget.target_budget, budget_currency)}",
                "- Preferred lower: "
                f"{_budget_amount(budget.preferred_lower_bound, budget_currency)}",
                f"- Allowed overspend: {_budget_amount(allowed_overspend, budget_currency)}",
                "- Configured hard ceiling: "
                f"{_budget_amount(budget.hard_authorized_ceiling, budget_currency)}",
                "- Account available: "
                f"{_budget_amount(budget.account_available_capital, budget_currency)}",
                "- Required account reserve: "
                f"{_budget_amount(budget.account_liquidity_reserve, budget_currency)}",
                "- Account deployable: "
                f"{_budget_amount(budget.account_deployable_capital, budget_currency)}",
                "- Effective hard ceiling: "
                f"{_budget_amount(budget.effective_hard_budget_ceiling, budget_currency)}",
                "- Maximum loss cap: "
                f"{_budget_amount(budget.maximum_loss_cap_effective, budget_currency)}",
                "- Buying-power cap: "
                f"{_budget_amount(budget.buying_power_cap_effective, budget_currency)}",
                "",
                f"{h2} This trade — Budget",
                "",
                "- Native executable entry: "
                f"{_budget_amount(budget.native_entry_cash, budget.native_currency or currency)}",
                "- Converted entry before FX cost: "
                f"{_budget_amount(budget.converted_entry_cash_before_fx_cost, budget_currency)}",
                "- Entry FX transaction cost: "
                f"{_budget_amount(budget.entry_fx_cost, budget_currency)} "
                f"(`{budget.entry_fx_cost_status or 'UNKNOWN'}`)",
                "- **REQUIRED ENTRY CASH AFTER FX: "
                f"{_budget_amount(budget.required_entry_cash_after_fx, budget_currency)}**",
                f"- FX rate: `{_number(budget.fx_rate, 8)}`",
                f"- FX rate source: `{budget.fx_rate_source or 'NOT_APPLICABLE'}`",
                f"- FX cost source: `{budget.fx_cost_source or 'NOT_APPLICABLE'}`",
                f"- Maximum loss: {_budget_amount(budget.maximum_loss, budget_currency)}",
                "- Buying power: "
                f"{_budget_amount(budget.buying_power_requirement, budget_currency)}",
                "- Effective capital: "
                f"{_budget_amount(budget.effective_capital_requirement, budget_currency)}",
                "- Delta vs target: "
                f"{_budget_amount(budget.budget_delta_to_target, budget_currency, signed=True)} "
                f"({_percentage(budget.budget_delta_percentage)})",
                "- Headroom: "
                f"{_budget_amount(budget.headroom_to_hard_ceiling, budget_currency, signed=True)}",
                "- Account headroom after trade: "
                f"{account_headroom}",
                f"- Status: `{budget.budget_status.value}`",
                f"- Budget guarantee: `{budget.budget_guarantee_status.value}`",
                f"- Reason codes: `{budget.reason_codes}`",
                f"- Eligible / research / paper: `{budget.eligible}` / "
                f"`{budget.research_eligible}` / `{budget.paper_eligible}`",
            ]
        )
        if ticket.lifecycle_capital_requirement is not None:
            lifecycle_capital = ticket.lifecycle_capital_requirement
            lifecycle_effective = lifecycle_capital.effective_budget_requirement
            lines.extend(
                [
                    "- Lifecycle capital policy / status: "
                    f"`{lifecycle_capital.policy}` / "
                    f"`{lifecycle_capital.calculation_status.value}`",
                    "- Lifecycle effective requirement: "
                    f"{_budget_amount(lifecycle_effective, budget_currency)}",
                    "- Lifecycle buffer / source / version: "
                    f"`{lifecycle_capital.mixed_expiry_close_buffer_calendar_days}` / "
                    f"`{lifecycle_capital.lifecycle_config_source or 'UNKNOWN'}` / "
                    f"`{lifecycle_capital.lifecycle_config_version or 'UNKNOWN'}`",
                ]
            )

    lines.extend(
        [
            "",
            f"{h2} Legs",
            "",
            "| Side | Qty | Type | Strike | Expiration | Bid | Ask | Mid | IV | Mid premium | "
            "Executable paid | Executable received |",
            "| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for leg in ticket.legs:
        lines.append(
            f"| {leg.side} | {leg.quantity} | {leg.option_type or leg.instrument_type} | "
            f"{_number(leg.strike, 2)} | "
            f"{leg.expiration.isoformat() if leg.expiration else 'n/a'} | "
            f"{_number(leg.bid, 4)} | {_number(leg.ask, 4)} | {_number(leg.mid, 4)} | "
            f"{_number(leg.implied_volatility, 6)} | {_amount(leg.mid_premium, currency)} | "
            f"{_amount(leg.executable_premium_paid, currency)} | "
            f"{_amount(leg.executable_premium_received, currency)} |"
        )
        if leg.greeks is not None:
            greeks = leg.greeks
            lines.extend(
                [
                    "",
                    f"Greeks `{leg.local_symbol or 'stock'}`:",
                    "",
                    f"- Delta: `{_greek(greeks.delta)}`",
                    f"- Gamma: `{_greek(greeks.gamma)}`",
                    f"- Theta: `{_greek(greeks.theta)}`",
                    f"- Vega: `{_greek(greeks.vega)}`",
                    f"- Rho: `{_greek(greeks.rho)}`",
                    f"- Vanna: `{_greek(greeks.vanna)}`",
                    f"- Vomma: `{_greek(greeks.vomma)}`",
                    f"- Charm / delta drift: `{_greek(greeks.charm_delta_drift_1_calendar_day)}`",
                    f"- Veta / vega drift: `{_greek(greeks.veta_vega_drift_1_calendar_day)}`",
                    f"- Speed: `{_greek(greeks.speed)}`",
                    f"- Color / gamma drift: `{_greek(greeks.color_gamma_drift_1_calendar_day)}`",
                ]
            )

    entry = ticket.entry_cost
    exit_cost = ticket.exit_cost_estimate
    round_trip = ticket.round_trip_cost
    lines.extend(
        [
            "",
            f"{h2} Cost — Entry",
            "",
            f"- Theoretical midpoint premium paid: "
            f"{_amount(entry.theoretical_mid_premium_paid, currency)}",
            f"- Theoretical midpoint premium received: "
            f"{_amount(entry.theoretical_mid_premium_received, currency)}",
            f"- Theoretical midpoint net premium: "
            f"{_amount(entry.theoretical_mid_net_premium, currency)}",
            f"- Executable premium paid at ask: {_amount(entry.executable_premium_paid, currency)}",
            f"- Executable premium received at bid: "
            f"{_amount(entry.executable_premium_received, currency)}",
            f"- Net executable debit/credit: {_amount(entry.executable_net_premium, currency)}",
            f"- Entry spread cost: {_amount(entry.entry_bid_ask_cost, currency)}",
            f"- Additional slippage: {_amount(entry.entry_slippage, currency)}",
            f"- Commission: {_amount(entry.entry_commission, currency)}",
            f"- FX: {_amount(entry.entry_fx_cost, currency)}",
            f"- **TOTAL ENTRY CASH FLOW: {_amount(entry.total_entry_cash_flow, currency)}**",
            f"- Total capital required: {_amount(entry.total_capital_required, currency)}",
            "",
            f"{h2} Cost — Exit",
            "",
            f"- Exit path estimate: `{exit_cost.exit_path.value}`",
            f"- Expected closing spread: "
            f"{_amount(exit_cost.estimated_exit_bid_ask_cost, currency)}",
            f"- Expected slippage: {_amount(exit_cost.estimated_exit_slippage, currency)}",
            f"- Closing commission: {_amount(exit_cost.closing_commissions, currency)}",
            f"- Exercise cost if relevant: "
            f"{_amount(exit_cost.exercise_cost_if_relevant, currency)}",
            f"- Assignment cost if relevant: "
            f"{_amount(exit_cost.assignment_cost_if_relevant, currency)}",
            f"- Settlement cost if relevant: "
            f"{_amount(exit_cost.settlement_cost_if_relevant, currency)}",
            f"- Hold-to-expiry cost status: `{exit_cost.hold_to_expiry_cost_status}`",
            f"- FX: {_amount(exit_cost.fx_exit_cost, currency)}",
            f"- Total close-before-expiry cost: {_amount(exit_cost.total_exit_cost, currency)} "
            f"(`{exit_cost.exit_cost_status}`)",
            "",
            f"{h2} Round trip",
            "",
            f"- Total estimated round-trip cost: "
            f"{_amount(round_trip.total_round_trip_cost, currency)}",
            f"- Round-trip cost / capital: "
            f"{_percentage(round_trip.round_trip_cost_as_pct_capital)}",
            "",
            f"{h2} Risk / payoff",
            "",
            f"- Margin / buying power: {_amount(ticket.margin.margin_requirement, currency)} / "
            f"{_amount(ticket.margin.buying_power_usage, currency)} "
            f"(`{ticket.margin.status.value}`)",
            f"- Capital at risk: {_amount(ticket.capital_at_risk, currency)}",
            f"- Maximum loss / profit: {_amount(ticket.maximum_loss, currency)} / "
            f"{_amount(ticket.maximum_profit, currency)}",
            f"- Expiration breakevens: `{ticket.expiration_breakevens}`"
            if ticket.managed_exit_deadline is None
            else "- Expiration breakeven: `not applicable to mixed expiry`",
            f"- Lambda / delta-notional / gross-delta leverage: "
            f"`{_number(ticket.leverage.lambda_value_elasticity)}` / "
            f"`{_number(ticket.leverage.delta_notional_leverage)}` / "
            f"`{_number(ticket.leverage.gross_delta_leverage)}`",
        ]
    )

    if ticket.time_decay is not None:
        decay = ticket.time_decay
        lines.extend(
            [
                "",
                f"{h2} Time decay",
                "",
                f"- Net theta today: {_amount(decay.current_net_theta, currency)} per calendar day",
                f"- Theta / capital / day: {_amount(decay.current_net_theta, currency)} / "
                f"{_percentage(decay.theta_per_capital_per_day)} "
                f"(`{decay.theta_capital_status}`)",
                "- Flat Spot Carry is produced by full repricing. Current theta is NOT "
                "multiplied by horizon.",
                "",
                "| Horizon | Flat Spot Carry | Flat Spot Carry % capital | % maximum loss | "
                "Valuation time |",
                "| ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for point in decay.time_decay_curve:
            lines.append(
                f"| {point.horizon_days}d | {_amount(point.flat_spot_carry, currency)} | "
                f"{_percentage(point.carry_as_pct_capital)} | "
                f"{_percentage(point.carry_as_pct_max_loss)} | "
                f"{point.valuation_time.isoformat()} |"
            )
        by_horizon = {point.horizon_days: point for point in decay.time_decay_curve}
        for horizon in (1, 7, 30, 60, 90):
            horizon_point = by_horizon.get(horizon)
            lines.append(
                f"- Flat Spot {horizon}d %: "
                f"{_percentage(horizon_point.carry_as_pct_capital if horizon_point else None)}"
            )
        lines.extend(
            [
                f"- Decay rate 0-7d: {_amount(decay.effective_decay_rate_0_7, currency)} "
                "per calendar day",
                f"- Decay rate 0-30d: {_amount(decay.effective_decay_rate_0_30, currency)} "
                "per calendar day",
                f"- Decay rate 30-60d: {_amount(decay.effective_decay_rate_30_60, currency)} "
                "per calendar day",
                f"- Decay rate 60-90d: {_amount(decay.effective_decay_rate_60_90, currency)} "
                "per calendar day",
                f"- Decay acceleration 30-60: {_amount(decay.decay_acceleration_30_60, currency)}",
                f"- Decay acceleration 60-90: {_amount(decay.decay_acceleration_60_90, currency)}",
                f"- Decay acceleration status: `{decay.acceleration_status}`",
            ]
        )

    if ticket.breakeven_clock is not None:
        lines.extend(["", f"{h2} Breakeven clock", ""])
        for result in ticket.breakeven_clock.results:
            intervals = [
                f"[{item.lower:.4f}, {'∞' if item.upper is None else f'{item.upper:.4f}'}]"
                for item in result.profit_intervals
            ]
            lines.append(
                f"- `{result.breakeven_type}` / `{result.volatility_scenario}` at "
                f"{result.horizon_days}d: roots `{result.break_even_roots}`, profitable "
                f"`{intervals}`, exit `{result.exit_path.value}`, applied exit cost "
                f"`{_number(result.applied_exit_cost, 4)}`, status `{result.status}` / "
                f"`{result.exit_cost_status}`."
            )
        lines.extend(["", f"{h2} Target timing", ""])
        for target in ticket.target_arrivals:
            latest = (
                target.latest_profitable_arrival_date.isoformat()
                if target.latest_profitable_arrival_date
                else "none"
            )
            lines.append(
                f"- Target {target.target_spot:.4f}, `{target.volatility_scenario}`: "
                f"`{target.status.value}`, latest `{latest}`."
            )

    lines.extend(["", f"{h2} Spot × time × volatility scenarios", ""])
    for matrix in ticket.scenario_matrices:
        lines.extend(
            [
                f"**{matrix.scenario_name}** — `{matrix.scenario_status.value}`",
                "",
                "| Spot | Requested | Effective | Position value | Gross PnL | Exit path | "
                "Exit cost | Net PnL | Return | Status |",
                "| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for cell in matrix.cells:
            lines.append(
                f"| {cell.spot:.4f} | {cell.requested_horizon_days}d | "
                f"{_number(cell.effective_horizon_days, 3)}d | "
                f"{cell.estimated_position_value:.4f} | {cell.gross_pnl:.4f} | "
                f"{cell.exit_path.value} | {_number(cell.exit_cost_applied, 4)} | "
                f"{_number(cell.net_pnl, 4)} | {_percentage(cell.net_return)} | "
                f"{cell.scenario_status} |"
            )
        lines.append("")

    statistics = ticket.distribution_pnl
    lines.extend([f"{h2} Statistics", ""])
    if statistics is None:
        lines.append("- N/A — legacy ticket has no DistributionPnLMetrics block.")
    elif statistics.availability_status.value == "UNAVAILABLE":
        lines.extend(
            [
                "- Expected PnL: `N/A`",
                "- Median PnL: `N/A`",
                f"- Reason: `{statistics.missing_reason}`",
                f"- Model: `{statistics.model or 'N/A'}`",
                f"- Calibration status: `{statistics.calibration_status.value}`",
            ]
        )
    else:
        lines.extend(
            [
                f"- Model-implied Expected PnL: {_amount(statistics.expected_pnl, currency)}",
                f"- Median PnL: {_amount(statistics.median_pnl, currency)}",
                f"- Expected return: {_percentage(statistics.expected_return)}",
                f"- Median return: {_percentage(statistics.median_return)}",
                f"- P(profit): {_percentage(statistics.probability_profit)}",
                f"- P(+25%): {_percentage(statistics.probability_gain_25)}",
                f"- P(+50%): {_percentage(statistics.probability_gain_50)}",
                f"- P(+90%): {_percentage(statistics.probability_gain_90)}",
                f"- P(x2): {_percentage(statistics.probability_x2)}",
                f"- P(x3): {_percentage(statistics.probability_x3)}",
                f"- P(loss >25%): {_percentage(statistics.probability_loss_25)}",
                f"- P(loss >50%): {_percentage(statistics.probability_loss_50)}",
                f"- P(loss >70%): {_percentage(statistics.probability_loss_70)}",
                f"- P(loss >90%): {_percentage(statistics.probability_loss_90)}",
                f"- VaR95 loss (positive-loss convention): {_amount(statistics.var_95, currency)}",
                f"- CVaR95 loss (positive-loss convention): "
                f"{_amount(statistics.cvar_95, currency)}",
                f"- ESS: {_number(statistics.effective_sample_size, 0)}",
                f"- Probability model: `{statistics.model}` / measure `{statistics.measure}`",
                f"- Calibration status: `{statistics.calibration_status.value}`",
            ]
        )
        lines.extend(f"- Assumption: {item}" for item in statistics.assumptions)

    lines.extend(["", f"{h2} Decision scores", ""])
    if ticket.five_scores is None:
        lines.append("- N/A — no canonical five-score snapshot was supplied to the ticket builder.")
    else:
        scores = ticket.five_scores
        lines.append(
            f"- Scope: `{scores.scope.value}`; source: `{scores.source}`; source candidate: "
            f"`{scores.candidate_id or 'n/a'}`."
        )
        for score in (
            scores.opportunity,
            scores.risk,
            scores.evidence,
            scores.model_agreement,
            scores.execution_quality,
        ):
            lines.append(
                f"- {score.name.replace('_', ' ').title()}: "
                f"`{_number(score.score_value, 4)} / 100`; coverage "
                f"`{_percentage(score.score_coverage)}`; confidence `{score.confidence}`; "
                f"version `{score.formula_version}`; status `{score.status}`; missing "
                f"`{score.missing_components}`."
            )

    lines.extend(["", f"{h2} Attribution", ""])
    for attribution in ticket.pnl_attributions:
        full = attribution.full_repricing
        lines.append(
            f"- `{attribution.scenario_name}` full repricing PnL {full.full_repriced_pnl:.4f}; "
            f"spot/time/vol/rates/FX/costs/other/residual = "
            f"{full.spot:.4f}/{full.time:.4f}/{full.volatility:.4f}/{full.rates:.4f}/"
            f"{full.fx:.4f}/{full.execution_costs:.4f}/{full.other:.4f}/{full.residual:.8f}; "
            f"Taylor residual {attribution.taylor.residual:.4f}."
        )

    event_cells = [
        cell
        for matrix in ticket.scenario_matrices
        for cell in matrix.cells
        if cell.event_status.value != "NOT_APPLICABLE"
    ]
    lines.extend(["", f"{h2} Event", ""])
    if not event_cells:
        lines.append("- No event-date scenario is present in this ticket.")
    else:
        seen: set[tuple[str, str, int | None, float | None]] = set()
        for cell in event_cells:
            key = (
                cell.volatility_scenario,
                cell.event_status.value,
                cell.event_to_expiry_days,
                cell.applied_vol_shift,
            )
            if key in seen:
                continue
            seen.add(key)
            lines.append(
                f"- `{cell.volatility_scenario}`: event date "
                f"`{cell.event_date.isoformat() if cell.event_date else 'none'}`, status "
                f"`{cell.event_status.value}`, event-to-expiry "
                f"`{cell.event_to_expiry_days}`, applied IV shift "
                f"`{_number(cell.applied_vol_shift, 4)} vol points`."
            )

    lines.extend(["", f"{h2} Liquidity / execution", ""])
    for item in ticket.liquidity:
        lines.append(
            f"- `{item.contract_symbol}` bid/ask/mid "
            f"`{_number(item.bid, 4)}/{_number(item.ask, 4)}/{_number(item.mid, 4)}`; "
            f"sizes `{item.bid_size}/{item.ask_size}`; volume/OI "
            f"`{item.volume}/{item.open_interest}`; quote age "
            f"`{item.quote_age_seconds:.2f}s`; model `{item.liquidity_model_version}` "
            f"(`{item.calibration_status}`)."
        )

    lines.extend(["", f"{h2} Exercise / contract risk", ""])
    lines.extend(f"- {risk}" for risk in ticket.assignment_and_exercise_risks)
    lines.extend(["", f"{h2} Classification and safety", ""])
    lines.extend(f"- Blocker: `{item}`" for item in ticket.blockers)
    lines.extend(f"- Warning: {item}" for item in ticket.warnings)
    lines.extend(
        [
            f"- FX mode/status/contribution: `{ticket.fx_attribution.mode.value}` / "
            f"`{ticket.fx_attribution.status}` / "
            f"`{_number(ticket.fx_attribution.fx_contribution_base)}`",
            f"- Intensity: `{ticket.intensity.category.value if ticket.intensity else 'UNKNOWN'}`",
            f"- Data status: `{ticket.data_status}`",
            f"- Probability status: `{ticket.probability_status.value}`",
            "- Full repricing is the primary financial value; Taylor/Greek output is explanatory.",
            f"- Safety: read_only=`{str(ticket.read_only).lower()}`, "
            f"transmit=`{str(ticket.transmit).lower()}`, "
            f"what_if=`{str(ticket.what_if).lower()}`, "
            f"order_capability=`{ticket.order_capability}`.",
            "",
        ]
    )
    return "\n".join(lines)
