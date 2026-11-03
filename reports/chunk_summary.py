"""One small file per chunk that says whether the desk was actually deciding.

    python -m reports.chunk_summary --log-dir logs/data --since-ms 1793680000000 [--out-dir logs/data/summaries]

Counts, over the events with since <= ts < until: records by kind, rejections and vetoes by check,
judge calls (answer records) and judge failures (jev_* rejections), decisions by action and how many
executed, fills, positions opened and closed, settlements (official or provisional), realized P&L,
equity at the start and end, and the feed's poll, error and rate-limit counters from the heartbeats.
`stalled` is true when the window spans at least 30 minutes and the judge was never asked: the
signature of every defect found on 2026-11-03, where commits kept landing while nothing was decided.
Writes summaries/chunk-<start>.json and summaries/latest.json and prints one line.
"""

from __future__ import annotations

import argparse
import collections
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from logs.writer import read_events

STALL_MS = 30 * 60_000


def summarize(log_dir: str | Path, *, since_ms: int, until_ms: int | None = None) -> dict:
    until = until_ms if until_ms is not None else int(time.time() * 1000) + 1
    kinds: collections.Counter[str] = collections.Counter()
    rejections: collections.Counter[str] = collections.Counter()
    vetoes: collections.Counter[str] = collections.Counter()
    actions: collections.Counter[str] = collections.Counter()
    executed = answers = opened = closed = 0
    fills: collections.Counter[str] = collections.Counter()
    settlements = {"official": 0, "provisional": 0}
    realized = 0.0
    equity: list[float] = []
    feed_first: dict | None = None
    feed_last: dict | None = None
    first_ts = last_ts = None
    models: collections.Counter[str] = collections.Counter()
    for e in read_events(log_dir):
        ts = e.get("ts")
        if not isinstance(ts, int) or ts < since_ms or ts >= until:
            continue
        first_ts = ts if first_ts is None else min(first_ts, ts)
        last_ts = ts if last_ts is None else max(last_ts, ts)
        kind = e.get("kind")
        kinds[kind] += 1
        if kind == "rejection":
            rejections[str(e.get("check"))] += 1
        elif kind == "veto":
            vetoes[str(e.get("check"))] += 1
        elif kind == "answer":
            answers += 1
            models[str(e.get("model"))] += 1
        elif kind == "decision":
            actions[str(e.get("action"))] += 1
            executed += bool(e.get("executed"))
        elif kind == "fill":
            fills[str(e.get("side"))] += 1
        elif kind == "position_opened":
            opened += 1
        elif kind == "position_closed":
            closed += 1
            realized += float(e.get("realized_pnl_usd") or 0.0)
        elif kind == "settlement":
            settlements["official" if e.get("official") else "provisional"] += 1
        elif kind == "heartbeat":
            if isinstance(e.get("equity_usd"), (int, float)):
                equity.append(float(e["equity_usd"]))
            if isinstance(e.get("feed"), dict):
                feed_first = feed_first or e["feed"]
                feed_last = e["feed"]
    span_ms = 0 if first_ts is None else last_ts - first_ts
    judge_failures = {k: v for k, v in rejections.items() if k.startswith("jev_") or k == "battery_fault"}
    feed = {}
    if feed_last:
        feed = {k: feed_last.get(k, 0) - (feed_first or {}).get(k, 0) for k in feed_last}
    return {
        "since_ms": since_ms,
        "until_ms": until,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "span_minutes": round(span_ms / 60_000, 1),
        "records": dict(kinds),
        "rejections": dict(rejections.most_common()),
        "vetoes": dict(vetoes.most_common()),
        "judge_calls": answers,
        "judge_failures": judge_failures,
        "models": dict(models),
        "decisions": dict(actions),
        "executed": executed,
        "fills": dict(fills),
        "positions_opened": opened,
        "positions_closed": closed,
        "settlements": settlements,
        "realized_pnl_usd": round(realized, 4),
        "equity_start": equity[0] if equity else None,
        "equity_end": equity[-1] if equity else None,
        "feed": feed,
        "stalled": span_ms >= STALL_MS and answers == 0,
    }


def one_line(s: dict) -> str:
    top = ", ".join(f"{k} {v}" for k, v in list(s["rejections"].items())[:3]) or "none"
    eq = "n/a" if s["equity_end"] is None else f"{s['equity_end']:.2f}"
    flag = " STALLED: the judge was never asked" if s["stalled"] else ""
    return (
        f"summary: {s['span_minutes']} min, judge calls {s['judge_calls']}, decisions {s['decisions'] or '{}'}, executed {s['executed']}, "
        f"opened {s['positions_opened']}, closed {s['positions_closed']}, realized {s['realized_pnl_usd']:+.2f} USD, equity {eq}, "
        f"top rejections: {top}, vetoes {sum(s['vetoes'].values())}, judge failures {sum(s['judge_failures'].values())}, "
        f"rate limits {s['feed'].get('rate_limits', 0)}{flag}"
    )


def write(summary: dict, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromtimestamp(summary["since_ms"] / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    path = out / f"chunk-{stamp}.json"
    text = json.dumps(summary, indent=1, sort_keys=True)
    path.write_text(text)
    (out / "latest.json").write_text(text)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize one chunk of the desk's events")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--since-ms", type=int, required=True)
    parser.add_argument("--until-ms", type=int, default=None)
    parser.add_argument("--out-dir", default=None, help="default: <log-dir>/summaries")
    args = parser.parse_args(argv)
    summary = summarize(args.log_dir, since_ms=args.since_ms, until_ms=args.until_ms)
    write(summary, args.out_dir or Path(args.log_dir) / "summaries")
    print(one_line(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
