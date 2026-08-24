"""Read-only CLI for knowledge validation and generic option-trade analysis."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from take_two_options.budget import (
    CapitalCap,
    CapitalCapMode,
    FlexibleBudgetPolicyV2,
    MinimumSpendPolicy,
)
from take_two_options.decision.pipeline import analyze_trade
from take_two_options.intelligence.backtesting import (
    load_walk_forward_dataset,
    run_walk_forward,
)
from take_two_options.intelligence.calibration import (
    build_dataset_splits,
    fit_offline_models,
    validate_historical_dataset,
)
from take_two_options.intelligence.monitoring import (
    monitor_position as assess_position,
)
from take_two_options.intelligence.monitoring import (
    replay_position_trajectory,
)
from take_two_options.intelligence.pipeline import run_intelligence
from take_two_options.intelligence.schemas import (
    PositionDossier,
    PositionMonitorInput,
    PositionTrajectoryFixture,
)
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
from take_two_options.opra.contracts import assess_provider_readiness
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
calibration_app = typer.Typer(
    no_args_is_help=True,
    help="Offline historical calibration and walk-forward validation; never uses live fallback.",
)
app.add_typer(knowledge_app, name="knowledge")
app.add_typer(data_app, name="data")
app.add_typer(trade_app, name="trade")
app.add_typer(position_app, name="position")
app.add_typer(calibration_app, name="calibration")
app.add_typer(legacy_app, name="legacy", hidden=True)


@app.command("pre-opra-finalize")
def pre_opra_finalize(
    config: Annotated[
        Path,
        typer.Option("--config", exists=True, dir_okay=False, readable=True),
    ] = Path("configs/pre_opra/v1/ttwo_research.yaml"),
) -> None:
    """Rebuild final aggregate evidence and inspect OPRA config without connecting."""

    repository = Path(__file__).resolve().parents[2]
    readiness = assess_provider_readiness(os.environ)
    try:
        subprocess.run(
            [
                sys.executable,
                str(repository / "scripts" / "build_opra_readiness.py"),
                "--output",
                str(repository / "reports/pre_opra/opra_interface_readiness_2026-08-08.json"),
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(repository / "scripts" / "build_pre_opra_final_report.py"),
                "--config",
                str(config.resolve()),
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        typer.echo("Pre-OPRA finalization failed without attempting a market connection.", err=True)
        if error.stderr:
            typer.echo(error.stderr.strip(), err=True)
        raise typer.Exit(code=1) from error
    typer.echo(
        "PRE_OPRA_RESEARCH_COMPLETE: "
        "report=reports/pre_opra/final_pre_opra_report_2026-08-08.html; "
        f"opra={readiness.status}; connection_attempted=false; phase_m_started=false; "
        "transmit=false; what_if=true; order capability forbidden"
    )


def _csv_floats(value: str, *, option_name: str) -> list[float]:
    try:
        values = [float(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise typer.BadParameter(f"{option_name} must be a comma-separated numeric list") from error
    if not values:
        raise typer.BadParameter(f"{option_name} cannot be empty")
    return values


def _write_model_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _capital_cap_option(value: str, *, option_name: str) -> CapitalCap:
    if value.strip().lower() == "auto":
        return CapitalCap()
    try:
        amount = float(value)
    except ValueError as error:
        raise typer.BadParameter(f"{option_name} must be auto or a positive amount") from error
    if amount <= 0:
        raise typer.BadParameter(f"{option_name} must be auto or a positive amount")
    return CapitalCap(mode=CapitalCapMode.EXPLICIT, value=amount)


def _budget_policy_from_cli(
    *,
    budget: float,
    budget_currency: str,
    allow_under: float,
    allow_over: float,
    minimum_spend_policy: str,
    max_loss: str,
    buying_power_cap: str,
    maximum_contracts: int,
    account_capital: float | None,
    liquidity_reserve: float,
) -> FlexibleBudgetPolicyV2:
    return FlexibleBudgetPolicyV2(
        currency=budget_currency,
        target_budget=budget,
        under_target_tolerance=allow_under,
        max_overspend=allow_over,
        minimum_spend_policy=MinimumSpendPolicy(minimum_spend_policy.upper()),
        maximum_loss_cap=_capital_cap_option(max_loss, option_name="--max-loss"),
        buying_power_cap=_capital_cap_option(
            buying_power_cap,
            option_name="--buying-power-cap",
        ),
        maximum_contracts=maximum_contracts,
        account_available_capital=account_capital,
        account_liquidity_reserve=liquidity_reserve,
    )


@trade_app.command("budget")
def trade_budget(
    budget: Annotated[float, typer.Option("--budget", min=0.01)] = 1_000,
    budget_currency: Annotated[str, typer.Option("--budget-currency")] = "EUR",
    allow_under: Annotated[float, typer.Option("--allow-under", min=0)] = 200,
    allow_over: Annotated[float, typer.Option("--allow-over", min=0)] = 500,
    minimum_spend_policy: Annotated[
        str,
        typer.Option("--minimum-spend-policy"),
    ] = "soft",
    max_loss: Annotated[str, typer.Option("--max-loss")] = "auto",
    buying_power_cap: Annotated[
        str,
        typer.Option("--buying-power-cap"),
    ] = "auto",
    maximum_contracts: Annotated[
        int,
        typer.Option("--maximum-contracts", min=1),
    ] = 4,
    account_capital: Annotated[
        float | None,
        typer.Option("--account-capital", min=0),
    ] = None,
    liquidity_reserve: Annotated[
        float,
        typer.Option("--liquidity-reserve", min=0),
    ] = 0,
    json_out: Annotated[Path | None, typer.Option("--json-out")] = None,
) -> None:
    """Build and display a prospective V2 budget policy; no market connection."""
    try:
        policy = _budget_policy_from_cli(
            budget=budget,
            budget_currency=budget_currency,
            allow_under=allow_under,
            allow_over=allow_over,
            minimum_spend_policy=minimum_spend_policy,
            max_loss=max_loss,
            buying_power_cap=buying_power_cap,
            maximum_contracts=maximum_contracts,
            account_capital=account_capital,
            liquidity_reserve=liquidity_reserve,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    payload = policy.model_dump_json(indent=2)
    if json_out is not None:
        _write_model_json(json_out, payload)
    typer.echo(payload)
    typer.echo("read_only=true; transmit=false; order_capability=forbidden")


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


@app.command("intelligence-run")
def intelligence_run(
    base_report: Annotated[
        Path,
        typer.Option(
            "--base-report",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = Path("reports/examples/v10_thesis_scan.json"),
    policy: Annotated[
        Path,
        typer.Option("--policy", exists=True, dir_okay=False, readable=True),
    ] = Path("configs/intelligence/v11.yaml"),
    events: Annotated[
        Path | None,
        typer.Option("--events", exists=True, dir_okay=False, readable=True),
    ] = None,
    factor_history: Annotated[
        Path | None,
        typer.Option("--factor-history", exists=True, dir_okay=False, readable=True),
    ] = None,
    calibration_data: Annotated[
        Path | None,
        typer.Option("--calibration-data", exists=True, dir_okay=False, readable=True),
    ] = None,
    walk_forward: Annotated[
        Path | None,
        typer.Option("--walk-forward", exists=True, dir_okay=False, readable=True),
    ] = None,
    profile: Annotated[
        str,
        typer.Option("--profile"),
    ] = "fast_fixture",
    json_out: Annotated[Path, typer.Option("--json-out")] = Path(
        "reports/v11/latest.json"
    ),
    markdown_out: Annotated[Path, typer.Option("--markdown-out")] = Path(
        "reports/v11/latest.md"
    ),
    html_out: Annotated[Path, typer.Option("--html-out")] = Path(
        "reports/v11/latest.html"
    ),
) -> None:
    """Run V11 probabilistic intelligence over a stable V10.1 structure report."""
    try:
        if profile not in {"fast_fixture", "research", "validation", "exhaustive"}:
            raise ValueError(
                "--profile must be fast_fixture, research, validation, or exhaustive"
            )
        report = run_intelligence(
            base_report_path=base_report,
            policy_path=policy,
            events_path=events,
            factor_history_path=factor_history,
            calibration_data_path=calibration_data,
            walk_forward_path=walk_forward,
            runtime_profile=profile,  # type: ignore[arg-type]
            json_out=json_out,
            markdown_out=markdown_out,
            html_out=html_out,
        )
    except (OSError, RuntimeError, ValueError) as error:
        typer.echo(f"V11 intelligence failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(
        f"{report.posture.value}: readiness={report.machine_summary.result_status.value} "
        f"calibration={report.machine_summary.calibration_status} "
        f"backtest={report.machine_summary.backtest_status} "
        f"models={len(report.model_metrics)} "
        f"allocations={len(report.allocations)} report={json_out}; "
        "transmit=false; order capability forbidden"
    )


@calibration_app.command("validate-dataset")
def calibration_validate_dataset(
    dataset: Annotated[
        Path | None,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = None,
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/calibration/dataset_quality.json"
    ),
) -> None:
    """Validate lineage, timezone, units, duplicates, and point-in-time availability."""
    _loaded, report = validate_historical_dataset(dataset)
    _write_model_json(output, report.model_dump_json(indent=2))
    typer.echo(f"{report.status}: report={output}; order capability forbidden")


@calibration_app.command("build-splits")
def calibration_build_splits(
    dataset: Annotated[
        Path | None,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = None,
    method: Annotated[str, typer.Option("--method")] = "expanding",
    embargo_days: Annotated[int, typer.Option("--embargo-days", min=0)] = 5,
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/calibration/splits.json"
    ),
) -> None:
    """Build a rolling or expanding split with embargo and a locked final holdout."""
    if method not in {"rolling", "expanding"}:
        raise typer.BadParameter("--method must be rolling or expanding")
    loaded, quality = validate_historical_dataset(dataset)
    report = build_dataset_splits(
        loaded,
        quality,
        method=method,  # type: ignore[arg-type]
        embargo_days=embargo_days,
    )
    _write_model_json(output, report.model_dump_json(indent=2))
    typer.echo(f"{report.status}: splits={len(report.splits)} report={output}")


@calibration_app.command("fit")
def calibration_fit(
    dataset: Annotated[
        Path | None,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = None,
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/calibration/fit.json"
    ),
) -> None:
    """Fit only identifiable offline parameters; refuse fake Heston calibration."""
    loaded, quality = validate_historical_dataset(dataset)
    report = fit_offline_models(loaded, quality)
    _write_model_json(output, report.model_dump_json(indent=2))
    typer.echo(f"{report.status}: report={output}; no fixture substitution")


@calibration_app.command("evaluate")
def calibration_evaluate(
    walk_forward: Annotated[
        Path | None,
        typer.Option("--walk-forward", exists=True, dir_okay=False, readable=True),
    ] = None,
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/calibration/walk_forward.json"
    ),
) -> None:
    """Evaluate a point-in-time walk-forward dataset with explicit baselines."""
    report = run_walk_forward(
        load_walk_forward_dataset(walk_forward)
        if walk_forward is not None
        else None
    )
    _write_model_json(output, report.model_dump_json(indent=2))
    typer.echo(f"{report.status}: report={output}; holdout tuning=false")


@calibration_app.command("report")
def calibration_report(
    dataset: Annotated[
        Path | None,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ] = None,
    walk_forward: Annotated[
        Path | None,
        typer.Option("--walk-forward", exists=True, dir_okay=False, readable=True),
    ] = None,
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/calibration/offline_validation.json"
    ),
) -> None:
    """Write one machine-readable offline validation summary."""
    loaded, quality = validate_historical_dataset(dataset)
    split_plan = build_dataset_splits(loaded, quality)
    calibration = fit_offline_models(loaded, quality)
    backtest = run_walk_forward(
        load_walk_forward_dataset(walk_forward)
        if walk_forward is not None
        else None
    )
    payload = {
        "schema_version": "11.1",
        "dataset_quality": quality.model_dump(mode="json"),
        "split_plan": split_plan.model_dump(mode="json"),
        "calibration": calibration.model_dump(mode="json"),
        "walk_forward": backtest.model_dump(mode="json"),
        "promotion_eligible": False,
        "order_capability": "forbidden",
    }
    _write_model_json(output, json.dumps(payload, indent=2))
    typer.echo(
        f"calibration={calibration.status}; backtest={backtest.status}; "
        f"report={output}; promotion=false"
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
    budget: Annotated[float | None, typer.Option("--budget", min=0.01)] = None,
    budget_currency: Annotated[str, typer.Option("--budget-currency")] = "EUR",
    allow_under: Annotated[float, typer.Option("--allow-under", min=0)] = 200,
    allow_over: Annotated[float, typer.Option("--allow-over", min=0)] = 500,
    minimum_spend_policy: Annotated[
        str,
        typer.Option("--minimum-spend-policy"),
    ] = "soft",
    max_loss: Annotated[str, typer.Option("--max-loss")] = "auto",
    buying_power_cap: Annotated[
        str,
        typer.Option("--buying-power-cap"),
    ] = "auto",
    maximum_contracts: Annotated[
        int,
        typer.Option("--maximum-contracts", min=1),
    ] = 4,
    account_capital: Annotated[
        float | None,
        typer.Option("--account-capital", min=0),
    ] = None,
    liquidity_reserve: Annotated[
        float,
        typer.Option("--liquidity-reserve", min=0),
    ] = 0,
) -> None:
    """Run the complete read-only decision pipeline."""
    budget_policy = None
    if budget is not None:
        try:
            budget_policy = _budget_policy_from_cli(
                budget=budget,
                budget_currency=budget_currency,
                allow_under=allow_under,
                allow_over=allow_over,
                minimum_spend_policy=minimum_spend_policy,
                max_loss=max_loss,
                buying_power_cap=buying_power_cap,
                maximum_contracts=maximum_contracts,
                account_capital=account_capital,
                liquidity_reserve=liquidity_reserve,
            )
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
    report = analyze_trade(
        request_path=request,
        report_dir=report_dir,
        knowledge_dir=knowledge_dir,
        research_config_path=research_config,
        refresh_data=refresh_data,
        budget_policy=budget_policy,
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


@position_app.command("assess")
def position_assess(
    dossier: Annotated[
        Path,
        typer.Option("--dossier", exists=True, dir_okay=False, readable=True),
    ],
    current: Annotated[
        Path,
        typer.Option("--current", exists=True, dir_okay=False, readable=True),
    ],
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/position_monitor.json"
    ),
) -> None:
    """Evaluate an open-position dossier and emit an explainable advisory action."""
    try:
        stored = PositionDossier.model_validate_json(dossier.read_text(encoding="utf-8"))
        snapshot = PositionMonitorInput.model_validate_json(
            current.read_text(encoding="utf-8")
        )
        report = assess_position(stored, snapshot)
    except (OSError, ValueError) as error:
        typer.echo(f"Position assessment failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(
        f"position action={report.action.value} report={output}; "
        "human confirmation required; order capability forbidden"
    )


@position_app.command("replay")
def position_replay(
    trajectory: Annotated[
        Path,
        typer.Option("--trajectory", exists=True, dir_okay=False, readable=True),
    ],
    output: Annotated[Path, typer.Option("--output")] = Path(
        "reports/v11/position_trajectory.json"
    ),
) -> None:
    """Replay a synthetic multi-date trajectory through advisory exit rules."""
    try:
        fixture = PositionTrajectoryFixture.model_validate_json(
            trajectory.read_text(encoding="utf-8")
        )
        report = replay_position_trajectory(fixture)
    except (OSError, ValueError) as error:
        typer.echo(f"Position trajectory replay failed: {error}", err=True)
        raise typer.Exit(code=1) from error
    _write_model_json(output, report.model_dump_json(indent=2))
    typer.echo(
        f"{report.status}: snapshots={len(report.reports)} report={output}; "
        "human confirmation required; order capability forbidden"
    )


if __name__ == "__main__":
    app()
