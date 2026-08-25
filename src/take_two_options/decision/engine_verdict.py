"""Strictly derived V10-versus-baseline development verdict."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from take_two_options.domain import StrictModel


class EngineValueVerdict(StrEnum):
    ENGINE_ADDS_VALUE = "ENGINE_ADDS_VALUE"
    ENGINE_NOT_PROVEN_SUPERIOR = "ENGINE_NOT_PROVEN_SUPERIOR"
    PROMISING_BUT_NOT_PROVEN = "PROMISING_BUT_NOT_PROVEN"
    BLOCKED_BY_DATA = "BLOCKED_BY_DATA"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class VerdictMetricSnapshot(StrictModel):
    dataset_role: Literal["full_development", "walk_forward_oos"]
    strategy: str
    observations: int = Field(gt=0)
    total_return: float
    expected_return: float
    cvar_95: float = Field(ge=0)
    maximum_drawdown: float = Field(ge=0)
    probability_profit: float = Field(ge=0, le=1)


class EngineVerdictReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    report_id: str
    ticker: str
    status: Literal["DERIVED_DEVELOPMENT_VERDICT"]
    verdict: EngineValueVerdict
    derivation_rule_version: Literal["pre-opra-engine-value-v1"]
    derivation_rule: str
    engine_full_development: VerdictMetricSnapshot
    engine_walk_forward_oos: VerdictMetricSnapshot
    best_simple_baseline_full: VerdictMetricSnapshot
    best_simple_baseline_oos: VerdictMetricSnapshot
    compared_baselines: list[str] = Field(min_length=1)
    holm_superiority_rejections: int = Field(ge=0)
    deflated_sharpe_probability: float | None = Field(default=None, ge=0, le=1)
    probability_backtest_overfitting: float | None = Field(default=None, ge=0, le=1)
    formal_sample_policy_satisfied: bool
    development_classification: str
    no_position_recommended: bool
    blockers: list[str]
    holdout_state: Literal["UNOPENED"] = "UNOPENED"
    holdout_used: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"


def derive_engine_value_verdict(
    *,
    full_engine_expected_return: float,
    full_engine_total_return: float,
    oos_engine_expected_return: float,
    oos_engine_total_return: float,
    cash_expected_return: float,
    holm_superiority_rejections: int,
    formal_sample_policy_satisfied: bool,
    holdout_used: bool,
    critical_invariant_failure: bool = False,
) -> tuple[EngineValueVerdict, str]:
    """Derive one verdict without discretionary post-result retuning."""

    if critical_invariant_failure or holdout_used:
        return (
            EngineValueVerdict.VALIDATION_FAILED,
            "A critical protocol invariant failed or the protected holdout was touched.",
        )
    stable_loss = (
        full_engine_expected_return <= cash_expected_return
        and oos_engine_expected_return <= cash_expected_return
        and full_engine_total_return < 0
        and oos_engine_total_return < 0
    )
    if stable_loss:
        return (
            EngineValueVerdict.ENGINE_NOT_PROVEN_SUPERIOR,
            "V10 underperforms cash in both full development and chronological OOS evidence.",
        )
    if (
        formal_sample_policy_satisfied
        and holm_superiority_rejections > 0
        and oos_engine_expected_return > cash_expected_return
    ):
        return (
            EngineValueVerdict.ENGINE_ADDS_VALUE,
            "Formal sample policy and multiplicity-adjusted OOS superiority conditions pass.",
        )
    if oos_engine_expected_return > cash_expected_return:
        return (
            EngineValueVerdict.PROMISING_BUT_NOT_PROVEN,
            "OOS economics are positive, but formal sample or adjusted superiority is absent.",
        )
    return (
        EngineValueVerdict.BLOCKED_BY_DATA,
        "Evidence is insufficient to distinguish V10 from cash under the registered rules.",
    )
