"""Tick type and the feed interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class FeedError(RuntimeError):
    pass


@dataclass(frozen=True)
class Tick:
    ts: int
    bid: float
    ask: float
    bid_qty: float
    ask_qty: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    def is_sane(self) -> bool:
        return self.bid > 0 and self.ask > 0 and self.ask >= self.bid and self.bid_qty >= 0 and self.ask_qty >= 0


class MarketFeed(Protocol):
    symbols: tuple[str, ...]

    def advance(self, until_ms: int) -> dict[str, list[Tick]]:
        """Deliver every not-yet-delivered tick with ts < until_ms, per symbol."""

    def history(self, sym: str) -> list[Tick]:
        """All delivered ticks for sym, oldest first (bounded)."""

    def last_tick_age_ms(self, sym: str, now_ms: int) -> int | None:
        """Age of the newest delivered tick, or None if nothing was delivered yet."""
