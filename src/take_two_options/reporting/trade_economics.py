"""Human-readable renderer for the versioned M0 trade-economics ticket."""

from __future__ import annotations

from take_two_options.trade_economics_models import GreekMeasure, TradeEconomicsTicket


def _amount(value: float | None, currency: str) -> str:
    return "UNKNOWN" if value is None else f"{value:,.2f} {currency}"


def _number(value: float | None, digits: int = 6) -> str:
    return "UNKNOWN" if value is None else f"{value:.{digits}f}"


def _greek(measure: GreekMeasure | None) -> str:
    if measure is None:
        return "disabled"
    return f"{measure.value:.6f} {measure.unit} ({measure.confidence.value})"


def render_trade_economics_markdown(
    ticket: TradeEconomicsTicket,
    *,
    heading_level: int = 1,
) -> str:
    """Render every financially material M0 ticket section from the typed object."""
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
        f"- Intraday precision: `{ticket.intraday_precision_status.value}`",
    ]
    if ticket.intraday_precision_warning:
        lines.append(f"- Intraday warning: {ticket.intraday_precision_warning}")

    lines.extend(
        [
            "",
            f"{h2} Legs",
            "",
            "| Side | Qty | Type | Strike | Expiration | Bid | Ask | Mid | IV | "
            "Multiplier | Premium paid | Premium received |",
            "| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for leg in ticket.legs:
        lines.append(
            f"| {leg.side} | {leg.quantity} | {leg.option_type or leg.instrument_type} | "
            f"{_number(leg.strike, 2)} | "
            f"{leg.expiration.isoformat() if leg.expiration else 'n/a'} | "
            f"{_number(leg.bid, 4)} | {_number(leg.ask, 4)} | {_number(leg.mid, 4)} | "
            f"{_number(leg.implied_volatility, 6)} | {leg.multiplier:g} | "
            f"{_amount(leg.premium_paid, currency)} | "
            f"{_amount(leg.premium_received, currency)} |"
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
                    "- Charm / delta drift: "
                    f"`{_greek(greeks.charm_delta_drift_1_calendar_day)}`",
                    "- Veta / vega drift: "
                    f"`{_greek(greeks.veta_vega_drift_1_calendar_day)}`",
                    f"- Speed: `{_greek(greeks.speed)}`",
                    "- Color / gamma drift: "
                    f"`{_greek(greeks.color_gamma_drift_1_calendar_day)}`",
                ]
            )

    entry = ticket.entry_cost
    exit_cost = ticket.exit_cost_estimate
    round_trip = ticket.round_trip_cost
    lines.extend(
        [
            "",
            f"{h2} Cost and capital",
            "",
            f"- Premium paid / received: {_amount(entry.premium_paid, currency)} / "
            f"{_amount(entry.premium_received, currency)}",
            f"- Net premium: {_amount(entry.net_premium, currency)}",
            f"- Mid theoretical value: {_amount(entry.mid_theoretical_value, currency)}",
            f"- Entry bid/ask / slippage / commission: "
            f"{_amount(entry.bid_ask_cost, currency)} / "
            f"{_amount(entry.expected_slippage, currency)} / "
            f"{_amount(entry.commission, currency)}",
            f"- Total entry cost: {_amount(entry.total_entry_cost, currency)}",
            f"- Exit bid/ask / slippage / commission: "
            f"{_amount(exit_cost.estimated_exit_bid_ask_cost, currency)} / "
            f"{_amount(exit_cost.estimated_exit_slippage, currency)} / "
            f"{_amount(exit_cost.closing_commissions, currency)}",
            f"- Total exit cost: {_amount(exit_cost.total_exit_cost, currency)} "
            f"(`{exit_cost.status.value}`)",
            f"- Total round-trip cost: {_amount(round_trip.total_round_trip_cost, currency)}",
            f"- Margin / buying power: {_amount(ticket.margin.margin_requirement, currency)} / "
            f"{_amount(ticket.margin.buying_power_usage, currency)} "
            f"(`{ticket.margin.status.value}`)",
            f"- Capital at risk: {_amount(ticket.capital_at_risk, currency)}",
            f"- Maximum loss / profit: {_amount(ticket.maximum_loss, currency)} / "
            f"{_amount(ticket.maximum_profit, currency)}",
            f"- Expiration breakevens: `{ticket.expiration_breakevens}`",
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
                f"{h2} Flat-spot carry",
                "",
                f"- Current local theta: {_amount(decay.current_net_theta, currency)} per day",
                "- Carry 1/7/30/60/90d: "
                f"`{_number(decay.flat_spot_1d)}` / `{_number(decay.flat_spot_7d)}` / "
                f"`{_number(decay.flat_spot_30d)}` / `{_number(decay.flat_spot_60d)}` / "
                f"`{_number(decay.flat_spot_90d)}`",
                f"- Decay acceleration status: `{decay.acceleration_status}`",
                "",
                "| Horizon | Valuation time | Full-repriced value | Flat-spot carry | Class |",
                "| ---: | --- | ---: | ---: | --- |",
            ]
        )
        for point in decay.time_decay_curve:
            lines.append(
                f"| {point.horizon_days}d | {point.valuation_time.isoformat()} | "
                f"{point.estimated_position_value:.4f} | {point.flat_spot_carry:.4f} | "
                f"{point.carry_classification} |"
            )

    lines.extend(["", f"{h2} Spot × time × volatility scenarios", ""])
    for matrix in ticket.scenario_matrices:
        lines.extend(
            [
                f"**{matrix.scenario_name}** — `{matrix.scenario_status.value}`",
                "",
                "| Spot | Horizon | Position value | Gross PnL | Round-trip cost | Net PnL |",
                "| ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for cell in matrix.cells:
            lines.append(
                f"| {cell.spot:.4f} | {cell.horizon_days}d | "
                f"{cell.estimated_position_value:.4f} | {cell.gross_pnl:.4f} | "
                f"{cell.round_trip_cost:.4f} | {cell.net_pnl:.4f} |"
            )
        lines.append("")

    lines.extend([f"{h2} Rate-curve stresses", ""])
    for rate_result in ticket.rate_stress_results:
        shifts = ", ".join(
            f"{symbol}={shift:+.2f}bp"
            for symbol, shift in rate_result.leg_rate_shifts_basis_points.items()
        )
        lines.append(
            f"- `{rate_result.scenario_name}` / `{rate_result.scenario_type.value}`: shifts "
            f"`{shifts or 'n/a'}`, value {rate_result.estimated_position_value:.4f}, "
            f"gross PnL {rate_result.gross_pnl:.4f}, net PnL {rate_result.net_pnl:.4f}, "
            f"status `{rate_result.status}`."
        )

    if ticket.breakeven_clock is not None:
        lines.extend([f"{h2} Breakeven clock and target timing", ""])
        for result in ticket.breakeven_clock.results:
            intervals = [
                f"[{item.lower:.4f}, {'∞' if item.upper is None else f'{item.upper:.4f}'}]"
                for item in result.profit_intervals
            ]
            lines.append(
                f"- `{result.volatility_scenario}` at {result.horizon_days}d: roots "
                f"`{result.break_even_roots}`, profitable `{intervals}`, status `{result.status}`"
            )
        for target in ticket.target_arrivals:
            latest = (
                target.latest_profitable_arrival_date.isoformat()
                if target.latest_profitable_arrival_date
                else "none"
            )
            lines.append(
                f"- Target {target.target_spot:.4f}, `{target.volatility_scenario}`: "
                f"`{target.status.value}`, latest "
                f"`{latest}`"
            )

    lines.extend(["", f"{h2} Attribution, FX, probability and risks", ""])
    for attribution in ticket.pnl_attributions:
        full = attribution.full_repricing
        lines.append(
            f"- `{attribution.scenario_name}` full repricing PnL {full.full_repriced_pnl:.4f}; "
            f"spot/time/vol/rates/FX/costs/other/residual = "
            f"{full.spot:.4f}/{full.time:.4f}/{full.volatility:.4f}/{full.rates:.4f}/"
            f"{full.fx:.4f}/{full.execution_costs:.4f}/{full.other:.4f}/{full.residual:.8f}."
        )
    if not ticket.touch_probabilities:
        lines.append("- P(touch): `null` — no configured/promoted P-path model.")
    for probability in ticket.touch_probabilities:
        lines.append(
            f"- P(touch {probability.target:g}): `{_number(probability.probability_touch)}`; "
            f"P(terminal above): `{_number(probability.probability_terminal_above)}`; "
            f"status `{probability.calibration_status.value}`; reason `{probability.reason}`."
        )
    lines.extend(
        [
            f"- FX mode/status/contribution: `{ticket.fx_attribution.mode.value}` / "
            f"`{ticket.fx_attribution.status}` / "
            f"`{_number(ticket.fx_attribution.fx_contribution_base)}`",
            f"- Intensity: `{ticket.intensity.category.value if ticket.intensity else 'UNKNOWN'}`",
        ]
    )
    lines.extend(f"- {risk}" for risk in ticket.assignment_and_exercise_risks)
    lines.extend(f"- Blocker: `{item}`" for item in ticket.blockers)
    lines.extend(f"- Warning: {item}" for item in ticket.warnings)
    lines.extend(
        [
            "",
            f"- Data status: `{ticket.data_status}`",
            f"- Probability status: `{ticket.probability_status.value}`",
            "- Full repricing is the primary financial value; Taylor/Greek output is explanatory.",
            f"- Safety: transmit=`{str(ticket.transmit).lower()}`, "
            f"what_if=`{str(ticket.what_if).lower()}`, "
            f"order_capability=`{ticket.order_capability}`.",
            "",
        ]
    )
    return "\n".join(lines)
