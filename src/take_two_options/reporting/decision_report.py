"""Canonical JSON, readable Markdown, and standalone HTML decision reports."""

from __future__ import annotations

import base64
import html
from pathlib import Path

from take_two_options.knowledge.schemas import CompiledStrategyCandidate, DecisionReport
from take_two_options.reporting.visualizations import write_visualizations


def _percentage(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "N/A"


def _candidate_markdown(candidate: CompiledStrategyCandidate) -> list[str]:
    metrics = candidate.evaluation.model_metrics
    conservative = candidate.evaluation.conservative_expected_pnl
    validation = candidate.evaluation.validation
    lines = [
        f"### {candidate.candidate_id}",
        "",
        f"- Pareto rank: `{candidate.pareto_rank or 'unranked'}`",
        f"- Explanatory score: `{candidate.explanatory_score}`",
        f"- Architecture / recipe: `{candidate.architecture.value}` / `{candidate.recipe_id}`",
        f"- Status: `{candidate.status}`",
        f"- Entry debit: `{candidate.risk.entry_debit:.2f} USD`",
        f"- Total modeled cost: `{candidate.risk.total_cost:.2f} USD`",
        f"- Fees / slippage: `{candidate.risk.fees:.2f}` / "
        f"`{candidate.risk.slippage:.2f} USD`",
        (
            f"- Maximum loss: `{candidate.risk.maximum_loss:.2f} USD`"
            if candidate.risk.maximum_loss is not None
            else "- Maximum loss: `UNKNOWN / BLOCKED`"
        ),
        f"- Maximum gain: `{candidate.risk.maximum_gain}`",
        f"- Break-even: `{candidate.risk.break_even_points}`",
        (
            f"- Budget remaining: `{candidate.risk.budget_remaining:.2f} request currency`"
            if candidate.risk.budget_remaining is not None
            else "- Budget remaining: `UNKNOWN / BLOCKED`"
        ),
        f"- TP / robust zone: `{candidate.exit_policy.profit_target}` / "
        f"`{candidate.evaluation.local_stability}`",
        f"- Stop: `{candidate.exit_policy.stop_loss}`",
        f"- Holding period: `{candidate.exit_policy.maximum_holding_days} days`",
        f"- Rolling: `{candidate.maintenance_policy.rolling_rule}`",
        f"- Capital recovery: `{candidate.maintenance_policy.capital_recovery_rule}`",
        f"- Conservative expected P&L: `{conservative}`",
        f"- Model dispersion: `{candidate.evaluation.model_dispersion}`",
        f"- DSR / PBO: `{validation.deflated_sharpe_probability if validation else None}` / "
        f"`{validation.pbo if validation else None}`",
        f"- Validation: `{validation.status if validation else 'not_run'}`",
        f"- Complexity penalty: `{candidate.evaluation.complexity_penalty:.4f}`",
        f"- Hard vetoes: `{candidate.hard_vetoes}`",
        "",
        "| Side | Qty | Type | Strike | Expiration | Entry | Symbol | Quality |",
        "| --- | ---: | --- | ---: | --- | ---: | --- | --- |",
    ]
    for leg in candidate.legs:
        lines.append(
            f"| {leg.side.value} | {leg.quantity} | {leg.quote.option_type.value} | "
            f"{leg.quote.strike:.2f} | {leg.quote.expiration.isoformat()} | "
            f"{leg.entry_price:.2f} | `{leg.quote.symbol}` | {leg.quote.price_quality} |"
        )
    lines.extend(["", "Model metrics:", ""])
    for metric in metrics:
        lines.append(
            f"- `{metric.model_id}` [{metric.eligibility.value}]: "
            f"P(gain) {metric.probability_profit:.1%}; "
            f"P(+50/+80/+100%) {_percentage(metric.probability_gain_50)}/"
            f"{_percentage(metric.probability_gain_80)}/"
            f"{_percentage(metric.probability_gain_100)}; "
            f"P(-50/-70%) {_percentage(metric.probability_loss_50)}/"
            f"{_percentage(metric.probability_loss_70)}; expected {metric.expected_pnl:.2f}; "
            f"median {metric.median_pnl:.2f}; VaR/CVaR "
            f"{metric.var_95:.2f}/{metric.cvar_95:.2f}; mean exit "
            f"{metric.mean_exit_days:.1f} days."
        )
    if validation:
        lines.extend(["", "Validation gates:", ""])
        lines.extend(f"- `{name}`: `{status}`" for name, status in validation.gates.items())
    lines.extend(["", f"Uncertainties: `{candidate.uncertainties}`", ""])
    return lines


def render_markdown_report(report: DecisionReport) -> str:
    lines = [
        "# ANALYSE",
        "",
        f"- Ticker: `{report.analysis.ticker}`",
        f"- Budget: `{report.analysis.budget:.2f} {report.analysis.currency}`",
        f"- Thèse: {report.analysis.thesis}",
        f"- Horizon: `{report.analysis.horizon_days[0]}–"
        f"{report.analysis.horizon_days[1]} jours`",
        f"- Date des données: `{report.analysis.data_date}`",
        f"- Qualité des données: `{report.analysis.data_quality}`",
        f"- Statut du holdout: `{report.analysis.holdout_status}`",
        f"- Nombre total d’essais: `{report.analysis.total_trials}`",
        "",
        "# VERDICT",
        "",
        f"`{report.verdict.value}`",
        "",
    ]
    if report.no_trade_reasons:
        lines.extend(["Raisons:", ""])
        lines.extend(f"- {reason}" for reason in report.no_trade_reasons)
        lines.append("")
    lines.extend(["## Candidats constructibles ou finalistes bloqués", ""])
    if not report.candidates:
        lines.extend(["Aucun candidat constructible n’est disponible.", ""])
    if report.candidate_comparison:
        lines.extend(["## Diagnostics des structures les plus proches", ""])
        for item in report.candidate_comparison:
            lines.append(
                f"- `{item.get('candidate_id')}` · `{item.get('architecture')}` · "
                f"perte max `{item.get('maximum_loss_usd', item.get('maximum_loss'))}` · "
                f"veto `{item.get('hard_vetoes', item.get('status'))}`"
            )
        lines.append("")
    for candidate in report.candidates:
        lines.extend(_candidate_markdown(candidate))
    lines.extend(["## Limites", ""])
    lines.extend(f"- {limitation}" for limitation in report.limitations)
    lines.extend(["", "## Provenance", ""])
    lines.extend(
        f"- `{source.source_id}` — {source.title} ({source.uri or 'source locale'})"
        for source in report.sources
    )
    lines.extend(["", "## Audit", ""])
    lines.extend(f"- `{path}`" for path in report.audit_files)
    lines.extend(["", "- Order capability: `forbidden`", ""])
    return "\n".join(lines)


def _standalone_html(report: DecisionReport, markdown: str, svg_paths: list[Path]) -> str:
    figures = []
    for path in svg_paths:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        figures.append(
            f"<figure><img alt='{html.escape(path.stem)}' "
            f"src='data:image/svg+xml;base64,{encoded}'></figure>"
        )
    candidate_rows = "".join(
        "<tr>"
        f"<td>{html.escape(candidate.candidate_id)}</td>"
        f"<td>{html.escape(candidate.architecture.value)}</td>"
        f"<td>{candidate.risk.maximum_loss:.2f}</td>"
        f"<td>{candidate.evaluation.conservative_expected_pnl}</td>"
        f"<td>{html.escape(candidate.status)}</td>"
        "</tr>"
        if candidate.risk.maximum_loss is not None
        else "<tr>"
        f"<td>{html.escape(candidate.candidate_id)}</td>"
        f"<td>{html.escape(candidate.architecture.value)}</td>"
        "<td>UNKNOWN / BLOCKED</td>"
        f"<td>{candidate.evaluation.conservative_expected_pnl}</td>"
        f"<td>{html.escape(candidate.status)}</td>"
        "</tr>"
        for candidate in report.candidates
    )
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{html.escape(report.report_id)}</title>
<style>
body{{font:15px system-ui;margin:0;background:#0b1020;color:#e8ecf3}}
main{{max-width:1180px;margin:auto;padding:32px}}
.hero{{padding:24px;background:#141c32;border-radius:16px}}
.verdict{{font-size:28px;color:#80d4ff}} table{{width:100%;border-collapse:collapse;margin:24px 0}}
th,td{{padding:9px;border-bottom:1px solid #34405d;text-align:left}} .grid{{display:grid;
grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}
figure{{margin:0;background:white;
border-radius:10px;overflow:hidden}} img{{width:100%;display:block}} pre{{white-space:pre-wrap;
background:#11182a;padding:18px;border-radius:12px;overflow:auto}}
</style></head><body><main>
<section class="hero"><div>ANALYSE · {html.escape(report.analysis.ticker)} ·
{report.analysis.budget:.0f} {report.analysis.currency}</div>
<div class="verdict">{html.escape(report.verdict.value)}</div>
<p>{html.escape("; ".join(report.no_trade_reasons))}</p></section>
<table><thead><tr><th>ID</th><th>Architecture</th><th>Perte max USD</th>
<th>Espérance prudente</th><th>Statut</th></tr></thead><tbody>{candidate_rows}</tbody></table>
<section class="grid">{''.join(figures)}</section>
<details><summary>Rapport Markdown canonique</summary><pre>{html.escape(markdown)}</pre></details>
</main></body></html>"""


def write_decision_report(report: DecisionReport, report_dir: Path) -> DecisionReport:
    report_dir.mkdir(parents=True, exist_ok=True)
    svg_paths = write_visualizations(report, report_dir / "visualizations")
    report.visualization_files = [str(path) for path in svg_paths]
    markdown = render_markdown_report(report)
    (report_dir / "decision_report.json").write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    (report_dir / "decision_report.md").write_text(markdown, encoding="utf-8")
    (report_dir / "decision_report.html").write_text(
        _standalone_html(report, markdown, svg_paths), encoding="utf-8"
    )
    return report
