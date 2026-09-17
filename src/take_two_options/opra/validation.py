"""Reproducible evidence report for the future IBKR read-only connection check."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import OptionType, StrictModel
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.opra.contracts import (
    LiveChainRequest,
    LiveComboLeg,
    LiveComboQuote,
    LiveComboQuoteRequest,
    LiveOptionChainSnapshot,
    ProviderHealth,
)
from take_two_options.opra.ibkr_provider import IbkrProviderDiagnostics, IbkrProviderError


class ComboValidationLeg(StrictModel):
    """A human-selected option identity, resolved to an IBKR conId from the captured chain."""

    expiration: date
    strike: float = Field(gt=0)
    option_type: OptionType
    action: Literal["BUY", "SELL"]
    ratio: int = Field(default=1, gt=0)
    exchange: str = Field(default="SMART", min_length=1)


class ComboValidationPlan(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    candidate_id: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    legs: list[ComboValidationLeg] = Field(min_length=2)
    maximum_quote_age_seconds: int = Field(default=30, gt=0)
    example_only: bool = False

    @model_validator(mode="after")
    def require_distinct_legs(self) -> ComboValidationPlan:
        identities = {(leg.expiration, leg.strike, leg.option_type) for leg in self.legs}
        if len(identities) != len(self.legs):
            raise ValueError("combo validation legs must be distinct")
        return self


class IbkrValidationCheck(StrictModel):
    check_id: str = Field(min_length=1)
    status: Literal["PASS", "WARN", "FAIL", "NOT_RUN"]
    detail_code: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class IbkrChainValidationEvidence(StrictModel):
    snapshot_id: str
    raw_snapshot_hash: str = Field(min_length=64, max_length=64)
    provider_metadata_hash: str = Field(min_length=64, max_length=64)
    underlying_price: float = Field(gt=0)
    source_latency_milliseconds: float = Field(ge=0)
    discovered_contract_count: int = Field(ge=0)
    usable_quote_count: int = Field(ge=0)
    missing_quote_count: int = Field(ge=0)
    identity_complete_count: int = Field(ge=0)
    volume_present_count: int = Field(ge=0)
    open_interest_present_count: int = Field(ge=0)
    greeks_complete_count: int = Field(ge=0)
    provider_timestamp_count: int = Field(ge=0)
    live_option_quote_count: int = Field(ge=0)
    underlying_timestamp_verified: bool
    underlying_live: bool
    promotion_eligible: bool


class IbkrReadOnlyValidationReport(StrictModel):
    schema_version: Literal["1.1"] = "1.1"
    report_id: str
    started_at: datetime
    completed_at: datetime
    status: Literal[
        "FAILED_SAFE",
        "CAPTURED_NOT_PROMOTABLE",
        "CHAIN_PROMOTION_ELIGIBLE",
        "CHAIN_AND_COMBO_PROMOTION_ELIGIBLE",
    ]
    maximum_claim: Literal[
        "software_only",
        "broker_read_only_path_observed",
        "broker_read_only_chain_promotable",
        "broker_read_only_chain_and_combo_promotable",
    ]
    provider: str
    ticker: str
    request: LiveChainRequest
    requested_market_data_type: Literal["live", "frozen", "delayed", "delayed_frozen"]
    explicit_connection_authorized: Literal[True] = True
    broker_read_observed: bool
    provider_diagnostics: IbkrProviderDiagnostics | None = None
    independent_second_session_requested: bool
    independent_second_session_verified: bool
    checks: list[IbkrValidationCheck] = Field(min_length=1)
    chain: IbkrChainValidationEvidence | None = None
    combo: LiveComboQuote | None = None
    failure_code: str | None = None
    human_gates_still_required: list[str] = Field(
        default_factory=lambda: [
            "OPRA entitlement/account evidence",
            "licence, storage and redistribution review",
            "operator comparison with TWS",
            "risk-owner approval before shadow or paper",
        ]
    )
    transmit: Literal[False] = False
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("started_at", "completed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("validation report timestamps must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_report(self) -> IbkrReadOnlyValidationReport:
        if self.completed_at < self.started_at:
            raise ValueError("validation report completion cannot precede start")
        if self.status == "FAILED_SAFE" and not self.failure_code:
            raise ValueError("failed validation reports require a failure_code")
        if self.status != "FAILED_SAFE" and self.chain is None:
            raise ValueError("captured validation reports require chain evidence")
        if self.status == "CHAIN_AND_COMBO_PROMOTION_ELIGIBLE" and (
            self.combo is None or not self.combo.comparison_confirmed
        ):
            raise ValueError("chain-and-combo promotion requires a confirmed combo comparison")
        return self


class IbkrValidationProvider(Protocol):
    def health(self) -> ProviderHealth: ...

    def get_option_chain(self, request: LiveChainRequest) -> LiveOptionChainSnapshot: ...

    def get_combo_quote(self, request: LiveComboQuoteRequest) -> LiveComboQuote: ...


@dataclass(frozen=True)
class IbkrValidationOutcome:
    report: IbkrReadOnlyValidationReport
    snapshot: LiveOptionChainSnapshot | None


def validate_ibkr_read_only(
    provider: IbkrValidationProvider,
    request: LiveChainRequest,
    *,
    provider_name: str,
    requested_market_data_type: Literal["live", "frozen", "delayed", "delayed_frozen"],
    combo_plan: ComboValidationPlan | None = None,
    exercise_second_session: bool = True,
    now: Callable[[], datetime] | None = None,
) -> IbkrValidationOutcome:
    """Observe bounded broker reads and return evidence even when the check fails safely."""

    clock = now or (lambda: datetime.now(UTC))
    started_at = _utc(clock())
    checks: list[IbkrValidationCheck] = []
    second_session_verified = False

    plan_failure = _combo_plan_preflight(combo_plan, request)
    if plan_failure is not None:
        checks.append(_failed("combo_plan_preflight", plan_failure))
        return _failed_outcome(
            started_at,
            clock,
            provider_name,
            request,
            requested_market_data_type,
            exercise_second_session,
            checks,
            plan_failure,
            provider_diagnostics=_provider_diagnostics(provider),
        )

    try:
        first_health = provider.health()
    except (IbkrProviderError, ValueError) as error:
        checks.append(_failed("initial_health", str(error)))
        return _failed_outcome(
            started_at,
            clock,
            provider_name,
            request,
            requested_market_data_type,
            exercise_second_session,
            checks,
            str(error),
            provider_diagnostics=_provider_diagnostics(provider),
        )
    if first_health.status != "available_read_only":
        code = f"IBKR_INITIAL_HEALTH_{first_health.status.upper()}"
        checks.append(_failed("initial_health", code))
        return _failed_outcome(
            started_at,
            clock,
            provider_name,
            request,
            requested_market_data_type,
            exercise_second_session,
            checks,
            code,
            broker_read_observed=True,
            provider_diagnostics=_provider_diagnostics(provider),
        )
    checks.append(_passed("initial_health", "IBKR_PAPER_READ_ONLY_HEALTH_OK"))

    if exercise_second_session:
        try:
            second_health = provider.health()
        except (IbkrProviderError, ValueError) as error:
            checks.append(_failed("independent_second_session", str(error)))
            return _failed_outcome(
                started_at,
                clock,
                provider_name,
                request,
                requested_market_data_type,
                exercise_second_session,
                checks,
                str(error),
                broker_read_observed=True,
                provider_diagnostics=_provider_diagnostics(provider),
            )
        second_session_verified = second_health.status == "available_read_only"
        if not second_session_verified:
            code = f"IBKR_SECOND_HEALTH_{second_health.status.upper()}"
            checks.append(_failed("independent_second_session", code))
            return _failed_outcome(
                started_at,
                clock,
                provider_name,
                request,
                requested_market_data_type,
                exercise_second_session,
                checks,
                code,
                broker_read_observed=True,
                provider_diagnostics=_provider_diagnostics(provider),
            )
        checks.append(_passed("independent_second_session", "IBKR_INDEPENDENT_SECOND_SESSION_OK"))
    else:
        checks.append(
            IbkrValidationCheck(
                check_id="independent_second_session",
                status="NOT_RUN",
                detail_code="IBKR_SECOND_SESSION_NOT_REQUESTED",
            )
        )

    try:
        snapshot = provider.get_option_chain(request)
    except (IbkrProviderError, ValueError) as error:
        checks.append(_failed("option_chain_capture", str(error)))
        return _failed_outcome(
            started_at,
            clock,
            provider_name,
            request,
            requested_market_data_type,
            exercise_second_session,
            checks,
            str(error),
            broker_read_observed=True,
            independent_second_session_verified=second_session_verified,
            provider_diagnostics=_provider_diagnostics(provider),
        )

    checks.append(
        _passed(
            "option_chain_capture",
            "IBKR_OPTION_CHAIN_CAPTURED",
            snapshot.snapshot_id,
            f"usable_quotes={len(snapshot.quotes)}",
        )
    )
    chain = _chain_evidence(snapshot)
    _append_chain_checks(checks, snapshot, chain)

    combo: LiveComboQuote | None = None
    if combo_plan is None:
        checks.append(
            IbkrValidationCheck(
                check_id="bag_combo_quote",
                status="NOT_RUN",
                detail_code="IBKR_COMBO_PLAN_NOT_PROVIDED",
            )
        )
    else:
        try:
            combo_request = _resolve_combo_plan(combo_plan, snapshot, clock())
            combo = provider.get_combo_quote(combo_request)
        except (IbkrProviderError, ValueError) as error:
            checks.append(_failed("bag_combo_quote", str(error)))
        else:
            checks.append(
                IbkrValidationCheck(
                    check_id="bag_combo_quote",
                    status="PASS" if combo.comparison_confirmed else "WARN",
                    detail_code=(
                        "IBKR_BAG_COMPARISON_CONFIRMED"
                        if combo.comparison_confirmed
                        else "IBKR_BAG_OBSERVED_NOT_CONFIRMED"
                    ),
                    evidence=[combo.source_id],
                )
            )

    status, maximum_claim, failure_code = _final_status(checks, snapshot, combo, combo_plan)
    completed_at = _utc(clock())
    payload = {
        "started_at": started_at,
        "completed_at": completed_at,
        "status": status,
        "maximum_claim": maximum_claim,
        "provider": provider_name,
        "ticker": request.ticker.upper(),
        "request": request,
        "requested_market_data_type": requested_market_data_type,
        "broker_read_observed": True,
        "provider_diagnostics": _provider_diagnostics(provider),
        "independent_second_session_requested": exercise_second_session,
        "independent_second_session_verified": second_session_verified,
        "checks": checks,
        "chain": chain,
        "combo": combo,
        "failure_code": failure_code,
    }
    report = IbkrReadOnlyValidationReport(
        report_id=f"ibkr-validation-{stable_hash(payload)[:20]}",
        **payload,
    )
    return IbkrValidationOutcome(report=report, snapshot=snapshot)


def render_ibkr_validation_markdown(report: IbkrReadOnlyValidationReport) -> str:
    """Render a compact human review without account, host, client ID or credentials."""

    lines = [
        "# Validation IBKR read-only",
        "",
        f"- Rapport : `{report.report_id}`",
        f"- Statut : `{report.status}`",
        f"- Preuve maximale : `{report.maximum_claim}`",
        f"- Provider : `{report.provider}`",
        f"- Ticker : `{report.ticker}`",
        f"- Expirations demandées : `{report.request.expiration_start}` → "
        f"`{report.request.expiration_end}`",
        f"- Strikes demandés : `{report.request.minimum_strike}` → "
        f"`{report.request.maximum_strike}`",
        f"- Type demandé : `{report.requested_market_data_type}`",
        f"- Lecture broker observée : `{report.broker_read_observed}`",
        f"- Seconde session indépendante : `{report.independent_second_session_verified}`",
        "- Transmission : `false`",
        "- Capacité d’ordre : `forbidden`",
        "",
        "## Contrôles",
        "",
        "| Contrôle | Statut | Code |",
        "|---|---:|---|",
    ]
    lines.extend(
        f"| `{item.check_id}` | `{item.status}` | `{item.detail_code}` |" for item in report.checks
    )
    if report.provider_diagnostics is not None:
        diagnostics = report.provider_diagnostics
        lines.extend(
            [
                "",
                "## Reprise, pacing et cache",
                "",
                f"- Lectures logiques : `{diagnostics.read_operations}`",
                f"- Tentatives transport : `{diagnostics.transport_attempts}`",
                f"- Erreurs transitoires : `{diagnostics.transient_failures}`",
                f"- Retries épuisés : `{diagnostics.retry_exhaustions}`",
                f"- Attentes de pacing : `{diagnostics.pacing_wait_count}`",
                f"- Temps de pacing : `{diagnostics.pacing_wait_seconds}` s",
                f"- Cache hits/misses : `{diagnostics.cache_hits}` / `{diagnostics.cache_misses}`",
                f"- Cache expiré : `{diagnostics.cache_expirations}`",
                f"- Repli vers donnée périmée : `{diagnostics.stale_fallbacks}`",
            ]
        )
    if report.chain is not None:
        chain = report.chain
        lines.extend(
            [
                "",
                "## Chaîne observée",
                "",
                f"- Snapshot : `{chain.snapshot_id}`",
                f"- Sous-jacent : `{chain.underlying_price}`",
                f"- Latence source : `{chain.source_latency_milliseconds}` ms",
                f"- Contrats découverts : `{chain.discovered_contract_count}`",
                f"- Quotes utilisables : `{chain.usable_quote_count}`",
                f"- Quotes manquantes : `{chain.missing_quote_count}`",
                f"- Identités complètes : `{chain.identity_complete_count}`",
                f"- Volume présent : `{chain.volume_present_count}`",
                f"- Open interest présent : `{chain.open_interest_present_count}`",
                f"- Greeks complets : `{chain.greeks_complete_count}`",
                f"- Timestamps provider/exchange : `{chain.provider_timestamp_count}`",
                f"- Options live : `{chain.live_option_quote_count}`",
                f"- Sous-jacent live et horodaté provider : "
                f"`{chain.underlying_live and chain.underlying_timestamp_verified}`",
                f"- Éligible à la promotion data : `{chain.promotion_eligible}`",
            ]
        )
    if report.combo is not None:
        lines.extend(
            [
                "",
                "## BAG observée",
                "",
                f"- Source : `{report.combo.source_id}`",
                f"- Bid/ask broker : `{report.combo.bid_net_debit}` / "
                f"`{report.combo.ask_net_debit}`",
                f"- Bid/ask synthétique : `{report.combo.synthetic_bid_net_debit}` / "
                f"`{report.combo.synthetic_ask_net_debit}`",
                f"- Divergence maximale : `{report.combo.maximum_absolute_divergence}`",
                f"- Fraîcheur vérifiée : `{report.combo.quote_freshness_verified}`",
                f"- Convention signée vérifiée : `{report.combo.price_convention_verified}`",
                f"- Comparaison confirmée : `{report.combo.comparison_confirmed}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Validations humaines toujours requises",
            "",
            *(f"- {item}" for item in report.human_gates_still_required),
            "",
            "> Ce rapport prouve au maximum un chemin de lecture broker observé. Il ne valide "
            "ni stratégie, ni rentabilité, ni exécution.",
            "",
        ]
    )
    return "\n".join(lines)


def _chain_evidence(snapshot: LiveOptionChainSnapshot) -> IbkrChainValidationEvidence:
    quotes = snapshot.quotes
    return IbkrChainValidationEvidence(
        snapshot_id=snapshot.snapshot_id,
        raw_snapshot_hash=snapshot.raw_snapshot_hash,
        provider_metadata_hash=snapshot.provider_metadata_hash,
        underlying_price=snapshot.underlying_price,
        source_latency_milliseconds=snapshot.source_latency_milliseconds,
        discovered_contract_count=snapshot.requested_contract_count or 0,
        usable_quote_count=len(quotes),
        missing_quote_count=snapshot.missing_quote_count,
        identity_complete_count=sum(
            quote.con_id is not None
            and bool(quote.local_symbol)
            and bool(quote.trading_class)
            and quote.multiplier > 0
            for quote in quotes
        ),
        volume_present_count=sum(quote.volume is not None for quote in quotes),
        open_interest_present_count=sum(quote.open_interest is not None for quote in quotes),
        greeks_complete_count=sum(
            all(
                value is not None
                for value in (
                    quote.implied_volatility,
                    quote.delta,
                    quote.gamma,
                    quote.vega,
                    quote.theta,
                )
            )
            for quote in quotes
        ),
        provider_timestamp_count=sum(
            quote.quote_timestamp_source in {"exchange", "provider"} for quote in quotes
        ),
        live_option_quote_count=sum(quote.market_data_type == "live" for quote in quotes),
        underlying_timestamp_verified=(
            snapshot.underlying_quote_timestamp is not None
            and snapshot.underlying_timestamp_source in {"exchange", "provider"}
        ),
        underlying_live=snapshot.underlying_market_data_type == "live",
        promotion_eligible=snapshot.promotion_eligible,
    )


def _append_chain_checks(
    checks: list[IbkrValidationCheck],
    snapshot: LiveOptionChainSnapshot,
    evidence: IbkrChainValidationEvidence,
) -> None:
    total = evidence.usable_quote_count
    checks.append(
        _coverage_check(
            "contract_identity",
            evidence.identity_complete_count,
            total,
            "IBKR_CONTRACT_IDENTITIES_COMPLETE",
            "IBKR_CONTRACT_IDENTITIES_INCOMPLETE",
        )
    )
    complete = snapshot.contract_discovery_complete and snapshot.quote_collection_complete
    checks.append(
        IbkrValidationCheck(
            check_id="chain_completeness",
            status="PASS" if complete else "WARN",
            detail_code=(
                "IBKR_CHAIN_COMPLETE" if complete else "IBKR_CHAIN_INCOMPLETE_OR_TRUNCATED"
            ),
            evidence=[f"missing={snapshot.missing_quote_count}"],
        )
    )
    for check_id, count, passed, warned in (
        (
            "volume_coverage",
            evidence.volume_present_count,
            "IBKR_VOLUME_COMPLETE",
            "IBKR_VOLUME_PARTIAL",
        ),
        (
            "open_interest_coverage",
            evidence.open_interest_present_count,
            "IBKR_OPEN_INTEREST_COMPLETE",
            "IBKR_OPEN_INTEREST_PARTIAL",
        ),
        (
            "greeks_coverage",
            evidence.greeks_complete_count,
            "IBKR_GREEKS_COMPLETE",
            "IBKR_GREEKS_PARTIAL",
        ),
    ):
        checks.append(_coverage_check(check_id, count, total, passed, warned))
    timestamps_complete = (
        evidence.provider_timestamp_count == total and evidence.underlying_timestamp_verified
    )
    checks.append(
        IbkrValidationCheck(
            check_id="timestamp_provenance",
            status="PASS" if timestamps_complete else "WARN",
            detail_code=(
                "IBKR_PROVIDER_TIMESTAMPS_COMPLETE"
                if timestamps_complete
                else "IBKR_CLIENT_RECEIPT_TIMESTAMPS_PRESENT"
            ),
            evidence=[f"provider_option_timestamps={evidence.provider_timestamp_count}/{total}"],
        )
    )
    live_complete = evidence.live_option_quote_count == total and evidence.underlying_live
    checks.append(
        IbkrValidationCheck(
            check_id="market_data_type",
            status="PASS" if live_complete else "WARN",
            detail_code=(
                "IBKR_LIVE_DATA_COMPLETE" if live_complete else "IBKR_NON_LIVE_DATA_PRESENT"
            ),
            evidence=[f"live_option_quotes={evidence.live_option_quote_count}/{total}"],
        )
    )
    checks.append(
        IbkrValidationCheck(
            check_id="data_promotion",
            status="PASS" if snapshot.promotion_eligible else "WARN",
            detail_code=(
                "IBKR_CHAIN_PROMOTION_ELIGIBLE"
                if snapshot.promotion_eligible
                else "IBKR_CHAIN_NOT_PROMOTION_ELIGIBLE"
            ),
        )
    )


def _coverage_check(
    check_id: str,
    count: int,
    total: int,
    pass_code: str,
    warn_code: str,
) -> IbkrValidationCheck:
    complete = total > 0 and count == total
    return IbkrValidationCheck(
        check_id=check_id,
        status="PASS" if complete else "WARN",
        detail_code=pass_code if complete else warn_code,
        evidence=[f"present={count}/{total}"],
    )


def _resolve_combo_plan(
    plan: ComboValidationPlan,
    snapshot: LiveOptionChainSnapshot,
    requested_at: datetime,
) -> LiveComboQuoteRequest:
    resolved: list[LiveComboLeg] = []
    for planned in plan.legs:
        matches = [
            quote
            for quote in snapshot.quotes
            if quote.expiration == planned.expiration
            and abs(quote.strike - planned.strike) <= 1e-9
            and quote.option_type == planned.option_type
        ]
        if len(matches) != 1:
            raise IbkrProviderError("IBKR_COMBO_LEG_RESOLUTION_NOT_UNIQUE")
        quote = matches[0]
        if quote.con_id is None:
            raise IbkrProviderError("IBKR_COMBO_LEG_CON_ID_MISSING")
        resolved.append(
            LiveComboLeg(
                con_id=quote.con_id,
                ratio=planned.ratio,
                action=planned.action,
                exchange=planned.exchange,
                bid=quote.bid,
                ask=quote.ask,
            )
        )
    return LiveComboQuoteRequest(
        candidate_id=plan.candidate_id,
        ticker=plan.ticker.upper(),
        legs=resolved,
        requested_at=_utc(requested_at),
        maximum_quote_age_seconds=plan.maximum_quote_age_seconds,
    )


def _final_status(
    checks: list[IbkrValidationCheck],
    snapshot: LiveOptionChainSnapshot,
    combo: LiveComboQuote | None,
    combo_plan: ComboValidationPlan | None,
) -> tuple[str, str, str | None]:
    failure = next((item.detail_code for item in checks if item.status == "FAIL"), None)
    if failure is not None:
        return "FAILED_SAFE", "broker_read_only_path_observed", failure
    if snapshot.promotion_eligible:
        if combo_plan is not None and combo is not None and combo.comparison_confirmed:
            return (
                "CHAIN_AND_COMBO_PROMOTION_ELIGIBLE",
                "broker_read_only_chain_and_combo_promotable",
                None,
            )
        return (
            "CHAIN_PROMOTION_ELIGIBLE",
            "broker_read_only_chain_promotable",
            None,
        )
    return "CAPTURED_NOT_PROMOTABLE", "broker_read_only_path_observed", None


def _failed_outcome(
    started_at: datetime,
    clock: Callable[[], datetime],
    provider_name: str,
    request: LiveChainRequest,
    requested_market_data_type: Literal["live", "frozen", "delayed", "delayed_frozen"],
    second_session_requested: bool,
    checks: list[IbkrValidationCheck],
    failure_code: str,
    *,
    broker_read_observed: bool = False,
    independent_second_session_verified: bool = False,
    provider_diagnostics: IbkrProviderDiagnostics | None = None,
) -> IbkrValidationOutcome:
    completed_at = _utc(clock())
    payload = {
        "started_at": started_at,
        "completed_at": completed_at,
        "status": "FAILED_SAFE",
        "maximum_claim": (
            "broker_read_only_path_observed" if broker_read_observed else "software_only"
        ),
        "provider": provider_name,
        "ticker": request.ticker.upper(),
        "request": request,
        "requested_market_data_type": requested_market_data_type,
        "broker_read_observed": broker_read_observed,
        "provider_diagnostics": provider_diagnostics,
        "independent_second_session_requested": second_session_requested,
        "independent_second_session_verified": independent_second_session_verified,
        "checks": checks,
        "failure_code": failure_code,
    }
    report = IbkrReadOnlyValidationReport(
        report_id=f"ibkr-validation-{stable_hash(payload)[:20]}",
        **payload,
    )
    return IbkrValidationOutcome(report=report, snapshot=None)


def _provider_diagnostics(provider: IbkrValidationProvider) -> IbkrProviderDiagnostics | None:
    diagnostics = getattr(provider, "diagnostics", None)
    if not callable(diagnostics):
        return None
    result = diagnostics()
    if not isinstance(result, IbkrProviderDiagnostics):
        raise ValueError("IBKR_PROVIDER_DIAGNOSTICS_INVALID")
    return result


def _combo_plan_preflight(
    plan: ComboValidationPlan | None,
    request: LiveChainRequest,
) -> str | None:
    """Reject unsafe/example BAG plans before the first provider call."""

    if plan is None:
        return None
    if plan.example_only:
        return "IBKR_COMBO_PLAN_MARKED_EXAMPLE_ONLY"
    if plan.ticker.upper() != request.ticker.upper():
        return "IBKR_COMBO_PLAN_TICKER_MISMATCH"
    for leg in plan.legs:
        if not request.expiration_start <= leg.expiration <= request.expiration_end:
            return "IBKR_COMBO_PLAN_EXPIRATION_OUTSIDE_REQUEST"
        if request.minimum_strike is not None and leg.strike < request.minimum_strike:
            return "IBKR_COMBO_PLAN_STRIKE_OUTSIDE_REQUEST"
        if request.maximum_strike is not None and leg.strike > request.maximum_strike:
            return "IBKR_COMBO_PLAN_STRIKE_OUTSIDE_REQUEST"
    return None


def _passed(check_id: str, detail_code: str, *evidence: str) -> IbkrValidationCheck:
    return IbkrValidationCheck(
        check_id=check_id,
        status="PASS",
        detail_code=detail_code,
        evidence=list(evidence),
    )


def _failed(check_id: str, detail_code: str) -> IbkrValidationCheck:
    return IbkrValidationCheck(
        check_id=check_id,
        status="FAIL",
        detail_code=detail_code,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("IBKR_VALIDATION_TIMESTAMP_NAIVE")
    return value.astimezone(UTC)
