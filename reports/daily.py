"""Daily summary: decisions made, trades taken, PnL after fees, every risk veto that fired.

    python -m reports.daily --log-dir logs/data --date YYYY-MM-DD [--out reports/out]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from logs.writer import read_events


def summarize(events: list[dict]) -> dict:
    decisions = [e for e in events if e["kind"] == "decision"]
    fills = [e for e in events if e["kind"] == "fill"]
    vetoes = [e for e in events if e["kind"] == "veto"]
    rejections = [e for e in events if e["kind"] == "rejection"]
    answers = [e for e in events if e["kind"] == "answer"]
    heartbeats = [e for e in events if e["kind"] == "heartbeat"]
    would = [e for e in events if e["kind"] == "would_execute"]
    fees = sum(float(f.get("fee_usd") or 0) + float(f.get("gas_usd") or 0) for f in fills)
    realized = sum(float(f.get("realized_pnl_usd") or 0) for f in fills)
    equity_start = heartbeats[0].get("equity_usd") if heartbeats else None
    equity_end = heartbeats[-1].get("equity_usd") if heartbeats else None
    return {
        "decisions": len(decisions),
        "decisions_by_bot_phase_action": Counter((d.get("bot"), d.get("phase"), d.get("action")) for d in decisions),
        "executed": sum(1 for d in decisions if d.get("executed")),
        "vetoed": sum(1 for d in decisions if d.get("approved") is False),
        "would_execute": len(would),
        "fills": len(fills),
        "fees_usd": fees,
        "realized_pnl_usd": realized,
        "realized_after_fees_usd": realized - fees,
        "equity_start": equity_start,
        "equity_end": equity_end,
        "vetoes": vetoes,
        "vetoes_by_check": Counter(v.get("check") for v in vetoes),
        "rejections_by_check": Counter(r.get("check") for r in rejections),
        "judge_calls": len(answers),
        "judge_models": Counter(a.get("model") for a in answers),
        "judge_latency_ms": (sum(float(a.get("latency_ms") or 0) for a in answers) / len(answers)) if answers else None,
    }


def render_markdown(date: str, s: dict) -> str:
    lines = [f"# Daily summary {date}", ""]
    lines.append(f"- Decisions: {s['decisions']} (executed {s['executed']}, vetoed {s['vetoed']}, shadow would-execute {s['would_execute']})")
    lines.append(f"- Trades (fills): {s['fills']}")
    lines.append(f"- Realized PnL after fees and gas: {s['realized_after_fees_usd']:+.2f} USD (gross {s['realized_pnl_usd']:+.2f}, fees+gas {s['fees_usd']:.2f})")
    if s["equity_start"] is not None and s["equity_end"] is not None:
        lines.append(f"- Equity: {s['equity_start']:.2f} -> {s['equity_end']:.2f} USD ({s['equity_end'] - s['equity_start']:+.2f}, includes unrealized)")
    lines.append(f"- Judge calls: {s['judge_calls']}, models seen: {dict(s['judge_models'])}, mean latency: {'n/a' if s['judge_latency_ms'] is None else f'{s['judge_latency_ms']:.0f} ms'}")
    lines += ["", "## Decisions by bot / phase / action", "", "| bot | phase | action | n |", "|---|---|---|---|"]
    for (bot, phase, action), n in sorted(s["decisions_by_bot_phase_action"].items(), key=lambda kv: str(kv[0])):
        lines.append(f"| {bot} | {phase} | {action} | {n} |")
    lines += ["", f"## Risk vetoes that fired ({len(s['vetoes'])})", ""]
    if s["vetoes"]:
        lines += ["| ts | decision | sym | check | detail |", "|---|---|---|---|---|"]
        for v in s["vetoes"]:
            lines.append(f"| {v.get('ts')} | {v.get('decision_id')} | {v.get('sym')} | {v.get('check')} | {v.get('detail')} |")
    else:
        lines.append("none")
    lines += ["", "## Funnel rejections by check", "", "| check | n |", "|---|---|"]
    for check, n in s["rejections_by_check"].most_common():
        lines.append(f"| {check} | {n} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Daily summary from the event log")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--date", required=True, help="UTC day, YYYY-MM-DD")
    parser.add_argument("--out", default="reports/out")
    args = parser.parse_args(argv)
    events = list(read_events(args.log_dir, date=args.date))
    text = render_markdown(args.date, summarize(events))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"daily-{args.date}.md"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
