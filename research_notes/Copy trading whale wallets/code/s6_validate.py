"""Check the constant-product price model: predict each swap's average fill from the previous swap's
post-trade state on the same pool and compare with the actual fill."""
import json, os, glob, statistics
from collections import defaultdict
D = os.environ["CT_DATA"]
err = defaultdict(list)
for fn in glob.glob(os.path.join(D, "paths", "*.json")):
    P = json.load(open(fn))
    sw = sorted(P["entry"]["swaps"], key=lambda s: (s["slot"], s["idx"]))
    for a, b in zip(sw, sw[1:]):
        if a["vault"] != b["vault"] or a["quote"] != b["quote"]: continue
        y, p = a["y_post"], a["p_post"]; dy = b["size_q"]
        if b["side"] == "buy":
            pred = p * (1 + dy / y)            # avg = (y+dy)/x with x = y/p
        else:
            pred = p * (y - dy) / y if dy < y else None   # avg = y_post/x_pre
        if not pred: continue
        actual = (b["p0"] * (b["y_post"] / b["y_pre"]))   # = pool avg price
        err[b["venue"]].append(abs(pred / actual - 1))
out = {}
for v, e in sorted(err.items(), key=lambda kv: -len(kv[1])):
    out[v] = {"pairs": len(e), "median_abs_err": statistics.median(e), "p90_abs_err": sorted(e)[int(0.9 * len(e))]}
    print(v, out[v])
json.dump(out, open(os.path.join(D, "model_validation.json"), "w"), indent=1)
