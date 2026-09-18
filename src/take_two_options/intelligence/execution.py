"""Preview-only IBKR artifacts and an explicit forbidden execution boundary."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from take_two_options.data import ReadOnlyBrokerGateway
from take_two_options.intelligence.schemas import ComboQuote, ExecutionPreview
from take_two_options.opra.contracts import BrokerWhatIfEvidence
from take_two_options.thesis_scanner.schemas import ThesisCandidate

FORBIDDEN_ORDER_IMPORTS = (
    "alpaca.trading.client",
    "alpaca.trading.requests",
    "ibapi.order",
    "ibapi.order_state",
    "ib_insync.order",
)
FORBIDDEN_ORDER_PRIMITIVES = {
    "place_order",
    "placeOrder",
    "submit_order",
    "modify_order",
    "cancel_order",
    "cancelOrder",
    "reqGlobalCancel",
    "exercise",
    "exerciseOptions",
}


def build_execution_previews(
    candidates: list[ThesisCandidate],
    *,
    combo_quotes: dict[str, ComboQuote] | None = None,
    what_if_evidence: dict[str, BrokerWhatIfEvidence] | None = None,
) -> list[ExecutionPreview]:
    """Build non-transmitting tickets; missing broker facts remain blockers."""
    combo_quotes = combo_quotes or {}
    what_if_evidence = what_if_evidence or {}
    previews: list[ExecutionPreview] = []
    for candidate in candidates:
        combo = combo_quotes.get(candidate.candidate_id)
        what_if = what_if_evidence.get(candidate.candidate_id)
        blockers: list[str] = []
        if combo is None:
            blockers.append("Live IBKR combo quote is unavailable.")
        elif not combo.executable or combo.ask is None:
            blockers.append("IBKR combo quote is not marked executable.")
        if any(
            metric.price_quality != "opra" for metric in candidate.decision_metrics.leg_execution
        ):
            blockers.append("At least one leg is not backed by a live OPRA quote.")
        usable_what_if = (
            what_if is not None
            and what_if.candidate_id == candidate.candidate_id
            and what_if.complete
            and what_if.currency == "USD"
        )
        if what_if is None:
            blockers.append(
                "Account-specific commission/margin what-if is unavailable; "
                "some smart combos may not support what-if."
            )
        elif what_if.candidate_id != candidate.candidate_id:
            blockers.append("Broker what-if evidence references a different candidate.")
        elif not what_if.complete:
            blockers.append("Broker what-if evidence is incomplete and was not consumed.")
        elif what_if.currency != "USD":
            blockers.append("Broker what-if evidence is not denominated in USD.")
        commission = what_if.estimated_commission if usable_what_if and what_if else None
        initial_margin = what_if.initial_margin_change if usable_what_if and what_if else None
        maintenance_margin = (
            what_if.maintenance_margin_change if usable_what_if and what_if else None
        )
        what_if_source_id = what_if.source_id if usable_what_if and what_if else None
        blockers.append("Contract conIds and deliverables require broker-side resolution.")
        blockers.append("Human confirmation is mandatory; automatic transmission is forbidden.")
        limit = (
            min(candidate.execution.indicative_limit_price_per_share, combo.ask)
            if combo is not None and combo.ask is not None
            else candidate.execution.indicative_limit_price_per_share
        )
        previews.append(
            ExecutionPreview(
                candidate_id=candidate.candidate_id,
                security_type="BAG" if len(candidate.base_candidate.legs) > 1 else "OPT",
                limit_debit_usd=max(limit, 0.0),
                combo_quote=combo,
                estimated_commission_usd=commission,
                margin_what_if_usd=initial_margin,
                maintenance_margin_change_usd=maintenance_margin,
                what_if_source_id=what_if_source_id,
                what_if_complete=usable_what_if,
                blockers=blockers,
            )
        )
    return previews


def execution_gateway() -> ReadOnlyBrokerGateway:
    """Return the repository-wide gateway that rejects every order-side mutation."""
    return ReadOnlyBrokerGateway()


def assert_no_order_capability(obj: Any) -> None:
    """Static/runtime defense against accidentally injecting an order-capable adapter."""
    forbidden = (
        "place_order",
        "placeOrder",
        "submit_order",
        "modify_order",
        "cancel_order",
        "cancelOrder",
        "exercise",
        "exerciseOptions",
    )
    exposed = [
        name
        for name in forbidden
        if callable(getattr(obj, name, None)) and not isinstance(obj, ReadOnlyBrokerGateway)
    ]
    if exposed:
        raise TypeError(f"order-capable object rejected by V11: {', '.join(exposed)}")


def assert_all_execution_paths_forbidden(
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Statically prove that research modules expose no usable order path."""
    root = package_root or Path(__file__).resolve().parents[1]
    paths = sorted(root.rglob("*.py"))
    violations, scanned = _scan_order_boundary(paths, allow_readonly_gateway_stubs=True)
    if violations:
        raise AssertionError("execution boundary violation(s): " + " | ".join(violations))
    gateway = execution_gateway()
    for method_name in ("submit_order", "modify_order", "cancel_order"):
        if not callable(getattr(gateway, method_name, None)):
            raise AssertionError(f"read-only gateway lacks forbidden stub {method_name}")
    return {
        "status": "all_execution_paths_forbidden",
        "python_files_scanned": scanned,
        "forbidden_order_imports": 0,
        "transmit_true_literals": 0,
        "order_capability": "forbidden",
    }


def _scan_order_boundary(
    paths: list[Path],
    *,
    allow_readonly_gateway_stubs: bool,
) -> tuple[list[str], int]:
    violations: list[str] = []
    scanned = 0
    for path in paths:
        scanned += 1
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            violations.append(f"{path}: cannot parse: {error}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                if any(
                    name == forbidden or name.startswith(f"{forbidden}.")
                    for name in names
                    for forbidden in FORBIDDEN_ORDER_IMPORTS
                ):
                    violations.append(f"{path}: forbidden broker-order import {names}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name not in FORBIDDEN_ORDER_PRIMITIVES:
                    continue
                if allow_readonly_gateway_stubs and path.name == "data.py":
                    body_text = ast.get_source_segment(source, node) or ""
                    if "raise ForbiddenOperation" in body_text:
                        continue
                violations.append(f"{path}: order-capable definition {node.name}")
            if isinstance(node, ast.Call):
                called_name: str | None = None
                if isinstance(node.func, ast.Name):
                    called_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    called_name = node.func.attr
                if called_name in FORBIDDEN_ORDER_PRIMITIVES:
                    violations.append(f"{path}: forbidden broker-order call {called_name}")
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                if node.value.value is True and any(
                    isinstance(target, ast.Name) and target.id == "transmit"
                    for target in node.targets
                ):
                    violations.append(f"{path}: transmit=True assignment")
            if isinstance(node, ast.keyword):
                if (
                    node.arg == "transmit"
                    and isinstance(node.value, ast.Constant)
                    and node.value.value is True
                ):
                    violations.append(f"{path}: transmit=True keyword")
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values, strict=True):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "transmit"
                        and isinstance(value, ast.Constant)
                        and value.value is True
                    ):
                        violations.append(f"{path}: transmit true mapping")
    return violations, scanned


def assert_read_only_modules_forbid_orders(paths: list[Path]) -> dict[str, int | str]:
    """Enforce a strict no-mutation boundary on provider or telemetry modules."""

    violations, scanned = _scan_order_boundary(
        sorted(paths),
        allow_readonly_gateway_stubs=False,
    )
    if violations:
        raise AssertionError("read-only boundary violation(s): " + " | ".join(violations))
    return {"status": "forbidden", "python_files_scanned": scanned}


def assert_disabled_gateway_runtime(main_path: Path) -> dict[str, str]:
    """Prove the bridge runtime is wired to DisabledGateway and no other adapter."""

    source = main_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(main_path))
    runtime_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "BridgeRuntime"
    ]
    safe_calls = [
        node
        for node in runtime_calls
        if len(node.args) >= 3
        and isinstance(node.args[2], ast.Call)
        and isinstance(node.args[2].func, ast.Name)
        and node.args[2].func.id == "DisabledGateway"
    ]
    if len(runtime_calls) != 1 or len(safe_calls) != 1:
        raise AssertionError(
            f"{main_path}: BridgeRuntime must instantiate exactly one DisabledGateway"
        )
    return {"status": "disabled", "runtime_gateway": "DisabledGateway"}


def assert_execution_security_boundaries(
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Report separate research, read-only, paper and live execution domains."""

    repo = repository_root or Path(__file__).resolve().parents[3]
    research = assert_all_execution_paths_forbidden(repo / "src/take_two_options")
    market_paths = [
        repo / "src/take_two_options/opra/ibkr_official.py",
        repo / "src/take_two_options/opra/ibkr_provider.py",
    ]
    telemetry_root = repo / "services/ibkr-paper-bridge/src/ttwo_ibkr_bridge"
    telemetry_paths = [
        path
        for path in telemetry_root.glob("*.py")
        if path.name == "ibkr_readonly.py"
        or path.name == "readonly_cli.py"
        or path.name.startswith("telemetry")
    ]
    market = assert_read_only_modules_forbid_orders(market_paths)
    telemetry = assert_read_only_modules_forbid_orders(telemetry_paths)
    paper = assert_disabled_gateway_runtime(telemetry_root / "main.py")
    return {
        "status": "execution_security_boundaries_enforced",
        "research_engine_order_capability": "forbidden",
        "read_only_market_provider_order_capability": "forbidden",
        "read_only_telemetry_order_capability": "forbidden",
        "paper_execution_adapter": "disabled",
        "live_execution_capability": "forbidden",
        "details": {
            "research": research,
            "market_provider": market,
            "telemetry": telemetry,
            "paper_runtime": paper,
        },
    }
