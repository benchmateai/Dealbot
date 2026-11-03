"""Shared pieces for the lab's live-feed strategies (B, C, E, F): the normalized records they read, and the
desk's edge bar. lab/replay.py streams the records.

The live-feed recorder writes, in lab/data:
  book        {ticker, series, event, close_ms, strike, strike_type, set, yes: [[price, size], ...], no: [[price, size], ...]}
              YES bids and NO bids, best first, dollars and contracts (a YES ask is 1 - the best NO bid);
              set is "15m", "E" or "F"
  trade       {ticker, yes_price, count, taker_side, trade_ts}
  index       {symbol, value, avg60, qavg, qn}     the CF Benchmarks index, about once a second
  incentives  {programs: [...]}                    Kalshi's active liquidity-incentive programs
  settled     {series, event, rows: [[ticker, result, settlement value], ...]}   (both recorders)
"""

from __future__ import annotations

from collections.abc import Iterable

from kalshi.api import taker_fee_usd

MARGIN = 0.5


def outcomes(recs: Iterable[dict]) -> dict[str, tuple[float, float | None]]:
    """ticker -> (YES payout, settlement value) from every settled record."""
    out = {}
    for r in recs:
        if r["kind"] == "settled":
            for ticker, result, value in r.get("rows") or []:
                if result in ("yes", "no"):
                    out[ticker] = (1.0 if result == "yes" else 0.0, value)
    return out


def best(book: dict) -> tuple[float | None, float | None, float, float]:
    """(YES bid, YES ask, size at the YES bid, size at the YES ask) from a normalized book."""
    yes, no = book.get("yes") or [], book.get("no") or []
    bid = yes[0][0] if yes else None
    ask = 1.0 - no[0][0] if no else None
    return bid, ask, (yes[0][1] if yes else 0.0), (no[0][1] if no else 0.0)


def min_edge(price: float, spread: float) -> float:
    """The paper desk's bar: 1.5 x (Kalshi's taker fee on one contract + half the spread)."""
    return (1 + MARGIN) * (taker_fee_usd(1, price) + max(spread, 0.0) / 2)
