"""Fail-closed data-use governance for research inputs and committed artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from take_two_options.domain import StrictModel


class UsagePermission(StrEnum):
    ALLOWED = "allowed"
    CONDITIONAL = "conditional"
    FORBIDDEN = "forbidden"
    TO_REVIEW = "to_review"


class DataUsageRight(StrictModel):
    provider: str = Field(min_length=1)
    dataset_class: str = Field(min_length=1)
    account_scope: str = Field(min_length=1)
    local_private_research: UsagePermission
    local_retention: UsagePermission
    internal_derived_analysis: UsagePermission
    raw_redistribution: UsagePermission
    aggregate_publication: UsagePermission
    raw_github: UsagePermission
    attribution_required: bool
    deletion_on_termination: bool
    terms_urls: list[str] = Field(min_length=1)
    reviewed_at: datetime
    rationale: str = Field(min_length=1)
    unresolved: list[str] = Field(default_factory=list)

    @field_validator("reviewed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("rights review timestamp must be timezone-aware")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def never_allow_raw_github_when_redistribution_is_restricted(self) -> DataUsageRight:
        if self.raw_redistribution is not UsagePermission.ALLOWED:
            if self.raw_github is UsagePermission.ALLOWED:
                raise ValueError("raw GitHub publication cannot exceed redistribution rights")
        return self


class DataUsageRightsReport(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    report_id: str = Field(min_length=1)
    generated_at: datetime
    records: list[DataUsageRight] = Field(min_length=1)
    raw_licensed_data_committed: Literal[False] = False
    legal_review_status: Literal["HUMAN_REVIEW_RECOMMENDED"] = "HUMAN_REVIEW_RECOMMENDED"
    order_capability: Literal["forbidden"] = "forbidden"

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("rights report timestamp must be timezone-aware")
        return value.astimezone(UTC)


def pre_opra_data_usage_rights(as_of: datetime) -> DataUsageRightsReport:
    """Return the reviewed policy matrix; account-specific grants remain conditional."""

    records = [
        DataUsageRight(
            provider="Market Data",
            dataset_class="historical US option EOD quotes",
            account_scope="self-service subscription; exact entitlement not inspected",
            local_private_research=UsagePermission.CONDITIONAL,
            local_retention=UsagePermission.CONDITIONAL,
            internal_derived_analysis=UsagePermission.CONDITIONAL,
            raw_redistribution=UsagePermission.FORBIDDEN,
            aggregate_publication=UsagePermission.CONDITIONAL,
            raw_github=UsagePermission.FORBIDDEN,
            attribution_required=True,
            deletion_on_termination=True,
            terms_urls=[
                "https://www.marketdata.app/terms/",
                "https://www.marketdata.app/docs/account/data-policies/data-redistribution/",
                "https://www.marketdata.app/terms/public-use/",
            ],
            reviewed_at=as_of,
            rationale=(
                "Self-service data is for the subscriber's own use; redistribution and bulk "
                "exports are forbidden. Public-use terms permit non-reconstructible aggregates "
                "for qualifying educational work with attribution."
            ),
            unresolved=[
                "Confirm subscriber professional/non-professional classification.",
                "Confirm current subscription and deletion obligations before continued use.",
                "Obtain written authorization for any use beyond local private research.",
            ],
        ),
        DataUsageRight(
            provider="Alpaca",
            dataset_class="IEX adjusted US equity bars and corporate actions",
            account_scope="authenticated customer API",
            local_private_research=UsagePermission.CONDITIONAL,
            local_retention=UsagePermission.CONDITIONAL,
            internal_derived_analysis=UsagePermission.CONDITIONAL,
            raw_redistribution=UsagePermission.FORBIDDEN,
            aggregate_publication=UsagePermission.CONDITIONAL,
            raw_github=UsagePermission.FORBIDDEN,
            attribution_required=True,
            deletion_on_termination=False,
            terms_urls=[
                "https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf",
                "https://docs.alpaca.markets/docs/about-market-data-api",
            ],
            reviewed_at=as_of,
            rationale=(
                "The customer agreement prohibits reproduction, distribution, sale, or "
                "commercial exploitation of market data without written consent."
            ),
            unresolved=[
                "Confirm account-specific market-data display/subscriber agreements.",
                "Confirm whether derived public aggregates need separate consent.",
            ],
        ),
        DataUsageRight(
            provider="U.S. Department of the Treasury",
            dataset_class="daily par yield curve rates",
            account_scope="public official website",
            local_private_research=UsagePermission.ALLOWED,
            local_retention=UsagePermission.ALLOWED,
            internal_derived_analysis=UsagePermission.ALLOWED,
            raw_redistribution=UsagePermission.CONDITIONAL,
            aggregate_publication=UsagePermission.ALLOWED,
            raw_github=UsagePermission.CONDITIONAL,
            attribution_required=True,
            deletion_on_termination=False,
            terms_urls=[
                "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files",
                "https://home.treasury.gov/footer/privacy-act/privacy-policy",
            ],
            reviewed_at=as_of,
            rationale=(
                "Official public rate files are available without authentication; attribution "
                "and source disclaimers are retained. Third-party material is excluded."
            ),
            unresolved=["Human legal review is recommended before republishing raw files."],
        ),
        DataUsageRight(
            provider="European Central Bank",
            dataset_class="EUR/USD reference exchange rates",
            account_scope="public official website",
            local_private_research=UsagePermission.ALLOWED,
            local_retention=UsagePermission.ALLOWED,
            internal_derived_analysis=UsagePermission.ALLOWED,
            raw_redistribution=UsagePermission.ALLOWED,
            aggregate_publication=UsagePermission.ALLOWED,
            raw_github=UsagePermission.ALLOWED,
            attribution_required=True,
            deletion_on_termination=False,
            terms_urls=[
                "https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html"
            ],
            reviewed_at=as_of,
            rationale=(
                "ECB permits free use when information is accurate, the ECB is cited, and any "
                "modification or derived calculation is disclosed."
            ),
        ),
        DataUsageRight(
            provider="U.S. Securities and Exchange Commission",
            dataset_class="EDGAR submissions and XBRL facts",
            account_scope="public data.sec.gov APIs",
            local_private_research=UsagePermission.ALLOWED,
            local_retention=UsagePermission.ALLOWED,
            internal_derived_analysis=UsagePermission.ALLOWED,
            raw_redistribution=UsagePermission.CONDITIONAL,
            aggregate_publication=UsagePermission.ALLOWED,
            raw_github=UsagePermission.CONDITIONAL,
            attribution_required=True,
            deletion_on_termination=False,
            terms_urls=[
                "https://www.sec.gov/about/developer-resources",
                "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data",
            ],
            reviewed_at=as_of,
            rationale=(
                "EDGAR data is publicly downloadable; automated access must declare a user "
                "agent, stay under ten requests per second, and avoid excessive crawling."
            ),
            unresolved=["Do not assume third-party exhibits are free of separate rights."],
        ),
    ]
    return DataUsageRightsReport(
        report_id="ttwo-pre-opra-data-rights-v1",
        generated_at=as_of,
        records=records,
    )
