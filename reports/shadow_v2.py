"""Paper rules on desk v2's own bets: what v2 would have made under a different rule, on the same markets.

    python -m reports.shadow_v2 --log-dir logs/data [--out FILE]

The owner chose the first two on 2026-11-05 after v2's first day, when the bets bought as long shots carried
the profit and the favourites barely paid, and the third on 2026-11-06, when v2's forecast graded worse than
Kalshi's own price in the last 3 minutes before the close. Each is fixed here before any bet it is judged on:
only bets opened from its registration test it (REGISTERED_MS, 2026-11-05T22:00Z, for the first two;
LATE_ENTRY_REGISTERED_MS, 2026-11-06T07:00Z, for the third, reported beside v2 on exactly the same bets).
v2 itself trades on unchanged.

  late_stop_underdogs  v2's late stop only on bets bought under UNDERDOG_BELOW (50 cents); a favourite the
                       desk sold in its last minute is held to the close instead, at its official result.
                       On v2's first 44 bets the stop saved 5.13 USD on 22 long shots and cost 6.27 on the
                       one favourite it sold, which then won.
  skip_favourites      skip bets bought above FAVOURITE_ABOVE (70 cents); every other bet as v2 traded it.
                       Lab strategy A's favourites made +2.50 USD on 52 trades: about nothing for the risk.
  skip_late_entries    skip bets opened under LATE_ENTRY_S (180 s) before the close, by the entry snapshot's
                       seconds to expiry; a bet without one counts as v2 traded it. Lab A's forecast beat the
                       market's mid 7 minutes out and lost to it 3 minutes and 1 minute out (log loss 0.316
                       against 0.309, 0.196 against 0.187); v2's 8 bets opened inside 3 minutes lost 1.90
                       USD while its other 55 made 37.78, though most of that loss was one favourite the
                       late stop sold, which then won.
  next_round           the owner's pick for the next round, 2026-11-06: skip_late_entries and
                       late_stop_underdogs together, favourites kept; from LATE_ENTRY_REGISTERED_MS too.

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

REGISTERED_MS = 1_793_916_000_000  # 2026-11-05T22:00:00Z: bets opened from here on test the first two rules
LATE_ENTRY_REGISTERED_MS = 1_793_948_400_000  # 2026-11-06T07:00:00Z: the third rule's own test starts here
UNDERDOG_BELOW = 0.50
FAVOURITE_ABOVE = 0.70
LATE_ENTRY_S = 180
STRATEGIES = {
    "desk": "desk v2, as traded",
    "late_stop_underdogs": f"late stop only on bets bought under {UNDERDOG_BELOW * 100:.0f} cents; favourites held to the close",
    "skip_favourites": f"skip bets bought above {FAVOURITE_ABOVE * 100:.0f} cents",
    "skip_late_entries": f"skip bets opened under {LATE_ENTRY_S // 60} minutes before the close",
    "next_round": "the next round's pick: no bets in the last 3 minutes, late stop on long shots only, favourites kept",
}
LATER_RULES = ("skip_late_entries", "next_round")  # registered at LATE_ENTRY_REGISTERED_MS
FIRST_RULES = ("desk", "late_stop_underdogs", "skip_favourites")


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
    if strategy in ("skip_late_entries", "next_round"):
        left = p.get("entry_left_s")
        if left is not None and left < LATE_ENTRY_S:
            return "skipped", 0.0
        return outcome(p, "late_stop_underdogs", payouts) if strategy == "next_round" else (p["result"], p["pnl"])
    if strategy == "late_stop_underdogs":
        if p["result"] == "sold" and p["bet_price"] >= UNDERDOG_BELOW:  # v2 sells only by its late stop
            payout = payouts.get(p.get("ticker") or "")
            if payout is None:
                return "open", None
            won = payout if p["sign"] > 0 else 1.0 - payout
            return ("won" if won >= 0.5 else "lost"), round(p["contracts"] * (won - p["bet_price"]) - p["entry_fee"], 2)
        return p["result"], p["pnl"]
    raise ValueError(f"unknown rule {strategy!r}")


def evaluate(log_dir: str | Path, *, registered_ms: int = REGISTERED_MS, late_entry_registered_ms: int = LATE_ENTRY_REGISTERED_MS) -> dict:
    start = v2_start_ms(log_dir)
    report: dict = {"v2_start_ms": start, "registered_ms": registered_ms, "late_entry_registered_ms": late_entry_registered_ms,
                    "rules": {"underdog_below": UNDERDOG_BELOW, "favourite_above": FAVOURITE_ABOVE, "late_entry_s": LATE_ENTRY_S},
                    "strategies": {}, "trades": []}
    if start is None:
        return report
    positions = [p for p in _positions(log_dir, start) if p["opened_ms"] >= start]
    payouts = _payouts(log_dir, start)
    for name, label in STRATEGIES.items():
        reg = late_entry_registered_ms if name in LATER_RULES else registered_ms
        report["strategies"][name] = {
            "label": label,
            "registered_ms": reg,
            "since_v2": _stats([outcome(p, name, payouts) for p in positions]),
            "test": _stats([outcome(p, name, payouts) for p in positions if p["opened_ms"] >= reg]),
        }
    # v2 on exactly the later rules' bets, so they compare like for like
    same = _stats([outcome(p, "desk", payouts) for p in positions if p["opened_ms"] >= late_entry_registered_ms])
    for name in LATER_RULES:
        report["strategies"][name]["desk_same"] = dict(same)
    for p in positions:
        report["trades"].append({"id": p["id"], "sym": p["sym"], "ticker": p.get("ticker"), "opened_ms": p["opened_ms"], "bet": p["bet"],
                                 "bet_price": round(p["bet_price"], 4), "entry_left_s": p.get("entry_left_s"),
                                 **{n: dict(zip(("result", "pnl_usd"), outcome(p, n, payouts))) for n in STRATEGIES}})
    return report


def _bit(name: str, x: dict) -> str:
    return (f"{name} {x['pnl_usd']:+.2f} ({x['trades']} closed, {x['won']} up" + (f", {x['skipped']} skipped" if x["skipped"] else "")
            + (f", {x['open']} awaiting a result" if x["open"] else "") + ")")


def one_line(report: dict, part: str, names: tuple[str, ...] | None = None) -> str:
    return " | ".join(_bit(name, s[part]) for name, s in report["strategies"].items() if names is None or name in names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Desk v2 beside the paper rules the owner chose on 2026-11-05 and 2026-11-06")
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
    first = time.strftime("%Y-%m-%d %H:%MZ", time.gmtime(report["registered_ms"] / 1000))
    third = time.strftime("%Y-%m-%d %H:%MZ", time.gmtime(report["late_entry_registered_ms"] / 1000))
    later = report["strategies"]
    print(f"v2 rules (test, bets opened from {first}): {one_line(report, 'test', FIRST_RULES)}")
    print(f"v2 rule 3 and the next round's pick (test, bets opened from {third}): {_bit('skip_late_entries', later['skip_late_entries']['test'])} | "
          f"{_bit('next_round', later['next_round']['test'])} | {_bit('desk', later['skip_late_entries']['desk_same'])} on the same bets")
    print(f"v2 rules (all of v2, in sample before each rule's start): {one_line(report, 'since_v2')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
