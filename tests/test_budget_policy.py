from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from take_two_options.budget import (
    BrokerCapitalContext,
    BudgetCandidate,
    BudgetPolicyV1Legacy,
    BudgetStatus,
    CapitalCap,
    CapitalCapMode,
    CapitalRequirementStatus,
    FlexibleBudgetPolicyV2,
    FXRate,
    LifecycleCapitalStatus,
    MinimumSpendPolicy,
    evaluate_budget_policy,
)
from take_two_options.candidate_generation.factory import build_candidate
from take_two_options.config.loader import load_prospective_budget_config
from take_two_options.decision.request import load_trade_request
from take_two_options.domain import OptionType, PositionSide
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import load_knowledge
from take_two_options.knowledge.schemas import Architecture, QuoteSnapshot

ROOT = Path(__file__).resolve().parents[1]

LEGACY_ARTIFACT_HASHES = {
    "reports/pre_opra/final_pre_opra_report_2026-08-08.json": (
        "cb56b9716a19224f3db7b6a92713ab95a79ec5f64000c252850778a18025634c"
    ),
    "reports/pre_opra/baseline_comparison_2026-08-08.json": (
        "d1079f0c5829a40afec467b7f4ca5982f300254d0001b7d68871b5412c1305eb"
    ),
    "reports/pre_opra/five_scores_2026-08-08.json": (
        "a09cbb759c4b9a05961fbb75966e074a54aa01f7556eb153918d5b40d068a5f4"
    ),
    "reports/M0_1_FINAL_PRE_OPRA_CORRECTION_REPORT.json": (
        "5dfcbddaa840fae19a97986190f6284caeb90a00146bdae27363f38164456430"
    ),
    "validation/final_holdout_ledger.jsonl": (
        "7081cdd91b9dfac1acdaae219ba3eecc8133c25da0d1ad63c92d1537e6c2929a"
    ),
}


def _policy(
    *,
    minimum: MinimumSpendPolicy = MinimumSpendPolicy.SOFT,
    maximum_loss_cap: CapitalCap | None = None,
) -> FlexibleBudgetPolicyV2:
    return FlexibleBudgetPolicyV2(
        currency="EUR",
        target_budget=1_000,
        under_target_tolerance=200,
        max_overspend=500,
        minimum_spend_policy=minimum,
        maximum_loss_cap=maximum_loss_cap or CapitalCap(),
        buying_power_cap=CapitalCap(),
        maximum_contracts=4,
    )


def _candidate(
    capital: float,
    *,
    candidate_id: str = "candidate",
    maximum_loss: float | None = None,
    buying_power: float | None = None,
    buying_power_required: bool = False,
) -> BudgetCandidate:
    return BudgetCandidate(
        candidate_id=candidate_id,
        architecture="long_call",
        currency="EUR",
        required_entry_cash=capital,
        maximum_loss=capital if maximum_loss is None else maximum_loss,
        buying_power_requirement=buying_power,
        buying_power_required=buying_power_required,
        buying_power_status=(
            CapitalRequirementStatus.ESTIMATED_ANALYTICAL_BOUND
            if buying_power is not None
            else CapitalRequirementStatus.UNKNOWN
            if buying_power_required
            else CapitalRequirementStatus.NOT_REQUIRED
        ),
    )


def _evaluate(
    candidate: BudgetCandidate,
    policy: FlexibleBudgetPolicyV2 | BudgetPolicyV1Legacy | None = None,
):
    return evaluate_budget_policy(candidate, policy or _policy(), None, None).diagnostics


def test_canonical_policy_derives_800_1000_1500_and_auto_caps() -> None:
    policy = _policy()

    assert policy.preferred_lower_bound == 800
    assert policy.target_budget == 1_000
    assert policy.hard_authorized_ceiling == 1_500
    assert policy.maximum_loss_cap_effective == 1_500
    assert policy.buying_power_cap_effective == 1_500
    assert policy.budget_policy_version == "2.0"


def test_prospective_phase_m_config_is_v2_and_does_not_start_opra() -> None:
    config = load_prospective_budget_config(
        ROOT / "configs/phase_m/v2/ttwo_prospective_budget.yaml"
    )
    assert config.budget_policy.preferred_lower_bound == 800
    assert config.budget_policy.hard_authorized_ceiling == 1_500
    assert config.holdout_status == "UNOPENED"
    assert config.opra_status == "NOT_STARTED"
    assert config.read_only is True
    assert config.transmit is False
    assert config.order_capability == "forbidden"


def test_policy_clips_lower_bound_and_rejects_negative_inputs() -> None:
    policy = FlexibleBudgetPolicyV2(
        currency="eur",
        target_budget=100,
        under_target_tolerance=200,
        max_overspend=0,
        maximum_contracts=1,
    )
    assert policy.currency == "EUR"
    assert policy.preferred_lower_bound == 0

    with pytest.raises(ValidationError):
        FlexibleBudgetPolicyV2(
            currency="EUR",
            target_budget=-1,
            under_target_tolerance=0,
            max_overspend=0,
            maximum_contracts=1,
        )
    with pytest.raises(ValidationError):
        FlexibleBudgetPolicyV2(
            currency="EUR",
            target_budget=1,
            under_target_tolerance=-1,
            max_overspend=0,
            maximum_contracts=1,
        )


@pytest.mark.parametrize(
    ("capital", "status"),
    [
        (600, BudgetStatus.BELOW_PREFERRED_RANGE),
        (800, BudgetStatus.WITHIN_PREFERRED_RANGE),
        (1_000, BudgetStatus.WITHIN_PREFERRED_RANGE),
        (1_001, BudgetStatus.ABOVE_TARGET_WITHIN_TOLERANCE),
        (1_499, BudgetStatus.ABOVE_TARGET_WITHIN_TOLERANCE),
        (1_500, BudgetStatus.AT_HARD_CEILING),
        (1_500.01, BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING),
    ],
)
def test_exact_budget_status_boundaries(capital: float, status: BudgetStatus) -> None:
    diagnostics = _evaluate(_candidate(capital))
    assert diagnostics.budget_status is status
    assert diagnostics.eligible is (status is not BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING)


def test_lower_bound_is_soft_hard_or_off_without_forcing_more_spend() -> None:
    soft = _evaluate(_candidate(700), _policy(minimum=MinimumSpendPolicy.SOFT))
    hard = _evaluate(_candidate(700), _policy(minimum=MinimumSpendPolicy.HARD))
    off = _evaluate(_candidate(700), _policy(minimum=MinimumSpendPolicy.OFF))

    assert soft.budget_status is BudgetStatus.BELOW_PREFERRED_RANGE
    assert soft.eligible
    assert hard.budget_status is BudgetStatus.BELOW_PREFERRED_RANGE
    assert not hard.eligible
    assert "BELOW_HARD_MINIMUM_SPEND" in hard.reason_codes
    assert off.budget_status is BudgetStatus.WITHIN_PREFERRED_RANGE
    assert off.eligible


def test_each_integer_quantity_has_its_own_capital_and_status() -> None:
    evaluations = [
        _evaluate(
            _candidate(
                540 * quantity,
                candidate_id=f"quantity-{quantity}",
            )
        )
        for quantity in range(1, 4)
    ]

    assert [item.effective_capital_requirement for item in evaluations] == [540, 1_080, 1_620]
    assert [item.eligible for item in evaluations] == [True, True, False]


def test_factory_evaluates_540_per_unit_as_distinct_whole_contract_candidates() -> None:
    request = load_trade_request(ROOT / "configs/trades/ttwo_gta6_1000eur.yaml").model_copy(
        update={
            "currency": "USD",
            "budget": 1_000.0,
            "maximum_loss": 1_000.0,
            "fx_rate_to_usd": None,
            "fx_rate_as_of": None,
        }
    )
    catalog = compile_knowledge(load_knowledge(ROOT / "research/knowledge_items"))
    recipe = next(item for item in catalog.recipes if item.architecture is Architecture.LONG_CALL)
    quote = QuoteSnapshot(
        symbol="TTWO270820C00100000",
        expiration=date(2027, 8, 20),
        option_type=OptionType.CALL,
        strike=100,
        bid=5.30,
        ask=5.393,
        volume=100,
        open_interest=500,
        implied_volatility=0.30,
        quote_timestamp=datetime(2026, 8, 24, 20, tzinfo=UTC),
        multiplier=100,
        price_quality="eod_bid_ask",
        source_id="unit-test",
    )
    usd_policy = _policy().model_copy(update={"currency": "USD"})
    candidates = [
        build_candidate(
            architecture=Architecture.LONG_CALL,
            recipe=recipe,
            leg_specs=[(PositionSide.LONG, 1, quote)],
            quantity=quantity,
            request=request,
            horizon_compatible=True,
            budget_policy=usd_policy,
        )
        for quantity in range(1, 4)
    ]

    assert len({candidate.candidate_id for candidate in candidates}) == 3
    assert [candidate.legs[0].quantity for candidate in candidates] == [1, 2, 3]
    assert [
        candidate.budget_diagnostics.effective_capital_requirement  # type: ignore[union-attr]
        for candidate in candidates
    ] == pytest.approx([540, 1_080, 1_620])
    assert [
        candidate.budget_diagnostics.eligible  # type: ignore[union-attr]
        for candidate in candidates
    ] == [True, True, False]


@pytest.mark.parametrize(
    ("architecture", "front_strike"),
    [
        (Architecture.CALL_CALENDAR, 100.0),
        (Architecture.CALL_DIAGONAL, 110.0),
    ],
)
def test_factory_mixed_expiry_v2_excludes_common_expiry_proxy(
    architecture: Architecture,
    front_strike: float,
) -> None:
    request = load_trade_request(
        ROOT / "configs/trades/ttwo_gta6_1000eur.yaml"
    ).model_copy(
        update={
            "currency": "USD",
            "budget": 1_000.0,
            "maximum_loss": 1_000.0,
            "fx_rate_to_usd": None,
            "fx_rate_as_of": None,
        }
    )
    catalog = compile_knowledge(load_knowledge(ROOT / "research/knowledge_items"))
    recipe = next(item for item in catalog.recipes if item.architecture is architecture)
    common_quote = {
        "option_type": OptionType.CALL,
        "volume": 100,
        "open_interest": 500,
        "implied_volatility": 0.30,
        "quote_timestamp": datetime(2026, 8, 24, 20, tzinfo=UTC),
        "multiplier": 100,
        "price_quality": "eod_bid_ask",
        "source_id": "unit-test",
    }
    back = QuoteSnapshot(
        symbol="TTWO280121C00100000",
        expiration=date(2028, 1, 21),
        strike=100,
        bid=5.30,
        ask=5.50,
        **common_quote,
    )
    front = QuoteSnapshot(
        symbol=f"TTWO270820C{int(front_strike * 1000):08d}",
        expiration=date(2027, 8, 20),
        strike=front_strike,
        bid=2.00,
        ask=2.20,
        **common_quote,
    )
    candidate = build_candidate(
        architecture=architecture,
        recipe=recipe,
        leg_specs=[
            (PositionSide.LONG, 1, back),
            (PositionSide.SHORT, 1, front),
        ],
        quantity=1,
        request=request,
        horizon_compatible=True,
        budget_policy=_policy().model_copy(update={"currency": "USD"}),
    )

    assert candidate.risk.maximum_loss > 0  # Legacy proxy retained for V1 reproduction.
    assert candidate.budget_diagnostics is not None
    assert candidate.budget_diagnostics.maximum_loss is None
    assert candidate.budget_diagnostics.budget_status is (
        BudgetStatus.BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN
    )
    assert candidate.lifecycle_capital_requirement is not None
    assert candidate.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.UNKNOWN
    )
    assert "BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN" in candidate.research_restrictions


def test_debit_entry_cash_uses_executable_premium_plus_all_entry_costs() -> None:
    executable_ask = 820
    slippage = 8
    commission = 1
    fx_cost = 3
    diagnostics = _evaluate(_candidate(executable_ask + slippage + commission + fx_cost))
    assert diagnostics.required_entry_cash == 832


def test_credit_trade_uses_loss_and_buying_power_not_negative_cash() -> None:
    candidate = BudgetCandidate(
        candidate_id="credit-spread",
        architecture="credit_spread",
        currency="EUR",
        required_entry_cash=-120,
        maximum_loss=760,
        buying_power_requirement=780,
        buying_power_required=True,
        buying_power_status=CapitalRequirementStatus.ESTIMATED_ANALYTICAL_BOUND,
    )
    eligible = _evaluate(candidate)
    assert eligible.required_entry_cash == 0
    assert eligible.effective_capital_requirement == 780
    assert eligible.eligible

    blocked = _evaluate(candidate.model_copy(update={"buying_power_requirement": 1_600}))
    assert blocked.budget_status is BudgetStatus.BUYING_POWER_EXCEEDED
    assert not blocked.eligible


def test_unknown_margin_remains_null_and_blocks_paper_only() -> None:
    candidate = BudgetCandidate(
        candidate_id="credit-unknown-margin",
        architecture="iron_condor",
        currency="EUR",
        required_entry_cash=-100,
        maximum_loss=700,
        buying_power_required=True,
        buying_power_status=CapitalRequirementStatus.UNKNOWN,
    )
    diagnostics = _evaluate(candidate)
    assert diagnostics.buying_power_requirement is None
    assert diagnostics.budget_status is BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN
    assert diagnostics.research_eligible
    assert not diagnostics.paper_eligible


def test_unknown_maximum_loss_remains_null_and_cannot_authorize_paper() -> None:
    candidate = BudgetCandidate(
        candidate_id="unknown-loss",
        architecture="bounded_candidate_pending_proof",
        currency="EUR",
        required_entry_cash=500,
        maximum_loss=None,
    )
    diagnostics = _evaluate(candidate)
    assert diagnostics.maximum_loss is None
    assert diagnostics.budget_status is BudgetStatus.CAPITAL_REQUIREMENT_UNKNOWN
    assert not diagnostics.paper_eligible


@pytest.mark.parametrize("architecture", ["call_calendar", "call_diagonal"])
def test_mixed_expiry_v2_never_uses_legacy_common_expiry_proxy(
    architecture: str,
) -> None:
    candidate = BudgetCandidate(
        candidate_id=architecture,
        architecture=architecture,
        currency="EUR",
        required_entry_cash=400,
        maximum_loss=None,
        buying_power_required=True,
        buying_power_status=CapitalRequirementStatus.UNKNOWN,
        mixed_expiry=True,
        managed_exit_deadline=date(2027, 1, 14),
        legacy_common_expiry_maximum_loss=200,
    )
    evaluation = evaluate_budget_policy(candidate, _policy(), None, None)

    assert evaluation.diagnostics.maximum_loss is None
    assert evaluation.diagnostics.budget_status is (
        BudgetStatus.BLOCKED_MIXED_EXPIRY_CAPITAL_UNPROVEN
    )
    assert evaluation.diagnostics.research_eligible
    assert not evaluation.diagnostics.paper_eligible
    assert evaluation.lifecycle_capital_requirement is not None
    assert evaluation.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.UNKNOWN
    )
    assert any(
        "LEGACY_COMMON_EXPIRY_PROXY" in warning
        for warning in evaluation.lifecycle_capital_requirement.warnings
    )


def test_validated_broker_buying_power_can_prove_mixed_expiry_capital() -> None:
    candidate = BudgetCandidate(
        candidate_id="calendar",
        architecture="call_calendar",
        currency="EUR",
        required_entry_cash=400,
        buying_power_required=True,
        buying_power_status=CapitalRequirementStatus.UNKNOWN,
        as_of=datetime(2026, 8, 24, 20, tzinfo=UTC),
        mixed_expiry=True,
        managed_exit_deadline=date(2027, 1, 14),
    )
    broker = BrokerCapitalContext(
        buying_power_requirement=900,
        currency="EUR",
        source="IBKR what-if fixture",
        timestamp=datetime(2026, 8, 24, 12, tzinfo=UTC),
        validated=True,
    )
    evaluation = evaluate_budget_policy(candidate, _policy(), None, broker)

    assert evaluation.diagnostics.paper_eligible
    assert evaluation.diagnostics.effective_capital_requirement == 900
    assert evaluation.lifecycle_capital_requirement is not None
    assert evaluation.lifecycle_capital_requirement.calculation_status is (
        LifecycleCapitalStatus.BROKER_BUYING_POWER
    )


def test_fx_is_required_then_applied_with_point_in_time_provenance() -> None:
    candidate = BudgetCandidate(
        candidate_id="usd-long",
        architecture="long_call",
        currency="USD",
        required_entry_cash=1_200,
        maximum_loss=1_200,
        as_of=datetime(2026, 8, 24, 20, tzinfo=UTC),
    )
    missing = evaluate_budget_policy(candidate, _policy(), None, None).diagnostics
    assert missing.budget_status is BudgetStatus.FX_REQUIRED
    assert not missing.paper_eligible

    fx = FXRate(
        source_currency="USD",
        policy_currency="EUR",
        rate_to_policy_currency=0.8,
        timestamp=datetime(2026, 8, 24, 12, tzinfo=UTC),
        source="PIT test FX",
    )
    converted = evaluate_budget_policy(candidate, _policy(), fx, None).diagnostics
    assert converted.required_entry_cash == pytest.approx(960)
    assert converted.budget_status is BudgetStatus.WITHIN_PREFERRED_RANGE
    assert converted.fx_source == "PIT test FX"

    future_fx = fx.model_copy(
        update={"timestamp": datetime(2026, 8, 25, 12, tzinfo=UTC)}
    )
    rejected_future = evaluate_budget_policy(
        candidate, _policy(), future_fx, None
    ).diagnostics
    assert rejected_future.budget_status is BudgetStatus.FX_REQUIRED
    assert any("after the candidate cutoff" in warning for warning in rejected_future.warnings)

    stronger_euro = fx.model_copy(update={"rate_to_policy_currency": 1.3})
    reclassified = evaluate_budget_policy(candidate, _policy(), stronger_euro, None).diagnostics
    assert reclassified.budget_status is BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING


def test_fees_and_slippage_can_push_entry_above_hard_ceiling() -> None:
    diagnostics = _evaluate(_candidate(1_490 + 20))
    assert diagnostics.required_entry_cash == 1_510
    assert diagnostics.budget_status is BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING


def test_maximum_loss_is_an_independent_gate_and_custom_cap_wins() -> None:
    auto = _evaluate(_candidate(900, maximum_loss=1_550))
    assert auto.budget_status is BudgetStatus.MAXIMUM_LOSS_EXCEEDED

    explicit = CapitalCap(mode=CapitalCapMode.EXPLICIT, value=1_100)
    custom = _evaluate(
        _candidate(1_000, maximum_loss=1_250),
        _policy(maximum_loss_cap=explicit),
    )
    assert custom.budget_status is BudgetStatus.MAXIMUM_LOSS_EXCEEDED


def test_no_position_remains_eligible_even_with_hard_minimum() -> None:
    candidate = BudgetCandidate(
        candidate_id="no-position",
        architecture="no_position",
        currency="EUR",
        required_entry_cash=0,
        maximum_loss=0,
        quantity=0,
        is_no_position=True,
    )
    diagnostics = _evaluate(candidate, _policy(minimum=MinimumSpendPolicy.HARD))
    assert diagnostics.eligible
    assert diagnostics.paper_eligible


def test_legacy_policy_retains_budget_loss_and_reserve_semantics() -> None:
    legacy = BudgetPolicyV1Legacy(
        currency="EUR",
        budget=1_000,
        maximum_loss=1_000,
        safety_reserve_fraction=0.05,
        maximum_contracts=4,
    )
    diagnostics = _evaluate(_candidate(960), legacy)
    assert legacy.deployable_budget == 950
    assert diagnostics.budget_policy_version == "1.0"
    assert diagnostics.budget_status is BudgetStatus.EXCEEDS_HARD_BUDGET_CEILING


def test_v2_does_not_rewrite_historical_pre_opra_or_holdout_artifacts() -> None:
    for relative_path, expected_hash in LEGACY_ARTIFACT_HASHES.items():
        actual_hash = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash
