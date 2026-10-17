"""Replay recorded ticks from a JSONL file: one object per line with ts, sym, bid, ask, bid_qty, ask_qty."""

from __future__ import annotations

import json
from pathlib import Path

from feed.base import FeedError, Tick


class ReplayFeed:
    def __init__(self, path: str | Path, symbols: tuple[str, ...] | None = None, *, max_history: int = 200_000) -> None:
        rows: dict[str, list[Tick]] = {}
        with open(path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    tick = Tick(int(obj["ts"]), float(obj["bid"]), float(obj["ask"]), float(obj["bid_qty"]), float(obj["ask_qty"]))
                    sym = str(obj["sym"])
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise FeedError(f"{path}:{line_no}: bad tick row ({exc})") from exc
                rows.setdefault(sym, []).append(tick)
        for ticks in rows.values():
            ticks.sort(key=lambda t: t.ts)
        self.symbols = tuple(symbols) if symbols else tuple(sorted(rows))
        missing = [s for s in self.symbols if s not in rows]
        if missing:
            raise FeedError(f"replay file has no rows for {missing}")
        self._rows = rows
        self._cursor = {s: 0 for s in self.symbols}
        self._hist: dict[str, list[Tick]] = {s: [] for s in self.symbols}
        self._max_history = max_history

    def advance(self, until_ms: int) -> dict[str, list[Tick]]:
        out: dict[str, list[Tick]] = {}
        for sym in self.symbols:
            rows = self._rows[sym]
            i = self._cursor[sym]
            start = i
            while i < len(rows) and rows[i].ts < until_ms:
                i += 1
            new = rows[start:i]
            self._cursor[sym] = i
            hist = self._hist[sym]
            hist.extend(new)
            if len(hist) > self._max_history:
                del hist[: len(hist) - self._max_history]
            out[sym] = new
        return out

    def history(self, sym: str) -> list[Tick]:
        return self._hist[sym]

    def last_tick_age_ms(self, sym: str, now_ms: int) -> int | None:
        hist = self._hist.get(sym)
        return None if not hist else now_ms - hist[-1].ts

    def exhausted(self) -> bool:
        return all(self._cursor[s] >= len(self._rows[s]) for s in self.symbols)
