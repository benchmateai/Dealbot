"""Check the desk's provisional settlements against Kalshi's official results. Read-only, no key.

    python -m reports.reconcile --log-dir logs/data [--since-ms MS] [--out FILE]

The desk settles a contract from Kalshi's official result when it is out within two minutes of the
close, and otherwise provisionally, from the underlying's last-minute average against the strike.
This looks up each provisionally settled contract once on the public API. One that went the wrong
way moved realized P&L by qty x (official payout - desk payout) on any position the desk held in
it; those rows come first. Prints one line, writes the rows as JSON when --out is given, and exits
3 when a position was settled the wrong way (0 otherwise).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable

from kalshi.api import KalshiApiError, KalshiClient
from logs.writer import read_events

PAUSE_S = 1.1  # the unauthenticated rate limit is about one request a second


def reconcile(log_dir: str | Path, client, *, since_ms: int = 0, sleep: Callable[[float], None] = time.sleep) -> dict:
    qty_by_decision: dict[str, float] = {}
    last_by_ticker: dict[str, dict] = {}
    position_ticker: dict[str, str] = {}
    for e in read_events(log_dir):
        kind, ts = e.get("kind"), e.get("ts")
        if not isinstance(ts, int) or ts < since_ms:
            continue
        if kind == "position_opened":
            pos = e.get("position") or {}
            did = str(e.get("decision_id") or pos.get("decision_id") or "")
            qty_by_decision[did] = float(pos.get("qty") or 0.0)
        elif kind == "settlement" and e.get("ticker"):
            ticker = str(e["ticker"])
            prior = last_by_ticker.get(ticker)
            if prior is None or not prior.get("decision_id"):
                last_by_ticker[ticker] = e  # one record per contract, keeping the one that closed a position
            if e.get("decision_id"):
                position_ticker[str(e["decision_id"])] = ticker
    rows: list[dict] = []
    official_at_the_time = 0
    for ticker, e in sorted(last_by_ticker.items(), key=lambda kv: kv[1]["ts"]):
        if e.get("official"):
            official_at_the_time += 1
            continue
        result = _official_result(client, ticker, sleep)
        desk_payout = float(e.get("payout") or 0.0)
        did = str(e.get("decision_id") or "")
        qty = qty_by_decision.get(did) if did else None
        row = {
            "ticker": ticker, "sym": e.get("sym"), "settled_ms": e.get("settled_ts"), "decision_id": did or None, "qty": qty,
            "desk_payout": desk_payout, "official": result, "status": "pending", "pnl_delta_usd": 0.0,
        }
        if result in ("yes", "no"):
            official_payout = 1.0 if result == "yes" else 0.0
            row["status"] = "confirmed" if official_payout == desk_payout else "wrong"
            if row["status"] == "wrong" and qty:
                row["pnl_delta_usd"] = round(qty * (official_payout - desk_payout), 2)
        rows.append(row)
    rows.sort(key=lambda r: (r["status"] != "wrong" or not r["qty"], r["status"] != "wrong", r["status"] != "pending"))
    wrong_positions = [r for r in rows if r["status"] == "wrong" and r["qty"]]
    summary = {
        "settlements": len(last_by_ticker), "official_at_the_time": official_at_the_time, "provisional": len(rows),
        "confirmed": sum(r["status"] == "confirmed" for r in rows), "wrong": sum(r["status"] == "wrong" for r in rows),
        "pending": sum(r["status"] == "pending" for r in rows), "positions_wrong": len(wrong_positions),
        "pnl_delta_usd": round(sum(r["pnl_delta_usd"] for r in wrong_positions), 2),
    }
    return {"summary": summary, "rows": rows}


def _official_result(client, ticker: str, sleep: Callable[[float], None]) -> str | None:
    delay = 2.0
    for attempt in range(4):
        sleep(PAUSE_S if attempt == 0 else delay)
        try:
            return client.market(ticker).result
        except KalshiApiError as exc:
            if not exc.rate_limited:
                return None
            delay = max(delay * 2, exc.retry_after_s or 0.0)
    return None


def one_line(s: dict) -> str:
    return (
        f"{s['settlements']} contracts settled ({s['official_at_the_time']} from the official result, {s['provisional']} provisionally): "
        f"{s['confirmed']} confirmed, {s['wrong']} wrong, {s['pending']} not final yet; "
        f"positions settled the wrong way: {s['positions_wrong']} (realized P&L off by {s['pnl_delta_usd']:+.2f} USD)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check provisional settlements against Kalshi's official results")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--since-ms", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = reconcile(args.log_dir, KalshiClient(), since_ms=args.since_ms)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(f"reconcile: {one_line(report['summary'])}")
    return 3 if report["summary"]["positions_wrong"] else 0


if __name__ == "__main__":
    sys.exit(main())
