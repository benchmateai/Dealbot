"""The Bitcoin options test's rows for the money dashboard, merged into its data file.

    python -m dashboard.options --lab <lab/data> --merge-into /tmp/dealbot-dashboard/money.json

Rows, each with a `table` column like the rest of money.json (lab/strategies/btc_options.py makes the numbers):
  opt_summary   one row: when it started and was last read, how much it priced, and each venue's median gap to
                the options' price (all, the year-end ranges, the touch markets) and how often an edge of a
                cent or more was there
  opt_variant   one row per hurdle (1, 2 and 3 cents): its paper buys, what they cost, fees, the money's cost,
                and their worth at the options' price and at the venues' bids, by venue
  opt_market    one row per Bitcoin pair priced: a plain label, the options' price and both venues' mids
  opt_position  one row per paper buy of the 2-cent variant
Old opt_* rows in the file are replaced; every other row is left as it is.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from lab.strategies.btc_options import REGISTERED_MS, evaluate

SHOWN_VARIANT = "hurdle_2c"


def _usd(k: int) -> str:
    return f"${k // 1000}k" if k % 1000 == 0 else f"${k:,}"


def label(pair: str, model: dict | None) -> str:
    """A pair's market in a few plain words: 'Year end $70k-75k', 'How high: $100k', '$100k by Nov 30'."""
    m = model or {}
    kind = m.get("kind")
    if kind == "range":
        return f"Year end {_usd(int(m['lo']))}–{_usd(int(m['hi']))[1:]}"
    if kind == "below":
        return f"Year end under {_usd(int(m['k']))}"
    if kind == "above":
        return f"Year end {_usd(int(m['k']))}+"
    if pair.startswith("btc-high-"):
        return f"How high: {_usd(int(m['k']))}"
    if pair.startswith("btc-low-"):
        return f"How low: {_usd(int(m['k']))}"
    if kind in ("touch_up", "touch_down"):
        by = "Nov 30" if str(m.get("by", "")).startswith("2026-12-01") else "Dec 31"
        return f"Hits {_usd(int(m['k']))} by {by}"
    return pair


def rows(report: dict, *, now_ms: int, models: dict[str, dict] | None = None) -> list[dict]:
    s, d = report["summary"], report["deviation"]
    models = models or {}
    out = [{"table": "opt_summary", "id": "options", "started": bool(s["surfaces"]), "registered_ms": report["registered_ms"],
            "since_ms": report["since_ms"], "end_ms": report["end_ms"] or None, "updated_ms": now_ms, **s,
            **{f"{v}_{part}_{field}": d[v][part][field] for v in ("kalshi", "poly") for part in ("all", "terminal", "touch")
               for field in ("median_gap_cents", "mean_signed_cents", "hours")},
            "kalshi_edge_share": d["kalshi"]["edge_1c_share"], "poly_edge_share": d["poly"]["edge_1c_share"]}]
    for name, v in report["variants"].items():
        row = {"table": "opt_variant", "id": name, "hurdle_cents": int(name.split("_")[1].rstrip("c")),
               **{k: v[k] for k in ("positions", "contracts", "cost_usd", "fees_usd", "carry_usd", "pnl_at_options_usd", "pnl_at_bids_usd", "settled")}}
        for venue in ("kalshi", "poly"):
            row[f"{venue}_positions"] = v["by_venue"][venue]["positions"]
            row[f"{venue}_pnl_at_bids_usd"] = v["by_venue"][venue]["pnl_at_bids_usd"]
        for h, x in v["drift"].items():
            row[f"drift_{h}_positions"], row[f"drift_{h}_entry_cents"], row[f"drift_{h}_after_cents"] = x["positions"], x["gap_at_entry_cents"], x["gap_after_cents"]
        out.append(row)
    for m in report["latest"]:
        out.append({"table": "opt_market", "id": m["pair"], "label": label(m["pair"], models.get(m["pair"])), "group": m["group"],
                    "fair": m["fair"], "kalshi_mid": m["kalshi_mid"], "poly_mid": m["poly_mid"], "ts": m["ts"]})
    shown = report["variants"].get(SHOWN_VARIANT) or {"entries": []}
    for e in shown["entries"]:
        pnl_fair = e["n"] * (e["worth_fair"] - e["price"]) - e.get("fee", 0.0)
        out.append({"table": "opt_position", "id": f"{e['pair']}:{e['venue']}:{e['side']}", "label": label(e["pair"], models.get(e["pair"])),
                    "venue": e["venue"], "side": e["side"], "price": e["price"], "contracts": e["n"], "opened_ms": e["ts"],
                    "worth_fair": round(e["worth_fair"], 4), "worth_bid": round(e["worth_bid"], 4), "payout": e["payout"],
                    "pnl_at_options_usd": round(pnl_fair, 2)})
    return out


def merge(path: str | Path, new: list[dict]) -> list[dict]:
    """money.json's rows with any old options rows replaced by `new`."""
    p = Path(path)
    old = json.loads(p.read_text()) if p.exists() else []
    kept = [r for r in old if not str(r.get("table", "")).startswith("opt_")]
    merged = kept + new
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, separators=(",", ":")))
    return merged


def main(argv: list[str] | None = None) -> int:
    from lab.store import read_lab

    parser = argparse.ArgumentParser(description="The Bitcoin options test's rows for the money dashboard")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--merge-into", default=None, help="the money dashboard's data file (money.json)")
    parser.add_argument("--since-ms", type=int, default=REGISTERED_MS)
    args = parser.parse_args(argv)
    report = evaluate(args.lab, since_ms=args.since_ms)
    models = {}
    for r in read_lab(args.lab, since_ms=max(0, args.since_ms - 4 * 3_600_000), kinds=("gap_pair",), streams=("gap",)):
        if r.get("model"):
            models[r["pair"]] = r["model"]
    new = rows(report, now_ms=int(time.time() * 1000), models=models)
    if args.merge_into:
        merge(args.merge_into, new)
    s = report["summary"]
    shown = report["variants"][SHOWN_VARIANT]
    print(f"{'merged into ' + args.merge_into + ': ' if args.merge_into else ''}{len(new)} rows; "
          + (f"{s['pairs_priced']} Bitcoin pairs priced on {s['surfaces']} option surfaces; 2c hurdle: {shown['positions']} paper buys, "
             f"{shown['pnl_at_options_usd']:+.2f} at the options' price" if s["surfaces"] else "no option surface recorded yet"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
