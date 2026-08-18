"""Preview-only IBKR artifacts and an explicit forbidden execution boundary."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from take_two_options.data import ReadOnlyBrokerGateway
from take_two_options.intelligence.schemas import ComboQuote, ExecutionPreview
from take_two_options.thesis_scanner.schemas import ThesisCandidate


def build_execution_previews(
    candidates: list[ThesisCandidate],
    *,
    combo_quotes: dict[str, ComboQuote] | None = None,
    what_if_results: dict[str, dict[str, float]] | None = None,
) -> list[ExecutionPreview]:
    """Build non-transmitting tickets; missing broker facts remain blockers."""
    combo_quotes = combo_quotes or {}
    what_if_results = what_if_results or {}
    previews: list[ExecutionPreview] = []
    for candidate in candidates:
        combo = combo_quotes.get(candidate.candidate_id)
        what_if = what_if_results.get(candidate.candidate_id, {})
        blockers: list[str] = []
        if combo is None:
            blockers.append("Live IBKR combo quote is unavailable.")
        elif not combo.executable or combo.ask is None:
            blockers.append("IBKR combo quote is not marked executable.")
        if any(
            metric.price_quality != "opra"
            for metric in candidate.decision_metrics.leg_execution
        ):
            blockers.append("At least one leg is not backed by a live OPRA quote.")
        if not what_if:
            blockers.append(
                "Account-specific commission/margin what-if is unavailable; "
                "some smart combos may not support what-if."
            )
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
                estimated_commission_usd=what_if.get("commission_usd"),
                margin_what_if_usd=what_if.get("margin_usd"),
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
        if callable(getattr(obj, name, None))
        and not isinstance(obj, ReadOnlyBrokerGateway)
    ]
    if exposed:
        raise TypeError(f"order-capable object rejected by V11: {', '.join(exposed)}")


def assert_all_execution_paths_forbidden(
    package_root: Path | None = None,
) -> dict[str, Any]:
    """Statically prove that research modules expose no usable order path."""
    root = package_root or Path(__file__).resolve().parents[1]
    forbidden_imports = (
        "alpaca.trading.client",
        "alpaca.trading.requests",
        "ibapi.order",
        "ibapi.order_state",
        "ib_insync.order",
    )
    forbidden_definitions = {
        "place_order",
        "placeOrder",
        "submit_order",
        "modify_order",
        "cancel_order",
        "cancelOrder",
        "exercise",
        "exerciseOptions",
    }
    violations: list[str] = []
    scanned = 0
    for path in sorted(root.rglob("*.py")):
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
                    for forbidden in forbidden_imports
                ):
                    violations.append(f"{path}: forbidden broker-order import {names}")
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name not in forbidden_definitions:
                    continue
                if path.name == "data.py":
                    body_text = ast.get_source_segment(source, node) or ""
                    if "raise ForbiddenOperation" in body_text:
                        continue
                violations.append(f"{path}: order-capable definition {node.name}")
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
