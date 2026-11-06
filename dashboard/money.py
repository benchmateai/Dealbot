"""The numbers behind the phone dashboard, as one JSON file of rows.

    python -m dashboard.money --log-dir logs/data --out /tmp/dealbot-dashboard/money.json

Every row carries a `table` column, so one file feeds the whole page:
  summary  one row: bankroll, equity, net and realized P&L after fees, today's change, trade counts and
           win rate, fees, Jev calls and their cost, the best and worst trade, and the run's clock
  trade    one row per position, newest first, written the way a Kalshi user reads a bet: a short YES
           position is "NO at 21c", its stake is what the bet cost, its result won, lost, sold or open
  equity   the equity curve, the last reading in each 10-minute slot
  day      one row per UTC day: change in equity, trades closed, wins, fees
  shadow   (v1 only) one row per strategy in reports.shadow (the live desk and the shadow rules), counted
           only over bets placed after the rules were registered, with the rules' own numbers
  previous (v2 only) one row: the first desk's final result, from the measured week's start to the switch
  rule     (v2 only) one row per paper rule in reports.shadow_v2 (v2 as traded, the owner's two rules of
           2026-11-05 and a third of 2026-11-06), each over v2's bets opened from its own registration; the
           third also carries v2's result on exactly the same bets (desk_same_*)
Numbers come straight from the desk's own log; nothing here trades or decides. Only events from
`since_ms` on count: by default desk v2's start once it has taken over (reports.runs), else WEEK_START_MS,
the start of the first measured week. The bankroll is the first equity reading from then, and a position
carried in from before shows in equity, not as a bet.
A fill belongs to its own decision's position when that is a position (the opening fill and the
settlement), otherwise to the position open on that contract (an exit is its own decision).
"""

from __future__ import annotations

import argparse
import json
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from logs.writer import read_events
from reports.runs import WEEK1_START_MS, v2_start_ms

JEV_USD_PER_INPUT_TOKEN = 0.042 / 1_000_000  # TypeSafe's price per input token; output tokens are free
SLOT_MS = 600_000
WEEK_START_MS = WEEK1_START_MS  # 2026-11-03T08:25:00Z, the first desk's measured week (see reports/runs.py)
FILL_GRACE_MS = 60_000  # a fill is stamped when it filled, a few seconds before its decision's record
WEEK_MS = 7 * 86_400_000
MARKETS = {"KXETH15M": "ETH 15-min", "KXBTC15M": "BTC 15-min"}


def _day(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def build(log_dir: str | Path, *, start_cash: float = 10_000.0, now_ms: int | None = None, since_ms: int | None = None,
          until_ms: int | None = None, v2_ms: int | None | bool = False) -> list[dict]:
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    if v2_ms is False:
        v2_ms = v2_start_ms(log_dir)
    if since_ms is None:
        since_ms = v2_ms if v2_ms is not None else WEEK_START_MS
    on_v2 = v2_ms is not None and since_ms >= v2_ms and until_ms is None  # until_ms set: a closed window (the first desk's)
    trades: OrderedDict[str, dict] = OrderedDict()
    fills: dict[str, list[dict]] = {}  # by position; an opening fill waits here under its own decision id
    open_on: dict[str, str] = {}  # contract series -> the decision id of the position open on it
    closes: dict[str, dict] = {}
    first_eq = None
    equity: OrderedDict[int, tuple[int, float]] = OrderedDict()
    day_first: dict[str, float] = {}
    day_last: dict[str, float] = {}
    jev_calls = jev_tokens = 0
    last_eq = None
    for e in read_events(log_dir):
        kind, ts = e.get("kind"), e.get("ts")
        if not isinstance(ts, int) or ts < since_ms - (FILL_GRACE_MS if kind == "fill" else 0):
            continue
        if until_ms is not None and ts >= until_ms:
            continue
        if kind == "heartbeat" and isinstance(e.get("equity_usd"), (int, float)):
            eq = float(e["equity_usd"])
            first_eq = eq if first_eq is None else first_eq
            last_eq = eq
            equity[ts - ts % SLOT_MS] = (ts, eq)
            day = _day(ts)
            day_first.setdefault(day, eq)
            day_last[day] = eq
        elif kind == "answer":
            jev_calls += 1
            usage = e.get("usage") or {}
            jev_tokens += int(usage.get("input_tokens") or 0)
        elif kind == "position_opened":
            pos = e.get("position") or {}
            did = str(e.get("decision_id") or pos.get("decision_id") or "")
            qty = float(pos.get("qty") or 0.0)
            yes_price = float(pos.get("entry_price") or 0.0)
            long = qty > 0
            price = yes_price if long else 1.0 - yes_price
            trades[did] = {
                "table": "trade", "id": did, "opened_ms": ts, "sym": e.get("sym"), "market": MARKETS.get(str(e.get("sym")), str(e.get("sym"))),
                "bet": "YES" if long else "NO", "contracts": abs(qty), "price_cents": round(price * 100, 1), "stake_usd": round(abs(qty) * price, 2),
                "fees_usd": 0.0, "gross_usd": 0.0, "result": "open", "pnl_usd": None, "closed_ms": None, "official": None,
            }
            open_on[str(e.get("sym"))] = did
        elif kind == "fill":
            did, sym = str(e.get("decision_id") or ""), str(e.get("sym") or "")
            owner = did if did in trades else open_on.get(sym, did)
            fills.setdefault(owner, []).append(e)
        elif kind == "settlement" and e.get("decision_id"):
            t = trades.get(str(e["decision_id"]))
            if t is not None:
                t["official"] = bool(e.get("official"))
        elif kind == "position_closed" and e.get("decision_id"):
            closes[str(e["decision_id"])] = e
            if open_on.get(str(e.get("sym"))) == str(e["decision_id"]):
                del open_on[str(e.get("sym"))]
    for did, t in trades.items():
        for f in fills.get(did, []):
            t["fees_usd"] = round(t["fees_usd"] + float(f.get("fee_usd") or 0.0) + float(f.get("gas_usd") or 0.0), 4)
            t["gross_usd"] = round(t["gross_usd"] + float(f.get("realized_pnl_usd") or 0.0), 4)
        close = closes.get(did)
        if close is None:
            continue
        t["closed_ms"] = close["ts"]
        t["pnl_usd"] = round(t["gross_usd"] - t["fees_usd"], 2)
        if close.get("settled"):
            won = (float(close.get("payout") or 0.0) >= 0.5) == (t["bet"] == "YES")
            t["result"] = "won" if won else "lost"
        else:
            t["result"] = "sold"
    closed = [t for t in trades.values() if t["result"] != "open"]
    wins = sum(1 for t in closed if (t["pnl_usd"] or 0) > 0)
    fees = round(sum(t["fees_usd"] for t in trades.values()), 2)
    realized = round(sum(t["pnl_usd"] or 0.0 for t in closed), 2)
    start = first_eq if first_eq is not None else start_cash
    equity_now = last_eq if last_eq is not None else start
    today = _day(now)
    best = max(closed, key=lambda t: t["pnl_usd"], default=None)
    worst = min(closed, key=lambda t: t["pnl_usd"], default=None)
    summary = {
        "table": "summary", "id": "summary",
        "start_usd": round(start, 2), "equity_usd": round(equity_now, 2), "net_pnl_usd": round(equity_now - start, 2),
        "realized_pnl_usd": realized, "today_pnl_usd": round(day_last.get(today, equity_now) - day_first.get(today, equity_now), 2),
        "trades_closed": len(closed), "trades_open": len(trades) - len(closed), "wins": wins, "losses": len(closed) - wins,
        "win_rate": round(wins / len(closed), 4) if closed else None, "fees_usd": fees,
        "jev_calls": jev_calls, "jev_cost_usd": round(jev_tokens * JEV_USD_PER_INPUT_TOKEN, 4),
        "best_pnl_usd": None if best is None else best["pnl_usd"], "worst_pnl_usd": None if worst is None else worst["pnl_usd"],
        "updated_ms": now, "week_started_ms": since_ms, "week_ends_ms": since_ms + WEEK_MS,
        "week_day": max(1, min(7, (now - since_ms) // 86_400_000 + 1)), "desk": "v2" if on_v2 else "v1",
    }
    rows: list[dict] = [summary]
    for t in sorted(trades.values(), key=lambda t: t["opened_ms"], reverse=True):
        rows.append({k: v for k, v in t.items() if k != "gross_usd"})
    for slot, (ts, eq) in equity.items():
        rows.append({"table": "equity", "id": f"e{slot}", "t_ms": ts, "equity_usd": round(eq, 2)})
    if on_v2:
        v1 = build(log_dir, start_cash=start_cash, now_ms=now, since_ms=WEEK_START_MS, until_ms=v2_ms, v2_ms=v2_ms)[0]
        rows.append({"table": "previous", "id": "v1", "from_ms": WEEK_START_MS, "to_ms": v2_ms,
                     **{k: v1[k] for k in ("start_usd", "equity_usd", "net_pnl_usd", "realized_pnl_usd", "trades_closed", "trades_open", "wins", "losses", "win_rate", "fees_usd", "jev_calls")}})
        from reports.shadow_v2 import evaluate as v2_rules  # here: reports.shadow_v2 imports this module through reports.shadow

        report = v2_rules(log_dir)
        for name, st in report.get("strategies", {}).items():
            t = st["test"]
            row = {"table": "rule", "id": name, "label": st["label"], "registered_ms": st["registered_ms"], "test_pnl_usd": t["pnl_usd"],
                   "test_trades": t["trades"], "test_won": t["won"], "test_skipped": t["skipped"], "test_open": t["open"]}
            if "desk_same" in st:  # v2 on exactly this rule's bets
                row.update({"desk_same_pnl_usd": st["desk_same"]["pnl_usd"], "desk_same_trades": st["desk_same"]["trades"], "desk_same_won": st["desk_same"]["won"]})
            rows.append(row)
    from reports.shadow import CAP, EXIT_BEFORE_S, LATE_STOP_S, REGISTERED_MS, evaluate  # here: reports.shadow imports this module

    shadow_strategies = {} if on_v2 or until_ms is not None else evaluate(log_dir, since_ms=since_ms, until_ms=v2_ms).get("strategies", {})
    for name, st in shadow_strategies.items():
        test = st["test"]
        row = {
            "table": "shadow", "id": name, "test_pnl_usd": test["pnl_usd"], "test_trades": test["trades"], "test_won": test["won"],
            "test_skipped": test["skipped"], "test_open": test["open"], "in_sample_pnl_usd": st["in_sample"]["pnl_usd"],
            "cap_points": round(CAP * 100), "exit_minutes": EXIT_BEFORE_S // 60, "late_seconds": LATE_STOP_S,
            "registered_ms": st.get("registered_ms", REGISTERED_MS),
        }
        if "desk_same" in st:  # the desk on exactly this rule's bets
            row.update({"desk_same_pnl_usd": st["desk_same"]["pnl_usd"], "desk_same_trades": st["desk_same"]["trades"], "desk_same_won": st["desk_same"]["won"]})
        rows.append(row)
    for day in sorted(day_last):
        closed_today = [t for t in closed if _day(t["closed_ms"]) == day]
        rows.append({
            "table": "day", "id": day, "day": day, "pnl_usd": round(day_last[day] - day_first[day], 2),
            "trades": len(closed_today), "wins": sum(1 for t in closed_today if (t["pnl_usd"] or 0) > 0),
            "fees_usd": round(sum(t["fees_usd"] for t in closed_today), 2),
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the phone dashboard's data file")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--out", default="/tmp/dealbot-dashboard/money.json")
    parser.add_argument("--start-cash", type=float, default=10_000.0, help="bankroll when the log has no equity reading yet")
    parser.add_argument("--since-ms", type=int, default=None, help="start of the measured window (default: desk v2's start, or the first measured week)")
    args = parser.parse_args(argv)
    rows = build(args.log_dir, start_cash=args.start_cash, since_ms=args.since_ms)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, separators=(",", ":")))
    s = rows[0]
    print(f"wrote {out}: equity {s['equity_usd']:.2f}, net {s['net_pnl_usd']:+.2f}, {s['trades_closed']} closed and {s['trades_open']} open trades, {sum(1 for r in rows if r['table'] == 'equity')} equity points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
