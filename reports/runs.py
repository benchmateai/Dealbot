"""Which desk wrote which stretch of the paper run's log.

The first desk (v1: Jev's probability blended 50/50 with a spot-price formula) ran the measured week from
WEEK1_START_MS. Desk v2 (policy/anchored.py: the market-anchored forecast, no Jev, the late stop) took over
at the first trial it registered, which v2_start_ms finds in the log, so the dashboard, the shadow report
and the analyst all split the record at the same moment without a hard-coded time. Desk v3 (the same
forecast; entries 3 to 10 minutes out, the late stop on long shots only) takes over the same way, at the
first trial whose spec names its rules (v3_start_ms).
"""

from __future__ import annotations

import json
from pathlib import Path

# The measured week starts with the first chunk after the fix for the doubled desk (1f1a3f4): from
# 06:42 to 08:23Z on 2026-11-03 two to four desk processes wrote into one log, so that stretch is
# kept in the record but left out of the results.
WEEK1_START_MS = 1_793_694_300_000  # 2026-11-03T08:25:00Z


def v2_start_ms(log_dir: str | Path) -> int | None:
    """Time of the first paper trial registered with the anchored forecast, or None while v1 still runs."""
    return _first_paper_trial_ms(log_dir, lambda kalshi: kalshi.get("forecast") == "anchored")


def v3_start_ms(log_dir: str | Path) -> int | None:
    """Time of the first paper trial registered with desk v3's rules, or None while an earlier desk runs."""
    return _first_paper_trial_ms(log_dir, lambda kalshi: kalshi.get("rules") == "v3")


def _first_paper_trial_ms(log_dir: str | Path, match) -> int | None:
    for path in sorted(Path(log_dir).glob("events-*.jsonl")):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if '"kind":"trial"' not in line and '"kind": "trial"' not in line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                kalshi = (e.get("spec") or {}).get("kalshi") or {}
                if match(kalshi) and e.get("mode") == "paper" and isinstance(e.get("ts"), int):
                    return e["ts"]
    return None
