"""Build a governed point-in-time TTWO event history from official sources."""

from __future__ import annotations

import argparse
import json
import math
import os
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, cast
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from take_two_options.config.loader import load_pre_opra_config
from take_two_options.historical_data.event_regimes import (
    EventKind,
    EventOutcome,
    PointInTimeEvent,
    build_event_regime_report,
)
from take_two_options.historical_data.market_context import MarketContextDataset, canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK0000946581.json"
IR_RSS = "https://ir.take2games.com/rss/news-releases.xml?items=100"
USER_AGENT = os.getenv("SEC_USER_AGENT", "Insular Research contact@take-two-options.dev")
NEW_YORK = ZoneInfo("America/New_York")


def _fetch(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json, application/rss+xml, application/xml;q=0.9",
            "Accept-Encoding": "identity",
        },
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return cast(bytes, response.read())


def _source_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _sec_events(raw: bytes, cutoff: datetime, start: date) -> list[PointInTimeEvent]:
    submissions = cast(dict[str, Any], json.loads(raw))
    recent = cast(dict[str, list[Any]], cast(dict[str, Any], submissions["filings"])["recent"])
    rows = [dict(zip(recent, values, strict=True)) for values in zip(*recent.values(), strict=True)]
    earnings_acceptance_dates = {
        datetime.fromisoformat(str(row["acceptanceDateTime"]).replace("Z", "+00:00")).date()
        for row in rows
        if row["form"] in {"8-K", "8-K/A"} and "2.02" in str(row.get("items", ""))
    }
    events: list[PointInTimeEvent] = []
    for row in rows:
        filing_date = date.fromisoformat(str(row["filingDate"]))
        form = str(row["form"])
        if filing_date < start or filing_date > cutoff.date():
            continue
        if form not in {"8-K", "8-K/A", "10-Q", "10-K"}:
            continue
        accepted_at = datetime.fromisoformat(str(row["acceptanceDateTime"]).replace("Z", "+00:00"))
        if form in {"10-Q", "10-K"} and accepted_at.date() in earnings_acceptance_dates:
            continue
        accession = str(row["accessionNumber"])
        primary_document = str(row["primaryDocument"])
        accession_path = accession.replace("-", "")
        uri = f"https://www.sec.gov/Archives/edgar/data/946581/{accession_path}/{primary_document}"
        is_earnings = "2.02" in str(row.get("items", ""))
        kind = EventKind.EARNINGS if is_earnings else EventKind.REGULATORY
        metadata = {
            "accession": accession,
            "form": form,
            "items": row.get("items", ""),
            "accepted_at": accepted_at.isoformat(),
            "uri": uri,
        }
        events.append(
            PointInTimeEvent(
                event_id=f"sec-{accession_path}",
                external_id=f"sec-{accession}",
                entity="Take-Two Interactive Software, Inc.",
                kind=kind,
                event_time=accepted_at,
                publication_time=accepted_at,
                available_at=accepted_at,
                decision_cutoff=cutoff,
                source_id=uri,
                source_hash=_source_hash(metadata),
                summary=(
                    f"Official SEC {form} filing; items {row.get('items') or 'not specified'}."
                ),
            )
        )
    return events


def _rss_product_events(raw: bytes, cutoff: datetime, start: date) -> list[PointInTimeEvent]:
    root = ET.fromstring(raw)
    output: list[PointInTimeEvent] = []
    product_markers = (
        "available",
        "announces",
        "pre-order",
        "pre-orders",
        "cover",
        "launch",
        "releases",
    )
    excluded_markers = ("reports results", "to report", "to present", "conference")
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        lowered = title.casefold()
        if not any(marker in lowered for marker in product_markers):
            continue
        if any(marker in lowered for marker in excluded_markers):
            continue
        published = parsedate_to_datetime(item.findtext("pubDate") or "").astimezone(UTC)
        if published.date() < start or published > cutoff:
            continue
        guid = (item.findtext("guid") or _source_hash(title)[:12]).strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        metadata = {
            "guid": guid,
            "title": title,
            "published": published.isoformat(),
            "link": link,
            "description": description,
        }
        output.append(
            PointInTimeEvent(
                event_id=f"ir-{guid}",
                external_id=f"ir-{guid}",
                entity="Take-Two Interactive Software, Inc.",
                kind=EventKind.PRODUCT_RELEASE,
                event_time=published,
                publication_time=published,
                available_at=published,
                decision_cutoff=cutoff,
                source_id=link,
                source_hash=_source_hash(metadata),
                summary=title,
            )
        )
    return output


def _configured_events(records: list[dict[str, Any]], cutoff: datetime) -> list[PointInTimeEvent]:
    output: list[PointInTimeEvent] = []
    for record in records:
        available_at = datetime.fromisoformat(str(record["available_at"]))
        metadata = {str(key): value for key, value in record.items()}
        output.append(
            PointInTimeEvent(
                event_id=str(record["event_id"]),
                external_id=str(record["event_id"]),
                entity="Take-Two Interactive Software, Inc.",
                kind=EventKind(str(record["kind"])),
                event_time=available_at,
                publication_time=available_at,
                available_at=available_at,
                decision_cutoff=cutoff,
                source_id=str(record["source_url"]),
                source_hash=_source_hash(metadata),
                summary=str(record["summary"]),
            )
        )
    return output


def _event_outcomes(
    events: list[PointInTimeEvent], context: MarketContextDataset
) -> list[EventOutcome]:
    bars = sorted(context.underlying_bars, key=lambda item: item.market_time)
    by_date = {bar.market_time.date(): bar.close for bar in bars}
    session_dates = sorted(by_date)
    output: list[EventOutcome] = []
    for event in events:
        local = event.available_at.astimezone(NEW_YORK)
        eligible_base = [
            day
            for day in session_dates
            if day < local.date() or (day == local.date() and local.hour >= 16)
        ]
        future = [day for day in session_dates if day > local.date()]
        if not eligible_base:
            continue
        base = by_date[eligible_base[-1]]
        for horizon in (1, 5, 20):
            if len(future) >= horizon:
                output.append(
                    EventOutcome(
                        event_id=event.event_id,
                        horizon_sessions=horizon,
                        return_value=by_date[future[horizon - 1]] / base - 1.0,
                    )
                )
    return output


def _regime_rows(
    context: MarketContextDataset,
) -> list[tuple[str, datetime, datetime, float, float]]:
    bars = sorted(context.underlying_bars, key=lambda item: item.market_time)
    output: list[tuple[str, datetime, datetime, float, float]] = []
    for index in range(20, len(bars)):
        window = bars[index - 20 : index + 1]
        returns = [
            math.log(window[position].close / window[position - 1].close)
            for position in range(1, len(window))
        ]
        mean = sum(returns) / len(returns)
        variance = sum((value - mean) ** 2 for value in returns) / (len(returns) - 1)
        trailing = window[-1].close / window[0].close - 1.0
        available_at = window[-1].available_at
        output.append(
            (
                f"regime-{window[-1].market_time.date().isoformat()}",
                available_at,
                available_at,
                trailing,
                math.sqrt(variance * 252),
            )
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    arguments = parser.parse_args()
    config = load_pre_opra_config(arguments.config.resolve())
    settings = config.extensions.get("event_history", {})
    cutoff = config.market_context.decision_cutoff
    start = date.fromisoformat(str(settings.get("start", "2025-07-01")))
    context_path = ROOT / str(
        config.extensions.get("market_context", {}).get(
            "private_output", "data/pre_opra/market_context.json"
        )
    )
    context = MarketContextDataset.model_validate_json(context_path.read_text(encoding="utf-8"))
    sec_raw = _fetch(SEC_SUBMISSIONS)
    rss_raw = _fetch(IR_RSS)
    events = [
        *_sec_events(sec_raw, cutoff, start),
        *_rss_product_events(rss_raw, cutoff, start),
        *_configured_events(cast(list[dict[str, Any]], settings.get("manual_events", [])), cutoff),
    ]
    deduplicated = {event.event_id: event for event in events}
    events = sorted(deduplicated.values(), key=lambda item: (item.available_at, item.event_id))
    outcomes = _event_outcomes(events, context)
    dataset_hash = canonical_hash(
        {
            "events": [event.model_dump(mode="json") for event in events],
            "outcomes": [outcome.model_dump(mode="json") for outcome in outcomes],
            "market_context_hash": canonical_hash(context.model_dump(mode="json")),
        }
    )
    report = build_event_regime_report(
        events,
        outcomes,
        _regime_rows(context),
        ticker="TTWO",
        dataset_hash=dataset_hash,
        trend_threshold=float(settings.get("trend_threshold", 0.05)),
        high_volatility_threshold=float(settings.get("high_volatility_threshold", 0.40)),
        synthetic=False,
    )
    private_path = ROOT / str(
        settings.get("private_output", "data/pre_opra/event_regime_dataset.json")
    )
    committed_path = ROOT / str(
        settings.get("aggregate_output", "reports/pre_opra/event_regime_dataset_2026-08-08.json")
    )
    private_path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    aggregate = report.model_copy(update={"regimes": []})
    committed_path.write_text(aggregate.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Governed events: accepted={len(report.accepted_events)}, "
        f"event-study cells={len(report.event_study)}, private regimes={len(report.regimes)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
