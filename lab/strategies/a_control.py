"""A, the control: the repaired 15-minute model, anchored on the market price, trading as a taker only when its
fitted weight says the model adds anything to the price.

It replays the paper desk's per-block tape (paper-run branch). The model is lab/model.py's: the
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
import math
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

from kalshi.api import taker_fee_usd
from lab.model import EwmaVol, brier, fit_weight, log_loss, p_contract, pool
from lab.store import read_lab
from logs.writer import read_events

REGISTERED_MS = 1_793_739_600_000  # 2026-11-03T21:00:00Z
HORIZONS_S = (420, 300, 180, 60)
MIN_ROWS = 300
REFIT_EVERY = 25
CONTRACTS = 10
MARGIN = 0.5
STALE_QUOTE_MS = 24_000
CORR_WINDOW = 50
TRADE_WINDOW_S = (60, 600)


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

    vols: dict[str, EwmaVol] = defaultdict(EwmaVol)
    gaps: dict[str, list[float]] = defaultdict(list)       # sym -> recent (settlement value - Coinbase) in bps
    window_spots: dict[str, list[float]] = defaultdict(list)  # ticker -> log spots seen in its last minute
    sym_of: dict[str, str] = {}
    pending_rows: dict[str, list[dict]] = defaultdict(list)  # ticker -> horizon rows awaiting the outcome
    recorded: set[tuple[str, int]] = set()
    resolved_rows: list[dict] = []
    outcomes: dict[str, int] = {}
    weight, weight_loss, last_fit_n = 0.0, None, 0
    positions: dict[str, dict] = {}
    trades: list[dict] = []

    def corr_bps(sym: str) -> float:
        g = gaps[sym][-CORR_WINDOW:]
        return median(g) if g else 0.0

    for ts, _, e in timeline:
        if e["kind"] == "settlement":
            t = e["ticker"]
            if t in outcomes:
                continue
            y = 1 if float(e.get("payout") or 0.0) >= 0.5 else 0
            outcomes[t] = y
            for row in pending_rows.pop(t, []):
                resolved_rows.append({**row, "y": y})
            pos = positions.get(t)
            if pos and pos["result"] is None:
                won = (y == 1) == (pos["side"] == "YES")
                pos["result"] = "won" if won else "lost"
                pos["pnl"] = round(CONTRACTS * ((1.0 if won else 0.0) - pos["price"]) - pos["fee"], 2)
            if len(resolved_rows) >= MIN_ROWS and len(resolved_rows) - last_fit_n >= REFIT_EVERY:
                weight, weight_loss = fit_weight((r["m"], r["p"], r["y"]) for r in resolved_rows)
                last_fit_n = len(resolved_rows)
            continue
        if e["kind"] == "lab_settled":
            for ticker, result, value in e.get("rows") or []:
                sym = sym_of.get(ticker)
                spots = window_spots.pop(ticker, None)
                if sym and value and spots:
                    gaps[sym].append(1e4 * (math.log(float(value)) - sum(spots) / len(spots)))
            continue
        for sym, c in (e.get("contracts") or {}).items():
            spot, ticker, tau = c.get("spot"), c.get("ticker"), c.get("expires_in_s")
            if not spot or not ticker or tau is None:
                continue
            vols[sym].update(ts, float(spot))
            sym_of[ticker] = sym
            log_spot = math.log(float(spot))
            if tau <= 60:
                window_spots[ticker].append(log_spot)
            bid, ask, qts = c.get("yes_bid"), c.get("yes_ask"), c.get("quote_ts")
            if bid is None or ask is None or qts is None or ts - qts > STALE_QUOTE_MS or not 0 < bid <= ask < 1 or tau <= 0:
                continue
            adj_spot = float(spot) * math.exp(corr_bps(sym) / 1e4)
            obs = window_spots[ticker]
            obs_mean = (sum(obs) / len(obs) + corr_bps(sym) / 1e4) if (tau < 60 and obs) else None
            p = p_contract(c.get("strike_type") or "greater_or_equal", c.get("strike"), None, adj_spot, float(tau), vols[sym].s2_per_s, observed_log_mean=obs_mean)
            if p is None:
                continue
            m = (bid + ask) / 2
            for h in HORIZONS_S:
                if (ticker, h) not in recorded and h - 24 < tau <= h:
                    recorded.add((ticker, h))
                    pending_rows[ticker].append({"ticker": ticker, "sym": sym, "h": h, "ts": ts, "m": m, "p": p, "desk": c.get("model_p_yes")})
            if ts < registered_ms or ticker in positions or not TRADE_WINDOW_S[0] <= tau <= TRADE_WINDOW_S[1] or weight == 0.0:
                continue
            q = pool(m, p, weight)
            spread = ask - bid
            if q - ask >= _min_edge(ask, spread):
                positions[ticker] = {"ticker": ticker, "ts": ts, "side": "YES", "price": ask, "fee": taker_fee_usd(CONTRACTS, ask), "q": round(q, 4), "result": None, "pnl": None}
            elif (1 - q) - (1 - bid) >= _min_edge(1 - bid, spread):
                positions[ticker] = {"ticker": ticker, "ts": ts, "side": "NO", "price": 1 - bid, "fee": taker_fee_usd(CONTRACTS, 1 - bid), "q": round(q, 4), "result": None, "pnl": None}

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
        "resolved_forecasts": len(resolved_rows), "weight": round(weight, 3), "weight_active": len(resolved_rows) >= MIN_ROWS,
        "weight_fit_log_loss": None if weight_loss is None else round(weight_loss, 4), "corr_bps": {s: round(corr_bps(s), 2) for s in gaps},
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
