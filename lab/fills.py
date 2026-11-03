"""Pessimistic paper fills for resting orders, from the order book and trade prints only, with markouts.

Paper cannot know a resting order's place in the queue or whether a touch would have filled it, and fills
arrive disproportionately just before the price moves against the maker. So a simulated maker result is
an upper bound, and this module makes that bound as tight as the data allows:

- an order joins the back of the queue: everything displayed at its price when it is placed is ahead of it
- it fills only from trades: at its own price once the queue ahead has traded, or any trade that prints
  through its price (which must have taken it first)
- a quote touching it never fills it
- each fill records its markout: the contract's mid 60 and 300 seconds later (the book as it stood then:
  the last one recorded at or before that moment, no older than MAX_BOOK_AGE_MS, with the recording still
  running after it), and the settlement, against the fill price, which measures what informed takers took

Kalshi's conventions: a trade has a YES price and a taker side. A YES taker buys YES from a resting NO bid
at 1 - yes_price; a NO taker buys NO from a resting YES bid at yes_price. Books list YES bids and NO bids
(a YES ask is 1 - the best NO bid). Prices are dollars.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

MARKOUT_S = (60, 300)
MAX_BOOK_AGE_MS = 330_000  # the live feed rewrites an unchanged book at least every 5 minutes
TICK = 0.01
EPS = 0.00005  # prices are 4-decimal dollar strings, and some books tick in tenths of a cent: compare tightly


@dataclass
class Resting:
    ticker: str
    side: str  # "yes": a YES bid at `price`; "no": a NO bid at `price` (a YES offer at 1 - price)
    price: float
    size: float
    placed_ts: int
    queue_ahead: float
    filled: float = 0.0
    fills: list[dict] = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return max(0.0, self.size - self.filled)


def displayed_at(levels: list[list[float]], price: float) -> float:
    return sum(s for p, s in levels if abs(p - price) < EPS)


def place(ticker: str, side: str, price: float, size: float, ts: int, book: dict) -> Resting:
    """A resting order behind everything already displayed at its price on its side of `book`."""
    return Resting(ticker, side, round(price, 4), size, ts, displayed_at(book.get(side) or [], price))


def apply_trade(order: Resting, trade: dict) -> float:
    """Fill `order` from one trade print; returns the contracts filled (and records them)."""
    if order.remaining <= 0 or trade.get("ts", 0) < order.placed_ts:
        return 0.0
    yes_price, count, taker = float(trade["yes_price"]), float(trade["count"]), trade.get("taker_side")
    if order.side == "yes":
        if taker != "no":
            return 0.0
        at_our_price, through = abs(yes_price - order.price) < EPS, yes_price < order.price - EPS
    else:
        if taker != "yes":
            return 0.0
        our_yes_offer = 1.0 - order.price
        at_our_price, through = abs(yes_price - our_yes_offer) < EPS, yes_price > our_yes_offer + EPS
    if through:
        qty = min(order.remaining, count)
    elif at_our_price:
        eaten = min(order.queue_ahead, count)
        order.queue_ahead -= eaten
        qty = min(order.remaining, count - eaten)
    else:
        return 0.0
    if qty > 0:
        order.filled += qty
        order.fills.append({"ts": trade["ts"], "qty": qty, "price": order.price, "through": through})
    return qty


def side_mid(book: dict, side: str) -> float | None:
    """The mid of the order's own side: for a YES bid the YES mid, for a NO bid the NO mid."""
    yes, no = book.get("yes") or [], book.get("no") or []
    if not yes or not no:
        return None
    best_yes_bid, best_no_bid = yes[0][0], no[0][0]
    yes_mid = (best_yes_bid + (1.0 - best_no_bid)) / 2
    return yes_mid if side == "yes" else 1.0 - yes_mid


def book_at(books: list[tuple[int, dict]], times: list[int], ts: int) -> dict | None:
    """The book as it stood at `ts`: the last one recorded at or before it, if it is recent enough and the
    recording ran on past `ts`. `times` are the books' times."""
    if not times or times[-1] < ts:
        return None
    i = bisect.bisect_right(times, ts) - 1
    return books[i][1] if i >= 0 and ts - times[i] <= MAX_BOOK_AGE_MS else None


def markouts(order: Resting, books: list[tuple[int, dict]], payout_yes: float | None) -> list[dict]:
    """For each fill: the side's mid MARKOUT_S seconds later and the settlement value, minus the fill price
    (positive is good for the maker). `books` is (ts, book) in time order for this ticker."""
    out = []
    times = [t for t, _ in books]
    for f in order.fills:
        row = {"ts": f["ts"], "qty": f["qty"], "price": f["price"]}
        for s in MARKOUT_S:
            later = book_at(books, times, f["ts"] + s * 1000)
            mid = side_mid(later, order.side) if later else None
            row[f"m{s}"] = None if mid is None else round(mid - f["price"], 4)
        if payout_yes is not None:
            settle = payout_yes if order.side == "yes" else 1.0 - payout_yes
            row["settle"] = round(settle - f["price"], 4)
        out.append(row)
    return out
