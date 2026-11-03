"""Replaying the live feed for strategies B, C, E and F without holding a week of records in memory.

The live feed alone writes book, trade, index and incentives records, and one writer's hour files hold its
records in the order it wrote them, so they can stream straight from disk in time order. Settlements (from
both recorders) are few and read first. Markouts are worked out as the books stream past, giving the same
numbers as lab.fills.markouts with every book in hand.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from lab.fills import MARKOUT_S, MAX_BOOK_AGE_MS, side_mid
from lab.store import read_lab
from lab.strategies.maker_common import outcomes

LIVE_KINDS = ("book", "trade", "index", "incentives")


def live_records(lab_dir: str | Path, *, since_ms: int = 0, kinds: tuple[str, ...] = LIVE_KINDS) -> Iterator[dict]:
    """The live feed's records from `since_ms` on, in the order it recorded them."""
    wanted = [k for k in kinds if k in LIVE_KINDS]
    return read_lab(lab_dir, since_ms=since_ms, kinds=wanted)


def settled_outcomes(lab_dir: str | Path, *, since_ms: int = 0) -> dict[str, tuple[float, float | None]]:
    """ticker -> (YES payout, settlement value), from every settled record of either recorder."""
    return outcomes(read_lab(lab_dir, since_ms=since_ms, kinds=("settled",)))


class Markouts:
    """Each fill's markout: its side's mid MARKOUT_S seconds after the fill, from the book as it stood then
    (the last one at or before that moment, no older than MAX_BOOK_AGE_MS), once a book at or after the
    moment shows the recording ran past it; minus the fill price, so positive is good for the maker."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self._last: dict[str, tuple[int, dict]] = {}
        self._waiting: dict[str, list[tuple[int, str, dict]]] = defaultdict(list)

    def fill(self, ticker: str, side: str, fill: dict) -> dict:
        row = {"ticker": ticker, "side": side, "ts": fill["ts"], "qty": fill["qty"], "price": fill["price"]}
        for s in MARKOUT_S:
            row[f"m{s}"] = None
            self._waiting[ticker].append((fill["ts"] + s * 1000, f"m{s}", row))
        self.rows.append(row)
        return row

    def book(self, ticker: str, ts: int, book: dict) -> None:
        waiting = self._waiting.get(ticker)
        if waiting:
            before = self._last.get(ticker)
            still = []
            for target, key, row in waiting:
                if ts < target:
                    still.append((target, key, row))
                    continue
                at = (ts, book) if ts == target else before
                if at is not None and target - at[0] <= MAX_BOOK_AGE_MS:
                    mid = side_mid(at[1], row["side"])
                    row[key] = None if mid is None else round(mid - row["price"], 4)
            if still:
                self._waiting[ticker] = still
            else:
                del self._waiting[ticker]
        self._last[ticker] = (ts, book)

    def settle(self, result: dict[str, tuple[float, float | None]]) -> list[dict]:
        """Adds each fill's settlement markout where its market has settled; returns every row."""
        for row in self.rows:
            payout = result.get(row["ticker"], (None, None))[0]
            if payout is not None:
                own = payout if row["side"] == "yes" else 1.0 - payout
                row["settle"] = round(own - row["price"], 4)
        return self.rows
