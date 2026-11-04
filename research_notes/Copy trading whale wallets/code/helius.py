"""Read-only Helius client with credit tracking. Never logs the API key."""
import json, os, time, urllib.request, urllib.error, threading

_KEY = os.environ.get("HELIUS_API_KEY", "")
RPC = "https://mainnet.helius-rpc.com/?api-key="
LEDGER = os.path.join(os.environ.get("CT_DATA", "."), "credits.json")
_lock = threading.Lock()
_last = [0.0]
MIN_GAP = 0.12  # ~8 req/s

# Estimated credit cost per call (Helius published pricing; updated if observed otherwise)
COST = {"getTransaction": 1, "getSlot": 1, "getBlockTime": 1, "default": 1}  # gtfa costs computed per call below

def _charge(kind, c=None):
    if c is None:
        c = COST.get(kind, COST["default"])
    with _lock:
        d = None
        for _ in range(50):
            try:
                d = json.load(open(LEDGER)); break
            except FileNotFoundError:
                d = {}; break
            except Exception:
                time.sleep(0.02)
        if d is None:
            raise RuntimeError("credit ledger unreadable")
        d[kind] = d.get(kind, 0) + c
        d["total"] = d.get("total", 0) + c
        tmp = f"{LEDGER}.{os.getpid()}.tmp"
        json.dump(d, open(tmp, "w")); os.replace(tmp, LEDGER)
        with open(LEDGER + ".log", "a") as f:
            f.write(f"{kind} {c}\n")
    return c

def credits_used():
    try:
        return json.load(open(LEDGER)).get("total", 0)
    except Exception:
        return 0

def _throttle():
    with _lock:
        now = time.time()
        wait = _last[0] + MIN_GAP - now
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()

def _req(url, body=None, kind="default", tries=9, cost_fn=None):
    data = json.dumps(body).encode() if body is not None else None
    for i in range(tries):
        _throttle()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "dealbot-research"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out = json.loads(r.read())
                _charge(kind, cost_fn(out) if cost_fn else None)
                return out
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode(errors="replace").replace(_KEY, "***") if _KEY else ""
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(30, 2 ** i))
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            time.sleep(min(30, 2 ** i))
    raise RuntimeError("request failed after retries")

def rpc(method, params, kind=None):
    out = _req(RPC + _KEY, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, kind or method)
    if "error" in out:
        raise RuntimeError(f"RPC error: {json.dumps(out['error'])[:300]}")
    return out["result"]

def _gtfa_cost(out):
    res = out.get("result") or {}
    n = len(res.get("data") or [])
    return max(10, -(-n // 100) * 10)

def gtfa(address, gte=None, lt=None, details="full", limit=None, sort="asc", status="succeeded",
         max_pages=1000, extra_filters=None, slot_gte=None):
    """Helius getTransactionsForAddress, paginated. Yields items.
    Cost (Helius docs): full = 10 credits per 100 txs returned (min 10); signatures = flat 10."""
    filt = {}
    bt = {}
    if gte is not None: bt["gte"] = gte
    if lt is not None: bt["lt"] = lt
    if bt: filt["blockTime"] = bt
    if slot_gte is not None: filt["slot"] = {"gte": slot_gte}
    if status: filt["status"] = status
    if extra_filters: filt.update(extra_filters)
    if limit is None:
        limit = 100 if details == "full" else 1000
    tok = None
    for _ in range(max_pages):
        opts = {"transactionDetails": details, "limit": limit, "sortOrder": sort, "filters": filt,
                "encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}
        if details != "full":
            opts.pop("encoding"); opts.pop("maxSupportedTransactionVersion")
        if tok: opts["paginationToken"] = tok
        body = {"jsonrpc": "2.0", "id": 1, "method": "getTransactionsForAddress", "params": [address, opts]}
        out = _req(RPC + _KEY, body, "gtfa_" + details,
                   cost_fn=(_gtfa_cost if details == "full" else (lambda o: 10)))
        if "error" in out:
            raise RuntimeError(f"RPC error: {json.dumps(out['error'])[:300]}")
        res = out["result"]
        for it in res.get("data") or []:
            yield it
        tok = res.get("paginationToken")
        if not tok or not res.get("data"):
            return
