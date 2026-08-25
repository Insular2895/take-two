"""JSON, Markdown, and standalone HTML reporting for the V10.1 scanner."""

# ruff: noqa: E501

from __future__ import annotations

from pathlib import Path

from take_two_options.thesis_scanner.schemas import ThesisScanReport


def markdown_report(report: ThesisScanReport) -> str:
    candidate_by_id = {candidate.candidate_id: candidate for candidate in report.candidates}
    lines = [
        "# V10.1 Bullish Thesis Scanner",
        "",
        f"- Statut global : `{report.overall_status.value}`",
        f"- Ticker / direction : `{report.request.ticker}` / bullish",
        f"- Spot de référence : `${report.chain.spot:.2f}` au "
        f"`{report.chain.spot_timestamp.isoformat()}`",
        f"- Budget : `€{report.request.budget_eur:,.2f}` ; perte maximale : "
        f"`€{report.request.max_loss_eur:,.2f}`",
        f"- Catalyseur : `{report.request.catalyst_date.isoformat()}` + "
        f"`{report.request.expiration_buffer_days}` jours",
        f"- Probabilités : `{report.probability_status}`",
        f"- Capacité d'ordre : `{report.order_capability}`",
        "",
        "> Recherche en lecture seule. Les candidats sont des constructions "
        "synthétiques à contrôler dans IBKR, pas des recommandations.",
        "",
        f"## Meilleures stratégies — Top {report.request.top} par profil",
        "",
    ]
    for ranking in report.rankings:
        lines.extend([f"### {ranking.profile.value.title()}", ""])
        if not ranking.scores:
            lines.extend(["Aucun candidat classable.", ""])
            continue
        lines.extend(
            [
                "| Rang | Candidat | Structure | Score | Coût EUR | Perte max EUR | "
                "Meilleur gain modélisé EUR | Break-even | Statut |",
                "|---:|---|---|---:|---:|---:|---:|---|---|",
            ]
        )
        for index, score in enumerate(ranking.scores, start=1):
            candidate = candidate_by_id[score.candidate_id]
            lines.append(
                f"| {index} | `{score.candidate_id}` | {candidate.display_name} | "
                f"{score.score:.2f} | €{candidate.execution.total_cost_eur:,.2f} | "
                f"€{candidate.maximum_loss_eur:,.2f} | "
                f"€{candidate.decision_metrics.best_modeled_gain_eur:,.2f} | "
                f"`{candidate.base_candidate.risk.break_even_points}` | "
                f"`{candidate.status.value}` |"
            )
        lines.append("")

    lines.extend(
        [
            "## Filtrage auditable",
            "",
            f"- Quotes reçues : `{report.quote_rejections.total_quotes}`",
            f"- Calls utilisables : `{report.quote_rejections.usable_calls}`",
            f"- Combinaisons générées : `{report.generated_candidates}`",
            f"- Candidats techniquement admissibles : `{report.technically_admissible_candidates}`",
            "",
            "| Motif | Nombre |",
            "|---|---:|",
        ]
    )
    combined_reasons = {
        **report.quote_rejections.reasons,
        **{
            reason: report.quote_rejections.reasons.get(reason, 0) + count
            for reason, count in report.blocked_reasons.items()
        },
    }
    for reason, count in sorted(combined_reasons.items()):
        lines.append(f"| `{reason}` | {count} |")
    if not combined_reasons:
        lines.append("| Aucun rejet | 0 |")

    selected_ids = {score.candidate_id for ranking in report.rankings for score in ranking.scores}
    for candidate_id in sorted(selected_ids):
        candidate = candidate_by_id[candidate_id]
        metrics = candidate.decision_metrics
        lines.extend(
            [
                "",
                f"## {candidate.display_name}",
                "",
                f"- ID : `{candidate.candidate_id}`",
                f"- Architecture : `{candidate.architecture.value}` ; maturité : "
                f"`{candidate.maturity_class}` ; DTE : `{candidate.dte}`",
                f"- Combo : mid `${candidate.execution.theoretical_mid_debit_usd:,.2f}` / "
                f"`€{candidate.execution.theoretical_mid_debit_eur:,.2f}` ; "
                f"débit prudent `${candidate.execution.conservative_debit_usd:,.2f}` / "
                f"`€{candidate.execution.conservative_debit_eur:,.2f}`",
                f"- Slippage / commissions : `${candidate.execution.slippage_usd:,.2f}` / "
                f"`${candidate.execution.commissions_usd:,.2f}` ; "
                f"`€{candidate.execution.slippage_eur:,.2f}` / "
                f"`€{candidate.execution.commissions_eur:,.2f}`",
                f"- Coût total : `${candidate.execution.total_cost_usd:,.2f}` / "
                f"`€{candidate.execution.total_cost_eur:,.2f}`",
                f"- FX : `{candidate.execution.fx_rate:.6f} USD/EUR`, "
                f"`{candidate.execution.fx_rate_date}`, "
                f"{candidate.execution.fx_rate_source}",
                f"- Perte max : `${candidate.base_candidate.risk.maximum_loss:,.2f}` / "
                f"`€{candidate.maximum_loss_eur:,.2f}` ; "
                f"`{metrics.loss_budget_fraction:.2%}` du budget",
                f"- Gain maximal contractuel : "
                f"`{metrics.contractual_max_gain_usd if metrics.contractual_max_gain_usd is not None else 'Illimité théorique'}`",
                f"- Meilleur gain parmi les scénarios modélisés : "
                f"`${metrics.best_modeled_gain_usd:,.2f}` / "
                f"`€{metrics.best_modeled_gain_eur:,.2f}`",
                f"- Ratio gain/perte contractuel : "
                f"`{metrics.contractual_gain_loss_ratio if metrics.contractual_gain_loss_ratio is not None else 'non borné'}` ; "
                f"ratio modélisé : `{metrics.modeled_gain_loss_ratio:.4f}`",
                f"- Break-even : `{candidate.base_candidate.risk.break_even_points}`",
                f"- {metrics.lose_if}",
                f"- {metrics.win_if}",
                f"- Greeks nets : delta `{candidate.net_greeks.delta:.3f}`, "
                f"gamma `{candidate.net_greeks.gamma:.3f}`, "
                f"theta `{candidate.net_greeks.theta:.3f}`, "
                f"vega `{candidate.net_greeks.vega:.3f}`",
                "",
                "### Jambes et cotations",
                "",
                "| Action | Quantité | OCC | Strike | Bid | Ask | Mid | Multiplicateur |",
                "|---|---:|---|---:|---:|---:|---:|---:|",
                *[
                    (
                        f"| {'ACHETER' if leg.side.value == 'long' else 'VENDRE'} | "
                        f"{leg.quantity} | `{leg.quote.symbol}` | {leg.quote.strike:g} | "
                        f"${leg.quote.bid:,.2f} | ${leg.quote.ask:,.2f} | "
                        f"${((leg.quote.bid + leg.quote.ask) / 2):,.2f} | "
                        f"{leg.quote.multiplier} |"
                    )
                    for leg in candidate.base_candidate.legs
                ],
                "",
                "### Seuils de performance à l'échéance",
                "",
            ]
        )
        lines.append(
            "> ×2 la mise = valeur finale égale à deux fois le coût total initial, "
            "soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie "
            "n'est ajouté."
        )
        for threshold in metrics.terminal_value_thresholds:
            lines.append(f"- ×{threshold.multiple} : {threshold.message}")
        lines.extend(
            [
                "",
                "### P&L aux objectifs",
                "",
                "| Spot | Catalyseur IV down | Catalyseur IV stable | "
                "Catalyseur IV up | Échéance |",
                "|---:|---:|---:|---:|---:|",
            ]
        )
        for row in metrics.target_pnl_rows:
            lines.append(
                f"| ${row.spot:,.2f} | ${row.catalyst_iv_down_usd:,.2f} / "
                f"€{row.catalyst_iv_down_eur:,.2f} | "
                f"${row.catalyst_iv_stable_usd:,.2f} / "
                f"€{row.catalyst_iv_stable_eur:,.2f} | "
                f"${row.catalyst_iv_up_usd:,.2f} / €{row.catalyst_iv_up_eur:,.2f} | "
                f"${row.expiration_usd:,.2f} / €{row.expiration_eur:,.2f} |"
            )
        if report.probability_status == "user_supplied":
            lines.extend(
                [
                    "",
                    f"P&L espéré conditionnel aux probabilités utilisateur : "
                    f"`${candidate.expected_pnl_usd:,.2f}` / "
                    f"`€{metrics.expected_pnl_eur:,.2f}` ; "
                    f"probabilité de résultat positif : "
                    f"`{candidate.probability_success:.2%}`.",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "Aucun P&L espéré ni probabilité de succès n'est calculé : "
                    "aucune probabilité utilisateur n'a été fournie.",
                ]
            )
        lines.extend(
            [
                "",
                "### Alertes",
                "",
                *([f"- `{warning}`" for warning in candidate.warnings] or ["- Aucune"]),
                "",
                "### Preview IBKR",
                "",
            ]
        )
        ticket = next(item for item in report.ibkr_previews if item.candidate_id == candidate_id)
        lines.extend(
            [
                f"- Type / ordre : `{ticket.security_type}` / `{ticket.order_type}` ; "
                f"`mode={ticket.mode}` ; `transmit={str(ticket.transmit).lower()}` ; "
                f"`what_if={str(ticket.what_if).lower()}`",
                f"- Débit maximum indicatif : `${ticket.debit_max_per_share_usd:.2f}` "
                "par action de combo",
                f"- Coût indicatif par lot : "
                f"`${ticket.indicative_cost_per_lot_usd:,.2f}` / "
                f"`€{ticket.indicative_cost_eur:,.2f}`",
                f"- Date de la quote : `{ticket.quote_date.isoformat()}`",
                f"- Message : {ticket.message}",
            ]
        )
        for leg in ticket.legs:
            lines.append(
                f"- {leg.action} `{leg.quantity}` × `{leg.occ_symbol}` "
                f"CALL {leg.strike:g} {leg.expiration.isoformat()} SMART"
            )

    lines.extend(
        [
            "",
            "## Historique de backtest — séparé de la simulation actuelle",
            "",
            f"- Statut : `{report.historical_evidence.status}`",
            f"- Effet sur l'éligibilité : `{report.historical_evidence.eligibility_effect}`",
            f"- Confiance : `{report.historical_evidence.confidence:.2f}`",
            f"- {report.historical_evidence.summary}",
            *[
                f"- Limite historique : {value}"
                for value in report.historical_evidence.limitations
            ],
            *[
                f"- Artefact : `{value}`"
                for value in report.historical_evidence.source_artifacts
            ],
            "",
            "## Limites et hypothèses actuelles",
            "",
            f"- {report.historical_warning}",
            *[f"- {value}" for value in report.limitations],
            *[f"- Hypothèse : {value}" for value in report.assumptions],
            "",
            "## Sources",
            "",
            *[f"- {source}" for source in report.data_sources],
            "",
        ]
    )
    return "\n".join(lines)


def html_dashboard(report: ThesisScanReport) -> str:
    payload = report.model_dump_json().replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>V10.1 Bullish Thesis Scanner · {report.request.ticker}</title>
<style>
:root{{--bg:#071014;--panel:#101b21;--panel2:#15242b;--line:#29404a;--text:#eef7f5;
--muted:#9ab0b3;--green:#2ee6a6;--red:#ff6b7a;--amber:#ffcb66;--blue:#68a7ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}
main{{max-width:1500px;margin:auto;padding:24px}} header{{display:flex;gap:20px;justify-content:
space-between;align-items:flex-start;margin:12px 0 28px}} h1{{font-size:clamp(28px,4vw,52px);
line-height:1;margin:8px 0}} h2{{font-size:20px;margin:0 0 16px}} h3{{margin:0 0 8px}}
.eyebrow{{color:var(--green);letter-spacing:.16em;text-transform:uppercase;font-weight:800}}
.muted{{color:var(--muted)}} .chips{{display:flex;gap:8px;flex-wrap:wrap}} .chip{{padding:6px 10px;
border:1px solid var(--line);border-radius:999px;background:#0d181d}} .status{{color:var(--amber)}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .card,.section{{border:1px solid
var(--line);background:var(--panel);
border-radius:16px;padding:18px;box-shadow:0 18px 50px #0004;min-width:0;
overflow-wrap:anywhere}} .profile{{position:relative;
overflow:hidden}} .profile:before{{content:"";position:absolute;inset:0 auto 0 0;width:4px;
background:var(--green)}} .metric{{font-size:24px;font-weight:800}} .section{{margin-top:14px}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .metricbox{{background:#0b151a;
border-radius:11px;padding:12px}} table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;
padding:9px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--muted);
font-size:12px;text-transform:uppercase;letter-spacing:.05em}} .scroll{{overflow:auto}}
.vizgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .chart{{min-height:270px}}
svg{{width:100%;height:245px;overflow:visible}} .axis{{stroke:#46606a;stroke-width:1}}
.profit{{stroke:var(--green);fill:none;stroke-width:3}} .loss{{stroke:var(--red);fill:none;
stroke-width:3}} .bar{{fill:var(--blue)}} .zero{{stroke:var(--amber);stroke-dasharray:4 4}}
.heat{{display:grid;gap:3px;min-width:580px}} .heat div{{padding:7px;text-align:center;border-radius:5px;
font-variant-numeric:tabular-nums}} select{{background:#0b151a;color:var(--text);border:1px solid
var(--line);border-radius:8px;padding:8px;max-width:100%}} .warn{{color:var(--amber)}}
.buy{{color:var(--green)}} .sell{{color:var(--red)}} code{{color:#bce8dc}}
.profiledata{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:14px 0}}
.profiledata div,.compactbox{{background:#0b151a;border-radius:8px;padding:8px}}
.profiledata span,.label{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;
letter-spacing:.04em}} .profiledata strong{{font-size:14px}} .detailgrid{{display:grid;
grid-template-columns:1fr 1fr;gap:14px}} .list{{margin:0;padding-left:18px}} .list li{{margin:6px 0}}
.detailgrid>*,.vizgrid>*{{min-width:0}}
.advantage{{color:var(--green)}} .risk{{color:var(--amber)}} .smallmetric{{font-size:16px;
font-weight:750;word-break:break-word}} .legend{{display:flex;gap:14px;flex-wrap:wrap;
margin:6px 0;color:var(--muted)}} .swatch{{display:inline-block;width:10px;height:10px;
border-radius:2px;margin-right:5px}}
.ticket{{border-left:3px solid var(--amber);padding-left:14px;margin:14px 0}} footer{{margin:26px 0;
color:var(--muted)}} .profile-columns{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));
gap:14px}} .profile-column{{min-width:0}} .profile-heading{{display:flex;align-items:center;
justify-content:space-between;gap:10px;margin-bottom:10px}} .accordion-item{{border:1px solid
var(--line);border-radius:12px;background:#0b151a;margin:8px 0;overflow:hidden}}
.accordion-trigger{{width:100%;border:0;background:transparent;color:var(--text);padding:12px;
text-align:left;cursor:pointer}} .accordion-trigger:hover{{background:#13242b}}
.accordion-trigger:focus-visible,select:focus-visible,button:focus-visible{{outline:3px solid
var(--blue);outline-offset:2px}} .accordion-trigger[aria-expanded="true"]{{background:#173038}}
.accordion-trigger.active{{box-shadow:inset 4px 0 var(--green)}} .accordion-summary{{display:grid;
grid-template-columns:auto 1fr auto;gap:8px;align-items:center}} .rank{{display:grid;place-items:center;
width:28px;height:28px;border-radius:50%;background:#20343d;color:var(--green);font-weight:800}}
.accordion-title{{font-weight:800}} .accordion-score{{font-variant-numeric:tabular-nums;
color:var(--green);font-weight:800}} .accordion-facts{{display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 10px;margin-top:8px;color:var(--muted);
font-size:12px}} .accordion-panel{{border-top:1px solid var(--line);padding:12px}}
.accordion-panel[hidden]{{display:none}} .decision-sheet{{display:grid;grid-template-columns:
repeat(2,minmax(0,1fr));gap:10px}} .decision-part{{background:#0d1a20;border:1px solid #20343d;
border-radius:11px;padding:12px}} .decision-part h4{{margin:0 0 9px;color:var(--green);
font-size:13px;text-transform:uppercase;letter-spacing:.06em}} .decision-part p{{margin:6px 0}}
.active-banner{{border-left:4px solid var(--green);padding:10px 12px;background:#0d1a20;
margin-bottom:12px}} .convention{{padding:10px;border-radius:8px;background:#17252b;
color:var(--muted)}} .currency-control{{display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.currency-control button{{border:1px solid var(--line);background:#0b151a;color:var(--text);
padding:7px 12px;border-radius:8px;cursor:pointer}} .currency-control button[aria-pressed="true"]{{
background:var(--green);color:#04100d;border-color:var(--green)}} .risk-grid{{display:grid;
grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}} .risk-indicator{{background:#0b151a;
border-radius:9px;padding:9px}} .risk-indicator strong{{display:block;margin-top:3px}}
.research-warning{{border:1px solid var(--amber);border-radius:9px;padding:10px;color:var(--amber);
margin:10px 0;grid-column:1/-1}} @media(max-width:1050px){{.profile-columns{{grid-template-columns:1fr}}}}
@media(max-width:900px){{.grid3,.vizgrid,.metrics{{grid-template-columns:1fr}}
header{{display:block}} main{{padding:14px}} .detailgrid,.profiledata,.decision-sheet,
.risk-grid{{grid-template-columns:1fr}} .accordion-facts{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<main>
<header><div><div class="eyebrow">Read-only · V10.1</div><h1>Bullish Thesis Scanner</h1>
<div class="muted" id="subtitle"></div></div><div class="chips" id="headerChips"></div></header>
<section class="section"><h2>Contexte de marché et hypothèses utilisateur</h2>
<div class="metrics" id="marketContext"></div><div id="freshnessWarnings"></div></section>
<section class="section" aria-labelledby="top-title"><h2 id="top-title">
Meilleures stratégies — <span id="topCount"></span> par profil</h2>
<p class="muted">Classements indépendants et déterministes. Ouvrir une ligne met à jour toute
l’analyse détaillée; une même structure peut apparaître dans plusieurs profils.</p>
<div class="profile-columns" id="profileAccordions"></div></section>
<section class="section"><h2>Univers et contrôles</h2><div class="metrics" id="universe"></div>
<div class="scroll"><table><thead><tr><th>Motif explicite</th><th>Nombre</th></tr></thead>
<tbody id="rejections"></tbody></table></div></section>
<section class="section"><h2>Comparaison visuelle des profils</h2>
<div class="legend"><span><i class="swatch" style="background:#68a7ff"></i>Coût EUR</span>
<span><i class="swatch" style="background:#ff6b7a"></i>Perte maximale EUR</span>
<span><i class="swatch" style="background:#2ee6a6"></i>Gain potentiel modélisé EUR</span></div>
<svg id="profileChart" role="img"
aria-label="Coût, perte maximale et gain potentiel des premiers candidats par profil"></svg>
<div class="scroll">
<table><thead><tr><th>Profil</th><th>Rang</th><th>Candidat</th><th>Score</th><th>Perte max</th>
<th>Coût EUR</th><th>Gain potentiel</th><th>Statut</th></tr></thead>
<tbody id="comparison"></tbody></table></div></section>
<section class="section"><h2>Tous les candidats <span class="muted">— secondaire</span></h2>
<label for="candidate">Candidat actif </label>
<select id="candidate"></select><div class="metrics" id="candidateMetrics"></div></section>
<section class="section"><h2>Fiche décisionnelle active</h2>
<div id="activeCandidateBanner" class="active-banner" aria-live="polite"></div>
<div id="activeDecision"></div></section>
<section class="section"><h2>1–2. Jambes exactes et cotations bid/ask</h2>
<div class="scroll"><table><thead><tr><th>Action</th><th>Quantité</th><th>OCC</th><th>Strike</th>
<th>Bid</th><th>Ask</th><th>Mid</th><th>OI</th><th>Volume</th><th>Multiplicateur</th></tr></thead>
<tbody id="legs"></tbody></table></div></section>
<div class="detailgrid">
<section class="section"><h2>3–4. Ticket IBKR et coûts</h2><div id="selectedTicket"></div>
<div class="metrics" id="costs"></div></section>
<section class="section"><h2>5. Greeks nets</h2><div class="metrics" id="greeks"></div></section>
</div>
<div class="detailgrid">
<section class="section"><h2>6. Liquidité</h2><div class="scroll"><table><thead><tr>
<th>Jambe</th><th>Spread relatif</th><th>OI</th><th>Volume</th><th>Qualité</th></tr></thead>
<tbody id="liquidity"></tbody></table></div></section>
<section class="section"><h2>7. Hypothèses utilisées</h2><div id="assumptions"></div></section>
</div>
<div class="detailgrid">
<section class="section"><h2>8. Raisons de sélection</h2><div id="selectionReasons"></div>
<div class="scroll"><table><thead><tr><th>Profil</th><th>Score</th><th>Critères normalisés</th></tr>
</thead><tbody id="criteria"></tbody></table></div></section>
<section class="section"><h2>9. Risques de la structure</h2>
<div id="candidateRisks"></div></section>
</div>
<section class="section"><div class="profile-heading"><h2>Tableau de P&amp;L aux objectifs</h2>
<div class="currency-control" role="group" aria-label="Devise du tableau P et L">
<span>Devise</span><button type="button" id="currencyUSD" aria-pressed="true">USD</button>
<button type="button" id="currencyEUR" aria-pressed="false">EUR</button></div></div>
<p class="muted">Valeurs au catalyseur sous trois hypothèses d’IV, puis payoff exact à
l’échéance. Les scénarios viennent du moteur Python.</p>
<div class="scroll"><table><thead><tr><th>Cours TTWO</th><th>P&amp;L catalyseur IV down</th>
<th>P&amp;L IV stable</th><th>P&amp;L IV up</th><th>P&amp;L à expiration</th></tr></thead>
<tbody id="targetPnl"></tbody></table></div></section>
<div class="vizgrid">
<section class="section chart"><h2>Payoff terminal</h2><svg id="payoff" role="img"></svg></section>
<section class="section chart"><h2>Courbes de P&amp;L à plusieurs dates · IV stable</h2>
<svg id="dates" role="img" aria-label="Courbes de P et L par spot pour plusieurs dates"></svg></section>
</div>
<section class="section"><h2>Heatmap spot × date · IV stable</h2><div class="scroll">
<div id="heatmap" class="heat"></div></div></section>
<div class="vizgrid">
<section class="section"><h2>Sensibilité IV au catalyseur</h2>
<svg id="iv" role="img" aria-label="Comparaison du P et L sous IV en baisse, stable et en hausse"></svg></section>
<section class="section"><h2>Scénarios compacts</h2><div class="scroll"><table><thead>
<tr><th>Objectif</th><th>IV down</th><th>IV stable</th><th>IV up</th></tr></thead>
<tbody id="scenarios"></tbody></table></div></section>
</div>
<section class="section"><h2>Attribution et Greeks nets</h2><div id="attribution"></div></section>
<section class="section"><h2>10. Historique de backtest — séparé de la simulation actuelle</h2>
<div id="history"></div></section>
<section class="section"><h2>Limites, provenance et sécurité</h2><div id="limits"></div></section>
<footer>Rapport local autonome. Aucune requête réseau, aucun bouton d'achat, aucune capacité d'ordre.</footer>
</main>
<script type="application/json" id="report">{payload}</script>
<script>
"use strict";
const R=JSON.parse(document.getElementById("report").textContent);
const byId=Object.fromEntries(R.candidates.map(c=>[c.candidate_id,c]));
const ticketById=Object.fromEntries(R.ibkr_previews.map(t=>[t.candidate_id,t]));
const $=id=>document.getElementById(id);
const E=(tag,text,cls)=>{{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);
if(cls)n.className=cls;return n}};
const money=(v,c="$")=>c+Number(v).toLocaleString("fr-FR",{{maximumFractionDigits:2,minimumFractionDigits:2}});
const pct=v=>(100*Number(v)).toFixed(1)+"%";
const chip=t=>{{const n=E("span",t,"chip");$("headerChips").append(n)}};
const maxGainLabel=c=>c.decision_metrics.contractual_gain_unbounded?"Illimité théorique":
money(c.decision_metrics.contractual_max_gain_usd)+" / "+money(c.decision_metrics.contractual_max_gain_eur,"€");
const breakEven=c=>c.base_candidate.risk.break_even_points.length?
c.base_candidate.risk.break_even_points.map(x=>"$"+Number(x).toFixed(2)).join(" / "):"—";
const ratio=v=>v===null?"Non borné":Number(v).toFixed(2)+"×";
const yesNo=v=>v?"Oui":"Non";
const ageLabel=s=>s<3600?Math.round(s/60)+" min":s<86400?(s/3600).toFixed(1)+" h":(s/86400).toFixed(1)+" j";
const appendList=(parent,items,cls)=>{{parent.replaceChildren();const ul=E("ul",undefined,"list");
(items.length?items:["Aucun"]).forEach(x=>ul.append(E("li",x,cls)));parent.append(ul)}};
document.querySelectorAll(".scroll").forEach(node=>{{node.tabIndex=0}});
function decisionPart(title,rows){{const part=E("section",undefined,"decision-part");part.append(E("h4",title));
rows.forEach(([label,value,cls])=>{{const p=E("p",undefined,cls);p.append(E("span",label+" · ","muted"),E("strong",value));part.append(p)}});
return part}}
function decisionSheet(c){{const d=c.decision_metrics,sheet=E("div",undefined,"decision-sheet");
const riskRows=[
["Coût total",money(c.execution.total_cost_usd)+" / "+money(c.execution.total_cost_eur,"€")],
["Perte maximale",money(c.base_candidate.risk.maximum_loss)+" / "+money(c.maximum_loss_eur,"€")],
["Part du budget exposée",pct(d.loss_budget_fraction)],
["Part de la mise pouvant être perdue",pct(d.stake_loss_fraction)],
["Expiration / DTE",c.expiration+" / "+c.dte+" j"],
["Contrats / unités de stratégie",d.total_option_contracts+" / "+d.strategy_units],
["Tu perds si…",d.lose_if,"risk"]];
const gainRows=[
["Gain maximal contractuel",maxGainLabel(c)],
["Meilleur gain parmi les scénarios modélisés",money(d.best_modeled_gain_usd)+" / "+money(d.best_modeled_gain_eur,"€")],
["Ratio gain/perte contractuel",ratio(d.contractual_gain_loss_ratio)],
["Ratio gain/perte modélisé",Number(d.modeled_gain_loss_ratio).toFixed(2)+"×"]];
if(d.expected_pnl_eur!==null)gainRows.push(["P&L espéré conditionnel",money(c.expected_pnl_usd)+" / "+money(d.expected_pnl_eur,"€")]);
gainRows.push(["Tu gagnes si…",d.win_if,"advantage"]);
if(d.strike_width!==null)gainRows.push(["Largeur des strikes",money(d.strike_width)]);
if(d.capped_gain_from_spot!==null)gainRows.push(["Gain plafonné à partir de",money(d.capped_gain_from_spot)]);
if(d.butterfly_center_strike!==null)gainRows.push(["Strike central / gain maximal",money(d.butterfly_center_strike)]);
if(d.profit_zone.length)gainRows.push(["Zone de profit",d.profit_zone.map(x=>"$"+Number(x).toFixed(2)).join(" – ")]);
const thresholdRows=d.terminal_value_thresholds.map(t=>["×"+t.multiple,t.message,t.attainable?"advantage":"risk"]);
thresholdRows.unshift(["Convention","×2 la mise = valeur finale égale à deux fois le coût total initial, soit un bénéfice net égal à une fois la mise. Aucun nouveau frais de sortie n’est ajouté."]);
const dataRows=[
["Spot TTWO",money(R.chain.spot)],
["Cotation",d.quote_timestamp+" · âge "+ageLabel(d.quote_age_seconds)],
["Source",d.source_ids.join(" · ")],
["Qualité",d.data_qualities.join(" · ")],
["Spread relatif maximal",pct(d.maximum_leg_relative_spread)],
["Open interest minimal",d.minimum_open_interest??"indisponible"],
["Volume minimal",d.minimum_volume??"indisponible"],
["Frais / slippage",money(c.execution.commissions_usd)+" / "+money(c.execution.slippage_usd)],
["FX",c.execution.fx_rate+" USD/EUR · "+c.execution.fx_rate_date]];
sheet.append(decisionPart("Mise et risque",riskRows),decisionPart("Gains",gainRows),
decisionPart("Seuils de performance",thresholdRows),decisionPart("Données et qualité d’exécution",dataRows));
if(d.research_estimate_warning){{const warning=E("p",d.research_estimate_warning,"research-warning");sheet.append(warning)}}
return sheet}}
$("subtitle").textContent=`${{R.request.ticker}} · spot $${{R.chain.spot.toFixed(2)}} · données ${{R.chain.as_of}} · qualité ${{R.chain.price_quality}}`;
chip(R.overall_status);chip("source: "+R.chain.price_quality);chip("budget "+money(R.request.budget_eur,"€"));
chip("perte max "+money(R.request.max_loss_eur,"€"));chip("order: forbidden");
function field(parent,label,value){{const b=E("div",undefined,"metricbox");b.append(E("div",label,"muted"),
E("div",value,"metric"));parent.append(b)}}
function compactField(parent,label,value){{const b=E("div",undefined,"compactbox");b.append(E("span",label,"label"),
E("strong",value,"smallmetric"));parent.append(b)}}
const expirations=[...new Set(R.candidates.map(c=>c.expiration))].sort();
compactField($("marketContext"),"Ticker / spot",R.request.ticker+" / "+money(R.chain.spot));
compactField($("marketContext"),"Date et heure des données",R.chain.as_of);
compactField($("marketContext"),"Qualité / source",R.chain.price_quality+" / "+R.chain.source_id);
compactField($("marketContext"),"Budget / perte autorisée",money(R.request.budget_eur,"€")+" / "+money(R.request.max_loss_eur,"€"));
compactField($("marketContext"),"Catalyseur + buffer",R.request.catalyst_date+" + "+R.request.expiration_buffer_days+" j");
compactField($("marketContext"),"Échéances étudiées",expirations.join(", ")||"Aucune");
compactField($("marketContext"),"Scénarios de prix",R.request.target_prices.map(x=>"$"+x).join(", "));
compactField($("marketContext"),"Probabilités",R.probability_status);
const freshness=[...R.chain.warnings];
if(R.quote_rejections.reasons.QUOTE_STALE)freshness.push(R.quote_rejections.reasons.QUOTE_STALE+" quote(s) périmée(s) rejetée(s)");
appendList($("freshnessWarnings"),freshness,"warn");
const profileNames={{prudent:"PRUDENT",balanced:"ÉQUILIBRÉ",aggressive:"AGRESSIF"}};
$("topCount").textContent="Top "+R.request.top;
function buildAccordions(){{const triggers=[];$("profileAccordions").replaceChildren();
R.rankings.forEach(ranking=>{{const column=E("section",undefined,"profile-column card");
const heading=E("div",undefined,"profile-heading");heading.append(E("h3",profileNames[ranking.profile]),
E("span",ranking.scores.length+" stratégie(s)","chip"));column.append(heading);
if(!ranking.scores.length)column.append(E("p","Aucun candidat classable; aucun filtre n’a été relâché.","muted"));
ranking.scores.forEach((score,index)=>{{const c=byId[score.candidate_id],item=E("div",undefined,"accordion-item"),
trigger=E("button",undefined,"accordion-trigger"),summary=E("div",undefined,"accordion-summary"),
title=E("div"),facts=E("div",undefined,"accordion-facts"),panel=E("div",undefined,"accordion-panel"),
triggerId=`accordion-${{ranking.profile}}-${{index+1}}`,panelId=triggerId+"-panel";
trigger.type="button";trigger.id=triggerId;trigger.setAttribute("aria-expanded","false");
trigger.setAttribute("aria-controls",panelId);panel.id=panelId;panel.setAttribute("role","region");
panel.setAttribute("aria-labelledby",triggerId);panel.hidden=true;
title.append(E("div",c.display_name,"accordion-title"),E("div",c.warnings[0]||c.invalidation_conditions[0],"risk"));
summary.append(E("span","#"+(index+1),"rank"),title,E("span",score.score.toFixed(2),"accordion-score"));
[["Coût",money(c.execution.total_cost_eur,"€")],["Perte max",money(c.maximum_loss_eur,"€")],
["Meilleur gain modélisé",money(c.decision_metrics.best_modeled_gain_eur,"€")],
["Break-even",breakEven(c)],["Échéance",c.expiration]].forEach(([k,v])=>facts.append(E("span",k+" · "+v)));
trigger.append(summary,facts);panel.append(decisionSheet(c));item.append(trigger,panel);column.append(item);
trigger.dataset.candidateId=c.candidate_id;trigger.dataset.profile=ranking.profile;
trigger.addEventListener("click",()=>{{const opening=trigger.getAttribute("aria-expanded")!=="true";
column.querySelectorAll(".accordion-trigger").forEach(other=>{{other.setAttribute("aria-expanded","false");
other.classList.remove("active");const target=document.getElementById(other.getAttribute("aria-controls"));target.hidden=true}});
if(opening){{trigger.setAttribute("aria-expanded","true");trigger.classList.add("active");panel.hidden=false;
selectCandidate(c.candidate_id,trigger)}}}});triggers.push(trigger)}});$("profileAccordions").append(column)}});
return triggers}}
field($("universe"),"Quotes",R.quote_rejections.total_quotes);field($("universe"),"Calls utilisables",
R.quote_rejections.usable_calls);field($("universe"),"Combinaisons",R.generated_candidates);
field($("universe"),"Admissibles",R.technically_admissible_candidates);
const reasons={{...R.quote_rejections.reasons}};Object.entries(R.blocked_reasons).forEach(([k,v])=>reasons[k]=(reasons[k]||0)+v);
Object.entries(reasons).sort().forEach(([k,v])=>{{const tr=E("tr");tr.append(E("td",k),E("td",v));$("rejections").append(tr)}});
const selected=new Set();R.rankings.forEach(rank=>rank.scores.forEach((s,i)=>{{selected.add(s.candidate_id);const c=byId[s.candidate_id],
tr=E("tr");[rank.profile,i+1,c.display_name,s.score.toFixed(2),money(c.base_candidate.risk.maximum_loss),
money(c.execution.total_cost_eur,"€"),money(c.decision_metrics.best_modeled_gain_eur,"€")+" modélisé",c.status]
.forEach(v=>tr.append(E("td",v)));$("comparison").append(tr)}}));
R.candidates.slice().sort((a,b)=>a.display_name.localeCompare(b.display_name)).forEach(c=>{{const ranked=selected.has(c.candidate_id)?" · classé":"";
const o=E("option",c.display_name+ranked);o.value=c.candidate_id;$("candidate").append(o)}});
const NS="http://www.w3.org/2000/svg";
function svg(tag,attrs={{}}){{const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,String(v)));return n}}
function profileBars(){{const node=$("profileChart"),W=600,H=210;node.setAttribute("viewBox",`0 0 ${{W}} ${{H}}`);
const rows=R.rankings.filter(r=>r.scores[0]).map(r=>{{const c=byId[r.scores[0].candidate_id];
return {{profile:r.profile,cost:c.execution.total_cost_eur,loss:c.maximum_loss_eur,gain:c.decision_metrics.best_modeled_gain_eur}}}});
const max=Math.max(1,...rows.flatMap(r=>[r.cost,r.loss,r.gain])),x0=125,scale=390/max,colors=["#68a7ff","#ff6b7a","#2ee6a6"];
rows.forEach((row,i)=>{{const y=18+i*62,label=svg("text",{{x:5,y:y+25,fill:"#eef7f5"}});
label.textContent=profileNames[row.profile];node.append(label);[row.cost,row.loss,row.gain].forEach((v,j)=>{{
const rect=svg("rect",{{x:x0,y:y+j*15,width:Math.max(v*scale,1),height:11,rx:3,fill:colors[j]}}),
value=svg("text",{{x:x0+v*scale+5,y:y+9+j*15,fill:"#eef7f5","font-size":"10"}});
value.textContent="€"+v.toFixed(0);node.append(rect,value)}})}})}}
profileBars();
function lineChart(node,points,xKey,yKey){{node.replaceChildren();if(!points.length)return;const W=600,H=220,p=28;
const xs=points.map(x=>Number(x[xKey])),ys=points.map(x=>Number(x[yKey]));let xmin=Math.min(...xs),xmax=Math.max(...xs),
ymin=Math.min(...ys,0),ymax=Math.max(...ys,0);if(xmax===xmin)xmax=xmin+1;if(ymax===ymin)ymax=ymin+1;
const X=x=>p+(x-xmin)/(xmax-xmin)*(W-2*p),Y=y=>H-p-(y-ymin)/(ymax-ymin)*(H-2*p);
node.setAttribute("viewBox",`0 0 ${{W}} ${{H}}`);node.append(svg("line",{{x1:p,y1:Y(0),x2:W-p,y2:Y(0),class:"zero"}}));
node.append(svg("line",{{x1:p,y1:p,x2:p,y2:H-p,class:"axis"}}),svg("line",{{x1:p,y1:H-p,x2:W-p,y2:H-p,class:"axis"}}));
const path=svg("path",{{d:points.map((q,i)=>`${{i?"L":"M"}} ${{X(q[xKey])}} ${{Y(q[yKey])}}`).join(" "),class:"profit"}});
const title=svg("title");title.textContent=`min ${{ymin.toFixed(2)}} max ${{ymax.toFixed(2)}}`;node.append(path,title)}}
function multiLineChart(node,series){{node.replaceChildren();const all=series.flatMap(s=>s.points);if(!all.length)return;
const W=600,H=220,p=32,xs=all.map(q=>q.spot),ys=all.map(q=>q.pnl_usd);let xmin=Math.min(...xs),xmax=Math.max(...xs),
ymin=Math.min(...ys,0),ymax=Math.max(...ys,0);if(xmax===xmin)xmax=xmin+1;if(ymax===ymin)ymax=ymin+1;
const X=x=>p+(x-xmin)/(xmax-xmin)*(W-2*p),Y=y=>H-p-(y-ymin)/(ymax-ymin)*(H-2*p),
colors=["#2ee6a6","#68a7ff","#ffcb66","#ff8f66","#c792ff","#ff6b7a"];
node.setAttribute("viewBox",`0 0 ${{W}} ${{H}}`);node.append(svg("line",{{x1:p,y1:Y(0),x2:W-p,y2:Y(0),class:"zero"}}),
svg("line",{{x1:p,y1:p,x2:p,y2:H-p,class:"axis"}}),svg("line",{{x1:p,y1:H-p,x2:W-p,y2:H-p,class:"axis"}}));
series.forEach((s,i)=>{{const color=colors[i%colors.length],path=svg("path",{{d:s.points.map((q,j)=>`${{j?"L":"M"}} ${{X(q.spot)}} ${{Y(q.pnl_usd)}}`).join(" "),
fill:"none",stroke:color,"stroke-width":"2"}}),legend=svg("text",{{x:p+(i%3)*175,y:13+Math.floor(i/3)*13,fill:color,"font-size":"9"}});
legend.textContent=s.label;node.append(path,legend)}})}}
function valueBars(node,rows){{node.replaceChildren();if(!rows.length)return;const W=600,H=220,p=50,
values=rows.map(r=>r.value),min=Math.min(0,...values),max=Math.max(0,...values),span=Math.max(max-min,1),
X=v=>p+(v-min)/span*(W-2*p),zero=X(0),colors=["#68a7ff","#ffcb66","#2ee6a6"];
node.setAttribute("viewBox",`0 0 ${{W}} ${{H}}`);node.append(svg("line",{{x1:zero,y1:15,x2:zero,y2:H-20,class:"zero"}}));
rows.forEach((row,i)=>{{const y=35+i*55,x=X(row.value),rect=svg("rect",{{x:Math.min(zero,x),y,width:Math.max(Math.abs(x-zero),1),
height:28,rx:5,fill:colors[i]}}),label=svg("text",{{x:5,y:y+19,fill:"#eef7f5","font-size":"11"}}),
value=svg("text",{{x:Math.max(zero,x)+6,y:y+19,fill:"#eef7f5","font-size":"11"}});
label.textContent=row.label;value.textContent=money(row.value);node.append(rect,label,value)}})}}
let pnlCurrency="USD";
function renderTargetPnl(c){{$("targetPnl").replaceChildren();c.decision_metrics.target_pnl_rows.forEach(row=>{{
const suffix=pnlCurrency==="USD"?"_usd":"_eur",symbol=pnlCurrency==="USD"?"$":"€",tr=E("tr");
[money(row.spot),money(row["catalyst_iv_down"+suffix],symbol),money(row["catalyst_iv_stable"+suffix],symbol),
money(row["catalyst_iv_up"+suffix],symbol),money(row["expiration"+suffix],symbol)]
.forEach(v=>tr.append(E("td",v)));$("targetPnl").append(tr)}})}}
function render(){{const c=byId[$("candidate").value],d=c.decision_metrics;$("candidateMetrics").replaceChildren();
$("activeCandidateBanner").textContent="Candidat actif · "+c.display_name+" · "+c.status;
$("activeDecision").replaceChildren(decisionSheet(c));
field($("candidateMetrics"),"Statut",c.status);
field($("candidateMetrics"),"Coût USD / EUR",money(c.execution.total_cost_usd)+" / "+money(c.execution.total_cost_eur,"€"));
field($("candidateMetrics"),"Perte maximale",money(c.base_candidate.risk.maximum_loss)+" / "+money(c.maximum_loss_eur,"€"));
field($("candidateMetrics"),"Gain maximal",maxGainLabel(c));field($("candidateMetrics"),"Break-even",breakEven(c));
field($("candidateMetrics"),"Échéance / DTE",c.expiration+" / "+c.dte+" j");
field($("candidateMetrics"),"Meilleur gain modélisé",money(d.best_modeled_gain_usd)+" / "+money(d.best_modeled_gain_eur,"€"));
field($("candidateMetrics"),"Confiance historique",pct(c.historical_confidence));
$("legs").replaceChildren();const legMetrics=Object.fromEntries(d.leg_execution.map(x=>[x.symbol,x]));
c.base_candidate.legs.forEach(l=>{{const tr=E("tr"),q=legMetrics[l.quote.symbol],
values=[l.side==="long"?"ACHETER":"VENDRE",l.quantity,l.quote.symbol,l.quote.strike,money(l.quote.bid),
money(l.quote.ask),money(q.midpoint),l.quote.open_interest??"indisponible",
l.quote.volume??"indisponible",l.quote.multiplier];values.forEach(v=>tr.append(E("td",v)));$("legs").append(tr)}});
$("costs").replaceChildren();
[["Mid théorique",money(c.execution.theoretical_mid_debit_usd)+" / "+money(c.execution.theoretical_mid_debit_eur,"€")],
["Débit prudent ask/bid",money(c.execution.conservative_debit_usd)+" / "+money(c.execution.conservative_debit_eur,"€")],
["Slippage",money(c.execution.slippage_usd)+" / "+money(c.execution.slippage_eur,"€")],
["Commissions",money(c.execution.commissions_usd)+" / "+money(c.execution.commissions_eur,"€")],
["Coût total",money(c.execution.total_cost_usd)+" / "+money(c.execution.total_cost_eur,"€")],
["Limite indicative/action",money(c.execution.indicative_limit_price_per_share)],
["FX USD/EUR",c.execution.fx_rate+" · "+c.execution.fx_rate_date],
["Source FX",c.execution.fx_rate_source]].forEach(([k,v])=>compactField($("costs"),k,v));
$("greeks").replaceChildren();[["Delta",c.net_greeks.delta],["Gamma",c.net_greeks.gamma],
["Theta/jour",c.net_greeks.theta],["Vega/point IV",c.net_greeks.vega],["Rho/point taux",c.net_greeks.rho],
["Modèle",c.net_greeks.model]].forEach(([k,v])=>compactField($("greeks"),k,typeof v==="number"?v.toFixed(4):v));
$("liquidity").replaceChildren();d.leg_execution.forEach(q=>{{const tr=E("tr");
[q.symbol,pct(q.relative_spread),q.open_interest??"indisponible",q.volume??"indisponible",
q.price_quality].forEach(v=>tr.append(E("td",v)));$("liquidity").append(tr)}});
appendList($("assumptions"),[
`IV : baisse ×${{R.policy.iv_case_multipliers.iv_down}}, stable ×${{R.policy.iv_case_multipliers.iv_stable}}, hausse ×${{R.policy.iv_case_multipliers.iv_up}}`,
`Taux sans risque ${{pct(R.policy.risk_free_rate)}} au ${{R.policy.risk_free_rate_date}} · ${{R.policy.risk_free_rate_source}}`,
`Dividende continu ${{pct(R.policy.continuous_dividend_yield)}} · ${{R.policy.dividend_source}}`,
`FX ${{R.policy.eur_usd_rate}} USD/EUR au ${{R.policy.fx_rate_date}} · ${{R.policy.fx_rate_source}}`,
`Frais ${{money(R.policy.commission_per_contract_side)}} et slippage ${{money(R.policy.slippage_per_contract_side)}} par côté`,
`Âge maximal quote ${{R.policy.maximum_quote_age_days}} jours · spread maximal ${{pct(R.policy.maximum_relative_spread)}}`,
...c.execution.notes]);
const rankedScores=R.rankings.flatMap(r=>r.scores.filter(s=>s.candidate_id===c.candidate_id));
appendList($("selectionReasons"),[...c.selection_reasons,...rankedScores.flatMap(s=>s.reasons)]);
$("criteria").replaceChildren();rankedScores.forEach(s=>{{const tr=E("tr"),
criteria=Object.entries(s.criteria).map(([k,v])=>k+"="+Number(v).toFixed(3)).join(" · ");
[s.profile,s.score.toFixed(2),criteria].forEach(v=>tr.append(E("td",v)));$("criteria").append(tr)}});
const riskBox=$("candidateRisks");riskBox.replaceChildren();
if(d.research_estimate_warning)riskBox.append(E("p",d.research_estimate_warning,"research-warning"));
const riskGrid=E("div",undefined,"risk-grid");
[["Perte totale possible de la prime",yesNo(d.total_premium_loss_possible)],
["Perte max / budget",money(c.maximum_loss_eur,"€")+" / "+pct(d.loss_budget_fraction)],
["Theta quotidien / poids de mise",money(c.net_greeks.theta)+" / "+pct(d.theta_to_stake_daily)],
["Pire impact IV down vs stable",money(d.iv_down_impact_usd)+" / "+money(d.iv_down_impact_eur,"€")],
["Vega",c.net_greeks.vega.toFixed(4)],["Spread relatif maximal",pct(d.maximum_leg_relative_spread)],
["Open interest minimal",d.minimum_open_interest??"indisponible"],["Volume minimal",d.minimum_volume??"indisponible"],
["Jambes short",yesNo(d.has_short_legs)],["Risque d’assignation",yesNo(d.assignment_risk)],
["Pin risk",yesNo(d.pin_risk)],["Risque d’IV crush",yesNo(d.iv_crush_exposure)],
["Risque de retard du catalyseur",yesNo(d.catalyst_delay_exposure)]].forEach(([k,v])=>{{
const box=E("div",undefined,"risk-indicator");box.append(E("span",k,"muted"),E("strong",v));riskGrid.append(box)}});
riskBox.append(riskGrid);const invalidations=E("div");appendList(invalidations,
[...c.warnings,...c.invalidation_conditions,...c.base_candidate.uncertainties],"risk");riskBox.append(invalidations);
renderTargetPnl(c);
const ticket=ticketById[c.candidate_id],ticketBox=$("selectedTicket");ticketBox.replaceChildren();
if(ticket){{const meta=E("div",undefined,"ticket");meta.append(E("strong",`${{ticket.security_type}} · ${{ticket.order_type}} · mode=${{ticket.mode}}`),
E("p",`transmit=${{ticket.transmit}} · what_if=${{ticket.what_if}} · confirmation humaine=${{ticket.human_confirmation_required}}`,"warn"),
E("p",`Débit maximal ${{money(ticket.debit_max_per_share_usd)}} par action · coût/lot ${{money(ticket.indicative_cost_per_lot_usd)}} · coût ${{money(ticket.indicative_cost_eur,"€")}}`),
E("p","Quote "+ticket.quote_date,"muted"));ticket.legs.forEach(l=>meta.append(E("div",
`${{l.action}} ${{l.quantity}} × CALL ${{l.occ_symbol}} · strike ${{l.strike}} · ${{l.expiration}} · ${{l.exchange}}`,
l.action==="ACHETER"?"buy":"sell")));meta.append(E("p",ticket.message,"muted"));ticketBox.append(meta)}}
const terminal=c.scenario_points.filter(p=>p.terminal&&p.iv_case==="iv_stable").sort((a,b)=>a.spot-b.spot);
lineChart($("payoff"),terminal,"spot","pnl_usd");
const target=R.request.target_prices[Math.floor(R.request.target_prices.length/2)];
const stable=c.scenario_points.filter(p=>p.iv_case==="iv_stable");
const dates=[...new Set(stable.map(p=>p.valuation_date))];
const dateSeries=dates.map(d=>({{label:d,points:stable.filter(p=>p.valuation_date===d).sort((a,b)=>a.spot-b.spot)}}));
multiLineChart($("dates"),dateSeries);
const spots=[...new Set(stable.map(p=>p.spot))];$("heatmap").replaceChildren();$("heatmap").style.gridTemplateColumns=`90px repeat(${{spots.length}},minmax(65px,1fr))`;
$("heatmap").append(E("div","Date / spot","muted"));spots.forEach(s=>$("heatmap").append(E("div","$"+s,"muted")));
dates.forEach(d=>{{$("heatmap").append(E("div",d,"muted"));spots.forEach(s=>{{const p=stable.find(x=>x.valuation_date===d&&x.spot===s),
n=E("div",p?money(p.pnl_usd):"—");if(p){{const strength=Math.min(Math.abs(p.pnl_usd)/Math.max(c.base_candidate.risk.maximum_loss,1),1);
n.style.background=p.pnl_usd>=0?`rgba(46,230,166,${{.12+.55*strength}})`:`rgba(255,107,122,${{.12+.55*strength}})`}}$("heatmap").append(n)}})}});
const ivRows=["iv_down","iv_stable","iv_up"].map(k=>{{const p=c.scenario_points.find(x=>x.valuation_date===R.request.catalyst_date&&Math.abs(x.spot-target)<.001&&x.iv_case===k);
return {{label:k,value:p?p.pnl_usd:0}}}});valueBars($("iv"),ivRows);
$("scenarios").replaceChildren();d.target_pnl_rows.forEach(row=>{{const tr=E("tr");
[money(row.spot),money(row.catalyst_iv_down_usd),money(row.catalyst_iv_stable_usd),
money(row.catalyst_iv_up_usd)].forEach(v=>tr.append(E("td",v)));$("scenarios").append(tr)}});
const p=c.scenario_points.find(x=>x.valuation_date===R.request.catalyst_date&&Math.abs(x.spot-target)<.001&&x.iv_case==="iv_stable");
$("attribution").replaceChildren(E("p",`Objectif $${{target}} : sous-jacent ${{money(p.underlying_effect_usd)}}, temps ${{money(p.theta_effect_usd)}}, IV ${{money(p.iv_effect_usd)}}, exécution ${{money(p.execution_cost_effect_usd)}}, résiduel ${{money(p.residual_usd)}}`),
E("p",`Delta ${{c.net_greeks.delta.toFixed(3)}} · gamma ${{c.net_greeks.gamma.toFixed(3)}} · theta ${{c.net_greeks.theta.toFixed(3)}} · vega ${{c.net_greeks.vega.toFixed(3)}} · rho ${{c.net_greeks.rho.toFixed(3)}}`));
}}
function selectCandidate(candidateId,sourceTrigger){{$("candidate").value=candidateId;
document.querySelectorAll(".accordion-trigger").forEach(trigger=>trigger.classList.remove("active"));
if(sourceTrigger)sourceTrigger.classList.add("active");render()}}
const accordionTriggers=buildAccordions();
$("candidate").addEventListener("change",()=>selectCandidate($("candidate").value,null));
$("currencyUSD").addEventListener("click",()=>{{pnlCurrency="USD";$("currencyUSD").setAttribute("aria-pressed","true");
$("currencyEUR").setAttribute("aria-pressed","false");renderTargetPnl(byId[$("candidate").value])}});
$("currencyEUR").addEventListener("click",()=>{{pnlCurrency="EUR";$("currencyEUR").setAttribute("aria-pressed","true");
$("currencyUSD").setAttribute("aria-pressed","false");renderTargetPnl(byId[$("candidate").value])}});
const balanced=R.rankings.find(r=>r.profile==="balanced"&&r.scores.length);
const firstAvailable=R.rankings.find(r=>r.scores.length);
const initialScore=(balanced||firstAvailable)?.scores[0];
if(initialScore){{const preferredProfile=balanced?"balanced":firstAvailable.profile,
initialTrigger=accordionTriggers.find(trigger=>trigger.dataset.profile===preferredProfile&&
trigger.dataset.candidateId===initialScore.candidate_id);if(initialTrigger)initialTrigger.click();
else selectCandidate(initialScore.candidate_id,null)}}
const history=$("history"),historyLimits=E("div");
appendList(historyLimits,R.historical_evidence.limitations);
history.append(E("p",R.historical_evidence.summary),
E("p",`Statut=${{R.historical_evidence.status}} · confiance=${{R.historical_evidence.confidence}} · effet=${{R.historical_evidence.eligibility_effect}}`,"warn"),
historyLimits,E("p","Artefacts : "+R.historical_evidence.source_artifacts.join(" · "),"muted"));
const lim=$("limits");lim.append(E("p",R.historical_warning,"warn"));R.limitations.forEach(x=>lim.append(E("p","• "+x)));
lim.append(E("p","Sources : "+R.data_sources.join(" · "),"muted"),E("p","Probabilités : "+R.probability_status,"muted"),
E("p","order_capability="+R.order_capability+"; aucune fonction de transmission.","warn"));
</script>
</body>
</html>
"""


def write_reports(
    report: ThesisScanReport,
    *,
    json_out: Path,
    markdown_out: Path,
    html_out: Path,
) -> ThesisScanReport:
    outputs = [str(json_out), str(markdown_out), str(html_out)]
    updated = report.model_copy(update={"output_files": outputs})
    for path in (json_out, markdown_out, html_out):
        path.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(updated.model_dump_json(indent=2), encoding="utf-8")
    markdown_out.write_text(markdown_report(updated), encoding="utf-8")
    html_out.write_text(html_dashboard(updated), encoding="utf-8")
    return updated
