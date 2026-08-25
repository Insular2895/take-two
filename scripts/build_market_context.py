"""Acquire and align the private pre-OPRA market context through read-only APIs."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, cast
from urllib.request import Request, urlopen

from alpaca.data.historical.corporate_actions import CorporateActionsClient
from alpaca.data.requests import CorporateActionsRequest

from take_two_options.alpaca_data import AlpacaCredentials, AlpacaReadOnlyMarketData
from take_two_options.config.loader import load_pre_opra_config
from take_two_options.historical_data.market_context import (
    CorporateActionRecord,
    DividendPolicyEvidence,
    MarketContextDataset,
    UnderlyingDailyBar,
    canonical_hash,
    parse_ecb_fx_csv,
    parse_treasury_csv,
    summarize_market_context,
)

ROOT = Path(__file__).resolve().parents[1]
DIVIDEND_SOURCE = (
    "https://www.sec.gov/Archives/edgar/data/946581/000162828026037434/ttwo-20260331.htm"
)


def _fetch_ecb(start: str, end: str) -> str:
    url = (
        "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
        f"?startPeriod={start}&endPeriod={end}&format=csvdata"
    )
    request = Request(url, headers={"User-Agent": "take-two-options/0.11 read-only research"})
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return cast(bytes, response.read()).decode("utf-8")


def _normalize_actions(raw: dict[str, Any]) -> list[CorporateActionRecord]:
    output: list[CorporateActionRecord] = []
    for action_type, actions in sorted(raw.items()):
        for index, action in enumerate(cast(list[dict[str, Any]], actions)):
            raw_date = (
                action.get("ex_date") or action.get("effective_date") or action["process_date"]
            )
            effective = datetime.fromisoformat(str(raw_date)).date()
            action_id = str(action.get("id") or f"{action_type}-{effective}-{index}")
            fields = {
                str(key): value
                for key, value in action.items()
                if isinstance(value, (str, int, float, bool)) or value is None
            }
            output.append(
                CorporateActionRecord(
                    action_type=action_type,
                    action_id=action_id,
                    effective_date=effective,
                    available_at=datetime.combine(
                        effective + timedelta(days=1), datetime.min.time(), UTC
                    ),
                    raw_public_fields=fields,
                )
            )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    config = load_pre_opra_config(arguments.config.resolve())
    settings = config.extensions.get("market_context", {})
    start = datetime.fromisoformat(str(settings.get("start", "2024-02-01T00:00:00+00:00")))
    end = datetime.combine(config.research_request.as_of, datetime.max.time(), UTC)
    generated_at = datetime.combine(config.research_request.as_of, datetime.min.time(), UTC)
    feed = str(settings.get("stock_feed", "iex"))
    if feed not in {"iex", "sip"}:
        raise ValueError("stock_feed must be iex or sip")
    client = AlpacaReadOnlyMarketData.from_env()
    bars = client.stock_bars(ticker="TTWO", start=start, end=end, feed=cast(Any, feed))
    underlying = [
        UnderlyingDailyBar(
            ticker=bar.symbol,
            market_time=bar.timestamp,
            available_at=bar.timestamp + timedelta(days=1),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            trade_count=bar.trade_count,
            vwap=bar.vwap,
            feed=cast(Any, feed),
        )
        for bar in bars
    ]
    credentials = AlpacaCredentials.from_env()
    actions_client = CorporateActionsClient(
        api_key=credentials.key_id,
        secret_key=credentials.secret_key,
        raw_data=True,
    )
    action_response = actions_client.get_corporate_actions(
        CorporateActionsRequest(symbols=["TTWO"], start=start.date(), end=end.date())
    )
    raw_actions = cast(dict[str, Any], action_response)
    actions = _normalize_actions(raw_actions)
    treasury_paths = [
        ROOT / str(path)
        for path in settings.get(
            "treasury_files",
            [
                "data/treasury/daily_treasury_yield_curve_2025.csv",
                "data/treasury/daily_treasury_yield_curve_2026.csv",
            ],
        )
    ]
    treasury_texts = [path.read_text(encoding="utf-8") for path in treasury_paths]
    curves_by_date = {
        curve.observation_date: curve
        for text in treasury_texts
        for curve in parse_treasury_csv(text)
    }
    ecb_text = _fetch_ecb("2025-07-01", config.research_request.as_of.isoformat())
    fx_rates = parse_ecb_fx_csv(ecb_text)
    dividend_statement = (
        "Take-Two reported that it has never declared or paid cash dividends and does not "
        "expect to do so in the foreseeable future."
    )
    dataset = MarketContextDataset(
        dataset_id="ttwo-pre-opra-market-context-v1",
        generated_at=generated_at,
        underlying_bars=underlying,
        risk_free_curves=sorted(curves_by_date.values(), key=lambda item: item.observation_date),
        fx_rates=fx_rates,
        corporate_actions=actions,
        dividend_policy=DividendPolicyEvidence(
            status="verified_zero_through_filing_date",
            filing_date=datetime(2026, 5, 21).date(),
            available_at=datetime(2026, 5, 22, tzinfo=UTC),
            source_url=DIVIDEND_SOURCE,
            source_hash=sha256(dividend_statement.encode()).hexdigest(),
            statement=dividend_statement,
        ),
        source_hashes={
            "alpaca_underlying": canonical_hash(
                [item.model_dump(mode="json") for item in underlying]
            ),
            "alpaca_corporate_actions": canonical_hash(raw_actions),
            "treasury": canonical_hash(treasury_texts),
            "ecb_fx": sha256(ecb_text.encode()).hexdigest(),
            "sec_dividend_policy": sha256(dividend_statement.encode()).hexdigest(),
        },
    )
    private_path = ROOT / str(settings.get("private_output", "data/pre_opra/market_context.json"))
    summary_path = ROOT / str(
        settings.get("aggregate_summary", "reports/pre_opra/market_context_2026-08-08.json")
    )
    private_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_text(dataset.model_dump_json(indent=2) + "\n", encoding="utf-8")
    summary = summarize_market_context(dataset)
    summary_path.write_text(summary.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Market context: bars={summary.underlying_bar_count}, "
        f"curves={summary.rate_curve_count}, fx={summary.fx_rate_count}, "
        f"actions={summary.corporate_action_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
