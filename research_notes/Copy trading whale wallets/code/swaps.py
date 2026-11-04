"""Parse a jsonParsed Solana transaction into a swap record from balance changes only."""
from collections import defaultdict

WSOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrajaCRuGS3sDiPF2z3KGRBG66H7QdemWByNXBY"
QUOTES = {WSOL: "SOL", USDC: "USDC"}
SKIP_MINTS = {WSOL, USDC, USDT}
PUMP_CURVE = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
VENUES = {
    PUMP_CURVE: "pumpfun",
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": "pumpswap",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "raydium_v4",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "raydium_cpmm",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "raydium_clmm",
    "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj": "raydium_launchlab",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "meteora_dlmm",
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": "meteora_damm_v1",
    "cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG": "meteora_damm_v2",
    "dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN": "meteora_dbc",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "orca_whirlpool",
}
JUPITER = {"JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUc5pjrRDzBTAV4", "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"}
# Swap fee charged by the venue on each side (fraction of notional). Published figures; where the
# venue uses tiers we take the LOW end so that results are biased in the copier's favour.
VENUE_FEE = {"pumpfun": 0.0125, "pumpswap": 0.0030, "raydium_v4": 0.0025, "raydium_cpmm": 0.0025,
             "raydium_clmm": 0.0025, "raydium_launchlab": 0.0100, "meteora_dlmm": 0.0025,
             "meteora_damm_v1": 0.0025, "meteora_damm_v2": 0.0025, "meteora_dbc": 0.0100,
             "orca_whirlpool": 0.0025, "other": 0.0030}

def _keys(tx):
    return [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]

def _signers(tx):
    ks = tx["transaction"]["message"]["accountKeys"]
    return {k["pubkey"] for k in ks if isinstance(k, dict) and k.get("signer")}

def venue_of(keys):
    vs = [VENUES[k] for k in keys if k in VENUES]
    via_jup = any(k in JUPITER for k in keys)
    if not vs:
        return ("jupiter_other" if via_jup else "other"), via_jup
    return vs[0], via_jup

def deltas(tx):
    """Return (token_delta[owner][mint] in UI units, token_post[owner][mint], lamport_delta[pubkey],
    lamport_post[pubkey], token_accounts_by_owner[owner] -> set(indices), decimals)."""
    meta = tx["meta"]; keys = _keys(tx)
    pre = {b["accountIndex"]: b for b in meta.get("preTokenBalances") or []}
    post = {b["accountIndex"]: b for b in meta.get("postTokenBalances") or []}
    td = defaultdict(lambda: defaultdict(float)); tp = defaultdict(lambda: defaultdict(float))
    acc_owner = {}
    dec = {}
    for idx in set(pre) | set(post):
        b = post.get(idx) or pre.get(idx)
        mint, owner = b["mint"], b.get("owner")
        d = int(b["uiTokenAmount"]["decimals"]); dec[mint] = d
        a0 = int(pre[idx]["uiTokenAmount"]["amount"]) if idx in pre else 0
        a1 = int(post[idx]["uiTokenAmount"]["amount"]) if idx in post else 0
        td[owner][mint] += (a1 - a0) / 10 ** d
        tp[owner][mint] += a1 / 10 ** d
        acc_owner[idx] = (owner, mint)
    ld = {}; lp = {}
    for i, k in enumerate(keys):
        ld[k] = (meta["postBalances"][i] - meta["preBalances"][i]) / 1e9
        lp[k] = meta["postBalances"][i] / 1e9
    return td, tp, ld, lp, acc_owner, dec, keys

def parse(tx, trader=None):
    """Swap record or None. trader defaults to fee payer. Prices are quote per token."""
    if tx.get("meta") is None or tx["meta"].get("err") is not None:
        return None
    td, tp, ld, lp, acc_owner, dec, keys = deltas(tx)
    if trader is None:
        trader = keys[0]
    if trader not in _signers(tx):
        return None
    # trader's quote change. SOL: wallet lamports + lamports of all its token accounts (so refundable
    # account rent and WSOL wrap/unwrap net out); USDC from token deltas.
    sol = ld.get(trader, 0.0)
    for idx, (owner, mint) in acc_owner.items():
        if owner == trader:
            sol += ld.get(keys[idx], 0.0)
    # WSOL accounts created+closed inside the tx have no token balance entry but their lamports net to 0
    usdc = td[trader].get(USDC, 0.0)
    toks = {m: v for m, v in td[trader].items() if m not in SKIP_MINTS and abs(v) > 0}
    if len(toks) != 1:
        return None
    mint, dtok = next(iter(toks.items()))
    if abs(usdc) > 0.01 and abs(usdc) * 0.004 > abs(sol):   # treat as USDC-quoted
        quote, dq = "USDC", usdc
    else:
        quote, dq = "SOL", sol
    side = "buy" if dtok > 0 and dq < 0 else "sell" if dtok < 0 and dq > 0 else None
    if side is None:
        return None
    fee = tx["meta"]["fee"] / 1e9
    venue, via_jup = venue_of(keys)
    rec = {"slot": tx["slot"], "idx": tx.get("transactionIndex", 0), "time": tx.get("blockTime"),
           "sig": tx["transaction"]["signatures"][0], "trader": trader, "mint": mint, "side": side,
           "tokens": abs(dtok), "quote": quote, "quote_amt": abs(dq), "trader_post_tokens": tp[trader].get(mint, 0.0),
           "trader_price": abs(dq) / abs(dtok), "txfee": fee, "venue": venue, "via_jupiter": via_jup,
           "cu_price_total_fee": fee}
    rec.update(pool_side(td, tp, ld, lp, keys, mint, dtok, quote, trader, acc_owner))
    return rec

def pool_side(td, tp, ld, lp, keys, mint, dtok, quote, trader, acc_owner):
    """Find the pool (owner whose token change mirrors the trader) and its price and quote reserve."""
    qmint = WSOL if quote == "SOL" else USDC
    best = None
    for owner, m in td.items():
        if owner == trader: continue
        v = m.get(mint, 0.0)
        if v * dtok < 0 and (best is None or abs(v) > abs(best[1])):
            best = (owner, v)
    if best is None:
        return {"pool": None}
    owner, vtok = best
    qd = td[owner].get(qmint, 0.0); qpost = tp[owner].get(qmint, 0.0); native = False
    if quote == "SOL" and abs(qd) < 1e-12 and owner in ld:
        qd = ld[owner]; qpost = lp[owner]; native = True
    if qd == 0 or qd * vtok > 0:
        return {"pool": owner, "pool_price": None}
    virt = 30.0 if (native and PUMP_CURVE in keys) else 0.0
    vault = None
    for idx, (o, mm) in acc_owner.items():
        if o == owner and mm == mint:
            vault = keys[idx]
    return {"pool": owner, "pool_vault": vault, "pool_price": abs(qd) / abs(vtok), "pool_quote": abs(qd),
            "pool_quote_reserve_post": qpost + virt, "pool_token_reserve_post": tp[owner].get(mint, 0.0)}
