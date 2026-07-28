"""JSON, Markdown, and network-free standalone HTML reporting for V11.1."""

from __future__ import annotations

import html
from pathlib import Path

from take_two_options.intelligence.schemas import V11IntelligenceReport


def markdown_report(report: V11IntelligenceReport) -> str:
    calibration_status = str(report.offline_calibration.get("status", "unknown"))
    backtest_status = str(report.walk_forward_backtest.get("status", "unknown"))
    sensitivity = report.bayesian_distribution.sensitivity
    lines = [
        "# V11.1 — Offline Reliability & Probabilistic Strategy Intelligence",
        "",
        f"- Posture : `{report.posture.value}`",
        f"- Readiness du résultat : `{report.machine_summary.result_status.value}`",
        f"- Base V10.1 : `{report.base_v10_report_id}`",
        f"- Run : `{report.run_manifest.run_id}`",
        f"- Cutoff : `{report.machine_summary.cutoff.isoformat()}`",
        f"- Configuration : `{report.run_manifest.configuration_hash}`",
        f"- Données : `{report.run_manifest.data_hash}`",
        "- Exécution : `forbidden` ; `transmit=false` ; `what_if=true` ; confirmation humaine",
        "",
        "## 1. État des données",
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
            "## 2. Statut de calibration et de backtest",
            "",
            f"- Calibration historique : `{calibration_status}`",
            f"- Walk-forward : `{backtest_status}`",
            "- Aucun dataset manquant n'est remplacé par une fixture.",
            "",
            "## 3. Probabilités initiales, postérieures et sensibilité",
            "",
            "| Scénario | Posterior | Minimum sensibilité | Maximum sensibilité |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for scenario, probability in sorted(
        report.bayesian_distribution.scenario_probabilities.items()
    ):
        minimum = (
            sensitivity.posterior_minimum[scenario] if sensitivity is not None else probability
        )
        maximum = (
            sensitivity.posterior_maximum[scenario] if sensitivity is not None else probability
        )
        lines.append(
            f"| {scenario} | {probability:.2%} | {minimum:.2%} | {maximum:.2%} |"
        )
    lines.extend(
        [
            "",
            f"- Confiance : `{report.bayesian_distribution.confidence_level}`",
            f"- Classement stable sous sensibilité : "
            f"`{sensitivity.ranking_stable if sensitivity else False}`",
            "",
            "## 4. Provenance des événements",
            "",
            "| Événement | Type | Famille | Règle | Revue | Sources |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for event in report.event_normalization.events:
        lines.append(
            f"| {event.event_id} | {event.event_type.value} | {event.family.value} | "
            f"{event.normalization_rule_id} | {event.human_review_status.value} | "
            f"{', '.join(event.source_ids)} |"
        )
    if not report.event_normalization.events:
        lines.append("| — | aucun événement | — | — | — | — |")
    lines.extend(["", "## 5. Contradictions", ""])
    if report.event_normalization.contradiction_clusters:
        lines.extend(
            f"- `{cluster}` : {', '.join(event_ids)}"
            for cluster, event_ids in report.event_normalization.contradiction_clusters.items()
        )
    else:
        lines.append("- Aucune contradiction normalisée dans ce run.")
    lines.extend(
        [
            "",
            "## 6–11. Comparaison des modèles et distribution du P&L",
            "",
            "| Candidat | Modèle | Régime | Validité | Convergence | IC 95 % P&L | "
            "P(profit) | P(perte totale) | x2/x3/x5 | VaR/CVaR |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for metric in report.model_metrics:
        lines.append(
            f"| {metric.candidate_id} | {metric.model.value} | {metric.regime.value} | "
            f"{metric.calibration_status} | {metric.convergence_status} | "
            f"[{metric.confidence_interval_95_low_usd:.2f}, "
            f"{metric.confidence_interval_95_high_usd:.2f}] | "
            f"{metric.probability_profit:.1%} | {metric.probability_total_loss:.1%} | "
            f"{metric.probability_x2:.1%}/{metric.probability_x3:.1%}/"
            f"{metric.probability_x5:.1%} | "
            f"{metric.var_95_usd:.2f}/{metric.cvar_95_usd:.2f} |"
        )
    lines.extend(
        [
            "",
            "## 12. Robustesse et désaccord des modèles",
            "",
            "| Candidat | Verdict | Score | Dispersion P(profit) | Dispersion P&L | "
            "Dispersion CVaR | Modèles invalides |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in report.robustness:
        lines.append(
            f"| {item.candidate_id} | {item.verdict.value} | "
            f"{item.robustness_score:.1f} | {item.probability_profit_dispersion:.1%} | "
            f"{item.expected_pnl_dispersion_usd:.2f} | {item.cvar_dispersion_usd:.2f} | "
            f"{item.invalid_model_count} |"
        )
    lines.extend(
        [
            "",
            "## 13. Stress tests",
            "",
            "| Candidat | Stress | Statut | P&L stressé | Méthode |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for stress in report.stress_tests:
        pnl = "n/a" if stress.stressed_pnl_usd is None else f"{stress.stressed_pnl_usd:.2f}"
        lines.append(
            f"| {stress.candidate_id} | {stress.stress_id} | {stress.status} | "
            f"{pnl} | {stress.method} |"
        )
    lines.extend(["", "## 14–15. Allocation et cash non utilisé", ""])
    for allocation in report.allocations:
        label = "cash / NO_TRADE" if allocation.no_trade else ", ".join(
            f"{line.strategy_units}× {line.candidate_id}" for line in allocation.lines
        )
        lines.extend(
            [
                f"### {allocation.profile} — rang {allocation.rank}",
                "",
                f"- Allocation : {label}",
                f"- Réserve : {allocation.cash_reserve_eur:.2f} EUR",
                f"- P&L espéré expérimental : {allocation.expected_pnl_eur:.2f} EUR",
                f"- CVaR 95 : {allocation.cvar_95_eur:.2f} EUR",
                f"- Contraintes actives : "
                f"{', '.join(allocation.active_constraints) or 'aucune proche de la borne'}",
                f"- Motif du cash : {allocation.cash_reason}",
                "",
            ]
        )
    lines.extend(["## 16. Risques d'exécution", ""])
    for preview in report.execution_previews:
        lines.append(
            f"- `{preview.candidate_id}` : `transmit={str(preview.transmit).lower()}` ; "
            f"`what_if={str(preview.what_if).lower()}` ; "
            f"`order_capability={preview.order_capability}` ; "
            f"blockers={len(preview.blockers)}"
        )
    lines.extend(["", "## 17. Règles de sortie", ""])
    for plan in report.exit_plans:
        lines.append(f"### {plan.candidate_id}")
        lines.append("")
        lines.extend(
            f"- `{rule.rule_id}` → `{rule.suggested_action.value}` ; "
            f"seuil=`{rule.threshold}` ; données={', '.join(rule.required_data)}"
            for rule in plan.rules
        )
        lines.append("")
    lines.extend(["## 18. Conditions d'invalidation", ""])
    for plan in report.exit_plans:
        lines.append(
            f"- `{plan.candidate_id}` : "
            f"{'; '.join(plan.fundamental_invalidations) or 'aucune règle fournie'}"
        )
    lines.extend(
        [
            "",
            "## 19. Readiness status",
            "",
            "| Fonction | Statut | Implémentée | Blockers |",
            "| --- | --- | --- | --- |",
        ]
    )
    for readiness in report.readiness:
        lines.append(
            f"| {readiness.feature} | {readiness.status.value} | "
            f"{str(readiness.implemented).lower()} | "
            f"{' · '.join(readiness.blockers) or '—'} |"
        )
    lines.extend(["", "## 20. Raisons de NO_TRADE ou blocage", ""])
    lines.extend(f"- {item}" for item in report.machine_summary.blocking_reasons)
    lines.extend(
        [
            "",
            "## Exports et reproductibilité",
            "",
            "- Exports : JSON strict, Markdown et HTML autonome.",
            f"- Schéma : `{report.schema_version}`",
            f"- Seed : `{report.run_manifest.seed}`",
            f"- Profil : `{report.run_manifest.profile}`",
            f"- Versions : `{report.run_manifest.model_versions}`",
            f"- Durées : `{report.run_manifest.stage_durations_seconds}`",
            "",
            "## Limites et validations requises",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.limitations)
    lines.extend(["", "### Validations requises", ""])
    lines.extend(f"- {item}" for item in report.validations_required)
    return "\n".join(lines) + "\n"


def html_report(report: V11IntelligenceReport) -> str:
    def esc(value: object) -> str:
        return html.escape(str(value))

    connector_rows = "".join(
        "<tr>"
        f"<td>{esc(connector.connector_id)}</td>"
        f"<td><code>{esc(connector.state.value)}</code></td>"
        f"<td>{connector.observations}</td>"
        f"<td>{esc(' · '.join(connector.warnings) or connector.error or '—')}</td>"
        "</tr>"
        for connector in report.data_snapshot.connectors
    )
    posterior_rows = "".join(
        "<tr>"
        f"<td>{esc(scenario)}</td><td>{probability:.2%}</td>"
        f"<td>{report.bayesian_distribution.sensitivity.posterior_minimum[scenario]:.2%}</td>"
        f"<td>{report.bayesian_distribution.sensitivity.posterior_maximum[scenario]:.2%}</td>"
        "</tr>"
        for scenario, probability in sorted(
            report.bayesian_distribution.scenario_probabilities.items()
        )
        if report.bayesian_distribution.sensitivity is not None
    )
    event_rows = "".join(
        "<tr>"
        f"<td>{esc(event.event_type.value)}</td><td>{esc(event.family.value)}</td>"
        f"<td>{esc(event.normalization_rule_id)}</td>"
        f"<td>{esc(event.human_review_status.value)}</td>"
        f"<td>{esc(', '.join(event.source_ids))}</td>"
        "</tr>"
        for event in report.event_normalization.events
    ) or "<tr><td colspan=\"5\">Aucun événement normalisé.</td></tr>"
    contradiction_rows = "".join(
        f"<li><code>{esc(cluster)}</code> : {esc(', '.join(event_ids))}</li>"
        for cluster, event_ids in report.event_normalization.contradiction_clusters.items()
    ) or "<li>Aucune contradiction normalisée.</li>"
    model_rows = "".join(
        "<tr>"
        f"<td>{esc(metric.candidate_id)}</td><td>{esc(metric.model.value)}</td>"
        f"<td>{esc(metric.regime.value)}</td><td>{esc(metric.calibration_status)}</td>"
        f"<td>{esc(metric.convergence_status)}</td>"
        f"<td>{metric.expected_pnl_usd:.2f}</td><td>{metric.standard_error_usd:.2f}</td>"
        f"<td>{metric.probability_profit:.1%}</td>"
        f"<td>{metric.probability_total_loss:.1%}</td>"
        f"<td>{metric.probability_x2:.1%}/{metric.probability_x3:.1%}/"
        f"{metric.probability_x5:.1%}</td>"
        f"<td>{metric.var_95_usd:.2f}/{metric.cvar_95_usd:.2f}</td>"
        "</tr>"
        for metric in report.model_metrics
    )
    robustness_rows = "".join(
        "<tr>"
        f"<td>{esc(item.candidate_id)}</td><td>{esc(item.verdict.value)}</td>"
        f"<td>{item.robustness_score:.1f}</td>"
        f"<td>{item.probability_profit_dispersion:.1%}</td>"
        f"<td>{item.expected_pnl_dispersion_usd:.2f}</td>"
        f"<td>{item.cvar_dispersion_usd:.2f}</td>"
        f"<td>{item.invalid_model_count}</td>"
        "</tr>"
        for item in report.robustness
    )
    stress_rows = "".join(
        "<tr>"
        f"<td>{esc(item.candidate_id)}</td><td>{esc(item.stress_id)}</td>"
        f"<td>{esc(item.status)}</td>"
        f"<td>{'n/a' if item.stressed_pnl_usd is None else f'{item.stressed_pnl_usd:.2f}'}</td>"
        f"<td>{esc(item.method)}</td>"
        "</tr>"
        for item in report.stress_tests
    )
    allocation_card_parts: list[str] = []
    for item in report.allocations:
        if item.rank > 3:
            continue
        allocation_label = (
            "cash / NO_TRADE"
            if item.no_trade
            else ", ".join(
                f"{line.strategy_units}× {line.candidate_id}" for line in item.lines
            )
        )
        allocation_card_parts.append(
            "<article>"
            f"<h3>{esc(item.profile)} · #{item.rank}</h3>"
            f"<p>{esc(allocation_label)}</p>"
            "<dl>"
            f"<div><dt>Réserve</dt><dd>{item.cash_reserve_eur:.2f} EUR</dd></div>"
            f"<div><dt>P&amp;L expérimental</dt><dd>{item.expected_pnl_eur:.2f} EUR</dd></div>"
            f"<div><dt>CVaR 95</dt><dd>{item.cvar_95_eur:.2f} EUR</dd></div>"
            "</dl>"
            f"<p>{esc(item.cash_reason)}</p>"
            f"<p><strong>Contraintes actives :</strong> "
            f"{esc(', '.join(item.active_constraints) or 'aucune proche de la borne')}</p>"
            "</article>"
        )
    allocation_cards = "".join(allocation_card_parts)
    preview_rows = "".join(
        "<tr>"
        f"<td>{esc(item.candidate_id)}</td><td>{str(item.transmit).lower()}</td>"
        f"<td>{str(item.what_if).lower()}</td><td>{esc(item.order_capability)}</td>"
        f"<td>{esc(' · '.join(item.blockers))}</td>"
        "</tr>"
        for item in report.execution_previews
    )
    exit_rows = "".join(
        "<tr>"
        f"<td>{esc(plan.candidate_id)}</td><td>{esc(rule.rule_id)}</td>"
        f"<td>{esc(rule.threshold)}</td><td>{esc(rule.suggested_action.value)}</td>"
        f"<td>{esc(', '.join(rule.required_data))}</td>"
        "</tr>"
        for plan in report.exit_plans
        for rule in plan.rules
    )
    invalidations = "".join(
        f"<li><code>{esc(plan.candidate_id)}</code> : "
        f"{esc('; '.join(plan.fundamental_invalidations) or 'aucune règle fournie')}</li>"
        for plan in report.exit_plans
    )
    readiness_rows = "".join(
        "<tr>"
        f"<td>{esc(item.feature)}</td><td><code>{esc(item.status.value)}</code></td>"
        f"<td>{str(item.implemented).lower()}</td>"
        f"<td>{esc(' · '.join(item.blockers) or '—')}</td>"
        "</tr>"
        for item in report.readiness
    )
    blockers = "".join(
        f"<li>{esc(item)}</li>" for item in report.machine_summary.blocking_reasons
    )
    limitations = "".join(f"<li>{esc(item)}</li>" for item in report.limitations)
    missing_series = esc(
        ", ".join(report.data_snapshot.missing_required_series) or "aucune"
    )
    calibration_status_html = esc(report.offline_calibration.get("status"))
    backtest_status_html = esc(report.walk_forward_backtest.get("status"))
    local_status_html = esc(report.local_volatility_calibration.status)
    arbitrage_status_html = str(
        report.local_volatility_calibration.arbitrage_free_input
    ).lower()
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>V11.1 · TTWO Offline Reliability</title>
<style>
:root{{--ink:#172019;--muted:#657064;--paper:#f5f1e8;--card:#fffdf8;
--line:#d9d2c3;--green:#235d3a;--amber:#8b5a13;--red:#8a2d2d}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.5 ui-sans-serif,system-ui,sans-serif}} main{{max-width:1320px;margin:auto;
padding:32px 20px 64px}} header{{border-bottom:2px solid var(--ink);padding-bottom:22px}}
.eyebrow{{text-transform:uppercase;letter-spacing:.14em;color:var(--green);font-weight:750;
font-size:12px}} h1{{font:700 clamp(32px,6vw,64px)/1.02 ui-serif,Georgia,serif;
margin:.2em 0}} h2{{margin-top:42px;font:700 28px/1.15 ui-serif,Georgia,serif}}
.status{{display:flex;gap:10px;flex-wrap:wrap}} .pill{{padding:6px 10px;border:1px solid
var(--line);background:var(--card);border-radius:999px}} .warn{{color:var(--amber);
font-weight:700}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
gap:14px}} article{{background:var(--card);border:1px solid var(--line);padding:18px;
border-radius:14px}} dl div{{display:flex;justify-content:space-between;border-top:1px solid
var(--line);padding:7px 0}} dt{{color:var(--muted)}} dd{{margin:0;
font-variant-numeric:tabular-nums}} .table{{overflow:auto;border:1px solid var(--line);
border-radius:12px}} table{{width:100%;border-collapse:collapse;background:var(--card)}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;
vertical-align:top}} th{{position:sticky;top:0;background:#ebe5d8}} code{{font-size:.9em}}
.blocked{{border-left:5px solid var(--red);padding-left:16px}} :focus-visible{{outline:3px
solid var(--green);outline-offset:3px}} @media(max-width:560px){{main{{padding:22px 12px 48px}}
th,td{{min-width:130px}}}}
</style>
</head>
<body><main>
<header><div class="eyebrow">V11.1 · offline · research-only · auditable</div>
<h1>Probabilistic Strategy Intelligence</h1>
<div class="status"><span class="pill">posture: {esc(report.posture.value)}</span>
<span class="pill">status: {esc(report.machine_summary.result_status.value)}</span>
<span class="pill">transmit=false</span><span class="pill">what_if=true</span>
<span class="pill warn">confirmation humaine</span></div>
<p>Run <code>{esc(report.run_manifest.run_id)}</code> · cutoff
<code>{esc(report.machine_summary.cutoff.isoformat())}</code> · schéma
<code>{esc(report.schema_version)}</code></p></header>

<section><h2>1. État des données</h2><p>Séries manquantes : <strong>{missing_series}</strong></p>
<div class="table"><table><thead><tr><th>Connecteur</th><th>Statut</th>
<th>Observations</th><th>Diagnostic</th></tr></thead><tbody>{connector_rows}</tbody></table></div>
</section>
<section><h2>2. Statut de calibration</h2>
<div class="grid"><article><h3>Calibration</h3>
<p><code>{calibration_status_html}</code></p></article>
<article><h3>Walk-forward</h3><p><code>{backtest_status_html}</code></p></article>
<article><h3>Local volatility</h3><p><code>{local_status_html}</code></p>
<p>Arbitrage-free input: {arbitrage_status_html}</p></article></div>
</section>
<section><h2>3. Probabilités initiales et postérieures</h2>
<div class="table"><table><thead><tr><th>Scénario</th><th>Central</th><th>Minimum</th>
<th>Maximum</th></tr></thead><tbody>{posterior_rows}</tbody></table></div></section>
<section><h2>4. Provenance des événements</h2><div class="table"><table>
<thead><tr><th>Type</th><th>Famille</th><th>Règle</th><th>Revue</th><th>Sources</th></tr></thead>
<tbody>{event_rows}</tbody></table></div></section>
<section><h2>5. Contradictions</h2><ul>{contradiction_rows}</ul></section>
<section><h2>6–11. Modèles, distribution du P&amp;L, probabilités et VaR/CVaR</h2>
<div class="table"><table><thead><tr><th>Candidat</th><th>Modèle</th><th>Régime</th>
<th>Calibration</th><th>Convergence</th><th>P&amp;L moyen</th><th>Erreur standard</th>
<th>P(profit)</th><th>P(perte totale)</th><th>x2/x3/x5</th><th>VaR/CVaR</th></tr></thead>
<tbody>{model_rows}</tbody></table></div></section>
<section><h2>12. Robustesse et désaccord entre modèles</h2><div class="table"><table>
<thead><tr><th>Candidat</th><th>Verdict</th><th>Score</th><th>Dispersion P(profit)</th>
<th>Dispersion P&amp;L</th><th>Dispersion CVaR</th><th>Invalides</th></tr></thead>
<tbody>{robustness_rows}</tbody></table></div></section>
<section><h2>13. Stress tests</h2><div class="table"><table><thead><tr><th>Candidat</th>
<th>Stress</th><th>Statut</th><th>P&amp;L</th><th>Méthode</th></tr></thead>
<tbody>{stress_rows}</tbody></table></div></section>
<section><h2>14–15. Allocation et cash non utilisé</h2><div class="grid">{allocation_cards}</div>
</section>
<section><h2>16. Risques d'exécution</h2><div class="table"><table><thead><tr>
<th>Candidat</th><th>Transmit</th><th>What-if</th><th>Capability</th><th>Blockers</th>
</tr></thead><tbody>{preview_rows}</tbody></table></div></section>
<section><h2>17. Règles de sortie</h2><div class="table"><table><thead><tr><th>Candidat</th>
<th>Règle</th><th>Seuil</th><th>Action suggérée</th><th>Données</th></tr></thead>
<tbody>{exit_rows}</tbody></table></div></section>
<section><h2>18. Conditions d'invalidation</h2><ul>{invalidations}</ul></section>
<section><h2>19. Readiness status</h2><div class="table"><table><thead><tr><th>Fonction</th>
<th>Statut</th><th>Implémentée</th><th>Blockers</th></tr></thead>
<tbody>{readiness_rows}</tbody></table></div></section>
<section class="blocked"><h2>20. Raisons de NO_TRADE ou blocage</h2><ul>{blockers}</ul></section>
<section><h2>Exports, versions et reproductibilité</h2>
<p>Exports générés : JSON strict, Markdown et HTML autonome. Aucun calcul financier n'est
effectué en JavaScript ; ce fichier ne contient aucun JavaScript et aucune requête réseau.</p>
<ul><li>Configuration : <code>{esc(report.run_manifest.configuration_hash)}</code></li>
<li>Données : <code>{esc(report.run_manifest.data_hash)}</code></li>
<li>Input : <code>{esc(report.run_manifest.input_hash)}</code></li>
<li>Versions : <code>{esc(report.run_manifest.model_versions)}</code></li></ul></section>
<section><h2>Limites</h2><ul>{limitations}</ul></section>
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
