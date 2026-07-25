"""Read-only CLI for knowledge validation and generic option-trade analysis."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from take_two_options.decision.pipeline import analyze_trade
from take_two_options.knowledge.compiler import compile_knowledge
from take_two_options.knowledge.loader import KnowledgeLoadError, load_knowledge
from take_two_options.knowledge.schemas import DecisionReport
from take_two_options.knowledge.validator import validate_knowledge
from take_two_options.legacy_cli import app as legacy_app
from take_two_options.market_snapshot import (
    MarketSnapshotError,
    refresh_market_snapshot,
    snapshot_manifest,
)
from take_two_options.reporting.ibkr_ticket import (
    TicketBlockedError,
    write_ibkr_preview,
)
from take_two_options.thesis_scanner.engine import run_thesis_scan
from take_two_options.thesis_scanner.schemas import ThesisScanRequest

app = typer.Typer(
    no_args_is_help=True,
    help="Read-only option research. This program has no live-order capability.",
)
knowledge_app = typer.Typer(no_args_is_help=True)
data_app = typer.Typer(no_args_is_help=True)
trade_app = typer.Typer(no_args_is_help=True)
position_app = typer.Typer(no_args_is_help=True)
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(data_app, name="data")
app.add_typer(trade_app, name="trade")
app.add_typer(position_app, name="position")
app.add_typer(legacy_app, name="legacy", hidden=True)


def _csv_floats(value: str, *, option_name: str) -> list[float]:
    try:
        values = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise typer.BadParameter(f"{option_name} must be a comma-separated numeric list") from error
    if not values:
        raise typer.BadParameter(f"{option_name} cannot be empty")
    return values


@app.command("thesis-scan")
def thesis_scan(
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    direction: Annotated[str, typer.Option("--direction")] = "bullish",
    budget_eur: Annotated[float, typer.Option("--budget-eur", min=0.01)] = 1_000,
    catalyst_date: Annotated[
        str,
        typer.Option("--catalyst-date"),
    ] = ...,  # type: ignore[assignment]
    expiration_buffer_days: Annotated[
        int,
        typer.Option("--expiration-buffer-days", min=0),
    ] = 45,
    target_prices: Annotated[
        str,
        typer.Option("--target-prices"),
    ] = ...,  # type: ignore[assignment]
    scenario_probabilities: Annotated[
        str | None,
        typer.Option("--scenario-probabilities"),
    ] = None,
    max_loss_eur: Annotated[float, typer.Option("--max-loss-eur", min=0.01)] = 1_000,
    top: Annotated[int, typer.Option("--top", min=1, max=20)] = 3,
    current_chain: Annotated[
        Path,
        typer.Option(
            "--current-chain",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = ...,  # type: ignore[assignment]
    spot: Annotated[float | None, typer.Option("--spot", min=0.01)] = None,
    json_out: Annotated[Path, typer.Option("--json-out")] = Path("reports/thesis_scan/latest.json"),
    markdown_out: Annotated[Path, typer.Option("--markdown-out")] = Path(
        "reports/thesis_scan/latest.md"
    ),
    html_out: Annotated[Path, typer.Option("--html-out")] = Path("reports/thesis_scan/latest.html"),
    policy: Annotated[Path, typer.Option("--policy")] = Path("configs/thesis_scanner/default.yaml"),
) -> None:
    """Enumerate and rank bounded bullish option theses; never transmit an order."""
    if direction != "bullish":
        raise typer.BadParameter("V10 thesis-scan currently supports --direction bullish only")
    try:
        parsed_catalyst_date = date.fromisoformat(catalyst_date)
    except ValueError as error:
        raise typer.BadParameter("--catalyst-date must use YYYY-MM-DD") from error
    try:
        request = ThesisScanRequest(
            ticker=ticker.upper(),
            direction="bullish",
            budget_eur=budget_eur,
            max_loss_eur=max_loss_eur,
            catalyst_date=parsed_catalyst_date,
            expiration_buffer_days=expiration_buffer_days,
            target_prices=_csv_floats(
                target_prices,
                option_name="--target-prices",
            ),
            scenario_probabilities=(
                _csv_floats(
                    scenario_probabilities,
                    option_name="--scenario-probabilities",
                )
                if scenario_probabilities is not None
                else None
            ),
            top=top,
            current_chain=str(current_chain),
            spot_override=spot,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    try:
        report = run_thesis_scan(
            request=request,
            json_out=json_out,
            markdown_out=markdown_out,
            html_out=html_out,
            policy_path=policy,
        )
    except (OSError, RuntimeError, ValueError) as error:
        typer.echo(f"Thesis scan failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(
        f"{report.overall_status.value}: candidates="
        f"{report.technically_admissible_candidates} "
        f"json={json_out} markdown={markdown_out} dashboard={html_out}; "
        "transmit=false"
    )


@knowledge_app.command("validate")
def knowledge_validate(
    knowledge_dir: Annotated[
        Path,
        typer.Option("--knowledge-dir", exists=True, file_okay=False, readable=True),
    ] = Path("research/knowledge_items"),
) -> None:
    """Validate strict knowledge, recipe, provenance, and modern-validation objects."""
    try:
        result = validate_knowledge(load_knowledge(knowledge_dir))
    except KnowledgeLoadError as error:
        typer.echo(f"Knowledge validation failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(result.model_dump_json(indent=2))
    if not result.valid:
        raise typer.Exit(code=1)


@knowledge_app.command("compile")
def knowledge_compile(
    knowledge_dir: Annotated[
        Path,
        typer.Option("--knowledge-dir", exists=True, file_okay=False, readable=True),
    ] = Path("research/knowledge_items"),
    catalog_out: Annotated[Path, typer.Option("--catalog-out")] = Path(
        "research/strategy_catalog/catalog.json"
    ),
) -> None:
    """Compile validated rules and recipes into a deterministic catalog."""
    try:
        catalog = compile_knowledge(load_knowledge(knowledge_dir))
    except (KnowledgeLoadError, ValueError) as error:
        typer.echo(f"Knowledge compilation failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    catalog_out.parent.mkdir(parents=True, exist_ok=True)
    catalog_out.write_text(catalog.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(
        f"catalog={catalog_out} recipes={len(catalog.recipes)} "
        f"rules={len(catalog.rules)} blocked={len(catalog.blocked_items)}"
    )


@data_app.command("refresh")
def data_refresh(
    ticker: Annotated[str, typer.Option("--ticker")] = "TTWO",
    as_of: Annotated[str | None, typer.Option("--as-of")] = None,
    strike_limit: Annotated[int, typer.Option("--strike-limit", min=1, max=100)] = 40,
    print_json: Annotated[bool, typer.Option("--print-json")] = False,
) -> None:
    """Refresh one read-only MarketData.app EOD chain and persist a normalized cache."""
    selected_date = date.fromisoformat(as_of) if as_of else date.today()
    try:
        snapshot = refresh_market_snapshot(
            ticker=ticker.upper(),
            as_of=selected_date,
            strike_limit=strike_limit,
        )
    except MarketSnapshotError as error:
        typer.echo(f"Data refresh failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    if print_json:
        typer.echo(snapshot.model_dump_json(indent=2))
    else:
        typer.echo(snapshot_manifest(snapshot))


@trade_app.command("analyze")
def trade_analyze(
    request: Annotated[
        Path,
        typer.Option("--request", exists=True, dir_okay=False, readable=True),
    ],
    refresh_data: Annotated[bool, typer.Option("--refresh-data")] = False,
    report_dir: Annotated[Path, typer.Option("--report-dir")] = Path("reports/latest"),
    knowledge_dir: Annotated[Path, typer.Option("--knowledge-dir")] = Path(
        "research/knowledge_items"
    ),
    research_config: Annotated[Path, typer.Option("--research-config")] = Path(
        "configs/research/default.yaml"
    ),
) -> None:
    """Run the complete read-only decision pipeline."""
    report = analyze_trade(
        request_path=request,
        report_dir=report_dir,
        knowledge_dir=knowledge_dir,
        research_config_path=research_config,
        refresh_data=refresh_data,
    )
    typer.echo(
        f"{report.verdict.value}: candidates={len(report.candidates)} "
        f"trials={report.analysis.total_trials} report={report_dir / 'decision_report.json'}"
    )


@trade_app.command("compare")
def trade_compare(
    report: Annotated[
        Path,
        typer.Option("--report", exists=True, dir_okay=False, readable=True),
    ],
) -> None:
    """Print a compact comparison of report candidates."""
    decision = DecisionReport.model_validate_json(report.read_text(encoding="utf-8"))
    typer.echo("candidate\tarchitecture\tmax_loss\texpected\tpareto\tstatus")
    for candidate in decision.candidates:
        typer.echo(
            f"{candidate.candidate_id}\t{candidate.architecture.value}\t"
            f"{candidate.risk.maximum_loss:.2f}\t"
            f"{candidate.evaluation.conservative_expected_pnl}\t"
            f"{candidate.pareto_rank}\t{candidate.status}"
        )


@trade_app.command("ibkr-ticket")
def trade_ibkr_ticket(
    report: Annotated[
        Path,
        typer.Option("--report", exists=True, dir_okay=False, readable=True),
    ],
    candidate_id: Annotated[str, typer.Option("--candidate-id")],
    mode: Annotated[str, typer.Option("--mode")] = "preview",
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/latest/ibkr_ticket_preview.json"
    ),
) -> None:
    """Create a non-transmitting IBKR preview for an admissible candidate only."""
    if mode != "preview":
        raise typer.BadParameter("only preview mode is supported")
    decision = DecisionReport.model_validate_json(report.read_text(encoding="utf-8"))
    try:
        write_ibkr_preview(decision, candidate_id, output)
    except TicketBlockedError as error:
        typer.echo(f"Ticket blocked: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"IBKR preview={output}; transmit=false; order capability forbidden")


@position_app.command("monitor")
def position_monitor(
    position: Annotated[
        Path,
        typer.Option("--position", exists=True, dir_okay=False, readable=True),
    ],
    refresh_data: Annotated[bool, typer.Option("--refresh-data")] = False,
    report_dir: Annotated[Path, typer.Option("--report-dir")] = Path(
        "reports/latest/position"
    ),
) -> None:
    """Record a read-only position snapshot; position mutation is unsupported."""
    payload = json.loads(position.read_text(encoding="utf-8"))
    report_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "status": "MONITORING_REQUIRES_FRESH_QUOTES"
        if refresh_data
        else "CACHED_POSITION_REVIEW",
        "position": payload,
        "actions_allowed": ["review", "preview"],
        "actions_forbidden": ["submit", "modify", "cancel", "exercise"],
        "order_capability": "forbidden",
    }
    output_path = report_dir / "position_monitor.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    typer.echo(f"position monitor={output_path}; order capability forbidden")


if __name__ == "__main__":
    app()
