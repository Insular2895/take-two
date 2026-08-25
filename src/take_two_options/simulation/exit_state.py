"""Serializable, look-ahead-safe state machine for simulated exit policies."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from take_two_options.domain import StrictModel


class ExitState(StrEnum):
    OPEN = "open"
    PROFIT_TARGET = "profit_target"
    STOP_LOSS = "stop_loss"
    TIME_EXIT = "time_exit"


class ExitMachineState(StrictModel):
    """Complete state after observing one checkpoint on a single path."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, frozen=True)

    state: ExitState = ExitState.OPEN
    current_day: int = Field(default=0, ge=0)
    exit_day: int | None = Field(default=None, ge=0)
    pnl: float
    peak_pnl: float
    maximum_drawdown: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_terminal_state(self) -> ExitMachineState:
        terminal = self.state is not ExitState.OPEN
        if terminal != (self.exit_day is not None):
            raise ValueError("terminal exit states require exit_day; open states forbid it")
        if self.exit_day is not None and self.exit_day != self.current_day:
            raise ValueError("exit_day must equal the last observed current_day")
        if self.peak_pnl < self.pnl:
            raise ValueError("peak_pnl cannot be below current pnl")
        return self

    @property
    def terminal(self) -> bool:
        return self.state is not ExitState.OPEN


def initial_exit_state(initial_pnl: float) -> ExitMachineState:
    return ExitMachineState(pnl=initial_pnl, peak_pnl=initial_pnl)


def advance_exit_state(
    previous: ExitMachineState,
    *,
    day: int,
    pnl: float,
    return_on_risk: float,
    is_final_checkpoint: bool,
    profit_target: float | None,
    stop_loss: float | None,
) -> ExitMachineState:
    """Advance using only information observable at ``day``.

    Profit and stop thresholds are evaluated before the contractual time exit,
    preserving the historical engine's same-checkpoint priority.
    """

    if previous.terminal:
        raise ValueError("a terminal exit state cannot be advanced")
    if day <= previous.current_day:
        raise ValueError("exit checkpoints must be strictly chronological")
    if profit_target is not None and profit_target <= 0:
        raise ValueError("profit_target must be positive")
    if stop_loss is not None and stop_loss <= 0:
        raise ValueError("stop_loss must be positive")

    peak_pnl = max(previous.peak_pnl, pnl)
    maximum_drawdown = max(previous.maximum_drawdown, peak_pnl - pnl)
    if profit_target is not None and return_on_risk >= profit_target:
        state = ExitState.PROFIT_TARGET
    elif stop_loss is not None and return_on_risk <= -stop_loss:
        state = ExitState.STOP_LOSS
    elif is_final_checkpoint:
        state = ExitState.TIME_EXIT
    else:
        state = ExitState.OPEN
    return ExitMachineState(
        state=state,
        current_day=day,
        exit_day=day if state is not ExitState.OPEN else None,
        pnl=pnl,
        peak_pnl=peak_pnl,
        maximum_drawdown=maximum_drawdown,
    )
