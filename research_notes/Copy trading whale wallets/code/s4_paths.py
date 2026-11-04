"""Step 4: for every sampled test-week whale buy, fetch the pool's swaps right after the buy, after each
whale sell of that token (within 24 h), and around the 24-hour mark. Results cached on disk.
usage: s4_paths.py events.json"""
import json, os, sys, hashlib, concurrent.futures as cf
import helius as h, swaps
D = os.environ["CT_DATA"]; C = os.path.join(D, "cache"); os.makedirs(C, exist_ok=True)
SLOT_S = float(os.environ.get("SLOT_SECONDS", "0.2133"))
DELAYS = [("next_slot", None), ("0.4s", 0.4), ("1s", 1.0), ("5s", 5.0), ("30s", 30.0)]

def compact(r):
    if not r or not r.get("pool_price") or not r.get("pool_quote_reserve_post"):
        return None
    y_post = r["pool_quote_reserve_post"]; dy = r["pool_quote"]
    y_pre = y_post - dy if r["side"] == "buy" else y_post + dy
    if y_pre <= 0: return None
    p0 = r["pool_price"] * y_pre / y_post
    return {"slot": r["slot"], "idx": r["idx"], "time": r["time"], "side": r["side"], "mint": r["mint"],
            "venue": r["venue"], "quote": r["quote"], "p0": p0, "y_pre": y_pre,
            "p_post": p0 * (y_post / y_pre) ** 2, "y_post": y_post, "txfee": r["txfee"],
            "size_q": dy, "vault": r.get("pool_vault")}

def page(addr, mint, **kw):
    key = hashlib.sha1(json.dumps([addr, mint, kw], sort_keys=True).encode()).hexdigest()
    fn = os.path.join(C, key + ".json")
    if os.path.exists(fn):
        return json.load(open(fn))
    out = []; last_slot = None; n = 0
    for t in h.gtfa(addr, max_pages=1, **kw):
        n += 1; last_slot = t["slot"]
        r = swaps.parse(t)
        if r and r["mint"] == mint:
            c = compact(r)
            if c: out.append(c)
    res = {"swaps": out, "n": n, "last_slot": last_slot, "full": n >= kw.get("limit", 100)}
    json.dump(res, open(fn, "w"))
    return res

def window(vault, mint, slot):
    """Swaps on this pool from `slot` until the 30 s target is covered (at most 4 pages)."""
    targets = [slot + 1, slot + round(0.4 / SLOT_S), slot + round(1 / SLOT_S), slot + round(5 / SLOT_S), slot + round(30 / SLOT_S)]
    allsw = []; start = slot; pages = []
    for _ in range(4):
        p = page(vault, mint, slot_gte=start, limit=100, sort="asc")
        pages.append({"from": start, "last": p["last_slot"], "full": p["full"]})
        allsw += p["swaps"]
        if not p["full"] or p["last_slot"] is None:
            break
        nxt = [t for t in targets if t > p["last_slot"]]
        if not nxt:
            break
        start = nxt[0]
    return {"swaps": allsw, "pages": pages, "targets": targets}

def mark24(mint, vault, t24):
    """Pool state at t+24h: first swap of the token at/after t24 (within 2 h), else last swap before."""
    for addr in [mint, vault]:
        if not addr: continue
        a = page(addr, mint, gte=t24, lt=t24 + 7200, limit=40, sort="asc")
        if a["swaps"]:
            s = a["swaps"][0]; return {"how": "first_after", "addr": addr, **s}
        b = page(addr, mint, lt=t24, gte=t24 - 86400, limit=40, sort="desc")
        if b["swaps"]:
            s = b["swaps"][0]; return {"how": "last_before", "addr": addr, **s}
    return None

def work(ev):
    try:
        return _work(ev)
    except Exception as e:
        return ev["id"], "ERR " + str(e)[:100]

def _work(ev):
    fn = os.path.join(D, "paths", ev["id"] + ".json")
    if os.path.exists(fn): return ev["id"], "cached"
    out = {"id": ev["id"], "entry": window(ev["vault"], ev["mint"], ev["slot"]), "exits": [], "m24": None}
    for s in ev["sells"]:
        if s.get("vault"):
            out["exits"].append({"sig": s["sig"], **window(s["vault"], ev["mint"], s["slot"])})
    out["m24"] = mark24(ev["mint"], ev["vault"], ev["time"] + 86400)
    json.dump(out, open(fn + ".tmp", "w")); os.rename(fn + ".tmp", fn)
    return ev["id"], "ok"

if __name__ == "__main__":
    os.makedirs(os.path.join(D, "paths"), exist_ok=True)
    evs = json.load(open(sys.argv[1]))
    budget = float(os.environ.get("CREDIT_CAP", "700000"))
    with cf.ThreadPoolExecutor(int(os.environ.get("THREADS", "6"))) as ex:
        futs = []
        for i, (eid, st) in enumerate(ex.map(work, evs)):
            if i % 50 == 0:
                print(i, eid, st, "credits", h.credits_used(), flush=True)
            if h.credits_used() > budget:
                print("credit cap reached", flush=True); os._exit(2)
    print("done credits", h.credits_used())
