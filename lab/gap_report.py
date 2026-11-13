"""How big the Kalshi to Polymarket US price gaps are, how long they last, and whether any pays after fees.

From the gap recorder's records (lab/gap_recorder.py). For each pair and each recorded moment, with both
venues open and their quotes no more than MAX_SKEW_S apart:
  mid gap   Polymarket US's mid minus Kalshi's (only where both sides of both books are quoted)
  lock A    buy YES on Kalshi at its ask and short on Polymarket US at its bid:   p.bid - k.ask
  lock B    buy YES on Polymarket US at its ask and NO on Kalshi at its YES bid:  k.bid - p.ask
  net       the better lock less both taker fees, each coeff x price x (1 - price) per contract (Kalshi
            rounds its fee up to the cent per order, so a small order pays a little more than this)
  size      the contracts resting at both best prices (the smaller side); a lock counts as crossed or
            paying only with MIN_SIZE contracts or more
  carry     a lock ties up about $1 a contract (one leg's price plus the other's collateral, 1 - gross)
            until the market settles (the earlier of Kalshi's expected settlement and Polymarket US's
            end date): net after carry takes CARRY_RATE a year (T-bills) off it, which is what decides a
            long-dated lock such as a 2028 nomination
A moment holds until the pair's next record (the recorder writes one on any change and every HEARTBEAT_S),
and a pair's last moment until the recording's last record, at most HOLD_MAX_S either way. An episode is a run of moments with net above zero; it counts as lasting when it spans at
least two passes of the recorder (MIN_EPISODE_S), since a gap seen once may be the seconds between the two
venues' reads. A lock is only an upper bound on what a desk could keep: it assumes both orders fill at the
quoted prices at once, and the two contracts' rules match only as far as each pair's note says.

    python -m lab.gap_report --lab lab/data [--since-ms MS] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from lab.store import read_lab

MAX_SKEW_S = 20
HOLD_MAX_S = 1_200
MIN_EPISODE_S = 100
MIN_SIZE = 10  # contracts at both prices for a lock to count: a lock nobody could fill is not one
CARRY_RATE = 0.04
YEAR_MS = 365.25 * 86_400_000


def fee(coeff: float, price: float) -> float:
    return coeff * price * (1.0 - price)


def locks(k: dict, p: dict, k_fee: float, p_fee: float) -> dict | None:
    """The two locks at one moment, gross and net per contract, with the size at both prices; None if the
    two venues' quotes cannot be compared (a venue closed, or read too far apart)."""
    if k.get("status") not in (None, "active", "open") or p.get("state") not in (None, "MARKET_STATE_OPEN"):
        return None
    if abs((k.get("ts") or 0) - (p.get("ts") or 0)) > MAX_SKEW_S * 1000:
        return None
    out = {"mid_gap": None, "a": None, "b": None}
    if None not in (k.get("bid"), k.get("ask"), p.get("bid"), p.get("ask")):
        out["mid_gap"] = (p["bid"] + p["ask"]) / 2 - (k["bid"] + k["ask"]) / 2
    if k.get("ask") is not None and p.get("bid") is not None:
        gross = p["bid"] - k["ask"]
        out["a"] = (gross, gross - fee(k_fee, k["ask"]) - fee(p_fee, p["bid"]), min(k.get("ask_size") or 0.0, p.get("bid_size") or 0.0))
    if k.get("bid") is not None and p.get("ask") is not None:
        gross = k["bid"] - p["ask"]
        out["b"] = (gross, gross - fee(k_fee, k["bid"]) - fee(p_fee, p["ask"]), min(k.get("bid_size") or 0.0, p.get("ask_size") or 0.0))
    return out


def _share(rows: list[dict], key: str) -> float:
    """A share of the time over several pairs, each weighted by the hours it was seen."""
    hours = sum(r["hours"] for r in rows)
    return round(sum(r[key] * r["hours"] for r in rows) / hours, 4) if hours else 0.0


def report(lab_dir: str | Path, *, since_ms: int = 0, until_ms: int | None = None, carry_rate: float = CARRY_RATE) -> dict:
    pairs: dict[str, dict] = {}
    series: dict[str, list[tuple[int, dict, dict]]] = defaultdict(list)
    status = None
    end_ts = 0
    for r in read_lab(lab_dir, since_ms=since_ms, until_ms=until_ms, kinds=("gap_pair", "gap_quote", "gap_status"), streams=("gap",)):
        end_ts = max(end_ts, r["ts"])
        if r["kind"] == "gap_pair":
            pairs[r["pair"]] = r
        elif r["kind"] == "gap_quote":
            series[r["pair"]].append((r["ts"], r["k"], r["p"]))
        else:
            status = r
    rows = []
    for pair, quotes in sorted(series.items()):
        info = pairs.get(pair) or {}
        k_fee = 0.07 if info.get("k_fee") is None else float(info["k_fee"])  # 0.0 means the market charges no fee
        p_fee = 0.095 if info.get("p_fee") is None else float(info["p_fee"])
        settles = min([x for x in (info.get("k_close"), info.get("p_end")) if x], default=None)
        quotes.sort(key=lambda q: q[0])
        seen_s = crossed_s = paying_s = carried_s = 0.0
        mids, best_net, best = [], None, None
        episodes, run_s, run_best = [], 0.0, 0.0
        for i, (ts, k, p) in enumerate(quotes):
            hold = min(HOLD_MAX_S, max(0, (quotes[i + 1][0] if i + 1 < len(quotes) else end_ts) - ts) / 1000)
            lk = locks(k, p, k_fee, p_fee)
            if lk is None:
                continue
            seen_s += hold
            if lk["mid_gap"] is not None:
                mids.append(lk["mid_gap"])
            years = max(0.0, (settles - ts) / YEAR_MS) if settles else 0.0
            # each leg: (gross, net of fees, size, net after carry)
            legs = [(x[0], x[1], x[2], x[1] - (1.0 - x[0]) * carry_rate * years) for x in (lk["a"], lk["b"]) if x is not None and x[2] >= MIN_SIZE]
            top = max(legs, key=lambda x: x[3], default=None)
            if top is not None and top[0] > 0:
                crossed_s += hold
            if top is not None and top[1] > 0:
                paying_s += hold
            if top is not None and top[3] > 0:
                carried_s += hold
                run_s += hold
                run_best = max(run_best, top[3])
            elif run_s:
                episodes.append((run_s, run_best))
                run_s, run_best = 0.0, 0.0
            if top is not None and (best_net is None or top[3] > best_net):
                best_net, best = top[3], {"ts": ts, "gross": round(top[0], 4), "net": round(top[1], 4), "net_after_carry": round(top[3], 4),
                                          "years_to_settle": round(years, 2), "size": round(top[2], 1), "usd": round(max(0.0, top[3]) * top[2], 2), "k": k, "p": p}
        if run_s:
            episodes.append((run_s, run_best))
        lasting = [e for e in episodes if e[0] >= MIN_EPISODE_S]
        rows.append({"pair": pair, "category": info.get("category"), "kalshi": info.get("kalshi"), "polymarket_us": info.get("polymarket_us"),
                     "hours": round(seen_s / 3600, 2), "quotes": len(quotes),
                     "mid_gap_median_cents": round(100 * statistics.median([abs(m) for m in mids]), 2) if mids else None,
                     "mid_gap_mean_cents": round(100 * statistics.fmean(mids), 2) if mids else None,
                     "crossed_share": round(crossed_s / seen_s, 4) if seen_s else 0.0, "paying_share": round(paying_s / seen_s, 4) if seen_s else 0.0,
                     "paying_after_carry_share": round(carried_s / seen_s, 4) if seen_s else 0.0,
                     "episodes": len(episodes), "lasting_episodes": len(lasting), "longest_episode_s": round(max((e[0] for e in episodes), default=0.0)),
                     "best": best})
    seen = [r for r in rows if r["hours"] > 0]
    mids_all = [r["mid_gap_median_cents"] for r in seen if r["mid_gap_median_cents"] is not None]
    summary = {"pairs": len(pairs), "pairs_seen": len(seen), "hours": round(sum(r["hours"] for r in seen), 1),
               "median_mid_gap_cents": round(statistics.median(mids_all), 2) if mids_all else None,
               "crossed_share": _share(seen, "crossed_share"), "paying_share": _share(seen, "paying_share"),
               "paying_after_carry_share": _share(seen, "paying_after_carry_share"),
               "carry_rate": carry_rate,
               "pairs_with_lasting_episode": sum(1 for r in seen if r["lasting_episodes"]),
               "lasting_episodes": sum(r["lasting_episodes"] for r in seen),
               "best_usd": max((r["best"]["usd"] for r in seen if r["best"]), default=0.0),
               "recorder": {k: status.get(k) for k in ("kalshi", "polymarket_us", "quotes")} if status else None}
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in seen:
        by_cat[r["category"] or "other"].append(r)
    # by kind of market too: Kalshi quotes its year-end Bitcoin ranges in tenths of a cent and Polymarket US in
    # whole cents, so the cheapest ranges' books cross by a fraction of a cent most of the time
    summary["categories"] = {c: {"pairs": len(v), "median_mid_gap_cents": round(statistics.median([r["mid_gap_median_cents"] for r in v if r["mid_gap_median_cents"] is not None]), 2)
                                 if any(r["mid_gap_median_cents"] is not None for r in v) else None,
                                 "crossed_share": _share(v, "crossed_share"), "paying_share": _share(v, "paying_share"),
                                 "paying_after_carry_share": _share(v, "paying_after_carry_share"),
                                 "lasting_episodes": sum(r["lasting_episodes"] for r in v)} for c, v in sorted(by_cat.items())}
    return {"summary": summary, "pairs": rows}


def one_line(s: dict) -> str:
    if not s["pairs_seen"]:
        return f"gaps: {s['pairs']} pairs registered, nothing recorded yet"
    return (f"gaps: {s['pairs_seen']} of {s['pairs']} pairs over {s['hours']:.0f} pair-hours; median mid gap {s['median_mid_gap_cents']}c; "
            f"books crossed {100 * s['crossed_share']:.2f}% of the time, paying after both taker fees {100 * s['paying_share']:.2f}%, "
            f"and after {100 * s['carry_rate']:.0f}% a year on the money tied up {100 * s['paying_after_carry_share']:.2f}%; "
            f"{s['lasting_episodes']} such gaps lasted 100 s or more, in {s['pairs_with_lasting_episode']} pairs; best ${s['best_usd']:.2f} at the quoted size")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kalshi to Polymarket US price gaps from the gap recorder")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--since-ms", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    r = report(args.lab, since_ms=args.since_ms)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(r, indent=1))
    print(one_line(r["summary"]))
    for cat, v in r["summary"].get("categories", {}).items():
        print(f"  {cat}: {v['pairs']} pairs, median mid gap {v['median_mid_gap_cents']}c, crossed {100 * v['crossed_share']:.2f}%, "
              f"paying after fees {100 * v['paying_share']:.2f}% and after the money's cost {100 * v['paying_after_carry_share']:.2f}%, "
              f"{v['lasting_episodes']} lasting paying gaps")
    top = sorted((x for x in r["pairs"] if x["best"]), key=lambda x: -x["best"]["net_after_carry"])[:5]
    for x in top:
        b = x["best"]
        print(f"  best {x['pair']}: {100 * b['net_after_carry']:+.2f}c a contract after fees and carry ({100 * b['net']:+.2f}c after fees, "
              f"gross {100 * b['gross']:+.2f}c, {b['years_to_settle']:.2f} years to settle) on {b['size']:.0f} contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
