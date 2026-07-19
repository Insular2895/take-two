"""Read-only data providers and execution boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from take_two_options.domain import (
    CorporateAction,
    FundamentalSnapshot,
    MarketDataBundle,
    MarketEvent,
    OptionContract,
    OptionQuote,
    PortfolioState,
    UnderlyingSnapshot,
)
from take_two_options.exceptions import ForbiddenOperation


class MarketDataProvider(Protocol):
    def load_bundle(self) -> MarketDataBundle: ...


class UnderlyingDataSource(Protocol):
    def get_underlying(self, ticker: str) -> UnderlyingSnapshot: ...


class OptionChainDataSource(Protocol):
    def get_option_chain(self, underlying: UnderlyingSnapshot) -> list[OptionQuote]: ...


class ContractDetailsDataSource(Protocol):
    def get_contract_details(self, con_id: int) -> OptionContract: ...


class CorporateActionsDataSource(Protocol):
    def get_corporate_actions(self, ticker: str) -> list[CorporateAction]: ...


class EventsDataSource(Protocol):
    def get_events(self, ticker: str) -> list[MarketEvent]: ...


class YieldCurveDataSource(Protocol):
    def get_risk_free_rate(self, currency: str, maturity_days: int) -> float: ...


class FundamentalsDataSource(Protocol):
    def get_fundamentals(self, ticker: str) -> FundamentalSnapshot: ...


class PortfolioDataSource(Protocol):
    def get_portfolio_state(self) -> PortfolioState: ...


class CostMarginDataSource(Protocol):
    def enrich_costs_and_margin(self, portfolio: PortfolioState) -> PortfolioState: ...


class FixtureDataProvider:
    """Load a fully explicit, offline research fixture."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_bundle(self) -> MarketDataBundle:
        return MarketDataBundle.model_validate_json(self.path.read_text(encoding="utf-8"))


class ReadOnlyBrokerGateway:
    """Deliberately exposes no order implementation in V1."""

    def submit_order(self, _order: Any) -> None:
        raise ForbiddenOperation("Order submission is disabled: this engine is read-only research")

    def modify_order(self, _order_id: str, _changes: Any) -> None:
        raise ForbiddenOperation(
            "Order modification is disabled: this engine is read-only research"
        )

    def cancel_order(self, _order_id: str) -> None:
        raise ForbiddenOperation(
            "Order cancellation is unavailable because orders cannot be created"
        )
