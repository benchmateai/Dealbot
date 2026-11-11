"""The team's running cost for the money dashboard: its own dataset, costs.json, rebuilt by the coordinator (the only
teammate that can read the costs) at each supervisor check and morning report.

    python -m dashboard.costs --snapshot FILE --history FILE [--budgets ops/budgets.json] [--append] --out FILE

The snapshot is the one reports/costs.py reads (ops/TEAM.md, "Running cost and budgets"). --append adds it to the
history, a JSON-lines file of every snapshot the checks and morning reports took (the morning report's ledger stays
apart), once its rows are built; a snapshot taken at the same time as one already there replaces it, so a corrected
re-run is what is kept. Rows, each with a `table` column like money.json's:
  cost_summary  one row: the window, from the history's snapshot nearest 24 hours before this one (at least an hour
                back; none on the first look), the team's spend in it against its budget, the total since each
                session began, and when the first of them began
  cost_role     one row per teammate: its spend in the window against its budget, and its total
A replaced session that a snapshot in the history names under "retired" counts in the window when a snapshot after
the window's start names it. The totals count every session the history has seen, current or replaced, at the most it
was seen to cost, so a replaced session nobody named keeps its last reading there.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from reports.costs import BUDGETS, NAMES, ORDER, _ms, compare

MIN_BACK_MS = 3_600_000
DAY_MS = 86_400_000


def valid(s: dict) -> bool:
    """A snapshot this module can read: its time, and each session's cost and start, as numbers and ISO times."""
    try:
        _ms(s["at"])
        for v in s["sessions"].values():
            float(v["cost_usd"])
            _ms(v["created_at"])
        for v in (s.get("retired") or {}).values():
            float(v["cost_usd"])
        return isinstance(s["at"], str)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def load_history(path: str | Path) -> list[dict]:
    """The history's snapshots; a line that is not one (a bad edit, two lines run together) is skipped."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            s = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(s, dict) and valid(s):
            out.append(s)
    return out


def append(path: str | Path, snapshot: dict) -> None:
    """Add `snapshot` to the history in place of any copy taken at the same time; other lines are kept as they are."""
    p = Path(path)
    keep = []
    for line in (p.read_text().splitlines() if p.exists() else []):
        try:
            same = json.loads(line).get("at") == snapshot["at"]
        except (json.JSONDecodeError, AttributeError):
            same = False
        if line.strip() and not same:
            keep.append(line)
    keep.append(json.dumps(snapshot, separators=(",", ":")))
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text("\n".join(keep) + "\n")
    os.replace(tmp, p)


def _retired(snaps: list[dict]) -> dict[str, dict]:
    """Every replaced session the snapshots name, with the most it was seen to cost."""
    out: dict[str, dict] = {}
    for s in snaps:
        for sid, v in (s.get("retired") or {}).items():
            if sid not in out or float(v["cost_usd"]) > out[sid]["cost_usd"]:
                out[sid] = {"role": v.get("role"), "cost_usd": float(v["cost_usd"])}
    return out


def _seen(snaps: list[dict]) -> dict[str, dict]:
    """Every session the snapshots show, current or replaced: its role, the most it was seen to cost, and when it
    began (known from a snapshot that showed it current)."""
    out: dict[str, dict] = {}
    for s in snaps:
        for role, v in s["sessions"].items():
            e = out.setdefault(v.get("id") or f"{role}@{v['created_at']}", {"role": role, "cost_usd": 0.0, "created_ms": None})
            e["cost_usd"] = max(e["cost_usd"], float(v["cost_usd"]))
            e["created_ms"] = _ms(v["created_at"])
        for sid, v in (s.get("retired") or {}).items():
            e = out.setdefault(sid, {"role": v.get("role"), "cost_usd": 0.0, "created_ms": None})
            e["cost_usd"] = max(e["cost_usd"], float(v["cost_usd"]))
            e["role"] = e["role"] or v.get("role")
    return out


def window_start(snapshot: dict, history: list[dict]) -> dict | None:
    """The history's snapshot nearest 24 hours before `snapshot`, of those at least an hour before it."""
    now = _ms(snapshot["at"])
    earlier = [s for s in history if _ms(s["at"]) <= now - MIN_BACK_MS]
    return min(earlier, key=lambda s: (abs(_ms(s["at"]) - (now - DAY_MS)), -_ms(s["at"]))) if earlier else None


def rows(snapshot: dict, history: list[dict], budgets: dict[str, float]) -> list[dict]:
    now = _ms(snapshot["at"])
    earlier = sorted((s for s in history if _ms(s["at"]) < now), key=lambda s: _ms(s["at"]))
    start = window_start(snapshot, earlier)
    if start is not None:
        t0 = _ms(start["at"])
        known = {sid: v["cost_usd"] for sid, v in _retired([s for s in earlier if _ms(s["at"]) <= t0]).items()}
        named = _retired([s for s in earlier if _ms(s["at"]) > t0] + [snapshot])
        c = compare({**snapshot, "retired": named}, {**start, "retired_all": known}, budgets)
    else:
        c = compare(snapshot, None, budgets)
    roles = {r["role"]: r for r in c["rows"]}
    seen = _seen(earlier + [snapshot])
    out = []
    first = min((e["created_ms"] for e in seen.values() if e["created_ms"] is not None), default=None)
    windowed = start is not None
    out.append({"table": "cost_summary", "id": "team", "updated_ms": now,
                "window_start_ms": _ms(start["at"]) if windowed else None, "window_hours": c["window_hours"],
                "spent_usd": c["team_spent_usd"] if windowed else None,
                "budget_usd": round(sum(r["limit_usd"] for r in c["rows"] if r["limit_usd"] is not None), 2) if windowed else c["team_budget_usd"],
                "daily_budget_usd": c["team_budget_usd"], "first_since_ms": first,
                "total_usd": round(sum(e["cost_usd"] for e in seen.values()), 2),
                "over": [NAMES.get(r, r) for r in c["over"]] if windowed else [],
                "missing": [NAMES.get(r, r) for r in c["missing"]], "snapshots": len(earlier) + 1})
    for role in sorted(snapshot["sessions"], key=lambda r: (ORDER.index(r) if r in ORDER else len(ORDER), r)):
        r = roles[role]
        total = sum(e["cost_usd"] for e in seen.values() if e["role"] == role)
        out.append({"table": "cost_role", "id": role, "name": NAMES.get(role, role),
                    "spent_usd": r["spent_usd"] if windowed else None, "budget_usd": r["budget_usd"],
                    "limit_usd": r["limit_usd"] if windowed else r["budget_usd"], "over": bool(r["over"]) if windowed else False,
                    "total_usd": round(total, 2), "since_ms": _ms(snapshot["sessions"][role]["created_at"])})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The team's running cost, as rows for the money dashboard")
    parser.add_argument("--snapshot", required=True, help="this check's costs, as the coordinator read them with get_session")
    parser.add_argument("--history", required=True, help="the JSON-lines history of every snapshot the checks took")
    parser.add_argument("--budgets", default=str(BUDGETS))
    parser.add_argument("--append", action="store_true", help="add the snapshot to the history first")
    parser.add_argument("--out", required=True, help="the dataset's file (costs.json)")
    args = parser.parse_args(argv)
    snapshot = json.loads(Path(args.snapshot).read_text())
    if not isinstance(snapshot, dict) or not valid(snapshot):
        print(f"{args.snapshot}: not a cost snapshot (ops/TEAM.md, \"Running cost and budgets\"); nothing written", file=sys.stderr)
        return 2
    budgets = {k: float(v) for k, v in json.loads(Path(args.budgets).read_text())["daily_usd"].items()}
    history = load_history(args.history)
    out = rows(snapshot, [s for s in history if s.get("at") != snapshot["at"]], budgets)
    if args.append:
        append(args.history, snapshot)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, separators=(",", ":")))
    s = out[0]
    window = (f"${s['spent_usd']:,.2f} over the last {s['window_hours']:.1f} hours (budget ${s['budget_usd']:,.2f})"
              if s["spent_usd"] is not None else "no earlier snapshot an hour back yet")
    print(f"wrote {args.out}: {len(out)} rows; the team {window}; ${s['total_usd']:,.2f} since each session began")
    return 0


if __name__ == "__main__":
    sys.exit(main())
