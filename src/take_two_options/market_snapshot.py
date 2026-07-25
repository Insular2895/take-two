"""Refresh and normalize read-only option chains without exposing credentials."""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from take_two_options.alpaca_data import AlpacaOptionChainExport
from take_two_options.knowledge.provenance import stable_hash
from take_two_options.knowledge.schemas import MarketSnapshot, QuoteSnapshot
from take_two_options.marketdata_data import (
    MarketDataChainExport,
    MarketDataError,
    MarketDataReadOnlyClient,
    parse_occ_option_symbol,
)


class MarketSnapshotError(RuntimeError):
    """Raised when no authentic chain can be refreshed or loaded."""


def load_local_environment(path: Path = Path(".env")) -> list[str]:
    """Load missing keys only; values are never returned or logged."""

    loaded: list[str] = []
    if not path.is_file():
        return loaded
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip()
            loaded.append(key)
    return loaded


def configured_provider_keys() -> list[str]:
    return sorted(
        key
        for key in ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "MARKETDATA_TOKEN")
        if os.getenv(key)
    )


def _marketdata_snapshot(export: MarketDataChainExport, cache_path: Path) -> MarketSnapshot:
    spots = [
        record.underlying_price
        for record in export.contracts
        if record.underlying_price is not None
    ]
    if not spots:
        raise MarketSnapshotError("MarketData.app chain has no underlying price")
    quotes = [
        QuoteSnapshot(
            symbol=record.option_symbol,
            expiration=record.expiration.date(),
            option_type=record.option_type,
            strike=record.strike,
            bid=record.bid or 0.0,
            ask=record.ask or 0.0,
            volume=int(record.volume) if record.volume is not None else None,
            open_interest=(
                int(record.open_interest) if record.open_interest is not None else None
            ),
            implied_volatility=(
                record.vendor_implied_volatility
                or (
                    record.computed_analytics.implied_volatility
                    if record.computed_analytics is not None
                    else None
                )
            ),
            delta=(
                record.vendor_delta
                or (
                    record.computed_analytics.delta
                    if record.computed_analytics is not None
                    else None
                )
            ),
            quote_timestamp=record.quote_timestamp,
            multiplier=100,
            price_quality="eod_bid_ask",
            source_id=export.source.id,
        )
        for record in export.contracts
    ]
    as_of = max(quote.quote_timestamp for quote in quotes)
    spot = sorted(spots)[len(spots) // 2]
    return MarketSnapshot(
        snapshot_id=f"snapshot-{stable_hash(export.model_dump(mode='json'))[:16]}",
        ticker=export.ticker,
        as_of=as_of,
        spot=spot,
        spot_timestamp=as_of,
        quote_quality="eod_bid_ask",
        source_ids=[export.source.id],
        quotes=quotes,
        available_expirations=sorted({quote.expiration for quote in quotes}),
        data_warnings=[
            "End-of-day bid/ask does not prove an intraday or simultaneous combo fill",
            "Contract multiplier is normalized to 100 and must be rechecked with the broker",
        ],
        cache_path=str(cache_path),
    )


def _alpaca_snapshot(export: AlpacaOptionChainExport, cache_path: Path) -> MarketSnapshot:
    quotes: list[QuoteSnapshot] = []
    for record in export.contracts:
        parsed = parse_occ_option_symbol(record.symbol)
        if record.quote_timestamp is None:
            continue
        quotes.append(
            QuoteSnapshot(
                symbol=record.symbol,
                expiration=parsed.expiration,
                option_type=parsed.option_type,
                strike=parsed.strike,
                bid=record.bid or 0.0,
                ask=record.ask or 0.0,
                volume=None,
                open_interest=None,
                implied_volatility=record.implied_volatility,
                delta=record.delta,
                quote_timestamp=record.quote_timestamp,
                multiplier=100,
                price_quality="indicative",
                source_id=export.source.id,
            )
        )
    if not quotes:
        raise MarketSnapshotError("Alpaca chain has no timestamped option quotes")
    raise MarketSnapshotError(
        "Alpaca option snapshots do not provide the underlying price or open interest; "
        "a normalized MarketData.app snapshot is required for ranking"
    )


def refresh_market_snapshot(
    *,
    ticker: str,
    as_of: date,
    strike_limit: int,
    cache_dir: Path = Path("data/marketdata/cache"),
    snapshot_dir: Path = Path("data/marketdata/snapshots"),
) -> MarketSnapshot:
    load_local_environment()
    if not os.getenv("MARKETDATA_TOKEN"):
        raise MarketSnapshotError("MARKETDATA_TOKEN is not configured")
    client = MarketDataReadOnlyClient.from_env(cache_dir=cache_dir)
    errors: list[str] = []
    for offset in range(0, 8):
        quote_date = as_of - timedelta(days=offset)
        if quote_date.weekday() >= 5:
            continue
        try:
            export = client.historical_chain(
                ticker=ticker,
                quote_date=quote_date,
                expiration="all",
                side=None,
                strikes=None,
                strike_limit=strike_limit,
                min_open_interest=None,
                min_volume=None,
                risk_free_rate=None,
                continuous_dividend_yield=0.0,
                force_refresh=False,
            )
        except MarketDataError as error:
            errors.append(f"{quote_date.isoformat()}: {error}")
            continue
        if not export.contracts:
            errors.append(f"{quote_date.isoformat()}: empty chain")
            continue
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_dir / f"{ticker.upper()}_{quote_date.isoformat()}.json"
        snapshot = _marketdata_snapshot(export, path)
        path.write_text(snapshot.model_dump_json(indent=2), encoding="utf-8")
        return snapshot
    raise MarketSnapshotError("no recent MarketData.app chain: " + "; ".join(errors))


def load_latest_market_snapshot(
    *,
    ticker: str,
    as_of: date,
    snapshot_dir: Path = Path("data/marketdata/snapshots"),
) -> MarketSnapshot:
    candidates: list[tuple[date, Path]] = []
    for path in snapshot_dir.glob(f"{ticker.upper()}_*.json"):
        try:
            embedded_date = date.fromisoformat(path.stem.rsplit("_", 1)[1])
        except ValueError:
            continue
        if embedded_date <= as_of:
            candidates.append((embedded_date, path))
    if candidates:
        _, newest = max(candidates)
        return MarketSnapshot.model_validate_json(newest.read_text(encoding="utf-8"))

    legacy_marketdata = Path("data/marketdata/ttwo_2026-07-17_jan27_calls.json")
    if ticker.upper() == "TTWO" and legacy_marketdata.is_file():
        export = MarketDataChainExport.model_validate_json(
            legacy_marketdata.read_text(encoding="utf-8")
        )
        return _marketdata_snapshot(export, legacy_marketdata)
    legacy_alpaca = Path("data/alpaca/ttwo_option_chain_2026-07-19.json")
    if ticker.upper() == "TTWO" and legacy_alpaca.is_file():
        alpaca_export = AlpacaOptionChainExport.model_validate_json(
            legacy_alpaca.read_text(encoding="utf-8")
        )
        return _alpaca_snapshot(alpaca_export, legacy_alpaca)
    raise MarketSnapshotError(f"no cached normalized snapshot for {ticker} through {as_of}")


def snapshot_manifest(snapshot: MarketSnapshot) -> str:
    return json.dumps(
        {
            "snapshot_id": snapshot.snapshot_id,
            "ticker": snapshot.ticker,
            "as_of": snapshot.as_of.isoformat(),
            "spot": snapshot.spot,
            "spot_timestamp": snapshot.spot_timestamp.isoformat(),
            "quote_quality": snapshot.quote_quality,
            "source_ids": snapshot.source_ids,
            "contracts": len(snapshot.quotes),
            "expirations": [value.isoformat() for value in snapshot.available_expirations],
            "data_warnings": snapshot.data_warnings,
            "cache_path": snapshot.cache_path,
            "generated_at": datetime.now(UTC).isoformat(),
        },
        indent=2,
    )
