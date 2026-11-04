"""Markdown tables for the report from per_copy_results.csv, events and test-week swaps."""
import csv, json, os, glob, statistics as st
from collections import defaultdict
D = os.environ["CT_DATA"]; R = os.environ["RES"]
rows = [r for r in csv.DictReader(open(os.path.join(R, "per_copy_results.csv"))) if r["status"] == "ok"]
for r in rows:
    for k in ("return", "pnl_usd", "size_usd", "return_if_exit_at_whale_sell_price", "entry_vs_whale_pool_price", "whale_buy_quote", "held_to_24h_frac"):
        r[k] = float(r[k]) if r.get(k) not in (None, "") else None
    r["whale_return"] = float(r["whale_return"]) if r["whale_return"] else None
    r["went_to_zero"] = r["went_to_zero"] == "True"
evs = {e["id"]: e for e in json.load(open(os.path.join(D, "events.json")))}
names = {r["address"]: r["name"] for r in json.load(open(os.path.join(D, "selection_pnl.json")))}
sel = {r["address"]: r for r in json.load(open(os.path.join(D, "selection_pnl.json")))}
DL = ["zero_theoretical", "next_slot", "0.4s", "1s", "5s", "30s"]
LBL = {"zero_theoretical": "0 (whale's own price, impossible)", "next_slot": "next slot (~0.2 s)", "0.4s": "0.4 s", "1s": "1 s", "5s": "5 s", "30s": "30 s"}
pct = lambda x: f"{x*100:+.1f}%" if x is not None else "n/a"
out = []
def P(s=""): out.append(s)

P("### Main results"); P()
P("| Delay | Size | Copies | Win rate | Median return | Mean return | Total P&L | Went to zero | Whale median / mean on same trades |")
P("|---|---|---|---|---|---|---|---|---|")
for d in DL:
    for z in (100.0, 1000.0):
        rs = [r for r in rows if r["delay"] == d and r["size_usd"] == z]
        R_ = [r["return"] for r in rs]; W = [r["whale_return"] for r in rs if r["whale_return"] is not None]
        P(f"| {LBL[d]} | ${z:,.0f} | {len(rs)} | {sum(x>0 for x in R_)/len(R_)*100:.0f}% | {pct(st.median(R_))} | {pct(st.fmean(R_))} | ${sum(r['pnl_usd'] for r in rs):,.0f} | {sum(r['went_to_zero'] for r in rs)/len(rs)*100:.0f}% | {pct(st.median(W))} / {pct(st.fmean(W))} |")
P()
P("### Where the loss comes from ($100 copies)"); P()
P("| Delay | Median entry price vs whale's fill | Mean return | Mean return if the exit were at the whale's own sell price | Cost of being late on the exit |")
P("|---|---|---|---|---|")
for d in DL:
    rs = [r for r in rows if r["delay"] == d and r["size_usd"] == 100.0]
    a = st.fmean(r["return"] for r in rs); b = st.fmean(r["return_if_exit_at_whale_sell_price"] for r in rs)
    P(f"| {LBL[d]} | {pct(st.median(r['entry_vs_whale_pool_price'] for r in rs))} | {pct(a)} | {pct(b)} | {pct(a-b)} |")
P()
P("### By venue ($100, 1 s delay)"); P()
P("| Venue of whale buy | Copies | Win rate | Median | Mean | Went to zero | Whale mean |"); P("|---|---|---|---|---|---|---|")
by = defaultdict(list)
for r in rows:
    if r["delay"] == "1s" and r["size_usd"] == 100.0: by[r["venue"]].append(r)
for v, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    R_ = [r["return"] for r in rs]; W = [r["whale_return"] for r in rs if r["whale_return"] is not None]
    P(f"| {v} | {len(rs)} | {sum(x>0 for x in R_)/len(R_)*100:.0f}% | {pct(st.median(R_))} | {pct(st.fmean(R_))} | {sum(r['went_to_zero'] for r in rs)/len(rs)*100:.0f}% | {pct(st.fmean(W)) if W else 'n/a'} |")
P()
# whale test-week realized P&L on ALL their test-week swaps (same average-cost method as selection)
tw = {}
for fn in glob.glob(os.path.join(D, "test_swaps", "*.jsonl")):
    a = os.path.basename(fn)[:-6]
    recs = sorted((json.loads(l) for l in open(fn)), key=lambda r: (r["slot"], r["idx"]))
    pos = defaultdict(lambda: [0.0, 0.0]); real = 0.0; nb = 0
    for r in recs:
        if r["quote"] != "SOL": continue
        p = pos[r["mint"]]
        if r["side"] == "buy": p[0] += r["tokens"]; p[1] += r["quote_amt"]; nb += 1
        elif p[0] > 0:
            sold = min(r["tokens"], p[0]); c = p[1] * sold / p[0]
            real += r["quote_amt"] * sold / r["tokens"] - c; p[0] -= sold; p[1] -= c
    tw[a] = (real, nb)
P("### Each whale: selection week vs test week, and what copying it returned ($100, 1 s)"); P()
P("| Wallet (KOLScan name) | Selection-week realized P&L (SOL) | Test-week realized P&L (SOL) | Test-week buys | Copies sampled | Whale's mean return on sampled buys | Copier mean return | Copier win rate |")
P("|---|---|---|---|---|---|---|---|")
byw = defaultdict(list)
for r in rows:
    if r["delay"] == "1s" and r["size_usd"] == 100.0: byw[r["whale"]].append(r)
tot_sel = tot_test = 0
for a in sorted(sel, key=lambda a: -sel[a]["sel_realized_pnl_sol"]):
    if not sel[a]["selected"]: continue
    rs = byw.get(a, []); W = [r["whale_return"] for r in rs if r["whale_return"] is not None]
    tot_sel += sel[a]["sel_realized_pnl_sol"]; tot_test += tw.get(a, (0, 0))[0]
    P(f"| {names[a]} `{a[:6]}…` | {sel[a]['sel_realized_pnl_sol']:+.1f} | {tw.get(a,(0,0))[0]:+.1f} | {tw.get(a,(0,0))[1]} | {len(rs)} | {pct(st.fmean(W)) if W else 'n/a'} | {pct(st.fmean(r['return'] for r in rs)) if rs else 'n/a'} | {(sum(r['return']>0 for r in rs)/len(rs)*100) if rs else 0:.0f}% |")
P(f"| **All 20** | **{tot_sel:+.1f}** | **{tot_test:+.1f}** | | | | | |")
P()
# holding times and sizes
hold = []; sizes = []; nosell = 0
for e in evs.values():
    sizes.append(e["quote_amt"])
    if e["sells"]: hold.append(e["sells"][0]["time"] - e["time"])
    else: nosell += 1
hold.sort()
facts = {"events": len(evs), "median_whale_buy_sol": st.median(sizes), "mean_whale_buy_sol": st.fmean(sizes),
         "median_seconds_to_first_sell": st.median(hold), "share_first_sell_within_30s": sum(h <= 30 for h in hold) / len(evs),
         "share_first_sell_within_60s": sum(h <= 60 for h in hold) / len(evs), "share_first_sell_within_5min": sum(h <= 300 for h in hold) / len(evs),
         "share_no_sell_24h": nosell / len(evs),
         "sampled_whale_total_pnl_sol": sum((r["whale_return"] or 0) * r["whale_buy_quote"] for r in rows if r["delay"] == "1s" and r["size_usd"] == 100.0),
         "sampled_whale_total_cost_sol": sum(r["whale_buy_quote"] for r in rows if r["delay"] == "1s" and r["size_usd"] == 100.0),
         "sel_total_top20_sol": tot_sel, "test_total_top20_sol": tot_test}
P("```"); P(json.dumps(facts, indent=1)); P("```")
open(os.path.join(R, "tables.md"), "w").write("\n".join(out))
print("\n".join(out))
