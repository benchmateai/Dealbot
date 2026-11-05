"""A, the control: the repaired 15-minute model, anchored on the market price, trading as a taker only when its
fitted weight says the model adds anything to the price.

It replays the paper desk's per-block tape (paper-run branch) through policy/anchored.py's forecaster, the
same class the paper desk trades from v2 on (2026-11-05), so this replay and the desk cannot drift apart.
The model: the
probability that the sixty-second settlement average ends at or above the strike, with variance from an
exponentially weighted volatility (30-minute half-life) instead of the desk's 4-minute window, the part
of the average already fixed counted inside the last minute, and Coinbase's spot corrected toward the
settlement index by the median gap seen on recent settled contracts (from the lab's settlement values).

The forecast is q = pool(market mid, model, w): the market price moved toward the model by a weight w
fitted on resolved forecasts only (walk-forward), and held at zero until MIN_ROWS of them exist. With
w = 0 the strategy never trades, which is the expected answer in a calibrated market. It scores the
market, the repaired model, the desk's own formula and q at fixed horizons before each close, and
trades 10 contracts at the displayed price, net of Kalshi's taker fee, when q clears the same edge bar
the desk uses (1.5 x the fee plus half the spread). Trades count from REGISTERED_MS on.

    python -m lab.strategies.a_control --tape <paper-run copy>/logs/data --lab lab/data
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kalshi.api import taker_fee_usd
from lab.store import read_lab
from logs.writer import read_events
from policy.anchored import HORIZONS_S, MIN_ROWS, TRADE_WINDOW_S, AnchoredForecaster, brier, log_loss

REGISTERED_MS = 1_793_739_600_000  # 2026-11-03T21:00:00Z
CONTRACTS = 10
MARGIN = 0.5


def _min_edge(price: float, spread: float) -> float:
    return (1 + MARGIN) * (taker_fee_usd(1, price) + spread / 2)


def evaluate(tape_dir: str | Path, lab_dir: str | Path | None = None, *, since_ms: int = 0, registered_ms: int = REGISTERED_MS) -> dict:
    timeline: list[tuple[int, int, dict]] = []  # (ts, order, record): settlements sort before a same-time tape
    for e in read_events(tape_dir):
        ts = e.get("ts")
        if not isinstance(ts, int) or ts < since_ms:
            continue
        if e.get("kind") == "tape":
            timeline.append((ts, 1, e))
        elif e.get("kind") == "settlement" and e.get("ticker"):
            timeline.append((ts, 0, e))
    if lab_dir:
        for r in read_lab(lab_dir, since_ms=since_ms, kinds=("settled",)):
            if r.get("series") in ("KXBTC15M", "KXETH15M"):
                timeline.append((r["ts"], 0, {**r, "kind": "lab_settled"}))
    timeline.sort(key=lambda t: (t[0], t[1]))

    fc = AnchoredForecaster()  # the paper desk's own forecaster (v2), here also fed the lab's settlement values
    positions: dict[str, dict] = {}

    for ts, _, e in timeline:
        if e["kind"] == "settlement":
            t = e["ticker"]
            y = fc.observe_settlement(t, e.get("payout"))
            if y is None:
                continue
            pos = positions.get(t)
            if pos and pos["result"] is None:
                won = (y == 1) == (pos["side"] == "YES")
                pos["result"] = "won" if won else "lost"
                pos["pnl"] = round(CONTRACTS * ((1.0 if won else 0.0) - pos["price"]) - pos["fee"], 2)
            continue
        if e["kind"] == "lab_settled":
            for ticker, result, value in e.get("rows") or []:
                fc.observe_settlement_value(ticker, value)
            continue
        for sym, f in fc.observe_tape(ts, e.get("contracts") or {}).items():
            ticker, tau = f["ticker"], f["tau"]
            if ts < registered_ms or ticker in positions or not TRADE_WINDOW_S[0] <= tau <= TRADE_WINDOW_S[1] or fc.weight == 0.0:
                continue
            q, bid, ask = f["q"], f["bid"], f["ask"]
            spread = ask - bid
            if q - ask >= _min_edge(ask, spread):
                positions[ticker] = {"ticker": ticker, "ts": ts, "side": "YES", "price": ask, "fee": taker_fee_usd(CONTRACTS, ask), "q": round(q, 4), "result": None, "pnl": None}
            elif (1 - q) - (1 - bid) >= _min_edge(1 - bid, spread):
                positions[ticker] = {"ticker": ticker, "ts": ts, "side": "NO", "price": 1 - bid, "fee": taker_fee_usd(CONTRACTS, 1 - bid), "q": round(q, 4), "result": None, "pnl": None}

    resolved_rows = fc.resolved_rows
    scores = {}
    for h in HORIZONS_S:
        rows = [r for r in resolved_rows if r["h"] == h]
        if not rows:
            continue
        def mean(f):
            return round(sum(f(r) for r in rows) / len(rows), 4)
        desk_rows = [r for r in rows if r["desk"] is not None]
        scores[str(h)] = {
            "n": len(rows),
            "brier": {"market": mean(lambda r: brier(r["m"], r["y"])), "model": mean(lambda r: brier(r["p"], r["y"]))},
            "log_loss": {"market": mean(lambda r: log_loss(r["m"], r["y"])), "model": mean(lambda r: log_loss(r["p"], r["y"]))},
            "desk_formula_brier": round(sum(brier(r["desk"], r["y"]) for r in desk_rows) / len(desk_rows), 4) if desk_rows else None,
        }
    closed = [p for p in positions.values() if p["result"]]
    summary = {
        "resolved_forecasts": len(resolved_rows), "weight": round(fc.weight, 3), "weight_active": len(resolved_rows) >= MIN_ROWS,
        "weight_fit_log_loss": None if fc.weight_loss is None else round(fc.weight_loss, 4), "corr_bps": {s: round(fc.corr_bps(s), 2) for s in fc.gaps},
        "scores": scores, "trades": len(closed), "open": len(positions) - len(closed), "won": sum(p["result"] == "won" for p in closed),
        "pnl_usd": round(sum(p["pnl"] for p in closed), 2),
    }
    return {"summary": summary, "trades": sorted(positions.values(), key=lambda p: p["ts"])}


def one_line(s: dict) -> str:
    h60 = s["scores"].get("60") or {}
    ll = h60.get("log_loss") or {}
    w = f"weight {s['weight']}" if s["weight_active"] else f"weight 0 until {MIN_ROWS} resolved forecasts ({s['resolved_forecasts']} so far)"
    return (f"A control: {w}; 1 minute out log loss market {ll.get('market')} vs repaired model {ll.get('model')} (n={h60.get('n', 0)}); "
            f"{s['trades']} trades, {s['pnl_usd']:+.2f} USD after fees")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The repaired model as a market-anchored control")
    parser.add_argument("--tape", required=True, help="the paper desk's log directory (paper-run logs/data)")
    parser.add_argument("--lab", default="lab/data")
    parser.add_argument("--since-ms", type=int, default=0)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    report = evaluate(args.tape, args.lab, since_ms=args.since_ms)
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1))
    print(one_line(report["summary"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
