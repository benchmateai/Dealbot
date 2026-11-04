"""Build copy events: every test-week buy by the top-20 wallets (bought before Nov 3 00:00 UTC so a full
24 h follow-up exists), with that wallet's sells of the token in the next 24 h.
usage: s4_events.py test_swaps_dir out.json [max_events]"""
import json, os, sys, glob, random
from collections import defaultdict
TEST0, LAST_BUY = 1793145600, 1793664000
d, outp = sys.argv[1], sys.argv[2]; cap = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
evs = []; stats = defaultdict(int)
for fn in glob.glob(os.path.join(d, "*.jsonl")):
    w = os.path.basename(fn)[:-6]
    recs = sorted((json.loads(l) for l in open(fn)), key=lambda r: (r["slot"], r["idx"]))
    by = defaultdict(list)
    for r in recs: by[r["mint"]].append(r)
    for r in recs:
        if r["side"] != "buy": continue
        stats["buys_all"] += 1
        if not (TEST0 <= r["time"] < LAST_BUY): stats["buys_after_nov3"] += 1; continue
        if not r.get("pool_vault") or not r.get("pool_price"): stats["no_pool"] += 1; continue
        sells = []
        for s in by[r["mint"]]:
            if s["side"] == "sell" and (s["slot"], s["idx"]) > (r["slot"], r["idx"]) and s["time"] <= r["time"] + 86400:
                frac = s["tokens"] / (s["trader_post_tokens"] + s["tokens"])
                sells.append({"sig": s["sig"], "slot": s["slot"], "idx": s["idx"], "time": s["time"],
                              "vault": s.get("pool_vault"), "venue": s["venue"], "frac": min(1.0, frac),
                              "tokens": s["tokens"], "quote": s["quote"], "quote_amt": s["quote_amt"]})
        evs.append({"id": r["sig"][:24], "whale": w, "sig": r["sig"], "slot": r["slot"], "idx": r["idx"],
                    "time": r["time"], "mint": r["mint"], "venue": r["venue"], "via_jupiter": r["via_jupiter"],
                    "vault": r["pool_vault"], "quote": r["quote"], "quote_amt": r["quote_amt"],
                    "tokens": r["tokens"], "whale_price": r["trader_price"], "pool_price": r["pool_price"],
                    "pool_quote": r["pool_quote"], "y_post": r["pool_quote_reserve_post"],
                    "whale_post_tokens": r["trader_post_tokens"], "sells": sells})
stats["eligible"] = len(evs)
random.seed(7); random.shuffle(evs)
evs = evs[:cap]; stats["sampled"] = len(evs)
json.dump(evs, open(outp, "w"))
print(dict(stats))
