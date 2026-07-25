"""Non-transmitting, human-readable IBKR preview tickets."""

from __future__ import annotations

from take_two_options.domain import PositionSide
from take_two_options.thesis_scanner.schemas import (
    IBKRPreviewLeg,
    IBKRPreviewTicket,
    ThesisCandidate,
    side_label,
)


def build_ibkr_previews(
    candidates: list[ThesisCandidate],
) -> list[IBKRPreviewTicket]:
    """Create one display-only ticket per admissible candidate."""
    selected_ids = {candidate.candidate_id for candidate in candidates}
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    previews: list[IBKRPreviewTicket] = []
    for candidate_id in sorted(selected_ids):
        candidate = by_id[candidate_id]
        base = candidate.base_candidate
        strategy_units = min(leg.quantity for leg in base.legs if leg.side is PositionSide.LONG)
        previews.append(
            IBKRPreviewTicket(
                candidate_id=candidate_id,
                security_type="OPT" if len(base.legs) == 1 else "BAG",
                debit_max_per_share_usd=(candidate.execution.indicative_limit_price_per_share),
                indicative_cost_per_lot_usd=round(
                    candidate.execution.total_cost_usd / strategy_units,
                    4,
                ),
                indicative_cost_eur=candidate.execution.total_cost_eur,
                quote_date=candidate.execution.quote_date,
                legs=[
                    IBKRPreviewLeg(
                        action=side_label(leg.side),
                        quantity=leg.quantity,
                        option_type="CALL",
                        occ_symbol=leg.quote.symbol,
                        strike=leg.quote.strike,
                        expiration=leg.quote.expiration,
                    )
                    for leg in base.legs
                ],
            )
        )
    return previews
