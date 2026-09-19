"""Offline control plane for a future, human-approved shadow campaign."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.knowledge.provenance import stable_hash
from take_two_options.opra.paper_decisions import (
    ImmutableStrictModel,
    PaperDecisionDraft,
    PaperDecisionRecord,
    PaperRealizationDraft,
    PaperRealizationRecord,
    append_paper_decision,
    append_paper_realization,
    build_paper_decision_record,
    build_paper_realization_record,
    load_paper_decisions,
    load_paper_realizations,
    validate_paper_decision_chain,
    validate_paper_realization_chain,
)

ShadowCheckStatus = Literal["PASS", "WARN", "FAIL", "NOT_RUN"]
ShadowCampaignStatus = Literal[
    "BLOCKED_DRAFT",
    "READY_TO_START",
    "IN_PROGRESS",
    "OBSERVATION_TARGET_REACHED_PENDING_HUMAN_REVIEW",
    "WINDOW_ENDED_INCOMPLETE",
    "FAILED_SAFE",
]
ShadowMaximumClaim = Literal[
    "software_only",
    "campaign_control_ready",
    "prospective_observations_recorded",
]


class ShadowCampaignThresholds(ImmutableStrictModel):
    """Risk-owner values; the software deliberately supplies no defaults."""

    minimum_decisions: int = Field(gt=0)
    minimum_realizations: int = Field(gt=0)
    maximum_decision_recording_delay_seconds: int = Field(gt=0)
    maximum_realization_recording_delay_seconds: int = Field(gt=0)

    @model_validator(mode="after")
    def require_coherent_counts(self) -> ShadowCampaignThresholds:
        if self.minimum_realizations > self.minimum_decisions:
            raise ValueError("minimum realizations cannot exceed minimum decisions")
        return self


class ShadowCampaignManifest(ImmutableStrictModel):
    schema_version: Literal["1.1"] = "1.1"
    campaign_id: str = Field(min_length=1)
    ticker: Literal["TTWO"] = "TTWO"
    mode: Literal["shadow_observation_only"] = "shadow_observation_only"
    planned_start_at: datetime
    planned_end_at: datetime
    approval_status: Literal["draft_to_validate", "approved"] = "draft_to_validate"
    thresholds: ShadowCampaignThresholds | None = None
    code_commit: str | None = Field(default=None, min_length=7, max_length=40)
    strategy_config_hash: str | None = Field(default=None, min_length=64, max_length=64)
    ibkr_validation_report_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    holdout_ledger_hash: str | None = Field(default=None, min_length=64, max_length=64)
    data_rights_approval_reference: str | None = Field(default=None, min_length=1)
    risk_owner_approval_reference: str | None = Field(default=None, min_length=1)
    example_only: bool = True
    transmit: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("planned_start_at", "planned_end_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("shadow campaign timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def require_approved_lineage(self) -> ShadowCampaignManifest:
        if self.planned_end_at <= self.planned_start_at:
            raise ValueError("shadow campaign end must follow its start")
        if self.approval_status == "approved":
            required = {
                "thresholds": self.thresholds,
                "code_commit": self.code_commit,
                "strategy_config_hash": self.strategy_config_hash,
                "ibkr_validation_report_hash": self.ibkr_validation_report_hash,
                "holdout_ledger_hash": self.holdout_ledger_hash,
                "data_rights_approval_reference": self.data_rights_approval_reference,
                "risk_owner_approval_reference": self.risk_owner_approval_reference,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError("approved shadow campaign requires: " + ", ".join(sorted(missing)))
            if self.example_only:
                raise ValueError("an example shadow campaign cannot be approved")
        return self


class ShadowCampaignCheck(ImmutableStrictModel):
    check_id: str = Field(min_length=1)
    status: ShadowCheckStatus
    detail_code: str = Field(min_length=1)


class ShadowCampaignStatusReport(ImmutableStrictModel):
    schema_version: Literal["1.1"] = "1.1"
    report_id: str = Field(min_length=1)
    generated_at: datetime
    campaign_id: str = Field(min_length=1)
    manifest_hash: str = Field(min_length=64, max_length=64)
    status: ShadowCampaignStatus
    maximum_claim: ShadowMaximumClaim
    decision_count: int = Field(ge=0)
    realization_count: int = Field(ge=0)
    missing_realization_count: int = Field(ge=0)
    no_position_count: int = Field(ge=0)
    decision_ledger_head_hash: str | None = Field(default=None, min_length=64, max_length=64)
    realization_ledger_head_hash: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )
    checks: tuple[ShadowCampaignCheck, ...] = Field(min_length=1)
    paper_validation_passed: Literal[False] = False
    promotion_eligible: Literal[False] = False
    human_review_required: Literal[True] = True
    transmit: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("shadow report timestamp must be timezone-aware")
        return value.astimezone(UTC)


def record_shadow_decision(
    manifest: ShadowCampaignManifest,
    draft: PaperDecisionDraft,
    ledger_path: Path,
    *,
    now: Callable[[], datetime] | None = None,
) -> PaperDecisionRecord:
    """Append one prospective decision only under an approved frozen manifest."""

    thresholds = _recording_thresholds(manifest)
    if draft.example_only:
        raise ValueError("SHADOW_DECISION_DRAFT_MARKED_EXAMPLE_ONLY")
    recorded_at = _utc((now or (lambda: datetime.now(UTC)))())
    if not manifest.planned_start_at <= recorded_at <= manifest.planned_end_at:
        raise ValueError("SHADOW_DECISION_RECORDING_OUTSIDE_CAMPAIGN_WINDOW")
    if not manifest.planned_start_at <= draft.decided_at <= manifest.planned_end_at:
        raise ValueError("SHADOW_DECISION_OUTSIDE_CAMPAIGN_WINDOW")
    if recorded_at < draft.decided_at:
        raise ValueError("SHADOW_DECISION_TIMESTAMP_IN_FUTURE")
    delay = (recorded_at - draft.decided_at).total_seconds()
    if delay > thresholds.maximum_decision_recording_delay_seconds:
        raise ValueError("SHADOW_DECISION_RECORDING_DELAY_EXCEEDED")
    if draft.code_commit != manifest.code_commit:
        raise ValueError("SHADOW_CODE_COMMIT_DRIFT")
    if draft.config_hash != manifest.strategy_config_hash:
        raise ValueError("SHADOW_CONFIG_HASH_DRIFT")
    existing = load_paper_decisions(ledger_path)
    _validate_decisions_against_manifest(manifest, existing)
    record = build_paper_decision_record(
        existing,
        draft,
        campaign_id=manifest.campaign_id,
        recorded_at=recorded_at,
    )
    append_paper_decision(
        ledger_path,
        record,
        expected_head_hash=existing[-1].record_hash if existing else None,
    )
    return record


def record_shadow_realization(
    manifest: ShadowCampaignManifest,
    draft: PaperRealizationDraft,
    decision_ledger_path: Path,
    realization_ledger_path: Path,
    *,
    now: Callable[[], datetime] | None = None,
) -> PaperRealizationRecord:
    """Append one outcome linked to an existing prospective decision."""

    thresholds = _recording_thresholds(manifest)
    if draft.example_only:
        raise ValueError("SHADOW_REALIZATION_DRAFT_MARKED_EXAMPLE_ONLY")
    recorded_at = _utc((now or (lambda: datetime.now(UTC)))())
    if recorded_at < draft.observed_at:
        raise ValueError("SHADOW_REALIZATION_TIMESTAMP_IN_FUTURE")
    delay = (recorded_at - draft.observed_at).total_seconds()
    if delay > thresholds.maximum_realization_recording_delay_seconds:
        raise ValueError("SHADOW_REALIZATION_RECORDING_DELAY_EXCEEDED")
    decisions = load_paper_decisions(decision_ledger_path)
    _validate_decisions_against_manifest(manifest, decisions)
    if not decisions:
        raise ValueError("SHADOW_REALIZATION_WITHOUT_DECISION_LEDGER")
    existing = load_paper_realizations(realization_ledger_path, decisions)
    if any(record.campaign_id != manifest.campaign_id for record in existing):
        raise ValueError("SHADOW_REALIZATION_CAMPAIGN_DRIFT")
    record = build_paper_realization_record(
        draft,
        existing=existing,
        decisions=decisions,
        campaign_id=manifest.campaign_id,
        recorded_at=recorded_at,
    )
    append_paper_realization(
        realization_ledger_path,
        record,
        expected_head_hash=existing[-1].realization_hash if existing else None,
        decisions=decisions,
    )
    return record


def evaluate_shadow_campaign(
    manifest: ShadowCampaignManifest,
    decisions: list[PaperDecisionRecord],
    realizations: list[PaperRealizationRecord],
    *,
    now: Callable[[], datetime] | None = None,
) -> ShadowCampaignStatusReport:
    """Evaluate prospective evidence without starting a provider or promoting a strategy."""

    validate_paper_decision_chain(decisions)
    validate_paper_realization_chain(realizations, decisions)
    generated_at = _utc((now or (lambda: datetime.now(UTC)))())
    checks: list[ShadowCampaignCheck] = []

    if manifest.approval_status != "approved" or manifest.example_only:
        checks.append(_check("manifest_approval", "FAIL", "SHADOW_MANIFEST_NOT_APPROVED"))
        return _report(
            manifest,
            decisions,
            realizations,
            generated_at,
            checks,
            status="BLOCKED_DRAFT",
            maximum_claim="software_only",
        )
    checks.append(_check("manifest_approval", "PASS", "SHADOW_MANIFEST_APPROVED"))

    assert manifest.thresholds is not None
    assert manifest.code_commit is not None
    assert manifest.strategy_config_hash is not None
    lineage_failures = False
    for decision in decisions:
        if not manifest.planned_start_at <= decision.decided_at <= manifest.planned_end_at:
            checks.append(
                _check("decision_window", "FAIL", "SHADOW_DECISION_OUTSIDE_CAMPAIGN_WINDOW")
            )
            lineage_failures = True
            break
    else:
        checks.append(_check("decision_window", "PASS", "SHADOW_DECISIONS_WITHIN_WINDOW"))
    for check_id, matches, passed, failed in (
        (
            "campaign_id",
            all(decision.campaign_id == manifest.campaign_id for decision in decisions)
            and all(
                realization.campaign_id == manifest.campaign_id for realization in realizations
            ),
            "SHADOW_CAMPAIGN_ID_FROZEN",
            "SHADOW_CAMPAIGN_ID_DRIFT",
        ),
        (
            "example_records",
            all(not decision.example_only for decision in decisions)
            and all(not realization.example_only for realization in realizations),
            "SHADOW_RECORDS_NOT_EXAMPLES",
            "SHADOW_EXAMPLE_RECORD_PRESENT",
        ),
        (
            "code_commit",
            all(decision.code_commit == manifest.code_commit for decision in decisions),
            "SHADOW_CODE_COMMIT_FROZEN",
            "SHADOW_CODE_COMMIT_DRIFT",
        ),
        (
            "strategy_config",
            all(decision.config_hash == manifest.strategy_config_hash for decision in decisions),
            "SHADOW_CONFIG_HASH_FROZEN",
            "SHADOW_CONFIG_HASH_DRIFT",
        ),
    ):
        checks.append(
            _check(check_id, "PASS" if matches else "FAIL", passed if matches else failed)
        )
        lineage_failures = lineage_failures or not matches
    decision_delays_valid = all(
        (decision.recorded_at - decision.decided_at).total_seconds()
        <= manifest.thresholds.maximum_decision_recording_delay_seconds
        for decision in decisions
    )
    realization_delays_valid = all(
        (realization.recorded_at - realization.observed_at).total_seconds()
        <= manifest.thresholds.maximum_realization_recording_delay_seconds
        for realization in realizations
    )
    checks.extend(
        [
            _check(
                "decision_recording_delay",
                "PASS" if decision_delays_valid else "FAIL",
                "SHADOW_DECISIONS_RECORDED_PROSPECTIVELY"
                if decision_delays_valid
                else "SHADOW_DECISION_RECORDING_DELAY_EXCEEDED",
            ),
            _check(
                "realization_recording_delay",
                "PASS" if realization_delays_valid else "FAIL",
                "SHADOW_REALIZATIONS_RECORDED_PROSPECTIVELY"
                if realization_delays_valid
                else "SHADOW_REALIZATION_RECORDING_DELAY_EXCEEDED",
            ),
        ]
    )
    lineage_failures = lineage_failures or not decision_delays_valid or not realization_delays_valid
    if lineage_failures:
        return _report(
            manifest,
            decisions,
            realizations,
            generated_at,
            checks,
            status="FAILED_SAFE",
            maximum_claim="software_only",
        )

    decision_target_met = len(decisions) >= manifest.thresholds.minimum_decisions
    realization_target_met = len(realizations) >= manifest.thresholds.minimum_realizations
    checks.extend(
        [
            _check(
                "decision_target",
                "PASS" if decision_target_met else "WARN",
                "SHADOW_DECISION_TARGET_REACHED"
                if decision_target_met
                else "SHADOW_DECISION_TARGET_PENDING",
            ),
            _check(
                "realization_target",
                "PASS" if realization_target_met else "WARN",
                "SHADOW_REALIZATION_TARGET_REACHED"
                if realization_target_met
                else "SHADOW_REALIZATION_TARGET_PENDING",
            ),
        ]
    )
    status: ShadowCampaignStatus
    maximum_claim: ShadowMaximumClaim
    if decision_target_met and realization_target_met:
        status = "OBSERVATION_TARGET_REACHED_PENDING_HUMAN_REVIEW"
        maximum_claim = "prospective_observations_recorded"
    elif generated_at < manifest.planned_start_at and not decisions and not realizations:
        status = "READY_TO_START"
        maximum_claim = "campaign_control_ready"
    elif generated_at > manifest.planned_end_at:
        status = "WINDOW_ENDED_INCOMPLETE"
        maximum_claim = "prospective_observations_recorded"
    else:
        status = "IN_PROGRESS"
        maximum_claim = (
            "prospective_observations_recorded"
            if decisions or realizations
            else "campaign_control_ready"
        )
    return _report(
        manifest,
        decisions,
        realizations,
        generated_at,
        checks,
        status=status,
        maximum_claim=maximum_claim,
    )


def _report(
    manifest: ShadowCampaignManifest,
    decisions: list[PaperDecisionRecord],
    realizations: list[PaperRealizationRecord],
    generated_at: datetime,
    checks: list[ShadowCampaignCheck],
    *,
    status: ShadowCampaignStatus,
    maximum_claim: ShadowMaximumClaim,
) -> ShadowCampaignStatusReport:
    realized = {record.decision_id for record in realizations}
    payload = {
        "generated_at": generated_at,
        "campaign_id": manifest.campaign_id,
        "manifest_hash": stable_hash(manifest.model_dump(mode="json")),
        "status": status,
        "maximum_claim": maximum_claim,
        "decision_count": len(decisions),
        "realization_count": len(realizations),
        "missing_realization_count": sum(
            decision.decision_id not in realized for decision in decisions
        ),
        "no_position_count": sum(
            decision.selected_candidate == "no_position" for decision in decisions
        ),
        "decision_ledger_head_hash": decisions[-1].record_hash if decisions else None,
        "realization_ledger_head_hash": (
            realizations[-1].realization_hash if realizations else None
        ),
        "checks": tuple(checks),
    }
    return ShadowCampaignStatusReport(
        report_id=f"shadow-status-{stable_hash(payload)[:20]}",
        **payload,
    )


def _check(
    check_id: str,
    status: ShadowCheckStatus,
    detail_code: str,
) -> ShadowCampaignCheck:
    return ShadowCampaignCheck(check_id=check_id, status=status, detail_code=detail_code)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("SHADOW_CAMPAIGN_TIMESTAMP_NAIVE")
    return value.astimezone(UTC)


def _recording_thresholds(
    manifest: ShadowCampaignManifest,
) -> ShadowCampaignThresholds:
    if manifest.approval_status != "approved" or manifest.example_only:
        raise ValueError("SHADOW_MANIFEST_NOT_APPROVED")
    if manifest.thresholds is None:
        raise ValueError("SHADOW_THRESHOLDS_MISSING")
    return manifest.thresholds


def _validate_decisions_against_manifest(
    manifest: ShadowCampaignManifest,
    decisions: list[PaperDecisionRecord],
) -> None:
    for decision in decisions:
        if decision.campaign_id != manifest.campaign_id:
            raise ValueError("SHADOW_CAMPAIGN_ID_DRIFT")
        if not manifest.planned_start_at <= decision.decided_at <= manifest.planned_end_at:
            raise ValueError("SHADOW_DECISION_OUTSIDE_CAMPAIGN_WINDOW")
        if decision.code_commit != manifest.code_commit:
            raise ValueError("SHADOW_CODE_COMMIT_DRIFT")
        if decision.config_hash != manifest.strategy_config_hash:
            raise ValueError("SHADOW_CONFIG_HASH_DRIFT")
