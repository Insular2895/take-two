"""Fail-closed final pre-OPRA report and static dashboard rendering."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from take_two_options.domain import StrictModel


class RunManifest(StrictModel):
    schema_version: Literal["1.0"]
    generated_at: datetime
    code_commit: str = Field(min_length=7, max_length=40)
    configuration_hash: str = Field(min_length=64, max_length=64)
    dataset_hash: str = Field(min_length=64, max_length=64)
    seed: int
    python_version: str
    platform: str
    dependencies: dict[str, str]
    command: str
    holdout_used: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"


class PhaseResult(StrictModel):
    phase: Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
    title: str
    status: str
    artifact: str
    validated: list[str]
    remaining: list[str]


class FinalPreOpraReport(StrictModel):
    schema_version: Literal["1.0"]
    report_id: str
    ticker: str
    overall_status: Literal["READY_RESEARCH_ONLY", "BLOCKED_BY_DATA"]
    evidence_grade: Literal[
        "software_tested_only",
        "numerically_validated",
        "historically_validated",
        "forward_validated",
    ]
    decision: Literal["NO_POSITION_RECOMMENDED"]
    decision_scope: Literal["research_only_not_investment_advice"]
    run_manifest: RunManifest
    phase_results: list[PhaseResult] = Field(min_length=12, max_length=12)
    key_metrics: dict[str, float | int | str | None]
    score_status: dict[str, Literal["unavailable", "computed"]]
    best_blocked_candidate: str
    blockers: list[str] = Field(min_length=1)
    opra_readiness: list[str]
    external_source_ids: list[str]
    holdout_state: Literal["UNOPENED"]
    holdout_used: Literal[False]
    phase_m_started: Literal[False]
    order_capability: Literal["forbidden"] = "forbidden"

    @model_validator(mode="after")
    def enforce_fail_closed_boundary(self) -> FinalPreOpraReport:
        if [result.phase for result in self.phase_results] != list("ABCDEFGHIJKL"):
            raise ValueError("final report must contain exactly phases A through L in order")
        if self.overall_status == "BLOCKED_BY_DATA" and not self.blockers:
            raise ValueError("blocked final report requires blockers")
        if set(self.score_status) != {
            "opportunity",
            "risk",
            "evidence",
            "model_agreement",
            "execution_quality",
        }:
            raise ValueError("all five independent score statuses are required")
        return self


def render_markdown(report: FinalPreOpraReport) -> str:
    lines = [
        "# Validation quantitative finale pré-OPRA — TTWO",
        "",
        f"**Statut : `{report.overall_status}` — `{report.decision}`.**",
        "",
        "Le logiciel est testé, mais la preuve financière reste insuffisante. Ce rapport",
        "est un outil de recherche, pas un conseil en investissement, et ne peut créer",
        "aucun ordre.",
        "",
        "## Résultat par phase",
        "",
        "| Phase | Statut | Livrable |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {item.phase} — {item.title} | `{item.status}` | [{item.artifact}]({item.artifact}) |"
        for item in report.phase_results
    )
    lines.extend(["", "## Métriques réellement calculées", ""])
    lines.extend(f"- `{key}` : {value}" for key, value in report.key_metrics.items())
    lines.extend(["", "## Cinq scores indépendants", ""])
    lines.extend(f"- `{key}` : **{value}**" for key, value in report.score_status.items())
    lines.extend(
        [
            "",
            f"Meilleur candidat bloqué : `{report.best_blocked_candidate}`.",
            "",
            "## Bloqueurs",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report.blockers)
    lines.extend(["", "## Préparation OPRA future (phase M non démarrée)", ""])
    lines.extend(f"- {item}" for item in report.opra_readiness)
    lines.extend(
        [
            "",
            "## Reproductibilité",
            "",
            f"- Commit : `{report.run_manifest.code_commit}`",
            f"- Configuration : `{report.run_manifest.configuration_hash}`",
            f"- Dataset : `{report.run_manifest.dataset_hash}`",
            f"- Seed : `{report.run_manifest.seed}`",
            f"- Commande : `{report.run_manifest.command}`",
            "- Holdout : `UNOPENED`, jamais utilisé",
            "- Capacité d'ordre : `forbidden`",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(report: FinalPreOpraReport) -> str:
    phase_rows = "".join(
        "<tr>"
        f"<td>{item.phase}</td><td>{html.escape(item.title)}</td>"
        f"<td><code>{html.escape(item.status)}</code></td>"
        f"<td>{html.escape(item.artifact)}</td></tr>"
        for item in report.phase_results
    )
    metrics = "".join(
        f"<li><code>{html.escape(key)}</code>: {html.escape(str(value))}</li>"
        for key, value in report.key_metrics.items()
    )
    scores = "".join(
        f"<article><h3>{html.escape(key)}</h3><p>{value}</p></article>"
        for key, value in report.score_status.items()
    )
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in report.blockers)
    readiness = "".join(f"<li>{html.escape(item)}</li>" for item in report.opra_readiness)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>TTWO — validation finale pré-OPRA</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;margin:auto;max-width:1180px;
padding:32px;color:#172033;background:#f6f8fb}}
h1,h2{{color:#11264d}} .banner{{padding:20px;border-left:6px solid #b42318;background:#fff0ee}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
article{{background:white;padding:16px;border-radius:8px}}
table{{width:100%;border-collapse:collapse;background:white}}
th,td{{padding:9px;border:1px solid #d7dfeb;text-align:left}}
code{{word-break:break-all}}
</style></head><body>
<h1>Validation quantitative finale pré-OPRA — TTWO</h1>
<section class="banner"><strong>{report.overall_status} — {report.decision}</strong><br>
Logiciel testé, preuve financière insuffisante. Recherche uniquement,
aucun ordre possible.</section>
<h2>Phases A–L</h2><table><thead><tr><th>Phase</th><th>Objet</th>
<th>Statut</th><th>Livrable</th></tr></thead><tbody>{phase_rows}</tbody></table>
<h2>Métriques réellement calculées</h2><ul>{metrics}</ul>
<h2>Cinq scores distincts</h2><div class="grid">{scores}</div>
<h2>Meilleur candidat bloqué</h2><p><code>{html.escape(report.best_blocked_candidate)}</code></p>
<h2>Bloqueurs</h2><ul>{blockers}</ul>
<h2>Préparation OPRA future — phase M non démarrée</h2><ul>{readiness}</ul>
<h2>Reproductibilité</h2><ul><li>commit <code>{report.run_manifest.code_commit}</code></li>
<li>config <code>{report.run_manifest.configuration_hash}</code></li>
<li>dataset <code>{report.run_manifest.dataset_hash}</code></li>
<li>holdout UNOPENED, inutilisé</li><li>order_capability forbidden</li></ul>
</body></html>"""
