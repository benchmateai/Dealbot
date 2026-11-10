"""The lab's gap recorder: Kalshi beside Polymarket US on the same events, public prices only, no orders.

Each pair in lab/gap_pairs.json names one Kalshi market and the Polymarket US market that settles the same way
(its `rules` note says why the two match). Every EVERY_S seconds the recorder reads Kalshi's best bid and ask
for the pairs in batches of KALSHI_BATCH (GET /markets?tickers=..., public: two requests a pass for 219 pairs,
since Kalshi's public limit is shared by the team's sessions) and, right after each batch, the book of each
Polymarket US market in it (GET https://gateway.polymarket.us/v1/markets/{slug}/book, public), POLY_WORKERS
at a time, so the two quotes of a pair are seconds apart. It writes to its own hour files (<HH>.gap.jsonl):
  gap_pair   {pair, kalshi, polymarket_us, category, rules, k_fee, p_fee, k_close, p_end}   once a chunk
  gap_quote  {pair, k: {bid, ask, bid_size, ask_size, status, ts}, p: {bid, ask, bid_size, ask_size, state, ts}}
             when either side's quote changes, and every HEARTBEAT_S regardless
  gap_status {kalshi: request counters, polymarket_us: request counters, pairs, quotes, note}
Prices are the market's YES in dollars: Polymarket US has one instrument per market, bought for YES and
shorted for NO. Sizes are contracts at the best price; a side with nothing resting is null. k_fee and p_fee
are each venue's taker coefficient for the market (Kalshi's 0.07 times the series' fee multiplier, which is 0
on a series it charges no fee on, such as its year-end Bitcoin ranges; the coefficient Polymarket US
publishes on the market, 0.095 for an account below $10,000 of monthly volume).
Nothing is ever sent to either venue but public GETs; lab/gap_report.py turns the records into gaps net of
both fees and how long they last.

    python -m lab.gap_recorder --until <unix seconds> --data lab/data [--pairs lab/gap_pairs.json] [--every 60]
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from lab.recorder import _num, _ts
from lab.rest import Budget, LabRest
from lab.store import LabStore

log = logging.getLogger("lab.gaps")

STREAM = "gap"
PM_US = "https://gateway.polymarket.us"
EVERY_S = 60
HEARTBEAT_S = 600
KALSHI_BATCH = 110           # Kalshi answers 150 tickers in one GET /markets; 110 keeps 219 pairs to two requests a pass
POLY_WORKERS = 8
KALSHI_TAKER = 0.07          # Kalshi's taker coefficient, times the series' fee_multiplier
PM_TAKER_DEFAULT = 0.095     # Polymarket US's tier-1 taker coefficient, when a market does not publish its own
STATUS_S = 600
DESCRIBE_TRIES = 3           # tries for each of a chunk's one-off Kalshi lookups (fees, settlement dates)
PAIRS = Path(__file__).with_name("gap_pairs.json")


def load_pairs(path: str | Path = PAIRS) -> list[dict]:
    """The pairs, checked: each id, Kalshi ticker and Polymarket US slug appears once."""
    pairs = json.loads(Path(path).read_text())
    for key in ("id", "kalshi", "polymarket_us"):
        values = [p[key] for p in pairs]
        if len(set(values)) != len(values):
            raise ValueError(f"{path}: a {key} appears twice")
    return pairs


class PolyUS:
    """Polymarket US's public market data, paced by its own budget (the venue allows 25 requests a second);
    safe to call from several threads at once."""

    def __init__(self, budget: Budget | None = None, *, opener=urllib.request.urlopen, base: str = PM_US) -> None:
        self.budget = budget or Budget(15.0, 15.0)
        self.opener, self.base = opener, base
        self.requests = self.errors = self.rate_limited = 0
        self._lock = threading.Lock()

    def _count(self, **inc: int) -> None:
        with self._lock:
            for k, v in inc.items():
                setattr(self, k, getattr(self, k) + v)

    def get(self, path: str, params: list[tuple[str, str]] | None = None) -> dict | None:
        with self._lock:
            self.budget.take()
            self.requests += 1
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        try:
            with self.opener(urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "dealbot-lab"}), timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            self._count(errors=1, rate_limited=int(exc.code == 429))
            if exc.code == 429:
                with self._lock:
                    self.budget.pause(5.0)
            return None
        except (OSError, ValueError):
            self._count(errors=1)
            return None

    def counters(self) -> dict:
        return {"requests": self.requests, "errors": self.errors, "rate_limited": self.rate_limited}


def _coeff(x, default: float) -> float:
    """A published fee coefficient or multiplier, or `default` when there is none; 0 stays 0 (no fee)."""
    v = _num(x)
    return default if v is None else v


def _amount(x) -> float | None:
    return _num((x or {}).get("value")) if isinstance(x, dict) else _num(x)


def kalshi_quote(m: dict, ts: int) -> dict:
    bid, ask = _num(m.get("yes_bid_dollars")), _num(m.get("yes_ask_dollars"))
    return {"bid": bid if bid else None, "ask": ask if ask and ask < 1.0 else None,  # a 0 bid or $1 ask means nothing is resting
            "bid_size": _num(m.get("yes_bid_size_fp")) if bid else None, "ask_size": _num(m.get("yes_ask_size_fp")) if ask and ask < 1.0 else None,
            "status": m.get("status"), "ts": ts}


def poly_quote(book: dict, ts: int) -> dict:
    data = book.get("marketData") or {}
    bids = [(_amount(x.get("px")), _num(x.get("qty"))) for x in data.get("bids") or []]
    asks = [(_amount(x.get("px")), _num(x.get("qty"))) for x in data.get("offers") or []]
    bids = [(p, q) for p, q in bids if p is not None and q]
    asks = [(p, q) for p, q in asks if p is not None and q]
    bid = max(bids, default=None)
    ask = min(asks, default=None)
    return {"bid": bid[0] if bid else None, "ask": ask[0] if ask else None, "bid_size": bid[1] if bid else None,
            "ask_size": ask[1] if ask else None, "state": data.get("state"), "ts": ts}


class GapRecorder:
    def __init__(self, store: LabStore, kalshi: LabRest, poly: PolyUS, pairs: list[dict], *, now_ms=lambda: int(time.time() * 1000)) -> None:
        self.store, self.kalshi, self.poly, self.pairs, self.now_ms = store, kalshi, poly, pairs, now_ms
        self.last: dict[str, tuple] = {}          # pair -> (the quotes last written, when)
        self.quotes = 0

    def _lookup(self, path: str, params: dict | None = None) -> dict | None:
        """A Kalshi GET for the chunk's one-off lookups, tried DESCRIBE_TRIES times: a lookup refused for rate
        would leave a pair without its fee or settlement date for the whole chunk (LabRest waits out the
        refusal before the next try)."""
        for _ in range(DESCRIBE_TRIES):
            payload = self.kalshi.get(path, params)
            if payload is not None:
                return payload
        return None

    def describe(self) -> None:
        """One gap_pair record per pair: the rules note and each venue's taker coefficient and end date."""
        now = self.now_ms()
        k_fee: dict[str, float] = {}
        for series in sorted({p["kalshi"].split("-")[0] for p in self.pairs}):
            info = (self._lookup(f"/series/{series}") or {}).get("series") or {}
            k_fee[series] = KALSHI_TAKER * _coeff(info.get("fee_multiplier"), 1.0)  # 0 is a fee-free series, not a missing one
        k_close: dict[str, int | None] = {}
        for i in range(0, len(self.pairs), KALSHI_BATCH):  # when each Kalshi market is expected to settle
            batch = self.pairs[i:i + KALSHI_BATCH]
            payload = self._lookup("/markets", {"tickers": ",".join(p["kalshi"] for p in batch), "limit": len(batch)})
            for m in (payload or {}).get("markets") or []:
                k_close[m.get("ticker")] = _ts(m.get("expected_expiration_time")) or _ts(m.get("close_time"))
        p_info: dict[str, dict] = {}
        slugs = [p["polymarket_us"] for p in self.pairs]
        for i in range(0, len(slugs), 50):
            batch = slugs[i:i + 50]
            payload = self.poly.get("/v1/markets", [("slug", s) for s in batch] + [("limit", str(len(batch)))])
            for m in (payload or {}).get("markets") or []:
                p_info[m.get("slug")] = m
        for p in self.pairs:
            m = p_info.get(p["polymarket_us"]) or {}
            self.store.write("gap_pair", {"pair": p["id"], "kalshi": p["kalshi"], "polymarket_us": p["polymarket_us"], "category": p.get("category"),
                                          "rules": p.get("rules"), "k_fee": round(k_fee.get(p["kalshi"].split("-")[0], KALSHI_TAKER), 6),
                                          "p_fee": _coeff(m.get("feeCoefficient"), PM_TAKER_DEFAULT), "k_close": k_close.get(p["kalshi"]),
                                          "p_end": _ts(m.get("endDate"))}, ts_ms=now)

    def poll(self) -> None:
        """One pass over every pair: a Kalshi batch, then the Polymarket US books of that batch."""
        for i in range(0, len(self.pairs), KALSHI_BATCH):
            batch = self.pairs[i:i + KALSHI_BATCH]
            payload = self.kalshi.get("/markets", {"tickers": ",".join(p["kalshi"] for p in batch), "limit": len(batch)})
            k_ts = self.now_ms()
            kq = {m.get("ticker"): kalshi_quote(m, k_ts) for m in (payload or {}).get("markets") or []}
            if not kq:  # Kalshi's batch failed (a rate limit, say): its Polymarket books would have nothing to pair with
                continue
            wanted = [p for p in batch if p["kalshi"] in kq]

            def book_of(p: dict) -> tuple[dict | None, int]:
                book = self.poly.get(f"/v1/markets/{urllib.parse.quote(p['polymarket_us'])}/book")
                return book, self.now_ms()
            with ThreadPoolExecutor(POLY_WORKERS) as pool:
                books = list(pool.map(book_of, wanted))
            for p, (book, p_ts) in zip(wanted, books):
                if book is not None:
                    self.record(p["id"], kq[p["kalshi"]], poly_quote(book, p_ts))

    def record(self, pair: str, k: dict, p: dict) -> None:
        now = self.now_ms()
        key = tuple(k.get(x) for x in ("bid", "ask", "bid_size", "ask_size", "status")) + tuple(p.get(x) for x in ("bid", "ask", "bid_size", "ask_size", "state"))
        last = self.last.get(pair)
        if last is not None and last[0] == key and now - last[1] < HEARTBEAT_S * 1000:
            return
        self.last[pair] = (key, now)
        self.quotes += 1
        self.store.write("gap_quote", {"pair": pair, "k": k, "p": p}, ts_ms=now)

    def write_status(self, note: str | None = None) -> None:
        rec = {"kalshi": self.kalshi.counters(), "polymarket_us": self.poly.counters(), "pairs": len(self.pairs), "quotes": self.quotes}
        if note:
            rec["note"] = note
        self.store.write("gap_status", rec, ts_ms=self.now_ms())

    def run(self, until_ms: int, *, every_s: float = EVERY_S, sleep=time.sleep, stop=lambda: False) -> None:
        self.describe()
        next_status = 0
        while self.now_ms() < until_ms and not stop():
            started = self.now_ms()
            try:
                self.poll()
            except Exception as exc:  # noqa: BLE001 - one bad pass must not end the recording
                log.warning("poll failed: %s: %s", type(exc).__name__, exc)
                self.write_status(note=f"poll failed: {type(exc).__name__}: {str(exc)[:200]}")
            if self.now_ms() >= next_status:
                self.write_status()
                next_status = self.now_ms() + STATUS_S * 1000
            wait = every_s - (self.now_ms() - started) / 1000
            if wait > 0 and self.now_ms() + wait * 1000 < until_ms:
                sleep(wait)
            elif self.now_ms() + max(wait, 0) * 1000 >= until_ms:
                break


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record Kalshi and Polymarket US quotes on matched markets (public data, no orders)")
    parser.add_argument("--until", type=float, required=True, help="stop at this Unix time (seconds)")
    parser.add_argument("--data", default="lab/data")
    parser.add_argument("--pairs", default=str(PAIRS))
    parser.add_argument("--every", type=float, default=EVERY_S, help="seconds between passes over the pairs")
    parser.add_argument("--rate", type=float, default=0.25, help="average Kalshi requests a second")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    stopping = {"now": False}
    signal.signal(signal.SIGTERM, lambda *_: stopping.__setitem__("now", True))
    store = LabStore(args.data, stream=STREAM)
    rec = GapRecorder(store, LabRest(budget=Budget(args.rate, 3.0)), PolyUS(), load_pairs(args.pairs))

    def nap(seconds: float) -> None:  # sleeps in short steps so a TERM ends the chunk within a second
        end = time.time() + seconds
        while time.time() < end and not stopping["now"]:
            time.sleep(min(1.0, end - time.time()))
    try:
        rec.run(int(args.until * 1000), every_s=args.every, sleep=nap, stop=lambda: stopping["now"])
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)  # the last seal finishes before the process goes
        rec.write_status(note="gap recorder stopped")
        store.close()
        sealed = store.seal_closed_hours()  # this hour's file too, so the chunk publishes it
        print(f"gap recorder: {rec.quotes} quotes; Kalshi {rec.kalshi.counters()}; Polymarket US {rec.poly.counters()}; sealed {len(sealed)} hour files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
