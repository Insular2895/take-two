"""End-to-end read-only V10 Bullish Thesis Scanner."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml

from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.thesis_scanner.data import load_thesis_chain
from take_two_options.thesis_scanner.enumeration import enumerate_bullish_candidates
from take_two_options.thesis_scanner.pricing import evaluate_candidates
from take_two_options.thesis_scanner.ranking import rank_candidates
from take_two_options.thesis_scanner.reporting import write_reports
from take_two_options.thesis_scanner.schemas import (
    ThesisCandidateStatus,
    ThesisScanPolicy,
    ThesisScanReport,
    ThesisScanRequest,
)
from take_two_options.thesis_scanner.tickets import build_ibkr_previews


def load_thesis_policy(path: Path) -> ThesisScanPolicy:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("thesis scanner policy must be one YAML object")
    return ThesisScanPolicy.model_validate(payload)


def run_thesis_scan(
    *,
    request: ThesisScanRequest,
    json_out: Path,
    markdown_out: Path,
    html_out: Path,
    policy_path: Path = Path("configs/thesis_scanner/default.yaml"),
    knowledge_dir: Path = Path("research/knowledge_items"),
    created_at: datetime | None = None,
) -> ThesisScanReport:
    """Run the V10 scanner without exposing any order-transmission operation."""
    scan_time = created_at or datetime.now(UTC)
    if scan_time.tzinfo is None:
        scan_time = scan_time.replace(tzinfo=UTC)
    policy = load_thesis_policy(policy_path)
    chain = load_thesis_chain(
        Path(request.current_chain),
        ticker=request.ticker,
        spot_override=request.spot_override,
    )
    catalog = compile_knowledge(load_knowledge(knowledge_dir))
    enumeration = enumerate_bullish_candidates(
        request=request,
        policy=policy,
        chain=chain,
        catalog=catalog,
        scan_time=scan_time,
    )
    evaluation = evaluate_candidates(
        enumerated=enumeration.candidates,
        chain=chain,
        request=request,
        policy=policy,
    )
    candidates = list(evaluation.candidates)
    rankings = rank_candidates(
        candidates,
        request=request,
        policy=policy,
        spot=chain.spot,
    )
    previews = build_ibkr_previews(candidates, rankings)
    blocked = Counter(enumeration.blocked_reasons)
    blocked.update(evaluation.blocked_reasons)
    if any(candidate.status is ThesisCandidateStatus.ELIGIBLE for candidate in candidates):
        overall_status = ThesisCandidateStatus.ELIGIBLE
    elif candidates:
        overall_status = ThesisCandidateStatus.WATCHLIST
    else:
        overall_status = ThesisCandidateStatus.NO_TRADE
    report_identity = {
        "request": request,
        "policy": policy,
        "chain_source": chain.source_id,
        "chain_as_of": chain.as_of,
    }
    report_id = f"v10-{stable_hash(report_identity)[:20]}"
    report = ThesisScanReport(
        report_id=report_id,
        created_at=scan_time,
        request=request,
        policy=policy,
        chain=chain,
        quote_rejections=enumeration.quote_rejections,
        generated_by_architecture=enumeration.generated_by_architecture,
        generated_candidates=enumeration.generated_candidates,
        technically_admissible_candidates=len(candidates),
        overall_status=overall_status,
        candidates=candidates,
        rankings=rankings,
        ibkr_previews=previews,
        blocked_reasons=dict(sorted(blocked.items())),
        historical_warning=(
            "Les résultats historiques V9 étaient faibles/contaminés et abaissent "
            f"la confiance à {policy.historical_confidence:.2f}; ils ne bloquent pas "
            "automatiquement ce mode de thèse et ne constituent pas une validation."
        ),
        probability_status=(
            "user_supplied" if request.scenario_probabilities is not None else "not_provided"
        ),
        assumptions=[
            (
                "LEAPS call désigne une classe de maturité de long call, jamais une "
                "architecture distincte."
            ),
            "Le débit prudent utilise ask pour chaque achat et bid pour chaque vente.",
            (
                "Le moteur de scénario pré-échéance est le moteur américain "
                "QuantLib finite-difference partagé."
            ),
            (
                "Les objectifs de cours viennent de l'utilisateur; le scanner "
                "n'invente aucune probabilité."
            ),
        ],
        limitations=[
            "Une chaîne de jambes ne garantit pas une exécution combo simultanée.",
            "Les IV et Greeks sont des estimations de modèle, pas des cotations.",
            (
                "Les dividendes, taux, FX, coûts et seuils de liquidité sont des "
                "entrées datées à revérifier."
            ),
            (
                "Les contrats au multiplicateur ou livrable non confirmés restent "
                "signalés et doivent être contrôlés dans IBKR."
            ),
            "Aucune allocation V9 fixe n'est réutilisée dans ce scanner.",
        ],
        data_sources=sorted(
            {
                chain.source_id,
                chain.spot_source_id,
                policy.fx_rate_source,
                policy.risk_free_rate_source,
                policy.dividend_source,
                "research/knowledge_items (compiled strategy recipes)",
            }
        ),
    )
    return write_reports(
        report,
        json_out=json_out,
        markdown_out=markdown_out,
        html_out=html_out,
    )
