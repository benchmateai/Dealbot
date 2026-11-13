"""Block clock: the decision cadence. One block = one chance to decide; Jev must answer before the next."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Block:
    number: int
    ts_ms: int
    next_ts_ms: int


class BlockClock:
    def __init__(self, block_ms: int, start_ms: int, *, realtime: bool = True, now_ms: Callable[[], int] | None = None, sleep: Callable[[float], None] | None = None, start_number: int = 0) -> None:
        if block_ms <= 0:
            raise ValueError("block_ms must be positive")
        self._block_ms = block_ms
        self._start = start_ms
        self._start_number = start_number
        self._realtime = realtime
        self._now = now_ms or (lambda: int(time.time() * 1000))
        self._sleep = sleep or time.sleep

    def blocks(self, max_blocks: int | None = None) -> Iterator[Block]:
        ts, n = self._start, self._start_number
        while max_blocks is None or n < self._start_number + max_blocks:
            if self._realtime:
                wait = ts - self._now()
                if wait > 0:
                    self._sleep(wait / 1000)
            yield Block(n, ts, ts + self._block_ms)
            ts += self._block_ms
            n += 1
