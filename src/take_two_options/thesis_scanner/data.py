"""Read chain files into one provenance-preserving V10 contract."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from take_two_options.alpaca_data import AlpacaOptionChainExport
from take_two_options.calibration import CalibrationDataset
from take_two_options.knowledge.schemas import MarketSnapshot
from take_two_options.marketdata_data import parse_occ_option_symbol
from take_two_options.thesis_scanner.schemas import (
    ThesisChain,
    ThesisQuote,
)


class ThesisChainError(ValueError):
    """Raised when a chain cannot preserve required provenance."""


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _payload(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ThesisChainError(f"cannot read {path}: {error}") from error
    if not isinstance(value, dict):
        raise ThesisChainError(f"{path}: expected one JSON object")
    return value


def _spot_from_calibration(
    *,
    ticker: str,
    chain_time: datetime,
    chain_path: Path,
) -> tuple[float, datetime, str] | None:
    roots = [chain_path.parent, Path("data/alpaca")]
    paths = sorted(
        {
            path
            for root in roots
            for path in root.glob(f"{ticker.lower()}_calibration_dataset_*.json")
        }
    )
    for path in reversed(paths):
        try:
            dataset = CalibrationDataset.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        eligible = [
            point
            for point in dataset.points
            if _utc(point.timestamp) <= chain_time and _utc(point.data_available_at) <= chain_time
        ]
        if eligible:
            newest = max(eligible, key=lambda item: _utc(item.timestamp))
            return newest.close, _utc(newest.timestamp), dataset.source.id
    return None


def _from_market_snapshot(snapshot: MarketSnapshot, path: Path) -> ThesisChain:
    quality = (
        "opra"
        if snapshot.quote_quality == "live_broker"
        else snapshot.quote_quality
        if snapshot.quote_quality in {"eod_bid_ask", "indicative"}
        else "unknown"
    )
    return ThesisChain(
        ticker=snapshot.ticker,
        as_of=_utc(snapshot.as_of),
        retrieved_at=_utc(snapshot.as_of),
        spot=snapshot.spot,
        spot_timestamp=_utc(snapshot.spot_timestamp),
        spot_source_id=snapshot.source_ids[0],
        price_quality=quality,
        source_id=snapshot.source_ids[0],
        quotes=[
            ThesisQuote(
                symbol=quote.symbol,
                expiration=quote.expiration,
                option_type=quote.option_type,
                strike=quote.strike,
                bid=quote.bid,
                ask=quote.ask,
                volume=quote.volume,
                open_interest=quote.open_interest,
                implied_volatility=quote.implied_volatility,
                delta=quote.delta,
                quote_timestamp=_utc(quote.quote_timestamp),
                multiplier=quote.multiplier,
                multiplier_status="assumed",
                standard_contract=None,
                price_quality=quality,
                source_id=quote.source_id,
            )
            for quote in snapshot.quotes
        ],
        warnings=[
            *snapshot.data_warnings,
            (
                "Contract multiplier is present but deliverable/adjustment status is "
                "not broker-confirmed"
            ),
        ],
        source_path=str(path),
    )


def _from_alpaca(
    export: AlpacaOptionChainExport,
    path: Path,
    *,
    spot_override: float | None,
) -> ThesisChain:
    timestamped = [
        _utc(record.quote_timestamp)
        for record in export.contracts
        if record.quote_timestamp is not None
    ]
    if not timestamped:
        raise ThesisChainError("Alpaca chain has no timestamped quote")
    chain_time = max(timestamped)
    warnings = [
        (
            "Alpaca indicative is a derived feed, not an OPRA-executable quote"
            if export.feed == "indicative"
            else "OPRA source label does not guarantee a future fill"
        ),
        "Alpaca chain export does not provide open interest or contract deliverables",
        "Multiplier 100 is an explicit standard-contract assumption, not broker confirmation",
    ]
    if spot_override is not None:
        spot = spot_override
        spot_timestamp = chain_time
        spot_source = "cli-spot-override"
        warnings.append("Underlying spot was supplied explicitly on the command line")
    else:
        spot_record = _spot_from_calibration(
            ticker=export.ticker,
            chain_time=chain_time,
            chain_path=path,
        )
        if spot_record is None:
            raise ThesisChainError(
                "Alpaca option-chain exports contain no underlying spot; provide "
                "--spot or a timestamp-compatible calibration dataset"
            )
        spot, spot_timestamp, spot_source = spot_record
        warnings.append("Underlying spot comes from the latest look-ahead-safe calibration close")
    quotes: list[ThesisQuote] = []
    for record in export.contracts:
        try:
            parsed = parse_occ_option_symbol(record.symbol)
        except ValueError:
            continue
        quotes.append(
            ThesisQuote(
                symbol=parsed.symbol,
                expiration=parsed.expiration,
                option_type=parsed.option_type,
                strike=parsed.strike,
                bid=record.bid,
                ask=record.ask,
                bid_size=int(record.bid_size) if record.bid_size is not None else None,
                ask_size=int(record.ask_size) if record.ask_size is not None else None,
                volume=None,
                open_interest=None,
                implied_volatility=record.implied_volatility,
                delta=record.delta,
                gamma=record.gamma,
                theta=record.theta,
                vega=record.vega,
                rho=record.rho,
                quote_timestamp=(
                    _utc(record.quote_timestamp) if record.quote_timestamp is not None else None
                ),
                multiplier=100,
                multiplier_status="assumed",
                standard_contract=None,
                price_quality=export.feed,
                source_id=export.source.id,
            )
        )
    if not quotes:
        raise ThesisChainError("Alpaca chain contains no parseable OCC option symbol")
    return ThesisChain(
        ticker=export.ticker,
        as_of=chain_time,
        retrieved_at=_utc(export.retrieved_at),
        spot=spot,
        spot_timestamp=spot_timestamp,
        spot_source_id=spot_source,
        price_quality=export.feed,
        source_id=export.source.id,
        quotes=quotes,
        warnings=warnings,
        source_path=str(path),
    )


def load_thesis_chain(
    path: Path,
    *,
    ticker: str,
    spot_override: float | None = None,
) -> ThesisChain:
    payload = _payload(path)
    try:
        if payload.get("format_version") == "thesis_chain_v1":
            chain = ThesisChain.model_validate(payload)
            chain.source_path = str(path)
        elif "snapshot_id" in payload and "quotes" in payload:
            chain = _from_market_snapshot(MarketSnapshot.model_validate(payload), path)
        elif "feed" in payload and "contracts" in payload:
            chain = _from_alpaca(
                AlpacaOptionChainExport.model_validate(payload),
                path,
                spot_override=spot_override,
            )
        else:
            raise ThesisChainError(
                f"{path}: unsupported chain format; expected thesis_chain_v1, "
                "MarketSnapshot, or AlpacaOptionChainExport"
            )
    except ValueError as error:
        if isinstance(error, ThesisChainError):
            raise
        raise ThesisChainError(f"{path}: {error}") from error
    if chain.ticker.upper() != ticker.upper():
        raise ThesisChainError(f"chain ticker {chain.ticker!r} does not match request {ticker!r}")
    return chain
