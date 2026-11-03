"""The paper run's health in one line, for the hourly watchdog and the morning report. Read-only.

    python -m reports.health --log-dir <copy of the run branch>/logs/data --commit-ms <newest run commit, ms>

Prints "OK ...", "WARN ..." or "ALERT ..." with the reasons and a few numbers, and exits 3 on ALERT
(0 otherwise) so a caller can branch on it.

ALERT means someone should look now: nothing pushed to the run branch for over 75 minutes (the
chunk script publishes every 30), the desk reporting a fault, no Jev calls for two hours, more than
a fifth of the last hour's Jev calls failing, a position still open 35 minutes after it was taken
(a 15-minute contract settles within about 17), the day's loss at the risk gate's limit, or the same
decision logged twice in the last two hours (two desks writing to one log, as on 2026-11-03).
WARN is for the morning report: an hour without Jev calls, positions settled provisionally (worth
reconciling), most feed polls rate-limited, a day's loss past half the limit, or the bankroll down 2%.
The windows end at the newest heartbeat, so a stale log reads as stale, not as quiet.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from logs.writer import read_events

MINUTE_MS = 60_000
HOUR_MS = 60 * MINUTE_MS
STALE_COMMIT_MIN = 75
STUCK_POSITION_MIN = 35
FAIL_SHARE_ALERT = 0.2
RATE_LIMIT_SHARE_WARN = 0.3
DAILY_LOSS_LIMIT_USD = 100.0  # desk/config.py's default; the risk gate stops new exposure there
BANKROLL_WARN_FRAC = 0.02
START_CASH = 10_000.0


def _judge_failure(e: dict) -> bool:
    check = str(e.get("check") or "")
    return e.get("kind") == "rejection" and (check.startswith("jev_") or check == "battery_fault")


def check(log_dir: str | Path, *, commit_ms: int | None, now_ms: int | None = None,
          daily_loss_limit_usd: float = DAILY_LOSS_LIMIT_USD, start_cash: float = START_CASH) -> dict:
    now = now_ms if now_ms is not None else int(time.time() * 1000)
    events = [e for e in read_events(log_dir) if isinstance(e.get("ts"), int)]
    heartbeats = [e for e in events if e.get("kind") == "heartbeat"]
    alerts: list[str] = []
    warns: list[str] = []
    if commit_ms is not None and now - commit_ms > STALE_COMMIT_MIN * MINUTE_MS:
        alerts.append(f"nothing pushed to the run branch for {(now - commit_ms) // MINUTE_MS} min")
    if not heartbeats:
        alerts.append("no heartbeat in the log")
        return _verdict(alerts, warns, {})
    last = max(heartbeats, key=lambda e: e["ts"])
    end = last["ts"]
    first_ts = min(e["ts"] for e in events)

    def window(ms: int) -> list[dict]:
        return [e for e in events if end - ms < e["ts"] <= end]

    hour, two_hours = window(HOUR_MS), window(2 * HOUR_MS)
    calls_1h = sum(1 for e in hour if e.get("kind") == "answer")
    calls_2h = sum(1 for e in two_hours if e.get("kind") == "answer")
    failures_1h = sum(1 for e in hour if _judge_failure(e))
    entries_1h = sum(1 for e in hour if e.get("kind") == "decision" and e.get("executed") and str(e.get("action", "")).startswith("enter"))
    settled_1h = sum(1 for e in hour if e.get("kind") == "position_closed")
    provisional_24h = sum(1 for e in window(24 * HOUR_MS) if e.get("kind") == "settlement" and e.get("decision_id") and not e.get("official"))
    seen: dict[str, int] = {}
    for e in two_hours:
        if e.get("kind") == "decision" and e.get("decision_id"):
            seen[str(e["decision_id"])] = seen.get(str(e["decision_id"]), 0) + 1
    doubled = sum(1 for n in seen.values() if n > 1)

    if doubled:
        alerts.append(f"{doubled} decisions in the last two hours were logged more than once: more than one desk is writing to the log")
    if last.get("fault"):
        alerts.append(f"the desk reports a fault: {last['fault']}")
    position = last.get("position") or None
    if position and isinstance(position.get("entry_ts"), int) and end - position["entry_ts"] > STUCK_POSITION_MIN * MINUTE_MS:
        alerts.append(f"{position.get('sym')} position open {(end - position['entry_ts']) // MINUTE_MS} min; a 15-minute contract settles within about 17")
    if end - first_ts >= 2 * HOUR_MS - 5 * MINUTE_MS and calls_2h == 0:
        alerts.append("no Jev calls in two hours")
    elif end - first_ts >= HOUR_MS - 5 * MINUTE_MS and calls_1h == 0:
        warns.append("no Jev calls in the last hour")
    asked = calls_1h + failures_1h
    if asked >= 5 and failures_1h / asked > FAIL_SHARE_ALERT:
        alerts.append(f"{failures_1h} of {asked} Jev calls failed in the last hour")
    day_pnl = float(last.get("day_pnl_usd") or 0.0)
    if day_pnl <= -daily_loss_limit_usd:
        alerts.append(f"day P&L {day_pnl:+.2f} is at the {daily_loss_limit_usd:.0f} USD daily loss limit; the desk only reduces exposure until 00:00 UTC")
    elif day_pnl <= -daily_loss_limit_usd / 2:
        warns.append(f"day P&L {day_pnl:+.2f}, past half the {daily_loss_limit_usd:.0f} USD daily loss limit")
    equity = float(last.get("equity_usd") or start_cash)
    if equity < start_cash * (1 - BANKROLL_WARN_FRAC):
        warns.append(f"equity {equity:,.2f} is more than {BANKROLL_WARN_FRAC:.0%} below the {start_cash:,.0f} start")
    if provisional_24h:
        warns.append(f"{provisional_24h} position settlement(s) in 24 h were provisional; run reports.reconcile")
    feed = last.get("feed") if isinstance(last.get("feed"), dict) else {}
    polls, limited = int(feed.get("polls") or 0), int(feed.get("rate_limits") or 0)
    if polls >= 60 and limited / polls > RATE_LIMIT_SHARE_WARN:
        warns.append(f"{limited} of {polls} feed polls rate-limited since the desk started")
    stats = {
        "log_end_ms": end, "commit_age_min": None if commit_ms is None else (now - commit_ms) // MINUTE_MS,
        "jev_calls_1h": calls_1h, "jev_failures_1h": failures_1h, "entries_1h": entries_1h, "settled_1h": settled_1h,
        "equity_usd": round(equity, 2), "net_usd": round(equity - start_cash, 2), "day_pnl_usd": round(day_pnl, 2),
        "open_position": None if not position else f"{'YES' if float(position.get('qty') or 0) > 0 else 'NO'} {position.get('sym')}",
    }
    return _verdict(alerts, warns, stats)


def _verdict(alerts: list[str], warns: list[str], stats: dict) -> dict:
    status = "ALERT" if alerts else "WARN" if warns else "OK"
    parts = [status] + alerts + warns
    if stats:
        age = "" if stats["commit_age_min"] is None else f"pushed {stats['commit_age_min']} min ago, "
        parts.append(
            f"{age}last hour: {stats['jev_calls_1h']} Jev calls, {stats['entries_1h']} entries, {stats['settled_1h']} closed; "
            f"equity {stats['equity_usd']:,.2f} ({stats['net_usd']:+.2f} overall, {stats['day_pnl_usd']:+.2f} today)"
            + (f"; open: {stats['open_position']}" if stats["open_position"] else "")
        )
    return {"status": status, "alerts": alerts, "warnings": warns, "stats": stats, "line": " · ".join(parts)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-line health verdict on the paper run")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--commit-ms", type=int, default=None, help="time of the newest run-branch commit, in ms")
    args = parser.parse_args(argv)
    result = check(args.log_dir, commit_ms=args.commit_ms)
    print(f"health: {result['line']}")
    return 3 if result["status"] == "ALERT" else 0


if __name__ == "__main__":
    sys.exit(main())
