"""Step 5: simulate copies at each delay and size from cached price paths; write per-copy CSV + summary.
usage: s5_sim.py events.json out_dir"""
import json, os, sys, csv, statistics, math
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from swaps import VENUE_FEE
D = os.environ["CT_DATA"]
SLOT_S = float(os.environ.get("SLOT_SECONDS", "0.2133"))
PRIO_SOL = float(os.environ.get("PRIO_SOL", "0.0005"))    # priority fee + tip per copier transaction
SIZES = [100.0, 1000.0]
DELAYS = [("zero_theoretical", 0), ("next_slot", 1), ("0.4s", round(0.4 / SLOT_S)), ("1s", round(1 / SLOT_S)),
          ("5s", round(5 / SLOT_S)), ("30s", round(30 / SLOT_S))]
# SOL/USD from the Orca SOL-USDC pool (median of swaps in the first hour of each date)
SOLPTS = [(1792540800, 106.40), (1793145600, 101.23), (1793750400, 92.76)]
def solusd(t):
    for (t0, p0), (t1, p1) in zip(SOLPTS, SOLPTS[1:]):
        if t <= t1: return p0 + (p1 - p0) * (max(t, t0) - t0) / (t1 - t0)
    return SOLPTS[-1][1]
def fee(v): return VENUE_FEE.get(v, VENUE_FEE["other"])

def state(win, target, fallback):
    """Pool state a copier landing in slot `target` trades against: pre-trade state of the first real
    swap at/after `target`, else (no later swap in a non-truncated window) the last state before it."""
    sw = sorted(win["swaps"], key=lambda s: (s["slot"], s["idx"]))
    after = [s for s in sw if s["slot"] >= target]
    if after:
        s = after[0]; return {"p": s["p0"], "y": s["y_pre"], "venue": s["venue"], "quote": s["quote"], "lag_slots": s["slot"] - target}
    covered = any(not p["full"] for p in win["pages"])
    if not covered:
        return None
    before = [s for s in sw if s["slot"] < target]
    s = before[-1] if before else fallback
    if s is None: return None
    return {"p": s["p_post"], "y": s["y_post"], "venue": s["venue"], "quote": s["quote"], "lag_slots": None}

def buy_fill(X, st, f):      # X quote in -> tokens out, constant-product with reserve y
    net = X * (1 - f); return (st["y"] / st["p"]) * net / (st["y"] + net)
def sell_fill(q, st, f):     # q tokens in -> quote out
    return st["y"] * q * st["p"] / (st["y"] + q * st["p"]) * (1 - f)

def conv(amount, frm, to, t):
    if frm == to: return amount
    return amount * solusd(t) if frm == "SOL" else amount / solusd(t)

def simulate(ev, P):
    whale_state = {"slot": ev["slot"], "idx": ev["idx"], "p_post": None, "y_post": ev["y_post"], "venue": ev["venue"], "quote": ev["quote"]}
    yp = ev["y_post"]; dy = ev["pool_quote"]; ypre = yp - dy
    if ypre > 0:
        p0 = ev["pool_price"] * ypre / yp; whale_state["p_post"] = p0 * (yp / ypre) ** 2
    else:
        whale_state = None
    m24 = P.get("m24")
    m24st = None
    if m24:
        if m24["how"] == "first_after": m24st = {"p": m24["p0"], "y": m24["y_pre"], "venue": m24["venue"], "quote": m24["quote"]}
        else: m24st = {"p": m24["p_post"], "y": m24["y_post"], "venue": m24["venue"], "quote": m24["quote"]}
    t24 = ev["time"] + 86400
    exits = {e["sig"]: e for e in P["exits"]}
    rows = []
    # whale benchmark (all-in fills from its own balance changes)
    wtok = ev["tokens"]; wcost = ev["quote_amt"]; wproc = 0.0; wrem = wtok
    for s in ev["sells"]:
        sold = wrem * s["frac"]; wproc += conv(s["quote_amt"] * sold / s["tokens"], s["quote"], ev["quote"], s["time"]); wrem -= sold
    wmark = None
    if m24st and wrem > 0:
        y = conv(m24st["y"], m24st["quote"], ev["quote"], t24); p = conv(m24st["p"], m24st["quote"], ev["quote"], t24)
        wmark = sell_fill(wrem, {"y": y, "p": p}, fee(m24st["venue"]))
    whale_ret = (wproc + (wmark or 0.0) - wcost) / wcost if (wmark is not None or wrem <= 1e-12) else None
    whale_p24_ratio = (conv(m24st["p"], m24st["quote"], ev["quote"], t24) / ev["pool_price"]) if m24st else None
    for dname, dslots in DELAYS:
        if dslots == 0:   # impossible benchmark: trade against the same pool state the whale saw
            st = {"p": ev["pool_price"] * ypre / yp, "y": ypre, "venue": ev["venue"], "quote": ev["quote"], "lag_slots": 0} if ypre > 0 else None
            xs_delay = 0
        else:
            st = state(P["entry"], ev["slot"] + dslots, whale_state)
        for usd in SIZES:
            base = {"id": ev["id"], "whale": ev["whale"], "mint": ev["mint"], "buy_sig": ev["sig"], "buy_slot": ev["slot"],
                    "buy_time": ev["time"], "venue": ev["venue"], "via_jupiter": ev["via_jupiter"], "quote": ev["quote"],
                    "whale_buy_quote": round(ev["quote_amt"], 6), "whale_fill_price": ev["whale_price"],
                    "whale_pool_price": ev["pool_price"], "n_whale_sells_24h": len(ev["sells"]),
                    "whale_return": None if whale_ret is None else round(whale_ret, 5),
                    "delay": dname, "size_usd": usd, "status": "ok"}
            if st is None:
                rows.append({**base, "status": "no_entry_price"}); continue
            q = ev["quote"]; prio = conv(PRIO_SOL, "SOL", q, ev["time"])
            X = conv(usd, "SOL", q, ev["time"]) if q == "SOL" else usd
            X = usd / solusd(ev["time"]) if q == "SOL" else usd
            tok = buy_fill(X, st, fee(st["venue"])); cost = X + prio
            entry_px = X / tok
            res = {}
            for tag, xd in (("main", dslots), ("exit0", 0)):
                rem = tok; proc = 0.0; missing_exit = 0
                for s in ev["sells"]:
                    e = exits.get(s["sig"])
                    xs = state(e, s["slot"] + xd, None) if e else None
                    if xs is None:
                        missing_exit += 1; continue
                    y = conv(xs["y"], xs["quote"], q, s["time"]); p = conv(xs["p"], xs["quote"], q, s["time"])
                    qsell = rem * s["frac"]
                    out = sell_fill(qsell, {"y": y, "p": p}, fee(xs["venue"])) - prio
                    proc += out; rem -= qsell
                mark = None
                if rem > 0 and m24st:
                    y = conv(m24st["y"], m24st["quote"], q, t24); p = conv(m24st["p"], m24st["quote"], q, t24)
                    mark = max(0.0, sell_fill(rem, {"y": y, "p": p}, fee(m24st["venue"])) - prio)
                res[tag] = (rem, proc, mark, missing_exit)
            rem, proc, mark, missing_exit = res["main"]
            if rem > 1e-9 * tok and m24st is None:
                rows.append({**base, "status": "no_24h_price", "entry_price": entry_px}); continue
            ret = (proc + (mark or 0.0) - cost) / cost
            r0 = res["exit0"]; ret_exit0 = (r0[1] + (r0[2] or 0.0) - cost) / cost
            p24 = conv(m24st["p"], m24st["quote"], q, t24) if m24st else None
            rows.append({**base, "entry_price": entry_px, "entry_vs_whale_pool_price": entry_px / ev["pool_price"] - 1,
                         "entry_lag_slots": st["lag_slots"], "copier_tokens": tok, "held_to_24h_frac": rem / tok,
                         "missing_exit_windows": missing_exit,
                         "p24_vs_entry": (p24 / entry_px) if p24 else None,
                         "went_to_zero": (p24 / entry_px <= 0.10) if p24 else None,
                         "return": round(ret, 5), "pnl_usd": round(ret * usd, 3),
                         "return_if_exit_at_whale_sell_price": round(ret_exit0, 5)})
    return rows

def summarize(rows):
    out = []
    for dname, _ in DELAYS:
        for usd in SIZES:
            rs = [r for r in rows if r["delay"] == dname and r["size_usd"] == usd and r["status"] == "ok"]
            if not rs: continue
            R = [r["return"] for r in rs]; W = [r["whale_return"] for r in rs if r["whale_return"] is not None]
            z = [r for r in rs if r["went_to_zero"] is not None]
            out.append({"delay": dname, "size_usd": usd, "copies": len(rs),
                        "win_rate": sum(x > 0 for x in R) / len(R), "median_return": statistics.median(R),
                        "mean_return": statistics.fmean(R), "total_pnl_usd": sum(r["pnl_usd"] for r in rs),
                        "went_to_zero_share": sum(r["went_to_zero"] for r in z) / len(z) if z else None,
                        "whale_median_return": statistics.median(W) if W else None,
                        "whale_mean_return": statistics.fmean(W) if W else None,
                        "whale_win_rate": sum(x > 0 for x in W) / len(W) if W else None,
                        "median_return_exit_at_whale_price": statistics.median(r["return_if_exit_at_whale_sell_price"] for r in rs),
                        "mean_return_exit_at_whale_price": statistics.fmean(r["return_if_exit_at_whale_sell_price"] for r in rs),
                        "whale_total_pnl_sol": None,
                        "median_entry_premium": statistics.median(r["entry_vs_whale_pool_price"] for r in rs)})
    return out

if __name__ == "__main__":
    evs = json.load(open(sys.argv[1])); od = sys.argv[2]; os.makedirs(od, exist_ok=True)
    rows = []; nopath = 0
    for ev in evs:
        fn = os.path.join(D, "paths", ev["id"] + ".json")
        if not os.path.exists(fn): nopath += 1; continue
        rows += simulate(ev, json.load(open(fn)))
    keys = []
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with open(os.path.join(od, "per_copy_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    summ = summarize(rows)
    st = defaultdict(int)
    for r in rows: st[(r["delay"], r["size_usd"], r["status"])] += 1
    json.dump({"summary": summ, "events": len(evs), "events_without_paths": nopath,
               "status_counts": {f"{a}|{b}|{c}": n for (a, b, c), n in st.items()}}, open(os.path.join(od, "summary.json"), "w"), indent=1)
    for s in summ: print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()})
