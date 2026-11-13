"""Modes. shadow: Jev labels every decision, the policy logs what it would have done, nothing
executes. paper: the policy executes against the paper broker. Both run the full risk gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from broker.base import Broker, Fill, Order
from desk.clock import Block
from logs.writer import LogWriter
from risk.gate import RiskApproval

MODES = ("shadow", "paper")


@dataclass(frozen=True)
class ExecResult:
    executed: bool
    status: str
    fill: Fill | None = None
    reason: str | None = None


class Executor(Protocol):
    mode: str

    def execute(self, order: Order, approval: RiskApproval, *, block: Block) -> ExecResult: ...


class ShadowExecutor:
    mode = "shadow"

    def __init__(self, log: LogWriter) -> None:
        self._log = log

    def execute(self, order: Order, approval: RiskApproval, *, block: Block) -> ExecResult:
        self._log.write("would_execute", {"decision_id": order.decision_id, "order": order.to_dict(), "blk": block.number}, ts_ms=block.ts_ms)
        return ExecResult(False, "shadow", None, "shadow mode: nothing executes")


class PaperExecutor:
    mode = "paper"

    def __init__(self, broker: Broker, log: LogWriter) -> None:
        if getattr(broker, "kind", None) != "paper":
            raise ValueError("paper mode requires the paper broker")
        self._broker = broker
        self._log = log

    def execute(self, order: Order, approval: RiskApproval, *, block: Block) -> ExecResult:
        ack = self._broker.place_order(order, approval)
        self._log.write("order", {"decision_id": order.decision_id, "order": order.to_dict(), "status": ack.status, "reason": ack.reason, "blk": block.number}, ts_ms=block.ts_ms)
        if ack.fill is not None:
            self._log.write("fill", {**ack.fill.to_dict(), "decision_id": order.decision_id, "blk": block.number}, ts_ms=ack.fill.ts)
        return ExecResult(ack.status == "filled", ack.status, ack.fill, ack.reason)


def make_executor(mode: str, broker: Broker, log: LogWriter) -> Executor:
    if mode == "shadow":
        return ShadowExecutor(log)
    if mode == "paper":
        return PaperExecutor(broker, log)
    raise ValueError(f"unknown mode {mode!r}; expected one of {MODES}")
