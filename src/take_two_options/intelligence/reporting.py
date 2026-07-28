"""JSON, Markdown, and standalone HTML reporting for V11."""

from __future__ import annotations

import html
from pathlib import Path

from take_two_options.intelligence.schemas import V11IntelligenceReport


def markdown_report(report: V11IntelligenceReport) -> str:
    lines = [
        "# V11 — Probabilistic Strategy Intelligence & Execution Monitor",
        "",
        f"- Posture : `{report.posture.value}`",
        f"- Base V10.1 : `{report.base_v10_report_id}`",
        f"- Données : `{report.data_snapshot.snapshot_id}`",
        "- Exécution : `forbidden` ; `transmit=false` ; `what_if=true` ; validation humaine",
        "",
        "## Données et connecteurs",
        "",
        "- Séries requises manquantes : "
        + (
            ", ".join(report.data_snapshot.missing_required_series)
            if report.data_snapshot.missing_required_series
            else "aucune"
        ),
    ]
    lines.extend(
        f"- `{connector.connector_id}` : `{connector.state.value}` ; "
        f"{connector.observations} observations"
        for connector in report.data_snapshot.connectors
    )
    lines.extend(
        [
            "",
        "## Distribution bayésienne",
        "",
        "| Scénario | Probabilité |",
        "| --- | ---: |",
        ]
    )
    lines.extend(
        f"| {scenario} | {probability:.2%} |"
        for scenario, probability in sorted(
            report.bayesian_distribution.scenario_probabilities.items()
        )
    )
    lines.extend(
        [
            "",
            "Chaque mise à jour conserve le prior, la vraisemblance, le poids effectif, "
            "le posterior, la famille et les contradictions. Les faits dupliqués ne "
            "sont comptés qu'une fois.",
            "",
            "## Covariance dynamique",
            "",
            f"- Local vol : `{report.local_volatility_calibration.status}` "
            f"({report.local_volatility_calibration.output_nodes} nœuds, "
            f"{report.local_volatility_calibration.fallback_nodes} fallbacks)",
            f"- Statut : `{report.covariance.status}`",
            f"- Facteurs : {', '.join(report.covariance.factors) or 'aucun'}",
            f"- Shrinkage : {report.covariance.shrinkage_intensity:.2f}",
            f"- Valeur propre minimale : {report.covariance.minimum_eigenvalue:.6g}",
        ]
    )
    lines.extend(f"- Limite : {warning}" for warning in report.covariance.warnings)
    lines.extend(
        [
            "",
            "## Comparaison multi-modèles",
            "",
            "| Candidat | Modèle | Régime | P(profit) | P(perte totale) | "
            "P(x2) | P(x3) | P(x5) | P&L moyen USD | CVaR 95 USD |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for metric in report.model_metrics:
        lines.append(
            f"| {metric.candidate_id} | {metric.model.value} | {metric.regime.value} | "
            f"{metric.probability_profit:.1%} | {metric.probability_total_loss:.1%} | "
            f"{metric.probability_x2:.1%} | {metric.probability_x3:.1%} | "
            f"{metric.probability_x5:.1%} | {metric.expected_pnl_usd:.2f} | "
            f"{metric.cvar_95_usd:.2f} |"
        )
    lines.extend(["", "## Allocations sous contraintes", ""])
    for allocation in report.allocations:
        label = "cash / aucune stratégie" if allocation.no_trade else ", ".join(
            f"{line.strategy_units}× {line.candidate_id}" for line in allocation.lines
        )
        lines.extend(
            [
                f"### {allocation.profile} — rang {allocation.rank}",
                "",
                f"- Allocation : {label}",
                f"- Réserve : {allocation.cash_reserve_eur:.2f} EUR",
                f"- P&L espéré : {allocation.expected_pnl_eur:.2f} EUR",
                f"- CVaR 95 : {allocation.cvar_95_eur:.2f} EUR",
                f"- Dispersion modèles : {allocation.model_dispersion_eur:.2f} EUR",
                f"- Objectif normalisé : {allocation.objective:.6f}",
                "",
            ]
        )
    lines.extend(["## Validation walk-forward / stress / paper", ""])
    for validation in report.validation:
        lines.append(
            f"- `{validation.candidate_id}` : walk-forward="
            f"`{validation.walk_forward_status}` ; holdout="
            f"`{validation.holdout_status}` ; stress="
            f"`{validation.stress_status}` ; paper=`{validation.paper_status}` ; "
            "promotion=false"
        )
    lines.append("")
    lines.extend(["## Plans de sortie", ""])
    for plan in report.exit_plans:
        lines.extend(
            [
                f"### {plan.candidate_id}",
                "",
                f"- Profit : +{plan.profit_target:.0%}",
                f"- Prise partielle : +{plan.partial_profit_target:.0%}",
                f"- Stop opérationnel : -{plan.operational_stop_loss:.0%}",
                f"- Sortie temps : {plan.exit_days_before_expiration} jours avant échéance",
                f"- IV crush : {plan.iv_crush_threshold:.0%}",
                f"- Trailing : {plan.trailing_drawdown:.0%}",
                "",
            ]
        )
    lines.extend(["## Tickets IBKR", ""])
    for preview in report.execution_previews:
        lines.append(
            f"- `{preview.candidate_id}` : limite indicative "
            f"{preview.limit_debit_usd:.4f} USD/action ; "
            f"`transmit={str(preview.transmit).lower()}` ; "
            f"`what_if={str(preview.what_if).lower()}` ; "
            f"blockers={len(preview.blockers)}"
        )
    lines.extend(["", "## Limites et validations", ""])
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "### Validations requises", ""])
    lines.extend(f"- {item}" for item in report.validations_required)
    return "\n".join(lines) + "\n"


def html_report(report: V11IntelligenceReport) -> str:
    connector_rows = "".join(
        "<tr>"
        f"<td>{html.escape(connector.connector_id)}</td>"
        f"<td>{html.escape(connector.state.value)}</td>"
        f"<td>{connector.observations}</td>"
        f"<td>{html.escape(' · '.join(connector.warnings) or connector.error or '—')}</td>"
        "</tr>"
        for connector in report.data_snapshot.connectors
    )
    missing_series = (
        ", ".join(report.data_snapshot.missing_required_series)
        if report.data_snapshot.missing_required_series
        else "aucune"
    )
    posterior_rows = "".join(
        f"<tr><td>{html.escape(scenario)}</td><td>{probability:.2%}</td></tr>"
        for scenario, probability in sorted(
            report.bayesian_distribution.scenario_probabilities.items()
        )
    )
    model_rows = "".join(
        "<tr>"
        f"<td>{html.escape(metric.candidate_id)}</td>"
        f"<td>{html.escape(metric.model.value)}</td>"
        f"<td>{html.escape(metric.regime.value)}</td>"
        f"<td>{metric.probability_profit:.1%}</td>"
        f"<td>{metric.probability_total_loss:.1%}</td>"
        f"<td>{metric.expected_pnl_usd:.2f}</td>"
        f"<td>{metric.cvar_95_usd:.2f}</td>"
        "</tr>"
        for metric in report.model_metrics
    )
    allocation_card_parts: list[str] = []
    for allocation in report.allocations:
        if allocation.rank > 3:
            continue
        allocation_label = (
            "cash / aucune stratégie"
            if allocation.no_trade
            else ", ".join(
                f"{line.strategy_units}× {line.candidate_id}"
                for line in allocation.lines
            )
        )
        allocation_card_parts.append(
            "<article>"
            f"<h3>{html.escape(allocation.profile)} · #{allocation.rank}</h3>"
            f"<p>{html.escape(allocation_label)}</p>"
            f"<dl><div><dt>Réserve</dt><dd>{allocation.cash_reserve_eur:.2f} EUR</dd></div>"
            f"<div><dt>P&amp;L espéré</dt><dd>{allocation.expected_pnl_eur:.2f} EUR</dd></div>"
            f"<div><dt>CVaR 95</dt><dd>{allocation.cvar_95_eur:.2f} EUR</dd></div>"
            f"<div><dt>Objectif</dt><dd>{allocation.objective:.6f}</dd></div></dl>"
            "</article>"
        )
    allocation_cards = "".join(allocation_card_parts)
    validation_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.candidate_id)}</td>"
        f"<td>{html.escape(item.walk_forward_status)}</td>"
        f"<td>{html.escape(item.holdout_status)}</td>"
        f"<td>{html.escape(item.stress_status)}</td>"
        f"<td>{html.escape(item.paper_status)}</td>"
        f"<td>{str(item.promotion_eligible).lower()}</td>"
        "</tr>"
        for item in report.validation
    )
    preview_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.candidate_id)}</td>"
        f"<td>{item.limit_debit_usd:.4f}</td>"
        f"<td>{str(item.transmit).lower()}</td>"
        f"<td>{str(item.what_if).lower()}</td>"
        f"<td>{html.escape(' · '.join(item.blockers))}</td>"
        "</tr>"
        for item in report.execution_previews
    )
    limitations = "".join(f"<li>{html.escape(item)}</li>" for item in report.limitations)
    validations_required = "".join(
        f"<li>{html.escape(item)}</li>" for item in report.validations_required
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>V11 · TTWO Strategy Intelligence</title>
<style>
:root{{--ink:#172019;--muted:#657064;--paper:#f5f1e8;--card:#fffdf8;
--line:#d9d2c3;--green:#235d3a;--amber:#9a6416}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.5 ui-sans-serif,system-ui,sans-serif}}
main{{max-width:1240px;margin:auto;padding:32px 20px 64px}}
header{{border-bottom:2px solid var(--ink);padding-bottom:22px}}
.eyebrow{{text-transform:uppercase;letter-spacing:.14em;color:var(--green);
font-weight:750;font-size:12px}}
h1{{font:700 clamp(32px,6vw,64px)/1.02 ui-serif,Georgia,serif;margin:.2em 0}}
h2{{margin-top:40px;font:700 30px/1.1 ui-serif,Georgia,serif}}
.status{{display:inline-flex;gap:12px;flex-wrap:wrap}}
.pill{{padding:6px 10px;border:1px solid var(--line);background:var(--card);
border-radius:999px}}
.warn{{color:var(--amber);font-weight:700}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}
article{{background:var(--card);border:1px solid var(--line);padding:18px;
border-radius:14px}}
dl div{{display:flex;justify-content:space-between;border-top:1px solid var(--line);
padding:7px 0}}
dt{{color:var(--muted)}}dd{{margin:0;font-variant-numeric:tabular-nums}}
.table{{overflow:auto;border:1px solid var(--line);border-radius:12px}}
table{{width:100%;border-collapse:collapse;background:var(--card)}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;
white-space:nowrap}}
th{{position:sticky;top:0;background:#ebe5d8}}
@media(max-width:560px){{main{{padding:22px 12px 48px}}}}
</style>
</head>
<body><main>
<header><div class="eyebrow">V11 · research-only · explicable</div>
<h1>Probabilistic Strategy Intelligence</h1>
<div class="status"><span class="pill">posture: {html.escape(report.posture.value)}</span>
<span class="pill">transmit=false</span><span class="pill">what_if=true</span>
<span class="pill warn">confirmation humaine</span></div></header>
<section><h2>Données et connecteurs</h2>
<p>Séries requises manquantes : <strong>{html.escape(missing_series)}</strong></p>
<div class="table"><table><thead><tr><th>Connecteur</th><th>Statut</th>
<th>Observations</th><th>Avertissements</th></tr></thead>
<tbody>{connector_rows}</tbody></table></div></section>
<section><h2>Distribution bayésienne</h2><div class="table"><table>
<thead><tr><th>Scénario</th><th>Probabilité</th></tr></thead><tbody>{posterior_rows}</tbody>
</table></div></section>
<section><h2>Allocations robustes</h2><div class="grid">{allocation_cards}</div></section>
<section><h2>Comparaison multi-modèles</h2><div class="table"><table>
<thead><tr><th>Candidat</th><th>Modèle</th><th>Régime</th><th>P(profit)</th>
<th>P(perte totale)</th><th>P&amp;L moyen USD</th><th>CVaR 95 USD</th></tr></thead>
<tbody>{model_rows}</tbody></table></div></section>
<section><h2>Validation et promotion</h2><div class="table"><table>
<thead><tr><th>Candidat</th><th>Walk-forward</th><th>Holdout</th><th>Stress</th>
<th>Paper</th><th>Promotion</th></tr></thead>
<tbody>{validation_rows}</tbody></table></div></section>
<section><h2>Previews IBKR bloquées</h2><div class="table"><table>
<thead><tr><th>Candidat</th><th>Limite USD/action</th><th>Transmit</th>
<th>What-if</th><th>Blockers</th></tr></thead>
<tbody>{preview_rows}</tbody></table></div></section>
<section><h2>Covariance et limites</h2>
<p>Local vol: <strong>{html.escape(report.local_volatility_calibration.status)}</strong> ·
{report.local_volatility_calibration.output_nodes} nœuds ·
statut covariance: <strong>{html.escape(report.covariance.status)}</strong> ·
shrinkage {report.covariance.shrinkage_intensity:.2f} ·
facteurs {html.escape(', '.join(report.covariance.factors) or 'aucun')}</p>
<ul>{limitations}</ul>
<h3>Validations requises</h3><ul>{validations_required}</ul></section>
</main></body></html>"""


def write_reports(
    report: V11IntelligenceReport,
    *,
    json_out: Path,
    markdown_out: Path,
    html_out: Path,
) -> V11IntelligenceReport:
    for path in (json_out, markdown_out, html_out):
        path.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    markdown_out.write_text(markdown_report(report), encoding="utf-8")
    html_out.write_text(html_report(report), encoding="utf-8")
    return report
