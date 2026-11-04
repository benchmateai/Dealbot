"""Step 3: realized selection-week P&L per wallet (average-cost method, SOL), pick the top 20.
Sells of tokens bought before the window have no known cost and are left out of realized P&L."""
import json, os, sys, glob, statistics
from collections import defaultdict
D = os.environ["CT_DATA"]; sw = os.path.join(D, "sel_swaps")
SOLUSD = float(os.environ.get("SOLUSD", "190"))
seed = {s["address"]: s for s in json.load(open(os.path.join(D, "seed.json")))}
rows = []
for fn in glob.glob(os.path.join(sw, "*.jsonl")):
    a = os.path.basename(fn)[:-6]
    meta = json.load(open(fn[:-6] + ".meta"))
    recs = sorted((json.loads(l) for l in open(fn)), key=lambda r: (r["slot"], r["idx"]))
    pos = defaultdict(lambda: [0.0, 0.0])  # mint -> [tokens, cost SOL]
    realized = 0.0; nb = ns = 0; matched_sells = 0; vol = 0.0; mints = set()
    for r in recs:
        q = r["quote_amt"] if r["quote"] == "SOL" else r["quote_amt"] / SOLUSD
        p = pos[r["mint"]]; vol += q
        if r["side"] == "buy":
            nb += 1; p[0] += r["tokens"]; p[1] += q; mints.add(r["mint"])
        else:
            ns += 1
            if p[0] <= 0: continue
            sold = min(r["tokens"], p[0]); frac = sold / p[0]
            cost = p[1] * frac
            realized += q * (sold / r["tokens"]) - cost
            p[0] -= sold; p[1] -= cost; matched_sells += 1
    s = seed.get(a, {})
    rows.append({"address": a, "name": s.get("name"), "twitter": s.get("twitter"), "source": s.get("source"),
                 "sel_txs": meta["txs"], "sel_truncated": meta["truncated"], "sel_buys": nb, "sel_sells": ns,
                 "sel_matched_sells": matched_sells, "sel_tokens": len(mints), "sel_volume_sol": round(vol, 3),
                 "sel_realized_pnl_sol": round(realized, 4), "sel_realized_pnl_usd": round(realized * SOLUSD, 2)})
rows.sort(key=lambda r: -r["sel_realized_pnl_sol"])
elig = [r for r in rows if r["sel_buys"] + r["sel_sells"] >= 10 and r["sel_buys"] >= 1]
top = elig[:20]
for i, r in enumerate(rows):
    r["selected"] = r in top
json.dump(rows, open(os.path.join(D, "selection_pnl.json"), "w"), indent=1)
json.dump([r["address"] for r in top], open(os.path.join(D, "top20.json"), "w"))
print(len(rows), "wallets,", len(elig), "with >=10 trades")
for r in top: print(r["name"], r["address"][:8], r["sel_buys"], r["sel_sells"], r["sel_realized_pnl_sol"], r["sel_truncated"])
