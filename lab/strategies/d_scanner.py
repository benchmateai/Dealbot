"""D, the consistency scanner: contradictions between linked Kalshi contracts that pay at least $1 whatever
happens, measured after both taker fees. No forecast is involved, so a paper count of them is honest.

  ladder   "above K" contracts on one settlement number: above a higher strike can never be likelier than
           above a lower one, so a YES bid at the higher strike over a YES ask at the lower one is locked:
           buy YES low and NO high, cost ask_lo + (1 - bid_hi) < $1, pays at least $1
  range    a partition of brackets on one settlement number: NO on every bracket with a bid pays one less
           than their count, so bids summing over $1 lock a profit; YES on every bracket asks summing
           under $1 lock one too
  pair     the 15-minute contract that closes on the hour settles on the same sixty-second index average
           as that hour's ladder (verified from both rule texts): its YES bid over an hourly "above K"
           ask with K below its strike, or its YES ask under an hourly bid with K at or above it, is locked

Each finding records the gross gap, the edge left after Kalshi's taker fee on every leg (fee rounded up
to the cent per order, at 1 and at 100 contracts), the size shown at the top of the book (when the
data has it), and how many consecutive snapshots it lasted. The quotes come from Kalshi's market list,
which can be up to 15 seconds old and are not simultaneous across legs, so a finding seen in a single
snapshot is reported apart from one that persists.

    python -m lab.strategies.d_scanner --data lab/data [--since-ms MS]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from kalshi.api import taker_fee_usd
from lab.store import read_lab

REGISTERED_MS = 1_793_739_600_000  # 2026-11-03T21:00:00Z: the scanner's rules, fixed before its data
F = {"ticker": 0, "strike_type": 1, "floor": 2, "cap": 3, "bid": 4, "ask": 5, "bid_size": 6, "ask_size": 7}
PAIR_MAX_SKEW_MS = 10_000


def _fees(prices: list[float], contracts: int) -> float:
    return sum(taker_fee_usd(contracts, p) for p in prices)


def _net(gap: float, leg_prices: list[float]) -> dict:
    return {"gap": round(gap, 4), "net_1": round(gap - _fees(leg_prices, 1), 4), "net_100": round(gap - _fees(leg_prices, 100) / 100, 4)}


def _q(v) -> float | None:
    return None if v is None else float(v)


def ladder_findings(rows: list[list]) -> list[dict]:
    above = sorted((r for r in rows if r[F["strike_type"]] in ("greater", "greater_or_equal") and r[F["floor"]] is not None), key=lambda r: r[F["floor"]])
    out = []
    best_lo = None  # the lowest ask among lower strikes
    for r in above:
        bid, ask = _q(r[F["bid"]]), _q(r[F["ask"]])
        if best_lo is not None and bid is not None and bid > 0:
            lo = best_lo
            lo_ask = _q(lo[F["ask"]])
            if bid > lo_ask:
                f = {"kind": "ladder", "legs": [f"YES {lo[F['ticker']]}", f"NO {r[F['ticker']]}"], **_net(bid - lo_ask, [lo_ask, 1 - bid])}
                f["size"] = min(x for x in (_q(lo[F["ask_size"]]), _q(r[F["bid_size"]])) if x is not None) if lo[F["ask_size"]] is not None and r[F["bid_size"]] is not None else None
                out.append(f)
        if ask is not None and 0 < ask < 1 and (best_lo is None or ask < _q(best_lo[F["ask"]])):
            best_lo = r
    return out


def range_findings(rows: list[list]) -> list[dict]:
    legs = [r for r in rows if r[F["strike_type"]] in ("between", "less", "greater", "less_or_equal", "greater_or_equal")]
    if len(legs) < 3 or not any(r[F["strike_type"]] == "between" for r in legs):
        return []
    out = []
    bids = [(r, _q(r[F["bid"]])) for r in legs if _q(r[F["bid"]]) and _q(r[F["bid"]]) > 0]
    if bids:
        total = sum(b for _, b in bids)
        if total > 1:
            f = {"kind": "range_no", "legs": [f"NO {r[F['ticker']]}" for r, _ in bids], **_net(total - 1, [1 - b for _, b in bids])}
            sizes = [_q(r[F["bid_size"]]) for r, _ in bids]
            f["size"] = min(sizes) if all(s is not None for s in sizes) else None
            out.append(f)
    asks = [_q(r[F["ask"]]) for r in legs]
    if all(a is not None and 0 < a < 1 for a in asks):
        total = sum(asks)
        if total < 1:
            f = {"kind": "range_yes", "legs": [f"YES {r[F['ticker']]}" for r in legs], **_net(1 - total, asks)}
            sizes = [_q(r[F["ask_size"]]) for r in legs]
            f["size"] = min(sizes) if all(s is not None for s in sizes) else None
            out.append(f)
    return out


def pair_findings(m15: list, ladder_rows: list[list]) -> list[dict]:
    strike, bid15, ask15 = _q(m15[F["floor"]]), _q(m15[F["bid"]]), _q(m15[F["ask"]])
    if strike is None:
        return []
    out = []
    for r in ladder_rows:
        if r[F["strike_type"]] not in ("greater", "greater_or_equal") or r[F["floor"]] is None:
            continue
        k, bid_h, ask_h = r[F["floor"]], _q(r[F["bid"]]), _q(r[F["ask"]])
        if k < strike and bid15 is not None and ask_h is not None and 0 < ask_h < 1 and bid15 > ask_h:
            out.append({"kind": "pair_below", "legs": [f"YES {r[F['ticker']]}", f"NO {m15[F['ticker']]}"], **_net(bid15 - ask_h, [ask_h, 1 - bid15]),
                        "size": _min_size(r[F["ask_size"]], m15[F["bid_size"]])})
        if k >= strike and ask15 is not None and bid_h is not None and bid_h > 0 and 0 < ask15 < 1 and bid_h > ask15:
            out.append({"kind": "pair_above", "legs": [f"YES {m15[F['ticker']]}", f"NO {r[F['ticker']]}"], **_net(bid_h - ask15, [ask15, 1 - bid_h]),
                        "size": _min_size(m15[F["ask_size"]], r[F["bid_size"]])})
    return out


def _min_size(a, b):
    return None if a is None or b is None else min(float(a), float(b))


def scan(data_dir: str | Path, *, since_ms: int = 0, until_ms: int | None = None) -> dict:
    # book_top comes from the REST recorder alone, whose records are already in time order: stream them
    snaps = read_lab(data_dir, since_ms=since_ms, until_ms=until_ms, kinds=("book_top",))
    latest_15m: dict[str, tuple[int, list, int]] = {}  # series -> (ts, row, close_ms)
    runs: dict[tuple, dict] = {}  # persistence: the same legs in consecutive snapshots of that event
    counts = defaultdict(int)

    def found(f: dict) -> None:
        counts["findings"] += 1
        key = (f["kind"], tuple(f["legs"]))
        run = runs.get(key)
        if run and f["ts"] - run["last_ts"] <= 90_000:
            run.update(last_ts=f["ts"], seen=run["seen"] + 1, best_net_100=max(run["best_net_100"], f["net_100"]))
        else:
            runs[key] = {"kind": f["kind"], "legs": list(key[1]), "first_ts": f["ts"], "last_ts": f["ts"], "seen": 1, "best_net_100": f["net_100"], "size": f.get("size")}

    for s in snaps:
        counts[s["type"]] += 1
        ts, rows = s["ts"], s["rows"]
        if s["type"] == "15m" and rows:
            latest_15m[s["series"]] = (ts, rows[0], s["close_ms"])
        elif s["type"] == "ladder":
            for f in ladder_findings(rows):
                found({**f, "ts": ts, "event": s["event"]})
            m15_series = s["series"].replace("D", "15M", 1) if s["series"].endswith("D") else None  # KXBTCD -> KXBTC15M
            m15 = latest_15m.get(m15_series) if m15_series else None
            if m15 and m15[2] == s["close_ms"] and abs(ts - m15[0]) <= PAIR_MAX_SKEW_MS:
                counts["pair_checks"] += 1
                for f in pair_findings(m15[1], rows):
                    found({**f, "ts": ts, "event": s["event"], "skew_ms": ts - m15[0]})
        elif s["type"] == "range":
            for f in range_findings(rows):
                found({**f, "ts": ts, "event": s["event"]})
    findings = counts.pop("findings", 0)
    run_list = sorted(runs.values(), key=lambda r: -r["best_net_100"])
    summary = {
        "snapshots": dict(counts), "findings": findings,
        "profitable_after_fees_100": sum(1 for r in run_list if r["best_net_100"] > 0),
        "profitable_and_persistent": sum(1 for r in run_list if r["best_net_100"] > 0 and r["seen"] >= 2),
        "by_kind": {k: sum(1 for r in run_list if r["kind"] == k and r["best_net_100"] > 0) for k in ("ladder", "range_no", "range_yes", "pair_below", "pair_above")},
    }
    return {"summary": summary, "runs": run_list[:200]}


def one_line(s: dict) -> str:
    snaps = s["snapshots"]
    return (f"D scanner: {sum(v for k, v in snaps.items() if k != 'pair_checks')} snapshots ({snaps.get('pair_checks', 0)} 15-min/hourly pair checks); "
            f"{s['profitable_after_fees_100']} contradictions clear both fees at 100 contracts, {s['profitable_and_persistent']} of them in two or more snapshots; "
            f"by kind {s['by_kind']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Locked contradictions between linked Kalshi contracts, after fees")
    parser.add_argument("--data", default="lab/data")
    parser.add_argument("--since-ms", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = scan(args.data, since_ms=args.since_ms)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(one_line(report["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
