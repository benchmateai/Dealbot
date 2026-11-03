"""C, crypto market making in the ETH 15-minute books, bounded from above (maker).

Makers pay no fee in these series, and the research found the only lasting crypto edge belongs to whoever
rests orders, priced off the real settlement rule and pulled before informed takers arrive. C quotes both
sides at the best prices (a YES bid at the best YES bid, a NO bid at the best NO bid), QUOTE contracts
each, never letting its net position pass INVENTORY_CAP; re-joins the back of the queue whenever the best
price moves away from its order; pulls every quote PULL_LEFT_S before the close and holds what it owns to
settlement. Fills come only from lab/fills.py's pessimistic rules, so this is an upper bound: paper can
show C is unprofitable, never that it works. Markouts at 1 and 5 minutes say how much informed takers took.

    python -m lab.strategies.c_crypto_mm --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from lab.fills import EPS, apply_trade, markouts, place
from lab.strategies.maker_common import books_by_ticker, load, outcomes

REGISTERED_MS = 1_793_743_200_000  # 2026-11-03T22:00:00Z
SERIES = ("KXETH15M",)
QUOTE = 10
INVENTORY_CAP = 30
PULL_LEFT_S = 60


def evaluate(lab_dir: str | Path, *, since_ms: int = 0, registered_ms: int = REGISTERED_MS) -> dict:
    recs = load(lab_dir, since_ms=max(since_ms, registered_ms), kinds=("book", "trade", "settled"))
    result = outcomes(recs)
    live: dict[str, dict[str, object]] = defaultdict(dict)  # ticker -> side -> resting order
    every: dict[str, list] = defaultdict(list)               # ticker -> all orders ever placed
    inv: dict[str, float] = defaultdict(float)               # ticker -> net YES contracts
    for r in recs:
        if r["kind"] == "trade":
            for side, o in list(live.get(r["ticker"], {}).items()):
                q = apply_trade(o, {**r, "ts": r.get("trade_ts") or r["ts"]})
                inv[r["ticker"]] += q if side == "yes" else -q
            continue
        if r["kind"] != "book" or r.get("series") not in SERIES or not r.get("close_ms"):
            continue
        t = r["ticker"]
        if (r["close_ms"] - r["ts"]) / 1000.0 <= PULL_LEFT_S:
            live.pop(t, None)
            continue
        for side in ("yes", "no"):
            levels = r.get(side) or []
            if not levels:
                continue
            best_price = levels[0][0]
            room = INVENTORY_CAP - inv[t] if side == "yes" else INVENTORY_CAP + inv[t]
            o = live[t].get(side)
            if o is not None and abs(o.price - best_price) < EPS and o.remaining > 0:
                continue
            if room <= 0:
                live[t].pop(side, None)
                continue
            new = place(t, side, best_price, min(QUOTE, room), r["ts"], r)
            live[t][side] = new
            every[t].append(new)
    books = books_by_ticker(recs)
    fills, pnl, marks = 0.0, 0.0, []
    for t, orders in every.items():
        payout = result.get(t, (None, None))[0]
        for o in orders:
            for f in o.fills:
                fills += f["qty"]
                if payout is not None:
                    own = payout if o.side == "yes" else 1.0 - payout
                    pnl += f["qty"] * (own - f["price"])  # no maker fee in these series
            marks += markouts(o, books.get(t, []), payout)
    def avg(k):
        xs = [(m[k], m["qty"]) for m in marks if m.get(k) is not None]
        return None if not xs else round(sum(v * q for v, q in xs) / sum(q for _, q in xs) * 100, 3)
    summary = {"contracts_filled": fills, "orders": sum(len(v) for v in every.values()), "pnl_usd_upper_bound": round(pnl, 2),
               "markout_cents": {"1m": avg("m60"), "5m": avg("m300"), "settle": avg("settle")}}
    return {"summary": summary}


def one_line(s: dict) -> str:
    m = s["markout_cents"]
    return (f"C crypto market making (upper bound): {s['contracts_filled']:.0f} contracts filled, {s['pnl_usd_upper_bound']:+.2f} USD; "
            f"markout per contract {m['1m']} cents at 1 min, {m['5m']} at 5 min, {m['settle']} at settlement")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ETH 15-minute market making, bounded from above")
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
