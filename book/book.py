"""The book: at most one open position (or one pending entry order) at a time, plus equity marks."""

from __future__ import annotations

import math
from dataclasses import dataclass

from broker.base import Order
from state.snapshot import AccountState

DAY_MS = 86_400_000


class BookError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenPosition:
    sym: str
    qty: float
    entry_price: float
    entry_ts: int
    entry_block: int
    decision_id: str
    bot: str

    @property
    def side(self) -> str:
        return "long" if self.qty > 0 else "short"

    @property
    def sign(self) -> int:
        return 1 if self.qty > 0 else -1

    def upnl_bps(self, mid: float) -> float:
        return self.sign * 1e4 * math.log(mid / self.entry_price)

    def to_dict(self) -> dict:
        return {**self.__dict__, "side": self.side}


@dataclass(frozen=True)
class PendingOrder:
    order: Order
    placed_block: int


class Book:
    def __init__(self) -> None:
        self.position: OpenPosition | None = None
        self.pending: PendingOrder | None = None
        self.equity: float | None = None
        self.peak_equity: float | None = None
        self.day_start_equity: float | None = None
        self.day_peak_equity: float | None = None
        self._day: int | None = None

    def can_scan(self) -> bool:
        """No scan while a position is open or an entry order is resting."""
        return self.position is None and self.pending is None

    def open(self, position: OpenPosition) -> None:
        if self.position is not None:
            raise BookError(f"one open position at a time; {self.position.sym} is open")
        self.position = position
        self.pending = None

    def close(self) -> OpenPosition:
        if self.position is None:
            raise BookError("no open position to close")
        position, self.position = self.position, None
        return position

    def set_pending(self, order: Order, placed_block: int) -> None:
        if self.position is not None or self.pending is not None:
            raise BookError("a position or pending order already exists")
        self.pending = PendingOrder(order, placed_block)

    def clear_pending(self) -> PendingOrder | None:
        pending, self.pending = self.pending, None
        return pending

    def mark(self, equity: float, now_ms: int) -> None:
        day = now_ms // DAY_MS
        if self._day != day:
            self._day = day
            self.day_start_equity = equity
            self.day_peak_equity = equity
        self.equity = equity
        self.peak_equity = equity if self.peak_equity is None else max(self.peak_equity, equity)
        self.day_peak_equity = equity if self.day_peak_equity is None else max(self.day_peak_equity, equity)

    def day_pnl(self, equity: float | None = None) -> float:
        if self.day_start_equity is None:
            return 0.0
        current = self.equity if equity is None else equity
        return 0.0 if current is None else current - self.day_start_equity

    def account_state(self, inventory: float) -> AccountState:
        equity = self.equity or 0.0
        return AccountState(
            inventory=inventory,
            equity_usd=equity,
            peak_equity_usd=self.peak_equity or equity,
            day_peak_equity_usd=self.day_peak_equity or equity,
        )
