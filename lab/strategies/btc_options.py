"""The Bitcoin options test (lab, paper only, public data, no orders): Kalshi's and Polymarket US's Bitcoin markets
beside the odds Bitcoin's options imply, and paper buys wherever a venue sells a side for less than those odds
say it is worth, by more than its fee and the cost of the money.

It reads the gap recorder's records (lab/gap_recorder.py): gap_pair (each pair's fees, settlement dates and, for
the Bitcoin pairs, its `model`: what the contract pays on), gap_quote (both venues' best prices and sizes), and
the option records the recorder takes from Deribit's public API, opt_surface (every 5 minutes) and opt_index
(every pass). Each quote of a Bitcoin pair is priced on the latest surface at most SURFACE_MAX_AGE_MS old, with
the latest index at most INDEX_MAX_AGE_MS old (lab/btc_options.py: the year-end ranges at what the options
imply, the "hits $X" markets at a model's price), and then:
  gaps     how far each venue's mid sits from that price, time-weighted like lab/gap_report.py, for the ranges
           and the touch markets apart; and how often an edge of 1 cent or more was there to take
  trades   per variant, a paper taker buy at the displayed price and size, on either venue, of the side (YES at
           the ask, or NO at 1 - bid) worth more than it costs by the variant's hurdle after the venue's taker fee
           (Kalshi's rounded up to the cent per order) and CARRY_RATE a year on the money until settlement; at
           most STAKE_USD per market, side and venue, and CAP_USD open in all; one buy each, held to settlement
  marks    each position at the options' price now and at what the venue would pay for it now (its bid, or
           1 - ask for a NO), less fees and the cost of the money so far
  drift    how far, in the trade's favor, the venue's mid sat from the options' price at the entry and 1, 6
           and 24 hours later: whether the venues move toward the options or stay where they were
  settled  a market Kalshi has settled pays $1 a contract to the right side on both venues (their rules match)
Variants, fixed on 2026-11-10 before any result and never retuned: hurdles of 1, 2 and 3 cents.

    python -m lab.strategies.btc_options --lab lab/data [--since-ms MS] [--until-ms MS] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from lab.btc_options import YEAR_MS, Surface, fair, iso_ms
from lab.store import read_lab

REGISTERED_MS = 1_794_340_800_000  # 2026-11-10T20:00Z: the rules and variants here were fixed before any result
HURDLES = {"hurdle_1c": 0.01, "hurdle_2c": 0.02, "hurdle_3c": 0.03}
STAKE_USD = 100.0
CAP_USD = 3_000.0
CARRY_RATE = 0.04
SURFACE_MAX_AGE_MS = 15 * 60_000
INDEX_MAX_AGE_MS = 5 * 60_000
PAIR_LOOKBACK_MS = 4 * 3_600_000  # gap_pair records come once a chunk: read them from a little before the window
HOLD_MAX_S = 1_200
DRIFT_HOURS = (1, 6, 24)
TERMINAL = ("range", "above", "below")
VENUES = ("kalshi", "poly")


def taker_fee(venue: str, coeff: float, price: float, contracts: float) -> float:
    """An order's taker fee: coeff x price x (1 - price) a contract, Kalshi's rounded up to the cent per order."""
    raw = coeff * price * (1.0 - price) * contracts
    return math.ceil(raw * 100 - 1e-9) / 100 if venue == "kalshi" else raw


def edges(q: dict, fair_yes: float, coeff: float, years: float) -> list[tuple[str, float, float, float]]:
    """(side, price a contract, contracts on offer, edge a contract after the fee and the money's cost) for buying
    YES at the ask and NO at 1 - bid."""
    out = []
    ask, bid = q.get("ask"), q.get("bid")
    if ask is not None and q.get("ask_size"):
        out.append(("yes", ask, float(q["ask_size"]), fair_yes - ask - coeff * ask * (1 - ask) - ask * CARRY_RATE * years))
    if bid is not None and q.get("bid_size"):
        cost = 1.0 - bid
        out.append(("no", cost, float(q["bid_size"]), (1.0 - fair_yes) - cost - coeff * bid * (1 - bid) - cost * CARRY_RATE * years))
    return out


def _open(k: dict, p: dict) -> bool:
    return k.get("status") in (None, "active", "open") and p.get("state") in (None, "MARKET_STATE_OPEN")


def _mid(q: dict) -> float | None:
    return (q["bid"] + q["ask"]) / 2 if q.get("bid") is not None and q.get("ask") is not None else None


class Book:
    """One variant's paper positions."""

    def __init__(self, hurdle: float) -> None:
        self.hurdle = hurdle
        self.pos: dict[tuple[str, str, str], dict] = {}
        self.open_cost = 0.0

    def offer(self, ts: int, pair: str, venue: str, q: dict, fair_yes: float, coeff: float, years: float, group: str) -> None:
        for side, price, size, edge in edges(q, fair_yes, coeff, years):
            key = (pair, venue, side)
            if key in self.pos or edge < self.hurdle or price <= 0:
                continue
            n = math.floor(min(size, STAKE_USD / price, max(0.0, CAP_USD - self.open_cost) / price))
            if n < 1:
                continue
            mid = _mid(q)
            gap = (fair_yes - (mid if mid is not None else price)) if side == "yes" else ((mid if mid is not None else 1 - price) - fair_yes)
            self.pos[key] = {"ts": ts, "pair": pair, "venue": venue, "side": side, "group": group, "price": round(price, 4), "n": n,
                             "cost": n * price, "fee": taker_fee(venue, coeff, price, n), "edge": round(edge, 4), "gap0": gap,
                             "drift": {}, "worth_fair": fair_yes if side == "yes" else 1 - fair_yes,
                             "worth_bid": (q.get("bid") or 0.0) if side == "yes" else (1 - q["ask"] if q.get("ask") is not None else 0.0),
                             "payout": None, "settled_ts": None}
            self.open_cost += n * price

    def observe(self, ts: int, pair: str, venue: str, q: dict, fair_yes: float) -> None:
        mid = _mid(q)
        for side in ("yes", "no"):
            r = self.pos.get((pair, venue, side))
            if r is None or r["payout"] is not None:
                continue
            r["worth_fair"] = fair_yes if side == "yes" else 1 - fair_yes
            r["worth_bid"] = (q.get("bid") or 0.0) if side == "yes" else (1 - q["ask"] if q.get("ask") is not None else 0.0)
            if mid is not None:
                for h in DRIFT_HOURS:
                    if h not in r["drift"] and ts >= r["ts"] + h * 3_600_000:
                        r["drift"][h] = (fair_yes - mid) if side == "yes" else (mid - fair_yes)

    def settle(self, ts: int, pair: str, result: str) -> None:
        for r in self.pos.values():
            if r["pair"] == pair and r["payout"] is None:
                r["payout"] = 1.0 if (r["side"] == result) else 0.0
                r["worth_fair"] = r["worth_bid"] = r["payout"]
                r["settled_ts"] = ts
                self.open_cost -= r["cost"]

    def summary(self, end_ts: int) -> dict:
        def agg(rows: list[dict]) -> dict:
            cost, fee = sum(r["cost"] for r in rows), sum(r["fee"] for r in rows)
            carry = sum(r["cost"] * CARRY_RATE * max(0, (r["settled_ts"] or end_ts) - r["ts"]) / YEAR_MS for r in rows)
            at_fair, at_bid = sum(r["n"] * r["worth_fair"] for r in rows), sum(r["n"] * r["worth_bid"] for r in rows)
            return {"positions": len(rows), "contracts": sum(r["n"] for r in rows), "cost_usd": round(cost, 2), "fees_usd": round(fee, 2),
                    "carry_usd": round(carry, 2), "pnl_at_options_usd": round(at_fair - cost - fee - carry, 2),
                    "pnl_at_bids_usd": round(at_bid - cost - fee - carry, 2), "settled": sum(1 for r in rows if r["payout"] is not None)}
        rows = list(self.pos.values())
        out = agg(rows)
        out["by_venue"] = {v: agg([r for r in rows if r["venue"] == v]) for v in VENUES}
        out["by_group"] = {g: agg([r for r in rows if r["group"] == g]) for g in ("terminal", "touch")}
        out["drift"] = {}
        for h in DRIFT_HOURS:
            seen = [r for r in rows if h in r["drift"]]
            out["drift"][f"{h}h"] = {"positions": len(seen),
                                     "gap_at_entry_cents": round(100 * sum(r["gap0"] for r in seen) / len(seen), 2) if seen else None,
                                     "gap_after_cents": round(100 * sum(r["drift"][h] for r in seen) / len(seen), 2) if seen else None}
        out["entries"] = sorted(({k: r[k] for k in ("ts", "pair", "venue", "side", "price", "n", "fee", "edge", "worth_fair", "worth_bid", "payout")} for r in rows),
                                key=lambda r: r["ts"])
        return out


def _wmedian(rows: list[tuple[float, float]]) -> float | None:
    rows = sorted(r for r in rows if r[1] > 0)
    total = sum(w for _, w in rows)
    if not total:
        return None
    acc = 0.0
    for v, w in rows:
        acc += w
        if acc >= total / 2:
            return v
    return rows[-1][0]


def evaluate(lab_dir: str | Path, *, since_ms: int = REGISTERED_MS, until_ms: int | None = None, hurdles: dict[str, float] = HURDLES) -> dict:
    pairs: dict[str, dict] = {}
    for r in read_lab(lab_dir, since_ms=max(0, since_ms - PAIR_LOOKBACK_MS), until_ms=until_ms, kinds=("gap_pair",), streams=("gap",)):
        if r.get("model"):
            pairs[r["pair"]] = r
    surfaces: list[tuple[int, dict]] = []
    index: list[tuple[int, float]] = []
    quotes: list[tuple[int, str, dict, dict]] = []
    end_ts = 0
    for r in read_lab(lab_dir, since_ms=since_ms, until_ms=until_ms, kinds=("gap_pair", "gap_quote", "opt_surface", "opt_index"), streams=("gap",)):
        end_ts = max(end_ts, r["ts"])
        if r["kind"] == "gap_pair":
            if r.get("model"):
                pairs[r["pair"]] = r
        elif r["kind"] == "opt_surface":
            surfaces.append((r["ts"], r))
        elif r["kind"] == "opt_index":
            index.append((r["ts"], float(r["index"])))
        elif r.get("pair") in pairs:
            quotes.append((r["ts"], r["pair"], r["k"], r["p"]))
    quotes.sort(key=lambda q: q[0])
    holds, following = [0.0] * len(quotes), {}
    for i in range(len(quotes) - 1, -1, -1):  # a quote holds until its pair's next one, at most HOLD_MAX_S
        ts, pair = quotes[i][0], quotes[i][1]
        holds[i] = min(HOLD_MAX_S, max(0, following.get(pair, end_ts) - ts) / 1000)
        following[pair] = ts

    books = {name: Book(h) for name, h in hurdles.items()}
    dev = {v: {"terminal": [], "touch": []} for v in VENUES}       # (|mid - fair|, mid - fair, seconds)
    takeable = {v: [0.0, 0.0] for v in VENUES}                      # seconds with an edge of 1c or more, seconds seen
    built: dict[int, Surface] = {}
    cache: dict[tuple, float | None] = {}
    latest: dict[str, dict] = {}
    si = ii = -1
    for i, (ts, pair, k, p) in enumerate(quotes):
        info = pairs[pair]
        if k.get("result") in ("yes", "no"):
            for book in books.values():
                book.settle(ts, pair, k["result"])
        while si + 1 < len(surfaces) and surfaces[si + 1][0] <= ts:
            si += 1
        while ii + 1 < len(index) and index[ii + 1][0] <= ts:
            ii += 1
        if si < 0 or ts - surfaces[si][0] > SURFACE_MAX_AGE_MS or not _open(k, p):
            continue
        if ii >= 0 and ts - index[ii][0] <= INDEX_MAX_AGE_MS:
            spot, spot_key = index[ii][1], ("index", ii)
        elif ts - surfaces[si][0] <= INDEX_MAX_AGE_MS:
            spot, spot_key = float(surfaces[si][1]["index"]), ("surface", si)
        else:
            continue
        key = (pair, si, spot_key)
        if key not in cache:
            if si not in built:
                built[si] = Surface(surfaces[si][1], surfaces[si][0])
            cache[key] = fair(info["model"], built[si], ts, spot)
        f = cache[key]
        if f is None:
            continue
        group = "terminal" if info["model"]["kind"] in TERMINAL else "touch"
        years = max(0.0, (iso_ms(info["model"].get("at") or info["model"]["by"]) - ts) / YEAR_MS)
        w = holds[i]
        k_fee = 0.07 if info.get("k_fee") is None else float(info["k_fee"])
        p_fee = 0.095 if info.get("p_fee") is None else float(info["p_fee"])
        for venue, q, coeff in (("kalshi", k, k_fee), ("poly", p, p_fee)):
            mid = _mid(q)
            if mid is not None:
                dev[venue][group].append((abs(mid - f), mid - f, w))
            best = max((e[3] for e in edges(q, f, coeff, years)), default=None)
            takeable[venue][1] += w
            if best is not None and best >= 0.01:
                takeable[venue][0] += w
            for book in books.values():
                book.observe(ts, pair, venue, q, f)
                book.offer(ts, pair, venue, q, f, coeff, years, group)
        latest[pair] = {"pair": pair, "ts": ts, "fair": round(f, 4), "kalshi_mid": _mid(k), "poly_mid": _mid(p), "group": group}

    def dev_line(rows: list[tuple[float, float, float]]) -> dict:
        seconds = sum(r[2] for r in rows)
        med = _wmedian([(r[0], r[2]) for r in rows])
        return {"hours": round(seconds / 3600, 1), "median_gap_cents": round(100 * med, 2) if med is not None else None,
                "mean_signed_cents": round(100 * sum(r[1] * r[2] for r in rows) / seconds, 2) if seconds else None}
    deviation = {v: {"all": dev_line(dev[v]["terminal"] + dev[v]["touch"]), "terminal": dev_line(dev[v]["terminal"]),
                     "touch": dev_line(dev[v]["touch"]),
                     "edge_1c_share": round(takeable[v][0] / takeable[v][1], 4) if takeable[v][1] else 0.0} for v in VENUES}
    rows = sorted(latest.values(), key=lambda r: -max(abs((r["kalshi_mid"] if r["kalshi_mid"] is not None else r["fair"]) - r["fair"]),
                                                       abs((r["poly_mid"] if r["poly_mid"] is not None else r["fair"]) - r["fair"])))
    return {"registered_ms": REGISTERED_MS, "since_ms": since_ms, "end_ms": end_ts,
            "summary": {"pairs": len(pairs), "pairs_priced": len(latest), "surfaces": len(surfaces), "index_points": len(index), "quotes": len(quotes)},
            "deviation": deviation, "variants": {name: b.summary(end_ts) for name, b in books.items()}, "latest": rows}


def one_line(r: dict) -> str:
    s = r["summary"]
    if not s["surfaces"]:
        return f"options test: {s['pairs']} Bitcoin pairs, no option surface recorded yet"
    d = r["deviation"]
    c = lambda x: "-" if x is None else f"{x:.1f}c"  # noqa: E731
    v2 = r["variants"].get("hurdle_2c") or next(iter(r["variants"].values()))
    return (f"options test: {s['pairs_priced']} of {s['pairs']} Bitcoin pairs priced on {s['surfaces']} option surfaces; median gap to the options' "
            f"price on Kalshi {c(d['kalshi']['all']['median_gap_cents'])} (ranges {c(d['kalshi']['terminal']['median_gap_cents'])}, touches "
            f"{c(d['kalshi']['touch']['median_gap_cents'])}), on Polymarket US {c(d['poly']['all']['median_gap_cents'])} (ranges "
            f"{c(d['poly']['terminal']['median_gap_cents'])}, touches {c(d['poly']['touch']['median_gap_cents'])}); an edge of 1c or more after "
            f"fees and the money's cost {100 * d['kalshi']['edge_1c_share']:.1f}% of the time on Kalshi, {100 * d['poly']['edge_1c_share']:.1f}% on "
            f"Polymarket US; 2c hurdle: {v2['positions']} paper buys costing ${v2['cost_usd']:,.2f}, {v2['pnl_at_options_usd']:+.2f} at the options' "
            f"price and {v2['pnl_at_bids_usd']:+.2f} at the venues' bids")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The Bitcoin options test: both venues beside the options' price, and paper buys of the gaps")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--since-ms", type=int, default=REGISTERED_MS)
    parser.add_argument("--until-ms", type=int, default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    r = evaluate(args.lab, since_ms=args.since_ms, until_ms=args.until_ms)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(r, indent=1))
    print(one_line(r))
    for name, v in r["variants"].items():
        kv, pv = v["by_venue"]["kalshi"], v["by_venue"]["poly"]
        print(f"  {name}: {v['positions']} buys, {v['contracts']} contracts, ${v['cost_usd']:,.2f} paid, fees {v['fees_usd']:.2f}, money's cost "
              f"{v['carry_usd']:.2f}; at the options' price {v['pnl_at_options_usd']:+.2f}, at the bids {v['pnl_at_bids_usd']:+.2f} "
              f"(Kalshi {kv['positions']} buys {kv['pnl_at_bids_usd']:+.2f}, Polymarket US {pv['positions']} buys {pv['pnl_at_bids_usd']:+.2f}); "
              f"{v['settled']} settled")
    for row in r["latest"][:6]:
        k = "-" if row["kalshi_mid"] is None else f"{100 * row['kalshi_mid']:.1f}"
        p = "-" if row["poly_mid"] is None else f"{100 * row['poly_mid']:.1f}"
        print(f"  {row['pair']}: options {100 * row['fair']:.1f}c, Kalshi mid {k}c, Polymarket US mid {p}c")
    return 0


if __name__ == "__main__":
    sys.exit(main())
