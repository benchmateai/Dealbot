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

The realistic figure (2026-11-05) marks every fill to where its side stood at the end of the recording, or
to its settlement, instead of only 5 minutes on (the last book with both sides quoted: until 2026-11-07 a
market whose book emptied as it closed dropped out of the marking, which left out a presidential-approval
market E held on the losing side and overstated E by about $100): what E still holds can keep moving against it, as it did
while election results came in. It also reports the money E ties up (its resting orders' collateral plus
what its holdings are worth, a market's holding no longer once its result is recorded: Kalshi has paid it
out) and the fee: every series E has quoted so far is 'quadratic', which charges
makers nothing (Kalshi's /series endpoint, fee_type), so no fee is taken.

    python -m lab.strategies.e_incentive --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from lab.fills import EPS, apply_trade, place, side_mid
from lab.recorder import _ts
from lab.replay import Markouts, live_records, settled_outcomes
from lab.strategies.maker_common import outcomes

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


def side_share(levels: list[list[float]], target: float, discount: float, mine: tuple[float, float] | None,
               *, whole_level: bool = False) -> float | None:
    """Our share of one side's qualifying liquidity with our order (price, size) added behind the orders at its
    price, or None when the side, ours included, falls short of the Target Size (the snapshot then pays no one).
    Kalshi scores the orders that "help reach the Target Size"; whether that gives the orders already resting
    at a price priority over a newer one there is unconfirmed. By default it does (ours counts only if the
    side has not reached the Target Size before it); whole_level=True counts every order at a level the walk
    reaches, ours included, the generous reading."""
    book = [(p, s, False) for p, s in levels]
    if mine and mine[1] > 0:
        book.append((mine[0], mine[1], True))
    book.sort(key=lambda x: -x[0])  # stable: ours stays behind the orders already at its price
    if sum(s for _, s, _ in book) < target:
        return None
    ref = reference_price([[p, s] for p, s, _ in book], target / 5)
    raw = ours = cum = 0.0
    last_price = None
    for p, s, is_ours in book:
        same_level = whole_level and last_price is not None and abs(p - last_price) <= EPS
        if cum >= target and not same_level:
            break
        last_price = p
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
    fills: list[dict] = []                           # every fill, to mark at the end
    last_book: dict[str, dict] = {}                  # the latest book with both sides quoted: a closing market's book empties
    tied: dict[str, float] = {}                      # ticker -> resting collateral + what the holding is worth
    capital_sum = capital_peak = 0.0
    capital_n = 0
    first_ts = last_ts = None
    for r in live_records(lab_dir, since_ms=max(since_ms, registered_ms), kinds=("book", "trade", "incentives", "settled")):
        if r["kind"] == "settled":  # paid out: what E held there is no longer tied up
            for t in outcomes([r]):
                if t in tied:
                    tied[t] = 0.0
            continue
        first_ts = r["ts"] if first_ts is None else first_ts
        last_ts = r["ts"]
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
                    fills.append({"ticker": r["ticker"], "side": side, "price": o.price, "qty": q})
            continue
        if r["kind"] != "book":
            continue
        marks.book(r["ticker"], r["ts"], r)
        if side_mid(r, "yes") is not None:
            last_book[r["ticker"]] = r
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
            tied[t] = _holding_value(inv[t], r)
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
        tied[t] = sum(x.price * x.remaining for x in live[t].values() if x.remaining > 0) + _holding_value(inv[t], r)
        capital = sum(tied.values())
        capital_sum, capital_n, capital_peak = capital_sum + capital, capital_n + 1, max(capital_peak, capital)
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
    settled = settled_outcomes(lab_dir) if fills else {}
    marked = 0.0
    for f in fills:
        payout = settled.get(f["ticker"], (None, None))[0]
        value = (payout if f["side"] == "yes" else 1.0 - payout) if payout is not None else (
            side_mid(last_book[f["ticker"]], f["side"]) if f["ticker"] in last_book else None)
        if value is not None:
            marked += f["qty"] * (value - f["price"])
    summary = {"markets": len(quoted), "programs": len(earned), "samples": samples, "paying_samples": paying,
               "reward_usd": round(reward, 2), "payable_usd": round(payable, 2), "contracts_filled": filled,
               "markout_usd": round(markout, 2), "net_usd_upper_bound": round(payable + markout, 2),
               "hours": round((last_ts - first_ts) / 3.6e6, 1) if first_ts is not None else 0.0,
               "fills_marked_usd": round(marked, 2), "net_usd_realistic": round(payable + marked, 2), "maker_fees_usd": 0.0,
               "capital_peak_usd": round(capital_peak, 2), "capital_avg_usd": round(capital_sum / capital_n, 2) if capital_n else 0.0,
               "held_markets": sum(1 for v in inv.values() if abs(v) > 0.5)}
    return {"summary": summary, "by_program": {k: round(v, 4) for k, v in sorted(earned.items(), key=lambda kv: -kv[1])}}


def _holding_value(net_yes: float, book: dict) -> float:
    """What E's holding in one market is worth on this book: its side's mid times the contracts."""
    if abs(net_yes) < 1e-9:
        return 0.0
    mid = side_mid(book, "yes" if net_yes > 0 else "no")
    return abs(net_yes) * (mid if mid is not None else 1.0)


def one_line(s: dict) -> str:
    return (f"E incentive capture (upper bound): {s['markets']} markets, reward {s['reward_usd']:.2f} USD earned ({s['payable_usd']:.2f} payable at $1 a program) "
            f"in {s['paying_samples']} of {s['samples']} samples; {s['contracts_filled']:.0f} contracts filled, markout {s['markout_usd']:+.2f} at 5 minutes; "
            f"net {s['net_usd_upper_bound']:+.2f}; realistic, fills marked to the end: {s['fills_marked_usd']:+.2f}, net {s['net_usd_realistic']:+.2f} "
            f"over {s['hours']:.1f} h on {s['capital_avg_usd']:,.0f} USD tied up on average ({s['capital_peak_usd']:,.0f} at most)")


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
