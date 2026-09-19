"""Dependency-free SVG figures for the auditable decision report."""

from __future__ import annotations

import html
from collections.abc import Callable
from pathlib import Path

from take_two_options.candidate_generation.factory import terminal_payoff
from take_two_options.knowledge.schemas import CompiledStrategyCandidate, DecisionReport

FIGURE_NAMES = [
    "payoff_at_expiration",
    "pnl_distribution",
    "representative_paths",
    "strike_expiration_heatmap",
    "cost_by_strike",
    "probability_gain_by_strike",
    "probability_loss_70_by_strike",
    "expectation_by_profit_target",
    "drawdown_by_profit_target",
    "duration_by_profit_target",
    "stop_sensitivity",
    "dte_sensitivity",
    "iv_sensitivity",
    "pareto_frontier",
    "local_stability",
    "simulation_model_comparison",
]


def _bars(title: str, labels: list[str], values: list[float], note: str) -> str:
    width, height = 720, 360
    if not values:
        labels, values = ["insufficient_data"], [0.0]
    maximum = max(max(abs(value) for value in values), 1.0)
    bar_width = max(8, int(560 / len(values)))
    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        bar_height = 220 * abs(value) / maximum
        x = 100 + index * bar_width
        y = 280 - bar_height if value >= 0 else 280
        color = "#2ca6a4" if value >= 0 else "#ef6f6c"
        bars.append(
            f"<rect x='{x}' y='{y:.1f}' width='{bar_width - 3}' height='{bar_height:.1f}' "
            f"fill='{color}'/><text x='{x}' y='310' font-size='10' "
            f"transform='rotate(25 {x} 310)'>{html.escape(label[:16])}</text>"
        )
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        f"viewBox='0 0 {width} {height}'><rect width='100%' height='100%' fill='white'/>"
        f"<text x='28' y='34' font-size='20' font-family='system-ui'>{html.escape(title)}</text>"
        "<line x1='80' y1='280' x2='690' y2='280' stroke='#555'/>"
        f"{''.join(bars)}<text x='28' y='345' font-size='11' font-family='system-ui' "
        f"fill='#555'>{html.escape(note[:105])}</text></svg>"
    )


def _available_series(
    candidates: list[CompiledStrategyCandidate],
    value_for: Callable[[CompiledStrategyCandidate], float | None],
    *,
    labels_for: Callable[[CompiledStrategyCandidate], str] | None = None,
) -> tuple[list[str], list[float]]:
    pairs: list[tuple[str, float]] = []
    for candidate in candidates:
        value = value_for(candidate)
        if value is None:
            continue
        label = (
            labels_for(candidate)
            if labels_for is not None
            else candidate.candidate_id[-6:]
        )
        pairs.append((label, value))
    return [item[0] for item in pairs], [item[1] for item in pairs]


def _minimum_probability_profit(candidate: CompiledStrategyCandidate) -> float | None:
    values = [metric.probability_profit for metric in candidate.evaluation.model_metrics]
    return min(values) if values else None


def _maximum_probability_loss(candidate: CompiledStrategyCandidate) -> float | None:
    values = [
        metric.probability_loss_70
        for metric in candidate.evaluation.model_metrics
        if metric.probability_loss_70 is not None
    ]
    return max(values) if values else None


def _maximum_metric(
    candidate: CompiledStrategyCandidate,
    name: str,
) -> float | None:
    values = [float(getattr(metric, name)) for metric in candidate.evaluation.model_metrics]
    return max(values) if values else None


def _iv_sensitivity(candidate: CompiledStrategyCandidate) -> float | None:
    higher = candidate.evaluation.stress_results.get("iv_plus_10pct_proxy")
    lower = candidate.evaluation.stress_results.get("iv_minus_10pct_proxy")
    if higher is None or lower is None:
        return None
    return higher - lower


def _figure_data(report: DecisionReport, name: str) -> tuple[list[str], list[float], str]:
    candidates = report.candidates
    labels = [candidate.candidate_id[-6:] for candidate in candidates]
    if name == "payoff_at_expiration" and candidates:
        candidate = candidates[0]
        spot = candidate.legs[0].quote.strike
        spots = [spot * factor for factor in (0.6, 0.8, 1.0, 1.2, 1.4)]
        return (
            [f"{value:.0f}" for value in spots],
            [
                terminal_payoff(candidate.legs, value)
                - candidate.risk.entry_debit
                - candidate.risk.fees
                - candidate.risk.slippage
                for value in spots
            ],
            "Terminal payoff uses whole contracts and executable entry sides.",
        )
    if name in {"pnl_distribution", "simulation_model_comparison"} and candidates:
        metrics = candidates[0].evaluation.model_metrics
        return (
            [metric.model_id for metric in metrics],
            [metric.expected_pnl for metric in metrics],
            "Models are shown separately; no fixed ensemble weights are imposed.",
        )
    if name == "cost_by_strike":
        return labels, [candidate.risk.total_cost for candidate in candidates], "Modeled USD cost."
    if name == "probability_gain_by_strike":
        series_labels, values = _available_series(
            candidates,
            _minimum_probability_profit,
        )
        return (
            series_labels,
            values,
            "Conservative probability across separate simulation models.",
        )
    if name == "probability_loss_70_by_strike":
        series_labels, values = _available_series(
            candidates,
            _maximum_probability_loss,
        )
        return (
            series_labels,
            values,
            "Higher bars indicate more simulated severe-loss risk.",
        )
    if name in {"expectation_by_profit_target", "stop_sensitivity", "dte_sensitivity"}:
        series_labels, values = _available_series(
            candidates,
            lambda candidate: candidate.evaluation.conservative_expected_pnl,
            labels_for=lambda candidate: (
                f"{candidate.exit_policy.profit_target}/"
                f"{candidate.exit_policy.stop_loss}/"
                f"{candidate.exit_policy.maximum_holding_days}"
            ),
        )
        return (
            series_labels,
            values,
            "Parameters are experimental search points, not universal thresholds.",
        )
    if name == "drawdown_by_profit_target":
        series_labels, values = _available_series(
            candidates,
            lambda candidate: _maximum_metric(candidate, "simulated_drawdown"),
        )
        return (
            series_labels,
            values,
            "Worst simulated path drawdown by displayed candidate.",
        )
    if name == "duration_by_profit_target":
        series_labels, values = _available_series(
            candidates,
            lambda candidate: _maximum_metric(candidate, "mean_exit_days"),
        )
        return (
            series_labels,
            values,
            "Mean modeled exit time; no execution recommendation.",
        )
    if name == "iv_sensitivity":
        series_labels, values = _available_series(candidates, _iv_sensitivity)
        return (
            series_labels,
            values,
            "Proxy only; detailed future IV-surface forecasting remains unavailable.",
        )
    if name == "pareto_frontier":
        series_labels, values = _available_series(
            candidates,
            lambda candidate: (
                float(candidate.pareto_rank)
                if candidate.pareto_rank is not None
                else None
            ),
        )
        return (
            series_labels,
            values,
            "Pareto rank precedes the explanatory score.",
        )
    if name == "local_stability":
        series_labels, values = _available_series(
            candidates,
            lambda candidate: candidate.evaluation.local_stability,
        )
        return (
            series_labels,
            values,
            "Isolated optima receive low or unavailable stability.",
        )
    series_labels, values = _available_series(
        candidates,
        lambda candidate: candidate.evaluation.conservative_expected_pnl,
    )
    return (
        series_labels,
        values,
        "Figure is bounded by the candidates and data available in this run.",
    )


def write_visualizations(report: DecisionReport, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name in FIGURE_NAMES:
        labels, values, note = _figure_data(report, name)
        path = directory / f"{name}.svg"
        path.write_text(
            _bars(name.replace("_", " ").title(), labels, values, note),
            encoding="utf-8",
        )
        paths.append(path)
    return paths
