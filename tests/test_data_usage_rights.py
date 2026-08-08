from datetime import UTC, datetime

from take_two_options.historical_data.data_rights import (
    UsagePermission,
    pre_opra_data_usage_rights,
)


def test_licensed_market_data_can_never_be_committed_raw() -> None:
    report = pre_opra_data_usage_rights(datetime(2026, 8, 8, tzinfo=UTC))
    assert report.raw_licensed_data_committed is False
    records = {record.provider: record for record in report.records}
    assert records["Market Data"].raw_github is UsagePermission.FORBIDDEN
    assert records["Alpaca"].raw_github is UsagePermission.FORBIDDEN
    assert records["Market Data"].raw_redistribution is UsagePermission.FORBIDDEN


def test_account_specific_rights_remain_conditional() -> None:
    report = pre_opra_data_usage_rights(datetime(2026, 8, 8, tzinfo=UTC))
    records = {record.provider: record for record in report.records}
    assert records["Market Data"].local_private_research is UsagePermission.CONDITIONAL
    assert records["Alpaca"].unresolved
    assert report.legal_review_status == "HUMAN_REVIEW_RECOMMENDED"
