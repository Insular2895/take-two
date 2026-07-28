"""Unified, provenance-preserving data ingestion for V11."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Protocol, cast

from take_two_options.intelligence.schemas import (
    ComboQuote,
    ConnectorState,
    ConnectorStatus,
    DataDomain,
    DataQuality,
    SourceProvenance,
    UnifiedDataSnapshot,
    UnifiedObservation,
)
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.thesis_scanner.schemas import ThesisScanReport


class ConnectorError(RuntimeError):
    """Raised when a configured external connector cannot produce valid data."""


def _parse_utc_timestamp(value: Any, *, field: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as error:
        raise ConnectorError(f"{field} is not a valid ISO-8601 timestamp") from error
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


@dataclass(frozen=True)
class ConnectorResult:
    """Normalized connector payload."""

    source: SourceProvenance
    observations: list[UnifiedObservation]
    warnings: list[str]

    def __init__(
        self,
        source: SourceProvenance,
        observations: list[UnifiedObservation],
        warnings: list[str] | None = None,
    ) -> None:
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "warnings", warnings or [])


class DataConnector(Protocol):
    connector_id: str

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        """Fetch normalized, read-only observations."""


class IBKRDataPort(Protocol):
    """Narrow broker port: market data only, with no order methods."""

    def option_chain_snapshot(self, ticker: str) -> dict[str, Any]:
        """Return one broker snapshot with spot and option quotes."""

    def combo_quote(self, candidate_id: str, legs: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a non-order combo market quote."""


class GoogleTrendsDataPort(Protocol):
    """Injected official-alpha port; authentication remains provider-specific."""

    def interest(
        self,
        *,
        terms: list[str],
        end: datetime,
        region: str,
    ) -> list[dict[str, Any]]:
        """Return consistently scaled official-alpha search-interest rows."""


class MarketCalendarDataPort(Protocol):
    """Injected exchange/reference-data port for point-in-time sessions."""

    def sessions(
        self,
        *,
        exchange: str,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """Return dated exchange-session rows available at the cutoff."""


class UnifiedDataHub:
    """Collect connector outputs while preserving failures and provenance."""

    def __init__(self, required_series: Iterable[str] = ()) -> None:
        self.required_series = tuple(required_series)

    def collect(
        self,
        *,
        ticker: str,
        as_of: datetime,
        connectors: Iterable[DataConnector],
        seed_sources: Iterable[SourceProvenance] = (),
        seed_observations: Iterable[UnifiedObservation] = (),
    ) -> UnifiedDataSnapshot:
        sources = {item.source_id: item for item in seed_sources}
        observations = {item.observation_id: item for item in seed_observations}
        statuses: list[ConnectorStatus] = []
        if observations:
            statuses.append(
                ConnectorStatus(
                    connector_id="v10_normalized_seed",
                    state=ConnectorState.READY,
                    checked_at=datetime.now(UTC),
                    observations=len(observations),
                )
            )
        warnings: list[str] = []
        for connector in connectors:
            checked_at = datetime.now(UTC)
            try:
                result = connector.fetch(ticker=ticker, as_of=as_of)
            except ConnectorError as error:
                statuses.append(
                    ConnectorStatus(
                        connector_id=connector.connector_id,
                        state=ConnectorState.FAILED,
                        checked_at=checked_at,
                        observations=0,
                        error=str(error),
                    )
                )
                warnings.append(f"{connector.connector_id}: {error}")
                continue
            sources[result.source.source_id] = result.source
            for observation in result.observations:
                observations[observation.observation_id] = observation
            statuses.append(
                ConnectorStatus(
                    connector_id=connector.connector_id,
                    state=(
                        ConnectorState.READY
                        if result.observations
                        else ConnectorState.PARTIAL
                    ),
                    checked_at=checked_at,
                    observations=len(result.observations),
                    warnings=result.warnings,
                )
            )
            warnings.extend(f"{connector.connector_id}: {item}" for item in result.warnings)
        present = {item.series for item in observations.values()}
        missing = sorted(set(self.required_series) - present)
        identity = {
            "ticker": ticker,
            "as_of": as_of,
            "sources": sorted(sources),
            "observations": sorted(observations),
        }
        return UnifiedDataSnapshot(
            snapshot_id=f"v11-data-{stable_hash(identity)[:20]}",
            ticker=ticker,
            as_of=as_of,
            sources=list(sources.values()),
            observations=sorted(
                observations.values(),
                key=lambda item: (item.timestamp, item.series, item.observation_id),
            ),
            connectors=statuses,
            missing_required_series=missing,
            warnings=warnings,
        )


def seed_from_v10(
    report: ThesisScanReport,
) -> tuple[list[SourceProvenance], list[UnifiedObservation]]:
    """Translate the complete V10.1 chain and dated assumptions into V11 observations."""
    retrieved_at = report.created_at
    source_quality = {
        "opra": DataQuality.OPRA,
        "indicative": DataQuality.INDICATIVE,
        "eod_bid_ask": DataQuality.EOD,
        "synthetic": DataQuality.SYNTHETIC,
        "unknown": DataQuality.UNKNOWN,
    }[report.chain.price_quality]
    sources: dict[str, SourceProvenance] = {
        report.chain.source_id: SourceProvenance(
            source_id=report.chain.source_id,
            provider="V10.1 normalized option chain",
            uri=report.chain.source_path,
            retrieved_at=report.chain.retrieved_at,
            data_domain=DataDomain.OPTIONS,
            quality=source_quality,
            notes=list(report.chain.warnings),
        ),
        report.chain.spot_source_id: SourceProvenance(
            source_id=report.chain.spot_source_id,
            provider="V10.1 normalized underlying snapshot",
            uri=report.chain.source_path,
            retrieved_at=report.chain.retrieved_at,
            data_domain=DataDomain.MARKET,
            quality=source_quality,
        ),
        "v10-policy-fx": SourceProvenance(
            source_id="v10-policy-fx",
            provider=report.policy.fx_rate_source,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.MACRO,
            quality=DataQuality.OFFICIAL,
            notes=["Dated configuration input; freshness must be checked for live use."],
        ),
        "v10-policy-rate": SourceProvenance(
            source_id="v10-policy-rate",
            provider=report.policy.risk_free_rate_source,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.MACRO,
            quality=DataQuality.OFFICIAL,
            notes=["Dated configuration input; not a live curve."],
        ),
        "v10-policy-dividend": SourceProvenance(
            source_id="v10-policy-dividend",
            provider=report.policy.dividend_source,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.FUNDAMENTAL,
            quality=DataQuality.UNKNOWN,
            notes=["Assumption requiring corporate-action verification."],
        ),
    }
    observations = [
        UnifiedObservation(
            observation_id=f"{report.report_id}:spot",
            series=f"{report.request.ticker}.spot",
            timestamp=report.chain.spot_timestamp,
            value=report.chain.spot,
            unit="USD_per_share",
            source_id=report.chain.spot_source_id,
            domain=DataDomain.MARKET,
            quality=source_quality,
        ),
        UnifiedObservation(
            observation_id=f"{report.report_id}:eurusd",
            series="EURUSD",
            timestamp=datetime.combine(
                report.policy.fx_rate_date,
                datetime.min.time(),
                tzinfo=UTC,
            ),
            value=report.policy.eur_usd_rate,
            unit="USD_per_EUR",
            source_id="v10-policy-fx",
            domain=DataDomain.MACRO,
            quality=DataQuality.OFFICIAL,
        ),
        UnifiedObservation(
            observation_id=f"{report.report_id}:risk-free",
            series="USD.risk_free_rate",
            timestamp=datetime.combine(
                report.policy.risk_free_rate_date,
                datetime.min.time(),
                tzinfo=UTC,
            ),
            value=report.policy.risk_free_rate,
            unit="annual_decimal",
            source_id="v10-policy-rate",
            domain=DataDomain.MACRO,
            quality=DataQuality.OFFICIAL,
        ),
        UnifiedObservation(
            observation_id=f"{report.report_id}:dividend-yield",
            series=f"{report.request.ticker}.dividend_yield",
            timestamp=report.chain.as_of,
            value=report.policy.continuous_dividend_yield,
            unit="annual_decimal",
            source_id="v10-policy-dividend",
            domain=DataDomain.FUNDAMENTAL,
            quality=DataQuality.UNKNOWN,
        ),
    ]
    for quote in report.chain.quotes:
        sources.setdefault(
            quote.source_id,
            SourceProvenance(
                source_id=quote.source_id,
                provider="V10.1 option quote source",
                uri=report.chain.source_path,
                retrieved_at=report.chain.retrieved_at,
                data_domain=DataDomain.OPTIONS,
                quality={
                    "opra": DataQuality.OPRA,
                    "indicative": DataQuality.INDICATIVE,
                    "eod_bid_ask": DataQuality.EOD,
                    "synthetic": DataQuality.SYNTHETIC,
                    "unknown": DataQuality.UNKNOWN,
                }[quote.price_quality],
            ),
        )
        timestamp = quote.quote_timestamp or report.chain.as_of
        values: dict[str, tuple[float | int | str | bool, str]] = {
            "bid": (quote.bid if quote.bid is not None else -1.0, "USD_per_share"),
            "ask": (quote.ask if quote.ask is not None else -1.0, "USD_per_share"),
            "strike": (quote.strike, "USD_per_share"),
        }
        if quote.implied_volatility is not None:
            values["implied_volatility"] = (quote.implied_volatility, "annual_decimal")
        if quote.volume is not None:
            values["volume"] = (quote.volume, "contracts")
        if quote.open_interest is not None:
            values["open_interest"] = (quote.open_interest, "contracts")
        for field, (value, unit) in values.items():
            observations.append(
                UnifiedObservation(
                    observation_id=f"{report.report_id}:{quote.symbol}:{field}",
                    series=f"option.{quote.symbol}.{field}",
                    timestamp=timestamp,
                    value=value,
                    unit=unit,
                    source_id=quote.source_id,
                    domain=DataDomain.OPTIONS,
                    quality=sources[quote.source_id].quality,
                    metadata={
                        "expiration": quote.expiration.isoformat(),
                        "option_type": quote.option_type.value,
                    },
                )
            )
    return list(sources.values()), observations


class JsonObservationConnector:
    """Load a pre-normalized fixture or licensed provider export."""

    connector_id = "json_observations"

    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            source = SourceProvenance.model_validate(payload["source"])
            observations = [
                UnifiedObservation.model_validate(item) for item in payload["observations"]
            ]
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ConnectorError(f"invalid observation export {self.path}: {error}") from error
        filtered = [
            item
            for item in observations
            if item.timestamp <= as_of
            and (
                ticker.upper() in item.series.upper()
                or item.domain in {DataDomain.MACRO, DataDomain.MARKET}
            )
        ]
        return ConnectorResult(source, filtered)


class HttpJsonConnector:
    """Small official-API base with explicit headers, timeout, and injectable transport."""

    connector_id = "http_json"

    def __init__(
        self,
        *,
        user_agent: str,
        timeout_seconds: float = 15,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        if not user_agent.strip():
            raise ValueError("an identifying user agent is required")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._opener = opener

    def _get_json(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        request_headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        request_headers.update(headers or {})
        request = urllib.request.Request(url, headers=request_headers)
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError) as error:
            raise ConnectorError(f"GET failed for {url}: {error}") from error
        if not isinstance(payload, dict):
            raise ConnectorError(f"GET {url} did not return a JSON object")
        return cast(dict[str, Any], payload)


class SecEdgarConnector(HttpJsonConnector):
    """SEC submissions and company facts, respecting the public data API boundary."""

    connector_id = "sec_edgar"

    def __init__(self, *, cik: str, user_agent: str, **kwargs: Any) -> None:
        super().__init__(user_agent=user_agent, **kwargs)
        self.cik = cik.zfill(10)

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        submissions_url = f"https://data.sec.gov/submissions/CIK{self.cik}.json"
        facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{self.cik}.json"
        submissions = self._get_json(submissions_url)
        facts = self._get_json(facts_url)
        retrieved_at = datetime.now(UTC)
        source_id = f"sec-edgar-{self.cik}-{retrieved_at:%Y%m%dT%H%M%SZ}"
        source = SourceProvenance(
            source_id=source_id,
            provider="U.S. SEC EDGAR",
            uri=submissions_url,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.FUNDAMENTAL,
            quality=DataQuality.OFFICIAL,
            license_or_terms="SEC fair-access policy; maximum 10 requests/second.",
            content_hash=stable_hash({"submissions": submissions, "facts": facts}),
        )
        observations: list[UnifiedObservation] = []
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        for index, form in enumerate(forms):
            if index >= len(filing_dates) or index >= len(accession):
                break
            timestamp = datetime.fromisoformat(f"{filing_dates[index]}T00:00:00+00:00")
            if timestamp > as_of:
                continue
            observations.append(
                UnifiedObservation(
                    observation_id=f"{source_id}:filing:{accession[index]}",
                    series=f"{ticker.upper()}.sec_filing",
                    timestamp=timestamp,
                    value=str(form),
                    unit="form_type",
                    source_id=source_id,
                    domain=DataDomain.FUNDAMENTAL,
                    quality=DataQuality.OFFICIAL,
                    metadata={"accession_number": accession[index]},
                )
            )
        entity_name = str(facts.get("entityName", ticker.upper()))
        observations.append(
            UnifiedObservation(
                observation_id=f"{source_id}:entity",
                series=f"{ticker.upper()}.sec_entity_name",
                timestamp=retrieved_at,
                value=entity_name,
                unit="text",
                source_id=source_id,
                domain=DataDomain.FUNDAMENTAL,
                quality=DataQuality.OFFICIAL,
            )
        )
        return ConnectorResult(source, observations)


class FredConnector(HttpJsonConnector):
    """FRED v1 series observations with the API key kept in the environment."""

    connector_id = "fred"

    def __init__(
        self,
        *,
        series_ids: Iterable[str],
        user_agent: str,
        api_key_env: str = "FRED_API_KEY",
        **kwargs: Any,
    ) -> None:
        super().__init__(user_agent=user_agent, **kwargs)
        self.series_ids = tuple(series_ids)
        self.api_key_env = api_key_env

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise ConnectorError(f"{self.api_key_env} is not configured")
        retrieved_at = datetime.now(UTC)
        source_id = f"fred-{retrieved_at:%Y%m%dT%H%M%SZ}"
        observations: list[UnifiedObservation] = []
        hashes: dict[str, Any] = {}
        for series_id in self.series_ids:
            query = urllib.parse.urlencode(
                {
                    "series_id": series_id,
                    "api_key": api_key,
                    "file_type": "json",
                    "observation_end": as_of.date().isoformat(),
                }
            )
            url = f"https://api.stlouisfed.org/fred/series/observations?{query}"
            payload = self._get_json(url)
            hashes[series_id] = payload
            for item in payload.get("observations", []):
                if item.get("value") in {None, "."}:
                    continue
                observations.append(
                    UnifiedObservation(
                        observation_id=f"{source_id}:{series_id}:{item['date']}",
                        series=f"FRED.{series_id}",
                        timestamp=datetime.fromisoformat(f"{item['date']}T00:00:00+00:00"),
                        value=float(item["value"]),
                        unit="provider_defined",
                        source_id=source_id,
                        domain=DataDomain.MACRO,
                        quality=DataQuality.OFFICIAL,
                    )
                )
        source = SourceProvenance(
            source_id=source_id,
            provider="Federal Reserve Bank of St. Louis FRED",
            uri="https://api.stlouisfed.org/fred/series/observations",
            retrieved_at=retrieved_at,
            data_domain=DataDomain.MACRO,
            quality=DataQuality.OFFICIAL,
            content_hash=stable_hash(hashes),
        )
        return ConnectorResult(source, observations)


class TakeTwoRssConnector:
    """Read Take-Two's official RSS feed without treating headlines as decisions."""

    connector_id = "take_two_rss"

    def __init__(
        self,
        *,
        feed_url: str,
        opener: Callable[..., Any] = urllib.request.urlopen,
        timeout_seconds: float = 15,
    ) -> None:
        self.feed_url = feed_url
        self._opener = opener
        self.timeout_seconds = timeout_seconds

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        request = urllib.request.Request(
            self.feed_url,
            headers={"User-Agent": "take-two-options-v11/0.11 research-only"},
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
            root = ET.fromstring(raw)
        except (OSError, ET.ParseError) as error:
            raise ConnectorError(f"official RSS fetch failed: {error}") from error
        retrieved_at = datetime.now(UTC)
        source_id = f"take-two-rss-{retrieved_at:%Y%m%dT%H%M%SZ}"
        observations: list[UnifiedObservation] = []
        missing_or_invalid_dates = 0
        post_cutoff_items = 0
        for index, item in enumerate(root.findall(".//item")):
            title = item.findtext("title")
            published = item.findtext("pubDate")
            if not title or not published:
                missing_or_invalid_dates += 1
                continue
            try:
                timestamp = parsedate_to_datetime(published)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)
                timestamp = timestamp.astimezone(UTC)
            except (TypeError, ValueError):
                missing_or_invalid_dates += 1
                continue
            if timestamp > as_of:
                post_cutoff_items += 1
                continue
            observations.append(
                UnifiedObservation(
                    observation_id=f"{source_id}:{index}",
                    series=f"{ticker.upper()}.official_news",
                    timestamp=timestamp,
                    value=title,
                    unit="headline",
                    source_id=source_id,
                    domain=DataDomain.CATALYST,
                    quality=DataQuality.OFFICIAL,
                    metadata={
                        "published_raw": published or "",
                        "link": item.findtext("link") or "",
                    },
                )
            )
        source = SourceProvenance(
            source_id=source_id,
            provider="Take-Two Investor Relations RSS",
            uri=self.feed_url,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.CATALYST,
            quality=DataQuality.OFFICIAL,
            content_hash=stable_hash(raw.decode("utf-8", errors="replace")),
        )
        warnings = []
        if missing_or_invalid_dates:
            warnings.append(
                f"{missing_or_invalid_dates} RSS item(s) lacked a usable publication timestamp "
                "and were excluded."
            )
        if post_cutoff_items:
            warnings.append(
                f"{post_cutoff_items} post-cutoff RSS item(s) were excluded."
            )
        return ConnectorResult(source, observations, warnings)


class GoogleTrendsAlphaConnector:
    """Normalize the limited-access official Google Trends API alpha."""

    connector_id = "google_trends_alpha"

    def __init__(
        self,
        port: GoogleTrendsDataPort,
        *,
        terms: Iterable[str],
        region: str = "US",
    ) -> None:
        self.port = port
        self.terms = list(terms)
        self.region = region

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        try:
            rows = self.port.interest(terms=self.terms, end=as_of, region=self.region)
        except Exception as error:
            raise ConnectorError(f"Google Trends alpha fetch failed: {error}") from error
        retrieved_at = datetime.now(UTC)
        source_id = f"google-trends-alpha-{retrieved_at:%Y%m%dT%H%M%SZ}"
        observations = []
        post_cutoff_rows = 0
        for row in rows:
            timestamp = _parse_utc_timestamp(
                row["timestamp"],
                field="Google Trends row timestamp",
            )
            if timestamp > as_of:
                post_cutoff_rows += 1
                continue
            observations.append(
                UnifiedObservation(
                    observation_id=f"{source_id}:{row['term']}:{row['timestamp']}",
                    series=f"GOOGLE_TRENDS.{row['term']}",
                    timestamp=timestamp,
                    value=float(row["value"]),
                    unit="consistently_scaled_search_interest",
                    source_id=source_id,
                    domain=DataDomain.ATTENTION,
                    quality=DataQuality.OFFICIAL,
                    metadata={"region": str(row.get("region", self.region))},
                )
            )
        source = SourceProvenance(
            source_id=source_id,
            provider="Google Trends API alpha",
            uri="https://developers.google.com/search/apis/trends",
            retrieved_at=retrieved_at,
            data_domain=DataDomain.ATTENTION,
            quality=DataQuality.OFFICIAL,
            license_or_terms="Limited alpha access; provider terms and quota apply.",
            content_hash=stable_hash(rows),
            notes=[
                "Search interest is not absolute search volume.",
                "Attention-family evidence is capped in the Bayesian engine.",
            ],
        )
        return ConnectorResult(
            source,
            observations,
            (
                [f"{post_cutoff_rows} post-cutoff Trends row(s) were excluded."]
                if post_cutoff_rows
                else []
            ),
        )


class MarketCalendarConnector:
    """Normalize an official or licensed exchange-session calendar port."""

    connector_id = "market_calendar"

    def __init__(
        self,
        port: MarketCalendarDataPort,
        *,
        provider: str,
        exchange: str = "XNAS",
        quality: DataQuality = DataQuality.OFFICIAL,
        uri: str | None = None,
    ) -> None:
        self.port = port
        self.provider = provider
        self.exchange = exchange
        self.quality = quality
        self.uri = uri

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        try:
            rows = self.port.sessions(exchange=self.exchange, end=as_of)
        except Exception as error:
            raise ConnectorError(f"market calendar fetch failed: {error}") from error
        retrieved_at = datetime.now(UTC)
        source_id = (
            f"market-calendar-{self.exchange.lower()}-"
            f"{retrieved_at:%Y%m%dT%H%M%SZ}"
        )
        observations: list[UnifiedObservation] = []
        post_cutoff_rows = 0
        for row in rows:
            session = _parse_utc_timestamp(
                row["timestamp"],
                field=f"{self.exchange} session timestamp",
            )
            if session > as_of:
                post_cutoff_rows += 1
                continue
            observations.append(
                UnifiedObservation(
                    observation_id=f"{source_id}:{session.date().isoformat()}",
                    series="US.market_calendar",
                    timestamp=session,
                    value=bool(row.get("is_open", True)),
                    unit="session_open_boolean",
                    source_id=source_id,
                    domain=DataDomain.MARKET,
                    quality=self.quality,
                    metadata={
                        "exchange": self.exchange,
                        "opens_at": str(row.get("opens_at", "")),
                        "closes_at": str(row.get("closes_at", "")),
                        "early_close": bool(row.get("early_close", False)),
                    },
                )
            )
        source = SourceProvenance(
            source_id=source_id,
            provider=self.provider,
            uri=self.uri,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.MARKET,
            quality=self.quality,
            content_hash=stable_hash(rows),
            notes=["Calendar rows are filtered at the report cutoff."],
        )
        return ConnectorResult(
            source,
            observations,
            (
                [f"{post_cutoff_rows} post-cutoff calendar row(s) were excluded."]
                if post_cutoff_rows
                else []
            ),
        )


class IBKROpraConnector:
    """Normalize injected IBKR/OPRA market data while exposing no trading operation."""

    connector_id = "ibkr_opra_read_only"

    def __init__(self, port: IBKRDataPort) -> None:
        self.port = port

    def fetch(self, *, ticker: str, as_of: datetime) -> ConnectorResult:
        try:
            payload = self.port.option_chain_snapshot(ticker)
        except Exception as error:  # broker adapters may raise provider-specific exceptions
            raise ConnectorError(f"IBKR snapshot failed: {error}") from error
        retrieved_at = datetime.now(UTC)
        source_id = str(payload.get("source_id", f"ibkr-opra-{retrieved_at:%Y%m%dT%H%M%SZ}"))
        source = SourceProvenance(
            source_id=source_id,
            provider="Interactive Brokers TWS API / OPRA entitlement",
            uri=None,
            retrieved_at=retrieved_at,
            data_domain=DataDomain.OPTIONS,
            quality=DataQuality.OPRA,
            license_or_terms="Account market-data entitlements and OPRA terms apply.",
            notes=["Read-only port; no submit, modify, cancel, or exercise method exists."],
        )
        observations: list[UnifiedObservation] = []
        warnings: list[str] = []
        spot = payload.get("spot")
        spot_timestamp_raw = payload.get("spot_timestamp", payload.get("timestamp"))
        if spot is not None and spot_timestamp_raw is None:
            warnings.append("Broker spot lacked a timestamp and was excluded.")
        elif spot is not None:
            spot_timestamp = _parse_utc_timestamp(
                spot_timestamp_raw,
                field="broker spot timestamp",
            )
            if spot_timestamp > as_of:
                warnings.append("Post-cutoff broker spot was excluded.")
            else:
                observations.append(
                    UnifiedObservation(
                        observation_id=f"{source_id}:spot",
                        series=f"{ticker.upper()}.spot",
                        timestamp=spot_timestamp,
                        value=float(spot),
                        unit="USD_per_share",
                        source_id=source_id,
                        domain=DataDomain.MARKET,
                        quality=DataQuality.LIVE_BROKER,
                    )
                )
        post_cutoff_quotes = 0
        missing_quote_timestamps = 0
        for quote in payload.get("quotes", []):
            symbol = str(quote["symbol"])
            timestamp_raw = quote.get("timestamp")
            if timestamp_raw is None:
                missing_quote_timestamps += 1
                continue
            timestamp = _parse_utc_timestamp(
                timestamp_raw,
                field=f"broker quote timestamp for {symbol}",
            )
            if timestamp > as_of:
                post_cutoff_quotes += 1
                continue
            for field, unit in (
                ("bid", "USD_per_share"),
                ("ask", "USD_per_share"),
                ("implied_volatility", "annual_decimal"),
                ("volume", "contracts"),
                ("open_interest", "contracts"),
            ):
                value = quote.get(field)
                if value is None:
                    continue
                observations.append(
                    UnifiedObservation(
                        observation_id=f"{source_id}:{symbol}:{field}",
                        series=f"option.{symbol}.{field}",
                        timestamp=timestamp,
                        value=(
                            float(value)
                            if field not in {"volume", "open_interest"}
                            else int(value)
                        ),
                        unit=unit,
                        source_id=source_id,
                        domain=DataDomain.OPTIONS,
                        quality=DataQuality.OPRA,
                    )
                )
        if missing_quote_timestamps:
            warnings.append(
                f"{missing_quote_timestamps} quote(s) lacked timestamps and were excluded."
            )
        if post_cutoff_quotes:
            warnings.append(
                f"{post_cutoff_quotes} post-cutoff quote(s) were excluded."
            )
        return ConnectorResult(source, observations, warnings)

    def quote_combo(
        self,
        *,
        candidate_id: str,
        legs: list[dict[str, Any]],
    ) -> ComboQuote:
        try:
            payload = self.port.combo_quote(candidate_id, legs)
        except Exception as error:
            return ComboQuote(
                candidate_id=candidate_id,
                warnings=[f"IBKR combo quote unavailable: {error}"],
            )
        timestamp = payload.get("timestamp")
        return ComboQuote(
            candidate_id=candidate_id,
            bid=payload.get("bid"),
            ask=payload.get("ask"),
            timestamp=(
                _parse_utc_timestamp(timestamp, field="broker combo timestamp")
                if timestamp
                else None
            ),
            source_id=payload.get("source_id"),
            executable=bool(payload.get("executable", False)),
            warnings=list(payload.get("warnings", [])),
        )
