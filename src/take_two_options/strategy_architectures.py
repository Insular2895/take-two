"""Documented option architecture catalog and activation boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from take_two_options.domain import StrategyKind


class ArchitectureReadiness(StrEnum):
    BACKTESTED = "backtested"
    CATALOG_ONLY = "catalog_only"
    RISK_DISABLED = "risk_disabled"


@dataclass(frozen=True)
class StrategyArchitecture:
    kind: StrategyKind
    name: str
    family: str
    market_view: str
    volatility_view: str
    payoff: str
    maximum_risk: str
    readiness: ArchitectureReadiness
    default_entry: str
    default_exit: str
    required_data: str
    limitation: str
    source_reference: str


_BOOK_SOURCE = (
    "Natenberg ch. 8 / McMillan butterfly review; documentary rules remain to validate"
)


ARCHITECTURES: tuple[StrategyArchitecture, ...] = (
    StrategyArchitecture(
        StrategyKind.LONG_CALL,
        "Long call",
        "directional debit",
        "bullish",
        "long volatility",
        "convex upside",
        "premium paid plus costs",
        ArchitectureReadiness.BACKTESTED,
        "delta or moneyness target on the back expiry",
        "profit target, stop, or time exit",
        "historical bid/ask, IV/Greeks, rate, dividends",
        "American exercise and EOD execution remain modeled approximations",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LONG_PUT,
        "Long put",
        "directional debit",
        "bearish or hedge",
        "long volatility",
        "convex downside",
        "premium paid plus costs",
        ArchitectureReadiness.BACKTESTED,
        "delta or moneyness target on the back expiry",
        "profit target, stop, or time exit",
        "historical bid/ask, IV/Greeks, rate, dividends",
        "A standalone put is not a portfolio hedge without position context",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.BULL_CALL_SPREAD,
        "Bull call spread",
        "vertical debit",
        "moderately bullish",
        "limited vega exposure",
        "capped upside",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy higher-delta call and sell higher-strike call",
        "profit target, stop, or time exit",
        "same-expiry executable bid/ask for both legs",
        "Synthetic simultaneous marks are not broker combo fills",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.BEAR_PUT_SPREAD,
        "Bear put spread",
        "vertical debit",
        "moderately bearish",
        "limited vega exposure",
        "capped downside gain",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy higher-strike put and sell lower-strike put",
        "profit target, stop, or time exit",
        "same-expiry executable bid/ask for both legs",
        "Synthetic simultaneous marks are not broker combo fills",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LONG_STRADDLE,
        "Long straddle",
        "long volatility debit",
        "large move either way",
        "long gamma and vega",
        "two-sided convexity",
        "two premiums plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy ATM call and put at the same strike and expiry",
        "profit target, stop, or time exit",
        "call/put chains, IV level, event and realized-volatility context",
        "Negative theta can dominate when the realized move is too small",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LONG_STRANGLE,
        "Long strangle",
        "long volatility debit",
        "larger move either way",
        "long gamma and vega",
        "wider two-sided convexity",
        "two premiums plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy OTM put and OTM call at one expiry",
        "profit target, stop, or time exit",
        "call/put chains, IV level, event and realized-volatility context",
        "Cheaper than a straddle but needs a larger underlying move",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.CALL_BUTTERFLY,
        "Call butterfly",
        "defined-risk range",
        "target near center strike",
        "short volatility near center",
        "peaked 1/-2/1 payoff",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy lower call, sell two center calls, buy upper call",
        "profit target, stop, or exit before pin-risk window",
        "three strikes, one expiry, four-leg execution costs",
        "Pin, assignment, and legging risk are not replayed",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.PUT_BUTTERFLY,
        "Put butterfly",
        "defined-risk range",
        "target near center strike",
        "short volatility near center",
        "peaked 1/-2/1 payoff",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy lower put, sell two center puts, buy upper put",
        "profit target, stop, or exit before pin-risk window",
        "three strikes, one expiry, four-leg execution costs",
        "Pin, assignment, and legging risk are not replayed",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.IRON_CONDOR,
        "Iron condor",
        "defined-risk range credit",
        "range-bound",
        "short volatility",
        "flat center with bounded wings",
        "wing width less credit, plus costs",
        ArchitectureReadiness.BACKTESTED,
        "sell OTM put/call and buy farther OTM wings",
        "profit target, stop, or exit before expiration risk",
        "four executable legs, margin proxy, IV/skew and assignment context",
        "EOD marks do not capture intraday short-gamma or early assignment paths",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LONG_CALL_CALENDAR,
        "Long call calendar",
        "time spread debit",
        "near-term range with longer-term optionality",
        "term-structure relative value",
        "front short decay against back long option",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy back-month call and sell same-strike front-month call",
        "close all legs before the front expiry",
        "multiple expiries, term IV, rates, dividends and assignment context",
        "Historical panel measures the package, not a validated term-IV signal",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.CALL_DIAGONAL,
        "Call diagonal",
        "time and strike spread debit",
        "moderately bullish",
        "term-structure relative value",
        "long back call financed by higher-strike front call",
        "net debit plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy back-month call and sell higher-strike front-month call",
        "close all legs before the front expiry",
        "multiple expiries, skew, term IV, rates and assignment context",
        "Path-dependent assignment and rolling choices remain unmodeled",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LEAPS_CALL,
        "LEAPS call",
        "long-dated directional debit",
        "long-term bullish",
        "high vega and rho sensitivity",
        "long-duration convex upside",
        "premium paid plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy call near configured moneyness around one-year DTE",
        "profit target, stop, time exit, or separately validated roll",
        "long-dated liquidity, rates, dividends, borrow and IV history",
        "One-year free history cannot validate a full LEAPS lifecycle",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.LEAPS_PUT,
        "LEAPS put",
        "long-dated directional debit",
        "long-term bearish or standalone protection",
        "high vega and rho sensitivity",
        "long-duration convex downside",
        "premium paid plus costs",
        ArchitectureReadiness.BACKTESTED,
        "buy put near configured moneyness around one-year DTE",
        "profit target, stop, time exit, or separately validated roll",
        "long-dated liquidity, rates, dividends, borrow and IV history",
        "A +10% strike recipe is a hypothesis, not a validated universal rule",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.PROTECTIVE_PUT,
        "Protective put",
        "portfolio protection",
        "protect an existing long stock position",
        "long volatility",
        "floored portfolio downside",
        "put premium plus residual stock loss",
        ArchitectureReadiness.CATALOG_ONLY,
        "existing stock plus long put",
        "portfolio-defined hedge horizon or roll",
        "actual shares, tax lots, basis, hedge budget and permissions",
        "Blocked until real portfolio state is supplied",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.COVERED_CALL,
        "Covered call",
        "portfolio income",
        "neutral to moderately bullish",
        "short volatility",
        "capped stock upside with call premium",
        "stock downside less premium",
        ArchitectureReadiness.CATALOG_ONLY,
        "existing shares plus short call",
        "assignment-aware target, roll, or expiry",
        "actual shares, tax lots, dividends and assignment constraints",
        "Blocked until real portfolio state is supplied",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.COLLAR,
        "Collar / fence",
        "portfolio protection",
        "protect stock while financing the hedge",
        "mixed volatility exposure",
        "floored downside and capped upside",
        "bounded portfolio loss over the hedge window",
        ArchitectureReadiness.CATALOG_ONLY,
        "existing shares, long put, short call",
        "portfolio-defined horizon or coordinated roll",
        "actual shares, basis, tax, dividends and assignment constraints",
        "Blocked until real portfolio state is supplied",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.GAMMA_SCALPING,
        "Gamma scalping",
        "dynamic volatility trading",
        "realized volatility above implied costs",
        "long gamma with active delta hedging",
        "path-dependent hedge P&L",
        "option premium and repeated hedge losses",
        ArchitectureReadiness.CATALOG_ONLY,
        "long gamma package plus explicit hedge policy",
        "continuous rebalance and terminal close policy",
        "intraday options, stock ticks, fills, fees and hedge inventory",
        "EOD chains cannot backtest the required dynamic hedge path",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.SHORT_STRADDLE,
        "Short straddle",
        "naked short volatility",
        "very narrow range",
        "short gamma and vega",
        "limited premium with unbounded upside loss",
        "potentially unbounded",
        ArchitectureReadiness.RISK_DISABLED,
        "disabled",
        "disabled",
        "broker margin, intraday risk, assignment and hard limits",
        "Disabled by the bounded-risk policy",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.SHORT_STRANGLE,
        "Short strangle",
        "naked short volatility",
        "wide range",
        "short gamma and vega",
        "limited premium with unbounded upside loss",
        "potentially unbounded",
        ArchitectureReadiness.RISK_DISABLED,
        "disabled",
        "disabled",
        "broker margin, intraday risk, assignment and hard limits",
        "Disabled by the bounded-risk policy",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.RATIO_SPREAD,
        "Ratio spread",
        "asymmetric multi-leg",
        "directional with ratio exposure",
        "path-dependent gamma exposure",
        "ratio-dependent tail",
        "can be unbounded",
        ArchitectureReadiness.RISK_DISABLED,
        "disabled pending exact bounded specification",
        "disabled",
        "full margin, tail stress, assignment and ratio governance",
        "Generic ratio structures are too ambiguous for activation",
        _BOOK_SOURCE,
    ),
    StrategyArchitecture(
        StrategyKind.RATIO_BACKSPREAD,
        "Ratio backspread",
        "asymmetric convex spread",
        "large directional move",
        "long tail gamma when correctly constructed",
        "ratio-dependent convex tail",
        "construction-dependent",
        ArchitectureReadiness.RISK_DISABLED,
        "disabled pending exact bounded specification",
        "disabled",
        "full payoff proof, margin, liquidity and assignment governance",
        "The generic name does not prove bounded risk",
        _BOOK_SOURCE,
    ),
)

_BY_KIND = {architecture.kind: architecture for architecture in ARCHITECTURES}


def architecture_for(kind: StrategyKind) -> StrategyArchitecture | None:
    return _BY_KIND.get(kind)


def architecture_catalog_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for architecture in ARCHITECTURES:
        row = asdict(architecture)
        row["kind"] = architecture.kind.value
        row["readiness"] = architecture.readiness.value
        rows.append(row)
    return rows
