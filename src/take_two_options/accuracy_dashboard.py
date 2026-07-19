"""Canonical Data Analytics dashboard artifact for option opportunity reports."""

from __future__ import annotations

from datetime import date
from typing import Any

from take_two_options.accuracy import AccuracyCurrentCandidate, MarketDataAccuracyReport
from take_two_options.domain import StrategyKind
from take_two_options.marketdata_panel import (
    MarketDataPanelCaseResult,
    MarketDataPanelSelectedLeg,
)
from take_two_options.strategy_architectures import (
    architecture_catalog_rows,
    architecture_for,
)


def build_accuracy_dashboard_artifact(
    report: MarketDataAccuracyReport,
    *,
    report_path: str = "reports/ttwo_v9_budget_report.json",
) -> dict[str, Any]:
    variants = _variant_rows(report)
    trades = _trade_rows(report)
    execution_legs = _execution_leg_rows(report)
    current = _current_candidate_rows(report)
    budget_current = [row for row in current if row["budget_plan_id"] is not None]
    equity = _equity_rows(report)
    winners = [row for row in trades if row["outcome"] == "winner"]
    architectures = _architecture_rows()
    option_variants = [row for row in variants if row["strategy"] != StrategyKind.NO_TRADE.value]
    eligible_variants = [row for row in option_variants if row["validated"]]
    sufficiently_observed = [
        row for row in option_variants if int(row["test_effective_n"] or 0) >= 8
    ]
    research_lead = max(
        sufficiently_observed,
        key=lambda row: float(row["test_median_return"] or -10),
        default=None,
    )
    summary = [
        {
            "current_eligible_trades": sum(row["status"] == "eligible" for row in current),
            "current_watchlist_trades": sum(row["status"] == "watchlist" for row in current),
            "validated_variants": len(eligible_variants),
            "tested_variants": len(option_variants),
            "lead_observed_accuracy": (research_lead["test_win_rate"] if research_lead else None),
            "lead_accuracy_ci_low": (
                research_lead["test_win_rate_ci_low"] if research_lead else None
            ),
            "lead_accuracy_ci_high": (
                research_lead["test_win_rate_ci_high"] if research_lead else None
            ),
            "winning_test_trades": sum(
                row["outcome"] == "winner" and row["split"] == "test" for row in trades
            ),
            "latest_market_date": max(
                (str(row["quote_date"]) for row in current), default="unknown"
            ),
        }
    ]
    source_id = "accuracy_report"
    source = {
        "id": source_id,
        "label": f"TTWO {report.research_version} opportunity report",
        "path": "docs/sql/ttwo_v9_budget_dashboard_source.sql",
    }
    manifest = {
        "version": 1,
        "surface": "dashboard",
        "title": f"TTWO Options Opportunities {report.research_version}",
        "description": (
            "Read-only current opportunities, historical winners, architecture coverage, "
            "forecast uncertainty, liquidity, and bounded-risk diagnostics."
        ),
        "generatedAt": report.created_at.isoformat(),
        "sources": [source],
        "filters": [
            {
                "id": "strategy_filter",
                "label": "Strategy",
                "dataset": "trades",
                "field": "strategy",
                "includeAll": True,
                "targets": [
                    {"dataset": "variants", "field": "strategy"},
                    {"dataset": "option_variants", "field": "strategy"},
                    {"dataset": "current_candidates", "field": "strategy"},
                    {"dataset": "budget_candidates", "field": "strategy"},
                    {"dataset": "equity_curve", "field": "strategy"},
                    {"dataset": "execution_legs", "field": "strategy"},
                    {"dataset": "historical_winners", "field": "strategy"},
                ],
            },
            {
                "id": "split_filter",
                "label": "Sample",
                "dataset": "trades",
                "field": "split",
                "includeAll": True,
                "targets": [
                    {"dataset": "equity_curve", "field": "split"},
                    {"dataset": "execution_legs", "field": "split"},
                    {"dataset": "historical_winners", "field": "split"},
                ],
            },
            {
                "id": "outcome_filter",
                "label": "Outcome",
                "dataset": "trades",
                "field": "outcome",
                "includeAll": True,
                "targets": [
                    {"dataset": "execution_legs", "field": "outcome"},
                ],
            },
            {
                "id": "regime_filter",
                "label": "Regime",
                "dataset": "trades",
                "field": "regime",
                "includeAll": True,
                "targets": [
                    {"dataset": "execution_legs", "field": "regime"},
                    {"dataset": "historical_winners", "field": "regime"},
                ],
            },
            {
                "id": "candidate_status_filter",
                "label": "Opportunity status",
                "dataset": "current_candidates",
                "field": "status",
                "includeAll": True,
            },
        ],
        "cards": [
            _card(
                "eligible_current",
                "summary",
                "Current eligible trades",
                "current_eligible_trades",
                "number",
                "Candidates clearing historical, holdout, liquidity, and current-chain gates.",
            ),
            _card(
                "watchlist_current",
                "summary",
                "Current watchlist",
                "current_watchlist_trades",
                "number",
                "Numerically interesting rows that still require fresh validation.",
            ),
            _card(
                "validated_variants",
                "summary",
                "Validated variants",
                "validated_variants",
                "number",
                "Option variants passing test gates and untouched holdout validation.",
            ),
            _card(
                "lead_accuracy",
                "summary",
                "Research lead accuracy",
                "lead_observed_accuracy",
                "percent",
                (
                    "Highest observed test net win rate; use its confidence interval, "
                    "not the point estimate alone."
                ),
                supporting=[
                    {"label": "CI low", "field": "lead_accuracy_ci_low", "format": "percent"},
                    {"label": "CI high", "field": "lead_accuracy_ci_high", "format": "percent"},
                ],
            ),
            _card(
                "winning_trades",
                "summary",
                "Winning test selections",
                "winning_test_trades",
                "number",
                (
                    "Positive net P&L selections in the validation sample after configured "
                    "costs; the same date can appear in more than one experiment."
                ),
            ),
        ],
        "charts": [
            {
                "id": "variant_return_ranking",
                "title": "Median net return by variant",
                "subtitle": "Validation sample; no-trade remains the zero-return benchmark.",
                "intent": "comparison",
                "type": "horizontalBar",
                "dataset": "variants",
                "sourceId": source_id,
                "encodings": {
                    "x": {
                        "field": "variant_label",
                        "type": "nominal",
                        "label": "Variant",
                    },
                    "y": {
                        "field": "test_median_return",
                        "type": "quantitative",
                        "format": "percent",
                        "label": "Median net return",
                    },
                    "color": {"field": "validation_status", "type": "nominal"},
                    "tooltip": [
                        {"field": "test_win_rate", "format": "percent", "label": "Accuracy"},
                        {"field": "test_cvar_95", "format": "percent", "label": "CVaR 95%"},
                        {"field": "test_effective_n", "format": "number", "label": "Effective n"},
                    ],
                },
                "referenceLines": [{"axis": "y", "value": 0, "label": "No trade"}],
                "maxRows": 40,
                "layout": "full",
            },
            {
                "id": "risk_return_map",
                "title": "Return versus volatility",
                "subtitle": (
                    "Each point is one strategy, horizon, expiry target, and delta profile."
                ),
                "intent": "relationship",
                "type": "scatter",
                "dataset": "option_variants",
                "sourceId": source_id,
                "encodings": {
                    "x": {
                        "field": "test_return_volatility",
                        "type": "quantitative",
                        "format": "percent",
                        "label": "Return volatility",
                    },
                    "y": {
                        "field": "test_median_return",
                        "type": "quantitative",
                        "format": "percent",
                        "label": "Median net return",
                    },
                    "size": {"field": "test_effective_n", "type": "quantitative"},
                    "tooltip": [
                        {"field": "variant_label", "label": "Variant"},
                        {"field": "test_win_rate", "format": "percent", "label": "Accuracy"},
                        {"field": "test_cvar_95", "format": "percent", "label": "CVaR 95%"},
                    ],
                },
                "layout": "full",
            },
            {
                "id": "trade_return_distribution",
                "title": "Distribution of selected trade returns",
                "subtitle": (
                    "Use the outcome filter to compare winners, losers, or the full sample."
                ),
                "intent": "distribution",
                "type": "histogram",
                "dataset": "trades",
                "sourceId": source_id,
                "encodings": {
                    "x": {
                        "field": "net_return",
                        "type": "quantitative",
                        "format": "percent",
                        "label": "Net premium return",
                    },
                    "y": {
                        "field": "net_return",
                        "type": "quantitative",
                        "aggregate": "count",
                        "format": "number",
                        "label": "Trades",
                    },
                },
                "referenceLines": [{"axis": "x", "value": 0, "label": "Break-even"}],
                "layout": "full",
            },
            {
                "id": "equity_curve",
                "title": "Research lead cumulative normalized return",
                "subtitle": (
                    "Additive one-unit-risk curve for the best-observed validation variant; "
                    "all selections remain available in the audit table."
                ),
                "intent": "trend",
                "type": "line",
                "dataset": "equity_curve",
                "sourceId": source_id,
                "encodings": {
                    "x": {"field": "exit_date", "type": "temporal", "label": "Exit date"},
                    "y": {
                        "field": "cumulative_return",
                        "type": "quantitative",
                        "format": "percent",
                        "label": "Cumulative return",
                    },
                    "color": {"field": "variant_label", "type": "nominal"},
                },
                "layout": "full",
                "maxRows": 1_000,
            },
        ],
        "tables": [
            {
                "id": "budget_candidates_table",
                "title": "Plans sous budget de 1 000 EUR",
                "subtitle": (
                    "Comparaison entre un seul trade longue echeance et trois poches. "
                    "Le risque inclut les couts modelises; la limite IBKR doit venir du live."
                ),
                "dataset": "budget_candidates",
                "sourceId": source_id,
                "defaultSort": {"field": "plan_et_budget", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {
                        "field": "plan_et_budget",
                        "label": "Plan et consommation",
                        "type": "text",
                    },
                    {
                        "field": "ticket_ibkr",
                        "label": "Structure IBKR",
                        "type": "text",
                    },
                    {
                        "field": "scenario_gagnant",
                        "label": "Scenario necessaire",
                        "type": "text",
                    },
                    {
                        "field": "statut_et_blocage",
                        "label": "Validation",
                        "type": "text",
                    },
                    {
                        "field": "preuves_et_risque",
                        "label": "Tests et risque",
                        "type": "text",
                    },
                ],
                "layout": "full",
            },
            {
                "id": "current_candidates_table",
                "title": "Ordres potentiels actuels",
                "subtitle": (
                    "Lecture IBKR simplifiee sur la derniere chaine EOD. Un ordre bloque est "
                    "un scenario de recherche, pas un ordre a executer."
                ),
                "dataset": "current_candidates",
                "sourceId": source_id,
                "defaultSort": {"field": "statut_et_blocage", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {
                        "field": "statut_et_blocage",
                        "label": "Statut et raison",
                        "type": "text",
                    },
                    {
                        "field": "ticket_ibkr",
                        "label": "Ordre a saisir dans IBKR",
                        "type": "text",
                    },
                    {
                        "field": "scenario_gagnant",
                        "label": "Quand la strategie gagnerait",
                        "type": "text",
                    },
                    {
                        "field": "preuves_et_risque",
                        "label": "Tests et risque",
                        "type": "text",
                    },
                ],
                "layout": "full",
            },
            {
                "id": "historical_winners_table",
                "title": "Historical winning trades",
                "subtitle": (
                    "Positive net P&L after configured costs. Samples and duplicate economic "
                    "exposures remain explicit."
                ),
                "dataset": "historical_winners",
                "sourceId": source_id,
                "defaultSort": {"field": "net_return", "direction": "desc"},
                "density": "dense",
                "columns": [
                    {"field": "architecture", "label": "Architecture", "type": "text"},
                    {"field": "split", "label": "Sample", "type": "text"},
                    {"field": "regime", "label": "Regime", "type": "text"},
                    {"field": "trade_plan", "label": "Trade", "type": "text"},
                    {"field": "exit_summary", "label": "Exit", "type": "text"},
                    {"field": "risk_summary", "label": "Risk context", "type": "text"},
                    {"field": "net_return", "label": "Net return", "format": "percent"},
                ],
                "layout": "full",
            },
            {
                "id": "architecture_catalog_table",
                "title": "Architecture library",
                "subtitle": (
                    "The catalog is intentionally broader than the active backtest set. "
                    "Risk-disabled structures cannot be activated from this tool."
                ),
                "dataset": "architectures",
                "sourceId": source_id,
                "defaultSort": {"field": "readiness", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {"field": "name", "label": "Architecture", "type": "text"},
                    {"field": "readiness", "label": "Status", "type": "text"},
                    {"field": "family", "label": "Family", "type": "text"},
                    {"field": "thesis", "label": "Thesis and payoff", "type": "text"},
                    {"field": "rules", "label": "Entry and exit template", "type": "text"},
                    {"field": "risk_limit", "label": "Risk and limitation", "type": "text"},
                ],
                "layout": "full",
            },
            {
                "id": "trade_audit_table",
                "title": "Selected trade audit",
                "subtitle": (
                    "Every completed selected trade with performance, volatility proxy, "
                    "liquidity, Greeks, costs, and stress."
                ),
                "dataset": "trades",
                "sourceId": source_id,
                "defaultSort": {"field": "actual_exit_date", "direction": "desc"},
                "density": "dense",
                "columns": [
                    {"field": "trade_label", "label": "Trade", "type": "text"},
                    {"field": "split", "label": "Sample", "type": "text"},
                    {"field": "regime", "label": "Regime", "type": "text"},
                    {"field": "entry_date", "label": "Entry", "type": "date"},
                    {"field": "actual_exit_date", "label": "Actual exit", "type": "date"},
                    {"field": "exit_reason", "label": "Exit rule hit", "type": "text"},
                    {"field": "expirations", "label": "Expiry", "type": "text"},
                    {"field": "legs", "label": "Legs", "type": "text"},
                    {"field": "net_pnl", "label": "Net P&L", "format": "currency"},
                    {"field": "net_return", "label": "Net return", "format": "percent"},
                    {"field": "risk_capital", "label": "Risk / unit", "format": "currency"},
                    {"field": "stress_slippage_2x", "label": "Stress 2x", "format": "percent"},
                    {"field": "signal_iv", "label": "Signal IV", "format": "percent"},
                    {"field": "net_delta", "label": "Net delta", "format": "number"},
                    {"field": "max_spread_ratio", "label": "Max spread", "format": "percent"},
                    {"field": "min_open_interest", "label": "Min OI", "format": "number"},
                    {"field": "costs", "label": "Costs", "format": "currency"},
                ],
                "layout": "full",
            },
            {
                "id": "execution_legs_table",
                "title": "Execution legs",
                "subtitle": (
                    "Executable-side EOD prices and leg-level gross P&L for the filtered trades."
                ),
                "dataset": "execution_legs",
                "sourceId": source_id,
                "defaultSort": {"field": "trade_label", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {"field": "trade_label", "label": "Trade", "type": "text"},
                    {"field": "symbol", "label": "Contract", "type": "text"},
                    {"field": "side", "label": "Side", "type": "text"},
                    {"field": "quantity", "label": "Qty", "format": "number"},
                    {"field": "entry_bid", "label": "Entry bid", "format": "currency"},
                    {"field": "entry_ask", "label": "Entry ask", "format": "currency"},
                    {"field": "exit_bid", "label": "Exit bid", "format": "currency"},
                    {"field": "exit_ask", "label": "Exit ask", "format": "currency"},
                    {"field": "gross_pnl", "label": "Gross P&L", "format": "currency"},
                ],
                "layout": "full",
            },
        ],
        "blocks": [
            {
                "id": "summary_metrics",
                "type": "metric-strip",
                "cardIds": [
                    "eligible_current",
                    "watchlist_current",
                    "validated_variants",
                    "lead_accuracy",
                    "winning_trades",
                ],
                "layout": "full",
            },
            {
                "id": "budget_candidates_block",
                "type": "table",
                "tableId": "budget_candidates_table",
                "layout": "full",
            },
            {
                "id": "current_candidates_block",
                "type": "table",
                "tableId": "current_candidates_table",
                "layout": "full",
            },
            {
                "id": "historical_winners_block",
                "type": "table",
                "tableId": "historical_winners_table",
                "layout": "full",
            },
            {
                "id": "architecture_catalog_block",
                "type": "table",
                "tableId": "architecture_catalog_table",
                "layout": "full",
            },
            {
                "id": "variant_return_ranking_block",
                "type": "chart",
                "chartId": "variant_return_ranking",
                "layout": "full",
            },
            {
                "id": "risk_return_map_block",
                "type": "chart",
                "chartId": "risk_return_map",
                "layout": "full",
            },
            {
                "id": "trade_return_distribution_block",
                "type": "chart",
                "chartId": "trade_return_distribution",
                "layout": "full",
            },
            {
                "id": "equity_curve_block",
                "type": "chart",
                "chartId": "equity_curve",
                "layout": "full",
            },
            {
                "id": "trade_audit_block",
                "type": "table",
                "tableId": "trade_audit_table",
                "layout": "full",
            },
            {
                "id": "execution_legs_block",
                "type": "table",
                "tableId": "execution_legs_table",
                "layout": "full",
            },
        ],
    }
    return {
        "surface": "dashboard",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "generatedAt": report.created_at.isoformat(),
            "status": "ready",
            "datasets": {
                "summary": summary,
                "variants": variants,
                "option_variants": option_variants,
                "trades": trades,
                "execution_legs": execution_legs,
                "current_candidates": current,
                "budget_candidates": budget_current,
                "historical_winners": winners,
                "architectures": architectures,
                "equity_curve": equity,
            },
        },
        "sources": [source],
    }


def _card(
    card_id: str,
    dataset: str,
    label: str,
    field: str,
    value_format: str,
    description: str,
    *,
    supporting: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": card_id,
        "dataset": dataset,
        "sourceId": "accuracy_report",
        "description": description,
        "metrics": [
            {"label": label, "field": field, "format": value_format},
            *(supporting or []),
        ],
    }


def _architecture_rows() -> list[dict[str, Any]]:
    rows = architecture_catalog_rows()
    for row in rows:
        row["thesis"] = f"{row['market_view']} | {row['volatility_view']} | {row['payoff']}"
        row["rules"] = f"{row['default_entry']} | {row['default_exit']}"
        row["risk_limit"] = f"{row['maximum_risk']} | {row['limitation']}"
    return rows


def _money(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"${float(value):,.0f}"


def _percent(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1%}"


def _number(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.2f}"


def _compact_entry_rule(value: str) -> str:
    if not value:
        return "no entry"
    return (
        value.replace("long delta ", "d")
        .replace("%; short delta ", "/")
        .replace("strike near spot ", "K")
        .replace("; target ", " | ")
        .replace(" DTE", "d")
        .replace("%", "")
    )


def _compact_exit_rule(value: str) -> str:
    if not value:
        return "no exit"
    return (
        value.replace("cash-out +", "TP")
        .replace("stop -", "SL")
        .replace("time exit ", "H")
        .replace(" sessions", "")
        .replace("; ", " | ")
        .replace("%", "")
    )


def _compact_blockers(reasons: list[str]) -> str:
    labels = {
        "insufficient train observations": "train sample",
        "insufficient test observations": "test sample",
        "coverage below configured minimum": "coverage",
        "test median return below configured minimum": "median",
        "test drawdown above configured maximum": "drawdown",
        "test worst loss above configured maximum": "worst loss",
        "deflated Sharpe probability below configured minimum": "Deflated Sharpe",
        "train/test stability gap above configured maximum": "stability",
        "holdout validation did not pass": "holdout",
        "baseline retained until an option variant clears every gate": "baseline",
    }
    compact = []
    for reason in reasons:
        label = labels.get(reason)
        if label is None and (
            "selection" in reason or "eligible" in reason or reason.startswith("no listed")
        ):
            label = "no current legs"
        compact.append(label or reason)
    unique = list(dict.fromkeys(compact))
    if len(unique) > 3:
        unique = [*unique[:3], f"+{len(unique) - 3} gates"]
    return " / ".join(unique) or "all gates passed"


def _compact_money(value: float | None) -> str:
    if value is None:
        return "n/a"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}k"
    return f"${value:.0f}"


def _compact_count(value: float | None) -> str:
    if value is None:
        return "n/a"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:.0f}"


_MONTHS_FR = (
    "",
    "janv.",
    "fevr.",
    "mars",
    "avr.",
    "mai",
    "juin",
    "juil.",
    "aout",
    "sept.",
    "oct.",
    "nov.",
    "dec.",
)


def _date_fr(value: date) -> str:
    return f"{value.day} {_MONTHS_FR[value.month]} {value.year}"


def _readable_legs(legs: list[MarketDataPanelSelectedLeg]) -> str:
    readable = []
    for index, leg in enumerate(legs, start=1):
        action = "ACHETER" if leg.position_side.value == "long" else "VENDRE"
        option = (
            "CALL (option d'achat)" if leg.option_type.value == "call" else "PUT (option de vente)"
        )
        readable.append(
            f"Jambe {index}: {action} {leg.quantity} {option} TTWO, "
            f"strike ${leg.strike:g}, echeance {_date_fr(leg.expiration)} "
            f"[{leg.symbol}]"
        )
    return " || ".join(readable)


def _readable_exit_rule(value: str) -> str:
    return (
        value.replace("cash-out +", "prendre le profit a +")
        .replace("stop -", "couper la perte a -")
        .replace("time exit ", "fermer apres ")
        .replace(" sessions", " seances")
        .replace("; ", " | ")
    )


def _ibkr_ticket(candidate: AccuracyCurrentCandidate) -> str:
    if candidate.strategy is StrategyKind.NO_TRADE:
        return "AUCUN ORDRE | conserver le capital"
    if not candidate.legs:
        return "AUCUN ORDRE | aucun contrat conforme disponible"
    package = "COMBO" if len(candidate.legs) > 1 else "OPTION"
    net_value = candidate.net_debit_credit
    if net_value is None:
        price = "prix limite a definir sur la cotation IBKR live"
        direction = "ordre limite"
    else:
        direction = "ACHAT au DEBIT" if net_value >= 0 else "VENTE au CREDIT"
        price = (
            f"reference combo EOD ${abs(net_value) / 100:,.2f} par action, "
            f"soit environ {_money(abs(net_value))} pour 1 lot; "
            "verifier la cotation IBKR live"
        )
    return (
        f"{package} | ordre LMT {direction} | {price} | "
        f"{_readable_legs(candidate.legs)} | Sortie: "
        f"{_readable_exit_rule(candidate.exit_rule)}"
    )


def _strategy_scenario(strategy: StrategyKind) -> str:
    scenarios = {
        StrategyKind.NO_TRADE: "Aucun scenario de marche: le capital reste disponible.",
        StrategyKind.LONG_CALL: (
            "TTWO monte assez vite et/ou la volatilite implicite augmente avant la sortie."
        ),
        StrategyKind.BULL_CALL_SPREAD: (
            "TTWO monte moderement; le call vendu reduit le cout mais plafonne le gain."
        ),
        StrategyKind.LONG_PUT: (
            "TTWO baisse assez vite et/ou la volatilite implicite augmente avant la sortie."
        ),
        StrategyKind.BEAR_PUT_SPREAD: (
            "TTWO baisse moderement; le put vendu finance une partie du cout et plafonne le gain."
        ),
        StrategyKind.LONG_STRADDLE: (
            "TTWO fait un mouvement tres important dans un sens ou l'autre, superieur au cout "
            "des deux primes."
        ),
        StrategyKind.LONG_STRANGLE: (
            "TTWO fait un mouvement encore plus large; les deux options OTM doivent compenser "
            "leur erosion temps."
        ),
        StrategyKind.CALL_BUTTERFLY: (
            "TTWO termine pres du strike central; un mouvement trop faible ou trop fort penalise."
        ),
        StrategyKind.PUT_BUTTERFLY: (
            "TTWO termine pres du strike central; le gain maximal existe dans une zone etroite."
        ),
        StrategyKind.IRON_CONDOR: (
            "TTWO reste entre les strikes vendus et la volatilite realisee reste contenue."
        ),
        StrategyKind.LONG_CALL_CALENDAR: (
            "TTWO reste proche du strike pendant que l'option courte perd plus vite sa valeur "
            "temps que l'option longue."
        ),
        StrategyKind.CALL_DIAGONAL: (
            "TTWO monte moderement, sans depasser trop vite le call court, avec une structure "
            "de volatilite favorable."
        ),
        StrategyKind.LEAPS_CALL: (
            "TTWO progresse fortement sur la duree et la hausse compense prime, theta et IV."
        ),
        StrategyKind.LEAPS_PUT: (
            "TTWO baisse fortement sur la duree et la baisse compense prime, theta et IV."
        ),
    }
    return scenarios.get(strategy, "Le scenario propre a cette architecture doit etre valide.")


def _candidate_scenario(candidate: AccuracyCurrentCandidate) -> str:
    if candidate.strategy is not StrategyKind.BULL_CALL_SPREAD or not candidate.legs:
        return _strategy_scenario(candidate.strategy)
    long_calls = [
        leg
        for leg in candidate.legs
        if leg.option_type.value == "call" and leg.position_side.value == "long"
    ]
    short_calls = [
        leg
        for leg in candidate.legs
        if leg.option_type.value == "call" and leg.position_side.value == "short"
    ]
    if not long_calls or not short_calls or candidate.estimated_max_loss is None:
        return _strategy_scenario(candidate.strategy)
    long_leg = min(long_calls, key=lambda leg: leg.strike)
    short_leg = max(short_calls, key=lambda leg: leg.strike)
    terminal_break_even = long_leg.strike + candidate.estimated_max_loss / 100
    maximum_gain = _money(candidate.estimated_max_gain)
    return (
        f"A l'echeance: zone positive estimee au-dessus de ${terminal_break_even:,.2f}; "
        f"gain maximal {maximum_gain} si TTWO atteint au moins ${short_leg.strike:g}. "
        "Avant l'echeance, theta, IV, liquidite et sortie anticipee changent ce payoff."
    )


def _readable_blockers(reasons: list[str]) -> str:
    translations = {
        "baseline retained until an option variant clears every gate": (
            "aucune option ne passe tous les controles"
        ),
        "insufficient train observations": "pas assez d'observations d'entrainement",
        "insufficient test observations": "pas assez d'observations de test",
        "coverage below configured minimum": "couverture historique insuffisante",
        "test median return below configured minimum": "mediane du test negative",
        "test drawdown above configured maximum": "drawdown du test trop eleve",
        "test worst loss above configured maximum": "pire perte du test trop elevee",
        "deflated Sharpe probability below configured minimum": (
            "robustesse statistique insuffisante"
        ),
        "train/test stability gap above configured maximum": "resultats train/test instables",
        "holdout validation did not pass": "holdout non valide",
        "selected structure exceeds configured EUR risk budget": ("historique hors budget EUR"),
        "current structure exceeds configured EUR risk budget": (
            "structure actuelle hors budget EUR"
        ),
    }
    readable = []
    for reason in reasons:
        if reason.startswith("no listed"):
            readable.append("aucun strike cote assez proche de la cible")
        elif "selection" in reason or "eligible" in reason:
            readable.append("aucun contrat actuel conforme")
        else:
            readable.append(translations.get(reason, reason))
    return " | ".join(dict.fromkeys(readable)) or "tous les controles passent"


def _evidence_and_risk(candidate: AccuracyCurrentCandidate) -> str:
    test = candidate.historical_test_metrics
    holdout = candidate.historical_holdout_metrics
    if test is None:
        test_text = "Test: donnees insuffisantes"
    else:
        test_text = (
            f"Test: {test.observations} cas | gagnants {test.win_rate:.1%} "
            f"[{test.win_rate_ci_low:.1%}-{test.win_rate_ci_high:.1%}] | "
            f"mediane {test.median_return:+.1%} | drawdown {test.maximum_drawdown:.1%}"
        )
    holdout_text = (
        f"Holdout: {holdout.observations} cas | mediane {holdout.median_return:+.1%}"
        if holdout is not None
        else "Holdout: insuffisant"
    )
    iv_text = _percent(candidate.signal_implied_volatility)
    risk_eur = (
        candidate.estimated_max_loss / candidate.eur_usd_rate
        if candidate.estimated_max_loss is not None and candidate.eur_usd_rate is not None
        else None
    )
    risk_text = _money(candidate.estimated_max_loss)
    if risk_eur is not None:
        risk_text += f" (environ EUR {risk_eur:.0f})"
    return f"{test_text} | {holdout_text} | risque maximal estime {risk_text} | IV {iv_text}"


def _variant_rows(report: MarketDataAccuracyReport) -> list[dict[str, Any]]:
    rows = []
    for variant in report.variants:
        test = variant.test_metrics
        if test is None:
            continue
        numerically_validated = variant.eligible_for_ranking and variant.holdout_passed is True
        validated = numerically_validated and report.holdout_policy == "fresh"
        architecture = architecture_for(variant.strategy)
        rows.append(
            {
                "variant_id": variant.variant_id,
                "variant_label": _variant_label(variant.variant_id),
                "experiment_id": variant.experiment_id,
                "strategy": variant.strategy.value,
                "architecture": architecture.name if architecture else variant.strategy.value,
                "target_dte": variant.target_dte,
                "holding_sessions": variant.holding_sessions,
                "validated": validated,
                "validation_status": (
                    "validated"
                    if validated
                    else "watchlist"
                    if numerically_validated
                    else "blocked"
                ),
                "test_effective_n": test.effective_observations,
                "test_mean_return": test.mean_return,
                "test_median_return": test.median_return,
                "test_win_rate": test.win_rate,
                "test_win_rate_ci_low": test.win_rate_ci_low,
                "test_win_rate_ci_high": test.win_rate_ci_high,
                "test_return_volatility": test.return_volatility,
                "test_max_drawdown": test.maximum_drawdown,
                "test_var_95": test.value_at_risk_95,
                "test_cvar_95": test.conditional_value_at_risk_95,
                "test_profit_factor": test.profit_factor,
                "test_dsr_probability": test.deflated_sharpe_probability,
                "holdout_median_return": (
                    variant.holdout_metrics.median_return
                    if variant.holdout_metrics is not None
                    else None
                ),
                "reasons": "; ".join(variant.eligibility_reasons),
            }
        )
    return rows


def _trade_rows(report: MarketDataAccuracyReport) -> list[dict[str, Any]]:
    rows = []
    for panel in report.panels:
        for strategy in panel.strategies:
            if strategy.strategy is StrategyKind.NO_TRADE:
                continue
            variant_id = f"{panel.experiment_id}:{strategy.strategy.value}"
            for case in strategy.cases:
                if case.net_return is None:
                    continue
                rows.append(_trade_row(variant_id, strategy.strategy, case))
    return rows


def _trade_row(
    variant_id: str, strategy: StrategyKind, case: MarketDataPanelCaseResult
) -> dict[str, Any]:
    legs = " / ".join(
        f"{leg.position_side.value[0].upper()}{leg.quantity} "
        f"{leg.option_type.value[0].upper()}{leg.strike:g}"
        for leg in case.legs
    )
    expirations = "/".join(
        expiration.isoformat() for expiration in sorted({leg.expiration for leg in case.legs})
    )
    iv_values = [
        leg.signal_implied_volatility
        for leg in case.legs
        if leg.signal_implied_volatility is not None
    ]
    open_interest = [
        leg.signal_open_interest for leg in case.legs if leg.signal_open_interest is not None
    ]
    architecture = architecture_for(strategy)
    actual_exit = (
        case.actual_exit_quote_date.isoformat()
        if case.actual_exit_quote_date is not None
        else case.exit_quote_date.isoformat()
    )
    return {
        "trade_id": f"{variant_id}:{case.observation_id}",
        "trade_label": (f"{_variant_label(variant_id)} | {case.observation_id.rsplit('-', 1)[-1]}"),
        "variant_id": variant_id,
        "experiment_id": variant_id.split(":", 1)[0],
        "strategy": strategy.value,
        "architecture": architecture.name if architecture else strategy.value,
        "split": case.split,
        "outcome": "winner" if case.winner else "loser",
        "regime": case.regime,
        "signal_date": case.signal_quote_date.isoformat(),
        "entry_date": case.entry_quote_date.isoformat(),
        "exit_date": case.exit_quote_date.isoformat(),
        "actual_exit_date": actual_exit,
        "exit_reason": case.exit_reason,
        "expiration": case.legs[0].expiration.isoformat() if case.legs else None,
        "expirations": expirations,
        "legs": legs,
        "trade_plan": (f"{_readable_legs(case.legs)} | Entree: {_date_fr(case.entry_quote_date)}"),
        "exit_summary": (
            f"Sortie: {_date_fr(case.actual_exit_quote_date or case.exit_quote_date)} | "
            f"motif: {case.exit_reason or 'sortie au temps'}"
        ),
        "signal_spot": _first_spot(case, signal=True),
        "entry_spot": _first_spot(case, entry=True),
        "exit_spot": _first_spot(case, entry=False),
        "entry_outlay": case.entry_outlay,
        "risk_capital": case.risk_capital,
        "estimated_max_gain": case.estimated_max_gain,
        "estimated_max_loss": case.estimated_max_loss,
        "risk_summary": (
            f"risk {_money(case.risk_capital)} | P&L {_money(case.net_pnl)} | "
            f"IV/RV {_number(case.signal_iv_to_rv)} | "
            f"stress {_percent(case.slippage_stress_return_2x)}"
        ),
        "gross_pnl": case.gross_pnl,
        "costs": case.costs,
        "net_pnl": case.net_pnl,
        "net_return": case.net_return,
        "return_per_calendar_day": case.return_per_calendar_day,
        "stress_slippage_2x": case.slippage_stress_return_2x,
        "stress_spread_1_5x": case.spread_stress_return_1_5x,
        "signal_iv": sum(iv_values) / len(iv_values) if iv_values else None,
        "signal_realized_volatility_20": case.signal_realized_volatility_20,
        "signal_momentum_20": case.signal_momentum_20,
        "signal_iv_to_rv": case.signal_iv_to_rv,
        "net_delta": sum(
            leg.position_side.sign * leg.quantity * leg.signal_delta for leg in case.legs
        ),
        "net_gamma": _signed_greek(case, "signal_gamma"),
        "net_theta": _signed_greek(case, "signal_theta"),
        "net_vega": _signed_greek(case, "signal_vega"),
        "max_spread_ratio": max((leg.bid_ask_ratio for leg in case.legs), default=None),
        "min_open_interest": min(open_interest) if open_interest else None,
    }


def _execution_leg_rows(report: MarketDataAccuracyReport) -> list[dict[str, Any]]:
    rows = []
    for panel in report.panels:
        for strategy in panel.strategies:
            if strategy.strategy is StrategyKind.NO_TRADE:
                continue
            variant_id = f"{panel.experiment_id}:{strategy.strategy.value}"
            for case in strategy.cases:
                trade_id = f"{variant_id}:{case.observation_id}"
                for leg in case.execution_legs:
                    rows.append(
                        {
                            "trade_id": trade_id,
                            "trade_label": (
                                f"{_variant_label(variant_id)} | "
                                f"{case.observation_id.rsplit('-', 1)[-1]}"
                            ),
                            "strategy": strategy.strategy.value,
                            "split": case.split,
                            "outcome": "winner" if case.winner else "loser",
                            "regime": case.regime,
                            "symbol": leg.symbol,
                            "side": leg.position_side.value,
                            "quantity": leg.quantity,
                            "entry_bid": leg.entry_bid,
                            "entry_ask": leg.entry_ask,
                            "exit_bid": leg.exit_bid,
                            "exit_ask": leg.exit_ask,
                            "gross_pnl": leg.gross_pnl,
                        }
                    )
    return rows


def _current_candidate_rows(report: MarketDataAccuracyReport) -> list[dict[str, Any]]:
    rows = []
    for candidate in report.current_candidates:
        test = candidate.historical_test_metrics
        architecture = architecture_for(candidate.strategy)
        expirations = "/".join(
            expiration.isoformat()
            for expiration in sorted({leg.expiration for leg in candidate.legs})
        )
        legs = " / ".join(
            f"{leg.position_side.value[0].upper()}{leg.quantity} "
            f"{leg.option_type.value[0].upper()}{leg.strike:g}"
            for leg in candidate.legs
        )
        trade_plan = (
            f"{legs or 'No position'} | expiry {expirations or 'n/a'} | "
            f"{_compact_entry_rule(candidate.entry_rule)} | "
            f"{_compact_exit_rule(candidate.exit_rule)}"
        )
        risk_summary = (
            f"risk {_money(candidate.risk_capital)} | "
            f"max loss {_money(candidate.estimated_max_loss)} | "
            f"delta {_number(candidate.net_delta)} | "
            f"IV {_percent(candidate.signal_implied_volatility)}"
        )
        accuracy_summary = (
            f"Win{test.win_rate:.0%}[{test.win_rate_ci_low:.0%}-"
            f"{test.win_rate_ci_high:.0%}] Med{test.median_return:+.0%} "
            f"CVaR{test.conditional_value_at_risk_95:.0%}"
            if test is not None
            else "n/a"
        )
        liquidity = (
            f"OI {candidate.minimum_open_interest:g}; spread {candidate.max_bid_ask_ratio:.1%}"
            if candidate.minimum_open_interest is not None
            and candidate.max_bid_ask_ratio is not None
            else "n/a"
        )
        blockers = _compact_blockers(candidate.reasons)
        status_label = {
            "eligible": "ELIGIBLE",
            "watchlist": "A SURVEILLER",
            "blocked": "BLOQUE",
            "no_trade": "PAS DE TRADE",
        }[candidate.status]
        display_reasons = [
            reason
            for reason in candidate.reasons
            if not (
                not candidate.legs
                and reason == "current structure exceeds configured EUR risk budget"
            )
        ]
        readable_blockers = _readable_blockers(display_reasons)
        if candidate.strategy is StrategyKind.NO_TRADE:
            decision_summary = "Baseline | no market exposure"
        elif not candidate.legs:
            decision_summary = "No compliant contract | KPIs unavailable"
        else:
            decision_summary = (
                f"{accuracy_summary} Risk{_compact_money(candidate.risk_capital)} "
                f"OI{_compact_count(candidate.minimum_open_interest)} "
                f"Spr{_percent(candidate.max_bid_ask_ratio)}"
            )
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "candidate_label": _variant_label(candidate.candidate_id),
                "experiment_id": candidate.experiment_id,
                "strategy": candidate.strategy.value,
                "architecture": architecture.name if architecture else "No trade",
                "opportunity": (
                    f"{candidate.status.upper()} | "
                    f"{architecture.name if architecture else 'No trade'} | {blockers}"
                ),
                "statut_et_blocage": (
                    f"{status_label} | {architecture.name if architecture else 'Pas de trade'} "
                    f"| Pourquoi: {readable_blockers}"
                ),
                "ticket_ibkr": _ibkr_ticket(candidate),
                "scenario_gagnant": _candidate_scenario(candidate),
                "preuves_et_risque": _evidence_and_risk(candidate),
                "architecture_readiness": (
                    architecture.readiness.value if architecture else "baseline"
                ),
                "setup": _variant_label(candidate.candidate_id),
                "quote_date": candidate.quote_date.isoformat(),
                "expiration": candidate.expiration.isoformat() if candidate.expiration else None,
                "expirations": expirations,
                "status": candidate.status,
                "opportunity_order": {
                    "eligible": 0,
                    "watchlist": 1,
                    "blocked": 2,
                    "no_trade": 3,
                }[candidate.status],
                "legs": legs,
                "trade_plan": trade_plan,
                "entry_rule": candidate.entry_rule,
                "exit_rule": candidate.exit_rule,
                "net_debit_credit": candidate.net_debit_credit,
                "risk_capital": candidate.risk_capital,
                "estimated_max_gain": candidate.estimated_max_gain,
                "estimated_max_loss": candidate.estimated_max_loss,
                "signal_iv": candidate.signal_implied_volatility,
                "net_delta": candidate.net_delta,
                "risk_summary": risk_summary,
                "accuracy_summary": accuracy_summary,
                "liquidity": liquidity,
                "decision_summary": decision_summary,
                "test_win_rate": test.win_rate if test else None,
                "accuracy_ci": (
                    f"{test.win_rate_ci_low:.1%} to {test.win_rate_ci_high:.1%}" if test else "n/a"
                ),
                "test_median_return": test.median_return if test else None,
                "test_cvar_95": test.conditional_value_at_risk_95 if test else None,
                "reasons": "; ".join(candidate.reasons),
                "budget_plan_id": candidate.budget_plan_id,
                "budget_bucket": candidate.budget_bucket,
                "budget_eur": candidate.budget_eur,
                "eur_usd_rate": candidate.eur_usd_rate,
                "eur_usd_rate_date": (
                    candidate.eur_usd_rate_date.isoformat()
                    if candidate.eur_usd_rate_date is not None
                    else None
                ),
                "risk_eur": (
                    candidate.risk_capital / candidate.eur_usd_rate
                    if candidate.risk_capital is not None and candidate.eur_usd_rate is not None
                    else None
                ),
                "current_dte": max(
                    (leg.signal_dte for leg in candidate.legs if leg.signal_dte is not None),
                    default=None,
                ),
            }
        )
    plan_rows = [row for row in rows if row["budget_plan_id"] is not None]
    plan_totals: dict[str, tuple[float, float, int, int]] = {}
    for row in plan_rows:
        plan_id = str(row["budget_plan_id"])
        budget_total, risk_total, available, count = plan_totals.get(plan_id, (0.0, 0.0, 0, 0))
        plan_totals[plan_id] = (
            budget_total + float(row["budget_eur"] or 0),
            risk_total + float(row["risk_eur"] or 0),
            available + int(row["risk_eur"] is not None),
            count + 1,
        )
    plan_labels = {"single_long": "1 TRADE LONG", "staged_three": "3 TEMPS"}
    bucket_labels = {"short": "COURT", "medium": "MOYEN", "long": "LONG"}
    for row in plan_rows:
        plan_id = str(row["budget_plan_id"])
        budget_total, risk_total, available, count = plan_totals[plan_id]
        budget_value = row["budget_eur"]
        assert isinstance(budget_value, (int, float))
        expiry_text = row["expiration"] or "indisponible"
        dte_text = f"{row['current_dte']} jours" if row["current_dte"] is not None else "n/a"
        risk_text = f"EUR {float(row['risk_eur']):.0f}" if row["risk_eur"] is not None else "n/a"
        row["plan_et_budget"] = (
            f"PLAN {plan_labels.get(plan_id, plan_id.upper())} | "
            f"{bucket_labels.get(str(row['budget_bucket']), str(row['budget_bucket']).upper())} "
            f"| poche EUR {float(budget_value):.0f} | risque {risk_text} | "
            f"risque connu du plan EUR {risk_total:.0f} / {budget_total:.0f} | "
            f"{available}/{count} poches disponibles | "
            f"echeance {expiry_text} ({dte_text})"
        )
    return rows


def _equity_rows(report: MarketDataAccuracyReport) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    trades = _trade_rows(report)
    observed_variants = [
        variant
        for variant in report.variants
        if variant.strategy is not StrategyKind.NO_TRADE
        and variant.test_metrics is not None
        and variant.test_metrics.effective_observations >= 8
    ]
    lead = max(
        observed_variants,
        key=lambda variant: float(
            variant.test_metrics.median_return if variant.test_metrics is not None else -10
        ),
        default=None,
    )
    if lead is None:
        return rows
    cumulative = 0.0
    lead_rows = sorted(
        (row for row in trades if row["variant_id"] == lead.variant_id),
        key=lambda row: str(row["actual_exit_date"]),
    )
    for row in lead_rows:
        cumulative += float(row["net_return"] or 0)
        rows.append(
            {
                "variant_id": lead.variant_id,
                "variant_label": _variant_label(lead.variant_id),
                "strategy": row["strategy"],
                "split": row["split"],
                "exit_date": row["actual_exit_date"],
                "cumulative_return": round(cumulative, 8),
            }
        )
    return rows


def _first_spot(
    case: MarketDataPanelCaseResult,
    *,
    signal: bool = False,
    entry: bool | None = None,
) -> float | None:
    if signal:
        return next(
            (leg.signal_underlying_price for leg in case.legs if leg.signal_underlying_price),
            None,
        )
    if entry is True:
        return next(
            (
                leg.entry_underlying_price
                for leg in case.execution_legs
                if leg.entry_underlying_price
            ),
            None,
        )
    return next(
        (leg.exit_underlying_price for leg in case.execution_legs if leg.exit_underlying_price),
        None,
    )


def _signed_greek(case: MarketDataPanelCaseResult, field: str) -> float | None:
    values = []
    for leg in case.legs:
        value = getattr(leg, field)
        if value is not None:
            values.append(leg.position_side.sign * leg.quantity * float(value))
    return sum(values) if values else None


def _variant_label(variant_id: str) -> str:
    if variant_id == StrategyKind.NO_TRADE.value:
        return "No trade"
    experiment_id, separator, strategy = variant_id.partition(":")
    if not separator:
        return variant_id.replace("_", " ").title()
    experiment, _, profile = experiment_id.partition("__")
    parts = experiment.split("_")
    horizon = next(
        (part for part in parts if part.startswith("h") and part[1:].isdigit()),
        "h?",
    )
    dte = next((part for part in parts if part.startswith("dte")), "dte?")
    profile_label = profile.replace("delta", "d").replace("_", "/") if profile else "?"
    architecture = architecture_for(StrategyKind(strategy))
    strategy_label = architecture.name if architecture else strategy.replace("_", " ").title()
    return f"{horizon.upper()} {dte.upper()} {profile_label} | {strategy_label}"
