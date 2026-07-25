"""Trade-request loading."""

from __future__ import annotations

from pathlib import Path

import yaml

from take_two_options.knowledge.schemas import TradeRequest


def load_trade_request(path: Path) -> TradeRequest:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return TradeRequest.model_validate(payload)
