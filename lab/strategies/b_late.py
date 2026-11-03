"""B, late-window tail harvesting in the 15-minute BTC and ETH contracts (taker).

In the last three minutes much of the sixty-second settlement average is already fixed, so a contract can be
a near-certain YES while the spot price still sits below the strike. B prices that exactly from the CF
Benchmarks index prints (lab/model.py with the observed part of the average) and buys the side it makes at
least P_MIN likely, at the displayed ask and no more than the displayed size (capped at MAX_CONTRACTS), only
when the ask is below that probability by the desk's edge bar (1.5 x the taker fee plus half the spread).
One entry per contract, held to settlement, net of Kalshi's taker fee. The market makers price this too, so
the question is only whether they lag the index by enough, often enough, to pay for the upsets.

    python -m lab.strategies.b_late --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from kalshi.api import taker_fee_usd
from lab.model import EwmaVol, p_contract
from lab.strategies.maker_common import best, load, min_edge, outcomes

REGISTERED_MS = 1_793_743_200_000  # 2026-11-03T22:00:00Z
P_MIN = 0.95
LEFT_S = (5, 180)
MAX_CONTRACTS = 100
INDEX_FOR = {"KXBTC15M": "BRTI", "KXETH15M": "ETHUSD_RTI"}


def evaluate(lab_dir: str | Path, *, since_ms: int = 0, registered_ms: int = REGISTERED_MS) -> dict:
    recs = load(lab_dir, since_ms=since_ms)
    result = outcomes(recs)
    vols: dict[str, EwmaVol] = defaultdict(lambda: EwmaVol(half_life_s=1800.0))
    last_index: dict[str, tuple[int, float]] = {}
    window: dict[str, list[float]] = defaultdict(list)  # ticker -> log index prints inside its last minute
    active: dict[str, tuple[str, int]] = {}  # ticker -> (index symbol, close)
    entries: dict[str, dict] = {}
    for r in recs:
        if r["kind"] == "index":
            sym = r.get("symbol")
            if r.get("value"):
                v = float(r["value"])
                vols[sym].update(r["ts"], v)
                last_index[sym] = (r["ts"], v)
                for t, (s, close) in list(active.items()):
                    if close <= r["ts"]:
                        del active[t]  # closed: its window is complete
                    elif s == sym and close - 60_000 <= r["ts"]:
                        window[t].append(math.log(v))
            continue
        if r["kind"] != "book" or r.get("series") not in INDEX_FOR:
            continue
        ticker, close_ms = r["ticker"], r.get("close_ms")
        sym = INDEX_FOR[r["series"]]
        if not close_ms:
            continue
        if close_ms > r["ts"]:
            active[ticker] = (sym, close_ms)
        if sym not in last_index:
            continue
        tau = (close_ms - r["ts"]) / 1000.0
        idx_ts, idx = last_index[sym]
        if not LEFT_S[0] <= tau <= LEFT_S[1] or ticker in entries or r["ts"] < registered_ms or r["ts"] - idx_ts > 5_000:
            continue
        obs = window[ticker]
        p = p_contract(r.get("strike_type") or "greater_or_equal", r.get("strike"), None, idx, tau, vols[sym].s2_per_s,
                       observed_log_mean=(sum(obs) / len(obs)) if (tau < 60 and obs) else None)
        bid, ask, bid_size, ask_size = best(r)
        if p is None or bid is None or ask is None:
            continue
        spread = ask - bid
        if p >= P_MIN and p - ask >= min_edge(ask, spread) and ask_size > 0:
            entries[ticker] = {"ticker": ticker, "ts": r["ts"], "side": "YES", "price": ask, "qty": min(MAX_CONTRACTS, ask_size), "p": round(p, 4), "tau": tau}
        elif 1 - p >= P_MIN and (1 - p) - (1 - bid) >= min_edge(1 - bid, spread) and bid_size > 0:
            entries[ticker] = {"ticker": ticker, "ts": r["ts"], "side": "NO", "price": 1 - bid, "qty": min(MAX_CONTRACTS, bid_size), "p": round(p, 4), "tau": tau}
    closed = []
    for e in entries.values():
        if e["ticker"] in result:
            yes = result[e["ticker"]][0]
            won = (yes == 1.0) == (e["side"] == "YES")
            fee = taker_fee_usd(e["qty"], e["price"])
            closed.append({**e, "won": won, "fee": fee, "pnl": round(e["qty"] * ((1.0 if won else 0.0) - e["price"]) - fee, 2)})
    summary = {"entries": len(entries), "settled": len(closed), "won": sum(c["won"] for c in closed), "upsets": sum(not c["won"] for c in closed),
               "pnl_usd": round(sum(c["pnl"] for c in closed), 2), "contracts": sum(c["qty"] for c in closed),
               "per_contract_cents": round(100 * sum(c["pnl"] for c in closed) / max(1, sum(c["qty"] for c in closed)), 3)}
    return {"summary": summary, "trades": closed}


def one_line(s: dict) -> str:
    return (f"B late-window harvest: {s['settled']} settled entries, {s['upsets']} upsets, {s['pnl_usd']:+.2f} USD after fees "
            f"({s['per_contract_cents']:+.3f} cents a contract over {s['contracts']:.0f} contracts)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Late-window tail harvesting on the 15-minute contracts")
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
