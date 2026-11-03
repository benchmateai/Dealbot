"""F, the maker long-shot fade: rest NO bids where recreational traders overbuy YES long shots (maker).

Across Kalshi's trade history every price below 20 cents did worse than its odds and every price above 80
did better, and the makers on the other side of long-shot YES buying collected the difference. F rests a
NO bid at the best NO bid (a YES offer at the best YES ask) in long-dated markets whose YES ask is between
1 and 10 cents, QUOTE contracts, at most EVENT_CAP per event (a ladder on one event is one correlated bet),
re-joining the best price after a day unfilled, and holds every fill to settlement. Fills follow
lab/fills.py's pessimistic rules, so the result is an upper bound; a fill from a trade printing through
the price is reported separately because it is the likeliest to be real. One upset at 95 cents cancels
about 20 wins, so a verdict needs thousands of settled contracts.

    python -m lab.strategies.f_fade --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from lab.fills import apply_trade, place
from lab.replay import live_records, settled_outcomes
from lab.strategies.maker_common import best

REGISTERED_MS = 1_793_743_200_000  # 2026-11-03T22:00:00Z
YES_ASK_RANGE = (0.01, 0.10)
QUOTE = 10
EVENT_CAP = 30
REPLACE_AFTER_MS = 86_400_000


def evaluate(lab_dir: str | Path, *, since_ms: int = 0, registered_ms: int = REGISTERED_MS) -> dict:
    start = max(since_ms, registered_ms)
    result = settled_outcomes(lab_dir, since_ms=start)
    live: dict[str, object] = {}
    every: dict[str, list] = defaultdict(list)
    event_of: dict[str, str] = {}
    exposure: dict[str, float] = defaultdict(float)  # event -> contracts committed
    for r in live_records(lab_dir, since_ms=start, kinds=("book", "trade")):
        if r["kind"] == "trade":
            o = live.get(r["ticker"])
            if o is not None:
                apply_trade(o, {**r, "ts": r.get("trade_ts") or r["ts"]})
            continue
        if r["kind"] != "book" or r.get("set") != "F":
            continue
        t, event = r["ticker"], r.get("event") or r["ticker"]
        event_of[t] = event
        _, ask, _, _ = best(r)
        o = live.get(t)
        if o is not None and (o.remaining <= 0 or r["ts"] - o.placed_ts < REPLACE_AFTER_MS):
            continue
        if ask is None or not YES_ASK_RANGE[0] <= ask <= YES_ASK_RANGE[1]:
            continue
        if o is not None:  # a day unfilled: cancel and re-join the best price
            exposure[event] -= o.remaining
        room = EVENT_CAP - exposure[event]
        if room <= 0:
            continue
        new = place(t, "no", round(1.0 - ask, 4), min(QUOTE, room), r["ts"], r)
        live[t] = new
        every[t].append(new)
        exposure[event] += new.size
    filled = through = 0.0
    pnl = settled = upsets = 0.0
    for t, orders in every.items():
        payout = result.get(t, (None, None))[0]
        for o in orders:
            for f in o.fills:
                filled += f["qty"]
                through += f["qty"] if f["through"] else 0.0
                if payout is not None:
                    settled += f["qty"]
                    upsets += f["qty"] if payout == 1.0 else 0.0
                    pnl += f["qty"] * ((1.0 - payout) - f["price"])
    summary = {"markets": len(every), "contracts_filled": filled, "filled_by_trade_through": through, "contracts_settled": settled,
               "upset_contracts": upsets, "pnl_usd_upper_bound": round(pnl, 2)}
    return {"summary": summary}


def one_line(s: dict) -> str:
    return (f"F maker long-shot fade (upper bound): {s['markets']} markets, {s['contracts_filled']:.0f} contracts filled "
            f"({s['filled_by_trade_through']:.0f} by trades through the price), {s['contracts_settled']:.0f} settled with "
            f"{s['upset_contracts']:.0f} upsets, {s['pnl_usd_upper_bound']:+.2f} USD")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resting NO bids against long-shot YES buying, bounded from above")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = evaluate(args.lab)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(one_line(report["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
