"""Trial report: every configuration ever run, each survivor's Sharpe, and the deflated Sharpe haircut.

    python -m reports.trials --log-dir logs/data [--trials-file logs/data/trials.json] [--effective-trials N]

Returns come from the heartbeat equity series of each trial (one return per heartbeat interval,
within a run only, so restarts never create a phantom return). N is the number of registered trials;
pass --effective-trials to use a smaller number when trials are known to be highly correlated, or a
larger one to count trials run elsewhere. The cross-trial Sharpe variance needs at least two evaluated
trials; until then the null sampling variance 1/(T-1) is used and the report says so.
"""

from __future__ import annotations

import argparse
import math
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from logs.writer import read_events
from trials.deflated import deflated_sharpe, min_backtest_years, null_sharpe_variance, return_stats
from trials.registry import TrialRegistry

SECONDS_PER_YEAR = 31_557_600
DEFAULT_MIN_OBS = 30


def collect(log_dir: str | Path) -> tuple[dict[str, dict], dict[str, list[tuple[int, float]]]]:
    """Latest spec per trial from `trial` records, and (block, equity) points per trial from heartbeats."""
    specs: dict[str, dict] = {}
    points: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for event in read_events(log_dir, kinds=("trial", "heartbeat")):
        tid = event.get("trial_id")
        if not tid:
            continue
        if event["kind"] == "trial":
            specs[tid] = event.get("spec") or {}
        elif event.get("equity_usd") is not None and event.get("blk") is not None:
            points[tid].append((int(event["blk"]), float(event["equity_usd"])))
    return specs, points


def returns_from_heartbeats(points: list[tuple[int, float]], every: int) -> list[float]:
    """Simple returns between consecutive heartbeats exactly `every` blocks apart (same run, no gap)."""
    out = []
    for (b0, e0), (b1, e1) in zip(points, points[1:]):
        if b1 - b0 == every and e0 > 0:
            out.append(e1 / e0 - 1.0)
    return out


def evaluate_trial(spec: dict, points: list[tuple[int, float]], *, min_obs: int, now_ms: int) -> dict:
    every = int(spec.get("heartbeat_every_blocks") or 10)
    block_seconds = float(spec.get("block_seconds") or 12.0)
    period_seconds = every * block_seconds
    periods_per_year = SECONDS_PER_YEAR / period_seconds
    returns = returns_from_heartbeats(points, every)
    base = {"evaluated_ms": now_ms, "n_obs": len(returns), "period_seconds": period_seconds, "periods_per_year": periods_per_year, "sharpe": None}
    if len(returns) < min_obs:
        return {**base, "note": f"{len(returns)} returns, need {min_obs}"}
    stats = return_stats(returns)
    if stats is None:
        return {**base, "note": "no variance in equity (shadow mode, or no fills)"}
    return {
        **base,
        "sharpe": stats.sharpe,
        "sharpe_annual": stats.sharpe * math.sqrt(periods_per_year),
        "mean": stats.mean,
        "std": stats.std,
        "skew": stats.skew,
        "kurt": stats.kurt,
        "total_return": math.prod(1 + r for r in returns) - 1.0,
        "note": None,
    }


@dataclass(frozen=True)
class Row:
    trial_id: str
    bot: str
    modes: str
    runs: int
    n_obs: int
    sharpe_annual: float | None
    noise_max_annual: float | None
    haircut_annual: float | None
    dsr: float | None
    psr_zero: float | None
    passes_95: bool | None
    note: str


@dataclass(frozen=True)
class Report:
    n_trials: int
    n_registered: int
    n_evaluated: int
    var_sharpe: float | None
    var_source: str
    min_backtest_years: dict[float, float]
    rows: list[Row]


def evaluate(registry: TrialRegistry, log_dir: str | Path, *, min_obs: int = DEFAULT_MIN_OBS, effective_trials: int | None = None, target_sharpes: tuple[float, ...] = (0.5, 1.0, 2.0), now_ms: int | None = None) -> Report:
    now = int(time.time() * 1000) if now_ms is None else now_ms
    specs, points = collect(log_dir)
    for entry in registry.entries():
        spec = specs.get(entry.trial_id) or entry.spec
        registry.record_evaluation(entry.trial_id, evaluate_trial(spec, points.get(entry.trial_id, []), min_obs=min_obs, now_ms=now))
    n_trials = max(1, effective_trials if effective_trials is not None else registry.count())
    sharpes = registry.sharpes()
    var_sharpe = statistics.variance(sharpes) if len(sharpes) >= 2 else None
    var_source = "variance of Sharpe across evaluated trials" if var_sharpe is not None and var_sharpe > 0 else "null sampling variance 1/(T-1) (fewer than two evaluated trials)"
    if var_sharpe is not None and var_sharpe <= 0:
        var_sharpe = None
    rows = []
    for entry in registry.entries():
        ev = entry.evaluation or {}
        bot = str(entry.spec.get("bot", "?"))
        modes = ",".join(entry.modes)
        if ev.get("sharpe") is None:
            rows.append(Row(entry.trial_id, bot, modes, entry.runs, int(ev.get("n_obs") or 0), None, None, None, None, None, None, str(ev.get("note") or "not evaluated")))
            continue
        var_used = var_sharpe if var_sharpe is not None else null_sharpe_variance(int(ev["n_obs"]))
        deflated = deflated_sharpe(ev["sharpe"], int(ev["n_obs"]), n_trials, var_used, ev.get("skew", 0.0), ev.get("kurt", 3.0))
        ann = math.sqrt(ev["periods_per_year"])
        if deflated is None:
            rows.append(Row(entry.trial_id, bot, modes, entry.runs, int(ev["n_obs"]), ev["sharpe"] * ann, None, None, None, None, None, "moments make the PSR undefined"))
            continue
        rows.append(Row(entry.trial_id, bot, modes, entry.runs, int(ev["n_obs"]), ev["sharpe"] * ann, deflated.noise_max_sharpe * ann, deflated.haircut_sharpe * ann, deflated.dsr, deflated.psr_zero, deflated.passes_95, ""))
    return Report(n_trials, registry.count(), len(sharpes), var_sharpe, var_source, {t: min_backtest_years(n_trials, t) for t in target_sharpes}, rows)


def _f(value: float | None, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def render_markdown(report: Report) -> str:
    lines = ["# Trial registry and deflated Sharpe", ""]
    lines.append(f"- Trials registered: {report.n_registered} (N used for deflation: {report.n_trials}); evaluated with a Sharpe: {report.n_evaluated}")
    lines.append(f"- Cross-trial Sharpe variance: {_f(report.var_sharpe, 6)} per period, source: {report.var_source}")
    lines.append("- Minimum backtest length before a true annualized Sharpe stands out from the best of N noise trials: " + ", ".join(f"SR {t:g} -> {y:.2f} years" for t, y in report.min_backtest_years.items()))
    lines += ["", "| trial | bot | modes | runs | obs | Sharpe (ann.) | best-noise Sharpe (ann.) | haircut Sharpe (ann.) | DSR | PSR vs 0 | passes 95% | note |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report.rows:
        passes = "-" if r.passes_95 is None else ("yes" if r.passes_95 else "no")
        lines.append(f"| {r.trial_id} | {r.bot} | {r.modes} | {r.runs} | {r.n_obs} | {_f(r.sharpe_annual)} | {_f(r.noise_max_annual)} | {_f(r.haircut_annual)} | {_f(r.dsr, 3)} | {_f(r.psr_zero, 3)} | {passes} | {r.note} |")
    lines += [
        "",
        "Reading: the best-noise Sharpe is what selecting the best of N pure-noise trials would show; the haircut Sharpe is",
        "the observed Sharpe minus that. DSR is the probability the survivor beats the best noise trial, given its sample",
        "length, skew and kurtosis. A trial earns trust only when DSR is at least 0.95 and the sample is longer than the",
        "minimum backtest length for the Sharpe it claims. Every trial ever run counts toward N, including shadow runs.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trial registry report with the deflated Sharpe haircut")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--trials-file", default=None, help="default: <log-dir>/trials.json")
    parser.add_argument("--out", default="reports/out")
    parser.add_argument("--min-obs", type=int, default=DEFAULT_MIN_OBS)
    parser.add_argument("--effective-trials", type=int, default=None, help="override N (smaller for correlated trials, larger to count trials run elsewhere)")
    args = parser.parse_args(argv)
    trials_file = args.trials_file or str(Path(args.log_dir) / "trials.json")
    registry = TrialRegistry(trials_file)
    report = evaluate(registry, args.log_dir, min_obs=args.min_obs, effective_trials=args.effective_trials)
    text = render_markdown(report)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "trials.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out / 'trials.md'}; registry at {trials_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
