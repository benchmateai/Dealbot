"""One line per shadow strategy, A to F, and a JSON summary for the dashboard, the analyst and the morning report.

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
from lab.strategies import a_control, d_scanner

WAITING = {
    "B": "late-window harvest: waits for the live feed (second-by-second books and the settlement index) from the Kalshi key",
    "C": "crypto market making: waits for the live feed (full order book and trades) from the Kalshi key",
    "E": "incentive capture: waits for the live feed (full-depth books in incentive markets) from the Kalshi key",
    "F": "maker long-shot fade: waits for the live feed (books and trades in long-dated markets) from the Kalshi key",
}


def build(tape_dir: str | Path, lab_dir: str | Path) -> dict:
    out: dict = {"strategies": {}}
    a = a_control.evaluate(tape_dir, lab_dir, since_ms=0)
    out["strategies"]["A"] = {"line": a_control.one_line(a["summary"]), "summary": a["summary"]}
    d = d_scanner.scan(lab_dir, since_ms=d_scanner.REGISTERED_MS)
    out["strategies"]["D"] = {"line": d_scanner.one_line(d["summary"]), "summary": d["summary"], "top": d["runs"][:10]}
    status = [r for r in read_lab(lab_dir, kinds=("lab_status",)) if r.get("rest")]
    out["recorder"] = status[-1] if status else None
    for key in ("B", "C", "E", "F"):
        out["strategies"].setdefault(key, {"line": f"{key} {WAITING[key]}", "summary": None})
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
    if report["recorder"]:
        print(f"recorder: {report['recorder']['rest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
