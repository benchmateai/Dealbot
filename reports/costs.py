"""What the team's sessions cost to run, against each one's daily budget and the desk's paper result.

Only the coordinator can read the costs: get_session reports each session's cumulative usage cost
(usage.cost_usd). It writes them to a snapshot file,
  {"at": "<ISO time>", "sessions": {"<role>": {"id": "<session id>", "cost_usd": <number>, "created_at": "<ISO>"}}}
with the roles of ops/budgets.json (coordinator, runner, watchdog, analyst, lab_rest, lab_ws, lab_gap), and this
compares it with the last snapshot in the ledger (one JSON line per morning report):
  spent      a session's cost since the last snapshot; with no last snapshot, the average a day since each
             session began. When a teammate was replaced since the last snapshot its new session counts in full,
             and its old one counts for what it spent after the snapshot: the coordinator reads the old session
             too and adds it under "retired": {"<old session id>": {"role": "<role>", "cost_usd": <number>}} (each
             old one, if it was replaced more than once: any but the one in the last snapshot counts in full, once);
             the line says when a replaced session's last spend is missing
  budget     its daily budget, times the days the window spans when that is more than one, so a short window
             (the supervisor's checks, hours after the morning's snapshot) is held to a whole day's budget: a
             teammate over it before the next morning is a runaway to look into
--record appends the snapshot to the ledger (the morning report), with every replaced session's cost so far
under "retired_all", so the total since each session began keeps them; without it the ledger is only read.

    python -m reports.costs --snapshot FILE --ledger FILE [--budgets ops/budgets.json] [--record] [--paper-24h USD]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BUDGETS = Path(__file__).resolve().parent.parent / "ops" / "budgets.json"
ORDER = ("coordinator", "runner", "watchdog", "analyst", "lab_rest", "lab_ws", "lab_gap")
NAMES = {"coordinator": "coordinator", "runner": "runner", "watchdog": "watchdog", "analyst": "analyst",
         "lab_rest": "REST lab runner", "lab_ws": "live-feed lab runner", "lab_gap": "gap runner"}


def _ms(text: str) -> int:
    return int(datetime.fromisoformat(str(text).replace("Z", "+00:00")).timestamp() * 1000)


def last_entry(ledger: str | Path) -> dict | None:
    p = Path(ledger)
    if not p.exists():
        return None
    last = None
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    return last


def compare(snapshot: dict, previous: dict | None, budgets: dict[str, float]) -> dict:
    now = _ms(snapshot["at"])
    window_h = (now - _ms(previous["at"])) / 3.6e6 if previous else None
    retired = snapshot.get("retired") or {}
    missing = []
    rows = []
    for role in sorted(snapshot["sessions"], key=lambda r: (ORDER.index(r) if r in ORDER else len(ORDER), r)):
        s = snapshot["sessions"][role]
        cost = float(s["cost_usd"])
        before = (previous or {}).get("sessions", {}).get(role) if previous else None
        if previous is None:
            days = max(1 / 24, (now - _ms(s["created_at"])) / 86_400_000)
            spent, per_day, basis = cost, cost / days, "average"
        elif before and before.get("id") == s.get("id") and float(before["cost_usd"]) <= cost:
            spent, basis = cost - float(before["cost_usd"]), "since"
            per_day = spent / window_h * 24 if window_h else None
        else:  # a session replaced (or new) since the last snapshot: all of its cost falls in the window
            spent, basis = cost, "replaced"
            if before is not None:  # and the old one's, for what it spent after the snapshot
                old = retired.get(before.get("id"))
                if old is None:
                    missing.append(role)
                else:
                    spent += max(0.0, float(old["cost_usd"]) - float(before["cost_usd"]))
            # any other session it had in between counts in full, once: one the ledger already holds was counted before
            known = previous.get("retired_all") or {}
            spent += sum(float(v["cost_usd"]) for sid, v in retired.items()
                         if v.get("role") == role and sid != (before or {}).get("id") and sid not in known)
            per_day = spent / window_h * 24 if window_h else None
        budget = budgets.get(role)
        limit = None if budget is None else (budget if previous is None else budget * max(1.0, window_h / 24))
        over = limit is not None and (per_day if previous is None else spent) > limit
        rows.append({"role": role, "spent_usd": round(spent, 2), "per_day_usd": None if per_day is None else round(per_day, 2),
                     "budget_usd": budget, "limit_usd": None if limit is None else round(limit, 2), "over": over, "basis": basis,
                     "cost_usd": round(cost, 2)})
    team_spent = sum(r["spent_usd"] for r in rows) if previous else None
    team_per_day = sum(r["per_day_usd"] or 0 for r in rows)
    team_budget = sum(b for r, b in budgets.items() if r in snapshot["sessions"])
    return {"window_hours": None if window_h is None else round(window_h, 1), "rows": rows, "team_spent_usd": None if team_spent is None else round(team_spent, 2),
            "team_per_day_usd": round(team_per_day, 2), "team_budget_usd": team_budget, "over": [r["role"] for r in rows if r["over"]],
            "total_usd": round(sum(r["cost_usd"] for r in rows) + sum(retired_all(snapshot, previous).values()), 2), "missing": missing}


def retired_all(snapshot: dict, previous: dict | None) -> dict[str, float]:
    """Every replaced session's cost so far: the ledger's last count carried forward with this snapshot's."""
    out = dict((previous or {}).get("retired_all") or {})
    for sid, v in (snapshot.get("retired") or {}).items():
        out[sid] = max(out.get(sid, 0.0), float(v["cost_usd"]))
    return out


def line(c: dict, paper_24h: float | None = None) -> str:
    def who(r: dict) -> str:
        amount = r["per_day_usd"] if c["window_hours"] is None else r["spent_usd"]
        budget = "" if r["limit_usd"] is None else f" of ${r['limit_usd']:,.2f}"
        flag = " OVER" if r["over"] else ""
        return f"{NAMES.get(r['role'], r['role'])} ${amount:,.2f}{budget}{flag}"
    parts = ", ".join(who(r) for r in c["rows"])
    if c["window_hours"] is None:
        head = (f"costs (first look, the average a day since each session began): the team about ${c['team_per_day_usd']:,.2f} a day "
                f"(budget ${c['team_budget_usd']:,.2f}); {parts}")
    else:
        head = (f"costs: the team's usage came to ${c['team_spent_usd']:,.2f} over the last {c['window_hours']:.1f} hours "
                f"(budget ${c['team_budget_usd'] * max(1.0, c['window_hours'] / 24):,.2f}); {parts}")
    tail = f"; over budget: {', '.join(NAMES.get(r, r) for r in c['over'])}" if c["over"] else "; nobody over budget"
    if c.get("missing"):
        tail += (f"; not counted: what the replaced session of the {', '.join(NAMES.get(r, r) for r in c['missing'])} spent after the "
                 "last snapshot (read it with get_session and add it under retired)")
    paper = "" if paper_24h is None else f"; the desk made {paper_24h:+,.2f} USD on paper in the last 24 hours"
    return f"{head}{tail}{paper}; ${c['total_usd']:,.2f} in all since each session began"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The team's running cost against its budgets")
    parser.add_argument("--snapshot", required=True, help="this look's costs, as the coordinator read them with get_session")
    parser.add_argument("--ledger", required=True, help="the JSON-lines ledger of the morning snapshots")
    parser.add_argument("--budgets", default=str(BUDGETS))
    parser.add_argument("--record", action="store_true", help="append the snapshot to the ledger (the morning report)")
    parser.add_argument("--paper-24h", type=float, default=None, help="the desk's paper P&L over the last 24 hours, for the comparison")
    args = parser.parse_args(argv)
    snapshot = json.loads(Path(args.snapshot).read_text())
    budgets = {k: float(v) for k, v in json.loads(Path(args.budgets).read_text())["daily_usd"].items()}
    previous = last_entry(args.ledger)
    c = compare(snapshot, previous, budgets)
    print(line(c, args.paper_24h))
    if args.record:
        Path(args.ledger).parent.mkdir(parents=True, exist_ok=True)
        with open(args.ledger, "a") as fh:
            fh.write(json.dumps({**snapshot, "retired_all": retired_all(snapshot, previous)}, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
