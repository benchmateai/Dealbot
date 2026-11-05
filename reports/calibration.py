"""Calibration report: predicted probability vs realized outcome per bucket, Brier score, and a
reliability chart (SVG, no dependencies).

    python -m reports.calibration --log-dir logs/data --out reports/out [--date YYYY-MM-DD]

Outcome records carry `qkind` (the question kind). Noul answers give one forecast each. Choice and Score answers give one forecast per option (the
probability assigned to that option vs whether it was realized), the usual one-vs-rest reading.
"""

from __future__ import annotations

import argparse
import html
import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from logs.writer import read_events


@dataclass(frozen=True)
class Forecast:
    bot: str
    qid: str
    label: str
    p: float
    y: int


@dataclass(frozen=True)
class Bucket:
    lo: float
    hi: float
    n: int
    mean_p: float | None
    observed: float | None


def forecasts_from_outcomes(outcomes: Iterable[dict]) -> list[Forecast]:
    out: list[Forecast] = []
    for rec in outcomes:
        if rec.get("status") != "resolved":
            continue
        kind, predicted, realized = rec.get("qkind"), rec.get("predicted"), rec.get("realized")
        bot, qid = str(rec.get("bot")), str(rec.get("qid"))
        if kind == "noul" and isinstance(predicted, (int, float)) and isinstance(realized, bool):
            out.append(Forecast(bot, qid, "yes", float(predicted), int(realized)))
        elif kind in ("choice", "score") and isinstance(predicted, dict):
            realized_label = str(realized)
            for label, p in predicted.items():
                if isinstance(p, (int, float)):
                    out.append(Forecast(bot, qid, str(label), float(p), int(str(label) == realized_label)))
    return out


def load_forecasts(log_dir: str | Path, *, date: str | None = None) -> list[Forecast]:
    return forecasts_from_outcomes(read_events(log_dir, date=date, kinds=("outcome",)))


def brier(forecasts: Iterable[Forecast]) -> float | None:
    items = list(forecasts)
    if not items:
        return None
    return sum((f.p - f.y) ** 2 for f in items) / len(items)


def buckets(forecasts: Iterable[Forecast], n_buckets: int = 10) -> list[Bucket]:
    items = list(forecasts)
    out = []
    for i in range(n_buckets):
        lo, hi = i / n_buckets, (i + 1) / n_buckets
        members = [f for f in items if (lo <= f.p < hi) or (i == n_buckets - 1 and f.p == 1.0)]
        if members:
            out.append(Bucket(lo, hi, len(members), sum(f.p for f in members) / len(members), sum(f.y for f in members) / len(members)))
        else:
            out.append(Bucket(lo, hi, 0, None, None))
    return out


def reliability_svg(bks: list[Bucket], *, title: str = "Reliability", subtitle: str = "") -> str:
    size, margin = 560, 64
    plot = size - 2 * margin
    max_n = max((b.n for b in bks), default=0) or 1

    def x(p: float) -> float:
        return margin + p * plot

    def y(p: float) -> float:
        return size - margin - p * plot

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="{html.escape(title)}">',
        "<style>"
        ".viz{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e6e6e3;--ref:#9a9892;--s1:#2a78d6}"
        "@media (prefers-color-scheme: dark){.viz{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#33332f;--ref:#7a7873;--s1:#3987e5}}"
        ".viz text{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;fill:var(--ink)}"
        ".viz .t2{fill:var(--ink2)}.viz .grid{stroke:var(--grid);stroke-width:1}.viz .ref{stroke:var(--ref);stroke-width:2;stroke-dasharray:6 6}"
        ".viz .dot{fill:var(--s1);stroke:var(--surface);stroke-width:2}.viz .line{stroke:var(--s1);stroke-width:2;fill:none}"
        "</style>",
        '<g class="viz">',
        f'<rect width="{size}" height="{size}" fill="var(--surface)"/>',
        f'<text x="{margin}" y="28" font-size="16" font-weight="600">{html.escape(title)}</text>',
    ]
    if subtitle:
        parts.append(f'<text x="{margin}" y="46" font-size="12" class="t2">{html.escape(subtitle)}</text>')
    for k in range(6):
        p = k / 5
        parts.append(f'<line class="grid" x1="{x(0):.1f}" y1="{y(p):.1f}" x2="{x(1):.1f}" y2="{y(p):.1f}"/>')
        parts.append(f'<line class="grid" x1="{x(p):.1f}" y1="{y(0):.1f}" x2="{x(p):.1f}" y2="{y(1):.1f}"/>')
        parts.append(f'<text x="{x(p):.1f}" y="{size - margin + 18}" font-size="11" text-anchor="middle" class="t2">{p:.1f}</text>')
        parts.append(f'<text x="{margin - 8}" y="{y(p) + 4:.1f}" font-size="11" text-anchor="end" class="t2">{p:.1f}</text>')
    parts.append(f'<line class="ref" x1="{x(0):.1f}" y1="{y(0):.1f}" x2="{x(1):.1f}" y2="{y(1):.1f}"/>')
    points = [(b.mean_p, b.observed, b.n) for b in bks if b.n > 0 and b.mean_p is not None]
    if len(points) >= 2:
        path = " ".join(f"{'M' if i == 0 else 'L'}{x(px):.1f},{y(py):.1f}" for i, (px, py, _) in enumerate(points))
        parts.append(f'<path class="line" d="{path}"/>')
    for px, py, n in points:
        r = 4 + 8 * math.sqrt(n / max_n)
        parts.append(f'<circle class="dot" cx="{x(px):.1f}" cy="{y(py):.1f}" r="{r:.1f}"><title>predicted {px:.2f}, observed {py:.2f}, n={n}</title></circle>')
        parts.append(f'<text x="{x(px):.1f}" y="{y(py) - r - 4:.1f}" font-size="10" text-anchor="middle" class="t2">n={n}</text>')
    parts.append(f'<text x="{x(0.5):.1f}" y="{size - 18}" font-size="12" text-anchor="middle">Predicted probability (bucket mean)</text>')
    parts.append(f'<text x="18" y="{y(0.5):.1f}" font-size="12" text-anchor="middle" transform="rotate(-90 18 {y(0.5):.1f})">Observed frequency</text>')
    lx, ly = x(0.02), y(0.98)
    parts.append(f'<circle class="dot" cx="{lx + 6:.1f}" cy="{ly:.1f}" r="5"/><text x="{lx + 16:.1f}" y="{ly + 4:.1f}" font-size="11">Observed frequency per bucket (dot size = count)</text>')
    parts.append(f'<line class="ref" x1="{lx:.1f}" y1="{ly + 18:.1f}" x2="{lx + 12:.1f}" y2="{ly + 18:.1f}"/><text x="{lx + 16:.1f}" y="{ly + 22:.1f}" font-size="11">Perfect calibration</text>')
    parts.append("</g></svg>")
    return "\n".join(parts)


def render_markdown(forecasts: list[Forecast], bks: list[Bucket], *, svg_name: str) -> str:
    lines = ["# Calibration report", ""]
    score = brier(forecasts)
    lines.append(f"- Forecasts graded: {len(forecasts)}")
    lines.append(f"- Brier score (all): {'n/a' if score is None else f'{score:.4f}'} (0 is perfect; 0.25 is a coin flip at p=0.5)")
    base_rate = sum(f.y for f in forecasts) / len(forecasts) if forecasts else None
    if base_rate is not None:
        lines.append(f"- Base rate of realized 'yes': {base_rate:.3f} (Brier of always predicting the base rate: {base_rate * (1 - base_rate):.4f})")
    lines += ["", f"![reliability]({svg_name})", "", "## Reliability by bucket", "", "| bucket | n | mean predicted | observed | gap |", "|---|---|---|---|---|"]
    for b in bks:
        if b.n:
            lines.append(f"| {b.lo:.1f}-{b.hi:.1f} | {b.n} | {b.mean_p:.3f} | {b.observed:.3f} | {b.observed - b.mean_p:+.3f} |")
        else:
            lines.append(f"| {b.lo:.1f}-{b.hi:.1f} | 0 | - | - | - |")
    lines += ["", "## Brier by question", "", "| bot | question | option | n | Brier |", "|---|---|---|---|---|"]
    groups: dict[tuple[str, str, str], list[Forecast]] = defaultdict(list)
    for f in forecasts:
        groups[(f.bot, f.qid, f.label)].append(f)
    for (bot, qid, label), items in sorted(groups.items()):
        lines.append(f"| {bot} | {qid} | {label} | {len(items)} | {brier(items):.4f} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibration report from the event log")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--out", default="reports/out")
    parser.add_argument("--date", default=None, help="UTC day of the outcome records, YYYY-MM-DD (default: all)")
    args = parser.parse_args(argv)
    forecasts = load_forecasts(args.log_dir, date=args.date)
    bks = buckets(forecasts)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    suffix = args.date or "all"
    svg_name = f"reliability-{suffix}.svg"
    (out / svg_name).write_text(reliability_svg(bks, title="Reliability", subtitle=f"{len(forecasts)} graded forecasts, Brier {brier(forecasts) if forecasts else float('nan'):.4f}"), encoding="utf-8")
    (out / f"calibration-{suffix}.md").write_text(render_markdown(forecasts, bks, svg_name=svg_name), encoding="utf-8")
    print(f"wrote {out / f'calibration-{suffix}.md'} and {out / svg_name} ({len(forecasts)} forecasts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
