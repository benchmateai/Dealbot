"""Write a static snapshot of the dashboard state (the same JSON /api/state serves, plus decision
details) so the page can be viewed without the server, for example as a shared preview.

    python -m dashboard.export --log-dir logs/data --out reports/out/data.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dashboard.serve import Dashboard


def export(log_dir: str | Path, out: str | Path, *, trials_file: str | Path | None = None) -> dict:
    dashboard = Dashboard(log_dir, trials_file)
    dashboard.refresh()
    payload = dashboard.payload(include_details=True, source_mode="snapshot")
    payload["source"]["exported_ms"] = int(time.time() * 1000)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a static dashboard snapshot")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--trials-file", default=None)
    parser.add_argument("--out", default="reports/out/data.json")
    args = parser.parse_args(argv)
    payload = export(args.log_dir, args.out, trials_file=args.trials_file)
    print(f"wrote {args.out}: {len(payload['moves'])} moves, {len(payload['equity'])} equity points, {len(payload.get('details', {}))} decision details")
    return 0


if __name__ == "__main__":
    sys.exit(main())
