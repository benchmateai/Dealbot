"""One line per shadow strategy still in the lab (A, E, F) and a JSON summary for the dashboard, the analyst and
the morning report. B, C and D were dropped on 2026-11-05 (DROPPED says why); their modules stay for the record.

    python -m lab.report --tape <paper-run copy>/logs/data --lab <shadow-run copy>/lab/data [--out lab/summaries/latest.json]

A strategy with nothing to judge yet says what it is waiting for rather than printing a zero that looks
like a result. Strategies count only data after their registration time.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lab.store import read_lab
from lab.strategies import a_control, e_incentive, f_fade

WAITING = {
    "E": "incentive capture: waits for the live feed (full-depth books in incentive markets) from the Kalshi key",
    "F": "maker long-shot fade: waits for the live feed (books and trades in long-dated markets) from the Kalshi key",
}
LIVE = {"E": e_incentive, "F": f_fade}
DROPPED = {
    "B": "late-window harvest, dropped 2026-11-05: -79.52 USD on 22 entries (2 upsets); favourites were not underpriced",
    "C": "crypto market making, dropped 2026-11-05: -959.27 USD even as an upper bound (fills were picked off)",
    "D": "contradiction scanner, dropped 2026-11-05: 9 fee-clearing gaps in about 30 hours, 1 lasting past one snapshot",
}


def build(tape_dir: str | Path, lab_dir: str | Path) -> dict:
    out: dict = {"strategies": {}}
    a = a_control.evaluate(tape_dir, lab_dir, since_ms=0)
    out["strategies"]["A"] = {"line": a_control.one_line(a["summary"]), "summary": a["summary"]}
    out["dropped"] = dict(DROPPED)
    status = list(read_lab(lab_dir, kinds=("lab_status",)))
    rest = [r for r in status if r.get("rest") and r.get("source") != "ws"]
    live = [r for r in status if r.get("source") == "ws"]
    out["recorder"] = rest[-1] if rest else None
    out["live_feed"] = live[-1] if live else None
    for key, strategy in LIVE.items():
        if not live:
            out["strategies"][key] = {"line": f"{key} {WAITING[key]}", "summary": None}
            continue
        result = strategy.evaluate(lab_dir)
        out["strategies"][key] = {"line": strategy.one_line(result["summary"]), "summary": result["summary"]}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The shadow lab's strategies, one line each")
    parser.add_argument("--tape", required=True)
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = build(args.tape, args.lab)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=1))
    for key in sorted(report["strategies"]):
        print(report["strategies"][key]["line"])
    print("dropped: " + "; ".join(f"{k} {v.split(',')[0]}" for k, v in sorted(report.get("dropped", {}).items())))
    if report["recorder"]:
        print(f"recorder: {report['recorder']['rest']}")
    if report["live_feed"]:
        f = report["live_feed"]
        print(f"live feed: {f.get('ws')} watched {f.get('watched')} errors {f.get('errors')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
