"""The long-shot fade, tested on Kalshi's settled markets (reports/Viable Kalshi trading strategies.md, strategy 2):
buy NO where the YES side is a long shot, 10 cents or less, and hold to settlement. Paper only: public market data,
no orders, no key.

The rules below were fixed at REGISTERED, before any result was read, and are not tuned on what the test shows.

Markets: binary markets that settled yes or no and closed between CLOSED_FROM and CLOSED_TO, in series that do not
run intraday or daily, with at least MIN_VOLUME contracts traded over their life (a filter that uses the whole life,
which leans toward markets whose long shot came alive late: against the fade, so conservative), at most
MARKETS_PER_EVENT a event (a seeded random choice). Series are a seeded random sample of SERIES_SAMPLE from each
group: "recreational" (the categories with heavy casual YES buying) and "control" (where the research found the bias
near zero).

Entry: ENTRY_DAYS after the market opened (1, 7 and 30; 7 is the main test), if it is still open then, on its daily
bid and ask at the last close at or before that moment, at most a day old. Measuring from the open, never back from
the close, keeps the result out of the timing (a market can close early because its long shot came in).
  taker   buy NO at its ask (1 - the YES bid) where the YES bid is 1 to 10 cents; Kalshi's taker fee, 0.07 x the
          series' multiplier x price x (1 - price) a contract, rounded up to the cent on an order of ORDER_CONTRACTS
  maker   rest a NO bid at 1 - the YES ask where the YES ask is 1 to 10 cents; filled if a later day before the close
          traded YES above that price ("strict": a trade through it) or at it ("loose": a touch); the maker fee
          where the series charges one (0.0175 x multiplier x price x (1 - price))
Each event is one bet: every qualifying contract on it, one each, settled together.

Amended at AMENDED, after a review and before any price was fetched or result read: candles come in two shapes
(the historical endpoint's "close"/"high", the live one's "close_dollars"/"high_dollars") and both are read; a market
listed twice (by both endpoints around Kalshi's historical cutoff) counts once; the candle that holds the close is
fetched and counted, so an upset on the last day can fill a resting bid; a resting bid fills only on trades in days
that begin after entry, never on the entry day's earlier trades; an entry before CLOSED_FROM is left out (keeping it
would favour markets that had not closed early); and to keep the fetch to about a day at the rate Kalshi allows us,
prices are fetched for every market open 7 days or more (the main test and the 30-day entry) and for a seeded random
CANDLE_SHORT_SAMPLE of those open 1 to 7 days (the 1-day entry, which is description only; each sampled event
counts as many as its share of the population, so the long-lived markets are not over-weighted). Fees are each series'
schedule as of the fetch; Kalshi changed some within the period (by about 0.2-0.4% of stake, mostly in the fade's
favour), which this does not model.

Main test (pass or fail): taker, entry 7 days after the open, recreational group. It passes if the money made over
the money staked is above zero across a 95% bootstrap interval over events, and above zero in each half of the
period (split at the median entry time). Everything else is description.

    python -m lab.longshot fetch --data <dir>      (resumable; about 0.5 requests a second, backing off on 429)
    python -m lab.longshot report --data <dir> [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REGISTERED = "2026-11-11T04:20:00Z"
AMENDED = "2026-11-11T04:37:00Z"
CANDLE_SHORT_SAMPLE = 3_000
CLOSED_FROM, CLOSED_TO = "2025-05-01T00:00:00Z", "2026-11-10T00:00:00Z"
RECREATIONAL = ("Entertainment", "Sports", "Politics", "Elections", "Mentions", "World", "Culture", "Social")
CONTROL = ("Financials", "Economics", "Climate and Weather", "Crypto", "Commodities", "Companies", "Science and Technology", "Health")
SKIP_FREQUENCY = ("fifteen_min", "hourly", "daily")
SERIES_SAMPLE = {"recreational": 700, "control": 200}
MIN_VOLUME = 1_000
MARKETS_PER_EVENT = 30
ENTRY_DAYS = (1, 7, 30)
MAIN_DAYS = 7
MAX_YES = 0.10
TAKER, MAKER = 0.07, 0.0175
ORDER_CONTRACTS = 100
BOOTSTRAP = 2_000
SEED = 20261111
DAY_S = 86_400


def _ts(iso: str) -> int:
    return int(datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp())


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def group_of(category: str | None) -> str | None:
    return "recreational" if category in RECREATIONAL else "control" if category in CONTROL else None


def fee(coeff: float, price: float, contracts: int = ORDER_CONTRACTS) -> float:
    """A contract's share of the fee on an order of `contracts`, rounded up to the cent as Kalshi charges it."""
    if coeff <= 0:
        return 0.0
    return round(math.ceil(round(coeff * contracts * price * (1 - price) * 100, 6)) / 100 / contracts, 6)


def quote_at(candles: list[dict], t: int) -> dict | None:
    """The daily candle that closed last at or before t, if it is at most a day old."""
    best = None
    for c in candles:
        end = c.get("end_period_ts")
        if end is not None and end <= t and (best is None or end > best["end_period_ts"]):
            best = c
    return best if best is not None and t - best["end_period_ts"] <= DAY_S else None


def _field(d: dict | None, name: str) -> float | None:
    """A candle's value in either shape: the historical endpoint's "close", the live one's "close_dollars"."""
    d = d or {}
    return _num(d[name]) if d.get(name) is not None else _num(d.get(f"{name}_dollars"))


def _close(c: dict, side: str) -> float | None:
    return _field(c.get(side), "close")


def bets(market: dict, candles: list[dict], series: dict, days: int) -> dict:
    """{version: (price, fee, payout)} for one market entered `days` after it opened; versions it does not qualify
    for are absent."""
    opened, closed = _ts(market["open_time"]), _ts(market["close_time"])
    t = opened + days * DAY_S
    if closed <= t or t < _ts(CLOSED_FROM) or market.get("result") not in ("yes", "no"):
        return {}
    q = quote_at(candles, t)
    if q is None:
        return {}
    payout = 1.0 if market["result"] == "no" else 0.0
    mult = _num(series.get("fee_multiplier"))
    mult = 1.0 if mult is None else mult  # 0 is a fee-free series, not a missing one
    out = {}
    bid, ask = _close(q, "yes_bid"), _close(q, "yes_ask")
    if bid is not None and 0.01 - 1e-9 <= bid <= MAX_YES + 1e-9:
        price = round(1 - bid, 4)
        out["taker"] = (price, fee(TAKER * mult, price), payout)
    if ask is not None and 0.01 - 1e-9 <= ask <= MAX_YES + 1e-9:
        price = round(1 - ask, 4)
        maker_fee = fee(MAKER * mult, price) if "maker" in str(series.get("fee_type", "")) else 0.0
        # days that begin after entry, through the one that holds the close
        later = [c for c in candles if t <= c.get("end_period_ts", 0) - DAY_S < closed]
        highs = [h for h in (_field(c.get("price"), "high") for c in later) if h is not None]
        if any(h > ask + 1e-9 for h in highs):
            out["maker_strict"] = (price, maker_fee, payout)
        if any(h >= ask - 1e-9 for h in highs):
            out["maker_loose"] = (price, maker_fee, payout)
    return out


def bucket(price_no: float) -> str:
    yes = round(1 - price_no, 4)
    return "1-3c" if yes <= 0.03 + 1e-9 else "4-6c" if yes <= 0.06 + 1e-9 else "7-10c"


def short_lived(m: dict) -> bool:
    return _ts(m["close_time"]) - _ts(m["open_time"]) <= MAIN_DAYS * DAY_S


def event_bets(markets: list[dict], candles: dict[str, list[dict]], series: dict[str, dict], days: int, version: str,
               short_weight: float = 1.0) -> list[dict]:
    """One bet per event: {event, group, category, t, w, contracts, stake, pnl, won, buckets: {bucket: [stake, pnl]}};
    w is short_weight for an event of markets open 7 days or less (sampled), else 1."""
    events: dict[str, dict] = {}
    for m in markets:
        s = series.get(m["series_ticker"]) or {}
        b = bets(m, candles.get(m["ticker"]) or [], s, days).get(version)
        if b is None:
            continue
        price, f, payout = b
        e = events.setdefault(m["event_ticker"], {"event": m["event_ticker"], "group": group_of(s.get("category")), "category": s.get("category"),
                                                  "t": _ts(m["open_time"]) + days * DAY_S, "w": short_weight if short_lived(m) else 1.0,
                                                  "contracts": 0, "stake": 0.0, "pnl": 0.0,
                                                  "won": 0, "buckets": {}})
        e["contracts"] += 1
        e["stake"] += price + f
        e["pnl"] += payout - price - f
        e["won"] += int(payout == 1.0)
        bk = e["buckets"].setdefault(bucket(price), [0.0, 0.0, 0])
        bk[0] += price + f
        bk[1] += payout - price - f
        bk[2] += 1
    return list(events.values())


def summarize(evs: list[dict], rng: random.Random, draws: int = BOOTSTRAP) -> dict:
    """Money made over money staked, each event weighted by w (the sampled short-lived ones count for their share)."""
    stake, pnl = sum(e["w"] * e["stake"] for e in evs), sum(e["w"] * e["pnl"] for e in evs)
    n = sum(e["contracts"] for e in evs)
    out = {"events": len(evs), "contracts": n, "stake_usd": round(stake, 2), "pnl_usd": round(pnl, 2),
           "return": round(pnl / stake, 5) if stake else None, "no_won_share": round(sum(e["won"] for e in evs) / n, 4) if n else None,
           "upset_share": round(1 - sum(e["won"] for e in evs) / n, 4) if n else None}
    if len(evs) >= 2 and draws:
        rs = []
        for _ in range(draws):
            pick = [evs[rng.randrange(len(evs))] for _ in evs]
            st = sum(e["w"] * e["stake"] for e in pick)
            rs.append(sum(e["w"] * e["pnl"] for e in pick) / st if st else 0.0)
        rs.sort()
        out["ci95"] = [round(rs[int(0.025 * draws)], 5), round(rs[int(0.975 * draws) - 1], 5)]
    return out


def evaluate(markets: list[dict], candles: dict[str, list[dict]], series: dict[str, dict], short_weight: float = 1.0) -> dict:
    rng = random.Random(SEED)
    out = {"registered": REGISTERED, "amended": AMENDED, "markets": len(markets), "with_candles": sum(1 for m in markets if candles.get(m["ticker"])),
           "short_weight": round(short_weight, 3), "results": {}}
    for days in ENTRY_DAYS:
        for version in ("taker", "maker_strict", "maker_loose"):
            evs = event_bets(markets, candles, series, days, version, short_weight)
            for group in ("recreational", "control"):
                g = [e for e in evs if e["group"] == group]
                if not g:
                    continue
                key = f"{version}/{days}d/{group}"
                r = summarize(g, rng)
                mid = sorted(e["t"] for e in g)[len(g) // 2]
                r["halves"] = [summarize([e for e in g if e["t"] < mid], rng, 0), summarize([e for e in g if e["t"] >= mid], rng, 0)]
                r["by_bucket"] = {}
                for bk in ("1-3c", "4-6c", "7-10c"):
                    st = sum(e["w"] * e["buckets"].get(bk, [0, 0, 0])[0] for e in g)
                    pl = sum(e["w"] * e["buckets"].get(bk, [0, 0, 0])[1] for e in g)
                    r["by_bucket"][bk] = {"contracts": sum(e["buckets"].get(bk, [0, 0, 0])[2] for e in g), "return": round(pl / st, 5) if st else None}
                r["by_category"] = {}
                for cat in sorted({e["category"] for e in g}):
                    c = [e for e in g if e["category"] == cat]
                    st = sum(e["w"] * e["stake"] for e in c)
                    r["by_category"][cat] = {"events": len(c), "return": round(sum(e["w"] * e["pnl"] for e in c) / st, 5) if st else None}
                out["results"][key] = r
    main = out["results"].get(f"taker/{MAIN_DAYS}d/recreational")
    out["main_test"] = None if not main or "ci95" not in main else {
        "passed": bool(main["ci95"][0] > 0 and all((h.get("return") or 0) > 0 for h in main["halves"])),
        "return": main["return"], "ci95": main["ci95"], "halves": [h.get("return") for h in main["halves"]], "events": main["events"]}
    return out


# ---- fetching ---------------------------------------------------------------------------------------------------

class Fetcher:
    """Kalshi's public API, gently: about `rate` requests a second, a long pause after a 429, a few retries."""

    def __init__(self, rate: float = 0.5, log=print) -> None:
        from kalshi.api import KalshiClient
        self.client, self.gap, self.next_at, self.log = KalshiClient(), 1.0 / rate, 0.0, log
        self.requests = self.limited = self.failed = 0

    def get(self, path: str, params: dict | None = None) -> dict | None:
        from kalshi.api import KalshiApiError
        pause = 30.0
        for _ in range(6):
            wait = self.next_at - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.next_at = time.monotonic() + self.gap
            self.requests += 1
            try:
                return self.client.get(path, params)
            except KalshiApiError as exc:
                if getattr(exc, "rate_limited", False):
                    self.limited += 1
                    time.sleep(max(pause, getattr(exc, "retry_after_s", 0) or 0))
                    pause = min(pause * 2, 300.0)
                    continue
                if "404" in str(exc):
                    return None
                self.failed += 1
                time.sleep(5)
            except Exception:  # a timeout or a dropped connection
                self.failed += 1
                time.sleep(5)
        return None


def sample_series(all_series: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for group, n in SERIES_SAMPLE.items():
        pool = sorted((s for s in all_series if group_of(s.get("category")) == group and s.get("frequency") not in SKIP_FREQUENCY),
                      key=lambda s: s["ticker"])
        out += rng.sample(pool, min(n, len(pool)))
    return out


def _keep(m: dict) -> bool:
    try:
        closed = _ts(m["close_time"])
    except (KeyError, ValueError):
        return False
    return (m.get("market_type") == "binary" and m.get("result") in ("yes", "no") and _ts(CLOSED_FROM) <= closed < _ts(CLOSED_TO)
            and (_num(m.get("volume_fp")) or _num(m.get("volume")) or 0) >= MIN_VOLUME and bool(m.get("open_time")))


def fetch(data: Path, rate: float = 0.5) -> None:
    data.mkdir(parents=True, exist_ok=True)
    (data / "candles").mkdir(exist_ok=True)
    (data / "markets").mkdir(exist_ok=True)
    logf = open(data / "fetch.log", "a")
    def log(*a):
        print(datetime.now(timezone.utc).strftime("%H:%M:%SZ"), *a, file=logf, flush=True)
    f = Fetcher(rate, log)
    if not (data / "series.json").exists():
        _write(data / "series.json", (f.get("/series") or {}).get("series") or [])
    cutoff = _ts(((f.get("/historical/cutoff") or {}).get("market_settled_ts")) or "2026-09-11T00:00:00Z")
    picked = sample_series(json.loads((data / "series.json").read_text()))
    log(f"{len(picked)} series sampled; historical cutoff {cutoff}")
    unlisted = 0
    for i, s in enumerate(picked):
        path = data / "markets" / f"{s['ticker']}.json"
        if path.exists():
            continue
        found: dict[str, dict] = {}
        complete = True
        for endpoint, extra in (("/historical/markets", {}), ("/markets", {"status": "settled"})):
            cursor, pages = None, 0
            while True:
                page = f.get(endpoint, {"series_ticker": s["ticker"], "limit": 1000, **extra, **({"cursor": cursor} if cursor else {})})
                pages += 1
                if page is None:
                    complete = False
                    break
                for m in page.get("markets") or []:
                    if _keep(m):
                        found.setdefault(m["ticker"], m)  # listed by both endpoints around the cutoff: once
                cursor = page.get("cursor")
                if not cursor or pages >= 100:
                    if cursor:
                        log(f"series {s['ticker']}: {endpoint} stopped at 100 pages")
                    break
        if not complete:
            log(f"series {s['ticker']}: a listing page failed; left for the next run")
            unlisted += 1
            continue
        rng = random.Random(f"{SEED}:{s['ticker']}")
        by_event: dict[str, list[dict]] = {}
        for m in sorted(found.values(), key=lambda m: m["ticker"]):
            by_event.setdefault(m["event_ticker"], []).append({**m, "series_ticker": s["ticker"]})
        kept = [m for ms in by_event.values() for m in (rng.sample(ms, MARKETS_PER_EVENT) if len(ms) > MARKETS_PER_EVENT else ms)]
        _write(path, kept)
        log(f"series {i + 1}/{len(picked)} {s['ticker']}: {len(kept)} markets kept; requests {f.requests}, 429s {f.limited}, failed {f.failed}")
    markets = to_price(load_markets(data))
    log(f"{len(markets)} markets to price")
    for j, m in enumerate(markets):
        path = data / "candles" / f"{m['ticker']}.json"
        if path.exists():
            continue
        opened, closed = _ts(m["open_time"]), _ts(m["close_time"])
        params = {"start_ts": opened, "end_ts": min(closed + DAY_S, opened + (max(ENTRY_DAYS) + 400) * DAY_S), "period_interval": 1440}
        settled = _ts(m.get("settlement_ts") or m["close_time"])
        hist, live = f"/historical/markets/{m['ticker']}/candlesticks", f"/series/{m['series_ticker']}/markets/{m['ticker']}/candlesticks"
        first, second = (hist, live) if settled < cutoff else (live, hist)
        got = f.get(first, params)
        if got is None:
            got = f.get(second, params)
        if got is not None:
            _write(path, got.get("candlesticks") or [])
        if j % 100 == 0:
            log(f"candles {j}/{len(markets)}; requests {f.requests}, 429s {f.limited}, failed {f.failed}")
    missing = sum(1 for m in markets if not (data / "candles" / f"{m['ticker']}.json").exists())
    log(f"done: {len(markets) - missing} of {len(markets)} markets priced ({missing} missing), {unlisted} series not listed "
        f"(run again to retry both); "
        f"requests {f.requests}, 429s {f.limited}, failed {f.failed}")


def _write(path: Path, obj) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj))
    tmp.replace(path)


def load_markets(data: Path) -> list[dict]:
    """Every listed market once (a market listed twice around the cutoff counts once)."""
    seen: dict[str, dict] = {}
    for p in sorted((data / "markets").glob("*.json")):
        for m in json.loads(p.read_text()):
            seen.setdefault(m["ticker"], m)
    return list(seen.values())


def to_price(markets: list[dict]) -> list[dict]:
    """The markets whose prices are fetched: every one open 7 days or more, then a seeded sample of
    CANDLE_SHORT_SAMPLE of those open 1 to 7 days."""
    span = lambda m: _ts(m["close_time"]) - _ts(m["open_time"])  # noqa: E731
    long_ = sorted((m for m in markets if span(m) > MAIN_DAYS * DAY_S), key=lambda m: m["ticker"])
    short = sorted((m for m in markets if DAY_S < span(m) <= MAIN_DAYS * DAY_S), key=lambda m: m["ticker"])
    rng = random.Random(f"{SEED}:short")
    return long_ + (rng.sample(short, CANDLE_SHORT_SAMPLE) if len(short) > CANDLE_SHORT_SAMPLE else short)


def load(data: Path) -> tuple[list[dict], dict[str, list[dict]], dict[str, dict], float]:
    """(markets priced, their candles, series, the weight of a sampled short-lived event: population over sample)."""
    series = {s["ticker"]: s for s in json.loads((data / "series.json").read_text())}
    every = load_markets(data)
    markets = to_price(every)
    population = sum(1 for m in every if short_lived(m) and _ts(m["close_time"]) - _ts(m["open_time"]) > DAY_S)
    sampled = sum(1 for m in markets if short_lived(m))
    weight = population / sampled if sampled else 1.0
    candles = {}
    for m in markets:
        p = data / "candles" / f"{m['ticker']}.json"
        if p.exists():
            candles[m["ticker"]] = [{**c, "end_period_ts": int(c["end_period_ts"])} for c in json.loads(p.read_text()) if c.get("end_period_ts") is not None]
    return markets, candles, series, weight


def lines(r: dict) -> list[str]:
    pct = lambda x: "-" if x is None else f"{100 * x:+.2f}%"  # noqa: E731
    out = [f"long-shot fade backtest (rules registered {r['registered']}, amended {r['amended']} before any price was fetched): "
           f"{r['markets']} markets to price, {r['with_candles']} with daily prices"]
    for key, v in r["results"].items():
        ci = v.get("ci95")
        out.append(f"{key:28} {v['events']:5d} events {v['contracts']:6d} contracts  return {pct(v['return'])}"
                   + (f" (95%: {pct(ci[0])} to {pct(ci[1])})" if ci else "") + f"  halves {pct(v['halves'][0].get('return'))} / {pct(v['halves'][1].get('return'))}"
                   + f"  upsets {v['upset_share'] if v['upset_share'] is not None else '-'}")
    mt = r.get("main_test")
    out.append("main test (taker, 7 days, recreational): " + ("not enough data" if not mt else
               f"{'PASSED' if mt['passed'] else 'FAILED'}: return {pct(mt['return'])}, 95% {pct(mt['ci95'][0])} to {pct(mt['ci95'][1])}, halves {' / '.join(pct(h) for h in mt['halves'])}, {mt['events']} events"))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="The long-shot fade on Kalshi's settled markets")
    parser.add_argument("command", choices=("fetch", "report"))
    parser.add_argument("--data", required=True)
    parser.add_argument("--rate", type=float, default=0.5)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    data = Path(args.data)
    if args.command == "fetch":
        fetch(data, args.rate)
        return 0
    r = evaluate(*load(data))
    if args.out:
        Path(args.out).write_text(json.dumps(r, indent=1))
    print("\n".join(lines(r)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
