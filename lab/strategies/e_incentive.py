"""E, liquidity-incentive capture (maker): rest reward-earning size on both sides and count what Kalshi's program
would pay, less what the fills cost.

Kalshi pays a pool per market for resting depth (docs/lab/kalshi_interfaces.md 2.1-2.2). It snapshots the
book every second and finds each side's Reference Price: walking down from the best bid, the first level
where cumulative size reaches a fifth of the Target Size. Orders at or better than it get full credit,
orders below it the Discount Factor per tick; each side's pool of P / (2N) a second is split by share of
the liquidity that helps reach the Target Size, and a snapshot pays no one unless both sides reach it.

E rests QUOTE_FRACTION of the Target Size on each side at that side's Reference Price (full credit, and
further from the top than the best price), behind the orders already there, never letting its net
position pass INVENTORY_CAP_FRACTION of the Target Size, and re-joins at the new Reference Price whenever
it moves or the order fills. Each recorded book (every 15 s) stands until the next one, at most MAX_GAP_S,
so E only ever reacts to a book it has seen. Fills come from lab/fills.py's pessimistic rules, and each is
charged its 5-minute markout (the move of its side's mid against it), because these markets settle long
after the test. A program's reward below $1 is not paid. Where the rules are silent (whether the order
that crosses the Target Size counts in full; ticks on a tenth-of-a-cent grid) E takes the reading in the
reference sketch: whole levels, one-cent ticks. The recording does not see a market's open or paused
state, so E also counts any paused spell Kalshi would exclude. Reward less markouts is an upper bound on
what E keeps.

    python -m lab.strategies.e_incentive --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from lab.fills import EPS, apply_trade, place
from lab.recorder import _ts
from lab.replay import Markouts, live_records

REGISTERED_MS = 1_793_743_200_000  # 2026-11-03T22:00:00Z
QUOTE_FRACTION = 0.1
INVENTORY_CAP_FRACTION = 0.3
MAX_GAP_S = 75.0  # the feed's 60 s heartbeat for these books, plus slack: a longer gap is a recording gap
TICK = 0.01
MIN_PAYOUT_USD = 1.0


def reference_price(levels: list[list[float]], depth: float) -> float | None:
    cum = 0.0
    for p, s in levels:
        cum += s
        if cum >= depth:
            return p
    return None


def side_share(levels: list[list[float]], target: float, discount: float, mine: tuple[float, float] | None) -> float | None:
    """Our share of one side's qualifying liquidity with our order (price, size) added behind the orders at its
    price, or None when the side, ours included, falls short of the Target Size (the snapshot then pays no one)."""
    book = [(p, s, False) for p, s in levels]
    if mine and mine[1] > 0:
        book.append((mine[0], mine[1], True))
    book.sort(key=lambda x: -x[0])  # stable: ours stays behind the orders already at its price
    if sum(s for _, s, _ in book) < target:
        return None
    ref = reference_price([[p, s] for p, s, _ in book], target / 5)
    raw = ours = cum = 0.0
    for p, s, is_ours in book:
        if cum >= target:
            break
        credit = s * (1.0 if p >= ref - EPS else discount ** round((ref - p) / TICK))
        raw += credit
        ours += credit if is_ours else 0.0
        cum += s
    return ours / raw if raw > 0 else 0.0


def _per_side_per_s(p: dict) -> float:
    start, end = _ts(p.get("start_date")), _ts(p.get("end_date"))
    return (p.get("period_reward") or 0) / 10_000 / (2 * (end - start) / 1000.0) if start and end and end > start else 0.0


def evaluate(lab_dir: str | Path, *, since_ms: int = 0, registered_ms: int = REGISTERED_MS) -> dict:
    programs: dict[str, list[dict]] = {}
    marks = Markouts()
    live: dict[str, dict] = defaultdict(dict)        # ticker -> side -> resting order
    quoted: set[str] = set()                         # markets E placed an order in
    inv: dict[str, float] = defaultdict(float)       # ticker -> net YES contracts
    standing: dict[str, tuple[int, dict[str, float]]] = {}  # ticker -> (book time, program id -> reward a second)
    earned: dict[str, float] = defaultdict(float)    # program id -> USD
    samples = paying = 0
    for r in live_records(lab_dir, since_ms=max(since_ms, registered_ms), kinds=("book", "trade", "incentives")):
        if r["kind"] == "incentives":
            programs = defaultdict(list)
            for p in r.get("programs") or []:
                if p.get("incentive_type") == "liquidity" and p.get("target_size_fp") and _per_side_per_s(p) > 0:
                    programs[p["market_ticker"]].append(p)
            continue
        if r["kind"] == "trade":
            for side, o in live.get(r["ticker"], {}).items():
                q = apply_trade(o, {**r, "ts": r.get("trade_ts") or r["ts"]})
                if q:
                    inv[r["ticker"]] += q if side == "yes" else -q
                    marks.fill(o.ticker, o.side, o.fills[-1])
            continue
        if r["kind"] != "book":
            continue
        marks.book(r["ticker"], r["ts"], r)
        if "E" not in (r.get("sets") or [r.get("set")]):
            continue
        t, ts = r["ticker"], r["ts"]
        if t in standing:  # the previous book, and E's orders against it, stood until now
            since, rates = standing.pop(t)
            dt = min(MAX_GAP_S, (ts - since) / 1000.0)
            for pid, rate in rates.items():
                earned[pid] += rate * dt
        active = [p for p in programs.get(t, []) if (_ts(p.get("start_date")) or 0) <= ts < (_ts(p.get("end_date")) or 0)]
        if not active:
            live.pop(t, None)
            continue
        target = float(max(active, key=_per_side_per_s)["target_size_fp"])
        mine: dict[str, tuple[float, float]] = {}
        for side in ("yes", "no"):
            ref = reference_price(r.get(side) or [], target / 5)
            room = INVENTORY_CAP_FRACTION * target - (inv[t] if side == "yes" else -inv[t])
            if ref is None or room <= 0:
                live[t].pop(side, None)
                continue
            o = live[t].get(side)
            if o is None or abs(o.price - ref) > EPS or o.remaining <= 0:
                o = place(t, side, ref, min(QUOTE_FRACTION * target, room), ts, r)
                live[t][side] = o
                quoted.add(t)
            mine[side] = (o.price, o.remaining)
        rates = {}
        for p in active:
            samples += 1
            discount = (p.get("discount_factor_bps") or 10_000) / 10_000
            shares = [side_share(r.get(side) or [], float(p["target_size_fp"]), discount, mine.get(side)) for side in ("yes", "no")]
            if None in shares:
                continue
            paying += 1
            rates[p["id"]] = _per_side_per_s(p) * sum(shares)
        standing[t] = (ts, rates)
    filled = markout = 0.0
    for m in marks.rows:
        filled += m["qty"]
        if m.get("m300") is not None:
            markout += m["qty"] * m["m300"]
    reward = sum(earned.values())
    payable = sum(math.floor(v * 100) / 100 for v in earned.values() if v >= MIN_PAYOUT_USD)
    summary = {"markets": len(quoted), "programs": len(earned), "samples": samples, "paying_samples": paying,
               "reward_usd": round(reward, 2), "payable_usd": round(payable, 2), "contracts_filled": filled,
               "markout_usd": round(markout, 2), "net_usd_upper_bound": round(payable + markout, 2)}
    return {"summary": summary, "by_program": {k: round(v, 4) for k, v in sorted(earned.items(), key=lambda kv: -kv[1])}}


def one_line(s: dict) -> str:
    return (f"E incentive capture (upper bound): {s['markets']} markets, reward {s['reward_usd']:.2f} USD earned ({s['payable_usd']:.2f} payable at $1 a program) "
            f"in {s['paying_samples']} of {s['samples']} samples; {s['contracts_filled']:.0f} contracts filled, markout {s['markout_usd']:+.2f} at 5 minutes; "
            f"net {s['net_usd_upper_bound']:+.2f}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Liquidity-incentive capture, reward less markouts")
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
