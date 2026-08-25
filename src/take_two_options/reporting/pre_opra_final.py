"""Final pre-OPRA report contract and standalone French renderers."""

# ruff: noqa: E501

from __future__ import annotations

import html
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class RunManifest(StrictModel):
    schema_version: Literal["2.0"]
    generated_at: datetime
    code_commit: str = Field(min_length=7, max_length=40)
    configuration_hash: str = Field(min_length=64, max_length=64)
    dataset_hash: str = Field(min_length=64, max_length=64)
    seed: int
    python_version: str
    platform: str
    dependencies: dict[str, str]
    schema_versions: dict[str, str]
    score_versions: dict[str, str]
    artifact_hashes: dict[str, str]
    command: str
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"


class ReportSection(StrictModel):
    section_id: Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
    title: str
    status: str
    summary: str
    artifact: str


class FinalBaselineRow(StrictModel):
    strategy: str
    observations: int = Field(gt=0)
    total_return: float
    expected_return: float
    median_return: float
    cvar_95: float = Field(ge=0)
    maximum_drawdown: float = Field(ge=0)
    probability_profit: float = Field(ge=0, le=1)
    probability_target: float = Field(ge=0, le=1)
    probability_loss_50: float = Field(ge=0, le=1)
    probability_loss_70: float = Field(ge=0, le=1)
    probability_loss_90: float = Field(ge=0, le=1)
    sharpe: float | None
    sortino: float | None
    transaction_costs_eur: float = Field(ge=0)
    evidence: str


class FinalScoreSummary(StrictModel):
    kind: str
    score_value: float = Field(ge=0, le=100)
    score_coverage: float = Field(ge=0, le=1)
    missing_components: list[str]
    confidence: str
    formula_version: str


class FinalLossPoint(StrictModel):
    threshold: float = Field(gt=0, le=1)
    probability: float = Field(ge=0, le=1)
    wilson_interval_95: tuple[float, float]
    bootstrap_interval_95: tuple[float, float]


class FinalGateRow(StrictModel):
    setting_id: str
    passed: bool
    best_candidate_id: str | None
    minimum_opportunity: float
    maximum_risk: float
    minimum_evidence: float
    minimum_execution_quality: float


class TopCandidate(StrictModel):
    label: Literal[
        "BEST_RISK_ADJUSTED",
        "HIGHEST_UPSIDE",
        "LOWEST_RISK",
        "BEST_BLOCKED_CANDIDATE",
        "BEST_SIMPLE_BASELINE",
    ]
    candidate_id: str
    rationale: str
    classification: str


class FinalPreOpraReport(StrictModel):
    schema_version: Literal["2.0"]
    report_id: str
    ticker: Literal["TTWO"]
    generated_at: datetime
    overall_status: Literal["PRE_OPRA_RESEARCH_COMPLETE"]
    evidence_grade: Literal["development_oos_limited"]
    decision: Literal["NO_POSITION_RECOMMENDED"]
    decision_scope: Literal["research_only_not_investment_advice"]
    engine_verdict: Literal["ENGINE_NOT_PROVEN_SUPERIOR"]
    run_manifest: RunManifest
    sections: list[ReportSection] = Field(min_length=14, max_length=14)
    data_coverage: dict[str, float | int | str | None]
    calibration_status: dict[str, float | int | str | None]
    walk_forward_status: dict[str, float | int | str | bool | None]
    baseline_table: list[FinalBaselineRow] = Field(min_length=9, max_length=9)
    top_candidates: list[TopCandidate] = Field(min_length=5, max_length=5)
    five_scores: list[FinalScoreSummary] = Field(min_length=5, max_length=5)
    raw_metrics: dict[str, float | int | str | None]
    severe_loss_ladder: list[FinalLossPoint] = Field(min_length=6, max_length=6)
    gate_sensitivity: list[FinalGateRow] = Field(min_length=3)
    best_blocked_candidate: dict[str, object]
    remaining_blockers: list[str] = Field(min_length=1)
    opra_readiness: list[str] = Field(min_length=1)
    exact_opra_variables: list[str]
    exact_command_after_opra: str
    external_source_ids: list[str]
    holdout_state: Literal["UNOPENED"]
    holdout_used: Literal[False]
    phase_m_started: Literal[False]
    transmit: Literal[False] = False
    what_if: Literal[True] = True
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def enforce_final_boundary(self) -> FinalPreOpraReport:
        if [section.section_id for section in self.sections] != list("ABCDEFGHIJKLMN"):
            raise ValueError("final report must contain exactly sections A through N in order")
        if {score.kind for score in self.five_scores} != {
            "opportunity",
            "risk",
            "evidence",
            "model_agreement",
            "execution_quality",
        }:
            raise ValueError("all five independent scores are required")
        if {candidate.label for candidate in self.top_candidates} != {
            "BEST_RISK_ADJUSTED",
            "HIGHEST_UPSIDE",
            "LOWEST_RISK",
            "BEST_BLOCKED_CANDIDATE",
            "BEST_SIMPLE_BASELINE",
        }:
            raise ValueError("all five top-candidate views are required")
        return self


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_markdown(report: FinalPreOpraReport) -> str:
    lines = [
        "# Validation quantitative finale pré-OPRA — TTWO",
        "",
        f"**{report.overall_status} — {report.decision}**",
        "",
        f"Verdict moteur : **`{report.engine_verdict}`**. Recherche uniquement ; aucune capacité d'ordre.",
        "",
    ]
    for section in report.sections:
        lines.extend(
            [
                f"## {section.section_id}. {section.title}",
                "",
                f"Statut : `{section.status}`. {section.summary}",
                f"Preuve : `{section.artifact}`.",
                "",
            ]
        )
        if section.section_id == "E":
            lines.extend(
                [
                    "| Stratégie | Total | E[R] | Médiane | CVaR95 | Max DD | P(profit) | P(cible) | P(perte>50%) | Coûts EUR |",
                    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
                ]
            )
            lines.extend(
                "| "
                + " | ".join(
                    [
                        row.strategy,
                        _percent(row.total_return),
                        _percent(row.expected_return),
                        _percent(row.median_return),
                        _percent(row.cvar_95),
                        _percent(row.maximum_drawdown),
                        _percent(row.probability_profit),
                        _percent(row.probability_target),
                        _percent(row.probability_loss_50),
                        f"{row.transaction_costs_eur:.2f}",
                    ]
                )
                + " |"
                for row in report.baseline_table
            )
            lines.append("")
        elif section.section_id == "F":
            lines.extend(
                f"- `{item.label}` : **{item.candidate_id}** — {item.rationale}"
                for item in report.top_candidates
            )
            lines.append("")
        elif section.section_id == "G":
            lines.extend(
                f"- `{item.kind}` : **{item.score_value:.1f}/100**, couverture "
                f"{item.score_coverage:.0%}, confiance `{item.confidence}`, manquants "
                f"{', '.join(item.missing_components) or 'aucun'}"
                for item in report.five_scores
            )
            lines.append("")
        elif section.section_id == "I":
            lines.extend(
                f"- P(perte > {item.threshold:.0%}) = **{item.probability:.0%}** ; "
                f"Wilson 95 % [{item.wilson_interval_95[0]:.1%}, "
                f"{item.wilson_interval_95[1]:.1%}]"
                for item in report.severe_loss_ladder
            )
            lines.append("")
        elif section.section_id == "M":
            lines.extend(f"- {item}" for item in report.remaining_blockers)
            lines.append("")
        elif section.section_id == "N":
            lines.extend(f"- {item}" for item in report.opra_readiness)
            lines.extend(
                [
                    "",
                    "Variables attendues : " + ", ".join(report.exact_opra_variables),
                    "",
                    f"Commande : `{report.exact_command_after_opra}`",
                    "",
                ]
            )
    lines.extend(
        [
            "## Reproductibilité",
            "",
            f"- Commit source : `{report.run_manifest.code_commit}`",
            f"- Hash configuration : `{report.run_manifest.configuration_hash}`",
            f"- Hash dataset agrégé : `{report.run_manifest.dataset_hash}`",
            f"- Seed : `{report.run_manifest.seed}`",
            "- Holdout : `UNOPENED`",
            "- Invariants : `transmit=false`, `what_if=true`, `order_capability=forbidden`",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(report: FinalPreOpraReport) -> str:
    baseline_rows = "".join(
        "<tr>"
        f"<td><strong>{html.escape(row.strategy)}</strong></td>"
        f"<td>{_percent(row.total_return)}</td><td>{_percent(row.expected_return)}</td>"
        f"<td>{_percent(row.median_return)}</td><td>{_percent(row.cvar_95)}</td>"
        f"<td>{_percent(row.maximum_drawdown)}</td><td>{_percent(row.probability_profit)}</td>"
        f"<td>{_percent(row.probability_loss_50)}</td><td>€{row.transaction_costs_eur:.0f}</td>"
        "</tr>"
        for row in report.baseline_table
    )
    score_cards = "".join(
        "<article class='score-card'>"
        f"<div class='eyebrow'>{html.escape(score.kind)}</div>"
        f"<div class='score'>{score.score_value:.1f}<span>/100</span></div>"
        f"<div class='bar'><i style='width:{score.score_value:.1f}%'></i></div>"
        f"<p>Couverture <strong>{score.score_coverage:.0%}</strong> · "
        f"confiance {html.escape(score.confidence)}</p>"
        f"<small>Manquants : {html.escape(', '.join(score.missing_components) or 'aucun')}</small>"
        "</article>"
        for score in report.five_scores
    )
    top_cards = "".join(
        "<article class='candidate'>"
        f"<div class='eyebrow'>{html.escape(item.label)}</div>"
        f"<h3>{html.escape(item.candidate_id)}</h3>"
        f"<span class='pill'>{html.escape(item.classification)}</span>"
        f"<p>{html.escape(item.rationale)}</p></article>"
        for item in report.top_candidates
    )
    ladder = "".join(
        "<tr>"
        f"<td>&gt; {item.threshold:.0%}</td><td><strong>{item.probability:.0%}</strong></td>"
        f"<td>{item.wilson_interval_95[0]:.1%} – {item.wilson_interval_95[1]:.1%}</td>"
        f"<td>{item.bootstrap_interval_95[0]:.1%} – {item.bootstrap_interval_95[1]:.1%}</td>"
        "</tr>"
        for item in report.severe_loss_ladder
    )
    gate_rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.setting_id)}</td>"
        f"<td>{'PASS' if item.passed else 'NO POSITION'}</td>"
        f"<td>{item.minimum_opportunity:.0f}</td><td>{item.maximum_risk:.0f}</td>"
        f"<td>{item.minimum_evidence:.0f}</td><td>{item.minimum_execution_quality:.0f}</td>"
        "</tr>"
        for item in report.gate_sensitivity
    )
    sections = "".join(
        "<article class='section-row'>"
        f"<b>{item.section_id}</b><div><h3>{html.escape(item.title)}</h3>"
        f"<p>{html.escape(item.summary)}</p></div>"
        f"<span class='status'>{html.escape(item.status)}</span></article>"
        for item in report.sections
    )
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in report.remaining_blockers)
    readiness = "".join(f"<li>{html.escape(item)}</li>" for item in report.opra_readiness)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TTWO — validation quantitative finale pré-OPRA</title>
<style>
:root{{--ink:#17233d;--muted:#61708a;--paper:#f4f7fb;--card:#fff;--line:#dce4ef;
--blue:#2f6fed;--navy:#0d1f3c;--red:#b42318;--amber:#b96d00;--green:#16794d}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1240px;margin:auto;padding:44px 28px 80px}} h1{{font-size:clamp(34px,5vw,66px);
line-height:1.02;letter-spacing:-.045em;margin:14px 0 18px;max-width:900px}} h2{{font-size:26px;
letter-spacing:-.02em;margin:56px 0 18px}} h3{{margin:5px 0 8px}} p{{color:var(--muted)}}
.eyebrow{{font-size:11px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:var(--blue)}}
.hero{{background:linear-gradient(135deg,#0d1f3c,#163d7b);color:#fff;border-radius:24px;padding:42px;
box-shadow:0 22px 60px #17305a22}} .hero p{{color:#c7d6ef;max-width:760px;font-size:17px}}
.verdict{{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}} .pill,.verdict span{{display:inline-block;
padding:7px 11px;border-radius:999px;background:#eef3fb;color:#274467;font-size:12px;font-weight:750}}
.verdict span{{background:#ffffff16;color:#fff;border:1px solid #ffffff2c}}
.decision{{border-left:5px solid #f3b44e;background:#fff7e6;padding:18px 20px;border-radius:12px;margin-top:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}}
.score-card,.candidate{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;
box-shadow:0 8px 24px #17305a0a}} .score{{font-size:38px;font-weight:850;letter-spacing:-.04em}}
.score span{{font-size:14px;color:var(--muted);font-weight:600}} .score-card p{{margin-bottom:4px}}
.score-card small{{color:var(--muted)}} .bar{{height:7px;background:#e6edf7;border-radius:8px;overflow:hidden}}
.bar i{{display:block;height:100%;background:linear-gradient(90deg,#235ecf,#61a0ff)}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:16px;background:#fff}}
table{{border-collapse:collapse;width:100%;min-width:840px}} th{{background:#eef3f9;color:#475974;font-size:11px;
text-transform:uppercase;letter-spacing:.06em}} th,td{{padding:12px 13px;border-bottom:1px solid var(--line);
text-align:right;white-space:nowrap}} th:first-child,td:first-child{{text-align:left}}
.section-row{{display:grid;grid-template-columns:42px 1fr auto;gap:14px;align-items:center;padding:15px 0;
border-bottom:1px solid var(--line)}} .section-row>b{{display:grid;place-items:center;width:34px;height:34px;
border-radius:10px;background:#e8effb;color:#245ec4}} .section-row h3,.section-row p{{margin:0}}
.status{{font-size:11px;font-weight:800;color:#43526c}} .warning{{background:#fff;border:1px solid #f0c7c2;
border-left:6px solid var(--red);padding:24px;border-radius:16px}} .warning li{{margin:8px 0}}
.ready{{background:#eaf8f1;border-left:6px solid var(--green);padding:24px;border-radius:16px}}
code{{background:#eaf0f8;padding:2px 6px;border-radius:6px;overflow-wrap:anywhere}} footer{{margin-top:58px;
padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
@media(max-width:700px){{main{{padding:22px 15px 60px}}.hero{{padding:26px 22px}}.section-row{{grid-template-columns:38px 1fr}}
.section-row .status{{grid-column:2}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">TTWO · Research engine · 08 août 2026</div>
<h1>Validation quantitative finale pré‑OPRA</h1>
<p>Les données historiques accessibles ont été normalisées, calibrées et testées chronologiquement.
Le résultat financier du moteur est défavorable et l'incertitude reste élevée.</p>
<div class="verdict"><span>{report.overall_status}</span><span>{report.engine_verdict}</span>
<span>HOLDOUT {report.holdout_state}</span><span>ORDER CAPABILITY FORBIDDEN</span></div></section>
<div class="decision"><strong>{report.decision}</strong> — le meilleur résultat de développement
ne justifie pas une position. Le meilleur candidat bloqué reste visible ci-dessous.</div>

<h2>Top candidates</h2><div class="grid">{top_cards}</div>
<h2>Cinq scores indépendants</h2><div class="grid">{score_cards}</div>
<h2>V10 vs baselines — walk-forward OOS</h2><div class="table-wrap"><table><thead><tr>
<th>Stratégie</th><th>Total</th><th>E[R]</th><th>Médiane</th><th>CVaR95</th><th>Max DD</th>
<th>P(profit)</th><th>P(perte&gt;50%)</th><th>Coûts</th></tr></thead><tbody>{baseline_rows}</tbody></table></div>
<h2>Severe-loss ladder — engine candidate</h2><div class="table-wrap"><table><thead><tr>
<th>Seuil de perte</th><th>Probabilité</th><th>Wilson 95%</th><th>Bootstrap 95%</th>
</tr></thead><tbody>{ladder}</tbody></table></div>
<h2>Sensibilité des gates</h2><div class="table-wrap"><table><thead><tr><th>Réglage</th>
<th>Décision</th><th>Opp. min</th><th>Risque max</th><th>Preuve min</th><th>Exécution min</th>
</tr></thead><tbody>{gate_rows}</tbody></table></div>
<h2>Sections A–N</h2><section>{sections}</section>
<h2>Remaining blockers</h2><section class="warning"><ul>{blockers}</ul></section>
<h2>OPRA readiness</h2><section class="ready"><ul>{readiness}</ul>
<p>Variables : <code>{html.escape(', '.join(report.exact_opra_variables))}</code></p>
<p>Commande : <code>{html.escape(report.exact_command_after_opra)}</code></p></section>
<footer>Recherche uniquement — pas un conseil en investissement. <code>transmit=false</code> ·
<code>what_if=true</code> · <code>order_capability=forbidden</code><br>
Commit source {html.escape(report.run_manifest.code_commit)} · config {html.escape(report.run_manifest.configuration_hash)}</footer>
</main></body></html>"""
