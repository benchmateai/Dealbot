"""Step 1: screen KOLScan seed wallets for selection-week activity (signatures only, 10 credits/page)."""
import json, os, sys, concurrent.futures as cf
import helius as h
D = os.environ["CT_DATA"]
SEL0, SEL1 = 1792540800, 1793145600  # 2026-10-21, 2026-10-28 UTC
seed = json.load(open(sys.argv[1]))
out = {}
def work(w):
    n = 0
    for _ in h.gtfa(w["address"], SEL0, SEL1, details="signatures", max_pages=3):
        n += 1
    return w["address"], n
with cf.ThreadPoolExecutor(6) as ex:
    for a, n in ex.map(work, seed):
        out[a] = n
json.dump(out, open(os.path.join(D, "screen.json"), "w"))
print("done", len(out), "credits", h.credits_used())
