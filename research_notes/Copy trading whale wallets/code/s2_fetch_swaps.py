"""Step 2/3: fetch a wallet's full transactions in a window and keep only its own swaps.
usage: s2_fetch_swaps.py wallets.json START END outdir [max_pages]"""
import json, os, sys, concurrent.futures as cf
import helius as h, swaps
wallets = json.load(open(sys.argv[1])); S, E = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]
maxp = int(sys.argv[5]) if len(sys.argv) > 5 else 150
os.makedirs(out, exist_ok=True)
def work(a):
    try:
        return _work(a)
    except Exception as e:
        return a, "ERR", str(e)[:120]
def _work(a):
    fn = os.path.join(out, a + ".jsonl")
    if os.path.exists(fn):
        return a, -1, -1
    n = k = 0; recs = []; truncated = False
    pages = 0
    for t in h.gtfa(a, S, E, details="full", max_pages=maxp):
        n += 1
        r = swaps.parse(t, trader=a)
        if r:
            recs.append(r); k += 1
    truncated = n >= maxp * 100
    with open(fn + ".tmp", "w") as f:
        for r in recs: f.write(json.dumps(r) + "\n")
    os.rename(fn + ".tmp", fn)
    json.dump({"txs": n, "swaps": k, "truncated": truncated}, open(os.path.join(out, a + ".meta"), "w"))
    return a, n, k
with cf.ThreadPoolExecutor(int(os.environ.get("THREADS","6"))) as ex:
    for a, n, k in ex.map(work, wallets):
        print(a, n, k, "credits", h.credits_used(), flush=True)
print("done")
