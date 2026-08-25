"""Deterministic profile-specific rankings for bullish thesis candidates."""

from __future__ import annotations

from take_two_options.knowledge.schemas import Architecture
from take_two_options.thesis_scanner.schemas import (
    ProfileRanking,
    ProfileScore,
    ThesisCandidate,
    ThesisProfile,
    ThesisScanPolicy,
    ThesisScanRequest,
)


def _clamp(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _normalized_ratio(value: float) -> float:
    positive = max(value, 0.0)
    return positive / (1 + positive)


def _criteria(
    candidate: ThesisCandidate,
    *,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    spot: float,
) -> dict[str, float]:
    base = candidate.base_candidate
    budget_usd = request.budget_eur * policy.eur_usd_rate
    loss_ratio = base.risk.maximum_loss / budget_usd
    reduced_loss = _clamp(1 - loss_ratio)
    break_evens = base.risk.break_even_points
    nearest_break_even = (
        min(break_evens, key=lambda value: abs(value - spot)) if break_evens else spot * 2
    )
    target_span = max(max(request.target_prices) - spot, spot * 0.1, 1)
    breakeven_proximity = _clamp(1 - abs(nearest_break_even - spot) / target_span)

    spread_scores: list[float] = []
    liquidity_scores: list[float] = []
    for leg in base.legs:
        midpoint = (leg.quote.bid + leg.quote.ask) / 2
        relative_spread = (
            (leg.quote.ask - leg.quote.bid) / midpoint
            if midpoint > 0
            else policy.maximum_relative_spread * 2
        )
        spread_score = _clamp(1 - relative_spread / policy.maximum_relative_spread)
        spread_scores.append(spread_score)
        if leg.quote.open_interest is None:
            oi_score = 0.35
        elif policy.minimum_open_interest == 0:
            oi_score = 1
        else:
            oi_score = _clamp(leg.quote.open_interest / (policy.minimum_open_interest * 5))
        if leg.quote.volume is None:
            volume_score = 0.35
        elif policy.minimum_volume == 0:
            volume_score = 1
        else:
            volume_score = _clamp(leg.quote.volume / (policy.minimum_volume * 5))
        liquidity_scores.append(0.5 * spread_score + 0.35 * oi_score + 0.15 * volume_score)
    spread_quality = sum(spread_scores) / len(spread_scores)
    liquidity = sum(liquidity_scores) / len(liquidity_scores)

    daily_theta_fraction = abs(candidate.net_greeks.theta) / max(
        candidate.execution.total_cost_usd,
        1,
    )
    theta_moderation = _clamp(1 - daily_theta_fraction / 0.02)
    preference = {
        Architecture.BULL_CALL_SPREAD: 1.0,
        Architecture.CALL_BUTTERFLY: 0.65,
        Architecture.LONG_CALL: 0.45,
    }[candidate.architecture]
    target_returns = [
        pnl / max(base.risk.maximum_loss, 1)
        for pnl in candidate.target_pnl_stable_at_catalyst_usd.values()
    ]
    positive_target_share = sum(value > 0 for value in target_returns) / len(target_returns)
    payoff_ratio = (
        base.risk.maximum_gain / max(base.risk.maximum_loss, 1)
        if base.risk.maximum_gain is not None
        else max(target_returns)
    )
    long_contracts = sum(leg.quantity for leg in base.legs if leg.side.value == "long")
    bullish_exposure = _clamp(candidate.net_greeks.delta / max(100 * long_contracts, 1))
    cost_quality = _clamp(1 - candidate.execution.total_cost_usd / budget_usd)
    convexity = _normalized_ratio(max(candidate.net_greeks.gamma, 0))
    modeled_return = _normalized_ratio(max(target_returns))
    butterfly_targeting = 0.0
    if candidate.architecture is Architecture.CALL_BUTTERFLY:
        center = next(leg.quote.strike for leg in base.legs if leg.side.value == "short")
        target_distance = min(abs(target - center) for target in request.target_prices)
        wing_width = max(
            abs(leg.quote.strike - center) for leg in base.legs if leg.side.value == "long"
        )
        butterfly_targeting = _clamp(1 - target_distance / max(wing_width, 1))
    return {
        "reduced_loss": reduced_loss,
        "breakeven_proximity": breakeven_proximity,
        "liquidity": liquidity,
        "spread_quality": spread_quality,
        "theta_moderation": theta_moderation,
        "bull_spread_preference": preference,
        "payoff_ratio": _normalized_ratio(payoff_ratio),
        "scenario_breadth": positive_target_share,
        "bullish_exposure": bullish_exposure,
        "cost_quality": cost_quality,
        "convexity": convexity,
        "modeled_return": modeled_return,
        "butterfly_targeting": butterfly_targeting,
        "historical_confidence": policy.historical_confidence,
    }


def _reason(label: str, value: float) -> str:
    descriptions = {
        "reduced_loss": "perte maximale réduite vs budget",
        "breakeven_proximity": "seuil de rentabilité proche du spot",
        "liquidity": "qualité de liquidité des jambes",
        "spread_quality": "spreads bid/ask resserrés",
        "theta_moderation": "érosion temporelle modérée",
        "bull_spread_preference": "préférence structurelle du profil",
        "payoff_ratio": "ratio gain/risque",
        "scenario_breadth": "part des objectifs bénéficiaires",
        "bullish_exposure": "exposition directionnelle haussière",
        "cost_quality": "capital non consommé",
        "convexity": "convexité gamma positive",
        "modeled_return": "rendement modélisé sur objectifs",
        "butterfly_targeting": "centrage du butterfly sur un objectif",
        "historical_confidence": "confiance historique prudente",
    }
    return f"{descriptions[label]}: {value:.3f}/1.000"


def rank_candidates(
    candidates: list[ThesisCandidate],
    *,
    request: ThesisScanRequest,
    policy: ThesisScanPolicy,
    spot: float,
) -> list[ProfileRanking]:
    """Build independent, deterministic rankings without hidden tie breakers."""
    criteria_by_candidate = {
        candidate.candidate_id: _criteria(
            candidate,
            request=request,
            policy=policy,
            spot=spot,
        )
        for candidate in candidates
    }
    rankings: list[ProfileRanking] = []
    for profile in ThesisProfile:
        weights = policy.profile_weights[profile]
        total_weight = sum(weights.values())
        scores: list[ProfileScore] = []
        for candidate in candidates:
            criteria = criteria_by_candidate[candidate.candidate_id]
            contributions = {
                name: weights.get(name, 0) * criteria[name] / total_weight for name in weights
            }
            numeric_score = 100 * sum(contributions.values())
            top_reasons = sorted(
                contributions,
                key=lambda name: (-contributions[name], name),
            )[:3]
            scores.append(
                ProfileScore(
                    candidate_id=candidate.candidate_id,
                    profile=profile,
                    score=round(numeric_score, 6),
                    criteria={name: round(value, 6) for name, value in sorted(criteria.items())},
                    reasons=[_reason(name, criteria[name]) for name in top_reasons],
                    invalidation_conditions=[
                        *candidate.invalidation_conditions,
                        (
                            f"Le classement {profile.value} doit être recalculé si "
                            "le spot, l'IV, les spreads ou le budget changent"
                        ),
                    ],
                )
            )
        scores.sort(
            key=lambda score: (
                -score.score,
                next(
                    candidate.base_candidate.risk.maximum_loss
                    for candidate in candidates
                    if candidate.candidate_id == score.candidate_id
                ),
                score.candidate_id,
            )
        )
        selected = scores[: request.top]
        for rank, ranked_score in enumerate(selected, start=1):
            candidate = next(
                item for item in candidates if item.candidate_id == ranked_score.candidate_id
            )
            candidate.selection_reasons.append(
                f"Classé #{rank} pour le profil {profile.value} ({ranked_score.score:.2f}/100)"
            )
        rankings.append(ProfileRanking(profile=profile, scores=selected))
    return rankings
