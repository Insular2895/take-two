from __future__ import annotations

from pathlib import Path

import pytest

from take_two_options.intelligence.execution import (
    assert_all_execution_paths_forbidden,
    assert_disabled_gateway_runtime,
    assert_execution_security_boundaries,
    assert_read_only_modules_forbid_orders,
)


def _python(tmp_path: Path, name: str, source: str) -> Path:
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    return path


def test_research_engine_rejects_order_calls_imports_and_transmit_true(
    tmp_path: Path,
) -> None:
    _python(tmp_path, "place.py", "def run(client):\n    client.placeOrder(1, None, None)\n")
    with pytest.raises(AssertionError, match="placeOrder"):
        assert_all_execution_paths_forbidden(tmp_path)

    (tmp_path / "place.py").unlink()
    _python(tmp_path, "order_import.py", "from ibapi.order import Order\n")
    with pytest.raises(AssertionError, match="broker-order import"):
        assert_all_execution_paths_forbidden(tmp_path)

    (tmp_path / "order_import.py").unlink()
    _python(tmp_path, "transmit.py", "payload = {'transmit': True}\n")
    with pytest.raises(AssertionError, match="transmit true"):
        assert_all_execution_paths_forbidden(tmp_path)


def test_read_only_provider_and_telemetry_reject_order_api_imports(tmp_path: Path) -> None:
    provider = _python(tmp_path, "provider.py", "from ibapi.order import Order\n")
    with pytest.raises(AssertionError, match="read-only boundary"):
        assert_read_only_modules_forbid_orders([provider])

    telemetry = _python(tmp_path, "telemetry.py", "import ibapi.order\n")
    with pytest.raises(AssertionError, match="read-only boundary"):
        assert_read_only_modules_forbid_orders([telemetry])


def test_runtime_must_keep_disabled_gateway(tmp_path: Path) -> None:
    safe = _python(
        tmp_path,
        "safe_main.py",
        "runtime = BridgeRuntime(client, journal, DisabledGateway())\n",
    )
    assert assert_disabled_gateway_runtime(safe)["status"] == "disabled"

    unsafe = _python(
        tmp_path,
        "unsafe_main.py",
        "runtime = BridgeRuntime(client, journal, EnabledPaperGateway())\n",
    )
    with pytest.raises(AssertionError, match="DisabledGateway"):
        assert_disabled_gateway_runtime(unsafe)


def test_current_security_boundaries_are_reported_separately() -> None:
    root = Path(__file__).resolve().parents[1]
    result = assert_execution_security_boundaries(root)
    assert result["research_engine_order_capability"] == "forbidden"
    assert result["read_only_market_provider_order_capability"] == "forbidden"
    assert result["read_only_telemetry_order_capability"] == "forbidden"
    assert result["paper_execution_adapter"] == "disabled"
    assert result["live_execution_capability"] == "forbidden"
