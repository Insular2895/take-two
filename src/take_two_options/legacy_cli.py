"""Legacy V1-V9 command-line interface, isolated from the active optimizer."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Annotated, Literal, NoReturn, cast

import typer
from alpaca.common.exceptions import APIError, RetryException

from take_two_options.accuracy import (
    AccuracyGeneratorSpec,
    MarketDataAccuracyReport,
    MarketDataAccuracySuiteSpec,
    generate_accuracy_suite_spec,
    load_current_expirations,
    load_market_closes,
    load_market_sessions,
    render_accuracy_markdown,
    run_accuracy_suite,
)
from take_two_options.accuracy_dashboard import build_accuracy_dashboard_artifact
from take_two_options.alpaca_data import (
    AlpacaDataError,
    AlpacaOptionBacktestSpec,
    AlpacaReadOnlyMarketData,
)
from take_two_options.backtesting import (
    BacktestDataset,
    render_backtest_markdown,
    run_backtest,
)
from take_two_options.calibration import (
    CalibrationDataset,
    calibrate_dataset,
    render_calibration_markdown,
)
from take_two_options.data import FixtureDataProvider
from take_two_options.domain import DecisionReport
from take_two_options.engine import analyze_bundle
from take_two_options.marketdata_data import (
    MarketDataError,
    MarketDataOptionBacktestSpec,
    MarketDataReadOnlyClient,
)
from take_two_options.marketdata_panel import (
    MarketDataPanelSpec,
    render_marketdata_panel_markdown,
    run_marketdata_panel,
)
from take_two_options.reporting import render_decision_journal, render_json, render_markdown
from take_two_options.treasury_data import (
    TreasuryDataError,
    TreasuryYieldCurve,
    fetch_treasury_year,
)

app = typer.Typer(
    no_args_is_help=True,
    help="Read-only TTWO options research. No command can submit or modify an order.",
)


def _write(path: Path | None, content: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _stock_feed(value: str) -> Literal["iex", "sip"]:
    normalized = value.lower()
    if normalized not in {"iex", "sip"}:
        raise typer.BadParameter("stock feed must be iex or sip")
    return cast(Literal["iex", "sip"], normalized)


def _option_feed(value: str) -> Literal["indicative", "opra"]:
    normalized = value.lower()
    if normalized not in {"indicative", "opra"}:
        raise typer.BadParameter("option feed must be indicative or opra")
    return cast(Literal["indicative", "opra"], normalized)


def _optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter("dates must use YYYY-MM-DD") from error


def _iso_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise typer.BadParameter("timestamps must use ISO-8601") from error


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter("dates must use YYYY-MM-DD") from error


def _marketdata_expiration(value: str | None) -> date | Literal["all"] | None:
    if value is None:
        return None
    if value.lower() == "all":
        return "all"
    return _iso_date(value)


def _strike_values(value: str | None) -> list[float] | None:
    if value is None:
        return None
    try:
        strikes = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise typer.BadParameter("strikes must be comma-separated numbers") from error
    if not strikes or any(strike <= 0 for strike in strikes):
        raise typer.BadParameter("strikes must contain positive numbers")
    return strikes


def _alpaca_failure(error: Exception) -> NoReturn:
    typer.echo(f"Alpaca read-only data error: {error}", err=True)
    raise typer.Exit(code=1)


def _marketdata_failure(error: Exception) -> NoReturn:
    typer.echo(f"MarketData.app read-only data error: {error}", err=True)
    raise typer.Exit(code=1)


@app.command()
def analyze(
    fixture: Annotated[
        Path,
        typer.Option("--fixture", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
    journal_out: Annotated[Path | None, typer.Option("--journal-out")] = None,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Analyze one explicit fixture and emit auditable research artifacts."""
    report = analyze_bundle(FixtureDataProvider(fixture).load_bundle())
    json_text = render_json(report)
    _write(json_out, json_text)
    _write(markdown_out, render_markdown(report))
    _write(journal_out, render_decision_journal(report))
    if print_json:
        typer.echo(json_text)
    else:
        typer.echo(
            f"{report.report_id}: {len(report.candidates)} candidates, "
            f"{len(report.ranked_candidate_ids)} scored, order capability forbidden"
        )


@app.command()
def calibrate(
    fixture: Annotated[
        Path,
        typer.Option("--fixture", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Calibrate only parameters supported by timestamped training data."""
    dataset = CalibrationDataset.model_validate_json(fixture.read_text(encoding="utf-8"))
    report = calibrate_dataset(dataset)
    json_text = report.model_dump_json(indent=2)
    _write(json_out, json_text)
    _write(markdown_out, render_calibration_markdown(report))
    if print_json:
        typer.echo(json_text)
    else:
        typer.echo(
            f"{report.ticker}: {len(report.results)} calibration results, "
            f"readiness {report.model_readiness.value}"
        )


@app.command()
def backtest(
    fixture: Annotated[
        Path,
        typer.Option("--fixture", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Run a train/test options backtest with look-ahead controls."""
    dataset = BacktestDataset.model_validate_json(fixture.read_text(encoding="utf-8"))
    report = run_backtest(dataset)
    json_text = report.model_dump_json(indent=2)
    _write(json_out, json_text)
    _write(markdown_out, render_backtest_markdown(report))
    if print_json:
        typer.echo(json_text)
    else:
        typer.echo(
            f"{report.ticker}: train n={report.train_metrics.observations}, "
            f"test n={report.test_metrics.observations}, order capability forbidden"
        )


@app.command("alpaca-check")
def alpaca_check(
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    stock_feed: Annotated[str, typer.Option("--stock-feed")] = "iex",
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Verify read-only Alpaca stock-data access without touching trading APIs."""
    try:
        report = AlpacaReadOnlyMarketData.from_env().check_connection(
            ticker=ticker.upper(), feed=_stock_feed(stock_feed)
        )
    except (AlpacaDataError, APIError, RetryException) as error:
        _alpaca_failure(error)
    if print_json:
        typer.echo(report.model_dump_json(indent=2))
    else:
        typer.echo(
            f"Alpaca read-only connected: {report.ticker}, feed={report.stock_feed}, "
            f"bars={report.bars_received}, order capability forbidden"
        )


@app.command("alpaca-chain")
def alpaca_chain(
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    feed: Annotated[str, typer.Option("--feed")] = "indicative",
    expiration_from: Annotated[str | None, typer.Option("--expiration-from")] = None,
    expiration_to: Annotated[str | None, typer.Option("--expiration-to")] = None,
    strike_min: Annotated[float | None, typer.Option("--strike-min")] = None,
    strike_max: Annotated[float | None, typer.Option("--strike-max")] = None,
    option_type: Annotated[str | None, typer.Option("--option-type")] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Export a current Alpaca option chain with quote, IV, and Greek provenance."""
    normalized_type = option_type.lower() if option_type else None
    if normalized_type not in {None, "call", "put"}:
        raise typer.BadParameter("option type must be call or put")
    try:
        export = AlpacaReadOnlyMarketData.from_env().option_chain(
            ticker=ticker.upper(),
            feed=_option_feed(feed),
            expiration_date_gte=_optional_date(expiration_from),
            expiration_date_lte=_optional_date(expiration_to),
            strike_price_gte=strike_min,
            strike_price_lte=strike_max,
            option_type=cast(Literal["call", "put"] | None, normalized_type),
        )
    except (AlpacaDataError, APIError, RetryException) as error:
        _alpaca_failure(error)
    json_text = export.model_dump_json(indent=2)
    _write(json_out, json_text)
    if print_json:
        typer.echo(json_text)
    else:
        typer.echo(
            f"Alpaca {export.feed} chain: {export.ticker}, "
            f"contracts={len(export.contracts)}, order capability forbidden"
        )


@app.command("alpaca-calibrate")
def alpaca_calibrate(
    start: Annotated[str, typer.Option("--start")],
    end: Annotated[str, typer.Option("--end")],
    training_cutoff: Annotated[str, typer.Option("--training-cutoff")],
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    stock_feed: Annotated[str, typer.Option("--stock-feed")] = "iex",
    jump_threshold_sigma: Annotated[float, typer.Option("--jump-threshold-sigma")] = 2.5,
    dataset_out: Annotated[Path | None, typer.Option("--dataset-out")] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
) -> None:
    """Fetch real Alpaca equity bars, persist the dataset, and calibrate supported models."""
    try:
        dataset = AlpacaReadOnlyMarketData.from_env().calibration_dataset(
            ticker=ticker.upper(),
            start=_iso_datetime(start),
            end=_iso_datetime(end),
            training_cutoff=_iso_datetime(training_cutoff),
            feed=_stock_feed(stock_feed),
            jump_threshold_sigma=jump_threshold_sigma,
        )
        report = calibrate_dataset(dataset)
    except (AlpacaDataError, APIError, RetryException) as error:
        _alpaca_failure(error)
    _write(dataset_out, dataset.model_dump_json(indent=2))
    _write(json_out, report.model_dump_json(indent=2))
    _write(markdown_out, render_calibration_markdown(report))
    typer.echo(
        f"Alpaca calibration: {report.ticker}, observations={report.results[0].observations}, "
        f"readiness={report.model_readiness.value}, order capability forbidden"
    )


@app.command("alpaca-backtest")
def alpaca_backtest(
    spec: Annotated[
        Path,
        typer.Option("--spec", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    dataset_out: Annotated[Path | None, typer.Option("--dataset-out")] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
) -> None:
    """Build and run a real-bar option backtest with explicit execution-proxy labeling."""
    specification = AlpacaOptionBacktestSpec.model_validate_json(spec.read_text(encoding="utf-8"))
    try:
        dataset = AlpacaReadOnlyMarketData.from_env().option_backtest_dataset(specification)
        report = run_backtest(dataset)
    except (AlpacaDataError, APIError, RetryException) as error:
        _alpaca_failure(error)
    _write(dataset_out, dataset.model_dump_json(indent=2))
    _write(json_out, report.model_dump_json(indent=2))
    _write(markdown_out, render_backtest_markdown(report))
    typer.echo(
        f"Alpaca option backtest: train={report.train_metrics.observations}, "
        f"test={report.test_metrics.observations}, prices={report.execution_price_quality}, "
        "order capability forbidden"
    )


@app.command("marketdata-chain")
def marketdata_chain(
    quote_date: Annotated[str, typer.Option("--date")],
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    expiration: Annotated[str | None, typer.Option("--expiration")] = None,
    side: Annotated[str | None, typer.Option("--side")] = None,
    strikes: Annotated[str | None, typer.Option("--strikes")] = None,
    strike_limit: Annotated[int | None, typer.Option("--strike-limit")] = 10,
    min_open_interest: Annotated[int | None, typer.Option("--min-open-interest")] = None,
    min_volume: Annotated[int | None, typer.Option("--min-volume")] = None,
    risk_free_rate: Annotated[float | None, typer.Option("--risk-free-rate")] = None,
    dividend_yield: Annotated[float, typer.Option("--dividend-yield")] = 0.0,
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("data/marketdata/cache"),
    force_refresh: Annotated[bool, typer.Option("--force-refresh")] = False,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Fetch a filtered historical EOD option chain; no account or order API is used."""
    normalized_side = side.lower() if side else None
    if normalized_side not in {None, "call", "put"}:
        raise typer.BadParameter("side must be call or put")
    try:
        export = MarketDataReadOnlyClient.from_env(cache_dir=cache_dir).historical_chain(
            ticker=ticker.upper(),
            quote_date=_iso_date(quote_date),
            expiration=_marketdata_expiration(expiration),
            side=cast(Literal["call", "put"] | None, normalized_side),
            strikes=_strike_values(strikes),
            strike_limit=strike_limit,
            min_open_interest=min_open_interest,
            min_volume=min_volume,
            risk_free_rate=risk_free_rate,
            continuous_dividend_yield=dividend_yield,
            force_refresh=force_refresh,
        )
    except MarketDataError as error:
        _marketdata_failure(error)
    json_text = export.model_dump_json(indent=2)
    _write(json_out, json_text)
    if print_json:
        typer.echo(json_text)
    else:
        analytics_count = sum(
            contract.computed_analytics is not None for contract in export.contracts
        )
        typer.echo(
            f"MarketData.app EOD chain: {export.ticker} {export.requested_date}, "
            f"contracts={len(export.contracts)}, local_analytics={analytics_count}, "
            f"cache_hit={export.cache_hit}, credits_remaining={export.usage.remaining}, "
            "order capability forbidden"
        )


@app.command("marketdata-backtest")
def marketdata_backtest(
    spec: Annotated[
        Path,
        typer.Option("--spec", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("data/marketdata/cache"),
    force_refresh: Annotated[bool, typer.Option("--force-refresh")] = False,
    dataset_out: Annotated[Path | None, typer.Option("--dataset-out")] = None,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
) -> None:
    """Build and run a source-backed EOD bid/ask option backtest."""
    specification = MarketDataOptionBacktestSpec.model_validate_json(
        spec.read_text(encoding="utf-8")
    )
    try:
        dataset = MarketDataReadOnlyClient.from_env(cache_dir=cache_dir).option_backtest_dataset(
            specification, force_refresh=force_refresh
        )
        report = run_backtest(dataset)
    except MarketDataError as error:
        _marketdata_failure(error)
    _write(dataset_out, dataset.model_dump_json(indent=2))
    _write(json_out, report.model_dump_json(indent=2))
    _write(markdown_out, render_backtest_markdown(report))
    typer.echo(
        f"MarketData.app EOD backtest: train={report.train_metrics.observations}, "
        f"test={report.test_metrics.observations}, prices={report.execution_price_quality}, "
        "order capability forbidden"
    )


@app.command("marketdata-panel")
def marketdata_panel(
    spec: Annotated[
        Path,
        typer.Option("--spec", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("data/marketdata/cache"),
    force_refresh: Annotated[bool, typer.Option("--force-refresh")] = False,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown-out")] = None,
) -> None:
    """Run a prior-signal, later-entry EOD bid/ask strategy panel."""
    specification = MarketDataPanelSpec.model_validate_json(spec.read_text(encoding="utf-8"))
    try:
        report = run_marketdata_panel(
            MarketDataReadOnlyClient.from_env(cache_dir=cache_dir),
            specification,
            force_refresh=force_refresh,
        )
    except MarketDataError as error:
        _marketdata_failure(error)
    _write(json_out, report.model_dump_json(indent=2))
    _write(markdown_out, render_marketdata_panel_markdown(report))
    ranking = ", ".join(strategy.value for strategy in report.ranked_strategy_ids) or "none"
    typer.echo(
        f"MarketData.app panel: requests={report.provider_requests}, "
        f"cache_hits={report.cache_hits}, ranking={ranking}, order capability forbidden"
    )


@app.command("accuracy-spec")
def accuracy_spec(
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    calibration_dataset: Annotated[
        Path,
        typer.Option(
            "--calibration-dataset",
            exists=True,
            readable=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    current_chain: Annotated[
        Path | None,
        typer.Option(
            "--current-chain",
            exists=True,
            readable=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    treasury_cache_dir: Annotated[Path, typer.Option("--treasury-cache-dir")] = Path(
        "data/treasury"
    ),
    force_refresh_rates: Annotated[bool, typer.Option("--force-refresh-rates")] = False,
    json_out: Annotated[Path, typer.Option("--json-out")] = Path(
        "data/marketdata/ttwo_v9_budget_spec.json"
    ),
) -> None:
    """Generate rolling, purged opportunity specs from Alpaca sessions and Treasury rates."""
    generator = AccuracyGeneratorSpec.model_validate_json(config.read_text(encoding="utf-8"))
    try:
        rate_paths = [
            fetch_treasury_year(
                year,
                cache_dir=treasury_cache_dir,
                force_refresh=force_refresh_rates,
            )
            for year in range(generator.start_date.year, generator.end_date.year + 1)
        ]
        curve = TreasuryYieldCurve.from_files(rate_paths)
    except TreasuryDataError as error:
        typer.echo(f"Treasury read-only data error: {error}", err=True)
        raise typer.Exit(code=1) from error
    suite = generate_accuracy_suite_spec(
        generator,
        load_market_sessions(calibration_dataset),
        curve,
        current_expirations=(
            load_current_expirations(current_chain, generator.current_quote_date)
            if current_chain is not None
            else None
        ),
        market_closes=load_market_closes(calibration_dataset),
    )
    _write(json_out, suite.model_dump_json(indent=2))
    typer.echo(
        f"{suite.research_version} opportunity spec: panels={len(suite.panels)}, "
        f"observations={sum(len(panel.observations) for panel in suite.panels)}, "
        "order capability forbidden"
    )


@app.command("marketdata-accuracy")
def marketdata_accuracy(
    spec: Annotated[
        Path,
        typer.Option("--spec", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    cache_dir: Annotated[Path, typer.Option("--cache-dir")] = Path("data/marketdata/cache"),
    force_refresh: Annotated[bool, typer.Option("--force-refresh")] = False,
    json_out: Annotated[Path, typer.Option("--json-out")] = Path(
        "reports/ttwo_v9_budget_report.json"
    ),
    markdown_out: Annotated[Path, typer.Option("--markdown-out")] = Path(
        "reports/ttwo_v9_budget_report.md"
    ),
    artifact_out: Annotated[Path, typer.Option("--artifact-out")] = Path(
        "reports/ttwo_v9_budget_dashboard.artifact.json"
    ),
) -> None:
    """Run source-backed panels, holdout governance, current scan, and dashboard extract."""
    specification = MarketDataAccuracySuiteSpec.model_validate_json(
        spec.read_text(encoding="utf-8")
    )
    try:
        report = run_accuracy_suite(
            MarketDataReadOnlyClient.from_env(cache_dir=cache_dir),
            specification,
            force_refresh=force_refresh,
        )
    except MarketDataError as error:
        _marketdata_failure(error)
    _write(json_out, report.model_dump_json(indent=2))
    _write(markdown_out, render_accuracy_markdown(report))
    artifact = build_accuracy_dashboard_artifact(
        report,
        report_path=str(json_out),
    )
    _write(artifact_out, json.dumps(artifact, indent=2, ensure_ascii=True))
    typer.echo(
        f"{report.research_version} opportunity report: panels={len(report.panels)}, "
        f"variants={len(report.variants)}, "
        f"ranking={','.join(report.ranked_variant_ids)}, order capability forbidden"
    )


@app.command("accuracy-dashboard")
def accuracy_dashboard(
    report_path: Annotated[
        Path,
        typer.Option("--report", exists=True, readable=True, dir_okay=False, resolve_path=True),
    ],
    artifact_out: Annotated[Path, typer.Option("--artifact-out")] = Path(
        "reports/ttwo_v9_budget_dashboard.artifact.json"
    ),
) -> None:
    """Rebuild the canonical dashboard artifact from an existing opportunity report."""
    report = MarketDataAccuracyReport.model_validate_json(report_path.read_text(encoding="utf-8"))
    artifact = build_accuracy_dashboard_artifact(
        report,
        report_path=str(report_path),
    )
    _write(artifact_out, json.dumps(artifact, indent=2, ensure_ascii=True))
    typer.echo(f"{report.research_version} dashboard artifact: {artifact_out}")


@app.command("schema")
def print_schema() -> None:
    """Print the canonical DecisionReport JSON Schema."""
    typer.echo(json.dumps(DecisionReport.model_json_schema(), indent=2))


if __name__ == "__main__":
    app()
