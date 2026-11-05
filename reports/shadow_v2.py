"""Paper rules on desk v2's own bets: what v2 would have made under a different rule, on the same markets.

    python -m reports.shadow_v2 --log-dir logs/data [--out FILE]

The owner chose these on 2026-11-05 after v2's first day, when the bets bought as long shots carried the
profit and the favourites barely paid. Both are fixed here before any bet they are judged on: only bets
opened from REGISTERED_MS (2026-11-05T22:00Z) on test them. v2 itself trades on unchanged.

  late_stop_underdogs  v2's late stop only on bets bought under UNDERDOG_BELOW (50 cents); a favourite the
                       desk sold in its last minute is held to the close instead, at its official result.
                       On v2's first 44 bets the stop saved 5.13 USD on 22 long shots and cost 6.27 on the
                       one favourite it sold, which then won.
  skip_favourites      skip bets bought above FAVOURITE_ABOVE (70 cents); every other bet as v2 traded it.
                       Lab strategy A's favourites made +2.50 USD on 52 trades: about nothing for the risk.

A rule can only keep a bet the desk sold or skip one it took; it never takes a bet the desk did not.
Holding to the close pays no fee; a skipped bet counts 0.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from logs.writer import read_events
from reports.runs import v2_start_ms
from reports.shadow import _positions, _stats

REGISTERED_MS = 1_793_916_000_000  # 2026-11-05T22:00:00Z: bets opened from here on test the rules
UNDERDOG_BELOW = 0.50
FAVOURITE_ABOVE = 0.70
STRATEGIES = {
    "desk": "desk v2, as traded",
    "late_stop_underdogs": f"late stop only on bets bought under {UNDERDOG_BELOW * 100:.0f} cents; favourites held to the close",
    "skip_favourites": f"skip bets bought above {FAVOURITE_ABOVE * 100:.0f} cents",
}


def _payouts(log_dir: str | Path, since_ms: int) -> dict[str, float]:
    """ticker -> YES payout from the desk's own settlement records (official, or provisional until Kalshi's)."""
    out: dict[str, float] = {}
    for e in read_events(log_dir):
        if e.get("kind") == "settlement" and e.get("ticker") and isinstance(e.get("ts"), int) and e["ts"] >= since_ms:
            if e.get("official") or e["ticker"] not in out:
                out[e["ticker"]] = float(e.get("payout") or 0.0)
    return out


def outcome(p: dict, strategy: str, payouts: dict[str, float]) -> tuple[str, float | None]:
    """(result, P&L after fees) of one v2 position under a rule; ("skipped", 0.0) when the rule would not take it."""
    if strategy == "desk":
        return p["result"], p["pnl"]
    if strategy == "skip_favourites":
        return ("skipped", 0.0) if p["bet_price"] > FAVOURITE_ABOVE else (p["result"], p["pnl"])
    if strategy == "late_stop_underdogs":
        if p["result"] == "sold" and p["bet_price"] >= UNDERDOG_BELOW:  # v2 sells only by its late stop
            payout = payouts.get(p.get("ticker") or "")
            if payout is None:
                return "open", None
            won = payout if p["sign"] > 0 else 1.0 - payout
            return ("won" if won >= 0.5 else "lost"), round(p["contracts"] * (won - p["bet_price"]) - p["entry_fee"], 2)
        return p["result"], p["pnl"]
    raise ValueError(f"unknown rule {strategy!r}")


def evaluate(log_dir: str | Path, *, registered_ms: int = REGISTERED_MS) -> dict:
    start = v2_start_ms(log_dir)
    report: dict = {"v2_start_ms": start, "registered_ms": registered_ms, "rules": {"underdog_below": UNDERDOG_BELOW, "favourite_above": FAVOURITE_ABOVE},
                    "strategies": {}, "trades": []}
    if start is None:
        return report
    positions = [p for p in _positions(log_dir, start) if p["opened_ms"] >= start]
    payouts = _payouts(log_dir, start)
    for name, label in STRATEGIES.items():
        report["strategies"][name] = {
            "label": label,
            "since_v2": _stats([outcome(p, name, payouts) for p in positions]),
            "test": _stats([outcome(p, name, payouts) for p in positions if p["opened_ms"] >= registered_ms]),
        }
    for p in positions:
        report["trades"].append({"id": p["id"], "sym": p["sym"], "ticker": p.get("ticker"), "opened_ms": p["opened_ms"], "bet": p["bet"],
                                 "bet_price": round(p["bet_price"], 4), **{n: dict(zip(("result", "pnl_usd"), outcome(p, n, payouts))) for n in STRATEGIES}})
    return report


def one_line(report: dict, part: str) -> str:
    bits = []
    for name, s in report["strategies"].items():
        x = s[part]
        bits.append(f"{name} {x['pnl_usd']:+.2f} ({x['trades']} closed, {x['won']} up" + (f", {x['skipped']} skipped" if x["skipped"] else "")
                    + (f", {x['open']} awaiting a result" if x["open"] else "") + ")")
    return " | ".join(bits)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Desk v2 beside the paper rules the owner chose on 2026-11-05")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = evaluate(args.log_dir)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=1))
    if report["v2_start_ms"] is None:
        print("v2 rules: desk v2 has not started in this log")
        return 0
    when = time.strftime("%Y-%m-%d %H:%MZ", time.gmtime(report["registered_ms"] / 1000))
    print(f"v2 rules (test, bets opened from {when}): {one_line(report, 'test')}")
    print(f"v2 rules (all of v2, in sample before {when}): {one_line(report, 'since_v2')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
