"""The shadow lab's numbers for the money dashboard's second dataset (`lab`), from lab.report's JSON.

    python -m dashboard.lab --report <lab.report --out file> --out /tmp/dealbot-dashboard/lab.json

One row per strategy still in the lab (A, E, F) with its one-line result and the scalar numbers of its
summary, one row per dropped strategy saying why, and when they were computed. The morning report rebuilds
it daily: E's replay takes seconds per day recorded, too slow to add to the hourly watchdog.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def rows(report: dict, *, now_ms: int) -> list[dict]:
    out = []
    for key, s in sorted((report.get("strategies") or {}).items()):
        summary = s.get("summary") or {}
        flat = {k: v for k, v in summary.items() if v is None or isinstance(v, (int, float, str, bool))}
        out.append({"id": key, "line": s.get("line"), **flat, "dropped": False, "updated_ms": now_ms})
    for key, why in sorted((report.get("dropped") or {}).items()):
        out.append({"id": key, "line": why, "dropped": True, "updated_ms": now_ms})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the money dashboard's lab rows")
    parser.add_argument("--report", required=True, help="lab.report's JSON (its --out file)")
    parser.add_argument("--out", default="/tmp/dealbot-dashboard/lab.json")
    args = parser.parse_args(argv)
    data = rows(json.loads(Path(args.report).read_text()), now_ms=int(time.time() * 1000))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, separators=(",", ":")))
    e = next((r for r in data if r["id"] == "E"), {})
    print(f"wrote {out}: {len(data)} rows; E realistic net {e.get('net_usd_realistic')} USD over {e.get('hours')} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
