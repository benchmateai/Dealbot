"""Seeded random-walk quotes. Deterministic for (seed, symbols, start_ms); never reads the wall clock."""

from __future__ import annotations

import math
import random

from feed.base import Tick

DEFAULT_PRICES = {"ETH-USD": 2500.0, "BTC-USD": 60000.0}


class SyntheticFeed:
    def __init__(
        self,
        symbols: tuple[str, ...],
        *,
        start_ms: int,
        tick_ms: int = 1000,
        seed: int = 7,
        start_prices: dict[str, float] | None = None,
        vol_bps_per_tick: float = 3.0,
        spread_bps: float = 2.0,
        max_history: int = 50_000,
    ) -> None:
        self.symbols = tuple(symbols)
        self._rng = random.Random(seed)
        self._tick_ms = tick_ms
        self._vol = vol_bps_per_tick
        self._spread = spread_bps
        self._max_history = max_history
        prices = {**DEFAULT_PRICES, **(start_prices or {})}
        self._px = {s: prices.get(s, 100.0) for s in self.symbols}
        self._next_ts = {s: start_ms for s in self.symbols}
        self._hist: dict[str, list[Tick]] = {s: [] for s in self.symbols}

    def advance(self, until_ms: int) -> dict[str, list[Tick]]:
        out: dict[str, list[Tick]] = {}
        for sym in self.symbols:
            new: list[Tick] = []
            while self._next_ts[sym] < until_ms:
                ts = self._next_ts[sym]
                self._px[sym] *= math.exp(self._rng.gauss(0.0, self._vol / 1e4))
                mid = self._px[sym]
                half = mid * self._spread / 2e4
                bid_qty = round(self._rng.uniform(1.0, 10.0), 3)
                ask_qty = round(self._rng.uniform(1.0, 10.0), 3)
                new.append(Tick(ts, round(mid - half, 6), round(mid + half, 6), bid_qty, ask_qty))
                self._next_ts[sym] += self._tick_ms
            hist = self._hist[sym]
            hist.extend(new)
            if len(hist) > self._max_history:
                del hist[: len(hist) - self._max_history]
            out[sym] = new
        return out

    def history(self, sym: str) -> list[Tick]:
        return self._hist[sym]

    def seed_history(self, sym: str, ticks: list[Tick]) -> None:
        """Restore a tail of ticks from a checkpoint so the first blocks after a restart are not blind."""
        if sym in self._hist and ticks:
            self._hist[sym] = sorted(ticks, key=lambda t: t.ts)

    def last_tick_age_ms(self, sym: str, now_ms: int) -> int | None:
        hist = self._hist.get(sym)
        return None if not hist else now_ms - hist[-1].ts
