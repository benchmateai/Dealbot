"""The E desk's rows for the money dashboard, merged into its data file, and the E desk's health line.

    python -m dashboard.edesk --lab <lab/data> --merge-into /tmp/dealbot-dashboard/money.json [--variants]
    python -m dashboard.edesk --lab <lab/data> --health

Rows, each with a `table` column like the rest of money.json:
  edesk         one row: the desk's totals (lab/strategies/e_desk.py), its start and the end of its week
  edesk_market  one row per market it quoted or holds: payments, contracts, holding, its value and P&L, status
  edesk_equity  its equity every 10 minutes
  edesk_variant one row per variant replayed beside it (with --variants; the morning report adds them)
Before the desk starts there is only the edesk row, with started false. Old edesk rows in the file are
replaced; the desk v2 rows are left as they are.

--health judges the recording the desk runs on, for the watchdog once the E desk is the round
(ops/round.txt): ALERT when the live feed has written no E book for STALE_ALERT_S, WARN past STALE_WARN_S.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from lab.store import read_lab
from lab.strategies.e_desk import START_MS, WEEK_MS, compare, evaluate

STALE_WARN_S = 70 * 60
STALE_ALERT_S = 150 * 60


def rows(report: dict, *, now_ms: int) -> list[dict]:
    s = report["summary"]
    flat = {k: v for k, v in s.items() if v is None or isinstance(v, (int, float, str, bool))}
    day = max(1, min(7, (now_ms - s["start_ms"]) // 86_400_000 + 1)) if now_ms >= s["start_ms"] else 0
    out = [{"table": "edesk", "id": "edesk", **flat, "ends_ms": s["start_ms"] + WEEK_MS, "week_day": day, "updated_ms": now_ms}]
    for m in report.get("markets") or []:
        out.append({"table": "edesk_market", "id": m["ticker"], **m})
    for ts, eq in report.get("equity") or []:
        out.append({"table": "edesk_equity", "id": f"q{ts}", "t_ms": ts, "equity_usd": eq})
    for name, v in (report.get("variants") or {}).items():
        out.append({"table": "edesk_variant", "id": name, **{k: x for k, x in v.items() if x is None or isinstance(x, (int, float, str, bool))}})
    return out


def merge(path: str | Path, new: list[dict]) -> list[dict]:
    """money.json's rows with any old E desk rows replaced by `new`."""
    p = Path(path)
    old = json.loads(p.read_text()) if p.exists() else []
    kept = [r for r in old if not str(r.get("table", "")).startswith("edesk")]
    merged = kept + new
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(merged, separators=(",", ":")))
    return merged


def health(lab_dir: str | Path, *, now_ms: int) -> tuple[str, int]:
    """(line, exit code): how fresh the live feed's E books are, and the desk's money."""
    newest = None
    for r in read_lab(lab_dir, since_ms=now_ms - 6 * 3_600_000, kinds=["book"]):
        if "E" in (r.get("sets") or [r.get("set")]):
            newest = r["ts"] if newest is None else max(newest, r["ts"])
    s = evaluate(lab_dir, since_ms=START_MS)["summary"] if now_ms >= START_MS else None
    money = "" if not s or not s["started"] else f" · E desk net {s['net_usd']:+.2f} (payments {s['payable_usd']:.2f}, fills marked {s['fills_marked_usd']:+.2f}), equity {s['equity_usd']:,.2f}"
    if newest is None:
        return f"health: ALERT · the live feed has written no E book in 6 hours{money}", 3
    age = (now_ms - newest) / 1000
    if age >= STALE_ALERT_S:
        return f"health: ALERT · the live feed's newest E book is {age / 60:.0f} minutes old{money}", 3
    if age >= STALE_WARN_S:
        return f"health: WARN · the live feed's newest E book is {age / 60:.0f} minutes old{money}", 0
    return f"health: OK · newest E book {age / 60:.0f} minutes old{money}", 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The E desk's dashboard rows, or its health line")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--merge-into", default=None, help="the money dashboard's data file (money.json)")
    parser.add_argument("--variants", action="store_true", help="replay the variants beside the desk too (slower)")
    parser.add_argument("--health", action="store_true")
    parser.add_argument("--since-ms", type=int, default=START_MS)
    args = parser.parse_args(argv)
    now = int(time.time() * 1000)
    if args.health:
        line, code = health(args.lab, now_ms=now)
        print(line)
        return code
    report = compare(args.lab, since_ms=args.since_ms) if args.variants else evaluate(args.lab, since_ms=args.since_ms)
    new = rows(report, now_ms=now)
    if args.merge_into:
        merge(args.merge_into, new)
    s = report["summary"]
    print(f"{'merged into ' + args.merge_into + ': ' if args.merge_into else ''}{len(new)} rows; "
          + (f"E desk net {s['net_usd']:+.2f} over {s['hours']:.1f} h" if s["started"] else
             f"E desk starts {time.strftime('%Y-%m-%d %H:%MZ', time.gmtime(s['start_ms'] / 1000))}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
