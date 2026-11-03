"""Shadow strategies: what the paper desk would have made under a different rule, on the same markets.

    python -m reports.shadow --log-dir logs/data [--since-ms MS] [--out FILE]

The owner chose this on 2026-11-03 (option A of that morning's report): keep the live test exactly as
it is and judge the analyst's proposal beside it. Two rules, fixed in this file before any of the data
they are judged on (REGISTERED_MS):

  capped       skip an entry when the desk's P(yes) is more than CAP (10 points) from the market's mid
  capped_exit  the same, and never hold to expiry: sell what is still open EXIT_BEFORE_S (3 minutes)
               before the contract closes, and skip entries made with less time than that left

Both rules' in-sample results were known when they were registered (08:25 to 13:25Z: desk -20.17,
capped -6.30, capped_exit -18.84), so only trades opened from REGISTERED_MS on test them. A first
exit rule, selling a bet once its price halved, was dropped before registration (-17.16 in-sample:
these cheap contracts often halve and recover); it is not part of the test.

Everything else is the desk's own: its entry decisions and fills, its exits and settlements, and the
quotes it logged every block while holding. A shadow can only skip a trade or leave it early; it
never takes a trade the desk did not, since the desk asks Jev nothing while it holds a position. An
early sale is at the logged quote and pays Kalshi's taker fee at that price.

Trades opened before REGISTERED_MS are in-sample (the rules were chosen after seeing them); only
those from REGISTERED_MS on test the rules. Prints one line and writes JSON when --out is given.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dashboard.money import FILL_GRACE_MS, WEEK_START_MS
from kalshi.api import taker_fee_usd
from logs.writer import read_events

REGISTERED_MS = 1_793_718_900_000  # 2026-11-03T15:15:00Z: trades opened from here on test the rules
CAP = 0.10
EXIT_BEFORE_S = 180
STRATEGIES = {
    "desk": "the live desk, as traded",
    "capped": f"skip entries more than {CAP * 100:.0f} points from the market",
    "capped_exit": f"capped, and sell {EXIT_BEFORE_S // 60} minutes before the close",
}


def _positions(log_dir: str | Path, since_ms: int) -> list[dict]:
    positions: dict[str, dict] = {}
    open_on: dict[str, str] = {}
    pending_fills: dict[str, list[dict]] = {}
    entries: dict[str, dict] = {}
    entry_quotes: dict[str, dict] = {}
    path: dict[str, list[tuple[int, float, float, float | None]]] = {}  # sym -> (ts, yes_bid, yes_ask, seconds to close) while held
    for e in read_events(log_dir):
        kind, ts = e.get("kind"), e.get("ts")
        if not isinstance(ts, int) or ts < since_ms - (FILL_GRACE_MS if kind == "fill" else 0):
            continue
        did, sym = str(e.get("decision_id") or ""), str(e.get("sym") or "")
        if kind == "decision" and str(e.get("action", "")).startswith("enter") and e.get("executed"):
            entries[did] = e
        elif kind == "snapshot":
            contract = (e.get("state") or {}).get("contract") or {}
            if e.get("phase") == "entry":
                entry_quotes[did] = contract
            elif sym in open_on and contract.get("yes_bid") is not None and contract.get("yes_ask") is not None:
                left = contract.get("expires_in_s")
                path.setdefault(sym, []).append((ts, float(contract["yes_bid"]), float(contract["yes_ask"]), None if left is None else float(left)))
        elif kind == "position_opened":
            pos = e.get("position") or {}
            qty = float(pos.get("qty") or 0.0)
            yes = float(pos.get("entry_price") or 0.0)
            positions[did] = {
                "id": did, "sym": sym, "opened_ms": ts, "closed_ms": None, "sign": 1 if qty > 0 else -1, "contracts": abs(qty),
                "bet": "YES" if qty > 0 else "NO", "bet_price": yes if qty > 0 else 1.0 - yes, "entry_fee": 0.0, "gross": 0.0, "fees": 0.0,
                "result": "open", "path": [],
            }
            for f in pending_fills.pop(did, []):
                _add_fill(positions[did], f, opening=True)
            open_on[sym] = did
            path[sym] = []
        elif kind == "fill":
            owner = did if did in positions else open_on.get(sym)
            if owner is None:
                pending_fills.setdefault(did, []).append(e)  # an opening fill, logged before its position
            else:
                _add_fill(positions[owner], e, opening=False)
        elif kind == "position_closed" and did in positions:
            p = positions[did]
            p["closed_ms"] = ts
            p["result"] = "sold" if not e.get("settled") else ("won" if (float(e.get("payout") or 0.0) >= 0.5) == (p["sign"] > 0) else "lost")
            p["path"] = path.pop(sym, [])
            if open_on.get(sym) == did:
                del open_on[sym]
    for sym, did in open_on.items():
        positions[did]["path"] = path.get(sym, [])
    out = []
    for did, p in positions.items():
        decision, quote = entries.get(did), entry_quotes.get(did) or {}
        p_yes = None
        if decision is not None and isinstance(decision.get("prob"), (int, float)):
            p_yes = float(decision["prob"]) if p["sign"] > 0 else 1.0 - float(decision["prob"])
        mid = None
        if quote.get("yes_bid") is not None and quote.get("yes_ask") is not None:
            mid = (float(quote["yes_bid"]) + float(quote["yes_ask"])) / 2
        p["p_yes"], p["mid"] = p_yes, mid
        p["entry_left_s"] = None if quote.get("expires_in_s") is None else float(quote["expires_in_s"])
        p["gap"] = None if p_yes is None or mid is None else round(abs(p_yes - mid), 4)
        p["pnl"] = None if p["result"] == "open" else round(p["gross"] - p["fees"], 2)
        out.append(p)
    return out


def _add_fill(p: dict, f: dict, *, opening: bool) -> None:
    fee = float(f.get("fee_usd") or 0.0) + float(f.get("gas_usd") or 0.0)
    p["fees"] += fee
    p["gross"] += float(f.get("realized_pnl_usd") or 0.0)
    if opening:
        p["entry_fee"] += fee


def shadow_outcome(p: dict, strategy: str) -> tuple[str, float | None]:
    """(result, P&L after fees) of one desk position under a strategy; ("skipped", 0.0) when it would not have been taken."""
    if strategy == "desk":
        return p["result"], p["pnl"]
    if p["gap"] is not None and p["gap"] > CAP:
        return "skipped", 0.0
    if strategy == "capped":
        return p["result"], p["pnl"]
    if p["entry_left_s"] is not None and p["entry_left_s"] < EXIT_BEFORE_S:
        return "skipped", 0.0
    for ts, bid, ask, left in p["path"]:
        if left is not None and left <= EXIT_BEFORE_S:
            sell = bid if p["sign"] > 0 else 1.0 - ask
            pnl = p["contracts"] * (sell - p["bet_price"]) - p["entry_fee"] - taker_fee_usd(p["contracts"], sell)
            return "sold_early", round(pnl, 2)
    return p["result"], p["pnl"]


def evaluate(log_dir: str | Path, *, since_ms: int = WEEK_START_MS, registered_ms: int = REGISTERED_MS) -> dict:
    positions = _positions(log_dir, since_ms)
    report: dict = {"since_ms": since_ms, "registered_ms": registered_ms, "rules": {"cap": CAP, "exit_before_s": EXIT_BEFORE_S}, "strategies": {}, "trades": []}
    for name, label in STRATEGIES.items():
        stats = {}
        for part, keep in (("all", lambda p: True), ("in_sample", lambda p: p["opened_ms"] < registered_ms), ("test", lambda p: p["opened_ms"] >= registered_ms)):
            outcomes = [shadow_outcome(p, name) for p in positions if keep(p)]
            closed = [(r, v) for r, v in outcomes if r not in ("open", "skipped")]
            stats[part] = {
                "trades": len(closed), "open": sum(r == "open" for r, _ in outcomes), "skipped": sum(r == "skipped" for r, _ in outcomes),
                "won": sum(1 for _, v in closed if v > 0), "lost": sum(1 for _, v in closed if v <= 0),
                "sold_early": sum(r == "sold_early" for r, _ in outcomes), "pnl_usd": round(sum(v for _, v in closed), 2),
            }
        report["strategies"][name] = {"label": label, **stats}
    for p in positions:
        report["trades"].append({
            "id": p["id"], "sym": p["sym"], "opened_ms": p["opened_ms"], "bet": p["bet"], "bet_price": round(p["bet_price"], 4),
            "p_yes": p["p_yes"], "mid": p["mid"], "gap": p["gap"],
            **{name: dict(zip(("result", "pnl_usd"), shadow_outcome(p, name))) for name in STRATEGIES},
        })
    return report


def one_line(report: dict, part: str = "all") -> str:
    bits = []
    for name, s in report["strategies"].items():
        x = s[part]
        bits.append(f"{name} {x['pnl_usd']:+.2f} ({x['trades']} closed, {x['won']} up" + (f", {x['skipped']} skipped" if x["skipped"] else "") + (f", {x['sold_early']} sold 3 min before the close" if x["sold_early"] else "") + ")")
    return " | ".join(bits)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The paper desk beside its shadow strategies")
    parser.add_argument("--log-dir", default="logs/data")
    parser.add_argument("--since-ms", type=int, default=WEEK_START_MS)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = evaluate(args.log_dir, since_ms=args.since_ms)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(f"shadow (since the week began): {one_line(report, 'all')}")
    print(f"shadow (test, trades opened from the rules' registration on): {one_line(report, 'test')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
