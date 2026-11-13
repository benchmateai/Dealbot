"""Weekly summary: the daily figures for each of the last N days plus the window's calibration and
the trial registry's verdict. The question it answers is "what did the desk do, and would its
judgments have been worth trusting", not "how much did it make".

    python -m reports.weekly --log-dir logs/data [--days 7] [--end YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from logs.writer import read_events
from reports.calibration import brier, buckets, forecasts_from_outcomes
from reports.daily import summarize
from reports.trials import evaluate
from trials.registry import TrialRegistry


def window_days(end: str | None, days: int) -> list[str]:
    last = datetime.strptime(end, "%Y-%m-%d").date() if end else datetime.now(timezone.utc).date()
    return [(last - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days - 1, -1, -1)]


def render(log_dir: str | Path, dates: list[str], *, trials_file: str | Path | None = None) -> str:
    lines = [f"# Weekly summary {dates[0]} to {dates[-1]}", "", "| day | decisions | executed | vetoed | fills | realized after fees | equity start | equity end |", "|---|---|---|---|---|---|---|---|"]
    totals = {"decisions": 0, "executed": 0, "vetoed": 0, "fills": 0, "realized": 0.0}
    first_equity, last_equity = None, None
    for day in dates:
        s = summarize(list(read_events(log_dir, date=day)))
        totals["decisions"] += s["decisions"]
        totals["executed"] += s["executed"]
        totals["vetoed"] += s["vetoed"]
        totals["fills"] += s["fills"]
        totals["realized"] += s["realized_after_fees_usd"]
        if s["equity_start"] is not None and first_equity is None:
            first_equity = s["equity_start"]
        if s["equity_end"] is not None:
            last_equity = s["equity_end"]
        eq = lambda v: "-" if v is None else f"{v:.2f}"  # noqa: E731
        lines.append(f"| {day} | {s['decisions']} | {s['executed']} | {s['vetoed']} | {s['fills']} | {s['realized_after_fees_usd']:+.2f} | {eq(s['equity_start'])} | {eq(s['equity_end'])} |")
    lines.append(f"| total | {totals['decisions']} | {totals['executed']} | {totals['vetoed']} | {totals['fills']} | {totals['realized']:+.2f} | {'-' if first_equity is None else f'{first_equity:.2f}'} | {'-' if last_equity is None else f'{last_equity:.2f}'} |")
    if first_equity is not None and last_equity is not None and first_equity > 0:
        lines += ["", f"Equity change over the window, unrealized included: {last_equity - first_equity:+.2f} USD ({(last_equity / first_equity - 1) * 1e4:+.0f} bps)."]
    forecasts = [f for day in dates for f in forecasts_from_outcomes(read_events(log_dir, date=day, kinds=("outcome",)))]
    score = brier(forecasts)
    lines += ["", "## Calibration over the window", ""]
    if forecasts:
        base = sum(f.y for f in forecasts) / len(forecasts)
        lines.append(f"- {len(forecasts)} graded forecasts, Brier {score:.4f}; always predicting the base rate {base:.3f} would score {base * (1 - base):.4f}.")
        lines += ["", "| bucket | n | mean predicted | observed |", "|---|---|---|---|"]
        for b in buckets(forecasts):
            if b.n:
                lines.append(f"| {b.lo:.1f}-{b.hi:.1f} | {b.n} | {b.mean_p:.3f} | {b.observed:.3f} |")
    else:
        lines.append("- No graded forecasts yet.")
    tf = Path(trials_file) if trials_file else Path(log_dir) / "trials.json"
    lines += ["", "## Trials", ""]
    if tf.exists():
        report = evaluate(TrialRegistry(tf), log_dir, persist=False)
        lines.append(f"- {report.n_registered} configurations registered (N = {report.n_trials}); minimum backtest for a true annualized Sharpe of 1: {report.min_backtest_years.get(1.0, 0):.2f} years.")
        lines += ["", "| trial | bot | obs | Sharpe (ann.) | best-noise Sharpe | DSR | verdict |", "|---|---|---|---|---|---|---|"]
        for r in report.rows:
            verdict = "passes 95%" if r.passes_95 else ("fails 95%" if r.passes_95 is False else r.note)
            f = lambda v: "-" if v is None else f"{v:.2f}"  # noqa: E731
            lines.append(f"| {r.trial_id[:8]} | {r.bot} | {r.n_obs} | {f(r.sharpe_annual)} | {f(r.noise_max_annual)} | {'-' if r.dsr is None else f'{r.dsr:.3f}'} | {verdict} |")
    else:
        lines.append("- No trial registry found.")
    lines += ["", "Read the money line last. A week is far below the minimum backtest length for any Sharpe worth having; the calibration table and the trial verdict are the evidence."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly summary from the event log")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--trials-file", default=None)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--end", default=None, help="last UTC day, YYYY-MM-DD (default today)")
    parser.add_argument("--out", default="reports/out")
    args = parser.parse_args(argv)
    dates = window_days(args.end, args.days)
    text = render(args.log_dir, dates, trials_file=args.trials_file)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"weekly-{dates[-1]}.md"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
