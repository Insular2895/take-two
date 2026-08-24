"""Export a canonical trade-economics ticket as an immutable cloud dossier."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from functools import reduce
from pathlib import Path
from typing import Any

from take_two_options.cloud.contracts import (
    CloudCloseAction,
    CloudExitPlan,
    CloudFiveScoreSnapshot,
    CloudFlatSpotDiagnostics,
    CloudFXContext,
    CloudFXCostStatus,
    CloudLegSide,
    CloudModelSnapshot,
    CloudPositionDossier,
    CloudPositionLeg,
    CloudPositionState,
    CloudScoreValue,
)
from take_two_options.trade_economics_models import TradeEconomicsTicket


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _is_sha256(value: str | None) -> bool:
    return (
        value is not None
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _git_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _score_value(value: Any) -> CloudScoreValue:
    return CloudScoreValue(
        score_value=value.score_value,
        coverage=value.score_coverage,
        confidence=value.confidence,
        formula_version=value.formula_version,
    )


def _five_scores(ticket: TradeEconomicsTicket) -> CloudFiveScoreSnapshot | None:
    scores = ticket.five_scores
    if scores is None:
        return None
    return CloudFiveScoreSnapshot(
        opportunity=_score_value(scores.opportunity),
        risk=_score_value(scores.risk),
        evidence=_score_value(scores.evidence),
        model_agreement=_score_value(scores.model_agreement),
        execution_quality=_score_value(scores.execution_quality),
        source=scores.source,
        scope=scores.scope,
        timestamp=scores.generated_at,
    )


def _model_snapshot(ticket: TradeEconomicsTicket) -> CloudModelSnapshot | None:
    distribution = ticket.distribution_pnl
    if distribution is None or distribution.expected_pnl is None:
        return None
    return CloudModelSnapshot(
        timestamp=(
            ticket.five_scores.generated_at if ticket.five_scores else ticket.exact_market_timestamp
        ),
        source=distribution.model or "canonical_trade_economics_ticket",
        status=distribution.calibration_status.value,
        expected_remaining_pnl=distribution.expected_pnl,
        probability_profit=distribution.probability_profit,
        loss_probabilities={
            key: value
            for key, value in {
                "loss_25": distribution.probability_loss_25,
                "loss_50": distribution.probability_loss_50,
                "loss_70": distribution.probability_loss_70,
                "loss_90": distribution.probability_loss_90,
            }.items()
            if value is not None
        },
        var_95=distribution.var_95,
        cvar_95=distribution.cvar_95,
        assumptions=list(distribution.assumptions),
    )


def _signed_entry_cash_flow_policy(ticket: TradeEconomicsTicket) -> float:
    """Return the opening account cash flow using receipt-positive semantics.

    TradeEconomicsTicket uses the established cost convention where a debit is positive and a
    credit is negative.  The cloud control plane uses the account convention, so the final value
    is its additive inverse after the canonical policy-currency conversion and FX execution cost.
    """
    native_cost_flow = ticket.entry_cost.total_entry_cash_flow
    if native_cost_flow is None or not math.isfinite(native_cost_flow):
        raise ValueError("ENTRY_CASH_FLOW_SIGN_UNPROVEN")
    diagnostics = ticket.budget_diagnostics
    policy_currency = diagnostics.currency if diagnostics is not None else ticket.currency
    if policy_currency == ticket.currency:
        return -native_cost_flow
    if (
        diagnostics is None
        or diagnostics.native_entry_cash is None
        or diagnostics.fx_rate_to_policy_currency is None
        or diagnostics.entry_fx_cost is None
    ):
        raise ValueError("ENTRY_CASH_FLOW_SIGN_UNPROVEN")
    expected_native_before_policy_fx = native_cost_flow - (ticket.entry_cost.entry_fx_cost or 0.0)
    if not math.isclose(
        diagnostics.native_entry_cash,
        expected_native_before_policy_fx,
        rel_tol=0.0,
        abs_tol=1e-8,
    ):
        raise ValueError("ENTRY_CASH_FLOW_SIGN_UNPROVEN")
    policy_cost_flow = (
        diagnostics.native_entry_cash * diagnostics.fx_rate_to_policy_currency
        + diagnostics.entry_fx_cost
    )
    return -policy_cost_flow


def _capital_required_policy(ticket: TradeEconomicsTicket) -> float:
    diagnostics = ticket.budget_diagnostics
    requirement = diagnostics.effective_capital_requirement if diagnostics is not None else None
    if requirement is None or not math.isfinite(requirement) or requirement < 0:
        raise ValueError("CAPITAL_REQUIREMENT_UNPROVEN")
    return requirement


def build_cloud_position_dossier(
    ticket: TradeEconomicsTicket,
    *,
    ticket_bytes: bytes,
    repository_root: Path,
    initial_state: CloudPositionState = CloudPositionState.PLANNED,
) -> CloudPositionDossier:
    """Map canonical fields without repricing or recalculating financial outputs."""
    if ticket.underlying_spot is None:
        raise ValueError("ticket must contain underlying_spot for a cloud position export")
    if not ticket.legs:
        raise ValueError("cloud position export requires at least one option leg")
    structure_quantity = reduce(math.gcd, (leg.quantity for leg in ticket.legs))
    multiplier = ticket.legs[0].multiplier
    legs: list[CloudPositionLeg] = []
    for index, leg in enumerate(ticket.legs, start=1):
        if leg.instrument_type != "option" or leg.option_type is None or leg.strike is None:
            raise ValueError("CF0 supports complete option structures only")
        identity = leg.local_symbol or (f"conid:{leg.con_id}" if leg.con_id else "")
        if not identity:
            raise ValueError("every exported leg requires local_symbol or con_id")
        side = CloudLegSide.LONG if leg.side == "long" else CloudLegSide.SHORT
        legs.append(
            CloudPositionLeg(
                leg_id=f"leg-{index}",
                contract_identity=identity,
                con_id=leg.con_id,
                local_symbol=leg.local_symbol,
                underlying=ticket.underlying,
                side=side,
                close_action=(
                    CloudCloseAction.SELL_TO_CLOSE
                    if side is CloudLegSide.LONG
                    else CloudCloseAction.BUY_TO_CLOSE
                ),
                ratio=leg.quantity // structure_quantity,
                quantity=leg.quantity,
                multiplier=leg.multiplier,
                option_right=leg.option_type.upper(),
                strike=leg.strike,
                expiration=leg.expiration,
                entry_bid=leg.bid,
                entry_ask=leg.ask,
                entry_mid=leg.mid,
                entry_executable_price=(leg.ask if side is CloudLegSide.LONG else leg.bid),
            )
        )
    if any(leg.multiplier != multiplier for leg in ticket.legs):
        raise ValueError("cloud dossier requires one consistent contract multiplier")
    diagnostics = ticket.budget_diagnostics
    policy_currency = diagnostics.currency if diagnostics is not None else ticket.currency
    entry_cash_flow_policy = _signed_entry_cash_flow_policy(ticket)
    capital_required_policy = _capital_required_policy(ticket)
    fx_status = (
        diagnostics.entry_fx_cost_status.value
        if diagnostics is not None and diagnostics.entry_fx_cost_status is not None
        else "UNKNOWN"
    )
    ticket_hash = _sha256_bytes(ticket_bytes)
    config_payload = {
        "budget": diagnostics.model_dump(mode="json") if diagnostics is not None else None,
        "lifecycle_policy": ticket.lifecycle_policy,
        "lifecycle_source": ticket.lifecycle_config_source,
        "lifecycle_version": ticket.lifecycle_config_version,
        "exit_cost": ticket.exit_cost_estimate.model_dump(mode="json"),
    }
    has_canonical_config_hash = ticket.five_scores is not None and _is_sha256(
        ticket.five_scores.config_hash
    )
    config_hash = (
        ticket.five_scores.config_hash
        if has_canonical_config_hash and ticket.five_scores is not None
        else _stable_hash(config_payload)
    )
    market_payload = {
        "ticker": ticket.underlying,
        "spot": ticket.underlying_spot,
        "timestamp": ticket.exact_market_timestamp,
        "legs": [
            {
                "identity": leg.contract_identity,
                "bid": leg.entry_bid,
                "ask": leg.entry_ask,
                "iv": ticket.legs[index].implied_volatility,
            }
            for index, leg in enumerate(legs)
        ],
    }
    initial_greeks = {
        name: getattr(ticket.aggregate_greeks, name).value
        for name in ("delta", "gamma", "theta", "vega", "rho", "vanna", "vomma")
        if ticket.aggregate_greeks is not None
    }
    initial_iv = {
        leg.contract_identity: ticket.legs[index].implied_volatility
        for index, leg in enumerate(legs)
    }
    return CloudPositionDossier(
        fixture_status=(
            "CANONICAL_EXPORT" if ticket.fixture_status == "LIVE_INPUT" else "SYNTHETIC_DEMO"
        ),
        dossier_id=f"dossier-{ticket_hash[:20]}",
        position_id=f"position-{ticket.candidate_id}-{ticket_hash[:12]}",
        created_at=ticket.exact_market_timestamp,
        opened_at=ticket.exact_market_timestamp,
        initial_position_state=initial_state,
        ticker=ticket.underlying,
        structure_name=ticket.strategy_name,
        structure_type=ticket.candidate_id,
        legs=legs,
        quantity=structure_quantity,
        multiplier=multiplier,
        entry_native_currency=ticket.currency,
        policy_currency=policy_currency,
        entry_cash_flow_policy=entry_cash_flow_policy,
        capital_required_policy=capital_required_policy,
        actual_entry_fx=CloudFXContext(
            rate_to_policy_currency=(diagnostics.fx_rate if diagnostics else None),
            rate_source=(diagnostics.fx_rate_source if diagnostics else None),
            rate_timestamp=(diagnostics.fx_timestamp if diagnostics else None),
            transaction_cost=(diagnostics.entry_fx_cost if diagnostics else None),
            transaction_cost_status=CloudFXCostStatus(fx_status),
            transaction_cost_source=(diagnostics.fx_cost_source if diagnostics else None),
        ),
        actual_entry_commissions=ticket.entry_cost.entry_commission or 0.0,
        actual_entry_slippage=ticket.entry_cost.entry_slippage or 0.0,
        initial_spot=ticket.underlying_spot,
        initial_iv=initial_iv,
        initial_greeks=initial_greeks,
        expirations=ticket.expirations,
        managed_exit_deadline=ticket.managed_exit_deadline,
        initial_scenario_probabilities=None,
        latest_promoted_model_snapshot=_model_snapshot(ticket),
        flat_spot_diagnostics=(
            CloudFlatSpotDiagnostics(
                timestamp=ticket.exact_market_timestamp,
                source="TradeEconomicsTicket.time_decay",
                flat_spot_7d=ticket.time_decay.flat_spot_7d,
                flat_spot_30d=ticket.time_decay.flat_spot_30d,
                flat_spot_60d=ticket.time_decay.flat_spot_60d,
                flat_spot_90d=ticket.time_decay.flat_spot_90d,
            )
            if ticket.time_decay is not None
            else None
        ),
        five_scores=_five_scores(ticket),
        budget_diagnostics=(diagnostics.model_dump(mode="json") if diagnostics else {}),
        exit_plan=CloudExitPlan(status="NOT_CONFIGURED"),
        trade_economics_ticket_hash=ticket_hash,
        trade_economics_schema_version=ticket.schema_version,
        phase_m_context_id=ticket.phase_m_context_id,
        phase_m_context_hash=ticket.phase_m_context_hash,
        git_commit=_git_commit(repository_root),
        config_hash=config_hash,
        config_hash_source=(
            "FiveScoreSnapshot.config_hash"
            if has_canonical_config_hash
            else "canonical_cloud_export_configuration_projection"
        ),
        market_snapshot_hash=_stable_hash(market_payload),
        market_snapshot_hash_source="canonical_ticket_market_projection",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticket", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--state",
        choices=[state.value for state in CloudPositionState],
        default=CloudPositionState.PLANNED.value,
    )
    arguments = parser.parse_args()
    ticket_bytes = arguments.ticket.read_bytes()
    ticket = TradeEconomicsTicket.model_validate_json(ticket_bytes)
    root = Path(__file__).resolve().parents[3]
    dossier = build_cloud_position_dossier(
        ticket,
        ticket_bytes=ticket_bytes,
        repository_root=root,
        initial_state=CloudPositionState(arguments.state),
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(dossier.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Exported validated CloudPositionDossier to {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
